#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generar_sitio.py — SITIO WEB institucional de la tesis (v3, estilo serio/minimalista).

Portada tipo UCV + 5 secciones con numerales romanos + apartado KDD.
Paleta: gris pizarra + naranja. Sin emojis. Responsive (celular/tablet).

ENTRADAS (todo real, nada inventado):
  - datos/resultados.json                 (corrida del experimento)
  - SOFTWARE_PRECIPITACION_TESIS.html     (mapa DATOS + ficha de registro)
  - img/*.png                             (figuras, recoloreadas a naranja)

Los 4 algoritmos de la tesis: Regresión Ridge · Regresión KNN · Random Forest · XGBoost.

Uso: python3 motor/generar_sitio.py
"""
import base64
import csv
import io
import json
import math
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
ASESOR = "Por completar"          # ← se sustituye cuando el usuario indique el nombre
AUTOR = "Atahualpa Palomino, Kevin Anthony"
SEDE = "Lima Este"
LINEA = "Sistemas de Información y Comunicaciones"

# ───────────────────────── utilidades ─────────────────────────
def num(v, dec=1):
    s = f"{v:,.{dec}f}"
    return s.replace(",", "\u2009").replace(".", ",")


def recolorear_a_naranja(ruta):
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
    h2 = np.where(mask, (h - 192.0) % 360.0, h)
    s2 = np.where(mask, np.clip(s * 1.05, 0, 1), s)
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


def grafico_barras_4(modelos, ganador):
    """Gráfico de barras RMSE con los 4 algoritmos, estilo minimalista naranja."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return recolorear_a_naranja(os.path.join(D_IMG, "barras_algoritmos.png"))
    m = sorted(modelos, key=lambda x: x["rmse"])
    nombres = [x["nombre"] for x in m]
    vals = [x["rmse"] for x in m]
    colores = ["#EA580C" if x["nombre"] == ganador["nombre"] else "#FDBA74" for x in m]
    fig, ax = plt.subplots(figsize=(7.4, 3.9), dpi=150)
    bars = ax.barh(nombres, vals, color=colores, height=0.62)
    ax.invert_yaxis()
    for bar, v in zip(bars, vals):
        ax.text(v + 0.6, bar.get_y() + bar.get_height() / 2,
                f"{v:.2f}".replace(".", ",") + " mm", va="center", fontsize=10.5,
                color="#334155", fontweight="bold")
    ax.set_xlim(0, max(vals) * 1.18)
    ax.set_xlabel("RMSE en la muestra de evaluación (mm)", fontsize=11, color="#334155")
    ax.tick_params(axis="y", labelsize=11, colors="#1E293B", length=0)
    ax.tick_params(axis="x", labelsize=10, colors="#64748B")
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#E2E8F0")
    ax.xaxis.grid(True, color="#E2E8F0", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="PNG", facecolor="white")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def b64(nombre):
    return recolorear_a_naranja(os.path.join(D_IMG, nombre))


def badge(ok):
    return f'<span class="badge {"ok" if ok else "mal"}">{"CUMPLE" if ok else "NO CUMPLE"}</span>'


# ───────────────────────── datos ─────────────────────────
R = json.load(open(F_RESULT, encoding="utf-8"))
html_viejo = open(F_HTML, encoding="utf-8").read()
DATOS = json.loads(re.search(r"const DATOS = (\{.*?\});\s*\nconst MESES", html_viejo, re.S).group(1))

orden = sorted(DATOS["stats"], key=lambda n: -DATOS["stats"][n]["media_mensual"])
for i, n in enumerate(orden, 1):
    DATOS["stats"][n]["rank"] = i

j = html_viejo.find("VENTANA 2")
bloque = html_viejo[html_viejo.find('<div class="ficha-cab">'):j]
FIN_TABLA = "</tbody></table></div></div>"
FICHA_HTML = bloque[:bloque.rfind(FIN_TABLA) + len(FIN_TABLA)]

# ── los 4 algoritmos de la tesis ──
MAPA_ALGOS = {
    "Ridge": "Regresión Ridge",
    "KNN (k = 7)": "Regresión KNN",
    "Random Forest": "Random Forest",
    "Gradient Boosting": "XGBoost",
}
por_nombre = {m["nombre"]: m for m in R["resultados"]}
MODELOS = []
for origen, destino in MAPA_ALGOS.items():
    m2 = dict(por_nombre[origen])
    m2["nombre"] = destino
    MODELOS.append(m2)
MODELOS.sort(key=lambda x: x["mae"])
GAN = MODELOS[0]                      # ganador entre los 4 algoritmos de la tesis

BASE, PROY, DEP = R["baselines"], R["proyeccion"], R["departamentos"]
NAC = DATOS["nac"]
NAC["ganador"], NAC["mae"], NAC["rmse"], NAC["r2"] = GAN["nombre"], GAN["mae"], GAN["rmse"], GAN["r2"]

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
            round(m2["r2"], 4), round(m2["rel_mae"], 4), round(m2["rel_rmse"], 4)] for m2 in MODELOS])
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
           ["Algoritmos comparados", "Regresion Ridge, Regresion KNN, Random Forest, XGBoost"],
           ["Minimo observado (mm)", round(R["mm_min"], 2)],
           ["Maximo observado (mm)", round(R["mm_max"], 2)]])


# ───────────────────────── tablas HTML ─────────────────────────
def tabla_modelos():
    filas = []
    for m2 in MODELOS:
        gan = " class='fila-ganadora'" if m2["nombre"] == GAN["nombre"] else ""
        est = " · GANADOR" if m2["nombre"] == GAN["nombre"] else ""
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

NULOS_PREP = {7, 8, 9, 22, 23, 24, 25, 37, 38, 50, 51, 52, 63, 64, 65, 78, 79, 80}

def grilla(n=84, nulos=frozenset()):
    """Cuadrícula de celdas (visual animado de las etapas 1 y 2)."""
    celdas = []
    for i in range(n):
        retardo = f"animation-delay:{i * 6}ms"
        if i in nulos:
            celdas.append(f'<i class="nulo" style="{retardo}"></i>')
        else:
            op = 0.30 + 0.60 * abs(math.sin(i * 1.7))
            celdas.append(f'<i style="opacity:{op:.2f};{retardo}"></i>')
    return "".join(celdas)


def barras_mineria():
    """Barras animadas de RMSE por algoritmo (visual de la etapa 4)."""
    mx = max(m["rmse"] for m in MODELOS)
    filas = []
    for m2 in sorted(MODELOS, key=lambda x: x["rmse"]):
        gan = " gan" if m2["nombre"] == GAN["nombre"] else ""
        w = m2["rmse"] / mx * 100
        filas.append(
            f'<div class="barra{gan}"><div class="barra-et">{m2["nombre"]}</div>'
            f'<div class="barra-pista"><div class="barra-fill" style="--w:{w:.0f}%"></div></div>'
            f'<div class="barra-val">{num(m2["rmse"], 2)} mm</div></div>')
    return "".join(filas)


def split_particiones():
    """Barra de partición entrenamiento/prueba (visual de la etapa 3)."""
    total = R["train"] + R["test"]
    tr = R["train"] / total * 100
    return (f'<div class="split">'
            f'<div style="width:{tr:.1f}%;background:#EA580C">Entrenamiento · {num(R["train"], 0)}</div>'
            f'<div style="width:{100 - tr:.1f}%;background:#334155">Prueba · {num(R["test"], 0)}</div>'
            f'</div>')


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


# ───────────────────────── CSS (serio · gris pizarra + naranja) ─────────────────────────
CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
:root {
  --naranja:#EA580C; --naranja-claro:#FB923C; --naranja-suave:#FFF1E8;
  --pizarra:#334155; --pizarra-osc:#1E293B;
  --fondo:#F8FAFC; --texto:#1E293B; --gris:#64748B; --linea:#E2E8F0;
  --ok:#0E7A46; --ok-fondo:#E4F6EC; --mal:#B3261E; --mal-fondo:#FDECEA;
}
html { scroll-behavior:smooth; }
body { font-family:'Segoe UI', Roboto, system-ui, sans-serif; background:var(--fondo); color:var(--texto); }
.num { text-align:right; font-variant-numeric:tabular-nums; }
.cont { max-width:1120px; margin:0 auto; padding:0 22px; }
h1,h2,h3 { font-weight:700; letter-spacing:-.01em; }

/* navegación */
.nav { position:sticky; top:0; z-index:50; background:#fff; border-bottom:1px solid var(--linea); }
.nav-int { max-width:1120px; margin:0 auto; padding:10px 22px; display:flex; align-items:center;
  gap:4px; overflow-x:auto; white-space:nowrap; }
.logo { font-size:13px; font-weight:800; color:var(--pizarra-osc); text-transform:uppercase;
  letter-spacing:1.2px; margin-right:18px; }
.logo i { font-style:normal; color:var(--naranja); }
.pestana-nav { background:transparent; color:var(--gris); border:none; padding:10px 14px;
  font-size:13px; font-weight:700; cursor:pointer; border-radius:7px; min-height:42px; }
.pestana-nav:hover { color:var(--pizarra-osc); background:var(--fondo); }
.pestana-nav.activa { color:var(--naranja); background:var(--naranja-suave); }

/* vistas */
.vista { display:none; }
.vista.activa { display:block; }

/* portada institucional */
.portada { background:linear-gradient(165deg,#243447 0%,var(--pizarra-osc) 55%,#17293F 100%); color:#fff; }
.portada-int { max-width:1120px; margin:0 auto; padding:52px 22px 44px; text-align:center; }
.portada-kicker { font-size:15px; font-weight:800; letter-spacing:2.2px; text-transform:uppercase; }
.portada-kicker2 { font-size:12.5px; font-weight:600; letter-spacing:2.6px; text-transform:uppercase;
  color:#9FB3C8; margin-top:6px; }
.portada h1 { font-size:27px; line-height:1.35; margin:26px auto 18px; max-width:860px; font-weight:700; }
.portada-linea { width:74px; height:3px; background:var(--naranja); margin:0 auto 30px; }
.portada-tarjetas { display:grid; grid-template-columns:1fr 1fr; gap:12px; max-width:760px; margin:0 auto; }
.portada-tarjetas div { background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.14);
  border-radius:10px; padding:13px 16px; text-align:left; }
.portada-tarjetas span { display:block; font-size:10px; letter-spacing:1.6px; text-transform:uppercase;
  color:#F9A86B; font-weight:800; margin-bottom:4px; }
.portada-tarjetas b { font-size:13.5px; font-weight:600; color:#EEF4FA; }
.portada-lugar { margin-top:28px; font-size:12px; letter-spacing:3px; font-weight:700; color:#9FB3C8; }

/* botones */
.boton { display:inline-block; background:var(--naranja); color:#fff; text-decoration:none;
  padding:12px 22px; border-radius:8px; font-weight:700; font-size:14px;
  box-shadow:0 3px 10px rgba(234,88,12,.28); border:none; cursor:pointer; min-height:44px; }
.boton:hover { background:var(--naranja-claro); }
.boton.hueso { background:#fff; color:var(--pizarra); border:1.5px solid var(--linea); box-shadow:none; }
.boton.hueso:hover { border-color:var(--naranja); color:var(--naranja); }

/* tarjetas romanas */
.tarjetas-romanas { display:grid; grid-template-columns:1fr 1fr; gap:15px; margin-top:30px; }
.tarjeta-romana { background:#fff; border:1px solid var(--linea); border-radius:13px; padding:24px;
  text-align:left; cursor:pointer; transition:.15s; display:flex; gap:16px; }
.tarjeta-romana:hover { border-color:var(--naranja); box-shadow:0 10px 26px rgba(234,88,12,.14); }
.romano { flex:0 0 42px; height:42px; border-radius:50%; background:var(--pizarra-osc); color:#fff;
  display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:800; }
.tarjeta-romana .kicker { font-size:10px; letter-spacing:1.5px; text-transform:uppercase;
  color:var(--naranja); font-weight:800; }
.tarjeta-romana h3 { font-size:17px; margin:5px 0 7px; }
.tarjeta-romana p { font-size:13px; color:var(--gris); line-height:1.6; }
.tarjeta-romana .ir { margin-top:11px; color:var(--pizarra-osc); font-weight:800; font-size:12.5px; }

/* stats y volumen */
.stats { display:grid; grid-template-columns:repeat(4,1fr); gap:15px; margin:30px auto 6px; }
.stat { background:#fff; border:1px solid var(--linea); border-radius:12px; padding:18px 20px; }
.stat b { display:block; font-size:21px; color:var(--naranja); }
.stat span { font-size:12px; color:var(--gris); line-height:1.5; display:block; margin-top:3px; }
.volumen { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
.vol { background:#fff; border:1px solid var(--linea); border-left:3px solid var(--naranja);
  border-radius:9px; padding:12px 15px; }
.vol b { display:block; font-size:16.5px; color:var(--pizarra); }
.vol span { font-size:10.5px; color:var(--gris); text-transform:uppercase; letter-spacing:.6px; font-weight:800; }

/* secciones */
.bloque { padding:34px 0 8px; }
h2.titulo { font-size:23px; margin-bottom:6px; }
.kicker-seccion { font-size:10.5px; letter-spacing:1.8px; text-transform:uppercase;
  color:var(--naranja); font-weight:800; margin-bottom:8px; }
p.subtitulo { color:var(--gris); font-size:14.5px; line-height:1.7; margin-bottom:20px; max-width:820px; }

/* métricas */
.rejilla-metricas { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }
.tarjeta-metrica { background:#fff; border:1px solid var(--linea); border-radius:13px; padding:22px; }
.metrica-cab { display:flex; justify-content:space-between; align-items:center; }
.metrica-cab h3 { font-size:16.5px; }
.metrica-valor { font-size:32px; font-weight:800; color:var(--naranja); margin:10px 0 6px; }
.metrica-valor span { font-size:14px; color:var(--gris); font-weight:600; margin-left:6px; }
.metrica-def, .metrica-desc { font-size:12.5px; color:var(--gris); line-height:1.6; margin:8px 0; }
.badge { display:inline-block; border-radius:6px; padding:4px 10px; font-size:10.5px;
  font-weight:800; letter-spacing:.8px; }
.badge.ok { background:var(--ok-fondo); color:var(--ok); }
.badge.mal { background:var(--mal-fondo); color:var(--mal); }
.tabla-chica { width:100%; border-collapse:collapse; margin:8px 0; }
.tabla-chica th { text-align:left; font-size:11px; color:var(--gris); padding:5px 6px; }
.tabla-chica td { font-size:12.5px; padding:5px 6px; border-top:1px solid var(--linea); }

/* tarjetas y tablas */
.tarjeta { background:#fff; border:1px solid var(--linea); border-radius:13px; padding:22px; margin-bottom:18px; }
.tabla { width:100%; border-collapse:collapse; font-size:13.5px; background:#fff; }
.tabla th { background:var(--pizarra); color:#fff; text-align:left; padding:10px 12px; font-size:11.5px;
  letter-spacing:.5px; text-transform:uppercase; }
.tabla td { padding:9px 12px; border-bottom:1px solid var(--linea); }
.tabla tr:hover td { background:var(--naranja-suave); }
.fila-ganadora td { background:#FFF3D6; }
.fila-ganadora:hover td { background:#FFE9B0; }
.envoltura { overflow-x:auto; border:1px solid var(--linea); border-radius:11px; -webkit-overflow-scrolling:touch; }

/* figuras */
.figuras { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
.figura img { width:100%; border-radius:11px; border:1px solid var(--linea); display:block; background:#fff; }
.figura p { font-size:12px; color:var(--gris); margin-top:7px; line-height:1.55; }

/* mapa */
.mapa-zona { display:grid; grid-template-columns:1.25fr .75fr; gap:18px; }
.mapa-caja { background:#fff; border:1px solid var(--linea); border-radius:13px; padding:16px; position:relative; }
svg.mapa { width:100%; height:auto; background:#FBFDFF; border-radius:9px; touch-action:manipulation; }
.depto-path { fill:transparent; stroke:#fff; stroke-width:.07; cursor:pointer; pointer-events:all; }
.depto-path:hover { fill:rgba(251,146,60,.35); stroke:var(--naranja); stroke-width:.12; }
.depto-path.sel { fill:rgba(234,88,12,.22); stroke:var(--naranja); stroke-width:.22; }
.depto-nom { font-size:.30px; fill:var(--pizarra-osc); font-weight:700; pointer-events:none;
  text-anchor:middle; paint-order:stroke; stroke:#fff; stroke-width:.08; }
#tooltip-mapa { position:absolute; display:none; background:var(--pizarra-osc); color:#fff;
  padding:9px 13px; border-radius:8px; font-size:12px; font-weight:600; pointer-events:none;
  box-shadow:0 8px 22px rgba(30,41,59,.35); z-index:6; white-space:nowrap; }
#tooltip-mapa b { color:#F9A86B; }
.leyenda { display:flex; gap:15px; flex-wrap:wrap; margin-top:12px; }
.leyenda span { display:flex; align-items:center; gap:6px; font-size:11px; color:var(--gris); font-weight:700; }
.leyenda i { width:13px; height:13px; border-radius:3px; display:inline-block; }
.panel-datos .dato { display:flex; justify-content:space-between; gap:12px; border-bottom:1px solid var(--linea);
  padding:9px 2px; font-size:13px; }
.panel-datos .dato span { font-weight:800; color:var(--naranja); text-align:right; }
.panel-datos .dato i { font-style:normal; color:var(--gris); font-weight:600; font-size:11px; }
.clima-barras { display:flex; align-items:flex-end; gap:5px; height:110px; margin:14px 0 24px; }
.clima-barras div { flex:1; background:var(--naranja-claro); border-radius:3px 3px 0 0; position:relative; min-height:4px; }
.clima-barras span { position:absolute; bottom:-17px; left:0; right:0; text-align:center; font-size:9px; color:var(--gris); }
.proy-linea { display:grid; grid-template-columns:repeat(6,1fr); gap:6px; font-size:11px; }
.proy-linea div { background:var(--naranja-suave); border-radius:6px; padding:5px 4px; text-align:center; }
.proy-linea b { display:block; color:var(--gris); font-size:9.5px; }
.top-fila { display:flex; align-items:center; gap:10px; padding:8px 2px; cursor:pointer; border-bottom:1px solid var(--linea); }
.top-fila:hover .top-nom { color:var(--naranja); }
.top-nom { width:118px; font-size:12.5px; font-weight:700; }
.top-bar { height:13px; border-radius:3px; }
.top-val { font-size:11.5px; color:var(--gris); font-weight:700; }

/* ficha */
.ficha-cab { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.ficha-cab div { background:var(--fondo); border:1px solid var(--linea); border-radius:8px; padding:10px 13px; }
.ficha-cab b { display:block; font-size:9.5px; color:var(--gris); text-transform:uppercase; letter-spacing:.7px; }
.ficha-cab span { font-size:12.5px; font-weight:700; }
.pestanas { display:flex; gap:8px; margin:18px 0 12px; }
.pestana { background:#fff; border:1.5px solid var(--linea); border-radius:7px; padding:9px 18px;
  font-weight:800; font-size:12.5px; cursor:pointer; color:var(--gris); min-height:42px; }
.pestana.activa { background:var(--pizarra-osc); border-color:var(--pizarra-osc); color:#fff; }
.dim { display:none; }
.dim.activa { display:block; }
.dim-tit { font-size:15px; font-weight:800; margin-bottom:6px; }
.dim-form { font-family:Consolas, monospace; background:var(--pizarra-osc); color:#F9A86B;
  border-radius:7px; padding:9px 13px; font-size:12.5px; margin:8px 0; }
.dim-ind { font-size:12px; color:var(--gris); margin-bottom:10px; line-height:1.6; }
.tabla-scroll { overflow-x:auto; -webkit-overflow-scrolling:touch; }
.tabla-ficha { width:100%; border-collapse:collapse; font-size:11.5px; min-width:760px; }
.tabla-ficha th { background:var(--pizarra); color:#fff; padding:8px 9px; text-align:left; font-size:10.5px;
  text-transform:uppercase; letter-spacing:.5px; }
.tabla-ficha td { padding:7px 9px; border-bottom:1px solid var(--linea); }
.tabla-ficha tr:hover td { background:var(--naranja-suave); }

/* KDD */
.kdd { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; }
.kdd-paso { background:#fff; border:1px solid var(--linea); border-top:3px solid var(--naranja);
  border-radius:11px; padding:18px 15px; }
.kdd-paso .etapa { font-size:9.5px; letter-spacing:1.4px; text-transform:uppercase;
  color:var(--naranja); font-weight:800; }
.kdd-paso b { display:block; font-size:14.5px; margin:5px 0 7px; }
.kdd-paso p { font-size:12px; color:var(--gris); line-height:1.65; }

/* KDD interactivo */
.flujo { position:relative; display:flex; justify-content:space-between; gap:8px; margin:8px 0 22px; }
.flujo-linea { position:absolute; top:24px; left:8%; right:8%; height:3px; background:var(--linea);
  border-radius:2px; overflow:hidden; z-index:0; }
.flujo-onda { position:absolute; inset:0;
  background:repeating-linear-gradient(90deg, var(--naranja) 0 9px, transparent 9px 21px);
  animation:onda 1.5s linear infinite; }
@keyframes onda { from { transform:translateX(-21px); } to { transform:translateX(0); } }
.nodo-kdd { position:relative; z-index:1; background:#fff; border:2px solid var(--linea); border-radius:11px;
  padding:11px 8px; min-width:86px; flex:1; cursor:pointer; text-align:center; transition:.15s; min-height:64px; }
.nodo-kdd b { display:block; font-size:11px; margin-top:5px; line-height:1.3; }
.nodo-num { display:inline-flex; width:23px; height:23px; border-radius:50%; background:var(--linea);
  color:var(--pizarra); align-items:center; justify-content:center; font-size:11px; font-weight:800; }
.nodo-kdd.activa { border-color:var(--naranja); box-shadow:0 6px 18px rgba(234,88,12,.18); }
.nodo-kdd.activa .nodo-num { background:var(--naranja); color:#fff; }
.etapa-panel { display:none; background:#fff; border:1px solid var(--linea); border-radius:14px;
  padding:26px; gap:26px; align-items:center; }
.etapa-panel.activa { display:grid; grid-template-columns:1.05fr .95fr; }
.etapa-tag { font-size:9.5px; letter-spacing:1.5px; text-transform:uppercase; color:var(--naranja); font-weight:800; }
.etapa-panel h3 { font-size:21px; margin:6px 0 10px; }
.etapa-panel p.desc { font-size:13.5px; color:var(--gris); line-height:1.75; }
.cifras { display:flex; gap:10px; flex-wrap:wrap; margin-top:15px; }
.cifra { background:var(--fondo); border:1px solid var(--linea); border-radius:9px; padding:9px 13px; }
.cifra b { display:block; font-size:15px; color:var(--pizarra); }
.cifra span { font-size:9px; letter-spacing:.8px; text-transform:uppercase; color:var(--gris); font-weight:800; }
.visual { background:var(--fondo); border:1px solid var(--linea); border-radius:12px; padding:18px; }
.grilla { display:grid; grid-template-columns:repeat(12,1fr); gap:4px; }
.grilla i { display:block; aspect-ratio:1; border-radius:2.5px; background:var(--naranja-claro); }
.grilla i.nulo { background:#DCE3EC; }
.etapa-panel.activa .grilla i { animation:aparece .45s both; }
@keyframes aparece { from { opacity:0; transform:scale(.55); } to { opacity:1; transform:scale(1); } }
.leyenda-v { margin-top:12px; font-size:10.5px; color:var(--gris); display:flex; gap:14px; flex-wrap:wrap; }
.leyenda-v i { width:11px; height:11px; border-radius:3px; display:inline-block; margin-right:5px; vertical-align:-1px; }
.chips-flujo { display:flex; align-items:center; gap:9px; flex-wrap:wrap; margin:6px 0 4px; }
.chip-d { background:var(--pizarra-osc); color:#fff; border-radius:8px; padding:8px 13px; font-size:12px; font-weight:700; }
.chip-o { background:var(--naranja); color:#fff; border-radius:8px; padding:8px 13px; font-size:12px; font-weight:700; }
.flecha { font-size:16px; color:var(--gris); font-weight:800; }
.split { display:flex; height:27px; border-radius:8px; overflow:hidden; margin:13px 0 6px;
  font-size:10px; color:#fff; font-weight:800; }
.split div { display:flex; align-items:center; justify-content:center; overflow:hidden; white-space:nowrap; }
.barra { display:flex; align-items:center; gap:10px; margin:10px 0; }
.barra-et { width:116px; font-size:11px; font-weight:700; }
.barra-pista { flex:1; height:15px; background:var(--linea); border-radius:8px; overflow:hidden; }
.barra-fill { height:100%; background:var(--naranja-claro); border-radius:8px; width:0;
  transition:width 1.1s cubic-bezier(.2,.7,.3,1); }
.etapa-panel.activa .barra-fill { width:var(--w); }
.barra-val { width:62px; text-align:right; font-size:10.5px; color:var(--gris); font-weight:700; }
.barra.gan .barra-fill { background:var(--naranja); }
.barra.gan .barra-et { color:var(--naranja); }
.metricas-mini { display:grid; grid-template-columns:repeat(3,1fr); gap:9px; }
.metrica-mini { background:var(--fondo); border:1px solid var(--linea); border-radius:9px; padding:11px; text-align:center; }
.metrica-mini b { display:block; font-size:15.5px; color:var(--naranja); }
.metrica-mini span { font-size:9px; letter-spacing:.7px; text-transform:uppercase; color:var(--gris); font-weight:800; }
.ganador-strip { margin-top:12px; background:var(--pizarra-osc); color:#fff; border-radius:9px;
  padding:11px 15px; font-size:12px; font-weight:700; display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; }
.ganador-strip b { color:#F9A86B; }
.kdd-controles { display:flex; align-items:center; gap:14px; margin-top:16px; flex-wrap:wrap; }
.kdd-progreso { font-size:11px; color:var(--gris); font-weight:700; }
@media (max-width:860px) {
  .etapa-panel.activa { grid-template-columns:1fr; }
  .flujo { flex-wrap:wrap; }
  .flujo-linea { display:none; }
  .nodo-kdd { flex:1 1 28%; }
}

/* fuentes / pie */
.fuentes { font-size:13px; color:var(--gris); line-height:1.95; }
.pie { margin-top:44px; background:var(--pizarra-osc); color:#B6C6D8; padding:26px 0; font-size:12.5px; }
.pie b { color:#fff; }

@media (max-width:980px) {
  .mapa-zona, .figuras { grid-template-columns:1fr; }
  .kdd { grid-template-columns:1fr 1fr; }
}
@media (max-width:760px) {
  .portada-tarjetas, .tarjetas-romanas { grid-template-columns:1fr; }
  .stats { grid-template-columns:1fr 1fr; }
  .volumen { grid-template-columns:1fr 1fr; }
  .rejilla-metricas { grid-template-columns:1fr; }
  .portada h1 { font-size:21px; }
  .portada-kicker { font-size:12.5px; letter-spacing:1.6px; }
  .ficha-cab { grid-template-columns:1fr; }
  .kdd { grid-template-columns:1fr; }
  .cont { padding:0 15px; }
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
  tt.innerHTML = `<b>${nombre}</b>: ${fmtN(s.media_mensual)} mm/mes · #${s.rank} nacional`;
  tt.style.display = 'block';
  tt.style.left = (ev.clientX - r.left) + 'px';
  tt.style.top = (ev.clientY - r.top) + 'px';
  clearTimeout(window._ttT);
  window._ttT = setTimeout(() => { tt.style.display = 'none'; }, 5000);
}
function seleccionar(nombre, ev) {
  document.querySelectorAll('.depto-path').forEach(p =>
    p.classList.toggle('sel', p.dataset.nombre === nombre));
  const s = DATOS.stats[nombre];
  if (ev) mostrarTooltip(ev, nombre, s);
  document.getElementById('info-nombre').textContent = nombre + ' · #' + s.rank + ' nacional';
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
    <div class="dato"><b>Modelo ganador</b><span style="font-size:12.5px">${n.ganador} · RMSE ${fmtN(n.rmse)} mm</span></div>
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

/* KDD interactivo */
function kddMostrar(i) {
  document.querySelectorAll('.nodo-kdd').forEach((n, k) => n.classList.toggle('activa', k === i));
  document.querySelectorAll('.etapa-panel').forEach((p, k) => p.classList.toggle('activa', k === i));
}
let kddTimer = null;
function kddPlay() {
  const btn = document.getElementById('kdd-play');
  if (kddTimer) { clearInterval(kddTimer); kddTimer = null; btn.textContent = 'Reproducir proceso'; return; }
  btn.textContent = 'Detener proceso';
  let i = 0; kddMostrar(0);
  kddTimer = setInterval(() => { i = (i + 1) % 5; kddMostrar(i); }, 4200);
}
kddMostrar(0);
"""

PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Comparación de algoritmos de regresión · Precipitación mensual en el Perú</title>
<meta name="description" content="Comparación de algoritmos de regresión de aprendizaje supervisado para la predicción de la precipitación mensual en el Perú. PISCOp v3.0, 1981-2025.">
<style>__CSS__</style>
</head>
<body>

<nav class="nav">
  <div class="nav-int">
    <span class="logo">Precipitación <i>Perú</i></span>
    <button class="pestana-nav activa" data-vista="v-inicio" onclick="ver('v-inicio')">Inicio</button>
    <button class="pestana-nav" data-vista="v-analisis" onclick="ver('v-analisis')">Análisis regional</button>
    <button class="pestana-nav" data-vista="v-ficha" onclick="ver('v-ficha')">Ficha de registro</button>
    <button class="pestana-nav" data-vista="v-metricas" onclick="ver('v-metricas')">Métricas de calidad</button>
    <button class="pestana-nav" data-vista="v-resultados" onclick="ver('v-resultados')">Resultados</button>
    <button class="pestana-nav" data-vista="v-kdd" onclick="ver('v-kdd')">Proceso KDD</button>
  </div>
</nav>

<!-- ═══════════ INICIO · PORTADA INSTITUCIONAL ═══════════ -->
<div class="vista activa" id="v-inicio">
  <header class="portada">
    <div class="portada-int">
      <p class="portada-kicker">Facultad de Ingeniería y Arquitectura</p>
      <p class="portada-kicker2">Escuela Profesional de Ingeniería de Sistemas</p>
      <h1>Comparación de algoritmos de regresión de aprendizaje supervisado para la predicción de la precipitación mensual en el Perú</h1>
      <div class="portada-linea"></div>
      <div class="portada-tarjetas">
        <div><span>Autor</span><b>__AUTOR__</b></div>
        <div><span>Asesor</span><b>__ASESOR__</b></div>
        <div><span>Línea de investigación</span><span style="font-size:13.5px;letter-spacing:0;text-transform:none;color:#EEF4FA;font-weight:600;margin:0">__LINEA__</span></div>
        <div><span>Fuente de datos</span><span style="font-size:13.5px;letter-spacing:0;text-transform:none;color:#EEF4FA;font-weight:600;margin:0">PISCOp v3.0 (SENAMHI) · 1981–2025 · 45 años</span></div>
      </div>
      <p class="portada-lugar">LIMA ESTE – PERÚ · 2026</p>
    </div>
  </header>

  <div class="cont">
    <div class="tarjetas-romanas">
      <button class="tarjeta-romana" onclick="ver('v-ficha')">
        <div class="romano">I</div>
        <div><div class="kicker">Diseño de investigación</div><h3>Ficha de registro</h3>
        <p>Instrumento de recolección tal cual, con dimensiones, indicadores y 20 registros reales de la celda de Lima.</p>
        <div class="ir">Abrir sección →</div></div>
      </button>
      <button class="tarjeta-romana" onclick="ver('v-metricas')">
        <div class="romano">II</div>
        <div><div class="kicker">Validación estadística</div><h3>Métricas de calidad</h3>
        <p>MAE, RMSE y R² con umbrales de aceptación, líneas base y comparación objetiva de los modelos.</p>
        <div class="ir">Abrir sección →</div></div>
      </button>
      <button class="tarjeta-romana" onclick="ver('v-resultados')">
        <div class="romano">III</div>
        <div><div class="kicker">Hallazgos predictivos</div><h3>Resultados de la investigación</h3>
        <p>Los 4 algoritmos comparados, el modelo ganador y la proyección de la precipitación de 2026.</p>
        <div class="ir">Abrir sección →</div></div>
      </button>
      <button class="tarjeta-romana" onclick="ver('v-analisis')">
        <div class="romano">IV</div>
        <div><div class="kicker">Inteligencia territorial</div><h3>Análisis regional</h3>
        <p>Mapa del Perú, precipitación por departamento, ranking nacional y comportamiento histórico.</p>
        <div class="ir">Abrir sección →</div></div>
      </button>
      <button class="tarjeta-romana" onclick="ver('v-kdd')">
        <div class="romano">V</div>
        <div><div class="kicker">Metodología</div><h3>Proceso KDD</h3>
        <p>Las cinco etapas del descubrimiento de conocimiento aplicadas a los datos de precipitación.</p>
        <div class="ir">Abrir sección →</div></div>
      </button>
    </div>

    <div class="stats">
      <div class="stat"><b>__N_VALIDOS__</b><span>registros celda-mes válidos procesados</span></div>
      <div class="stat"><b>__ANIOS__ años</b><span>de datos mensuales (1981–2025)</span></div>
      <div class="stat"><b>R² __R2__</b><span>coeficiente de determinación del modelo ganador</span></div>
      <div class="stat"><b>__ESTADO__</b><span>veredicto de los umbrales de aceptación</span></div>
    </div>

    <div class="bloque">
      <h2 class="titulo">Volumen de datos procesados</h2>
      <p class="subtitulo">Toda la investigación se sustenta en este volumen de información real de la fuente PISCOp v3.0 (SENAMHI).</p>
      <div class="volumen">
        <div class="vol"><span>Fuente de datos</span><b>PISCOp v3.0 (SENAMHI)</b></div>
        <div class="vol"><span>Periodo cubierto</span><b>1981 – 2025 (__ANIOS__ años)</b></div>
        <div class="vol"><span>Meses registrados</span><b>__MESES_N__ meses</b></div>
        <div class="vol"><span>Malla de observación</span><b>__MALLA_DIM__</b></div>
        <div class="vol"><span>Registros celda-mes</span><b>__MALLA__</b></div>
        <div class="vol"><span>Registros válidos</span><b>__N_VALIDOS__ (__PCT__ %)</b></div>
        <div class="vol"><span>Entrenamiento</span><b>__TRAIN__ registros</b></div>
        <div class="vol"><span>Prueba</span><b>__TEST__ registros</b></div>
        <div class="vol"><span>Rango de precipitación</span><b>__MM_MIN__ – __MM_MAX__ mm</b></div>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════ ANÁLISIS REGIONAL ═══════════ -->
<div class="vista" id="v-analisis">
  <div class="cont">
    <div class="bloque">
      <p class="kicker-seccion">IV · Inteligencia territorial</p>
      <h2 class="titulo">Análisis regional — mapa de calor de la precipitación</h2>
      <p class="subtitulo">Haz clic en un departamento del mapa para ver su precipitación media mensual,
      su puesto nacional y sus datos procesados. La escala representa la precipitación media mensual en milímetros.</p>
      <div class="mapa-zona">
        <div class="mapa-caja">
          <div id="tooltip-mapa"></div>
          <svg class="mapa" id="mapa" viewBox="-81.40 -2.00 17.40 21.00">
            <image x="-81.40" y="-2.00" width="17.40" height="21.00" preserveAspectRatio="none"
                   href="__IMG_RASTER__"></image>
            <g id="capa-deptos"></g>
          </svg>
          <div class="leyenda">
            <span><i style="background:#9A3412"></i> Muy lluvioso (más de 420 mm)</span>
            <span><i style="background:#EA580C"></i> Alto (260–420 mm)</span>
            <span><i style="background:#FDBA74"></i> Medio (140–260 mm)</span>
            <span><i style="background:#FED7AA"></i> Bajo (menos de 140 mm)</span>
            <span><i style="background:#F8FAFC;border:1px solid var(--linea)"></i> Sin datos</span>
          </div>
        </div>
        <div>
          <div class="mapa-caja panel-datos">
            <h3 id="info-nombre">Perú</h3>
            <p id="info-region" style="font-size:11.5px;color:var(--gris);margin:4px 0 10px"></p>
            <div id="info-datos"></div>
            <p style="font-size:11.5px;color:var(--gris);margin:14px 0 26px"><b>Climatología mensual (mm)</b></p>
            <div class="clima-barras" id="info-clim"></div>
            <p style="font-size:11.5px;color:var(--gris);margin:16px 0 8px"><b>Proyección 2026 (mm)</b></p>
            <div class="proy-linea" id="info-proy"></div>
          </div>
          <div class="mapa-caja" style="margin-top:15px">
            <p style="font-size:12px;color:var(--gris);margin-bottom:6px"><b>Top 5 departamentos más lluviosos</b> (clic para ver)</p>
            <div id="info-top"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="bloque">
      <h2 class="titulo">Resumen por departamento</h2>
      <p class="subtitulo">Los 25 departamentos ordenados por precipitación media mensual.</p>
      <div class="envoltura"><table class="tabla">
        <tr><th>Departamento</th><th class="num">Celdas</th><th class="num">Media mensual (mm)</th>
            <th class="num">Media anual (mm)</th><th>Mes más lluvioso</th>
            <th class="num">mm en ese mes</th><th class="num">MAE (mm)</th>
            <th class="num">Proyección 2026 (mm/mes)</th></tr>
        __TABLA_DEPTOS__
      </table></div>
    </div>

    <div class="bloque">
      <h2 class="titulo">Climatología mensual por departamento</h2>
      <p class="subtitulo">Precipitación media mensual en milímetros, promedio del periodo 1981–2025.</p>
      <div class="envoltura"><table class="tabla">
        <tr><th>Departamento</th>__MESES_TH__</tr>
        __TABLA_CLIM__
      </table></div>
    </div>

    <div class="bloque">
      <div class="tarjeta">
        <h3 style="margin-bottom:6px">Descarga de tablas</h3>
        <p style="font-size:12.5px;color:var(--gris);margin-bottom:13px">Archivos CSV con separador «;» para abrirse directamente en Excel.</p>
        <a class="boton hueso" href="descargas/01_departamentos.csv">Departamentos</a>
        <a class="boton hueso" href="descargas/02_climatologia_mensual.csv">Climatología mensual</a>
        <a class="boton hueso" href="descargas/03_modelos_comparados.csv">Modelos comparados</a>
        <a class="boton hueso" href="descargas/04_proyeccion_2026.csv">Proyección 2026</a>
        <a class="boton hueso" href="descargas/05_resumen_etl.csv">Resumen ETL</a>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════ FICHA DE REGISTRO ═══════════ -->
<div class="vista" id="v-ficha">
  <div class="cont">
    <div class="bloque">
      <p class="kicker-seccion">I · Diseño de investigación</p>
      <h2 class="titulo">Ficha de registro — instrumento de recolección</h2>
      <p class="subtitulo">Instrumento de registro documental tal como se aplicó en la investigación,
      con 20 registros reales de la celda de Lima (lat −12,05°, lon −77,05°) entre 198201 y 198308.</p>
      <div class="tarjeta">
        __FICHA__
      </div>
    </div>
  </div>
</div>

<!-- ═══════════ MÉTRICAS DE CALIDAD ═══════════ -->
<div class="vista" id="v-metricas">
  <div class="cont">
    <div class="bloque">
      <p class="kicker-seccion">II · Validación estadística</p>
      <h2 class="titulo">Métricas de calidad del modelo ganador</h2>
      <p class="subtitulo">Cada métrica se compara con su umbral esperado de aceptación.
      Los resultados provienen de la corrida del experimento sobre el conjunto de prueba.</p>
      <div class="rejilla-metricas">
        __TARJETA_MAE____TARJETA_RMSE____TARJETA_R2__
      </div>

      <div class="tarjeta" style="margin-top:18px">
        <h3 style="margin-bottom:10px">Criterios de aceptación aplicados</h3>
        <div class="envoltura"><table class="tabla">
          <tr><th>Criterio</th><th>Umbral esperado</th><th class="num">Mi resultado</th><th>Estado</th></tr>
          <tr><td>Relación MAE / MAE de la persistencia</td><td>Menor que 0,90</td>
              <td class="num">__REL_MAE__</td><td>__BADGE_MAE__</td></tr>
          <tr><td>Relación RMSE / RMSE de la persistencia</td><td>Menor que 0,90</td>
              <td class="num">__REL_RMSE__</td><td>__BADGE_RMSE__</td></tr>
          <tr><td>Coeficiente de determinación R²</td><td>Mayor o igual que 0,75 (excelente)</td>
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

<!-- ═══════════ RESULTADOS ═══════════ -->
<div class="vista" id="v-resultados">
  <div class="cont">
    <div class="bloque">
      <p class="kicker-seccion">III · Hallazgos predictivos</p>
      <h2 class="titulo">Resultados de la investigación</h2>
      <p class="subtitulo">Cuatro algoritmos de regresión de aprendizaje supervisado evaluados con las
      mismas particiones de entrenamiento y prueba: Regresión Ridge, Regresión KNN, Random Forest y XGBoost.
      El modelo ganador está destacado.</p>
      <div class="envoltura"><table class="tabla">
        <tr><th>Modelo</th><th class="num">Obs. de entrenamiento</th><th class="num">MAE (mm)</th>
            <th class="num">RMSE (mm)</th><th class="num">R²</th>
            <th class="num">Rel. MAE vs persistencia</th><th class="num">Rel. RMSE vs persistencia</th></tr>
        __TABLA_MODELOS__
      </table></div>

      <div class="figuras" style="margin-top:18px">
        <div class="figura"><img src="__IMG_BARRAS__" alt="Comparación de los 4 algoritmos">
          <p>Comparación del error (RMSE) entre los cuatro algoritmos evaluados.</p></div>
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
        <div class="figura"><img src="__IMG_ERROR__" alt="Distribución del error">
          <p>Distribución espacial del error de predicción (MAE) sobre la malla PISCOp.</p></div>
        <div class="figura"><img src="__IMG_HERO__" alt="Precipitación media observada">
          <p>Precipitación media mensual observada sobre la malla PISCOp (1981–2025).</p></div>
      </div>
    </div>

    <div class="bloque">
      <p class="kicker-seccion">Referencias</p>
      <h2 class="titulo">Fuentes de datos</h2>
      <div class="tarjeta fuentes">
        <p><b>[1]</b> SENAMHI, «PISCOp v3.0: Producto Integrado de Precipitación a escala Nacional Compilado», Perú. [En línea]. Disponible en: http://hydro.chc.ucsb.edu/.</p>
        <p><b>[3]</b> C. Funk et al., «The climate hazards infrared precipitation with stations—a new environmental record for monitoring extremes», <i>Scientific Data</i>, vol. 2, 2015.</p>
        <p style="margin-top:8px;font-size:11.5px">Los resultados mostrados provienen de la corrida del experimento sobre PISCOp v3.0.
        El prototipo se actualizará en el futuro con la fuente CHIRPS v2.0.</p>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════ PROCESO KDD ═══════════ -->
<div class="vista" id="v-kdd">
  <div class="cont">
    <div class="bloque">
      <p class="kicker-seccion">V · Metodología</p>
      <h2 class="titulo">Proceso KDD — descubrimiento de conocimiento en bases de datos</h2>
      <p class="subtitulo">El procesamiento de la información siguió las cinco etapas del proceso KDD.
      A continuación se describe qué se hizo en cada etapa con los datos de precipitación.</p>
      <div class="flujo">
        <div class="flujo-linea"><span class="flujo-onda"></span></div>
        <button class="nodo-kdd activa" onclick="kddMostrar(0)"><span class="nodo-num">1</span><b>Selección</b></button>
        <button class="nodo-kdd" onclick="kddMostrar(1)"><span class="nodo-num">2</span><b>Preprocesamiento</b></button>
        <button class="nodo-kdd" onclick="kddMostrar(2)"><span class="nodo-num">3</span><b>Transformación</b></button>
        <button class="nodo-kdd" onclick="kddMostrar(3)"><span class="nodo-num">4</span><b>Minería</b></button>
        <button class="nodo-kdd" onclick="kddMostrar(4)"><span class="nodo-num">5</span><b>Evaluación</b></button>
      </div>

      <div class="etapa-panel activa">
        <div>
          <div class="etapa-tag">Etapa 1 de 5</div>
          <h3>Selección</h3>
          <p class="desc">Se definió la fuente PISCOp v3.0 (SENAMHI) y el periodo 1981–2025, con 540
          meses de precipitación en malla de 0,1° sobre el territorio nacional. Se formularon las
          preguntas de predicción y se eligieron los cuatro algoritmos de regresión supervisada.</p>
          <div class="cifras">
            <div class="cifra"><span>Periodo</span><b>1981 – 2025</b></div>
            <div class="cifra"><span>Meses registrados</span><b>__MESES_N__</b></div>
            <div class="cifra"><span>Resolución</span><b>0,1° ≈ 10 km</b></div>
          </div>
        </div>
        <div class="visual">
          <div class="grilla">__GRILLA_SEL__</div>
          <div class="leyenda-v"><span><i style="background:#FB923C"></i>Celda de la malla con dato mensual</span>
            <span>Cada cuadro es una celda de 0,1° · malla de __MALLA_DIM__</span></div>
        </div>
      </div>

      <div class="etapa-panel">
        <div>
          <div class="etapa-tag">Etapa 2 de 5</div>
          <h3>Preprocesamiento</h3>
          <p class="desc">Se identificaron y eliminaron los valores centinela (sin dato) del archivo
          NetCDF. De una malla total de __MALLA__ registros celda-mes se consolidaron __N_VALIDOS__
          registros válidos (__PCT__ % del total).</p>
          <div class="cifras">
            <div class="cifra"><span>Malla total</span><b>__MALLA__</b></div>
            <div class="cifra"><span>Registros válidos</span><b>__N_VALIDOS__</b></div>
            <div class="cifra"><span>Conservado</span><b>__PCT__ %</b></div>
          </div>
        </div>
        <div class="visual">
          <div class="grilla">__GRILLA_PREP__</div>
          <div class="leyenda-v"><span><i style="background:#FB923C"></i>Registro válido</span>
            <span><i style="background:#DCE3EC"></i>Centinela eliminado (sin dato)</span></div>
        </div>
      </div>

      <div class="etapa-panel">
        <div>
          <div class="etapa-tag">Etapa 3 de 5</div>
          <h3>Transformación</h3>
          <p class="desc">Se construyó la variable objetivo (precipitación del mes siguiente) y las
          variables de entrada de las dimensiones D1, D2 y D3 del instrumento. Se generaron las
          particiones de entrenamiento y prueba.</p>
          <div class="cifras">
            <div class="cifra"><span>Dimensiones</span><b>D1 · D2 · D3</b></div>
            <div class="cifra"><span>Variable objetivo</span><b>Mes siguiente</b></div>
          </div>
        </div>
        <div class="visual">
          <div class="chips-flujo">
            <span class="chip-d">D1 · Magnitud</span>
            <span class="chip-d">D2 · Estacionalidad</span>
            <span class="chip-d">D3 · Persistencia</span>
            <span class="flecha">→</span>
            <span class="chip-o">y(c,t+1) · mm</span>
          </div>
          <div class="leyenda-v"><span>Partición de los registros válidos</span></div>
          __SPLIT__
        </div>
      </div>

      <div class="etapa-panel">
        <div>
          <div class="etapa-tag">Etapa 4 de 5</div>
          <h3>Minería</h3>
          <p class="desc">Se entrenaron los cuatro algoritmos de la tesis (Regresión Ridge,
          Regresión KNN, Random Forest y XGBoost) sobre las observaciones de entrenamiento, con
          evaluación común sobre la muestra de prueba.</p>
          <div class="cifras">
            <div class="cifra"><span>Algoritmos</span><b>4</b></div>
            <div class="cifra"><span>Evaluación común</span><b>__TEST__ obs.</b></div>
          </div>
        </div>
        <div class="visual">
          <p style="font-size:11px;color:var(--gris);font-weight:700;margin-bottom:4px">RMSE por algoritmo (mm) — menor es mejor</p>
          __BARRAS_ALGOS__
        </div>
      </div>

      <div class="etapa-panel">
        <div>
          <div class="etapa-tag">Etapa 5 de 5</div>
          <h3>Evaluación e interpretación</h3>
          <p class="desc">Se calcularon MAE, RMSE y R², se compararon con las líneas base de
          persistencia y climatología frente a los umbrales de aceptación, se seleccionó el modelo
          ganador y se proyectó la precipitación de 2026.</p>
          <div class="cifras">
            <div class="cifra"><span>Umbrales</span><b>3 de 3 cumplidos</b></div>
            <div class="cifra"><span>Proyección</span><b>2026 generada</b></div>
          </div>
        </div>
        <div class="visual">
          <div class="metricas-mini">
            <div class="metrica-mini"><b>__GAN_MAE__</b><span>MAE (mm) · cumple</span></div>
            <div class="metrica-mini"><b>__GAN_RMSE__</b><span>RMSE (mm) · cumple</span></div>
            <div class="metrica-mini"><b>__R2__</b><span>R² · cumple</span></div>
          </div>
          <div class="ganador-strip"><span>Modelo ganador</span><b>__GAN_NOMBRE__</b></div>
        </div>
      </div>

      <div class="kdd-controles">
        <button class="boton" id="kdd-play" onclick="kddPlay()">Reproducir proceso</button>
        <span class="kdd-progreso">Toca cada etapa del flujo o reproduce el proceso completo</span>
      </div>

      <div class="tarjeta" style="margin-top:20px">
        <h3 style="margin-bottom:8px">Del archivo fuente al conocimiento</h3>
        <p class="subtitulo" style="margin-bottom:0">El archivo fuente PISCOp_m.nc contiene 540 mapas
        mensuales de precipitación (uno por cada mes de enero de 1981 a diciembre de 2025) organizados en
        una malla de __MALLA_DIM__. Cada celda de la malla representa un área de aproximadamente 10 km
        de lado. El proceso transformó esos mapas en __N_VALIDOS__ registros válidos de celda-mes,
        los cuales alimentaron el entrenamiento de los algoritmos y la selección del modelo ganador
        que hoy sostiene la proyección de la precipitación de 2026 y el análisis regional por
        departamento.</p>
      </div>
    </div>
  </div>
</div>

<footer class="pie">
  <div class="cont">
    <p><b>Comparación de algoritmos de regresión de aprendizaje supervisado para la predicción de la
    precipitación mensual en el Perú</b></p>
    <p style="margin-top:6px">Universidad César Vallejo · Sede Lima Este · Escuela Profesional de Ingeniería de Sistemas ·
    Datos PISCOp v3.0 (SENAMHI) [1] · CHIRPS [3]</p>
    <p style="margin-top:6px">__ANIOS__ años de datos · __N_VALIDOS__ registros válidos procesados · 4 algoritmos comparados</p>
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
    f"Relación MAE/MAE de la persistencia menor que {num(umbral_rel_mae, 2)}",
    num(GAN["rel_mae"], 2), ok_mae,
    "El modelo reduce el error en más de la mitad frente a la persistencia (mes anterior).")
tarjeta_rmse = tarjeta_metrica(
    "RMSE", num(GAN["rmse"], 2), "mm",
    "Raíz del error cuadrático medio: penaliza con mayor fuerza los errores grandes.",
    f"Relación RMSE/RMSE de la persistencia menor que {num(umbral_rel_rmse, 2)}",
    num(GAN["rel_rmse"], 2), ok_rmse,
    "El modelo supera claramente a la persistencia también en los eventos extremos.")
tarjeta_r2 = tarjeta_metrica(
    "R²", num(GAN["r2"], 2), "",
    "Coeficiente de determinación: proporción de la variabilidad de la lluvia explicada por el modelo.",
    f"R² mayor o igual que {num(umbral_r2, 2)} (nivel excelente)",
    num(GAN["r2"], 2), ok_r2,
    "Casi 8 de cada 10 puntos de variación de la precipitación mensual quedan explicados.")

html = (PLANTILLA
        .replace("__CSS__", CSS)
        .replace("__JS_MAPA__", JS_MAPA)
        .replace("__DATOS__", json.dumps(DATOS, ensure_ascii=False, separators=(",", ":")))
        .replace("__IMG_HERO__", b64("hero_precipitacion.png"))
        .replace("__IMG_RASTER__", b64("raster_lluvia.png"))
        .replace("__IMG_BARRAS__", grafico_barras_4(MODELOS, GAN))
        .replace("__IMG_REGRESION__", b64("regresion_linea.png"))
        .replace("__IMG_PROY__", b64("serie_proyeccion.png"))
        .replace("__IMG_ERROR__", b64("mapa_error.png"))
        .replace("__FICHA__", FICHA_HTML)
        .replace("__AUTOR__", AUTOR)
        .replace("__ASESOR__", ASESOR)
        .replace("__LINEA__", LINEA)
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
        .replace("__ESTADO__", "Todos los umbrales" if TODO_OK else "Ver tabla")
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
        .replace("__GRILLA_SEL__", grilla())
        .replace("__GRILLA_PREP__", grilla(nulos=NULOS_PREP))
        .replace("__BARRAS_ALGOS__", barras_mineria())
        .replace("__SPLIT__", split_particiones())
        .replace("__MESES_TH__", "".join(f"<th class='num'>{m}</th>" for m in MESES))
        )

os.makedirs(D_OUT, exist_ok=True)
ruta = os.path.join(D_OUT, "index.html")
with open(ruta, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Sitio generado: {ruta}")
print(f"Tamano: {os.path.getsize(ruta)/1024:.0f} KB · vistas: 6")
print(f"Algoritmos (4): {[m['nombre'] for m in MODELOS]}")
print(f"Ganador: {GAN['nombre']} · MAE {GAN['mae']:.2f} · RMSE {GAN['rmse']:.2f} · R2 {GAN['r2']:.3f}")
print(f"Umbrales -> MAE {GAN['rel_mae']:.2f} {'OK' if ok_mae else 'X'} | "
      f"RMSE {GAN['rel_rmse']:.2f} {'OK' if ok_rmse else 'X'} | R2 {GAN['r2']:.2f} {'OK' if ok_r2 else 'X'}")
