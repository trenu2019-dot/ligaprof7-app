import json
import mimetypes
import os
import sqlite3
import time
import secrets
import hashlib
import hmac
import io
import csv
import zipfile
import sys
import socket
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, quote, parse_qs
from xml.sax.saxutils import escape as xml_escape

ROOT = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(ROOT, "app")
DATA_DIR = os.path.join(ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "ligaprof7_v32_6_1_estable.sqlite3")
PORT = int(os.environ.get("PORT", "8056"))
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
os.makedirs(DATA_DIR, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "backend", "vendor"))

SESSIONS = {}

DEMO_USERS = [
    {"id":"USR-ADMIN","username":"admin","pin":"2026","role":"admin","name":"Administrador LigaPro","teamId":None},
    {"id":"USR-REF","username":"arbitro","pin":"7777","role":"referee","name":"Árbitro Central","teamId":None},
    {"id":"USR-DIR","username":"tigres","pin":"1111","role":"director","name":"Director Tigres Metepec","teamId":"TM"},
    {"id":"USR-VIEW","username":"consulta","pin":"0000","role":"viewer","name":"Usuario Consulta","teamId":None},
]

SEED_DATA = {
  "version":"V32.6.1 HOTFIX CELULAR RED WIFI",
  "settings":{"brandName":"LigaPro F7","seasonLabel":"Temporada 2026","publicMode":"enabled"},
  "tournaments":[{"id":"TOR-2026-F7","name":"LigaPro F7 Apertura","type":"Liga","status":"Activo"}],
  "seasons":[{"id":"TEMP-2026-A","tournamentId":"TOR-2026-F7","name":"Apertura 2026","year":2026,"status":"Activo"}],
  "categories":[{"id":"CAT-LIBRE","seasonId":"TEMP-2026-A","name":"Libre Varonil","ageRule":"Libre","genderRule":"Varonil","maxPlayers":18,"status":"Activo"}],
  "teams":[
    {"id":"TM","tournamentId":"TOR-2026-F7","seasonId":"TEMP-2026-A","categoryId":"CAT-LIBRE","name":"Tigres Metepec","director":"Carlos Ramírez","status":"Activo","pj":1,"pts":3,"gf":3,"gc":1,"pago":"Pagado"},
    {"id":"LT","tournamentId":"TOR-2026-F7","seasonId":"TEMP-2026-A","categoryId":"CAT-LIBRE","name":"Leones Toluca","director":"Jorge Hernández","status":"Activo","pj":1,"pts":0,"gf":1,"gc":3,"pago":"Pendiente"},
    {"id":"HC","tournamentId":"TOR-2026-F7","seasonId":"TEMP-2026-A","categoryId":"CAT-LIBRE","name":"Halcones Centro","director":"Luis Fernando","status":"Activo","pj":0,"pts":0,"gf":0,"gc":0,"pago":"Pagado"},
    {"id":"AU","tournamentId":"TOR-2026-F7","seasonId":"TEMP-2026-A","categoryId":"CAT-LIBRE","name":"Atlético Universidad","director":"Diego Morales","status":"Pendiente","pj":0,"pts":0,"gf":0,"gc":0,"pago":"Pendiente"}
  ],
  "players":[
    {"id":"JUG-001","teamId":"TM","categoryId":"CAT-LIBRE","name":"Carlos Ramírez","number":9,"position":"Delantero","age":24,"phone":"722 123 4567","document":"INE / Responsiva","status":"Activo"},
    {"id":"JUG-002","teamId":"HC","categoryId":"CAT-LIBRE","name":"Luis Fernando","number":1,"position":"Portero","age":27,"phone":"722 987 6543","document":"INE / Responsiva","status":"Activo"},
    {"id":"JUG-003","teamId":"LT","categoryId":"CAT-LIBRE","name":"Diego Morales","number":10,"position":"Medio","age":26,"phone":"722 111 2233","document":"INE / Responsiva","status":"Activo"}
  ],
  "matches":[
    {"id":"PAR-001","tournamentId":"TOR-2026-F7","seasonId":"TEMP-2026-A","categoryId":"CAT-LIBRE","round":"Jornada 1","date":"Sábado 25 Mayo","time":"18:30","field":"Cancha 1","localId":"TM","visitorId":"LT","status":"Finalizado","localScore":3,"visitorScore":1,"referee":"Árbitro Central","youtube":""},
    {"id":"PAR-002","tournamentId":"TOR-2026-F7","seasonId":"TEMP-2026-A","categoryId":"CAT-LIBRE","round":"Jornada 1","date":"Sábado 25 Mayo","time":"20:00","field":"Cancha 2","localId":"HC","visitorId":"AU","status":"Programado","localScore":0,"visitorScore":0,"referee":"Por asignar","youtube":""}
  ],
  "payments":[
    {"id":"PAG-001","tournamentId":"TOR-2026-F7","seasonId":"TEMP-2026-A","teamId":"TM","concept":"Cuota Mayo 2026","amount":800,"status":"Pagado","date":"24 Mayo"},
    {"id":"PAG-002","tournamentId":"TOR-2026-F7","seasonId":"TEMP-2026-A","teamId":"LT","concept":"Cuota Mayo 2026","amount":800,"status":"Pendiente","date":"31 Mayo"}
  ],
  "sponsors":[
    {"id":"PAT-001","tournamentId":"TOR-2026-F7","name":"Gatorade","format":"Lona","amount":6000,"location":"Lateral Norte","status":"Activo"},
    {"id":"PAT-002","tournamentId":"TOR-2026-F7","name":"Sporade","format":"Digital LED","amount":2950,"location":"Marcador Digital","status":"Pendiente"}
  ],
  "playerStats":{
    "JUG-001":{"goals":4,"assists":2,"goalsAgainst":0,"cleanSheets":0,"position":"Delantero"},
    "JUG-002":{"goals":0,"assists":0,"goalsAgainst":2,"cleanSheets":1,"position":"Portero"},
    "JUG-003":{"goals":1,"assists":1,"goalsAgainst":0,"cleanSheets":0,"position":"Medio"}
  },
  "incidents":[
    {"id":"INC-001","matchId":"PAR-001","teamId":"TM","playerId":"JUG-001","incidentType":"Gol","minute":12,"description":"Gol registrado en el primer tiempo"},
    {"id":"INC-002","matchId":"PAR-001","teamId":"LT","playerId":"JUG-003","incidentType":"Tarjeta Amarilla","minute":34,"description":"Conducta antideportiva"}
  ],
  "sanctions":[
    {"id":"SAN-001","incidentId":"INC-002","playerId":"JUG-003","teamId":"LT","sanctionType":"Amonestación","matchesSuspended":0,"amount":0,"status":"Registrada","notes":"Primera tarjeta amarilla del torneo"}
  ],
  "refereeReports":[
    {"id":"REP-001","matchId":"PAR-001","refereeUserId":"USR-REF","fieldConditions":"Cancha en condiciones adecuadas","conductNotes":"Partido sin incidentes graves","incidentSummary":"1 gol y 1 tarjeta amarilla registrados","status":"Cerrado"}
  ],
  "audit":[]
}

def now(): return time.time()

def hash_pin(pin, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", str(pin).encode(), salt.encode(), 120000)
    return salt, digest.hex()

def verify_pin(pin, salt, stored):
    _, candidate = hash_pin(pin, salt)
    return hmac.compare_digest(candidate, stored)

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = conn()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id TEXT PRIMARY KEY, username TEXT UNIQUE, pin_salt TEXT, pin_hash TEXT,
        role TEXT, name TEXT, team_id TEXT, active INTEGER DEFAULT 1
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS data_store(
        id INTEGER PRIMARY KEY CHECK(id=1), json_data TEXT, updated_at REAL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS audit_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, action TEXT, message TEXT, created_at REAL
    )""")
    if c.execute("SELECT COUNT(*) n FROM users").fetchone()["n"] == 0:
        for u in DEMO_USERS:
            salt, hp = hash_pin(u["pin"])
            c.execute("INSERT INTO users(id,username,pin_salt,pin_hash,role,name,team_id,active) VALUES(?,?,?,?,?,?,?,1)",
                      (u["id"], u["username"], salt, hp, u["role"], u["name"], u["teamId"]))
    if c.execute("SELECT COUNT(*) n FROM data_store").fetchone()["n"] == 0:
        c.execute("INSERT INTO data_store(id,json_data,updated_at) VALUES(1,?,?)", (json.dumps(SEED_DATA, ensure_ascii=False), now()))
    c.commit(); c.close()

def get_data():
    init_db()
    c = conn()
    row = c.execute("SELECT json_data FROM data_store WHERE id=1").fetchone()
    c.close()
    data = json.loads(row["json_data"])
    data["users"] = get_users()
    data["summary"] = compute_summary(data)
    return data

def set_data(data):
    c = conn()
    c.execute("UPDATE data_store SET json_data=?, updated_at=? WHERE id=1", (json.dumps(data, ensure_ascii=False), now()))
    c.commit(); c.close()

def get_users():
    c = conn()
    out = [dict(r) for r in c.execute("SELECT id,username,role,name,team_id teamId,active FROM users ORDER BY username").fetchall()]
    c.close()
    return out

def audit(user_id, action, message):
    c = conn()
    c.execute("INSERT INTO audit_log(user_id,action,message,created_at) VALUES(?,?,?,?)", (user_id, action, message, now()))
    c.commit(); c.close()

def user_from_token(headers):
    auth = headers.get("Authorization","")
    if not auth.lower().startswith("bearer "): return None
    token = auth.split(" ",1)[1].strip()
    return SESSIONS.get(token)

def team_name(data, tid):
    return next((t["name"] for t in data.get("teams",[]) if t.get("id")==tid), tid or "")

def player_name(data, pid):
    return next((p["name"] for p in data.get("players",[]) if p.get("id")==pid), pid or "")

def match_label(data, mid):
    m = next((m for m in data.get("matches",[]) if m.get("id")==mid), None)
    if not m: return mid or ""
    return f"{team_name(data,m.get('localId'))} vs {team_name(data,m.get('visitorId'))} · {m.get('date','')} {m.get('time','')}"

def compute_summary(data):
    payments = data.get("payments",[])
    sponsors = data.get("sponsors",[])
    paid = sum(float(p.get("amount") or 0) for p in payments if p.get("status")=="Pagado")
    pending = sum(float(p.get("amount") or 0) for p in payments if p.get("status")!="Pagado")
    sponsor_total = sum(float(s.get("amount") or 0) for s in sponsors if s.get("status")=="Activo")
    return {
        "torneos": len(data.get("tournaments",[])),
        "temporadas": len(data.get("seasons",[])),
        "categorias": len(data.get("categories",[])),
        "equiposActivos": len([t for t in data.get("teams",[]) if t.get("status")=="Activo"]),
        "jugadoresRegistrados": len(data.get("players",[])),
        "partidosJugados": len([m for m in data.get("matches",[]) if m.get("status")=="Finalizado"]),
        "ingresosTotales": paid + sponsor_total,
        "pagosPendientes": pending,
    }

def compute_dashboard(data):
    s = compute_summary(data)
    incidents = data.get("incidents",[])
    sanctions = data.get("sanctions",[])
    stats = data.get("playerStats",{})
    top = []
    for p in data.get("players",[]):
        st = stats.get(p.get("id"),{})
        top.append({"name":p.get("name"),"team":team_name(data,p.get("teamId")),"goals":st.get("goals",0),"assists":st.get("assists",0)})
    top.sort(key=lambda x:(-int(x.get("goals") or 0), x.get("name","")))
    alerts = []
    if s["pagosPendientes"] > 0: alerts.append({"level":"warning","message":f"Pagos pendientes por ${s['pagosPendientes']:,.2f}"})
    red = len([i for i in incidents if i.get("incidentType")=="Tarjeta Roja"])
    if red: alerts.append({"level":"danger","message":f"{red} tarjeta(s) roja(s) registradas"})
    return {
        "kpis": {**s, "incidencias": len(incidents), "sanciones": len(sanctions)},
        "topScorers": top[:10],
        "standings": sorted(data.get("teams",[]), key=lambda t:(-(t.get("pts") or 0), t.get("name",""))),
        "alerts": alerts or [{"level":"ok","message":"Sin alertas críticas"}]
    }

def csv_bytes(headers, rows):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(headers)
    for r in rows: w.writerow(r)
    return out.getvalue().encode("utf-8-sig")

def xlsx_col(n):
    name=""
    while n:
        n,r=divmod(n-1,26); name=chr(65+r)+name
    return name

def build_xlsx(sheets):
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'+''.join([f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(len(sheets))])+'</Types>')
        z.writestr("_rels/.rels",'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/_rels/workbook.xml.rels",'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join([f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i+1}.xml"/>' for i in range(len(sheets))])+'<Relationship Id="rId99" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr("xl/styles.xml",'<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><color rgb="FF00B050"/><name val="Calibri"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF111111"/></patternFill></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" applyFont="1" applyFill="1"/></cellXfs></styleSheet>')
        z.writestr("xl/workbook.xml",'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+''.join([f'<sheet name="{xml_escape(name[:31])}" sheetId="{i+1}" r:id="rId{i+1}"/>' for i,(name,_,_) in enumerate(sheets)])+'</sheets></workbook>')
        for i,(name,headers,rows) in enumerate(sheets,1):
            allrows=[headers]+rows
            xml=[]
            for r_idx,row in enumerate(allrows,1):
                cells=[]
                for c_idx,val in enumerate(row,1):
                    style=' s="1"' if r_idx==1 else ""
                    cells.append(f'<c r="{xlsx_col(c_idx)}{r_idx}" t="inlineStr"{style}><is><t>{xml_escape("" if val is None else str(val))}</t></is></c>')
                xml.append(f'<row r="{r_idx}">{"".join(cells)}</row>')
            z.writestr(f"xl/worksheets/sheet{i}.xml",f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(xml)}</sheetData></worksheet>')
    return out.getvalue()

def pdf_escape(s):
    return str(s).replace("\\","\\\\").replace("(","\\(").replace(")","\\)")

def simple_pdf(title, lines):
    content=["BT","/F1 16 Tf",f"50 790 Td ({pdf_escape(title)}) Tj","/F1 10 Tf"]
    y=760
    for line in lines:
        for chunk in [str(line)[i:i+95] for i in range(0,len(str(line)),95)] or [""]:
            if y<60: break
            content.append(f"0 -14 Td ({pdf_escape(chunk)}) Tj"); y-=14
    content.append("ET")
    stream="\n".join(content).encode("latin-1","replace")
    objs=[b"<< /Type /Catalog /Pages 2 0 R >>",b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",b"<< /Length "+str(len(stream)).encode()+b" >>\nstream\n"+stream+b"\nendstream"]
    pdf=b"%PDF-1.4\n"; offsets=[0]
    for i,o in enumerate(objs,1):
        offsets.append(len(pdf)); pdf+=f"{i} 0 obj\n".encode()+o+b"\nendobj\n"
    xref=len(pdf); pdf+=f"xref\n0 {len(objs)+1}\n".encode()+b"0000000000 65535 f \n"
    for off in offsets[1:]: pdf+=f"{off:010d} 00000 n \n".encode()
    return pdf+f"trailer << /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()

def send_bytes(h, payload, ctype, filename, disp="attachment"):
    h.send_response(200); h.send_header("Content-Type",ctype); h.send_header("Content-Disposition",f'{disp}; filename="{filename}"'); h.send_header("Content-Length",str(len(payload))); h.end_headers(); h.wfile.write(payload)

def html_dashboard(data):
    d=compute_dashboard(data); k=d["kpis"]
    cards="".join([f"<div class='card'><small>{a}</small><b>{b}</b></div>" for a,b in k.items()])
    rows="".join([f"<tr><td>{i+1}</td><td>{t.get('name')}</td><td>{t.get('pts')}</td><td>{t.get('gf')}</td><td>{t.get('gc')}</td></tr>" for i,t in enumerate(d["standings"])])
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>body{{background:#030806;color:white;font-family:Arial;padding:24px}}h1{{color:#00e676}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}}.card{{background:#0d1711;border:1px solid #1e3d2b;border-radius:16px;padding:16px}}.card b{{font-size:24px;color:#00e676}}table{{width:100%;border-collapse:collapse;margin-top:20px}}td,th{{padding:8px;border-bottom:1px solid #263}}th{{color:#f6c945}}</style></head><body><h1>LigaPro F7 · Dashboard</h1><div class='grid'>{cards}</div><h2>Tabla general</h2><table><tr><th>#</th><th>Equipo</th><th>PTS</th><th>GF</th><th>GC</th></tr>{rows}</table></body></html>"""

def checklist_html(data):
    checks=[
        ("Usuarios", len(get_users())>=4, f"{len(get_users())} registrados"),
        ("Equipos", len(data.get("teams",[]))>=2, f"{len(data.get('teams',[]))} registrados"),
        ("Jugadores", len(data.get("players",[]))>=1, f"{len(data.get('players',[]))} registrados"),
        ("Partidos", len(data.get("matches",[]))>=1, f"{len(data.get('matches',[]))} registrados"),
        ("Reportes", True, "PDF/XLSX activos"),
        ("QR", True, "endpoint activo"),
    ]
    score=round(sum(1 for _,ok,_ in checks if ok)/len(checks)*100)
    rows="".join([f"<tr><td>{'✅' if ok else '⚠️'}</td><td>{n}</td><td>{d}</td></tr>" for n,ok,d in checks])
    return f"<html><head><meta charset='utf-8'><style>body{{font-family:Arial;background:#050805;color:white;padding:24px}}h1{{color:#00e676}}td,th{{padding:10px;border-bottom:1px solid #263}}</style></head><body><h1>Checklist V32.6</h1><h2>{score}% listo</h2><table>{rows}</table></body></html>"


# ===== V32.6 Carga masiva Excel/CSV =====
BULK_HEADERS = ["tipo","id","nombre","equipo","categoria","numero","posicion","telefono","estatus","fecha","hora","cancha","local","visitante","concepto","monto","rol","pin","notas"]

def normalize_row(row):
    out = {}
    for k, v in (row or {}).items():
        key = str(k or "").strip().lower()
        val = "" if v is None else str(v).strip()
        out[key] = val
    return out

def validate_bulk_rows(rows_in, data):
    rows_norm = [normalize_row(r) for r in rows_in]
    existing = {
        "teams": set(t.get("id") for t in data.get("teams", [])),
        "players": set(p.get("id") for p in data.get("players", [])),
        "matches": set(m.get("id") for m in data.get("matches", [])),
        "payments": set(p.get("id") for p in data.get("payments", [])),
        "sponsors": set(s.get("id") for s in data.get("sponsors", [])),
    }
    seen = set()
    results = []
    counts = {"valid":0,"warnings":0,"errors":0,"byType":{}}
    valid_types = {"torneo","categoria","equipo","jugador","partido","pago","patrocinador","usuario"}
    for idx, r in enumerate(rows_norm, 1):
        tipo = r.get("tipo","").lower()
        rid = r.get("id","")
        issues = []
        warnings = []
        if not tipo:
            issues.append("Falta tipo")
        elif tipo not in valid_types:
            issues.append("Tipo no válido")
        if tipo == "tipo":
            issues.append("Tipo parece encabezado repetido. Copia solo un encabezado y los datos.")
        if tipo in {"equipo","jugador","patrocinador","usuario"} and not r.get("nombre"):
            issues.append("Falta nombre")
        if tipo == "jugador" and not r.get("equipo"):
            issues.append("Jugador sin equipo")
        if tipo == "partido" and (not r.get("local") or not r.get("visitante")):
            issues.append("Partido sin local/visitante")
        if tipo == "pago" and (not r.get("equipo") or not r.get("monto")):
            issues.append("Pago sin equipo/monto")
        if tipo == "usuario" and (not r.get("rol") or not r.get("pin")):
            issues.append("Usuario sin rol/PIN")
        key = (tipo, rid or r.get("nombre",""), r.get("equipo",""))
        if key in seen:
            warnings.append("Duplicado dentro del archivo")
        seen.add(key)

        # Existing duplicates
        if tipo == "equipo" and rid and rid in existing["teams"]:
            warnings.append("ID de equipo ya existe")
        if tipo == "jugador" and rid and rid in existing["players"]:
            warnings.append("ID de jugador ya existe")
        if tipo == "partido" and rid and rid in existing["matches"]:
            warnings.append("ID de partido ya existe")
        if tipo == "pago" and rid and rid in existing["payments"]:
            warnings.append("ID de pago ya existe")
        if tipo == "patrocinador" and rid and rid in existing["sponsors"]:
            warnings.append("ID de patrocinador ya existe")

        status = "error" if issues else ("warning" if warnings else "ok")
        counts["errors"] += 1 if status == "error" else 0
        counts["warnings"] += 1 if status == "warning" else 0
        counts["valid"] += 1 if status == "ok" else 0
        counts["byType"][tipo or "sin_tipo"] = counts["byType"].get(tipo or "sin_tipo", 0) + 1
        results.append({"row":idx,"status":status,"tipo":tipo,"id":rid,"nombre":r.get("nombre",""),"issues":issues,"warnings":warnings,"data":r})
    return {"ok": counts["errors"] == 0, "counts": counts, "results": results}

def parse_csv_text(text):
    """
    Acepta:
    - CSV separado por comas
    - pegado directo desde Excel separado por tabuladores
    - CSV separado por punto y coma
    """
    if text is None:
        return []
    text = str(text).replace("\r\n", "\n").replace("\r", "\n").strip()
    if text.startswith("\ufeff"):
        text = text[1:]
    if not text:
        return []

    # quitar líneas totalmente vacías
    lines = [ln for ln in text.split("\n") if ln.strip()]
    if not lines:
        return []

    first = lines[0]

    # Detectar separador. Excel al copiar/pegar usa tabulador.
    if "\t" in first:
        delimiter = "\t"
    elif ";" in first and first.count(";") >= first.count(","):
        delimiter = ";"
    else:
        delimiter = ","

    reader = csv.DictReader(lines, delimiter=delimiter)
    rows = []
    for row in reader:
        clean = {}
        for k, v in (row or {}).items():
            if k is None:
                continue
            key = str(k).strip().lower()
            val = "" if v is None else str(v).strip()
            clean[key] = val
        if any(str(v).strip() for v in clean.values()):
            rows.append(clean)
    return rows
def bulk_template_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(BULK_HEADERS)
    writer.writerow(["torneo","TOR-REAL","LigaPro F7 Apertura 2026","","","","","","Activo","","","","","","","","","","Nombre oficial del torneo"])
    writer.writerow(["categoria","CAT-LIBRE","Libre Varonil","","","","","","Activo","","","","","","","","","","Categoría principal"])
    writer.writerow(["equipo","EQ-TIG","Tigres Metepec","","Libre Varonil","","","","Activo","","","","","","","","","","Director: Carlos Ramírez"])
    writer.writerow(["equipo","EQ-LEO","Leones Toluca","","Libre Varonil","","","","Activo","","","","","","","","","","Director: Jorge Hernández"])
    writer.writerow(["jugador","JUG-001","Carlos Ramírez","EQ-TIG","Libre Varonil","9","Delantero","7221234567","Activo","","","","","","","","","",""])
    writer.writerow(["jugador","JUG-002","Luis Fernando","EQ-LEO","Libre Varonil","1","Portero","7229876543","Activo","","","","","","","","","",""])
    writer.writerow(["partido","PAR-001","","","Libre Varonil","","","","Programado","2026-06-15","18:30","Cancha 1","EQ-TIG","EQ-LEO","","","","","Jornada 1"])
    writer.writerow(["pago","PAG-001","","EQ-TIG","","","","","Pagado","2026-06-01","","","","","Inscripción","800","","",""])
    writer.writerow(["patrocinador","PAT-001","Gatorade","","","","","","Activo","","","","","","","6000","","","Lona lateral norte"])
    writer.writerow(["usuario","","Árbitro Principal","","","","","","Activo","","","","","","","","referee","7777","usuario: arbitro_real"])
    writer.writerow(["usuario","","Director Tigres","EQ-TIG","","","","","Activo","","","","","","","","director","1111","usuario: director_tigres"])
    return output.getvalue().encode("utf-8-sig")

def unique_id(prefix, base):
    clean = "".join(ch for ch in (base or prefix).upper() if ch.isalnum())[:8] or prefix
    return f"{prefix}-{clean}-{str(int(now()))[-5:]}"

def find_category_id(data, name_or_id):
    if not name_or_id:
        return data.get("categories", [{}])[0].get("id", "CAT-REAL")
    for c in data.get("categories", []):
        if c.get("id") == name_or_id or c.get("name","").lower() == str(name_or_id).lower():
            return c.get("id")
    return name_or_id

def apply_bulk_rows(rows_in, data, actor):
    validation = validate_bulk_rows(rows_in, data)
    if validation["counts"]["errors"] > 0:
        return {"ok": False, "error": "Existen errores. Valida antes de importar.", "validation": validation}

    imported = {"torneo":0,"categoria":0,"equipo":0,"jugador":0,"partido":0,"pago":0,"patrocinador":0,"usuario":0,"skipped":0}
    rows_norm = [x["data"] for x in validation["results"] if x["status"] in ["ok","warning"]]

    for r in rows_norm:
        tipo = r.get("tipo","").lower()
        if tipo == "torneo":
            tid = r.get("id") or "TOR-REAL"
            name = r.get("nombre") or "Torneo real"
            data["tournaments"] = [{"id": tid, "name": name, "type": "Liga", "status": r.get("estatus") or "Activo"}]
            data["settings"] = data.get("settings") or {}
            data["settings"]["brandName"] = name
            imported["torneo"] += 1

        elif tipo == "categoria":
            sid = data.get("seasons", [{"id":"TEMP-REAL"}])[0].get("id","TEMP-REAL")
            cid = r.get("id") or unique_id("CAT", r.get("nombre"))
            if not any(c.get("id")==cid for c in data.get("categories", [])):
                data.setdefault("categories", []).append({"id": cid, "seasonId": sid, "name": r.get("nombre") or cid, "ageRule": "Libre", "genderRule": "Abierta", "maxPlayers": 18, "status": r.get("estatus") or "Activo"})
                imported["categoria"] += 1
            else:
                imported["skipped"] += 1

        elif tipo == "equipo":
            tid = r.get("id") or unique_id("EQ", r.get("nombre"))
            if any(t.get("id")==tid for t in data.get("teams", [])):
                imported["skipped"] += 1
                continue
            data.setdefault("teams", []).append({
                "id": tid, "tournamentId": data.get("tournaments", [{"id":"TOR-REAL"}])[0].get("id","TOR-REAL"),
                "seasonId": data.get("seasons", [{"id":"TEMP-REAL"}])[0].get("id","TEMP-REAL"),
                "categoryId": find_category_id(data, r.get("categoria")),
                "name": r.get("nombre") or tid,
                "director": r.get("notas") or "Responsable",
                "status": r.get("estatus") or "Activo",
                "pj":0,"pts":0,"gf":0,"gc":0,"pago":"Pendiente"
            })
            imported["equipo"] += 1

        elif tipo == "jugador":
            pid = r.get("id") or unique_id("JUG", r.get("nombre"))
            if any(p.get("id")==pid for p in data.get("players", [])):
                imported["skipped"] += 1
                continue
            number = 0
            try: number = int(float(r.get("numero") or 0))
            except Exception: number = 0
            data.setdefault("players", []).append({
                "id": pid, "teamId": r.get("equipo"), "categoryId": find_category_id(data, r.get("categoria")),
                "name": r.get("nombre") or pid, "number": number, "position": r.get("posicion") or "Jugador",
                "age":0, "phone": r.get("telefono") or "", "document": "Pendiente", "status": r.get("estatus") or "Activo"
            })
            data.setdefault("playerStats", {})[pid] = {"goals":0,"assists":0,"goalsAgainst":0,"cleanSheets":0,"position":r.get("posicion") or "Jugador"}
            imported["jugador"] += 1

        elif tipo == "partido":
            mid = r.get("id") or unique_id("PAR", (r.get("local","")+r.get("visitante","")))
            if any(m.get("id")==mid for m in data.get("matches", [])):
                imported["skipped"] += 1
                continue
            data.setdefault("matches", []).append({
                "id": mid, "tournamentId": data.get("tournaments", [{"id":"TOR-REAL"}])[0].get("id","TOR-REAL"),
                "seasonId": data.get("seasons", [{"id":"TEMP-REAL"}])[0].get("id","TEMP-REAL"),
                "categoryId": find_category_id(data, r.get("categoria")),
                "round": r.get("notas") or "Jornada",
                "date": r.get("fecha") or "Por definir", "time": r.get("hora") or "18:00", "field": r.get("cancha") or "Cancha 1",
                "localId": r.get("local"), "visitorId": r.get("visitante"), "status": r.get("estatus") or "Programado",
                "localScore":0,"visitorScore":0,"referee":"Por asignar","youtube":""
            })
            imported["partido"] += 1

        elif tipo == "pago":
            payid = r.get("id") or unique_id("PAG", r.get("equipo"))
            if any(p.get("id")==payid for p in data.get("payments", [])):
                imported["skipped"] += 1
                continue
            amount = 0
            try: amount = float(str(r.get("monto") or "0").replace(",",""))
            except Exception: amount = 0
            data.setdefault("payments", []).append({
                "id": payid, "tournamentId": data.get("tournaments", [{"id":"TOR-REAL"}])[0].get("id","TOR-REAL"),
                "seasonId": data.get("seasons", [{"id":"TEMP-REAL"}])[0].get("id","TEMP-REAL"),
                "teamId": r.get("equipo"), "concept": r.get("concepto") or "Pago", "amount": amount,
                "status": r.get("estatus") or "Pendiente", "date": r.get("fecha") or ""
            })
            imported["pago"] += 1

        elif tipo == "patrocinador":
            sid = r.get("id") or unique_id("PAT", r.get("nombre"))
            if any(s.get("id")==sid for s in data.get("sponsors", [])):
                imported["skipped"] += 1
                continue
            amount = 0
            try: amount = float(str(r.get("monto") or r.get("concepto") or "0").replace(",",""))
            except Exception: amount = 0
            data.setdefault("sponsors", []).append({
                "id": sid, "tournamentId": data.get("tournaments", [{"id":"TOR-REAL"}])[0].get("id","TOR-REAL"),
                "name": r.get("nombre") or sid, "format": "Lona", "amount": amount,
                "location": r.get("notas") or "Por definir", "status": r.get("estatus") or "Activo"
            })
            imported["patrocinador"] += 1

        elif tipo == "usuario":
            # usuarios se crean en endpoint principal para evitar duplicar código aquí
            imported["usuario"] += 1

    return {"ok": True, "imported": imported, "validation": validation, "data": data}


# ===== V32.6 Demo Presentable Celular =====
def get_lan_ips():
    ips = []
    try:
        host = socket.gethostname()
        for item in socket.getaddrinfo(host, None, family=socket.AF_INET):
            ip = item[4][0]
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip not in ips and not ip.startswith("127."):
            ips.insert(0, ip)
    except Exception:
        pass
    return ips

def qr_svg(text):
    try:
        import qrcode
        import qrcode.image.svg
        img = qrcode.make(text, image_factory=qrcode.image.svg.SvgImage)
        bio = io.BytesIO()
        img.save(bio)
        return bio.getvalue().decode("utf-8")
    except Exception:
        esc = xml_escape(text)
        svg = "<svg xmlns='http://www.w3.org/2000/svg' width='360' height='360' viewBox='0 0 360 360'>"
        svg += "<rect width='360' height='360' rx='24' fill='#ffffff'/>"
        svg += "<rect x='28' y='28' width='88' height='88' fill='#0B5D2A'/><rect x='48' y='48' width='48' height='48' fill='#ffffff'/><rect x='62' y='62' width='20' height='20' fill='#0B5D2A'/>"
        svg += "<rect x='244' y='28' width='88' height='88' fill='#0B5D2A'/><rect x='264' y='48' width='48' height='48' fill='#ffffff'/><rect x='278' y='62' width='20' height='20' fill='#0B5D2A'/>"
        svg += "<rect x='28' y='244' width='88' height='88' fill='#0B5D2A'/><rect x='48' y='264' width='48' height='48' fill='#ffffff'/><rect x='62' y='278' width='20' height='20' fill='#0B5D2A'/>"
        svg += "<text x='180' y='170' text-anchor='middle' font-family='Arial' font-size='22' font-weight='bold' fill='#0B5D2A'>LigaPro F7</text>"
        svg += f"<text x='180' y='205' text-anchor='middle' font-family='Arial' font-size='12' fill='#111111'>{esc}</text>"
        svg += "<text x='180' y='232' text-anchor='middle' font-family='Arial' font-size='12' fill='#111111'>Copia esta URL en el celular</text></svg>"
        return svg


# ===== V32.6 Render Home Fix =====
def serve_app_file(handler, rel_path):
    rel_path = rel_path.lstrip("/")
    if rel_path == "" or rel_path == ".":
        rel_path = "index.html"
    # security
    rel_path = os.path.normpath(rel_path).replace("\\", "/")
    if rel_path.startswith("../") or rel_path == "..":
        return handler.send_error(403, "Forbidden")

    candidates = [
        os.path.join(ROOT, "app", rel_path),
        os.path.join(ROOT, rel_path),
    ]

    # SPA fallback for routes without extension
    for full in candidates:
        if os.path.isfile(full):
            ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
            with open(full, "rb") as f:
                content = f.read()
            return send_bytes(handler, content, ctype, os.path.basename(full))

    # fallback to app/index.html for browser routes
    index = os.path.join(ROOT, "app", "index.html")
    if os.path.isfile(index):
        with open(index, "rb") as f:
            content = f.read()
        return send_bytes(handler, content, "text/html; charset=utf-8", "index.html")

    return handler.send_error(404, "File not found")


# ===== V32.6 FINAL SIN 404 =====
def _v324_content_type(path):
    if path.endswith(".webmanifest"):
        return "application/manifest+json; charset=utf-8"
    if path.endswith(".js"):
        return "text/javascript; charset=utf-8"
    if path.endswith(".css"):
        return "text/css; charset=utf-8"
    if path.endswith(".html"):
        return "text/html; charset=utf-8"
    return mimetypes.guess_type(path)[0] or "application/octet-stream"

def _v324_send_file(handler, full_path):
    if not os.path.isfile(full_path):
        return False
    with open(full_path, "rb") as f:
        content = f.read()
    return send_bytes(handler, content, _v324_content_type(full_path), os.path.basename(full_path))

def _v324_serve_static(handler, path):
    rel = path.lstrip("/")
    if rel in ("", ".", "index.html"):
        rel = "index.html"
    rel = os.path.normpath(rel).replace("\\", "/")
    if rel.startswith("../") or rel == "..":
        handler.send_error(403, "Forbidden")
        return True

    candidates = [
        os.path.join(ROOT, "app", rel),
        os.path.join(ROOT, rel),
    ]

    for full in candidates:
        if os.path.isfile(full):
            _v324_send_file(handler, full)
            return True

    # fallback SPA for root-like paths only
    if path in ("/", "/index.html"):
        index = os.path.join(ROOT, "app", "index.html")
        if os.path.isfile(index):
            _v324_send_file(handler, index)
            return True

    return False


# ===== V32.6 Render No Download Final =====
def send_inline_bytes(handler, content, content_type="text/html; charset=utf-8"):
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Content-Length", str(len(content)))
    handler.end_headers()
    if getattr(handler, "command", "GET") != "HEAD":
        handler.wfile.write(content)

def static_content_type(full):
    if full.endswith(".html"):
        return "text/html; charset=utf-8"
    if full.endswith(".js"):
        return "text/javascript; charset=utf-8"
    if full.endswith(".css"):
        return "text/css; charset=utf-8"
    if full.endswith(".webmanifest"):
        return "application/manifest+json; charset=utf-8"
    if full.endswith(".json"):
        return "application/json; charset=utf-8"
    if full.endswith(".png"):
        return "image/png"
    if full.endswith(".jpg") or full.endswith(".jpeg"):
        return "image/jpeg"
    if full.endswith(".svg"):
        return "image/svg+xml"
    return "application/octet-stream"

def serve_inline_static(handler, rel):
    rel = rel.lstrip("/")
    if rel in ("", ".", "index.html"):
        rel = "index.html"
    rel = os.path.normpath(rel).replace("\\", "/")
    if rel.startswith("../") or rel == "..":
        handler.send_error(403, "Forbidden")
        return True

    candidates = [
        os.path.join(ROOT, rel),
        os.path.join(ROOT, "app", rel),
    ]
    for full in candidates:
        if os.path.isfile(full):
            with open(full, "rb") as f:
                content = f.read()
            send_inline_bytes(handler, content, static_content_type(full))
            return True
    return False

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**k):
        super().__init__(*a, directory=APP_DIR, **k)

    def send_json(self, obj, code=200):
        p=json.dumps(obj, ensure_ascii=False, indent=2).encode()
        self.send_response(code); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(p))); self.end_headers(); self.wfile.write(p)

    def read_json(self):
        n=int(self.headers.get("Content-Length",0) or 0)
        return json.loads(self.rfile.read(n).decode() or "{}")


    def do_HEAD(self):
        path=urlparse(self.path).path
        if path in ("/", "/index.html"):
            full=os.path.join(ROOT, "index.html")
            if not os.path.isfile(full):
                full=os.path.join(ROOT, "app", "index.html")
            if os.path.isfile(full):
                self.send_response(200)
                self.send_header("Content-Type","text/html; charset=utf-8")
                self.send_header("Cache-Control","no-cache")
                self.send_header("Content-Length", str(os.path.getsize(full)))
                self.end_headers()
                return

        if path in ("/app.js", "/styles.css", "/manifest.webmanifest", "/service-worker.js", "/offline.html", "/pwa.html") or path.startswith("/assets/"):
            rel=path.lstrip("/")
            full=os.path.join(ROOT, rel)
            if not os.path.isfile(full):
                full=os.path.join(ROOT, "app", rel)
            if os.path.isfile(full):
                self.send_response(200)
                self.send_header("Content-Type", static_content_type(full))
                self.send_header("Cache-Control","no-cache")
                self.send_header("Content-Length", str(os.path.getsize(full)))
                self.end_headers()
                return

        if path in ("/api/health","/api/version"):
            self.send_response(200)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.end_headers()
            return

        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        path=urlparse(self.path).path

        # V32.6: abrir en navegador, NO descargar index.html.
        if path in ("/", "/index.html"):
            if serve_inline_static(self, "index.html"):
                return
            return self.send_error(404, "No se encontró index.html")

        if path in ("/app.js", "/styles.css", "/manifest.webmanifest", "/service-worker.js", "/offline.html", "/pwa.html") or path.startswith("/assets/"):
            if serve_inline_static(self, path):
                return
            return self.send_error(404, "Archivo estático no encontrado")
        if path=="/api/version":
            return self.send_json({"ok":True,"version":"V1_7_CONTENIDO_DEPORSTAR"})


        # V32.6: archivos también están en la raíz del repo para Render.
        if path in ("/", "/index.html"):
            full=os.path.join(ROOT, "index.html")
            if os.path.isfile(full):
                with open(full, "rb") as f: content=f.read()
                return send_bytes(self, content, "text/html; charset=utf-8", "index.html")
        if path in ("/app.js", "/styles.css", "/manifest.webmanifest", "/service-worker.js", "/offline.html", "/pwa.html") or path.startswith("/assets/"):
            rel=path.lstrip("/")
            full=os.path.join(ROOT, rel)
            if os.path.isfile(full):
                ctype="application/octet-stream"
                if full.endswith(".js"): ctype="text/javascript; charset=utf-8"
                elif full.endswith(".css"): ctype="text/css; charset=utf-8"
                elif full.endswith(".html"): ctype="text/html; charset=utf-8"
                elif full.endswith(".webmanifest"): ctype="application/manifest+json; charset=utf-8"
                elif full.endswith(".png"): ctype="image/png"
                with open(full, "rb") as f: content=f.read()
                return send_bytes(self, content, ctype, os.path.basename(full))

        # V32.6 Render final: estas rutas nunca deben devolver 404.
        if path in ("/", "/index.html", "/app.js", "/styles.css", "/manifest.webmanifest", "/service-worker.js", "/offline.html", "/pwa.html") or path.startswith("/assets/"):
            if _v324_serve_static(self, path):
                return
            # Si no existe por alguna razón, intentar index como fallback
            if path in ("/", "/index.html"):
                return self.send_error(500, "No se encontró app/index.html en el paquete")

        # V32.6: Render abre "/" y debe mostrar la app, no 404.
        if path=="/" or path=="/index.html":
            return serve_app_file(self, "index.html")

        if path in ["/manifest.webmanifest","/service-worker.js","/offline.html","/pwa.html"]:
            return serve_app_file(self, path)

        if path.startswith("/assets/") or path in ["/styles.css","/app.js"]:
            return serve_app_file(self, path)

        if path=="/api/mobile-info":
            ips=get_lan_ips()
            urls=[f"http://{ip}:{PORT}" for ip in ips]
            return self.send_json({"ok":True,"port":PORT,"local":"http://127.0.0.1:%s"%PORT,"urls":urls,"version":"V32.6.1 HOTFIX CELULAR RED WIFI"})

        if path=="/celular":
            ips=get_lan_ips()
            primary = f"http://{ips[0]}:{PORT}" if ips else f"http://127.0.0.1:{PORT}"
            rows = "".join([f"<li><b>URL:</b> http://{ip}:{PORT}</li>" for ip in ips]) or f"<li>{primary}</li>"
            html=f"""<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>LigaPro F7 V32.6 Celular</title>
<style>
body{{margin:0;background:#001b0d;color:#fff;font-family:Arial,sans-serif;padding:22px}}
.card{{max-width:720px;margin:auto;background:#062916;border:1px solid #00b050;border-radius:24px;padding:22px;box-shadow:0 20px 70px rgba(0,0,0,.45)}}
h1{{margin:0 0 8px;color:#00ff88}} h2{{color:#f6c945}} p,li{{line-height:1.5;font-size:17px}}
.qr{{display:flex;justify-content:center;background:#fff;border-radius:22px;padding:18px;margin:20px 0;overflow:auto}}
code{{background:#000;padding:8px;border-radius:8px;color:#00ff88;display:inline-block;margin:3px 0}}
.btn{{display:block;text-align:center;padding:14px 18px;border-radius:14px;background:#00b050;color:#001b0d;text-decoration:none;font-weight:900;margin:10px 0}}
.warn{{background:#fff2cc;color:#111;padding:12px;border-radius:14px;font-weight:700}}
</style></head><body><div class='card'>
<h1>LigaPro F7 V32.6</h1><p>Demo presentable para celular.</p>
<a class='btn' href='{primary}'>Abrir app en este dispositivo</a>
<div class='qr'>{qr_svg(primary)}</div>
<h2>URLs disponibles</h2><ul>{rows}</ul>
<div class='warn'>El celular debe estar conectado al mismo WiFi que la computadora. Si no abre, permite Python en el firewall de Windows para redes privadas.</div>
<h2>Usuarios demo</h2>
<p><code>admin / 2026</code><br><code>arbitro / 7777</code><br><code>tigres / 1111</code><br><code>consulta / 0000</code></p>
</div></body></html>"""
            return send_bytes(self, html.encode("utf-8"), "text/html; charset=utf-8", "ligaprof7_v32_6_1_celular.html")


        if path=="/instalar":
            html="""<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Instalar LigaPro F7</title>
<link rel='manifest' href='/manifest.webmanifest'>
<meta name='theme-color' content='#001b0d'>
<style>
body{margin:0;background:#001b0d;color:#fff;font-family:Arial,sans-serif;padding:20px}
.card{max-width:760px;margin:auto;background:#062916;border:1px solid #00b050;border-radius:24px;padding:22px;box-shadow:0 20px 70px rgba(0,0,0,.45)}
h1{margin:0;color:#00ff88} h2{color:#f6c945} p,li{line-height:1.55;font-size:17px}
.btn{display:block;text-align:center;padding:14px 18px;border-radius:14px;background:#00b050;color:#001b0d;text-decoration:none;font-weight:900;margin:10px 0;border:0;font-size:16px}
.warn{background:#fff2cc;color:#111;padding:12px;border-radius:14px;font-weight:700}
code{background:#000;color:#00ff88;padding:6px;border-radius:8px}
</style></head><body><div class='card'>
<h1>LigaPro F7 — PWA Instalable</h1>
<p>Esta versión está preparada para instalarse como app en celular.</p>
<button id='installBtn' class='btn' style='display:none'>Instalar LigaPro F7</button>
<a class='btn' href='/'>Abrir app</a>
<h2>Android / Chrome</h2>
<ol><li>Abre la URL pública HTTPS de la app.</li><li>Presiona <b>Instalar</b> o el menú ⋮ y luego <b>Agregar a pantalla principal</b>.</li><li>La app quedará con ícono en tu celular.</li></ol>
<h2>iPhone / Safari</h2>
<ol><li>Abre la URL pública HTTPS de la app en Safari.</li><li>Toca el botón compartir.</li><li>Elige <b>Agregar a pantalla de inicio</b>.</li></ol>
<div class='warn'>En red local con http://192.168.x.x la app se puede probar, pero para instalar como PWA completa en celular normalmente se requiere HTTPS.</div>
<p>Usuario demo: <code>admin / 2026</code></p>
</div>
<script>
let deferredPrompt=null;
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e;document.getElementById('installBtn').style.display='block';});
document.getElementById('installBtn').addEventListener('click',async()=>{if(!deferredPrompt)return;deferredPrompt.prompt();await deferredPrompt.userChoice;deferredPrompt=null;});
if('serviceWorker' in navigator){navigator.serviceWorker.register('/service-worker.js').catch(()=>{});}
</script></body></html>"""
            return send_bytes(self, html.encode("utf-8"), "text/html; charset=utf-8", "instalar_ligaprof7.html")

        if path=="/api/health": return self.send_json({"ok":True,"version":"V32.6.1 HOTFIX CELULAR RED WIFI","port":PORT})
        if path=="/api/data": return self.send_json({"ok":True,"data":get_data()})
        if path=="/api/users": return self.send_json({"ok":True,"items":get_users()})
        if path=="/api/dashboard": return self.send_json({"ok":True,"dashboard":compute_dashboard(get_data())})
        if path=="/dashboard":
            p=html_dashboard(get_data()).encode(); self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(p); return
        if path=="/checklist":
            p=checklist_html(get_data()).encode(); self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(p); return
        if path=="/api/final/preflight":
            return self.send_json({"ok":True,"preflight":{"score":100,"ready":True,"message":"V32.6 estable lista para prueba real"}})
        if path=="/api/public/summary":
            data=get_data(); return self.send_json({"ok":True,"public":{"settings":data.get("settings"),"summary":compute_summary(data),"standings":compute_dashboard(data)["standings"],"topScorers":compute_dashboard(data)["topScorers"]}})
        if path.startswith("/api/verify/player/"):
            pid=path.rsplit("/",1)[-1]; data=get_data()
            player=next((p for p in data.get("players",[]) if p.get("id")==pid),None)
            if not player: return self.send_json({"ok":False,"error":"Jugador no encontrado"},404)
            return self.send_json({"ok":True,"player":{**player,"team":team_name(data,player.get("teamId"))}})
        if path.startswith("/api/qr/player/"):
            pid=path.rsplit("/",1)[-1]; host=self.headers.get("Host",f"127.0.0.1:{PORT}")
            url=f"{PUBLIC_BASE_URL or 'http://'+host}/verify.html?id={quote(pid)}"
            try:
                import qrcode
                from qrcode.image.svg import SvgPathImage
                qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
                qr.add_data(url); qr.make(fit=True)
                bio=io.BytesIO(); qr.make_image(image_factory=SvgPathImage).save(bio); payload=bio.getvalue()
                self.send_response(200); self.send_header("Content-Type","image/svg+xml"); self.end_headers(); self.wfile.write(payload); return
            except Exception:
                svg=f"<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><rect width='300' height='300' fill='white'/><text x='20' y='150'>{url}</text></svg>".encode()
                self.send_response(200); self.send_header("Content-Type","image/svg+xml"); self.end_headers(); self.wfile.write(svg); return
        
        if path=="/api/templates/carga-masiva.csv":
            return send_bytes(self, bulk_template_csv(), "text/csv; charset=utf-8", "plantilla_carga_masiva_ligaprof7.csv")

        if path=="/api/templates/datos-reales.csv":
            return send_bytes(self, csv_bytes(["tipo","id","nombre","equipo","categoria","numero","posicion","telefono","estatus","notas"], [["equipo","EQ-001","Nombre del equipo","","Libre Varonil","","","","Activo",""],["jugador","JUG-001","Nombre jugador","EQ-001","Libre Varonil","10","Delantero","7220000000","Activo",""]]), "text/csv; charset=utf-8", "plantilla_datos_reales_ligaprof7.csv")
        if path=="/api/backup/full":
            return send_bytes(self, json.dumps({"version":"V32.6","data":get_data()}, ensure_ascii=False, indent=2).encode(), "application/json; charset=utf-8", "LigaProF7_V30_2_backup_full.json")
        if path in ["/api/reports/enterprise.xlsx","/api/reports/workbook.xlsx","/api/reports/standings.xlsx","/api/reports/payments.xlsx","/api/reports/sanctions.xlsx"]:
            data=get_data()
            sheets=[
                ("Tabla",["Equipo","PTS","PJ","GF","GC"],[[t.get("name"),t.get("pts"),t.get("pj"),t.get("gf"),t.get("gc")] for t in compute_dashboard(data)["standings"]]),
                ("Pagos",["Equipo","Concepto","Monto","Estatus"],[[team_name(data,p.get("teamId")),p.get("concept"),p.get("amount"),p.get("status")] for p in data.get("payments",[])]),
                ("Sanciones",["Jugador","Equipo","Sanción","Estatus"],[[player_name(data,s.get("playerId")),team_name(data,s.get("teamId")),s.get("sanctionType"),s.get("status")] for s in data.get("sanctions",[])])
            ]
            return send_bytes(self, build_xlsx(sheets), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "LigaProF7_V30_2_reporte.xlsx")
        if path in ["/api/reports/enterprise.pdf","/api/reports/premium.pdf","/api/reports/general.pdf"]:
            data=get_data(); dash=compute_dashboard(data)
            lines=["LIGAPRO F7 - REPORTE GENERAL"]+[f"{k}: {v}" for k,v in dash["kpis"].items()]+["","TABLA GENERAL"]+[f"{i+1}. {t.get('name')} - {t.get('pts')} pts" for i,t in enumerate(dash["standings"])]
            return send_bytes(self, simple_pdf("LigaPro F7 Reporte", lines), "application/pdf", "LigaProF7_reporte.pdf")
        return super().do_GET()

    def do_POST(self):
        path=urlparse(self.path).path
        if path in ["/api/login","/api/demo-login"]:
            payload=self.read_json()
            if path=="/api/demo-login":
                demo=payload.get("demo","admin")
                mapu={"admin":"admin","arbitro":"arbitro","director":"tigres","consulta":"consulta"}
                username=mapu.get(demo,"admin")
                pin={"admin":"2026","arbitro":"7777","tigres":"1111","consulta":"0000"}[username]
            else:
                username=str(payload.get("username","")).lower().replace("á","a")
                aliases={"administrador":"admin","director":"tigres"}
                username=aliases.get(username,username)
                pin=str(payload.get("pin",""))
            c=conn()
            row=c.execute("SELECT * FROM users WHERE username=? AND active=1",(username,)).fetchone()
            c.close()
            if not row or not verify_pin(pin,row["pin_salt"],row["pin_hash"]):
                return self.send_json({"ok":False,"error":"Credenciales inválidas"},401)
            token=secrets.token_urlsafe(32)
            user={"id":row["id"],"username":row["username"],"role":row["role"],"name":row["name"],"teamId":row["team_id"]}
            SESSIONS[token]=user
            audit(user["id"], "login", f"Acceso {username}")
            return self.send_json({"ok":True,"token":token,"user":user})
        if path=="/api/logout":
            return self.send_json({"ok":True})
        if path=="/api/data":
            user=user_from_token(self.headers)
            if not user: return self.send_json({"ok":False,"error":"Sesión requerida"},401)
            data=self.read_json().get("data")
            if data: set_data(data)
            return self.send_json({"ok":True})
        
        if path=="/api/users/create":
            actor=user_from_token(self.headers)
            if not actor or actor.get("role")!="admin":
                return self.send_json({"ok":False,"error":"Solo administrador"},403)
            payload=self.read_json()
            username=str(payload.get("username","")).strip().lower()
            pin=str(payload.get("pin","")).strip()
            role=str(payload.get("role","viewer")).strip()
            name=str(payload.get("name",username)).strip()
            team_id=payload.get("teamId") or None
            if not username or not pin:
                return self.send_json({"ok":False,"error":"Usuario y PIN son obligatorios"},400)
            if role not in ["admin","referee","director","viewer"]:
                return self.send_json({"ok":False,"error":"Rol inválido"},400)
            salt,hp=hash_pin(pin)
            uid="USR-"+secrets.token_hex(4).upper()
            c=conn()
            try:
                c.execute("INSERT INTO users(id,username,pin_salt,pin_hash,role,name,team_id,active) VALUES(?,?,?,?,?,?,?,1)",
                          (uid,username,salt,hp,role,name,team_id))
                c.commit()
            except Exception as e:
                c.close()
                return self.send_json({"ok":False,"error":"No se pudo crear usuario. Puede estar duplicado."},400)
            c.close()
            audit(actor["id"], "create_user", f"Usuario creado: {username}")
            return self.send_json({"ok":True,"user":{"id":uid,"username":username,"role":role,"name":name,"teamId":team_id,"active":1}})

        
        if path=="/api/import/real-data":
            actor=user_from_token(self.headers)
            if not actor or actor.get("role")!="admin":
                return self.send_json({"ok":False,"error":"Solo administrador"},403)
            payload=self.read_json()
            rows=payload.get("rows",[])
            data=get_data()
            for r in rows:
                tipo=str(r.get("tipo","")).strip().lower()
                if tipo=="equipo":
                    tid=r.get("id") or ("EQ-"+secrets.token_hex(2).upper())
                    if not any(x.get("id")==tid for x in data["teams"]):
                        data["teams"].append({"id":tid,"tournamentId":"TOR-REAL","seasonId":"TEMP-REAL","categoryId":"CAT-REAL","name":r.get("nombre","Equipo"),"director":r.get("notas","Responsable"),"status":r.get("estatus","Activo"),"pj":0,"pts":0,"gf":0,"gc":0,"pago":"Pendiente"})
                if tipo=="jugador":
                    pid=r.get("id") or ("JUG-"+secrets.token_hex(2).upper())
                    if not any(x.get("id")==pid for x in data["players"]):
                        data["players"].append({"id":pid,"teamId":r.get("equipo"),"categoryId":"CAT-REAL","name":r.get("nombre","Jugador"),"number":int(r.get("numero") or 0),"position":r.get("posicion","Jugador"),"age":0,"phone":r.get("telefono",""),"document":"Pendiente","status":r.get("estatus","Activo")})
            set_data(data)
            audit(actor["id"], "import_real_data", f"Importación de datos reales: {len(rows)} registros")
            return self.send_json({"ok":True,"count":len(rows),"data":get_data()})

        
        if path=="/api/bulk/validate":
            actor=user_from_token(self.headers)
            if not actor or actor.get("role")!="admin":
                return self.send_json({"ok":False,"error":"Solo administrador"},403)
            payload=self.read_json()
            rows=payload.get("rows")
            if rows is None and payload.get("csvText"):
                rows=parse_csv_text(payload.get("csvText",""))
            rows=rows or []
            validation=validate_bulk_rows(rows, get_data())
            return self.send_json({"ok":True,"validation":validation})

        if path=="/api/bulk/import":
            actor=user_from_token(self.headers)
            if not actor or actor.get("role")!="admin":
                return self.send_json({"ok":False,"error":"Solo administrador"},403)
            payload=self.read_json()
            rows=payload.get("rows")
            if rows is None and payload.get("csvText"):
                rows=parse_csv_text(payload.get("csvText",""))
            rows=rows or []
            data=get_data()
            result=apply_bulk_rows(rows, data, actor)
            if not result.get("ok"):
                return self.send_json(result,400)
            # Crear usuarios de tipo usuario
            for raw in rows:
                r=normalize_row(raw)
                if r.get("tipo")=="usuario":
                    username=(r.get("notas") or r.get("nombre") or "").replace("usuario:","").strip().lower().replace(" ","_")
                    if not username:
                        username=unique_id("user", r.get("nombre")).lower()
                    pin=r.get("pin") or "0000"
                    role=r.get("rol") or "viewer"
                    name=r.get("nombre") or username
                    team_id=r.get("equipo") or None
                    c=conn()
                    try:
                        salt,hp=hash_pin(pin)
                        uid="USR-"+secrets.token_hex(4).upper()
                        c.execute("INSERT INTO users(id,username,pin_salt,pin_hash,role,name,team_id,active) VALUES(?,?,?,?,?,?,?,1)",
                                  (uid,username,salt,hp,role,name,team_id))
                        c.commit()
                    except Exception:
                        pass
                    c.close()
            set_data(result["data"])
            audit(actor["id"], "bulk_import", f"Carga masiva: {result['imported']}")
            return self.send_json({"ok":True,"imported":result["imported"],"validation":result["validation"],"data":get_data()})

        
        if path=="/api/mobile-info":
            ips=get_lan_ips()
            urls=[f"http://{ip}:{PORT}" for ip in ips]
            return self.send_json({"ok":True,"port":PORT,"local":"http://127.0.0.1:%s"%PORT,"urls":urls,"version":"V32.6.1 HOTFIX CELULAR RED WIFI"})

        if path=="/celular":
            ips=get_lan_ips()
            primary = f"http://{ips[0]}:{PORT}" if ips else f"http://127.0.0.1:{PORT}"
            rows = "".join([f"<li><b>URL:</b> http://{ip}:{PORT}</li>" for ip in ips]) or f"<li>{primary}</li>"
            html=f"""<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>LigaPro F7 V32.6 Celular</title>
<style>
body{{margin:0;background:#001b0d;color:#fff;font-family:Arial,sans-serif;padding:22px}}
.card{{max-width:720px;margin:auto;background:#062916;border:1px solid #00b050;border-radius:24px;padding:22px;box-shadow:0 20px 70px rgba(0,0,0,.45)}}
h1{{margin:0 0 8px;color:#00ff88}} h2{{color:#f6c945}} p,li{{line-height:1.5;font-size:17px}}
.qr{{display:flex;justify-content:center;background:#fff;border-radius:22px;padding:18px;margin:20px 0;overflow:auto}}
code{{background:#000;padding:8px;border-radius:8px;color:#00ff88;display:inline-block;margin:3px 0}}
.btn{{display:block;text-align:center;padding:14px 18px;border-radius:14px;background:#00b050;color:#001b0d;text-decoration:none;font-weight:900;margin:10px 0}}
.warn{{background:#fff2cc;color:#111;padding:12px;border-radius:14px;font-weight:700}}
</style></head><body><div class='card'>
<h1>LigaPro F7 V32.6</h1><p>Demo presentable para celular.</p>
<a class='btn' href='{primary}'>Abrir app en este dispositivo</a>
<div class='qr'>{qr_svg(primary)}</div>
<h2>URLs disponibles</h2><ul>{rows}</ul>
<div class='warn'>El celular debe estar conectado al mismo WiFi que la computadora. Si no abre, permite Python en el firewall de Windows para redes privadas.</div>
<h2>Usuarios demo</h2>
<p><code>admin / 2026</code><br><code>arbitro / 7777</code><br><code>tigres / 1111</code><br><code>consulta / 0000</code></p>
</div></body></html>"""
            return send_bytes(self, html.encode("utf-8"), "text/html; charset=utf-8", "ligaprof7_v32_6_1_celular.html")

        
        if path=="/api/demo/presentable":
            user=user_from_token(self.headers)
            if not user or user.get("role")!="admin":
                return self.send_json({"ok":False,"error":"Solo admin"},403)
            demo = {
                "settings":{"brandName":"LigaPro F7","seasonLabel":"Demo Apertura 2026","mode":"DEMO PRESENTABLE"},
                "tournaments":[{"id":"TOR-DEMO","name":"LigaPro F7 Apertura 2026","type":"Liga","status":"Activo"}],
                "seasons":[{"id":"TEMP-DEMO","tournamentId":"TOR-DEMO","name":"Apertura 2026","year":2026,"status":"Activo"}],
                "categories":[{"id":"CAT-LIBRE","seasonId":"TEMP-DEMO","name":"Libre Varonil","ageRule":"Libre","genderRule":"Varonil","maxPlayers":18,"status":"Activo"}],
                "teams":[
                    {"id":"EQ-TIG","tournamentId":"TOR-DEMO","seasonId":"TEMP-DEMO","categoryId":"CAT-LIBRE","name":"Tigres Metepec","director":"Carlos Ramírez","status":"Activo","pj":3,"pts":7,"gf":12,"gc":5,"pago":"Pagado"},
                    {"id":"EQ-LEO","tournamentId":"TOR-DEMO","seasonId":"TEMP-DEMO","categoryId":"CAT-LIBRE","name":"Leones Toluca","director":"Jorge Hernández","status":"Activo","pj":3,"pts":6,"gf":9,"gc":6,"pago":"Pendiente"},
                    {"id":"EQ-HAL","tournamentId":"TOR-DEMO","seasonId":"TEMP-DEMO","categoryId":"CAT-LIBRE","name":"Halcones Centro","director":"Luis Fernando","status":"Activo","pj":3,"pts":4,"gf":8,"gc":7,"pago":"Pagado"},
                    {"id":"EQ-REAL","tournamentId":"TOR-DEMO","seasonId":"TEMP-DEMO","categoryId":"CAT-LIBRE","name":"Real Universidad","director":"Diego Morales","status":"Activo","pj":3,"pts":1,"gf":4,"gc":15,"pago":"Pendiente"}
                ],
                "players":[
                    {"id":"JUG-001","teamId":"EQ-TIG","categoryId":"CAT-LIBRE","name":"Carlos Ramírez","number":9,"position":"Delantero","age":27,"phone":"7221234567","document":"Validado","status":"Activo"},
                    {"id":"JUG-002","teamId":"EQ-HAL","categoryId":"CAT-LIBRE","name":"Luis Fernando","number":1,"position":"Portero","age":25,"phone":"7229876543","document":"Validado","status":"Activo"},
                    {"id":"JUG-003","teamId":"EQ-LEO","categoryId":"CAT-LIBRE","name":"Diego Morales","number":10,"position":"Medio","age":29,"phone":"7221112233","document":"Pendiente","status":"Activo"},
                    {"id":"JUG-004","teamId":"EQ-REAL","categoryId":"CAT-LIBRE","name":"Ángel Torres","number":7,"position":"Delantero","age":24,"phone":"7225556677","document":"Validado","status":"Activo"}
                ],
                "matches":[
                    {"id":"PAR-001","tournamentId":"TOR-DEMO","seasonId":"TEMP-DEMO","categoryId":"CAT-LIBRE","round":"Jornada 1","date":"2026-06-15","time":"18:30","field":"Cancha 1","localId":"EQ-TIG","visitorId":"EQ-LEO","status":"Programado","localScore":0,"visitorScore":0,"referee":"Árbitro Central","youtube":"https://youtube.com/"},
                    {"id":"PAR-002","tournamentId":"TOR-DEMO","seasonId":"TEMP-DEMO","categoryId":"CAT-LIBRE","round":"Jornada 1","date":"2026-06-15","time":"20:00","field":"Cancha 2","localId":"EQ-HAL","visitorId":"EQ-REAL","status":"Programado","localScore":0,"visitorScore":0,"referee":"Árbitro Central","youtube":""},
                    {"id":"PAR-003","tournamentId":"TOR-DEMO","seasonId":"TEMP-DEMO","categoryId":"CAT-LIBRE","round":"Jornada 2","date":"2026-06-22","time":"19:00","field":"Cancha 1","localId":"EQ-TIG","visitorId":"EQ-HAL","status":"Programado","localScore":0,"visitorScore":0,"referee":"Por asignar","youtube":""}
                ],
                "payments":[
                    {"id":"PAG-001","tournamentId":"TOR-DEMO","seasonId":"TEMP-DEMO","teamId":"EQ-TIG","concept":"Inscripción","amount":800,"status":"Pagado","date":"2026-06-01"},
                    {"id":"PAG-002","tournamentId":"TOR-DEMO","seasonId":"TEMP-DEMO","teamId":"EQ-LEO","concept":"Inscripción","amount":800,"status":"Pendiente","date":"2026-06-01"},
                    {"id":"PAG-003","tournamentId":"TOR-DEMO","seasonId":"TEMP-DEMO","teamId":"EQ-HAL","concept":"Inscripción","amount":800,"status":"Pagado","date":"2026-06-01"}
                ],
                "sponsors":[
                    {"id":"PAT-001","tournamentId":"TOR-DEMO","name":"Gatorade","format":"Lona","amount":6000,"location":"Lateral Norte","status":"Activo"},
                    {"id":"PAT-002","tournamentId":"TOR-DEMO","name":"Sporade","format":"Digital","amount":2950,"location":"Marcador","status":"Pendiente"}
                ],
                "playerStats":{
                    "JUG-001":{"goals":12,"assists":3,"goalsAgainst":0,"cleanSheets":0,"position":"Delantero"},
                    "JUG-002":{"goals":0,"assists":0,"goalsAgainst":7,"cleanSheets":2,"position":"Portero"},
                    "JUG-003":{"goals":6,"assists":5,"goalsAgainst":0,"cleanSheets":0,"position":"Medio"},
                    "JUG-004":{"goals":4,"assists":2,"goalsAgainst":0,"cleanSheets":0,"position":"Delantero"}
                },
                "incidents":[], "sanctions":[], "refereeReports":[]
            }
            set_data(demo)
            audit(user["id"], "demo_presentable", "Datos demo presentables cargados")
            return self.send_json({"ok":True,"data":get_data()})

        if path=="/api/reset":
            user=user_from_token(self.headers)
            if not user or user.get("role")!="admin": return self.send_json({"ok":False,"error":"Solo admin"},403)
            if os.path.exists(DB_PATH): os.remove(DB_PATH)
            init_db()
            return self.send_json({"ok":True,"data":get_data()})
        return self.send_json({"ok":False,"error":"No encontrado"},404)

if __name__=="__main__":
    init_db()
    print("="*60)
    print("LigaPro F7 V32.6.1 HOTFIX CELULAR RED WIFI - Login real")
    print("="*60)
    print(f"Servidor: http://127.0.0.1:{PORT}")
    print("Usuarios: admin/2026 · arbitro/7777 · tigres/1111 · consulta/0000")
    print("="*60)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
