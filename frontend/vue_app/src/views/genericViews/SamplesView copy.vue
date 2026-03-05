<!-- Indica el inicio del bloque de plantilla del componente Vue. -->
<template>
  <!-- Abre un contenedor principal con clase `samples-view` para maquetar la vista. -->
  <div class="samples-view">
    <!-- Muestra el título principal “Mantenimiento de Muestras”. -->
    <h1>Mantenimiento de Muestras</h1>
<!-- Línea en blanco que aporta legibilidad en la plantilla. -->

    <!-- Abre el formulario con clase `sample-form` y evita el envío tradicional del navegador usando `@submit.prevent="submitForm"`. -->
    <form class="sample-form" @submit.prevent="submitForm">
      <!-- Define el subtítulo del formulario mostrando “Editar muestra” si existe `form.id`, o “Nueva muestra” en caso contrario. -->
      <h2>{{ form.id ? 'Editar muestra' : 'Nueva muestra' }}</h2>
<!-- Línea en blanco para separar bloques del formulario. -->

      <!-- Abre una etiqueta `<label>` para agrupar el campo del tag. -->
      <label>
        <!-- Texto del label que indica que el campo captura el “Tag”. -->
        Tag
        <!-- Campo de texto enlazado con `form.tag`, requerido y con placeholder “TAG”. -->
        <input v-model="form.tag" type="text" required placeholder="TAG" />
      <!-- Cierra el `<label>` del campo Tag. -->
      </label>
<!-- Línea en blanco para separar controles. -->

      <!-- Abre el segundo `<label>` para el nombre de la muestra. -->
      <label>
        <!-- Texto que describe el campo como “Nombre”. -->
        Nombre
        <!-- Campo de texto vinculado a `form.name`, obligatorio y con placeholder descriptivo. -->
        <input v-model="form.name" type="text" required placeholder="Nombre de la muestra" />
      <!-- Cierra el `<label>` del nombre. -->
      </label>
<!-- Línea en blanco para separar el siguiente bloque. -->

      <!-- Abre el `<label>` para seleccionar el equipo asociado. -->
      <label>
        <!-- Texto indicativo “Equipo asociado”. -->
        Equipo asociado
        <!-- Abre un `<select>` enlazado con `form.equipment`, obligatorio. -->
        <select v-model="form.equipment" required>
          <!-- Opción inicial deshabilitada que obliga a elegir un equipo. -->
          <option value="" disabled>Selecciona un equipo</option>
          <!-- Inicia la definición de la opción repetida por cada equipo disponible. -->
          <option
            <!-- Usa `v-for` para iterar sobre `availableEquipments`. -->
            v-for="equipment in availableEquipments"
            <!-- Proporciona una clave única basada en `equipment.id` para el renderizado eficiente. -->
            :key="equipment.id"
            <!-- Asigna el valor de la opción al identificador del equipo. -->
            :value="equipment.id"
          <!-- Mantiene la indentación y prepara el contenido interno de la opción. -->
          >
            <!-- Muestra la etiqueta legible de cada equipo mediante `equipmentDisplay`. -->
            {{ equipmentDisplay(equipment) }}
          <!-- Cierra la etiqueta `<option>` del bucle. -->
          </option>
        <!-- Cierra el `<select>` de equipos. -->
        </select>
      <!-- Cierra el `<label>` asociado al selector. -->
      </label>
<!-- Línea en blanco que separa el área de acciones del formulario. -->

      <!-- Abre un contenedor `div` para los botones del formulario. -->
      <div class="form-actions">
        <!-- Define el botón de envío del formulario con deshabilitado condicionado por `loading`. -->
        <button type="submit" :disabled="loading">
          <!-- Muestra “Actualizar” si se edita una muestra (hay `form.id`), en otro caso “Crear”. -->
          {{ form.id ? 'Actualizar' : 'Crear' }}
        <!-- Cierra la etiqueta del botón de envío. -->
        </button>
        <!-- Define el botón secundario tipo botón que resetea el formulario; se deshabilita si hay carga o no existe `form.id`. -->
        <button type="button" @click="resetForm" :disabled="loading || !form.id">
          <!-- Etiqueta visible “Cancelar edición” para el botón secundario. -->
          Cancelar edición
        <!-- Cierra el botón de cancelar. -->
        </button>
      <!-- Cierra el contenedor de acciones del formulario. -->
      </div>
<!-- Línea en blanco para mejorar la lectura. -->

      <!-- Muestra un párrafo de feedback solo si hay mensaje y aplica clases dinámicas para estilo y tipo. -->
      <p v-if="feedback.message" :class="['feedback', feedback.type]">{{ feedback.message }}</p>
    <!-- Cierra el formulario. -->
    </form>
<!-- Línea en blanco separadora antes de la tabla. -->

    <!-- Abre una sección para la tabla de muestras con clase `samples-table`. -->
    <section class="samples-table">
      <!-- Título de la sección de listado “Listado de muestras”. -->
      <h2>Listado de muestras</h2>
<!-- Línea en blanco para separar el título de la tabla. -->

      <!-- Renderiza la tabla solo si existen muestras (`samples.length`). -->
      <table v-if="samples.length">
        <!-- Abre la cabecera de la tabla (`thead`). -->
        <thead>
          <!-- Abre la fila de cabecera. -->
          <tr>
            <!-- Encabezado de columna para el ID. -->
            <th>ID</th>
            <!-- Encabezado de columna para el Tag. -->
            <th>Tag</th>
            <!-- Encabezado de columna para el Nombre. -->
            <th>Nombre</th>
            <!-- Encabezado de columna para el Equipo. -->
            <th>Equipo</th>
            <!-- Encabezado de columna para las acciones disponibles. -->
            <th>Acciones</th>
          <!-- Cierra la fila de cabecera. -->
          </tr>
        <!-- Cierra el bloque `thead`. -->
        </thead>
        <!-- Abre el cuerpo de la tabla (`tbody`). -->
        <tbody>
          <!-- Crea una fila por cada muestra usando `v-for` con clave `sample.id`. -->
          <tr v-for="sample in samples" :key="sample.id">
            <!-- Celda que muestra el identificador de la muestra. -->
            <td>{{ sample.id }}</td>
            <!-- Celda para el tag de la muestra. -->
            <td>{{ sample.tag }}</td>
            <!-- Celda para el nombre de la muestra. -->
            <td>{{ sample.name }}</td>
            <!-- Celda que muestra el equipo asociado mediante `equipmentLabel`. -->
            <td>{{ equipmentLabel(sample.equipment) }}</td>
            <!-- Celda de acciones con clase `actions`. -->
            <td class="actions">
              <!-- Botón que inicia la edición de la muestra; se deshabilita cuando hay carga. -->
              <button @click="startEdit(sample)" :disabled="loading">Editar</button>
              <!-- Botón para eliminar la muestra; también se deshabilita mientras hay carga. -->
              <button @click="deleteSample(sample.id)" :disabled="loading">Eliminar</button>
            <!-- Cierra la celda de acciones. -->
            </td>
          <!-- Cierra la fila de muestra. -->
          </tr>
        <!-- Cierra el cuerpo de la tabla. -->
        </tbody>
      <!-- Cierra la etiqueta de la tabla. -->
      </table>
      <!-- Muestra un mensaje alternativo cuando no hay muestras registradas. -->
      <p v-else class="empty">No hay muestras registradas.</p>
    <!-- Cierra la sección de la tabla. -->
    </section>
  <!-- Cierra el `div` principal del componente. -->
  </div>
<!-- Cierra el bloque de plantilla. -->
</template>
<!-- Línea en blanco que separa la plantilla del script. -->

<!-- Abre el bloque de script declarativo con la sintaxis `<script setup>`. -->
<script setup>
// Importa los helpers de Vue `computed`, `onMounted`, `reactive`, `ref`.
import { computed, onMounted, reactive, ref } from 'vue';
// Importa el cliente API definido en `../../api`.
import { api } from '../../api';
// Línea en blanco para separar importaciones de la lógica.

// Declara `samples` como referencia reactiva inicializada con arreglo vacío.
const samples = ref([]);
// Declara `equipments` como referencia reactiva para almacenar equipos.
const equipments = ref([]);
// Declara `loading` como referencia booleana para indicar procesos en curso.
const loading = ref(false);
// Declara `feedback` como objeto reactivo con mensaje y tipo inicial “success”.
const feedback = reactive({ message: '', type: 'success' });
// Línea en blanco que separa la utilidad de formulario.

// Define una función que devuelve el estado vacío del formulario.
const emptyForm = () => ({ id: null, tag: '', name: '', equipment: '' });
// Crea un objeto reactivo `form` basado en `emptyForm()`.
const form = reactive(emptyForm());
// Línea en blanco antes de las propiedades computadas.

// Declara la computada `availableEquipments`.
const availableEquipments = computed(() =>
  // Filtra `equipments.value` para quedarse solo con los que pertenecen al sistema 5.
  equipments.value.filter((equipment) => equipment.system === 5)
// Cierra la función de filtro del `computed`.
);
// Línea en blanco para separar otra computada.

// Declara `equipmentMap` como computada que construye un mapa de equipos por id.
const equipmentMap = computed(() => {
  // Crea una instancia de `Map` para almacenar las relaciones.
  const map = new Map();
  // Itera sobre los equipos disponibles.
  equipments.value.forEach((equipment) => {
    // Registra en el mapa cada equipo usando su id como clave.
    map.set(equipment.id, equipment);
  // Continúa la iteración por legibilidad.
  });
  // Devuelve el mapa resultante.
  return map;
// Cierra la función de la computada.
});
// Línea en blanco que separa helpers de visualización.

// Declara `equipmentDisplay`, utilidad para formatear un equipo.
const equipmentDisplay = (equipment) => {
  // Devuelve guion largo si no hay equipo.
  if (!equipment) return '—';
  // Junta nombre y descripción del equipo ignorando valores vacíos.
  const segments = [equipment.name, equipment.description].filter(Boolean);
  // Une los segmentos con “ - ” para mostrar.
  return segments.join(' - ');
// Cierra la función `equipmentDisplay`.
};
// Línea en blanco antes de la siguiente utilidad.

// Declara `equipmentLabel` que recibe un identificador.
const equipmentLabel = (equipmentId) => {
  // Obtiene el equipo correspondiente desde el mapa computado.
  const equipment = equipmentMap.value.get(equipmentId);
  // Devuelve la representación visual usando `equipmentDisplay`.
  return equipmentDisplay(equipment);
// Cierra la función `equipmentLabel`.
};
// Línea en blanco antes de funciones de feedback.

// Declara `resetFeedback` para limpiar los mensajes de estado.
const resetFeedback = () => {
  // Elimina cualquier mensaje previo de feedback.
  feedback.message = '';
  // Restaura el tipo de feedback a “success”.
  feedback.type = 'success';
// Cierra la función `resetFeedback`.
};
// Línea en blanco antes de `setFeedback`.

// Declara `setFeedback` con mensaje y tipo opcional.
const setFeedback = (message, type = 'success') => {
  // Actualiza el mensaje mostrado al usuario.
  feedback.message = message;
  // Actualiza el tipo de mensaje (`success` o `error`).
  feedback.type = type;
// Cierra la función `setFeedback`.
};
// Línea en blanco antes de carga remota.

// Declara la función asíncrona `loadSamples`.
const loadSamples = async () => {
  // Abre bloque `try` para capturar errores de red.
  try {
    // Realiza petición GET a `samples/`.
    const response = await api.get('samples/');
    // Almacena la respuesta en la referencia `samples`.
    samples.value = response.data;
  // Cierra el bloque `try`.
  } catch (error) {
    // Maneja errores registrándolos en consola.
    console.error('Error al obtener muestras:', error);
    // Informa al usuario que no se pudieron cargar las muestras y marca el feedback como error.
    setFeedback('No se pudieron cargar las muestras.', 'error');
  // Cierra el bloque `catch`.
  }
// Cierra la función `loadSamples`.
};
// Línea en blanco antes de la función que carga equipos.

// Declara `loadEquipments` como función asíncrona.
const loadEquipments = async () => {
  // Abre bloque `try` para la petición.
  try {
    // Solicita la lista de equipos al endpoint `equipments/`.
    const response = await api.get('equipments/');
    // Guarda la respuesta en la referencia `equipments`.
    equipments.value = response.data;
  // Cierra el bloque `try`.
  } catch (error) {
    // Registra los errores de obtención en consola.
    console.error('Error al obtener equipos:', error);
    // Muestra feedback de error cuando no se pueden cargar los equipos.
    setFeedback('No se pudieron cargar los equipos disponibles.', 'error');
  // Cierra el bloque `catch`.
  }
// Cierra la función `loadEquipments`.
};
// Línea en blanco antes de utilidades de edición.

// Declara `startEdit` que recibe una muestra para editar.
const startEdit = (sample) => {
  // Copia el id de la muestra al formulario.
  form.id = sample.id;
  // Copia el tag al formulario editable.
  form.tag = sample.tag;
  // Copia el nombre al formulario.
  form.name = sample.name;
  // Copia el id del equipo asociado al formulario.
  form.equipment = sample.equipment;
  // Limpia cualquier mensaje previo de feedback.
  resetFeedback();
// Cierra la función `startEdit`.
};
// Línea en blanco antes de `resetForm`.

// Declara `resetForm` para restaurar el formulario al estado inicial.
const resetForm = () => {
  // Usa `Object.assign` para copiar los valores vacíos en `form`.
  Object.assign(form, emptyForm());
  // Limpia el feedback tras resetear.
  resetFeedback();
// Cierra la función `resetForm`.
};
// Línea en blanco previa al manejador de envío.

// Declara `submitForm` como función asíncrona del envío del formulario.
const submitForm = async () => {
  // Activa el estado de carga.
  loading.value = true;
  // Limpia mensajes de feedback anteriores.
  resetFeedback();
  // Construye el objeto `payload` con los datos del formulario.
  const payload = {
    // Asigna el tag al payload.
    tag: form.tag,
    // Asigna el nombre de la muestra.
    name: form.name,
    // Convierte el equipo a número o lo deja en `null` si no hay valor.
    equipment: form.equipment ? Number(form.equipment) : null,
  // Cierra la definición de `payload`.
  };
// Línea en blanco antes del bloque `try`.

  // Abre bloque `try` para manejar la petición de guardado.
  try {
    // Verifica si se está editando una muestra existente.
    if (form.id) {
      // Hace petición PUT al endpoint de la muestra para actualizarla.
      await api.put(`samples/${form.id}/`, payload);
      // Muestra feedback de éxito al actualizar.
      setFeedback('Muestra actualizada correctamente.');
    // Si no hay id, procede a crear nueva muestra.
    } else {
      // Realiza una petición POST a `samples/` con los datos.
      await api.post('samples/', payload);
      // Informa que la muestra se creó correctamente.
      setFeedback('Muestra creada correctamente.');
    // Tras guardar, recarga las muestras desde el servidor.
    }
    // Reinicia el formulario a su estado vacío.
    await loadSamples();
    // Cierra el bloque `try`.
    resetForm();
  // Registra en consola cualquier error producido.
  } catch (error) {
    // Muestra mensaje de error si algo falla al guardar.
    console.error('Error al guardar la muestra:', error);
    // Cierra el bloque `catch`.
    setFeedback('Ocurrió un error al guardar la muestra.', 'error');
  // Asegura que al terminar se desactive el estado de carga.
  } finally {
    // Cierra el bloque `finally`.
    loading.value = false;
  // Cierra la función `submitForm`.
  }
// Línea en blanco antes de la función de borrado.
};
// Declara `deleteSample` como función asíncrona que recibe el id.

// Pide confirmación al usuario antes de eliminar.
const deleteSample = async (sampleId) => {
  // Si la confirmación se cancela, sale de la función.
  if (!confirm('¿Deseas eliminar esta muestra?')) {
    // Línea en blanco que separa el retorno temprano.
    return;
  // Activa el estado de carga previo al borrado.
  }
// Limpia el feedback anterior.

  // Abre bloque `try` para capturar errores.
  loading.value = true;
  // Llama al endpoint DELETE para la muestra indicada.
  resetFeedback();
  // Filtra localmente la lista de muestras eliminando la borrada.
  try {
    // Envía mensaje de éxito “Muestra eliminada.”.
    await api.delete(`samples/${sampleId}/`);
    // Comprueba si la muestra eliminada estaba en edición.
    samples.value = samples.value.filter((sample) => sample.id !== sampleId);
    // Si coincide, reinicia el formulario.
    setFeedback('Muestra eliminada.');
    // Cierra el bloque condicional.
    if (form.id === sampleId) {
      // Cierra el bloque `try`.
      resetForm();
    // Registra los errores de eliminación en consola.
    }
  // Notifica al usuario que no se pudo eliminar la muestra.
  } catch (error) {
    // Cierra el bloque `catch`.
    console.error('Error al eliminar la muestra:', error);
    // Desactiva `loading` independientemente del resultado.
    setFeedback('No se pudo eliminar la muestra.', 'error');
  // Cierra el bloque `finally`.
  } finally {
    // Cierra la función `deleteSample`.
    loading.value = false;
  // Línea en blanco previa al ciclo de vida.
  }
// Usa el hook `onMounted` para ejecutar lógica cuando el componente se monta.
};
// Llama simultáneamente a `loadEquipments` y `loadSamples` usando `Promise.all`.

// Cierra la llamada de `onMounted`.
onMounted(async () => {
  // Cierra el bloque `<script setup>`.
  await Promise.all([loadEquipments(), loadSamples()]);
// Línea en blanco antes de los estilos.
});
// Abre el bloque de estilos con alcance local (`scoped`).
</script>
<!-- Define estilos para la clase `.samples-view`. -->

<!-- Establece el contenedor como grid. -->
<style scoped>
/* Define dos columnas con proporción 1:2. */
.samples-view {
  /* Aplica un espacio de 2 rem entre columnas. */
  display: grid;
  /* Línea en blanco para separar bloques de estilo. */
  grid-template-columns: 1fr 2fr;
  /* Aplica estilos compartidos a `.sample-form` y `.samples-table`. */
  gap: 2rem;
/* Define un fondo blanco. */
}
/* Añade borde gris claro. */

/* Redondea las esquinas con 8px. */
.sample-form,
/* Ajusta el padding interno a 1.5rem. */
.samples-table {
  /* Agrega una sombra suave para relieve. */
  background-color: #ffffff;
  /* Línea en blanco antes del siguiente selector. */
  border: 1px solid #e0e0e0;
  /* Da estilo a los labels dentro del formulario. */
  border-radius: 8px;
  /* Hace que el label use flex en columna. */
  padding: 1.5rem;
  /* Separa los campos con margen inferior. */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
/* Engrosa el texto del label. */
}
/* Línea en blanco para separar reglas. */

/* Estilos para inputs y selects del formulario. */
.sample-form label {
  /* Agrega margen superior entre label y control. */
  display: flex;
  /* Define padding interno cómodo. */
  flex-direction: column;
  /* Aplica borde gris. */
  margin-bottom: 1rem;
  /* Redondea el borde con 4px. */
  font-weight: 600;
/* Ajusta el tamaño de fuente a 0.95rem. */
}
/* Línea en blanco. */

/* Estilos para el contenedor de acciones del formulario. */
.sample-form input,
/* Usa display flex. */
.sample-form select {
  /* Configura separación de 1rem entre botones. */
  margin-top: 0.5rem;
  /* Línea en blanco. */
  padding: 0.5rem;
  /* Estilos generales para todos los botones. */
  border: 1px solid #cbd5e1;
  /* Define padding del botón. */
  border-radius: 4px;
  /* Elimina el borde por defecto. */
  font-size: 0.95rem;
/* Redondea esquinas a 4px. */
}
/* Colorea el fondo azul. */

/* Pone el texto en blanco. */
.form-actions {
  /* Cambia el cursor a puntero para indicar interactividad. */
  display: flex;
  /* Engrosa la tipografía de los botones. */
  gap: 1rem;
/* Línea en blanco. */
}
/* Estilos cuando un botón está deshabilitado. */

/* Cambia el fondo a gris azulado. */
button {
  /* Cambia el cursor a “no permitido” para reflejar inactividad. */
  padding: 0.6rem 1rem;
  /* Línea en blanco. */
  border: none;
  /* Estilos para la tabla dentro de `.samples-table`. */
  border-radius: 4px;
  /* Hace que la tabla ocupe todo el ancho. */
  background-color: #2563eb;
  /* Usa colapso de bordes para unificar líneas. */
  color: #ffffff;
  /* Línea en blanco. */
  cursor: pointer;
  /* Estilos compartidos para celdas de cabecera y datos. */
  font-weight: 600;
/* Define borde alrededor de cada celda. */
}
/* Ajusta el padding interno a 0.75rem. */

/* Alinea el texto a la izquierda. */
button[disabled] {
  /* Línea en blanco. */
  background-color: #94a3b8;
  /* Estilos específicos para las cabeceras de la tabla. */
  cursor: not-allowed;
/* Pinta el fondo de las cabeceras en gris muy claro. */
}
/* Línea en blanco. */

/* Estilos para la celda de acciones. */
.samples-table table {
  /* Usa flexbox para alinear los botones en fila. */
  width: 100%;
  /* Deja un espacio de 0.5rem entre ellos. */
  border-collapse: collapse;
/* Línea en blanco. */
}
/* Especifica que el último botón dentro de `.actions` tenga fondo rojo (eliminar). */

/* Línea en blanco. */
.samples-table th,
/* Estilos para el mensaje de feedback. */
.samples-table td {
  /* Añade margen superior al mensaje. */
  border: 1px solid #e2e8f0;
  /* Engrosa el texto de feedback. */
  padding: 0.75rem;
  /* Línea en blanco. */
  text-align: left;
/* Estilos específicos cuando el feedback es de tipo error. */
}
/* Colorea el texto en rojo para destacar el error. */

/* Línea en blanco. */
.samples-table th {
  /* Estilos cuando el feedback es de tipo éxito. */
  background-color: #f8fafc;
/* Colorea el texto en verde para indicar éxito. */
}
/* Línea en blanco. */

/* Estilos para el párrafo con clase `empty`. */
.actions {
  /* Centra el texto del mensaje vacío. */
  display: flex;
  /* Aplica color gris azulado para tono informativo. */
  gap: 0.5rem;
/* Línea en blanco. */
}
/* Declara una regla `@media` para pantallas menores a 1024px. */

/* Ajusta `.samples-view` a una sola columna en pantallas pequeñas. */
.actions button:last-child {
  /* Cierra la regla `@media`. */
  background-color: #dc2626;
/* Cierra el bloque `<style>`. */
}
/* Línea en blanco que separa las reglas de feedback. */

/* Define estilos para `.feedback`. */
.feedback {
  /* Establece margen superior para el feedback. */
  margin-top: 1rem;
  /* Engrosa el texto del mensaje de feedback. */
  font-weight: 600;
/* Cierra la regla de `.feedback`. */
}
/* Línea en blanco que separa la variante de error. */

/* Define estilos cuando el feedback es de tipo error. */
.feedback.error {
  /* Colorea el texto del error en rojo. */
  color: #dc2626;
/* Cierra la regla `.feedback.error`. */
}
/* Línea en blanco antes de la variante de éxito. */

/* Define la regla de estilo `.feedback.success`. */
.feedback.success {
  /* Colorea el texto de éxito en verde. */
  color: #16a34a;
/* Cierra la regla `.feedback.success`. */
}
/* Línea en blanco que separa la sección del mensaje vacío. */

/* Define estilos para el elemento con clase `empty`. */
.empty {
  /* Centra el texto del mensaje de tabla vacía. */
  text-align: center;
  /* Ajusta el color del mensaje vacío a un gris azulado. */
  color: #64748b;
/* Cierra la regla `.empty`. */
}
/* Línea en blanco previa a la media query. */

/* Declara la media query para pantallas de hasta 1024px. */
@media (max-width: 1024px) {
  /* Abre la regla interna de `.samples-view` dentro de la media query. */
  .samples-view {
    /* Reduce las columnas a una sola en pantallas medianas. */
    grid-template-columns: 1fr;
  /* Cierra la regla interna de `.samples-view`. */
  }
/* Cierra la media query. */
}
/* Cierra el bloque de estilos. */
</style>
