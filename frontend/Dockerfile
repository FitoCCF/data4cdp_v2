# Usa la última versión de Node.js
FROM node:latest

# Define el directorio de trabajo dentro del contenedor
WORKDIR /app/vue_app

# Copia los archivos package.json y package-lock.json para instalar dependencias
COPY vue_app/package*.json ./

# Instala las dependencias de Vue.js
RUN npm install

# Copia el resto del código fuente
COPY vue_app/ ./

# Expone el puerto 5173 para Vite
EXPOSE 5173

# Comando por defecto para iniciar el servidor de desarrollo
CMD ["npm", "run", "dev"]

