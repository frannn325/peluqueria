# Lasmondy Barber

Proyecto educativo inicial para aprender Flask, Jinja, SQLite, HTML, CSS y JavaScript.

## Base de datos

El archivo `barberia.db` se crea automáticamente al iniciar la aplicación. Contiene una única tabla llamada `servicios`, con los servicios y precios iniciales de la barbería.

Las funciones de conexión, creación de la tabla y consulta están en `database.py`. La ruta de Flask consulta esos datos y los envía a Jinja para mostrarlos en la página de inicio.

## Cómo iniciar el proyecto

1. Abrí una terminal dentro de esta carpeta.
2. Creá y activá un entorno virtual (opcional, pero recomendado).
3. Instalá la dependencia:

   ```bash
   pip install -r requirements.txt
   ```

4. Iniciá la aplicación:

   ```bash
   python app.py
   ```

5. Abrí `http://127.0.0.1:5000` en el navegador.

Por ahora solo existe la página de inicio y la tabla de servicios. Las funciones de usuarios, turnos y peluqueros se agregarán en etapas posteriores.
