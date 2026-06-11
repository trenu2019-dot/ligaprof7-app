LIGAPRO F7 V32.2 - RENDER FIX

Esta versión corrige el error:

python: can't open file '/app/backend/server.py'

Ahora Render arranca desde:

server.py

ubicado en la raíz del repositorio.

SUBIR A GITHUB:
1. Borra los archivos anteriores del repositorio si están mal subidos.
2. Sube TODO el contenido de esta carpeta descomprimida.
3. La raíz del repositorio debe mostrar:
   - server.py
   - Dockerfile
   - requirements.txt
   - app
   - backend
   - render.yaml

EN RENDER:
Runtime: Docker
Build Command: vacío
Start Command: vacío
