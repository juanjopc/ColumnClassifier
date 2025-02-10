# ColumnClassifier

## Descripción
ColumnClassifier es una herramienta poderosa que utiliza inteligencia artificial para realizar uniones inteligentes entre columnas de datos. Es ideal para reconciliar columnas de tablas, incluso si contienen errores ortográficos, espacios o formatos inconsistentes.

---

## Instrucciones de uso

1. **Requisito previo:** Asegúrate de tener Python instalado en tu computadora con Windows. Si no lo tienes, puedes instalarlo fácilmente siguiendo los pasos de este tutorial: [Cómo instalar Python en Windows](https://youtu.be/lBjLtoeKu-4).

2. **Descarga el repositorio:**
   - Descarga el repositorio como un archivo ZIP desde GitHub.
   - Descomprime el archivo ZIP en una carpeta de tu elección.

3. **Configurar tus variables de entorno:**
   - Abre el archivo `.env` que se encuentra dentro de la carpeta descomprimida.
   - Añade tus variables en el siguiente formato (recuerda incluir también la ruta del archivo de entrada, el nombre de la hoja y el nombre de la columna):

     ```env
     GEMINI_API_KEY="tu_clave_api_aqui"
     INPUT_FILE="C:/ruta/a/tu/archivo/Excel.xlsx"
     SHEET_NAME="NombreDeLaHoja"
     COLUMN_NAME="NombreDeLaColumna"
     ```

4. **Abrir la terminal (CMD):**
   - Abre el CMD (símbolo del sistema) en tu computadora.
   - Navega hasta la carpeta del repositorio utilizando el comando `cd`. Ejemplo:
     ```bash
     cd C:\Users\TuUsuario\Desktop\ColumnClassifier-main
     ```

5. **Instalar los requerimientos:**
   - Una vez dentro de la carpeta, instala los requerimientos ejecutando el siguiente comando (esto se hace solo una vez):
     ```bash
     pip install -r requirements.txt
     ```

6. **Ejecutar el script:**
   - Haz clic derecho sobre el archivo principal del script (`ColumnClassifier.py`).
   - Selecciona la opción "Ejecutar con Python".

7. **Listo:**
   - Sigue las instrucciones que aparecen en la terminal para realizar la clasificación de la columna de tus archivos de Excel.

---

## Nota
Si encuentras problemas durante la instalación o ejecución, asegúrate de:
- Tener una conexión a Internet estable.
- Haber instalado correctamente todas las dependencias del archivo `requirements.txt`.

---

¡Gracias por usar ColumnClassifier!

