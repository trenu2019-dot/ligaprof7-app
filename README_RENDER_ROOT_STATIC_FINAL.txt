# LigaPro F7 V32.5 — Render Root Static Final

Esta versión corrige definitivamente el error:

- GET / 404
- GET /index.html 404
- HEAD / 404

## Qué cambia

Además de conservar la carpeta `app`, ahora también deja estos archivos directamente en la raíz:

- index.html
- app.js
- styles.css
- manifest.webmanifest
- service-worker.js
- assets

Así Render puede encontrar la página principal aunque el servidor busque en la raíz.

## Subir a GitHub

Sube TODO el contenido de esta carpeta descomprimida a la raíz del repositorio.

En GitHub deben verse en la raíz:

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
- README_RENDER_ROOT_STATIC_FINAL.txt

## Render

Después en Render:

Manual Deploy > Clear build cache & deploy

## Pruebas

Abre:

https://ligaprof7-app.onrender.com/
https://ligaprof7-app.onrender.com/index.html
https://ligaprof7-app.onrender.com/api/health
https://ligaprof7-app.onrender.com/api/version

Si `/api/version` dice `V32.5_RENDER_ROOT_STATIC_FINAL`, Render ya tomó esta versión.
