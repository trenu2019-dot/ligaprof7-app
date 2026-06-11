LIGAPRO F7 V32.4 - RENDER FINAL SIN 404

Esta versión corrige:

GET / 404
GET /index.html 404
HEAD / 404

La ruta principal "/" y "/index.html" sirven directamente app/index.html.

SUBIR A GITHUB:
1. Descomprime este ZIP.
2. Sube TODO el contenido a la raíz del repositorio.
3. En la raíz debes ver:
   - server.py
   - Dockerfile
   - requirements.txt
   - app
   - backend
   - README_RENDER_FINAL_SIN_404.txt

EN RENDER:
Manual Deploy > Clear build cache & deploy

PRUEBAS:
https://ligaprof7-app.onrender.com/
https://ligaprof7-app.onrender.com/index.html
https://ligaprof7-app.onrender.com/api/health
https://ligaprof7-app.onrender.com/api/version

Si /api/version dice V32.4_RENDER_FINAL_SIN_404, Render ya tomó esta versión.
