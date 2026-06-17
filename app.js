function normalizeExcelPaste(text){
 // El servidor V32.1 detecta tabuladores, comas o punto y coma.
 return String(text||"").replace(/\r\n/g,"\n").replace(/\r/g,"\n").trim();
}

let token=localStorage.getItem("ligaprof7_v32_token")||"";
let currentUser=null;
let data=null;
let module="inicio";
let mobileScreenOpen=false;

const modules=[
 ["inicio","Inicio","assets/inicio.png"],
 ["pwa","Instalar app","assets/inicio.png"],
 ["celular","Celular","assets/inicio.png"],
 ["demo","Modo demo","assets/estadisticas.png"],
 ["masiva","Carga Excel","assets/estadisticas.png"],
 ["carga","Captura manual","assets/equipos.png"],
 ["equipos","Equipos","assets/equipos.png"],
 ["jugadores","Jugadores","assets/registro_qr.png"],
 ["calendario","Calendario","assets/calendario.png"],
 ["resultados","Resultados","assets/resultados.png"],
 ["tabla","Tabla","assets/tabla.png"],
 ["pagos","Pagos","assets/pagos.png"],
 ["reportes","Reportes","assets/estadisticas.png"],
 ["tv","LigaPro TV","assets/tv.png"]
];

function $(id){return document.getElementById(id)}
function isMobileAppView(){return window.matchMedia && window.matchMedia("(max-width:760px)").matches}
function updateMobileShell(){
 const isOpen = isMobileAppView() && mobileScreenOpen;
 document.body.classList.toggle("screen-open", !!isOpen);
 const titleEl=$("mobileScreenTitle");
 if(titleEl){
   const found=modules.find(x=>x[0]===module);
   titleEl.textContent=found?found[1]:"LigaPro F7";
 }
 const roleEl=$("mobileScreenRole");
 if(roleEl){
   roleEl.textContent=currentUser?(currentUser.role||"usuario"):"sin sesión";
 }
}
function goHome(){
 module="inicio";
 mobileScreenOpen=false;
 updateMobileShell();
 render();
 window.scrollTo({top:0,behavior:"smooth"});
}
function toast(m){const t=$("toast");t.textContent=m;t.style.display="block";setTimeout(()=>t.style.display="none",3500)}
function money(n){return "$"+Number(n||0).toLocaleString("es-MX")}
function auth(extra={}){return token?{...extra,Authorization:"Bearer "+token}:extra}
async function api(url,opt={}){const r=await fetch(url,opt);const txt=await r.text();let j={};try{j=JSON.parse(txt)}catch{};if(!r.ok)throw new Error(j.error||txt||"Error");return j}
async function load(){const j=await api("/api/data");data=j.data;render()}
async function save(){if(!currentUser){toast("Primero inicia sesión");return false}try{await api("/api/data",{method:"POST",headers:auth({"Content-Type":"application/json"}),body:JSON.stringify({data})});await load();toast("Datos guardados");return true}catch(e){toast("No se guardó: "+e.message);return false}}
function setModule(m){
 module=m;
 mobileScreenOpen = isMobileAppView() && m!=="inicio";
 document.body.dataset.module=m;
 const found=modules.find(x=>x[0]===m);
 if(found && $("mock")) $("mock").src=found[2];
 updateMobileShell();
 render();
 const right=document.querySelector(".right");
 if(right) right.scrollTo({top:0,behavior:"smooth"});
 if(!mobileScreenOpen) window.scrollTo({top:0,behavior:"smooth"});
}

function loginMobileManual(){
 const u=$("mobileUsername")?.value || "admin";
 const p=$("mobilePin")?.value || "2026";
 if($("username")) $("username").value=u;
 if($("pin")) $("pin").value=p;
 loginManual();
}
function renderNav(){ $("nav").innerHTML=modules.map(m=>`<button class="${module===m[0]?'active':''}" data-module="${m[0]}"><span>${m[1]}</span><small>Abrir pantalla</small></button>`).join("")}
function teamName(id){return (data.teams||[]).find(t=>t.id===id)?.name||id}
function playerName(id){return (data.players||[]).find(p=>p.id===id)?.name||id}
function activeTournament(){return data.tournaments?.[0]?.id||"TOR-REAL"}
function activeSeason(){return data.seasons?.[0]?.id||"TEMP-REAL"}
function activeCategory(){return data.categories?.[0]?.id||"CAT-REAL"}
function slugId(prefix, text){return prefix+"-"+String(text||"REAL").normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-zA-Z0-9]+/g,"").substring(0,8).toUpperCase()+"-"+String(Date.now()).slice(-4)}

function render(){
 if(!data)return;
 document.body.dataset.module=module;
 updateMobileShell();
 renderNav();
 $("loginCard").style.display=currentUser?"none":"block";
 $("roleBox").innerHTML=currentUser?`Sesión: ${currentUser.name}<br><small>${currentUser.role}</small>`:"Sin sesión";
 const mobileAuth=$("mobileAuthBox"); if(mobileAuth) mobileAuth.style.display=currentUser?"none":"block";
 const s=data.summary||{};
 $("kTeams").textContent=s.equiposActivos||0;
 $("kPlayers").textContent=s.jugadoresRegistrados||0;
 $("kIncome").textContent=money(s.ingresosTotales||0);
 $("kPending").textContent=money(s.pagosPendientes||0);

 let rows=[],title="Carga masiva",desc="Administración profesional del torneo en tiempo real.";
 if(module==="inicio"){
   title="Inicio LigaPro F7";
   desc="Crea torneos, registra equipos, genera partidos y administra resultados desde una sola plataforma.";
   rows=[
    ["Centro de mando","Control de equipos, jugadores, calendario, pagos y reportes desde una sola app."],
    ["Pantallas reales","Cada módulo se abre como pantalla completa con botón para regresar."],
    ["Datos del torneo","Consulta tabla, resultados, pagos pendientes y reportes ejecutivos."],
    ["Listo para presentar","Versión comercial para equipos, árbitros, patrocinadores y directores."]
   ];
 }
 if(module==="masiva"){
   title="Carga masiva · Excel/CSV";
   desc="Pega CSV, carga archivo CSV, valida e importa.";
   rows=[
    ["1. Descargar plantilla","Usa el botón Descargar plantilla."],
    ["2. Pegar o cargar CSV","Puedes pegar texto CSV o seleccionar archivo .csv."],
    ["3. Validar CSV","Revisa errores antes de importar."],
    ["4. Importar CSV","Guarda los registros en la base."]
   ];
 }


 if(module==="pwa"){
   title="Instalar como app";
   desc="PWA instalable con ícono y pantalla completa.";
   rows=[
    ["Android","Abre la URL HTTPS, toca Instalar o Agregar a pantalla principal."],
    ["iPhone","En Safari, toca Compartir y Agregar a pantalla de inicio."],
    ["Local","En red local puedes probarla; para instalación completa se recomienda HTTPS."],
    ["Siguiente","Publicar en internet para instalarla como app formal."]
   ];
 }

 if(module==="celular"){
   title="Abrir en celular";
   desc="Muestra la app en un teléfono dentro de la misma red WiFi.";
   rows=[
    ["Paso 1","Deja abierta esta app en la computadora."],
    ["Paso 2","Conecta el celular al mismo WiFi."],
    ["Paso 3","Abre /celular o usa el QR de acceso."],
    ["Importante","No uses 127.0.0.1 en el celular; usa la IP de la computadora."]
   ];
 }
 if(module==="demo"){
   title="Modo demo presentable";
   desc="Herramientas para enseñar la app de forma seria.";
   rows=[
    ["Cargar demo presentable","Restaura datos de ejemplo limpios y profesionales."],
    ["Backup","Descarga un respaldo antes y después de pruebas."],
    ["QR jugador","Muestra credencial/validación de jugador."],
    ["Celular","Abre la pantalla /celular para compartir en la red local."]
   ];
 }

 if(module==="carga"){
   title="Captura operativa individual";
   rows=[["Configurar torneo","Captura torneo, temporada y categoría"],["Agregar equipo","Alta individual"],["Agregar jugador","Alta individual"],["Agregar partido","Calendario individual"]];
 }
 if(module==="equipos"){title="Equipos";rows=(data.teams||[]).map(t=>[t.name,`${t.director||""} · ${t.status} · ${t.pts||0} pts`])}
 if(module==="jugadores"){title="Jugadores";rows=(data.players||[]).map(p=>[p.name,`#${p.number||0} · ${p.position||""} · ${teamName(p.teamId)}`])}
 if(module==="calendario"){title="Calendario";rows=(data.matches||[]).map(m=>[`${teamName(m.localId)} vs ${teamName(m.visitorId)}`,`${m.round} · ${m.date} · ${m.time} · ${m.status}`])}
 if(module==="resultados"){title="Resultados";rows=(data.matches||[]).map(m=>[`${teamName(m.localId)} ${m.localScore}-${m.visitorScore} ${teamName(m.visitorId)}`,m.status])}
 if(module==="tabla"){title="Tabla general";rows=[...(data.teams||[])].sort((a,b)=>(b.pts||0)-(a.pts||0)).map((t,i)=>[`${i+1}. ${t.name}`,`PTS ${t.pts||0} · PJ ${t.pj||0} · GF ${t.gf||0} · GC ${t.gc||0}`])}
 if(module==="pagos"){title="Pagos";rows=(data.payments||[]).map(p=>[teamName(p.teamId),`${p.concept} · ${money(p.amount)} · ${p.status}`])}
 if(module==="reportes"){title="Reportes";rows=[["Dashboard","/dashboard"],["Checklist","/checklist"],["XLSX","/api/reports/enterprise.xlsx"],["PDF","/api/reports/enterprise.pdf"],["Backup","/api/backup/full"],["Plantilla","/api/templates/carga-masiva.csv"]]}
 if(module==="tv"){title="LigaPro TV";rows=(data.matches||[]).map(m=>[`${teamName(m.localId)} vs ${teamName(m.visitorId)}`,m.youtube||"Sin enlace YouTube"])}
 $("moduleTitle").textContent=title;
 $("moduleDesc").textContent=desc;
 $("content").innerHTML=rows.map(r=>`<div class="row"><div><b>${r[0]}</b><small>${r[1]}</small></div><span class="pill">OK</span></div>`).join("");
 renderBulkPanel();
}

function renderBulkPanel(){
 const panel=$("loadPanel");
 if(!panel)return;
 if(module!=="masiva" && module!=="carga" && module!=="demo" && module!=="celular"){
   panel.innerHTML="";
   return;
 }
 panel.innerHTML=`
 <div class="formBox">
  <h3>LigaPro F7 V1.0 Presentable</h3>
  <p>Versión presentable: app web publicada, APK Android funcional, carga Excel, QR, reportes y backup.</p>
  <textarea id="bulkCsvText" placeholder="Pega aquí directo desde Excel. Copia desde la fila 5 incluyendo encabezados. Acepta tabuladores o CSV."></textarea>
  <input id="bulkCsvFile" type="file" accept=".csv,text/csv" />
  <div class="btnGrid">
   <button id="btnDownloadTemplate" type="button">Descargar plantilla CSV</button>
   <button id="btnSampleCsv" type="button">Ejemplo rápido</button>
   <button id="btnValidateCsv" type="button">Validar CSV</button>
   <button id="btnImportCsv" type="button">Importar CSV</button>
   <button id="btnClearCsv" type="button">Limpiar cuadro</button>
   <button id="btnBackup" type="button">Backup</button>
   <button id="btnMobilePage" type="button">Abrir guía celular</button>
   <button id="btnDemoData" type="button">Cargar demo presentable</button>
  </div>
  <div id="bulkResult" class="bulkResult">Sin validación todavía.</div>
 </div>
 <div class="formBox">
  <h3>Captura operativa individual</h3>
  <div class="btnGrid">
   <button id="btnConfigureTournament" type="button">Configurar torneo</button>
   <button id="btnAddTeam" type="button">Agregar equipo</button>
   <button id="btnAddPlayer" type="button">Agregar jugador</button>
   <button id="btnAddMatch" type="button">Agregar partido</button>
   <button id="btnAddPayment" type="button">Registrar pago</button>
   <button id="btnClearDemo" type="button">Limpiar demo</button>
  </div>
 </div>`;
 bindBulkButtons();
}

function bindBulkButtons(){
 const binds=[
  ["btnDownloadTemplate", downloadBulkTemplate],
  ["btnSampleCsv", sampleBulkCsv],
  ["btnValidateCsv", validateBulkCsv],
  ["btnImportCsv", importBulkCsv],
  ["btnClearCsv", clearCsvText],
  ["btnBackup", ()=>openUrl("/api/backup/full")],
  ["btnMobilePage", ()=>openUrl("/celular")],
  ["btnDemoData", loadDemoPresentable],
  ["btnConfigureTournament", configureTournament],
  ["btnAddTeam", addTeamReal],
  ["btnAddPlayer", addPlayerReal],
  ["btnAddMatch", addMatchReal],
  ["btnAddPayment", addPaymentReal],
  ["btnClearDemo", clearDemoData],
 ];
 for(const [id,fn] of binds){
  const el=$(id);
  if(el) el.addEventListener("click", (e)=>{e.preventDefault(); e.stopPropagation(); fn();});
 }
 const file=$("bulkCsvFile");
 if(file) file.addEventListener("change", readCsvFile);
}

function requireAdmin(){
 if(!currentUser){toast("Primero entra como admin / 2026");return false}
 if(currentUser.role!=="admin"){toast("Solo administrador");return false}
 return true;
}

function downloadBulkTemplate(){ openUrl("/api/templates/carga-masiva.csv"); }

function clearCsvText(){
 const t=$("bulkCsvText"); if(t)t.value="";
 const r=$("bulkResult"); if(r)r.textContent="Sin validación todavía.";
 toast("Cuadro limpio");
}

function readCsvFile(evt){
 const file=evt.target.files?.[0];
 if(!file){return}
 const reader=new FileReader();
 reader.onload=()=>{ $("bulkCsvText").value=reader.result; toast("CSV cargado desde archivo"); };
 reader.onerror=()=>toast("No se pudo leer el archivo");
 reader.readAsText(file, "utf-8");
}

function sampleBulkCsv(){
 const sample = `tipo,id,nombre,equipo,categoria,numero,posicion,telefono,estatus,fecha,hora,cancha,local,visitante,concepto,monto,rol,pin,notas
torneo,TOR-REAL,LigaPro F7 Apertura 2026,,,,,,Activo,,,,,,,,,,
categoria,CAT-LIBRE,Libre Varonil,,,,,,Activo,,,,,,,,,,
equipo,EQ-TIG,Tigres Metepec,,Libre Varonil,,,,Activo,,,,,,,,,,Director: Carlos Ramírez
equipo,EQ-LEO,Leones Toluca,,Libre Varonil,,,,Activo,,,,,,,,,,Director: Jorge Hernández
jugador,JUG-001,Carlos Ramírez,EQ-TIG,Libre Varonil,9,Delantero,7221234567,Activo,,,,,,,,,,
jugador,JUG-002,Luis Fernando,EQ-LEO,Libre Varonil,1,Portero,7229876543,Activo,,,,,,,,,,
partido,PAR-001,,,Libre Varonil,,,,Programado,2026-06-15,18:30,Cancha 1,EQ-TIG,EQ-LEO,,,,Jornada 1
pago,PAG-001,,EQ-TIG,,,,,Pagado,2026-06-01,,,,,Inscripción,800,,,
patrocinador,PAT-001,Gatorade,,,,,,Activo,,,,,,,6000,,,Lona lateral norte
usuario,,Árbitro Real,,,,,,Activo,,,,,,,,referee,7777,arbitro_real`;
 $("bulkCsvText").value = sample;
 toast("Ejemplo cargado");
}

function renderBulkResult(validation, imported){
 const box=$("bulkResult");
 if(!box)return;
 const counts=validation?.counts||{};
 const byType=counts.byType||{};
 let html=`<b>Resultado:</b><br>Válidos: ${counts.valid||0} · Advertencias: ${counts.warnings||0} · Errores: ${counts.errors||0}<br>`;
 html += `<small>${Object.entries(byType).map(([k,v])=>`${k}: ${v}`).join(" · ")}</small>`;
 if(imported){
  html += `<hr><b>Importado:</b><br><small>${Object.entries(imported).map(([k,v])=>`${k}: ${v}`).join(" · ")}</small>`;
 }
 const issues=(validation?.results||[]).filter(x=>x.status!=="ok").slice(0,10);
 if(issues.length){
  html += `<hr><b>Revisar:</b>`;
  html += issues.map(x=>`<div class="bulkIssue">${x.status.toUpperCase()} fila ${x.row}: ${(x.issues||[]).concat(x.warnings||[]).join("; ")}</div>`).join("");
 }
 box.innerHTML=html;
}

async function validateBulkCsv(){
 if(!requireAdmin())return;
 const csvText=normalizeExcelPaste($("bulkCsvText")?.value||"");
 if(!csvText.trim()){toast("Pega el CSV, carga archivo o usa Ejemplo rápido");return}
 try{
  const j=await api("/api/bulk/validate",{method:"POST",headers:auth({"Content-Type":"application/json"}),body:JSON.stringify({csvText})});
  renderBulkResult(j.validation);
  toast(j.validation.ok?"CSV válido":"CSV con errores/advertencias");
 }catch(e){
  console.error(e);
  toast("Error al validar: "+e.message);
 }
}

async function importBulkCsv(){
 if(!requireAdmin())return;
 const csvText=normalizeExcelPaste($("bulkCsvText")?.value||"");
 if(!csvText.trim()){toast("Pega el CSV, carga archivo o usa Ejemplo rápido");return}
 if(!confirm("¿Importar datos masivos a la base?"))return;
 try{
  const j=await api("/api/bulk/import",{method:"POST",headers:auth({"Content-Type":"application/json"}),body:JSON.stringify({csvText})});
  data=j.data;
  renderBulkResult(j.validation, j.imported);
  toast("Carga masiva importada");
  await load();
  setModule("masiva");
 }catch(e){
  console.error(e);
  toast("No se importó: "+e.message);
 }
}

async function configureTournament(){
 if(!requireAdmin())return;
 const name=prompt("Nombre real del torneo:", data.tournaments?.[0]?.name||"LigaPro F7 Apertura 2026"); if(!name)return;
 const season=prompt("Nombre de temporada:", data.seasons?.[0]?.name||"Apertura 2026")||"Temporada 2026";
 const category=prompt("Categoría principal:", data.categories?.[0]?.name||"Libre Varonil")||"Libre";
 data.tournaments=[{id:"TOR-REAL",name,type:"Liga",status:"Activo"}];
 data.seasons=[{id:"TEMP-REAL",tournamentId:"TOR-REAL",name:season,year:new Date().getFullYear(),status:"Activo"}];
 data.categories=[{id:"CAT-REAL",seasonId:"TEMP-REAL",name:category,ageRule:"Libre",genderRule:"Abierta",maxPlayers:18,status:"Activo"}];
 data.settings=data.settings||{}; data.settings.brandName=name; data.settings.seasonLabel=season;
 await save();
}

async function addTeamReal(){
 if(!requireAdmin())return;
 const name=prompt("Nombre del equipo:"); if(!name)return;
 const director=prompt("Nombre del director/responsable:","Responsable")||"Responsable";
 const id=slugId("EQ",name);
 data.teams.push({id,tournamentId:activeTournament(),seasonId:activeSeason(),categoryId:activeCategory(),name,director,status:"Activo",pj:0,pts:0,gf:0,gc:0,pago:"Pendiente"});
 await save(); setModule("equipos");
}

async function addPlayerReal(){
 if(!currentUser || !["admin","director"].includes(currentUser.role)){toast("Solo administrador o director");return}
 const teams=data.teams||[]; if(!teams.length){toast("Primero registra equipos");return}
 const teamId=currentUser.role==="director"&&currentUser.teamId?currentUser.teamId:(prompt("ID del equipo:\n"+teams.map(t=>`${t.id} = ${t.name}`).join("\n"),teams[0].id)||teams[0].id);
 const name=prompt("Nombre del jugador:"); if(!name)return;
 const number=Number(prompt("Número:", "0")||0);
 const position=prompt("Posición:","Jugador")||"Jugador";
 const phone=prompt("Teléfono:","")||"";
 const id=slugId("JUG",name);
 data.players.push({id,teamId,categoryId:activeCategory(),name,number,position,age:0,phone,document:"Pendiente",status:"Activo"});
 data.playerStats=data.playerStats||{}; data.playerStats[id]={goals:0,assists:0,goalsAgainst:0,cleanSheets:0,position};
 await save(); setModule("jugadores");
}

async function addMatchReal(){
 if(!requireAdmin())return;
 const teams=data.teams||[]; if(teams.length<2){toast("Necesitas al menos 2 equipos");return}
 const localId=prompt("ID equipo local:\n"+teams.map(t=>`${t.id} = ${t.name}`).join("\n"),teams[0].id)||teams[0].id;
 const visitorId=prompt("ID equipo visitante:",teams[1].id)||teams[1].id;
 const date=prompt("Fecha:","Por definir")||"Por definir";
 const time=prompt("Hora:","18:00")||"18:00";
 const field=prompt("Cancha:","Cancha 1")||"Cancha 1";
 const round=prompt("Jornada:","Jornada 1")||"Jornada 1";
 data.matches.push({id:slugId("PAR",localId+visitorId),tournamentId:activeTournament(),seasonId:activeSeason(),categoryId:activeCategory(),round,date,time,field,localId,visitorId,status:"Programado",localScore:0,visitorScore:0,referee:"Por asignar",youtube:""});
 await save(); setModule("calendario");
}

async function addPaymentReal(){
 if(!requireAdmin())return;
 const teams=data.teams||[]; if(!teams.length){toast("Primero registra equipos");return}
 const teamId=prompt("ID equipo:\n"+teams.map(t=>`${t.id} = ${t.name}`).join("\n"),teams[0].id)||teams[0].id;
 const concept=prompt("Concepto:","Inscripción / Cuota")||"Cuota";
 const amount=Number(prompt("Monto:","0")||0);
 const status=prompt("Estatus: Pagado / Pendiente / Vencido","Pagado")||"Pagado";
 data.payments.unshift({id:slugId("PAG",teamId),tournamentId:activeTournament(),seasonId:activeSeason(),teamId,concept,amount,status,date:new Date().toLocaleDateString("es-MX")});
 await save(); setModule("pagos");
}

async function clearDemoData(){
 if(!requireAdmin())return;
 if(!confirm("¿Limpiar equipos, jugadores, partidos, pagos, patrocinadores, incidencias y sanciones demo?"))return;
 data.teams=[]; data.players=[]; data.matches=[]; data.payments=[]; data.sponsors=[]; data.incidents=[]; data.sanctions=[]; data.refereeReports=[]; data.playerStats={};
 await save(); setModule("masiva");
}

async function login(username,pin){
 try{
  const j=await api("/api/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username,pin})});
  token=j.token; currentUser=j.user; localStorage.setItem("ligaprof7_v32_token",token);
  toast("Acceso correcto"); setModule("masiva");
 }catch(e){toast("No entró: "+e.message)}
}
function loginManual(){login($("username").value.trim(),$("pin").value.trim())}
function loginDemo(kind){const m={admin:["admin","2026"],arbitro:["arbitro","7777"],director:["tigres","1111"],consulta:["consulta","0000"]}[kind];login(m[0],m[1])}
function logout(){token="";currentUser=null;localStorage.removeItem("ligaprof7_v32_token");render();toast("Sesión cerrada")}
function openUrl(u){window.open(u,"_blank")}
function openQr(){const p=(data.players||[])[0];if(p)window.open(`/qr.html?id=${encodeURIComponent(p.id)}`,"_blank");else toast("No hay jugador")}

document.addEventListener("click", e=>{
 const btn=e.target.closest("button[data-module]");
 if(btn){setModule(btn.dataset.module)}
});
document.addEventListener("keydown",e=>{if(e.key==="Enter"&&!currentUser)loginManual()});

load().catch(e=>{console.error(e); toast("Error al cargar datos: "+e.message)});


async function loadDemoPresentable(){
 if(!requireAdmin()) return;
 if(!confirm("¿Cargar datos demo presentables? Esto reemplazará los datos actuales.")) return;
 try{
   const j=await api("/api/demo/presentable",{method:"POST",headers:auth({"Content-Type":"application/json"}),body:JSON.stringify({})});
   data=j.data;
   toast("Demo presentable cargada");
   await load();
   setModule("inicio");
 }catch(e){
   toast("No se pudo cargar demo: "+e.message);
 }
}

async function showMobileInfo(){
 try{
   const j=await api("/api/mobile-info");
   const urls=(j.urls||[]).join("\n");
   alert("Abre esta URL en el celular conectado al mismo WiFi:\n\n"+(urls||j.local));
 }catch(e){
   toast("No se pudo obtener IP: "+e.message);
 }
}



/* ===== V1.5 ESTILO DEPORSTAR Instalación ===== */
let deferredPwaPrompt = null;

function isStandalonePWA(){
  return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
}

function setupPWA(){
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/service-worker.js')
        .then(() => console.log('LigaPro F7 PWA service worker activo'))
        .catch(err => console.warn('No se registró service worker', err));
    });
  }

  const btn = document.getElementById('pwaInstallBtn');
  if (isStandalonePWA() && btn) {
    btn.style.display = 'none';
  }

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPwaPrompt = e;
    if (btn) {
      btn.style.display = 'block';
      btn.textContent = 'Instalar app';
    }
  });

  if (btn) {
    btn.addEventListener('click', async () => {
      if (deferredPwaPrompt) {
        deferredPwaPrompt.prompt();
        await deferredPwaPrompt.userChoice;
        deferredPwaPrompt = null;
        btn.style.display = 'none';
      } else {
        window.open('/instalar', '_blank');
      }
    });
  }

  window.addEventListener('appinstalled', () => {
    toast('LigaPro F7 instalada');
    if (btn) btn.style.display = 'none';
  });
}

setupPWA();

window.addEventListener("resize", updateMobileShell);


function renderFallbackHome(){
 try{
   document.body.dataset.module=module;
   updateMobileShell();
   renderNav();
   const mobileAuth=$("mobileAuthBox"); if(mobileAuth) mobileAuth.style.display=currentUser?"none":"block";
 }catch(e){ console.warn("Fallback home error", e); }
}
window.addEventListener("DOMContentLoaded", () => setTimeout(renderFallbackHome, 300));
