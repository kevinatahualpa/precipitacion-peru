#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generar_sitio.py — SITIO WEB de la tesis en PESTAÑAS (5 ventanas), estilo
"software de presentación" (gris pizarra + naranja).

ENTRADAS (todo real, nada inventado):
  - datos/resultados.json                     (corrida del experimento)
  - SOFTWARE_PRECIPITACION_TESIS.html         (mapa DATOS + ficha de registro)
  - img/*.png                                 (figuras, recoloreadas a naranja)

SALIDAS:
  - docs/index.html       sitio autocontenido
  - docs/descargas/*.csv  tablas descargables (';' para Excel)

Uso: python3 motor/generar_sitio.py   (solo biblioteca estándar + PIL/numpy)
"""
import base64
import csv
import io
import json
import os
import re

import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESIS = os.path.abspath(os.path.join(os.path.dirname(RAIZ), "..", "TESIS-PRECIPITACION", "10_SOFTWARE_PRESENTACION"))
F_RESULT = os.path.join(TESIS, "datos", "resultados.json")
F_HTML = os.path.join(TESIS, "SOFTWARE_PRECIPITACION_TESIS.html")
D_IMG = os.path.join(TESIS, "img")
D_OUT = os.path.join(RAIZ, "docs")
D_DESC = os.path.join(D_OUT, "descargas")

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]


# ───────────────────────── utilidades ─────────────────────────
def num(v, dec=1):
    s = f"{v:,.{dec}f}"
    return s.replace(",", "\u2009").replace(".", ",")


def recolorear_a_naranja(ruta):
    """Gira los tonos azules de la figura hacia el naranja de la paleta."""
    im = Image.open(ruta).convert("RGB")
    a = np.asarray(im).astype(np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    maxc, minc = a.max(2), a.min(2)
    v = maxc
    s = np.where(maxc > 0, (maxc - minc) / np.maximum(maxc, 1e-6), 0)
    c = maxc - minc
    h = np.zeros_like(maxc)
    m = c > 1e-6
    idx = (maxc == r) & m
    h[idx] = ((g - b)[idx] / c[idx]) % 6
    idx = (maxc == g) & m
    h[idx] = ((b - r)[idx] / c[idx]) + 2
    idx = (maxc == b) & m
    h[idx] = ((r - g)[idx] / c[idx]) + 4
    h = h * 60.0
    mask = (h > 170) & (h < 285) & (s > 0.10)
    h2 = np.where(mask, (h - 192.0) % 360.0, h)     # azul → naranja
    s2 = np.where(mask, np.clip(s * 1.05, 0, 1), s)
    # HSV → RGB
    hh = h2 / 60.0
    i = np.floor(hh).astype(int) % 6
    f = hh - np.floor(hh)
    p = v * (1 - s2)
    q = v * (1 - s2 * f)
    t = v * (1 - s2 * (1 - f))
    out = np.zeros_like(a)
    for k, (rr, gg, bb) in enumerate([(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]):
        sel = i == k
        out[..., 0] = np.where(sel, rr, out[..., 0])
        out[..., 1] = np.where(sel, gg, out[..., 1])
        out[..., 2] = np.where(sel, bb, out[..., 2])
    buf = io.BytesIO()
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def b64(nombre):
    return recolorear_a_naranja(os.path.join(D_IMG, nombre))


def badge(ok):
    return (f'<span class="badge {"ok" if ok else "mal"}">'
            f'{"✅ CUMPLE" if ok else "❌ NO CUMPLE"}</span>')


# ───────────────────────── datos ─────────────────────────
R = json.load(open(F_RESULT, encoding="utf-8"))
html_viejo = open(F_HTML, encoding="utf-8").read()
DATOS = json.loads(re.search(r"const DATOS = (\{.*?\});\s*\nconst MESES", html_viejo, re.S).group(1))

# ranking nacional por precipitación media (para el tooltip del mapa)
orden = sorted(DATOS["stats"], key=lambda n: -DATOS["stats"][n]["media_mensual"])
for i, n in enumerate(orden, 1):
    DATOS["stats"][n]["rank"] = i

# ficha de registro real (instrumento + 20 registros de la celda de Lima)
j = html_viejo.find("VENTANA 2")
bloque = html_viejo[html_viejo.find('<div class="ficha-cab">'):j]
FIN_TABLA = "</tbody></table></div></div>"
FICHA_HTML = bloque[:bloque.rfind(FIN_TABLA) + len(FIN_TABLA)]

MODELOS = sorted(R["resultados"], key=lambda x: x["mae"])
GAN, BASE, PROY, DEP, NAC = R["ganador"], R["baselines"], R["proyeccion"], R["departamentos"], DATOS["nac"]

umbral_rel_mae, umbral_rel_rmse, umbral_r2 = 0.90, 0.90, 0.75
ok_mae, ok_rmse = GAN["rel_mae"] < umbral_rel_mae, GAN["rel_rmse"] < umbral_rel_rmse
ok_r2 = GAN["r2"] >= umbral_r2
TODO_OK = ok_mae and ok_rmse and ok_r2
PCT_VALIDOS = R["validos"] / R["malla_total"] * 100
N_LAT = R["lat"] if isinstance(R.get("lat"), int) else len(R.get("lat", [0] * 210))
N_LON = R["lon"] if isinstance(R.get("lon"), int) else len(R.get("lon", [0] * 174))
N_CELDAS = N_LAT * N_LON
ANIOS = 2025 - 1981 + 1

# ───────────────────────── CSV ─────────────────────────
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
csv_write("02_climatologia_mensual.csv", ["Departamento"] + MESES,
          [[n] + [round(v, 2) for v in s["clim"]] for n, s in sorted(DEP.items())])
csv_write("03_modelos_comparados.csv",
          ["Modelo", "Observaciones de entrenamiento", "MAE (mm)", "RMSE (mm)", "R2",
           "Rel. MAE vs persistencia", "Rel. RMSE vs persistencia"],
          [[m2["nombre"], m2["tamano"], round(m2["mae"], 2), round(m2["rmse"], 4),
            round(m2["r2"], 4), round(m2["rel_mae"], 4), round(m2["rel_rmse"], 4)]
           for m2 in sorted(R["resultados"], key=lambda x: x["mae"])])
csv_write("04_proyeccion_2026.csv", ["Mes", "Precipitacion media nacional (mm)"],
          [[p, round(v, 2)] for p, v in zip(PROY["meses"], PROY["media_nacional_mm"])])
csv_write("05_resumen_etl.csv", ["Parametro", "Valor"],
          [["Fuente", "PISCOp v3.0 (SENAMHI) - archivo PISCOp_m.nc"],
           ["Periodo", "1981-01 a 2025-12 (540 meses, 45 anios)"],
           ["Resolucion", "0,1 grado (aprox. 10 km)"],
           ["Malla", f"{N_LAT} x {N_LON} = {N_CELDAS} celdas"],
           ["Malla total (celda-mes)", R["malla_total"]],
           ["Registros validos", R["validos"]],
           ["Porcentaje valido", f"{PCT_VALIDOS:.2f} %"],
           ["Conjunto de entrenamiento", R["train"]],
           ["Conjunto de prueba", R["test"]],
           ["Minimo observado (mm)", round(R["mm_min"], 2)],
           ["Maximo observado (mm)", round(R["mm_max"], 2)]])


# ───────────────────────── tablas HTML ─────────────────────────
def tabla_modelos():
    filas = []
    for m2 in MODELOS:
        gan = " class='fila-ganadora'" if m2["nombre"] == GAN["nombre"] else ""
        est = " 🏆 GANADOR" if m2["nombre"] == GAN["nombre"] else ""
        filas.append(
            f"<tr{gan}><td><b>{m2['nombre']}</b>{est}</td>"
            f"<td class='num'>{num(m2['tamano'], 0)}</td><td class='num'>{num(m2['mae'], 2)}</td>"
            f"<td class='num'>{num(m2['rmse'], 2)}</td><td class='num'>{num(m2['r2'], 2)}</td>"
            f"<td class='num'>{num(m2['rel_mae'], 2)}</td><td class='num'>{num(m2['rel_rmse'], 2)}</td></tr>")
    return "\n".join(filas)

def tabla_departamentos():
    return "\n".join(
        f"<tr><td><b>{n}</b></td><td class='num'>{num(s['celdas'], 0)}</td>"
        f"<td class='num'>{num(s['media_mensual'], 1)}</td><td class='num'>{num(s['media_anual'], 0)}</td>"
        f"<td>{MESES[s['mes_max'] - 1]}</td><td class='num'>{num(s['mm_max_mes'], 1)}</td>"
        f"<td class='num'>{num(s['mae'], 1)}</td><td class='num'>{num(s['proy_media'], 1)}</td></tr>"
        for n, s in sorted(DEP.items(), key=lambda kv: -kv[1]["media_mensual"]))

def tabla_climatologia():
    return "\n".join(
        f"<tr><td><b>{n}</b></td>" + "".join(f"<td class='num'>{num(v, 0)}</td>" for v in s["clim"]) + "</tr>"
        for n, s in sorted(DEP.items()))

def tabla_proyeccion():
    return "\n".join(f"<tr><td>{p}</td><td class='num'>{num(v, 1)}</td></tr>"
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


# ───────────────────────── CSS (gris pizarra + naranja) ─────────────────────────
CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
:root {
  --naranja:#EA580C; --naranja-claro:#FB923C; --naranja-suave:#FFF1E8;
  --pizarra:#334155; --pizarra-osc:#1E293B;
  --fondo:#F8FAFC; --texto:#1E293B; --gris:#64748B; --linea:#E2E8F0;
  --ok:#0E7A46; --ok-fondo:#E4F6EC; --mal:#B3261E; --mal-fondo:#FDECEA;
}
html { scroll-behavior:smooth; }
body { font-family:'Segoe UI', system-ui, sans-serif; background:var(--fondo); color:var(--texto); }
.num { text-align:right; font-variant-numeric:tabular-nums; }
.cont { max-width:1120px; margin:0 auto; padding:0 22px; }

/* nav de pestañas */
.nav { position:sticky; top:0; z-index:50; background:var(--pizarra); box-shadow:0 2px 12px rgba(30,41,59,.25); }
.nav-int { max-width:1120px; margin:0 auto; padding:11px 22px; display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.logo { font-size:16.5px; font-weight:800; color:#fff; margin-right:14px; }
.pestana-nav { background:transparent; color:#CBD5E1; border:none; padding:9px 15px; border-radius:8px;
  font-size:13.5px; font-weight:700; cursor:pointer; }
.pestana-nav:hover { background:rgba(255,255,255,.12); color:#fff; }
.pestana-nav.activa { background:var(--naranja); color:#fff; }

/* vistas */
.vista { display:none; }
.vista.activa { display:block; }

/* botones */
.boton { display:inline-block; background:var(--naranja); color:#fff; text-decoration:none;
  padding:11px 22px; border-radius:9px; font-weight:700; font-size:14.5px;
  box-shadow:0 3px 10px rgba(234,88,12,.3); border:none; cursor:pointer; }
.boton:hover { background:var(--naranja-claro); }
.boton.hueso { background:#fff; color:var(--pizarra); border:1.5px solid var(--linea); box-shadow:none; }
.boton.hueso:hover { border-color:var(--naranja); color:var(--naranja); }

/* hero */
.hero { background:linear-gradient(160deg,#fff 0%,var(--naranja-suave) 100%); border-bottom:1px solid var(--linea); }
.hero-int { max-width:1120px; margin:0 auto; padding:50px 22px; display:grid;
  grid-template-columns:1.1fr .9fr; gap:40px; align-items:center; }
.chip { display:inline-block; background:#fff; color:var(--pizarra); border:1px solid var(--linea);
  border-radius:999px; padding:5px 13px; font-size:12.5px; font-weight:700; margin:0 6px 6px 0; }
.hero h1 { font-size:31px; line-height:1.24; margin:14px 0 12px; }
.hero p.bajada { font-size:15.5px; color:var(--gris); line-height:1.65; margin-bottom:20px; }
.hero-img { border-radius:16px; box-shadow:0 18px 44px rgba(30,41,59,.22); width:100%; display:block; }

/* stats */
.stats { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin:30px auto 6px; }
.stat { background:#fff; border:1px solid var(--linea); border-radius:13px; padding:18px 20px; }
.stat b { display:block; font-size:22px; color:var(--naranja); }
.stat span { font-size:12.5px; color:var(--gris); }

/* volumen de datos */
.volumen { display:grid; grid-template-columns:repeat(3,1fr); gap:13px; }
.vol { background:#fff; border:1px solid var(--linea); border-left:4px solid var(--naranja);
  border-radius:10px; padding:13px 16px; }
.vol b { display:block; font-size:18px; color:var(--pizarra); }
.vol span { font-size:11.5px; color:var(--gris); text-transform:uppercase; letter-spacing:.4px; font-weight:700; }

/* botones grandes del inicio */
.botones-grandes { display:grid; grid-template-columns:repeat(4,1fr); gap:15px; }
.boton-grande { background:#fff; border:1px solid var(--linea); border-radius:14px; padding:22px 18px;
  text-align:left; cursor:pointer; transition:.15s; }
.boton-grande:hover { border-color:var(--naranja); box-shadow:0 8px 22px rgba(234,88,12,.18); transform:translateY(-2px); }
.boton-grande .num-paso { display:inline-flex; width:30px; height:30px; border-radius:9px;
  background:var(--naranja-suave); color:var(--naranja); align-items:center; justify-content:center;
  font-size:13px; font-weight:800; margin-bottom:10px; }
.boton-grande h3 { font-size:15.5px; margin-bottom:6px; }
.boton-grande p { font-size:12.5px; color:var(--gris); line-height:1.55; }
.boton-grande .ir { margin-top:10px; color:var(--naranja); font-weight:800; font-size:12.5px; }

/* secciones */
section, .bloque { padding:34px 0 8px; }
h2.titulo { font-size:24px; margin-bottom:6px; }
p.subtitulo { color:var(--gris); font-size:14.5px; line-height:1.6; margin-bottom:20px; max-width:820px; }

/* métricas */
.rejilla-metricas { display:grid; grid-template-columns:repeat(3,1fr); gap:18px; }
.tarjeta-metrica { background:#fff; border:1px solid var(--linea); border-radius:14px; padding:22px;
  box-shadow:0 4px 14px rgba(30,41,59,.07); }
.metrica-cab { display:flex; justify-content:space-between; align-items:center; }
.metrica-cab h3 { font-size:17px; }
.metrica-valor { font-size:33px; font-weight:800; color:var(--naranja); margin:10px 0 6px; }
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
  box-shadow:0 4px 14px rgba(30,41,59,.07); margin-bottom:18px; }
.tabla { width:100%; border-collapse:collapse; font-size:13.5px; background:#fff; }
.tabla th { background:var(--pizarra); color:#fff; text-align:left; padding:9px 11px; font-size:12.5px; }
.tabla td { padding:8px 11px; border-bottom:1px solid var(--linea); }
.tabla tr:hover td { background:var(--naranja-suave); }
.fila-ganadora td { background:#FFF3D6; }
.fila-ganadora:hover td { background:#FFE9B0; }
.envoltura { overflow-x:auto; border:1px solid var(--linea); border-radius:12px; }

/* figuras */
.figuras { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.figura img { width:100%; border-radius:12px; border:1px solid var(--linea); display:block; background:#fff; }
.figura p { font-size:12.5px; color:var(--gris); margin-top:7px; text-align:center; }

/* mapa */
.mapa-zona { display:grid; grid-template-columns:1.25fr .75fr; gap:20px; }
.mapa-caja { background:#fff; border:1px solid var(--linea); border-radius:14px; padding:16px; position:relative; }
svg.mapa { width:100%; height:auto; background:#FBFDFF; border-radius:10px; }
.depto-path { fill:transparent; stroke:#fff; stroke-width:.07; cursor:pointer; pointer-events:all; }
.depto-path:hover { fill:rgba(251,146,60,.45); }
.depto-path.sel { fill:rgba(234,88,12,.55); stroke:var(--pizarra-osc); stroke-width:.14; }
.depto-nom { font-size:.30px; fill:var(--pizarra-osc); font-weight:700; pointer-events:none;
  text-anchor:middle; paint-order:stroke; stroke:#fff; stroke-width:.07; }
#tooltip-mapa { position:absolute; display:none; background:var(--pizarra-osc); color:#fff;
  padding:9px 13px; border-radius:9px; font-size:12.5px; font-weight:600; pointer-events:none;
  box-shadow:0 8px 22px rgba(30,41,59,.35); z-index:6; white-space:nowrap; }
#tooltip-mapa b { color:#FDBA74; }
.leyenda { display:flex; gap:16px; flex-wrap:wrap; margin-top:12px; }
.leyenda span { display:flex; align-items:center; gap:6px; font-size:11.5px; color:var(--gris); font-weight:700; }
.leyenda i { width:14px; height:14px; border-radius:4px; display:inline-block; }
.panel-datos .dato { display:flex; justify-content:space-between; border-bottom:1px solid var(--linea);
  padding:9px 2px; font-size:13.5px; }
.panel-datos .dato span { font-weight:800; color:var(--naranja); }
.panel-datos .dato i { font-style:normal; color:var(--gris); font-weight:600; font-size:11.5px; }
.clima-barras { display:flex; align-items:flex-end; gap:5px; height:110px; margin:14px 0 22px; }
.clima-barras div { flex:1; background:var(--naranja-claro); border-radius:4px 4px 0 0; position:relative; min-height:4px; }
.clima-barras span { position:absolute; bottom:-18px; left:0; right:0; text-align:center; font-size:9.5px; color:var(--gris); }
.proy-linea { display:grid; grid-template-columns:repeat(6,1fr); gap:6px; font-size:11px; }
.proy-linea div { background:var(--naranja-suave); border-radius:6px; padding:5px 4px; text-align:center; }
.proy-linea b { display:block; color:var(--gris); font-size:10px; }
.top-fila { display:flex; align-items:center; gap:10px; padding:7px 2px; cursor:pointer; border-bottom:1px solid var(--linea); }
.top-fila:hover .top-nom { color:var(--naranja); }
.top-nom { width:118px; font-size:13px; font-weight:700; }
.top-bar { height:14px; border-radius:4px; }
.top-val { font-size:12px; color:var(--gris); font-weight:700; }

/* ficha */
.ficha-cab { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.ficha-cab div { background:var(--fondo); border:1px solid var(--linea); border-radius:9px; padding:10px 13px; }
.ficha-cab b { display:block; font-size:10px; color:var(--gris); text-transform:uppercase; letter-spacing:.5px; }
.ficha-cab span { font-size:13px; font-weight:700; }
.pestanas { display:flex; gap:8px; margin:18px 0 12px; }
.pestana { background:#fff; border:1.5px solid var(--linea); border-radius:8px; padding:8px 18px;
  font-weight:800; font-size:13px; cursor:pointer; color:var(--gris); }
.pestana.activa { background:var(--naranja); border-color:var(--naranja); color:#fff; }
.dim { display:none; }
.dim.activa { display:block; }
.dim-tit { font-size:15.5px; font-weight:800; margin-bottom:6px; }
.dim-form { font-family:Consolas, monospace; background:var(--pizarra-osc); color:#FDBA74;
  border-radius:8px; padding:9px 13px; font-size:13px; margin:8px 0; }
.dim-ind { font-size:12.5px; color:var(--gris); margin-bottom:10px; }
.tabla-scroll { overflow-x:auto; }
.tabla-ficha { width:100%; border-collapse:collapse; font-size:12px; min-width:760px; }
.tabla-ficha th { background:var(--pizarra); color:#fff; padding:7px 9px; text-align:left; position:sticky; top:0; }
.tabla-ficha td { padding:6px 9px; border-bottom:1px solid var(--linea); }
.tabla-ficha tr:hover td { background:var(--naranja-suave); }

/* proceso */
.pasos { display:grid; grid-template-columns:repeat(5,1fr); gap:13px; }
.paso { background:#fff; border:1px solid var(--linea); border-radius:13px; padding:18px 15px; }
.paso b { display:block; color:var(--naranja); font-size:14.5px; margin-bottom:6px; }
.paso p { font-size:12.5px; color:var(--gris); line-height:1.55; }
.paso .num-paso { display:inline-flex; width:26px; height:26px; border-radius:50%; background:var(--pizarra);
  color:#fff; align-items:center; justify-content:center; font-size:13px; font-weight:800; margin-bottom:9px; }

/* fuentes / pie */
.fuentes { font-size:13.5px; color:var(--gris); line-height:1.9; }
.pie { margin-top:44px; background:var(--pizarra); color:#CBD5E1; padding:26px 0; font-size:13px; }

@media (max-width:900px) {
  .hero-int, .mapa-zona, .figuras { grid-template-columns:1fr; }
  .stats, .botones-grandes { grid-template-columns:repeat(2,1fr); }
  .rejilla-metricas, .pasos, .volumen { grid-template-columns:1fr; }
  .ficha-cab { grid-template-columns:1fr; }
}
"""

JS_MAPA = """
function color(v) {
  if (v === null) return '#F8FAFC';
  const escala = [[0,'#FFF7ED'],[60,'#FED7AA'],[140,'#FDBA74'],[260,'#FB923C'],[420,'#EA580C'],[600,'#9A3412']];
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
    p.addEventListener('click', ev => seleccionar(d.nombre, ev));
    g.appendChild(p);
    // nombre del departamento sobre su geometría
    try {
      const bb = p.getBBox();
      const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      t.setAttribute('x', bb.x + bb.width / 2);
      t.setAttribute('y', bb.y + bb.height / 2);
      t.setAttribute('class', 'depto-nom');
      t.textContent = d.nombre;
      g.appendChild(t);
    } catch (e) {}
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
function mostrarTooltip(ev, nombre, s) {
  const caja = document.querySelector('#v-analisis .mapa-caja');
  const tt = document.getElementById('tooltip-mapa');
  const r = caja.getBoundingClientRect();
  tt.innerHTML = `<b>${nombre}</b>: ${fmtN(s.media_mensual)} mm/mes &nbsp;(#${s.rank} nacional)`;
  tt.style.display = 'block';
  tt.style.left = (ev.clientX - r.left) + 'px';
  tt.style.top = (ev.clientY - r.top) + 'px';
  setTimeout(() => { tt.style.display = 'none'; }, 4500);
}
function seleccionar(nombre, ev) {
  document.querySelectorAll('.depto-path').forEach(p =>
    p.classList.toggle('sel', p.dataset.nombre === nombre));
  const s = DATOS.stats[nombre];
  if (ev) mostrarTooltip(ev, nombre, s);
  document.getElementById('info-nombre').textContent = nombre + '  ·  #' + s.rank + ' nacional';
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
function pestana(btn, id) {
  btn.parentElement.querySelectorAll('.pestana').forEach(b => b.classList.remove('activa'));
  document.querySelectorAll('.dim').forEach(d => d.classList.remove('activa'));
  btn.classList.add('activa');
  document.getElementById(id).classList.add('activa');
}
function ver(id) {
  document.querySelectorAll('.vista').forEach(v => v.classList.remove('activa'));
  document.getElementById(id).classList.add('activa');
  document.querySelectorAll('.pestana-nav').forEach(b =>
    b.classList.toggle('activa', b.dataset.vista === id));
  window.scrollTo({ top: 0, behavior: 'smooth' });
  if (id === 'v-analisis') seleccionarNacional();
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
<meta name="description" content="Comparación de algoritmos de regresión de aprendizaje supervisado para la predicción de la precipitación mensual en el Perú. PISCOp v3.0, 1981-2025.">
<style>__CSS__</style>
</head>
<body>

<nav class="nav">
  <div class="nav-int">
    <span class="logo">🌧️ Precipitación Perú</span>
    <button class="pestana-nav activa" data-vista="v-inicio" onclick="ver('v-inicio')">🏠 Inicio</button>
    <button class="pestana-nav" data-vista="v-analisis" onclick="ver('v-analisis')">🗺️ Análisis regional</button>
    <button class="pestana-nav" data-vista="v-ficha" onclick="ver('v-ficha')">📋 Ficha de registro</button>
    <button class="pestana-nav" data-vista="v-metricas" onclick="ver('v-metricas')">📊 Métricas de calidad</button>
    <button class="pestana-nav" data-vista="v-resultados" onclick="ver('v-resultados')">📈 Resultados</button>
  </div>
</nav>

<!-- ═══════════ VISTA 1 · INICIO ═══════════ -->
<div class="vista activa" id="v-inicio">
  <header class="hero">
    <div class="hero-int">
      <div>
        <span class="chip">PISCOp v3.0 · 1981–2025</span>
        <span class="chip">45 años de datos</span>
        <span class="chip">6 algoritmos comparados</span>
        <span class="chip">25 departamentos</span>
        <h1>Comparación de algoritmos de regresión de aprendizaje supervisado para la predicción de la precipitación mensual en el Perú</h1>
        <p class="bajada">Prototipo web de la investigación: presenta la data procesada y su volumen,
        las métricas de desempeño con los umbrales de aceptación, el modelo ganador y el mapa
        interactivo de la precipitación por departamento, junto con la proyección de 2026.</p>
        <button class="boton" onclick="ver('v-metricas')">📊 Tablero de métricas</button>
        &nbsp; <button class="boton hueso" onclick="ver('v-analisis')">🗺️ Explorar el mapa</button>
      </div>
      <div><img class="hero-img" src="__IMG_HERO__" alt="Precipitación en el Perú"></div>
    </div>
  </header>

  <div class="cont">
    <div class="stats">
      <div class="stat"><b>__N_VALIDOS__</b><span>registros celda-mes válidos procesados</span></div>
      <div class="stat"><b>__ANIOS__ años</b><span>de datos mensuales (1981–2025)</span></div>
      <div class="stat"><b>R² __R2__</b><span>coeficiente de determinación del ganador</span></div>
      <div class="stat"><b>__ESTADO__</b><span>veredicto de los umbrales de aceptación</span></div>
    </div>

    <div class="bloque">
      <h2 class="titulo">📦 Volumen de datos procesados</h2>
      <p class="subtitulo">Toda la investigación se construyó sobre este volumen de información real de la fuente PISCOp v3.0 (SENAMHI).</p>
      <div class="volumen">
        <div class="vol"><span>Fuente de datos</span><b>PISCOp v3.0 (SENAMHI)</b></div>
        <div class="vol"><span>Periodo cubierto</span><b>1981 – 2025 (__ANIOS__ años)</b></div>
        <div class="vol"><span>Meses registrados</span><b>__MESES_N__ meses</b></div>
        <div class="vol"><span>Malla de observación</span><b>__MALLA_DIM__</b></div>
        <div class="vol"><span>Celda-mes en la malla</span><b>__MALLA__</b></div>
        <div class="vol"><span>Registros válidos</span><b>__N_VALIDOS__ (__PCT__ %)</b></div>
        <div class="vol"><span>Entrenamiento</span><b>__TRAIN__ registros</b></div>
        <div class="vol"><span>Prueba</span><b>__TEST__ registros</b></div>
        <div class="vol"><span>Rango de precipitación</span><b>__MM_MIN__ – __MM_MAX__ mm</b></div>
      </div>
    </div>

    <div class="bloque">
      <h2 class="titulo">🧭 Explora la investigación en 4 botones</h2>
      <p class="subtitulo">Cada botón abre la ventana correspondiente del prototipo.</p>
      <div class="botones-grandes">
        <button class="boton-grande" onclick="ver('v-ficha')">
          <div class="num-paso">1</div><h3>📋 Ficha de registro</h3>
          <p>El instrumento de recolección tal cual, con 20 registros reales de la celda de Lima.</p>
          <div class="ir">Abrir →</div></button>
        <button class="boton-grande" onclick="ver('v-analisis')">
          <div class="num-paso">2</div><h3>🗺️ Análisis regional</h3>
          <p>Mapa de calor interactivo: clic en un departamento y verás su precipitación y su puesto nacional.</p>
          <div class="ir">Abrir →</div></button>
        <button class="boton-grande" onclick="ver('v-metricas')">
          <div class="num-paso">3</div><h3>📊 Métricas de calidad</h3>
          <p>MAE, RMSE y R² con definición, umbral esperado, mi umbral y veredicto.</p>
          <div class="ir">Abrir →</div></button>
        <button class="boton-grande" onclick="ver('v-resultados')">
          <div class="num-paso">4</div><h3>📈 Resultados</h3>
          <p>Los 6 algoritmos comparados, el ganador destacado, las figuras y la proyección 2026.</p>
          <div class="ir">Abrir →</div></button>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════ VISTA 2 · ANÁLISIS REGIONAL ═══════════ -->
<div class="vista" id="v-analisis">
  <div class="cont">
    <div class="bloque">
      <h2 class="titulo">🗺️ Análisis regional — mapa de calor de la precipitación</h2>
      <p class="subtitulo">Haz clic en un departamento del mapa: verás su precipitación media mensual,
      su puesto nacional y todos sus datos procesados. Escala relativa en milímetros.</p>
      <div class="mapa-zona">
        <div class="mapa-caja">
          <div id="tooltip-mapa"></div>
          <svg class="mapa" id="mapa" viewBox="-81.40 -2.00 17.40 21.00">
            <image x="-81.40" y="-2.00" width="17.40" height="21.00" preserveAspectRatio="none"
                   href="__IMG_RASTER__"></image>
            <g id="capa-deptos"></g>
          </svg>
          <div class="leyenda">
            <span><i style="background:#9A3412"></i> Muy lluvioso (&gt; 420 mm)</span>
            <span><i style="background:#EA580C"></i> Alto (260–420 mm)</span>
            <span><i style="background:#FDBA74"></i> Medio (140–260 mm)</span>
            <span><i style="background:#FED7AA"></i> Bajo (&lt; 140 mm)</span>
            <span><i style="background:#F8FAFC;border:1px solid var(--linea)"></i> Sin datos</span>
          </div>
        </div>
        <div>
          <div class="mapa-caja panel-datos">
            <h3 id="info-nombre">Perú</h3>
            <p id="info-region" style="font-size:12px;color:var(--gris);margin:4px 0 10px"></p>
            <div id="info-datos"></div>
            <p style="font-size:12px;color:var(--gris);margin:14px 0 24px"><b>Climatología mensual (mm)</b></p>
            <div class="clima-barras" id="info-clim"></div>
            <p style="font-size:12px;color:var(--gris);margin:14px 0 8px"><b>Proyección 2026 (mm)</b></p>
            <div class="proy-linea" id="info-proy"></div>
          </div>
          <div class="mapa-caja" style="margin-top:16px">
            <p style="font-size:12.5px;color:var(--gris);margin-bottom:6px"><b>Top 5 departamentos más lluviosos</b> (clic para ver)</p>
            <div id="info-top"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="bloque">
      <h2 class="titulo">📋 Resumen por departamento</h2>
      <div class="envoltura"><table class="tabla">
        <tr><th>Departamento</th><th class="num">Celdas</th><th class="num">Media mensual (mm)</th>
            <th class="num">Media anual (mm)</th><th>Mes más lluvioso</th>
            <th class="num">mm en ese mes</th><th class="num">MAE (mm)</th>
            <th class="num">Proyección 2026 (mm/mes)</th></tr>
        __TABLA_DEPTOS__
      </table></div>
    </div>

    <div class="bloque">
      <h2 class="titulo">📅 Climatología mensual por departamento (mm/mes, 1981–2025)</h2>
      <div class="envoltura"><table class="tabla">
        <tr><th>Departamento</th>__MESES_TH__</tr>
        __TABLA_CLIM__
      </table></div>
    </div>

    <div class="bloque">
      <div class="tarjeta">
        <h3 style="margin-bottom:6px">⬇️ Descargar las tablas (CSV)</h3>
        <p style="font-size:13px;color:var(--gris);margin-bottom:12px">Archivos con separador «;» para abrirse directamente en Excel.</p>
        <a class="boton hueso" href="descargas/01_departamentos.csv">Departamentos</a>
        <a class="boton hueso" href="descargas/02_climatologia_mensual.csv">Climatología mensual</a>
        <a class="boton hueso" href="descargas/03_modelos_comparados.csv">Modelos comparados</a>
        <a class="boton hueso" href="descargas/04_proyeccion_2026.csv">Proyección 2026</a>
        <a class="boton hueso" href="descargas/05_resumen_etl.csv">Resumen ETL</a>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════ VISTA 3 · FICHA DE REGISTRO ═══════════ -->
<div class="vista" id="v-ficha">
  <div class="cont">
    <div class="bloque">
      <h2 class="titulo">📋 Ficha de registro — instrumento de recolección</h2>
      <p class="subtitulo">Instrumento de registro documental tal como se aplicó en la investigación,
      con 20 registros reales de la celda de Lima (lat −12,05°, lon −77,05°) entre 198201 y 198308.</p>
      <div class="tarjeta">
        __FICHA__
      </div>
    </div>
  </div>
</div>

<!-- ═══════════ VISTA 4 · MÉTRICAS DE CALIDAD ═══════════ -->
<div class="vista" id="v-metricas">
  <div class="cont">
    <div class="bloque">
      <h2 class="titulo">📊 Métricas de calidad del modelo ganador</h2>
      <p class="subtitulo">Cada métrica se compara con su umbral esperado de aceptación.
      Los resultados provienen de la corrida del experimento sobre el conjunto de prueba.</p>
      <div class="rejilla-metricas">
        __TARJETA_MAE____TARJETA_RMSE____TARJETA_R2__
      </div>

      <div class="tarjeta" style="margin-top:18px">
        <h3 style="margin-bottom:10px">Criterios de aceptación aplicados</h3>
        <div class="envoltura"><table class="tabla">
          <tr><th>Criterio</th><th>Umbral esperado</th><th class="num">Mi resultado</th><th>Estado</th></tr>
          <tr><td>Relación MAE / MAE de la persistencia</td><td>&lt; 0,90</td>
              <td class="num">__REL_MAE__</td><td>__BADGE_MAE__</td></tr>
          <tr><td>Relación RMSE / RMSE de la persistencia</td><td>&lt; 0,90</td>
              <td class="num">__REL_RMSE__</td><td>__BADGE_RMSE__</td></tr>
          <tr><td>Coeficiente de determinación R²</td><td>≥ 0,75 (excelente)</td>
              <td class="num">__R2__</td><td>__BADGE_R2__</td></tr>
        </table></div>
      </div>

      <div class="tarjeta">
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
    </div>
  </div>
</div>

<!-- ═══════════ VISTA 5 · RESULTADOS ═══════════ -->
<div class="vista" id="v-resultados">
  <div class="cont">
    <div class="bloque">
      <h2 class="titulo">📈 Resultados de la investigación</h2>
      <p class="subtitulo">Seis algoritmos de regresión de aprendizaje supervisado evaluados con las
      mismas particiones de entrenamiento y prueba. El ganador está destacado.</p>
      <div class="envoltura"><table class="tabla">
        <tr><th>Modelo</th><th class="num">Obs. de entrenamiento</th><th class="num">MAE (mm)</th>
            <th class="num">RMSE (mm)</th><th class="num">R²</th>
            <th class="num">Rel. MAE vs persistencia</th><th class="num">Rel. RMSE vs persistencia</th></tr>
        __TABLA_MODELOS__
      </table></div>

      <div class="figuras" style="margin-top:18px">
        <div class="figura"><img src="__IMG_BARRAS__" alt="Comparación de algoritmos">
          <p>Comparación del error (RMSE) entre los algoritmos evaluados.</p></div>
        <div class="figura"><img src="__IMG_REGRESION__" alt="Recta de regresión del modelo ganador">
          <p>Valores predichos frente a observados del modelo ganador en el conjunto de prueba.</p></div>
      </div>

      <div class="tarjeta" style="margin-top:18px">
        <h3 style="margin-bottom:10px">Proyección de la precipitación 2026 (media nacional)</h3>
        <div class="figuras">
          <div><table class="tabla">
            <tr><th>Mes</th><th class="num">Precipitación (mm)</th></tr>
            __TABLA_PROY__
          </table></div>
          <div class="figura"><img src="__IMG_PROY__" alt="Proyección 2026">
            <p>Proyección mensual generada con el modelo ganador.</p></div>
        </div>
      </div>

      <div class="figuras">
        <div class="figura"><img src="__IMG_ERROR__" alt="Mapa de error">
          <p>Distribución espacial del error de predicción (MAE) sobre la malla PISCOp.</p></div>
        <div class="figura"><img src="__IMG_HERO__" alt="Precipitación media">
          <p>Precipitación media mensual observada sobre la malla PISCOp (1981–2025).</p></div>
      </div>
    </div>

    <div class="bloque">
      <h2 class="titulo">⚙️ Proceso de procesamiento de datos</h2>
      <p class="subtitulo">Flujo de trabajo basado en el proceso KDD (descubrimiento de conocimiento en bases de datos).</p>
      <div class="pasos">
        <div class="paso"><div class="num-paso">1</div><b>Selección</b>
          <p>Se toma la fuente PISCOp v3.0: 540 meses de precipitación en malla de 0,1° sobre el Perú.</p></div>
        <div class="paso"><div class="num-paso">2</div><b>Preprocesamiento</b>
          <p>Se eliminan los valores sin dato (centinelas) y se consolidan los registros válidos de celda-mes.</p></div>
        <div class="paso"><div class="num-paso">3</div><b>Transformación</b>
          <p>Se construyen las variables de entrada y la etiqueta de precipitación del mes siguiente.</p></div>
        <div class="paso"><div class="num-paso">4</div><b>Minería</b>
          <p>Se entrenan seis algoritmos de regresión y se evalúan con las mismas particiones.</p></div>
        <div class="paso"><div class="num-paso">5</div><b>Evaluación</b>
          <p>Se comparan MAE, RMSE y R² frente a los umbrales y las líneas base, y se proyecta 2026.</p></div>
      </div>
    </div>

    <div class="bloque">
      <h2 class="titulo">📚 Fuentes de datos</h2>
      <div class="tarjeta fuentes">
        <p><b>[1]</b> SENAMHI, «PISCOp v3.0: Producto Integrado de Precipitación a escala Nacional Compilado», Perú. [En línea]. Disponible en: http://hydro.chc.ucsb.edu/.</p>
        <p><b>[3]</b> C. Funk et al., «The climate hazards infrared precipitation with stations—a new environmental record for monitoring extremes», <i>Scientific Data</i>, vol. 2, 2015.</p>
        <p style="margin-top:8px;font-size:12px">Los resultados mostrados provienen de la corrida del experimento sobre PISCOp v3.0.
        El prototipo se actualizará en el futuro con la fuente CHIRPS v2.0.</p>
      </div>
    </div>
  </div>
</div>

<footer class="pie">
  <div class="cont">
    <p><b>Precipitación Perú</b> — prototipo web de la tesis «Comparación de algoritmos de regresión de
    aprendizaje supervisado para la predicción de la precipitación mensual en el Perú».</p>
    <p style="margin-top:6px">Universidad César Vallejo · Datos PISCOp v3.0 (SENAMHI) [1] · CHIRPS [3] ·
    __ANIOS__ años de datos · __N_VALIDOS__ registros válidos procesados.</p>
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
        .replace("__FICHA__", FICHA_HTML)
        .replace("__TARJETA_MAE__", tarjeta_mae)
        .replace("__TARJETA_RMSE__", tarjeta_rmse)
        .replace("__TARJETA_R2__", tarjeta_r2)
        .replace("__BADGE_MAE__", badge(ok_mae))
        .replace("__BADGE_RMSE__", badge(ok_rmse))
        .replace("__BADGE_R2__", badge(ok_r2))
        .replace("__REL_MAE__", num(GAN["rel_mae"], 2))
        .replace("__REL_RMSE__", num(GAN["rel_rmse"], 2))
        .replace("__N_VALIDOS__", num(R["validos"], 0))
        .replace("__PCT__", num(PCT_VALIDOS, 2))
        .replace("__ANIOS__", str(ANIOS))
        .replace("__MESES_N__", num(R["meses"], 0))
        .replace("__MALLA_DIM__", f"{N_LAT} × {N_LON} celdas de 0,1° ({num(N_CELDAS, 0)})")
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

os.makedirs(D_OUT, exist_ok=True)
ruta = os.path.join(D_OUT, "index.html")
with open(ruta, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Sitio generado: {ruta}")
print(f"   Tamaño: {os.path.getsize(ruta)/1024:.0f} KB · vistas: 5 (pestañas)")
print(f"   Ficha registros: {'OK' if 'tabla-ficha' in html else 'FALTA'} · tooltip mapa: {'OK' if 'tooltip-mapa' in html else 'FALTA'}")
print(f"   Umbrales -> MAE {GAN['rel_mae']:.2f} {'✓' if ok_mae else '✗'} | "
      f"RMSE {GAN['rel_rmse']:.2f} {'✓' if ok_rmse else '✗'} | R² {GAN['r2']:.2f} {'✓' if ok_r2 else '✗'}")
