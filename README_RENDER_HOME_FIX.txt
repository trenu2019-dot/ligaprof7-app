LIGAPRO F7 V32.3 - RENDER HOME FIX

Corrige este error en Render:

HEAD / 404
GET / 404

Ahora la ruta principal "/" abre app/index.html.

SUBIR A GITHUB:
1. Descomprime este ZIP.
2. Sube TODO el contenido a la raíz del repositorio.
3. Confirma que en la raíz estén:
   - server.py
   - Dockerfile
   - requirements.txt
   - app
   - backend
   - render.yaml

EN RENDER:
Manual Deploy > Clear build cache & deploy

Después abre:
https://ligaprof7-app.onrender.com

También puedes probar:
https://ligaprof7-app.onrender.com/api/health
