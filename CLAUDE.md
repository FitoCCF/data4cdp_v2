# data4cdpv1

Servidor de desarrollo: PostgreSQL, backend y frontend en contenedores
Docker separados. Entorno de integración.

## Relación
Los scripts Python se validan primero en ../data4cdpv1_local/ y recién
después se integran aquí, con la misma versión de dependencias.

## Ejecución de comandos: los corre el usuario, no Claude

**Claude no ejecuta ningún comando.** No usa la terminal ni para leer. Esto vale para todo, sin
excepción y sin importar cuán inocuo parezca el comando: `migrate`, `makemigrations`, `test`, `psql`,
`docker exec`, `git`, `npm`, y también `cat`, `ls`, `grep` o un `SELECT` de solo lectura.

Claude sí lee y escribe archivos del repositorio con sus propias herramientas de archivo. Eso no
pasa por la terminal y no requiere autorización.

### Cómo se pide un comando
Claude escribe el comando y el usuario lo ejecuta en otra consola. Cada pedido lleva:

1. **Qué hace**, en una línea y en castellano llano.
2. **El comando**, en un bloque de código, completo y copiable de una sola vez (sin placeholders
   del tipo `<id>`: si hace falta un valor, Claude lo resuelve antes o lo pide aparte).
3. **Qué salida necesita de vuelta**, cuando no sea obvia: todo, las últimas N líneas, o solo si
   falla.

Si hay varios comandos independientes, van juntos en **un solo bloque** para que se peguen de una
vez. Si uno depende del resultado del anterior, van por separado y Claude espera la salida.

### Reglas
- **Claude espera la salida real antes de seguir.** No da por hecho que un comando funcionó, no
  escribe lo que "habría salido" y no reporta algo como verificado sin haber visto la salida.
- Si una conclusión depende de un comando que todavía no se corrió, Claude lo dice y avanza con todo
  lo que no dependa de eso.
- Los comandos destructivos o difíciles de revertir van **señalados aparte**, con lo que destruyen
  medido de antemano, nunca escondidos en un bloque junto a otros.
- Si un comando pide confirmación interactiva o credenciales, Claude lo avisa.

## Servicios
Contenedores: `postgres_db` (TimescaleDB/PostgreSQL), `django_backend`, `vue_frontend`.

- Base `mydb`, usuario `myuser`. Puerto 5432 dentro de la red de Docker, **5433** desde el host.
- En `django_backend`, `/app` es el `backend/` del host (mismo archivo por el volumen).
- El banco de pruebas `../data4cdpv1_local/` corre con pixi:
  `/home/daigo/data4cdpv1_local/.pixi/envs/default/bin/python`.

## Comandos

```bash
# Migraciones: generar, y después ajustar el dueño del archivo (el contenedor corre como root)
docker exec django_backend python manage.py makemigrations works4cdp --name <descripcion>
docker exec django_backend chown 1000:1000 /app/works4cdp/migrations/<archivo>.py

# Ver qué SQL ejecutaría una migración antes de aplicarla, y aplicarla
docker exec django_backend python manage.py sqlmigrate works4cdp <numero>
docker exec django_backend python manage.py migrate works4cdp

# Pruebas: SIEMPRE con --keepdb (ver la nota de abajo)
docker exec django_backend python manage.py test works4cdp --keepdb --noinput

# Consultas a la base
docker exec -i postgres_db psql -U myuser -d mydb -f - < <archivo.sql>
```

### Dos trampas conocidas del entorno (2026-11-05)
- **Las pruebas necesitan `--keepdb`.** Django no puede crear su base de pruebas: `template1` tiene
  una `datcollversion` vieja (2.36) que el glibc del contenedor ya no confirma, así que
  `CREATE DATABASE` falla. `test_mydb` se creó a mano desde `template0`.
- **La migración `0005` no se aplica en una base nueva**: agrega un `UniqueConstraint` llamado
  `works4cdp_assay_pkey`, que es el nombre que PostgreSQL ya le dio a la clave primaria implícita de
  `works4cdp_assay`. Para armar `test_mydb` hubo que aplicar `migrate works4cdp 0005 --fake`. **Está
  pendiente arreglarla**: hoy el proyecto no se puede levantar de cero.
