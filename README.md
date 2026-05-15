# PNG → WebP (lossless) Tkinter App

Simple GUI to convert PNG images to WebP (lossless) and re-compress WebP losslessly.

Requirements
- Python 3.8+
- See `requirements.txt` (install with `pip install -r requirements.txt`)

Run
```
python main.py
```

Notes
- Pillow wheels normally include WebP support on Windows. If you get an error about the WebP encoder, install a Pillow build with WebP or use the `cwebp` command-line tool as fallback.

cwebp (opcional, recomendado)
- Para compresión aún mejor, instala las herramientas de libwebp (`cwebp`). En Windows puedes descargar los binarios desde: https://developers.google.com/speed/webp/download
- Si `cwebp` está en `PATH`, la app lo detectará automáticamente. También puedes seleccionar manualmente `cwebp.exe` desde la interfaz.

Batch / Carpeta
- La app ahora soporta procesamiento por lotes:
	- "Procesar carpeta: PNG → WebP (batch)" — convierte todos los PNG de una carpeta a WebP en modo lossless.
	- "Comprimir carpeta: WebP (batch)" — re-encoda los WebP para intentar mejorar la compresión (usa `cwebp` si está disponible).

Uso
- Ejecuta `python main.py`, selecciona las carpetas de entrada y salida cuando se solicite.

Reemplazo de watermark
- Si las imágenes contienen la marca de agua de Gemini en la esquina inferior derecha, la app puede reemplazarla por tu logo personalizado.
- Coloca el logo en `assets/dupe_logo.png` (ruta relativa a la carpeta del script). El logo debe ser PNG con transparencia preferentemente.
- Activa o desactiva la opción desde la casilla "Imprimir marca de agua (assets\\dupe_logo.png)" en la interfaz.
- Si la casilla está desactivada, la conversión/compresión se hace sin agregar logo.


