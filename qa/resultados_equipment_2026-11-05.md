# QA de consistencia — `works4cdp_equipment` (2026-11-05)

Sonda: `qa/probe_equipment_consistency.sql` (solo SELECT). 209 filas, 0 sin área.

## Veredicto

La tabla **no tiene datos contradictorios**: ninguna fila es indistinguible de otra y el área
codificada en `description` coincide con `area_id` en las 62 filas donde viene. Lo que tiene son
**cuatro problemas de modelo**, y uno de ellos es un bug latente que rompe la aplicación.

## 1. BUG LATENTE: la secuencia de `id` va a chocar

| secuencia en | id máximo real | primer id ocupado por delante | INSERT antes del error |
|---:|---:|---:|---:|
| 184 | 99353 | 301 | **116** |

Las filas se cargaron a mano en bloques (`2001-2012`, `10001-10010`, `14001-14003`, `20001-20901`,
`21001-21902`, `22902`, `99353`) sin mover `works4cdp_equipment_id_seq`, que quedó en 184. Los
próximos 116 `INSERT` funcionan; el 117 pide el id 301, que ya existe, y revienta con
`duplicate key value violates unique constraint "works4cdp_equipment_pkey"`.

Arreglo (una línea, idempotente, se puede dejar en una migración `RunSQL`):

```sql
SELECT setval('works4cdp_equipment_id_seq', (SELECT max(id) FROM works4cdp_equipment));
```

Conviene revisar lo mismo en las otras tablas que se cargaron por script.

## 2. Hay 13 filas que no son equipos

| Qué es | Filas | Tareas asociadas |
|---|---:|---:|
| **Personas** (`Juan Alvarez`, `Gonzalo Chavez`, `Albert Churata`, `Sebastian Pino`, `Sharon Riquelme`, `Esteban Cabala`, `Jean Pool Mendoza`, `Eder Aliaga`, `Alexandra Flores`, `Adolfo Ccallo`) | 10 | **0** |
| Vehículo (`Camioneta S2417`) | 1 | 1 |
| Almacenes (`Minicelda`, `Remolienda`, descripción `Almacen`) | 2 | 2 |

Las 10 personas están todas en sistema `Seguridad y Salud Ocupacional` / área
`Sistema Integrado de Gestion`, con el cargo en `description` (Superintendencia, Jefatura,
Supervision, Entrenamiento, Tecnico, Becario). **Ninguna tiene una sola tarea**: no se usan, solo
ocupan la tabla. Y 5 de esas personas ya existen en `works4cdp_user`, así que están duplicadas
(ahí, además, con emails de relleno: `q@q.com`, `a@a.com`, `b@b.com`, `f@f.com`, `q@p.com`).

Propuesta: borrar las 10 filas de personas (no rompe nada, 0 referencias) y completar
`works4cdp_user`, que es donde va el cargo. Para el vehículo y los almacenes hay que decidir: o son
equipos de verdad y se quedan, o `Task` necesita poder colgar de algo que no sea un equipo.

## 3. El identificador real es `tag`, y falta en el 75 %

| | Filas |
|---|---:|
| `tag IS NULL` | 49 |
| `tag = ''` (cadena vacía) | 107 |
| **sin tag** | **156 de 209** |
| `description IS NULL` | 14 |
| `description = ''` | 44 |

Primero: **`NULL` y `''` se usan indistintamente** para lo mismo, en los dos campos. Eso obliga a
escribir `tag IS NULL OR btrim(tag) = ''` en cada consulta y es puro accidente histórico de dos vías
de carga distintas. Normalizar a `NULL` y dejarlo así.

Segundo, y más de fondo: `name` **no identifica** al equipo. Hay 60 filas llamadas `Controlador`,
16 `Cliente de Control`, 16 `HMI`, 15 `Gabinetes Comunicacion`. En `Molienda C1` hay 12
`Controlador` en la misma área, y lo único que los separa es el tag:

```
  406  Controlador  (null)        PLC   "Sistema Lubricación"
20009  Controlador  Courier_Moly  DCS
20010  Controlador  PCU01         DCS
20011  Controlador  PCU05         DCS
...    (hasta PCU22)
```

Eso está **bien**: son PCUs distintas y el tag las distingue. El problema es el otro lado: de los
130 equipos que tienen tareas, **82 no tienen tag**. Para esos 82 la identidad es
`nombre + área + sistema`, que en varios casos tampoco alcanza — `Relaves C1 / HMI` son dos filas
(412, 415) con el mismo nombre, la misma área y el mismo sistema.

## 4. Dos tags duplicados

```
2101   2003:System800xA (DCS, Espesador de lamas) | 2004:HMI (PLC, Espesador de lamas)
8200    375:System800xA (DCS, Sistema de bombeo C2) | 2001:System800xA (DCS, Barcazas)
```

El primero puede ser legítimo si `2101` es el código del área y no del equipo. El segundo son dos
`System800xA` con el mismo tag en **plantas distintas** (Concentradora 2 y Quebrada Honda): uno de
los dos está mal.

## 5. `description` hace de cuarto campo de ubicación

Los valores más frecuentes no son descripciones sino códigos de área: `Red` (28), `QH` (8), `C2` (5),
`C1` (4), `C2_Molibdeno` (4), `C1_Chancado Primario` (3), `C1_ExCuarto Molinos` (3)… Es la misma
información que ya está en `area_id`, repetida a mano. **Lo bueno: coincide en las 62 filas**, no hay
una sola contradicción. Pero es información duplicada que en algún momento va a divergir.

`C1_ExCuarto Molinos` no corresponde a ninguna área de `works4cdp_area`: es un nombre histórico que
sobrevive solo acá.

## 6. Riesgo estructural: `on_delete=CASCADE` en `Equipment.area`

`Area → Equipment → Task → TaskP`, más `Equipment → Sample` y `Equipment → CorrectiveTask`, todo en
cascada. Borrar **un** área desde el admin o desde una grilla borra en silencio su historial completo:

| Área | Equipos | Tareas | Ocurrencias TaskP | De ellas en R |
|---|---:|---:|---:|---:|
| Molibdeno C1 | 8 | 30 | 979 | 191 |
| Molibdeno C2 | 11 | 34 | 978 | 188 |
| Flotacion C2 | 7 | 34 | 978 | 193 |
| Flotacion C1 | 5 | 19 | 886 | 172 |
| Molienda C1 | 22 | 55 | 660 | 94 |

(Total de la tabla: 7487 ocurrencias, 1155 en estado R.)

Un solo borrado de `Molibdeno C1` se lleva 979 ocurrencias y 191 marcaciones de realizado. Debería
ser `PROTECT` en `Equipment.area` y `Equipment.system`, y `PROTECT` en `Task.equipment`.

## 7. Nada que arreglar acá

- Higiene de texto: 0 espacios al borde, 0 espacios dobles, 0 variantes del mismo nombre por tilde o
  mayúscula. Un solo tag con minúsculas (`Courier_Moly`).
- 0 filas con `area_id` nulo, 0 nombres vacíos.
- 0 contradicciones entre `description` y `area_id`.
- Ningún nombre con sufijo `C1`/`C2` colgado de la concentradora equivocada.

## 8. Cobertura (no es inconsistencia, pero conviene saberlo)

- **71 de 209 equipos sin ningún uso** (ni tarea, ni correctiva, ni muestra): 34 %.
- Áreas sin un solo equipo: `Agua C1` y `Area 3100`.
- Sistemas sin un solo equipo: `Sistema PI`, `CCTV`, `Actividades CDP`.
- Reparto por sistema: DCS 123, Redes 32, PLC 26, Seguridad y Salud Ocupacional 10, Analizadores 8,
  Sistema Experto 4, Otros 3, Sistema SPLIT 3.

## 9. Falta de restricciones en el modelo

`Equipment` no declara ni un `UniqueConstraint`. Nada impide hoy cargar dos veces el mismo equipo.
Candidatos:

```python
class Meta:
    constraints = [
        models.UniqueConstraint(Lower('tag'), name='equipment_tag_unico',
                                condition=~Q(tag=None) & ~Q(tag='')),
        models.UniqueConstraint(Lower('name'), 'area', 'system', name='equipment_nombre_area_sistema'),
    ]
```

La segunda **no pasa hoy**: la violan `Relaves C1/HMI` (412, 415) y `Data Center C1/Sala de
Servidores` (305, 373), entre otras. Hay que resolver esas filas antes de poder imponerla.

## Relación con `SIG_CDP_POWERAPPS`

Esto pega directo en la integración: SharePoint identifica el equipo por **nombre** (`trab_equipo`,
texto de la maestra `Equipo`, que a su vez solo tiene `Tag_equipo` en 11 de 467 filas). Con 60 filas
llamadas `Controlador` acá, el nombre no alcanza para decir qué se hizo. Publicar `equipo_tag` junto
al nombre es lo único que desambigua — y para 82 de los 130 equipos con tareas, ese tag no existe.
