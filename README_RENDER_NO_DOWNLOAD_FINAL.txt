# LigaPro F7 V32.6 — Render No Download Final

Esta versión corrige el problema donde Chrome descargaba `index.html` en lugar de abrir la app.

## Error corregido

Al abrir:

https://ligaprof7-app.onrender.com

Chrome descargaba:

index (29).html

## Causa

El servidor estaba mandando la página con encabezado de descarga.

## Corrección

Ahora `/`, `/index.html`, `app.js`, `styles.css`, `manifest.webmanifest`, `service-worker.js` y `assets` se sirven como contenido inline, para abrirse en el navegador.

## Subir a GitHub

Sube todo el contenido de esta carpeta a la raíz del repositorio.

Debe verse:

- server.py
- index.html
- app.js
- styles.css
- manifest.webmanifest
- service-worker.js
- assets
- app
- backend
- Dockerfile
- requirements.txt
- README_RENDER_NO_DOWNLOAD_FINAL.txt

## Render

Después en Render:

Manual Deploy > Clear build cache & deploy

## Prueba

https://ligaprof7-app.onrender.com/api/version

Debe responder:

V32.6_RENDER_NO_DOWNLOAD_FINAL

Luego abre:

https://ligaprof7-app.onrender.com

Ya no debe descargar index.html.
