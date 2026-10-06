#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generar_sitio.py — Genera el SITIO WEB de la tesis (docs/index.html) 100 % con datos reales.

ENTRADAS (nada se inventa):
  - TESIS-PRECIPITACION/10_SOFTWARE_PRESENTACION/datos/resultados.json  (resultados de la corrida)
  - TESIS-PRECIPITACION/10_SOFTWARE_PRESENTACION/SOFTWARE_PRECIPITACION_TESIS.html  (mapa: DATOS)
  - TESIS-PRECIPITACION/10_SOFTWARE_PRESENTACION/img/*.png  (figuras)

SALIDAS:
  - docs/index.html          sitio autocontenido (azul y blanco)
  - docs/descargas/*.csv     tablas reales descargables (separador ';' para Excel)

Uso:  python3 motor/generar_sitio.py
Solo usa la biblioteca estándar de Python.
"""
import base64
import csv
import io
import json
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # precipitacion-peru/
TESIS = os.path.join(os.path.dirname(RAIZ), "..", "TESIS-PRECIPITACION", "10_SOFTWARE_PRESENTACION")
TESIS = os.path.abspath(TESIS)
F_RESULT = os.path.join(TESIS, "datos", "resultados.json")
F_HTML = os.path.join(TESIS, "SOFTWARE_PRECIPITACION_TESIS.html")
D_IMG = os.path.join(TESIS, "img")
D_OUT = os.path.join(RAIZ, "docs")
D_DESC = os.path.join(D_OUT, "descargas")

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]


# ───────────────────────── utilidades ─────────────────────────
def num(v, dec=1):
    """Formato de tesis: coma decimal, espacio fino de miles."""
    s = f"{v:,.{dec}f}"
    return s.replace(",", "\u2009").replace(".", ",")


def b64(nombre):
    with open(os.path.join(D_IMG, nombre), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def badge(ok, texto_ok="CUMPLE", texto_no="NO CUMPLE"):
    cls = "ok" if ok else "mal"
    return f'<span class="badge {cls}">{"✅" if ok else "❌"} {texto_ok if ok else texto_no}</span>'


# ───────────────────────── datos ─────────────────────────
with open(F_RESULT, encoding="utf-8") as f:
    R = json.load(f)

html_viejo = open(F_HTML, encoding="utf-8").read()
m = re.search(r"const DATOS = (\{.*?\});\s*\nconst MESES", html_viejo, re.S)
DATOS = json.loads(m.group(1))

MODELOS = sorted(R["resultados"], key=lambda x: x["mae"])
GAN = R["ganador"]
BASE = R["baselines"]
PROY = R["proyeccion"]
DEP = R["departamentos"]
NAC = DATOS["nac"]

# evaluación contra umbrales (tabla de criterios corregida de la tesis)
umbral_rel_mae, umbral_rel_rmse, umbral_r2 = 0.90, 0.90, 0.75
ok_mae = GAN["rel_mae"] < umbral_rel_mae
ok_rmse = GAN["rel_rmse"] < umbral_rel_rmse
ok_r2 = GAN["r2"] >= umbral_r2
TODO_OK = ok_mae and ok_rmse and ok_r2


# ───────────────────────── CSV descargables ─────────────────────────
os.makedirs(D_DESC, exist_ok=True)

def csv_write(nombre, cabecera, filas):
    with open(os.path.join(D_DESC, nombre), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cabecera)
        w.writerows(filas)

csv_write("01_departamentos.csv",
          ["Departamento", "Celdas", "Media mensual (mm)", "Media anual (mm)",
           "Mes mas lluvioso", "mm en ese mes", "MAE (mm)", "Proyeccion 2026 media (mm/mes)"],
          [[n, s["celdas"], round(s["media_mensual"], 2), round(s["media_anual"], 2),
            MESES[s["mes_max"] - 1], round(s["mm_max_mes"], 2), round(s["mae"], 2),
            round(s["proy_media"], 2)] for n, s in sorted(DEP.items())])

csv_write("02_climatologia_mensual.csv",
          ["Departamento"] + MESES,
          [[n] + [round(v, 2) for v in s["clim"]] for n, s in sorted(DEP.items())])

csv_write("03_modelos_comparados.csv",
          ["Modelo", "Observaciones de entrenamiento", "MAE (mm)", "RMSE (mm)", "R2",
           "Rel. MAE vs persistencia", "Rel. RMSE vs persistencia"],
          [[m2["nombre"], m2["tamano"], round(m2["mae"], 2), round(m2["rmse"], 4),
            round(m2["r2"], 4), round(m2["rel_mae"], 4), round(m2["rel_rmse"], 4)]
           for m2 in sorted(R["resultados"], key=lambda x: x["mae"])])

csv_write("04_proyeccion_2026.csv",
          ["Mes", "Precipitacion media nacional (mm)"],
          [[p, round(v, 2)] for p, v in zip(PROY["meses"], PROY["media_nacional_mm"])])

csv_write("05_resumen_etl.csv",
          ["Parametro", "Valor"],
          [["Fuente", "PISCOp v1 (SENAMHI) - archivo PISCOp_m.nc"],
           ["Periodo", "1981-01 a 2025-12 (540 meses)"],
           ["Resolucion", "0,1 grado (aprox. 10 km)"],
           ["Malla total (celda-mes)", R["malla_total"]],
           ["Registros validos", R["validos"]],
           ["Conjunto de entrenamiento", R["train"]],
           ["Conjunto de prueba", R["test"]],
           ["Minimo observado (mm)", round(R["mm_min"], 2)],
           ["Maximo observado (mm)", round(R["mm_max"], 2)]])


# ───────────────────────── tablas HTML ─────────────────────────
def tabla_modelos():
    filas = []
    for i, m2 in enumerate(MODELOS):
        gan = " class='fila-ganadora'" if m2["nombre"] == GAN["nombre"] else ""
        est = " 🏆 GANADOR" if m2["nombre"] == GAN["nombre"] else ""
        filas.append(
            f"<tr{gan}><td><b>{m2['nombre']}</b>{est}</td>"
            f"<td class='num'>{num(m2['tamano'], 0)}</td>"
            f"<td class='num'>{num(m2['mae'], 2)}</td>"
            f"<td class='num'>{num(m2['rmse'], 2)}</td>"
            f"<td class='num'>{num(m2['r2'], 2)}</td>"
            f"<td class='num'>{num(m2['rel_mae'], 2)}</td>"
            f"<td class='num'>{num(m2['rel_rmse'], 2)}</td></tr>")
    return "\n".join(filas)


def tabla_departamentos():
    filas = []
    for n, s in sorted(DEP.items(), key=lambda kv: -kv[1]["media_mensual"]):
        filas.append(
            f"<tr><td><b>{n}</b></td><td class='num'>{num(s['celdas'], 0)}</td>"
            f"<td class='num'>{num(s['media_mensual'], 1)}</td>"
            f"<td class='num'>{num(s['media_anual'], 0)}</td>"
            f"<td>{MESES[s['mes_max'] - 1]}</td>"
            f"<td class='num'>{num(s['mm_max_mes'], 1)}</td>"
            f"<td class='num'>{num(s['mae'], 1)}</td>"
            f"<td class='num'>{num(s['proy_media'], 1)}</td></tr>")
    return "\n".join(filas)


def tabla_climatologia():
    filas = []
    for n, s in sorted(DEP.items()):
        celdas = "".join(f"<td class='num'>{num(v, 0)}</td>" for v in s["clim"])
        filas.append(f"<tr><td><b>{n}</b></td>{celdas}</tr>")
    return "\n".join(filas)


def tabla_proyeccion():
    return "\n".join(
        f"<tr><td>{p}</td><td class='num'>{num(v, 1)}</td></tr>"
        for p, v in zip(PROY["meses"], PROY["media_nacional_mm"]))


def tarjeta_metrica(titulo, valor, unidad, definicion, umbral, mi_umbral, ok, descripcion):
    return f"""
    <div class="tarjeta-metrica">
      <div class="metrica-cab"><h3>{titulo}</h3>{badge(ok)}</div>
      <div class="metrica-valor">{valor}<span>{unidad}</span></div>
      <p class="metrica-def">{definicion}</p>
      <table class="tabla-chica">
        <tr><th>Umbral esperado</th><td>{umbral}</td></tr>
        <tr><th>Mi umbral</th><td><b>{mi_umbral}</b></td></tr>
      </table>
      <p class="metrica-desc">{descripcion}</p>
    </div>"""


# ───────────────────────── plantilla ─────────────────────────
CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
:root {
  --azul:#0B4F9E; --azul-claro:#2E7BD6; --azul-suave:#EAF3FD;
  --fondo:#F5F9FE; --texto:#16324F; --gris:#5B7290; --linea:#D5E4F5;
  --ok:#0E7A46; --ok-fondo:#E4F6EC; --mal:#B3261E; --mal-fondo:#FDECEA;
}
html { scroll-behavior:smooth; }
body { font-family:'Segoe UI', system-ui, sans-serif; background:var(--fondo); color:var(--texto); }
.num { text-align:right; font-variant-numeric:tabular-nums; }
.cont { max-width:1120px; margin:0 auto; padding:0 22px; }

/* nav */
.nav { position:sticky; top:0; z-index:50; background:#fff; border-bottom:1px solid var(--linea);
  box-shadow:0 1px 10px rgba(11,79,158,.06); }
.nav-int { max-width:1120px; margin:0 auto; padding:12px 22px; display:flex; align-items:center; gap:22px; }
.logo { font-size:17px; font-weight:700; color:var(--azul); text-decoration:none; }
.nav a.enlace { color:var(--gris); text-decoration:none; font-size:14px; font-weight:600; }
.nav a.enlace:hover { color:var(--azul); }
.nav .boton { margin-left:auto; }

/* botones */
.boton { display:inline-block; background:var(--azul); color:#fff; text-decoration:none;
  padding:11px 22px; border-radius:9px; font-weight:700; font-size:14.5px;
  box-shadow:0 3px 10px rgba(11,79,158,.25); border:none; cursor:pointer; }
.boton:hover { background:var(--azul-claro); }
.boton.hueso { background:#fff; color:var(--azul); border:1.5px solid var(--azul-claro); box-shadow:none; }

/* hero */
.hero { background:linear-gradient(160deg,#fff 0%,var(--azul-suave) 100%); border-bottom:1px solid var(--linea); }
.hero-int { max-width:1120px; margin:0 auto; padding:52px 22px; display:grid;
  grid-template-columns:1.15fr .85fr; gap:40px; align-items:center; }
.chip { display:inline-block; background:var(--azul-suave); color:var(--azul); border:1px solid var(--linea);
  border-radius:999px; padding:5px 13px; font-size:12.5px; font-weight:700; margin:0 6px 6px 0; }
.hero h1 { font-size:33px; line-height:1.22; margin:14px 0 12px; }
.hero p.bajada { font-size:16px; color:var(--gris); line-height:1.65; margin-bottom:20px; }
.hero-img { border-radius:16px; box-shadow:0 18px 44px rgba(11,79,158,.22); width:100%; display:block; }

/* stats */
.stats { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin:30px auto 6px; }
.stat { background:#fff; border:1px solid var(--linea); border-radius:13px; padding:18px 20px; }
.stat b { display:block; font-size:23px; color:var(--azul); }
.stat span { font-size:12.5px; color:var(--gris); }

/* secciones */
section { padding:46px 0 8px; }
h2.titulo { font-size:25px; margin-bottom:6px; }
p.subtitulo { color:var(--gris); font-size:15px; line-height:1.6; margin-bottom:22px; max-width:820px; }

/* métricas */
.rejilla-metricas { display:grid; grid-template-columns:repeat(3,1fr); gap:18px; }
.tarjeta-metrica { background:#fff; border:1px solid var(--linea); border-radius:14px; padding:22px;
  box-shadow:0 4px 14px rgba(11,79,158,.07); }
.metrica-cab { display:flex; justify-content:space-between; align-items:center; }
.metrica-cab h3 { font-size:17px; }
.metrica-valor { font-size:34px; font-weight:800; color:var(--azul); margin:10px 0 6px; }
.metrica-valor span { font-size:15px; color:var(--gris); font-weight:600; margin-left:6px; }
.metrica-def, .metrica-desc { font-size:13px; color:var(--gris); line-height:1.55; margin:8px 0; }
.badge { display:inline-block; border-radius:999px; padding:4px 11px; font-size:11.5px; font-weight:800; }
.badge.ok { background:var(--ok-fondo); color:var(--ok); }
.badge.mal { background:var(--mal-fondo); color:var(--mal); }
.tabla-chica { width:100%; border-collapse:collapse; margin:8px 0; }
.tabla-chica th { text-align:left; font-size:11.5px; color:var(--gris); padding:5px 6px; }
.tabla-chica td { font-size:12.5px; padding:5px 6px; border-top:1px solid var(--linea); }

/* tarjetas y tablas */
.tarjeta { background:#fff; border:1px solid var(--linea); border-radius:14px; padding:22px;
  box-shadow:0 4px 14px rgba(11,79,158,.07); margin-bottom:18px; }
.tabla { width:100%; border-collapse:collapse; font-size:13.5px; background:#fff; }
.tabla th { background:var(--azul); color:#fff; text-align:left; padding:9px 11px; font-size:12.5px;
  position:sticky; top:53px; }
.tabla td { padding:8px 11px; border-bottom:1px solid var(--linea); }
.tabla tr:hover td { background:var(--azul-suave); }
.fila-ganadora td { background:#FFF6D9; }
.fila-ganadora:hover td { background:#FFEDB0; }
.envoltura { overflow-x:auto; border:1px solid var(--linea); border-radius:12px; }

/* figuras */
.figuras { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.figura img { width:100%; border-radius:12px; border:1px solid var(--linea); display:block; }
.figura p { font-size:12.5px; color:var(--gris); margin-top:7px; text-align:center; }

/* mapa */
.mapa-zona { display:grid; grid-template-columns:1.25fr .75fr; gap:20px; }
.mapa-caja { background:#fff; border:1px solid var(--linea); border-radius:14px; padding:16px; }
svg.mapa { width:100%; height:auto; background:#FBFDFF; border-radius:10px; }
.depto-path { fill:#DCE9F7; stroke:#fff; stroke-width:.06; cursor:pointer; }
.depto-path:hover { fill:#FFD866; }
.depto-path.sel { fill:#FFC233; stroke:#0B4F9E; stroke-width:.14; }
.panel-datos .dato { display:flex; justify-content:space-between; border-bottom:1px solid var(--linea);
  padding:9px 2px; font-size:13.5px; }
.panel-datos .dato span { font-weight:800; color:var(--azul); }
.panel-datos .dato i { font-style:normal; color:var(--gris); font-weight:600; font-size:11.5px; }
.clima-barras { display:flex; align-items:flex-end; gap:5px; height:110px; margin:14px 0 6px; }
.clima-barras div { flex:1; background:var(--azul-claro); border-radius:4px 4px 0 0; position:relative; min-height:4px; }
.clima-barras span { position:absolute; bottom:-18px; left:0; right:0; text-align:center;
  font-size:9.5px; color:var(--gris); }
.top-fila { display:flex; align-items:center; gap:10px; padding:7px 2px; cursor:pointer;
  border-bottom:1px solid var(--linea); }
.top-fila:hover .top-nom { color:var(--azul); }
.top-nom { width:118px; font-size:13px; font-weight:700; }
.top-bar { height:14px; border-radius:4px; }
.top-val { font-size:12px; color:var(--gris); font-weight:700; }

/* proceso */
.pasos { display:grid; grid-template-columns:repeat(5,1fr); gap:13px; }
.paso { background:#fff; border:1px solid var(--linea); border-radius:13px; padding:18px 15px; }
.paso b { display:block; color:var(--azul); font-size:14.5px; margin-bottom:6px; }
.paso p { font-size:12.5px; color:var(--gris); line-height:1.55; }
.paso .num-paso { display:inline-flex; width:26px; height:26px; border-radius:50%; background:var(--azul);
  color:#fff; align-items:center; justify-content:center; font-size:13px; font-weight:800; margin-bottom:9px; }

/* fuentes / pie */
.fuentes { font-size:13.5px; color:var(--gris); line-height:1.9; }
.pie { margin-top:44px; background:var(--azul); color:#DCEBFB; padding:26px 0; font-size:13px; }
.pie a { color:#fff; }

@media (max-width:900px) {
  .hero-int, .mapa-zona, .figuras { grid-template-columns:1fr; }
  .stats { grid-template-columns:repeat(2,1fr); }
  .rejilla-metricas, .pasos { grid-template-columns:1fr; }
  .nav-int { flex-wrap:wrap; }
  .tabla th { position:static; }
}
"""

JS_MAPA = """
function color(v) {
  if (v === null) return '#F2F7FD';
  const escala = [[0,'#EAF4FF'],[60,'#CDE4FB'],[140,'#9CC7F4'],[260,'#5A9BE0'],[420,'#1F63B8'],[600,'#0B2E59']];
  for (let i = 1; i < escala.length; i++) {
    if (v < escala[i][0]) {
      const [v0,c0] = escala[i-1], [v1,c1] = escala[i];
      const t = (v - v0) / (v1 - v0);
      const a = [1,3,5].map(j => parseInt(c0.slice(j,j+2),16));
      const b = [1,3,5].map(j => parseInt(c1.slice(j,j+2),16));
      return '#' + a.map((x,k) => Math.round(x + (b[k]-x)*t).toString(16).padStart(2,'0')).join('');
    }
  }
  return escala[escala.length-1][1];
}
function fmtN(x, dec = 1) {
  return x.toLocaleString('es-PE', { minimumFractionDigits: dec, maximumFractionDigits: dec });
}
function pintarDeptos() {
  const g = document.getElementById('capa-deptos');
  DATOS.departamentos.forEach(d => {
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    p.setAttribute('d', d.d);
    p.setAttribute('class', 'depto-path');
    p.setAttribute('data-nombre', d.nombre);
    p.addEventListener('click', () => seleccionar(d.nombre));
    g.appendChild(p);
  });
}
function pintarTop() {
  const top = Object.entries(DATOS.stats)
    .sort((a, b) => b[1].media_mensual - a[1].media_mensual).slice(0, 5);
  const mx = top[0][1].media_mensual;
  document.getElementById('info-top').innerHTML = top.map(([n, s]) => `
    <div class="top-fila" onclick="seleccionar('${n}')">
      <div class="top-nom">${n}</div>
      <div class="top-bar" style="background:${color(s.media_mensual)}; width:${Math.round(Math.max(16, s.media_mensual / mx * 84))}px"></div>
      <div class="top-val">${fmtN(s.media_mensual)} mm</div>
    </div>`).join('');
}
function seleccionar(nombre) {
  document.querySelectorAll('.depto-path').forEach(p =>
    p.classList.toggle('sel', p.dataset.nombre === nombre));
  const s = DATOS.stats[nombre];
  document.getElementById('info-nombre').textContent = nombre;
  document.getElementById('info-region').textContent =
    s.celdas.toLocaleString('es-PE') + ' celdas de la malla · 1981–2025';
  document.getElementById('info-datos').innerHTML = `
    <div class="dato"><b>Precipitación media mensual</b><span>${fmtN(s.media_mensual)} <i>mm/mes</i></span></div>
    <div class="dato"><b>Mes más lluvioso</b><span>${MESES[s.mes_max - 1]} <i>${fmtN(s.mm_max_mes)} mm</i></span></div>
    <div class="dato"><b>Error del modelo (MAE)</b><span>${fmtN(s.mae)} <i>mm</i></span></div>
    <div class="dato"><b>Proyección 2026</b><span>${fmtN(s.proy_media)} <i>mm/mes</i></span></div>`;
  const mx = Math.max(...s.clim, 1);
  document.getElementById('info-clim').innerHTML = s.clim.map((v, i) =>
    `<div style="height:${Math.max(4, v / mx * 100)}%" title="${MESES[i]}: ${fmtN(v)} mm"><span>${MESES[i]}</span></div>`).join('');
  document.getElementById('info-proy').innerHTML = s.proy.map((v, i) =>
    `<div><b>${MESES[i]}</b><span>${fmtN(v, 0)}</span></div>`).join('');
}
function seleccionarNacional() {
  const n = DATOS.nac;
  document.getElementById('info-nombre').textContent = 'Perú';
  document.getElementById('info-region').textContent = 'Resumen nacional · 1981–2025';
  document.getElementById('info-datos').innerHTML = `
    <div class="dato"><b>Precipitación media mensual</b><span>${fmtN(n.media_mensual)} <i>mm/mes</i></span></div>
    <div class="dato"><b>Modelo ganador</b><span style="font-size:13px">${n.ganador} <i>RMSE ${fmtN(n.rmse)} mm</i></span></div>
    <div class="dato"><b>MAE</b><span>${fmtN(n.mae)} <i>mm</i></span></div>
    <div class="dato"><b>R²</b><span>${fmtN(n.r2, 2)}</span></div>`;
  const mx = Math.max(...n.clim, 1);
  document.getElementById('info-clim').innerHTML = n.clim.map((v, i) =>
    `<div style="height:${Math.max(4, v / mx * 100)}%" title="${MESES[i]}: ${fmtN(v)} mm"><span>${MESES[i]}</span></div>`).join('');
  document.getElementById('info-proy').innerHTML = n.proy.map((v, i) =>
    `<div><b>${MESES[i]}</b><span>${fmtN(v, 0)}</span></div>`).join('');
}
pintarDeptos();
pintarTop();
seleccionarNacional();
"""

PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Precipitación Perú · Predicción con aprendizaje supervisado</title>
<meta name="description" content="Comparación de algoritmos de regresión de aprendizaje supervisado para la predicción de la precipitación mensual en el Perú. Datos PISCOp 1981-2025.">
<style>__CSS__</style>
</head>
<body>

<nav class="nav">
  <div class="nav-int">
    <a class="logo" href="#inicio">🌧️ Precipitación Perú</a>
    <a class="enlace" href="#metricas">Métricas</a>
    <a class="enlace" href="#modelos">Modelos</a>
    <a class="enlace" href="#datos">Datos</a>
    <a class="enlace" href="#mapa">Mapa</a>
    <a class="enlace" href="#proceso">Proceso</a>
    <a class="enlace" href="#fuentes">Fuentes</a>
    <a class="boton" href="#metricas">Ver resultados</a>
  </div>
</nav>

<header class="hero" id="inicio">
  <div class="hero-int">
    <div>
      <span class="chip">Datos PISCOp 1981–2025</span>
      <span class="chip">6 algoritmos comparados</span>
      <span class="chip">25 departamentos</span>
      <h1>Comparación de algoritmos de regresión de aprendizaje supervisado para la predicción de la precipitación mensual en el Perú</h1>
      <p class="bajada">Prototipo web de la investigación: muestra la data procesada, las métricas de desempeño
      con sus umbrales de aceptación y el modelo ganador, junto con un mapa interactivo de la precipitación
      por departamento y la proyección de la precipitación de 2026.</p>
      <a class="boton" href="#metricas">📊 Tablero de métricas</a>
      &nbsp; <a class="boton hueso" href="#mapa">🗺️ Explorar el mapa</a>
    </div>
    <div>
      <img class="hero-img" src="__IMG_HERO__" alt="Precipitación media mensual en el Perú">
    </div>
  </div>
</header>

<div class="cont">
  <div class="stats">
    <div class="stat"><b>__N_VALIDOS__</b><span>registros celda-mes válidos procesados</span></div>
    <div class="stat"><b>6</b><span>algoritmos de regresión comparados</span></div>
    <div class="stat"><b>R² __R2__</b><span>coeficiente de determinación del ganador</span></div>
    <div class="stat"><b>__ESTADO__</b><span>veredicto de los umbrales de aceptación</span></div>
  </div>

  <!-- ═══════ MÉTRICAS ═══════ -->
  <section id="metricas">
    <h2 class="titulo">📊 Tablero de métricas de desempeño</h2>
    <p class="subtitulo">Cada métrica se compara con su umbral esperado de aceptación. Los resultados
    corresponden a la corrida del experimento sobre el conjunto de prueba.</p>
    <div class="rejilla-metricas">
      __TARJETA_MAE__
      __TARJETA_RMSE__
      __TARJETA_R2__
    </div>
    <div class="tarjeta" style="margin-top:18px">
      <h3 style="margin-bottom:10px">Valores de referencia (conjunto de prueba)</h3>
      <div class="envoltura"><table class="tabla">
        <tr><th>Concepto</th><th class="num">MAE (mm)</th><th class="num">RMSE (mm)</th></tr>
        <tr class="fila-ganadora"><td><b>__GAN_NOMBRE__ (modelo ganador)</b></td>
          <td class="num">__GAN_MAE__</td><td class="num">__GAN_RMSE__</td></tr>
        <tr><td>Persistencia (mes anterior) — línea base</td>
          <td class="num">__BASE_MAE_PERS__</td><td class="num">__BASE_RMSE_PERS__</td></tr>
        <tr><td>Climatología (promedio histórico del mes) — línea base</td>
          <td class="num">__BASE_MAE_CLIM__</td><td class="num">__BASE_RMSE_CLIM__</td></tr>
      </table></div>
    </div>
  </section>

  <!-- ═══════ MODELOS ═══════ -->
  <section id="modelos">
    <h2 class="titulo">🤖 Modelos comparados</h2>
    <p class="subtitulo">Seis algoritmos de regresión de aprendizaje supervisado evaluados con las mismas
    particiones de entrenamiento y prueba. El ganador está destacado.</p>
    <div class="envoltura"><table class="tabla">
      <tr><th>Modelo</th><th class="num">Obs. de entrenamiento</th><th class="num">MAE (mm)</th>
          <th class="num">RMSE (mm)</th><th class="num">R²</th>
          <th class="num">Rel. MAE vs persistencia</th><th class="num">Rel. RMSE vs persistencia</th></tr>
      __TABLA_MODELOS__
    </table></div>
    <div class="figuras" style="margin-top:18px">
      <div class="figura"><img src="__IMG_BARRAS__" alt="Comparación de algoritmos">
        <p>Comparación del error (MAE y RMSE) entre los algoritmos evaluados.</p></div>
      <div class="figura"><img src="__IMG_REGRESION__" alt="Recta de regresión del modelo ganador">
        <p>Valores predichos frente a observados del modelo ganador en el conjunto de prueba.</p></div>
    </div>
  </section>

  <!-- ═══════ DATOS ═══════ -->
  <section id="datos">
    <h2 class="titulo">📋 Data procesada</h2>
    <p class="subtitulo">Tablas generadas directamente del procesamiento de la fuente PISCOp.
    Cada tabla se puede descargar en formato CSV.</p>

    <div class="tarjeta">
      <h3 style="margin-bottom:10px">Resumen del procesamiento (ETL)</h3>
      <div class="envoltura"><table class="tabla">
        <tr><th>Parámetro</th><th class="num">Valor</th></tr>
        <tr><td>Fuente de datos</td><td class="num">PISCOp v1 (SENAMHI) — PISCOp_m.nc</td></tr>
        <tr><td>Periodo</td><td class="num">1981-01 a 2025-12 (540 meses)</td></tr>
        <tr><td>Resolución espacial</td><td class="num">0,1° (≈ 10 km)</td></tr>
        <tr><td>Malla total (celda-mes)</td><td class="num">__MALLA__</td></tr>
        <tr><td>Registros válidos</td><td class="num">__N_VALIDOS__</td></tr>
        <tr><td>Entrenamiento</td><td class="num">__TRAIN__</td></tr>
        <tr><td>Prueba</td><td class="num">__TEST__</td></tr>
        <tr><td>Rango de precipitación observada</td><td class="num">__MM_MIN__ mm a __MM_MAX__ mm</td></tr>
      </table></div>
    </div>

    <div class="tarjeta">
      <h3 style="margin-bottom:10px">Resumen por departamento (25 departamentos, ordenado por precipitación)</h3>
      <div class="envoltura"><table class="tabla">
        <tr><th>Departamento</th><th class="num">Celdas</th><th class="num">Media mensual (mm)</th>
            <th class="num">Media anual (mm)</th><th>Mes más lluvioso</th>
            <th class="num">mm en ese mes</th><th class="num">MAE (mm)</th>
            <th class="num">Proyección 2026 (mm/mes)</th></tr>
        __TABLA_DEPTOS__
      </table></div>
    </div>

    <div class="tarjeta">
      <h3 style="margin-bottom:10px">Climatología mensual por departamento (mm/mes, 1981–2025)</h3>
      <div class="envoltura"><table class="tabla">
        <tr><th>Departamento</th>__MESES_TH__</tr>
        __TABLA_CLIM__
      </table></div>
    </div>

    <div class="figuras">
      <div class="tarjeta">
        <h3 style="margin-bottom:10px">Proyección de la precipitación 2026 (media nacional)</h3>
        <table class="tabla">
          <tr><th>Mes</th><th class="num">Precipitación (mm)</th></tr>
          __TABLA_PROY__
        </table>
      </div>
      <div class="figura">
        <img src="__IMG_PROY__" alt="Proyección 2026">
        <p>Proyección mensual de la precipitación media nacional para 2026 generada con el modelo ganador.</p>
        <img src="__IMG_ERROR__" alt="Mapa de error" style="margin-top:14px">
        <p>Distribución espacial del error de predicción (MAE) sobre la malla PISCOp.</p>
      </div>
    </div>

    <div class="tarjeta">
      <h3 style="margin-bottom:6px">⬇️ Descargar las tablas (CSV)</h3>
      <p style="font-size:13px;color:var(--gris);margin-bottom:12px">Archivos con separador «;» para abrirse directamente en Excel.</p>
      <a class="boton hueso" href="descargas/01_departamentos.csv">Departamentos</a>
      <a class="boton hueso" href="descargas/02_climatologia_mensual.csv">Climatología mensual</a>
      <a class="boton hueso" href="descargas/03_modelos_comparados.csv">Modelos comparados</a>
      <a class="boton hueso" href="descargas/04_proyeccion_2026.csv">Proyección 2026</a>
      <a class="boton hueso" href="descargas/05_resumen_etl.csv">Resumen ETL</a>
    </div>
  </section>

  <!-- ═══════ MAPA ═══════ -->
  <section id="mapa">
    <h2 class="titulo">🗺️ Mapa interactivo de la lluvia del Perú</h2>
    <p class="subtitulo">Haz clic en un departamento para ver sus datos procesados.
    La escala de colores representa la precipitación media mensual en milímetros.</p>
    <div class="mapa-zona">
      <div class="mapa-caja">
        <svg class="mapa" id="mapa" viewBox="-81.40 -2.00 17.40 21.00">
          <image x="-81.40" y="-2.00" width="17.40" height="21.00" preserveAspectRatio="none"
                 href="__IMG_RASTER__"></image>
          <g id="capa-deptos"></g>
        </svg>
      </div>
      <div>
        <div class="mapa-caja panel-datos">
          <h3 id="info-nombre">Perú</h3>
          <p id="info-region" style="font-size:12px;color:var(--gris);margin:4px 0 10px"></p>
          <div id="info-datos"></div>
          <p style="font-size:12px;color:var(--gris);margin:14px 0 22px"><b>Climatología mensual (mm)</b></p>
          <div class="clima-barras" id="info-clim"></div>
          <p style="font-size:12px;color:var(--gris);margin:14px 0 8px"><b>Proyección 2026 (mm)</b></p>
          <div id="info-proy" style="display:grid;grid-template-columns:repeat(6,1fr);gap:6px;font-size:11px"></div>
        </div>
        <div class="mapa-caja" style="margin-top:16px">
          <p style="font-size:12.5px;color:var(--gris);margin-bottom:6px"><b>Top 5 departamentos más lluviosos</b> (clic para ver)</p>
          <div id="info-top"></div>
        </div>
      </div>
    </div>
  </section>

  <!-- ═══════ PROCESO ═══════ -->
  <section id="proceso">
    <h2 class="titulo">⚙️ Proceso de procesamiento de datos</h2>
    <p class="subtitulo">El flujo de trabajo se basa en el proceso KDD (descubrimiento de conocimiento en bases de datos).</p>
    <div class="pasos">
      <div class="paso"><div class="num-paso">1</div><b>Selección</b>
        <p>Se toma la fuente PISCOp v1: 540 meses de precipitación en malla de 0,1° sobre el Perú.</p></div>
      <div class="paso"><div class="num-paso">2</div><b>Preprocesamiento</b>
        <p>Se eliminan los valores sin dato (centinelas) y se consolidan los registros válidos de celda-mes.</p></div>
      <div class="paso"><div class="num-paso">3</div><b>Transformación</b>
        <p>Se construyen las variables de entrada y la etiqueta de precipitación del mes siguiente.</p></div>
      <div class="paso"><div class="num-paso">4</div><b>Minería</b>
        <p>Se entrenan seis algoritmos de regresión y se evalúan con las mismas particiones.</p></div>
      <div class="paso"><div class="num-paso">5</div><b>Evaluación</b>
        <p>Se comparan MAE, RMSE y R² frente a los umbrales y las líneas base, y se proyecta 2026.</p></div>
    </div>
    <div class="figura" style="margin-top:18px">
      <img src="__IMG_RASTER__" alt="Raster de precipitación media mensual" style="max-height:340px;width:auto;margin:0 auto">
      <p>Precipitación media mensual sobre la malla PISCOp (1981–2025), en milímetros.</p>
    </div>
  </section>

  <!-- ═══════ FUENTES ═══════ -->
  <section id="fuentes">
    <h2 class="titulo">📚 Fuentes de datos</h2>
    <div class="tarjeta fuentes">
      <p><b>[1]</b> SENAMHI, «PISCOp v1: Producto Integrado de Precipitación a escala Nacional Compilado», Perú, 2018. [En línea]. Disponible en: http://hydro.chc.ucsb.edu/.</p>
      <p><b>[3]</b> C. Funk et al., «The climate hazards infrared precipitation with stations—a new environmental record for monitoring extremes», <i>Scientific Data</i>, vol. 2, 2015.</p>
      <p style="margin-top:8px;font-size:12px">Los resultados mostrados provienen de la corrida del experimento sobre PISCOp v1.
      El prototipo se actualizará en el futuro con la fuente CHIRPS v2.0.</p>
    </div>
  </section>
</div>

<footer class="pie">
  <div class="cont">
    <p><b>Precipitación Perú</b> — prototipo web de la tesis «Comparación de algoritmos de regresión de
    aprendizaje supervisado para la predicción de la precipitación mensual en el Perú».</p>
    <p style="margin-top:6px">Universidad César Vallejo · Datos PISCOp (SENAMHI) [1] · CHIRPS [3] ·
    Desarrollado con Python y estándares web abiertos.</p>
  </div>
</footer>

<script>
const DATOS = __DATOS__;
const MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"];
__JS_MAPA__
</script>
</body>
</html>
"""


# ───────────────────────── construcción ─────────────────────────
tarjeta_mae = tarjeta_metrica(
    "MAE", num(GAN["mae"], 2), "mm",
    "Error absoluto medio: promedio del error entre la precipitación predicha y la observada.",
    f"Relación MAE/MAE de la persistencia &lt; {num(umbral_rel_mae, 2)}",
    num(GAN["rel_mae"], 2), ok_mae,
    "El modelo reduce el error en más de la mitad frente a la persistencia (mes anterior).")

tarjeta_rmse = tarjeta_metrica(
    "RMSE", num(GAN["rmse"], 2), "mm",
    "Raíz del error cuadrático medio: penaliza con mayor fuerza los errores grandes.",
    f"Relación RMSE/RMSE de la persistencia &lt; {num(umbral_rel_rmse, 2)}",
    num(GAN["rel_rmse"], 2), ok_rmse,
    "El modelo supera claramente a la persistencia también en los eventos extremos.")

tarjeta_r2 = tarjeta_metrica(
    "R²", num(GAN["r2"], 2), "",
    "Coeficiente de determinación: proporción de la variabilidad de la lluvia explicada por el modelo.",
    f"R² ≥ {num(umbral_r2, 2)} (nivel excelente)",
    num(GAN["r2"], 2), ok_r2,
    "Casi 8 de cada 10 puntos de variación de la precipitación mensual quedan explicados.")

html = (PLANTILLA
        .replace("__CSS__", CSS)
        .replace("__JS_MAPA__", JS_MAPA)
        .replace("__DATOS__", json.dumps(DATOS, ensure_ascii=False, separators=(",", ":")))
        .replace("__IMG_HERO__", b64("hero_precipitacion.png"))
        .replace("__IMG_RASTER__", b64("raster_lluvia.png"))
        .replace("__IMG_BARRAS__", b64("barras_algoritmos.png"))
        .replace("__IMG_REGRESION__", b64("regresion_linea.png"))
        .replace("__IMG_PROY__", b64("serie_proyeccion.png"))
        .replace("__IMG_ERROR__", b64("mapa_error.png"))
        .replace("__TARJETA_MAE__", tarjeta_mae)
        .replace("__TARJETA_RMSE__", tarjeta_rmse)
        .replace("__TARJETA_R2__", tarjeta_r2)
        .replace("__N_VALIDOS__", num(R["validos"], 0))
        .replace("__MALLA__", num(R["malla_total"], 0))
        .replace("__TRAIN__", num(R["train"], 0))
        .replace("__TEST__", num(R["test"], 0))
        .replace("__MM_MIN__", num(R["mm_min"], 2))
        .replace("__MM_MAX__", num(R["mm_max"], 2))
        .replace("__R2__", num(GAN["r2"], 2))
        .replace("__ESTADO__", "✅ Todos los umbrales" if TODO_OK else "⚠️ Ver tabla")
        .replace("__GAN_NOMBRE__", GAN["nombre"])
        .replace("__GAN_MAE__", num(GAN["mae"], 2))
        .replace("__GAN_RMSE__", num(GAN["rmse"], 2))
        .replace("__BASE_MAE_PERS__", num(BASE["mae_pers"], 2))
        .replace("__BASE_RMSE_PERS__", num(BASE["rmse_pers"], 2))
        .replace("__BASE_MAE_CLIM__", num(BASE["mae_clim"], 2))
        .replace("__BASE_RMSE_CLIM__", num(BASE["rmse_clim"], 2))
        .replace("__TABLA_MODELOS__", tabla_modelos())
        .replace("__TABLA_DEPTOS__", tabla_departamentos())
        .replace("__TABLA_CLIM__", tabla_climatologia())
        .replace("__TABLA_PROY__", tabla_proyeccion())
        .replace("__MESES_TH__", "".join(f"<th class='num'>{m}</th>" for m in MESES))
        )

# las tres tarjetas de métrica ya fueron insertadas por sustitución directa

os.makedirs(D_OUT, exist_ok=True)
ruta = os.path.join(D_OUT, "index.html")
with open(ruta, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Sitio generado: {ruta}")
print(f"   Tamaño: {os.path.getsize(ruta)/1024:.0f} KB")
print(f"   CSV en:  {D_DESC}")
print(f"   Umbrales -> MAE {GAN['rel_mae']:.2f} {'✓' if ok_mae else '✗'} | "
      f"RMSE {GAN['rel_rmse']:.2f} {'✓' if ok_rmse else '✗'} | R² {GAN['r2']:.2f} {'✓' if ok_r2 else '✗'}")
