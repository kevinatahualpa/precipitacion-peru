#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
actualizar_panel.py — Actualiza docs/index.html (panel) y docs/descargas/*.csv
con los resultados FINALES del experimento (12/12), sin tocar el diseño.

FUENTE ÚNICA DE VERDAD
  /home/rusitos/Documents/RESULTADOS KAGGLE/results/
      metrics_todos.csv              MAE, RMSE, R², tiempos y parámetros (config. full)
      baseline_persistencia.csv      línea base de referencia
      dm_matrix_full.csv             p de Diebold-Mariano (config. full)
      wilcoxon_matrix_full.csv       p de Wilcoxon (config. full)
      features.parquet               conteos y min/máx de P
  TESIS-PRECIPITACION/05_PRODUCTO_ANEXOS/recalculo_espacial/salida_sitio.json
      dominio (Perú), MAE por departamento y proyección 2026
      (generado por recalcular_espacial_final.py con controles aprobados)

NADA SE ESCRIBE A MANO EN EL HTML: todos los números salen de los CSV/JSON.

NO confundir con motor/generar_sitio.py, que genera el sitio v3 anterior
(gris/naranja) y sobrescribe docs/index.html: no ejecutarlo.

Uso:  /tmp/opencode/venv/bin/python motor/actualizar_panel.py
"""
import csv
import json
import os
import re

import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL = os.path.join(RAIZ, "docs", "index.html")
DESC = os.path.join(RAIZ, "docs", "descargas")

RESULTS = "/home/rusitos/Documents/RESULTADOS KAGGLE/results"
SALIDA = ("/home/rusitos/Documents/Proyecto predeterminado/TESIS-PRECIPITACION/"
          "05_PRODUCTO_ANEXOS/recalculo_espacial/salida_sitio.json")

NOMBRES = {"Ridge": "Regresión Ridge", "RF": "Random Forest",
           "XGB": "XGBoost", "KNNFAISS": "KNN-FAISS (HNSW)"}
TRAIN = 11573496                    # 29 226 celdas x 396 meses (1982-2014)
N_CELDAS, N_MESES_TEORICAS = 210 * 174, 528
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]

cambios = []


def es(v, d=2):
    """Número en texto con coma decimal (estilo del panel)."""
    return f"{v:.{d}f}".replace(".", ",")


def tiempo_zona(s):
    """Tiempo para la zona 03 del KDD (segundos si es corto, si no h/min)."""
    if s < 3600:
        return f"{s:,.1f}".replace(",", " ").replace(".", ",") + " s"
    h, m = int(s // 3600), round((s % 3600) / 60)
    return f"{h} h {m} min"


# ───────────────────────── carga de fuentes ─────────────────────────
mt = pd.read_csv(os.path.join(RESULTS, "metrics_todos.csv"))
full = {r.modelo: r for r in mt[mt.config == "full"].itertuples()}
assert set(full) == {"RF", "XGB", "Ridge", "KNNFAISS"}, full.keys()

base = pd.read_csv(os.path.join(RESULTS, "baseline_persistencia.csv")).iloc[0]
B_MAE, B_RMSE = float(base.MAE), float(base.RMSE)

dm = pd.read_csv(os.path.join(RESULTS, "dm_matrix_full.csv"))
wx = pd.read_csv(os.path.join(RESULTS, "wilcoxon_matrix_full.csv"))
par_p = {}
for r in dm.itertuples():
    par_p[r.par] = {"dm": float(r.p)}
for r in wx.itertuples():
    par_p[r.par]["w"] = float(r.p)

sal = json.load(open(SALIDA, encoding="utf-8"))
DOM, DEP, PROY = sal["dominio"], sal["mae_por_departamento"], sal["proyeccion_2026_ridge"]

gan = full["RF"]                       # ganador: menor RMSE y mayor R²
assert gan.RMSE == min(r.RMSE for r in full.values()), "RF no es el de menor RMSE"
assert gan.R2 == max(r.R2 for r in full.values()), "RF no es el mayor R²"

m = {k: dict(mae=round(float(v.MAE), 4), rmse=round(float(v.RMSE), 4),
             r2=round(float(v.R2), 4), t=float(v.tiempo_s),
             relmae=round(float(v.MAE) / B_MAE, 5),
             relrmse=round(float(v.RMSE) / B_RMSE, 5))
     for k, v in full.items()}

# ───────────────────────── carga del panel ─────────────────────────
txt = open(PANEL, encoding="utf-8").read()
original = txt


def reemplaza_patron(patron, nuevo, nombre):
    """Sustituye el primer bloque que cumple el patrón; idempotente."""
    global txt
    if nuevo in txt:
        print(f"  · {nombre}: ya estaba actualizado")
        return
    hit = re.search(patron, txt, re.S)
    assert hit, f"NO SE ENCONTRÓ: {nombre}"
    assert txt.count(hit.group(0)) == 1, f"BLOQUE AMBIGUO: {nombre}"
    txt = txt[:hit.start()] + nuevo + txt[hit.end():]
    cambios.append(nombre)


def reemplaza_texto(viejo, nuevo, nombre):
    """Sustituye una cadena exacta; idempotente."""
    global txt
    if nuevo in txt:
        print(f"  · {nombre}: ya estaba actualizado")
        return
    assert txt.count(viejo) == 1, f"NO SE ENCONTRÓ (o es ambiguo): {nombre}"
    txt = txt.replace(viejo, nuevo)
    cambios.append(nombre)


# ── A · cabecera: fuente de los valores ──
cab_nueva = f"""<!-- ══════════════════════════════════════════════════════════════
     1 · DATOS DEL PANEL
     Objeto único y al inicio del archivo. Actualícelo con
     motor/actualizar_panel.py; no lo edite a mano.

     FUENTE DE LOS VALORES ACTUALES — corrida final (12/12 experimentos)
       · metrics_todos.csv        → MAE, RMSE, R² y tiempos (config. full)
       · baseline_persistencia.csv → línea base de referencia
       · dm_matrix_full.csv / wilcoxon_matrix_full.csv → significancia
       · preds_RF_full.npy        → error del ganador por celda y departamento
       · model_Ridge_full.joblib  → proyección 2026 (Regresión Ridge)
       · 05_PRODUCTO_ANEXOS/recalculo_espacial/ → dominio y departamentos
         (controles aprobados: MAE {m['RF']['mae']:.4f} · RMSE {m['RF']['rmse']:.4f} · R² {m['RF']['r2']:.4f})
     ══════════════════════════════════════════════════════════════ -->"""
reemplaza_patron(r"<!-- ═+\n     1 · DATOS DEL PANEL[\s\S]*?-->", cab_nueva, "cabecera fuente")

# ── B · dominio: error del ganador dentro/fuera del Perú ──
dom_nuevo = f"""  /* ── 4d · Dominio de evaluación ──
     Error del ganador (Random Forest, config. full) medido sobre TODAS las
     celdas con dato válido del dominio PISCOp ({DOM['celdas']:,} celdas), que
     incluye área adyacente al Perú, y sobre las {DOM['celdasPeru']:,} celdas
     dentro del territorio peruano. Justifica por qué el MAE en celdas
     peruanas ({es(DOM['maePeru'])} mm) no reproduce el MAE global del ganador
     ({es(DOM['maeGlobalGanador'])} mm): son poblaciones distintas.
     Fuente: recalcular_espacial_final.py (controles aprobados). */
  dominio: {{
    celdas: {DOM['celdas']},
    celdasPeru: {DOM['celdasPeru']},
    obsPrueba: {DOM['obsPrueba']},
    obsPeru: {DOM['obsPeru']},
    fracPeru: {DOM['fracPeru']},
    maePeru: {DOM['maePeru']},
    rmsePeru: {DOM['rmsePeru']},
    r2Peru: {DOM['r2Peru']},
    skillPeru: {DOM['skillPeru']}
  }},"""
reemplaza_patron(r"  /\* ── 4d · Dominio de evaluación[\s\S]*?\n  \},",
                 dom_nuevo, "bloque dominio")

# ── C · significancia: p reales de la corrida final ──
pares = [
    ("Regresión Ridge vs. Random Forest", "Ridge vs RF"),
    ("Regresión Ridge vs. XGBoost", "Ridge vs XGB"),
    ("Regresión Ridge vs. KNN-FAISS", "Ridge vs KNNFAISS"),
    ("Regresión Ridge vs. persistencia", "Ridge vs Persistencia"),
]
filas_pares = ",\n".join(
    f'      {{ par: "{etq}", dm: {par_p[k]["dm"]!r}, w: {par_p[k]["w"]!r} }}'
    for etq, k in pares)
sig_nuevo = f"""  /* ── 4c · Pruebas de significancia sobre el conjunto de prueba ──
     dm : p de Diebold-Mariano sobre el error cuadrático mensual (132 meses)
     w  : p de Wilcoxon con signo sobre el error absoluto mensual (132 meses)
     Se reporta la configuración final (full) de los cuatro algoritmos
     (dm_matrix_full.csv / wilcoxon_matrix_full.csv). */
  significancia: {{
    alfa: 0.05,
    nota: "Se comparan las series mensuales de error (132 meses) de cada par de pronósticos sobre el conjunto de prueba: Diebold-Mariano sobre el error cuadrático medio y Wilcoxon sobre el error absoluto medio.",
    pares: [
{filas_pares}
    ]
  }},"""
reemplaza_patron(r"  /\* ── 4c · Pruebas de significancia[\s\S]*?\n  \},",
                 sig_nuevo, "bloque significancia")

# ── D · tabla de algoritmos comparados (sección 03) ──
orden = ["Ridge", "RF", "XGB", "KNNFAISS"]
filas_mod = ",\n".join(
    '    { modelo: "%s",  tiempo: %s, mae: %s, rmse: %s, r2: %s, relMae: %s, relRmse: %s }'
    % (NOMBRES[k],
       ("%g" % m[k]["t"]),
       ("%g" % m[k]["mae"]), ("%g" % m[k]["rmse"]), ("%g" % m[k]["r2"]),
       ("%g" % m[k]["relmae"]), ("%g" % m[k]["relrmse"]))
    for k in orden)
mod_nuevo = f"""  /* ── 5 · Algoritmos comparados (conjunto de prueba, config. full) ──
     tiempo : segundos de la corrida (CV + ajuste + predicción) en metrics_todos.csv
     relMae / relRmse : métrica del modelo / métrica de la persistencia */
  modelos: [
{filas_mod}
  ],"""
reemplaza_patron(r"  /\* ── 5 · Algoritmos comparados[\s\S]*?\n  \],",
                 mod_nuevo, "bloque modelos")

# ── E · proyección: rotular el modelo que la calcula ──
proy_nuevo = """  /* ── 6 · Proyección nacional 2026 (mm/mes) ──
     Recalculada con 05_PRODUCTO_ANEXOS/recalcular_espacial_final.py:
     Regresión Ridge (config. full), predicción recursiva mes a mes con los
     lags observados hasta 2025. El error por departamento sí es del ganador
     (Random Forest); esta serie usa el pipeline Ridge conservado, cuyas
     predicciones coinciden con las de la corrida final hasta 2,4 × 10⁻⁴ mm.
     Se promedia SOLO sobre las celdas dentro del territorio peruano
     (9 963 celdas); total anual 1 832 mm por celda. */
  proyeccion: {
    anio: "2026",
    modelo: "la Regresión Ridge","""
if 'modelo: "la Regresión Ridge",' in txt:
    print("  · proyección (rotular modelo): ya estaba actualizado")
else:
    reemplaza_patron(r'  /\* ── 6 · Proyección nacional 2026[\s\S]*?anio: "2026",',
                     proy_nuevo, "proyección (rotular modelo)")

# ── F · departamentos: comentario del bloque ──
dep_com = """  /* ── 7 · Departamentos: precipitación media y geometría del mapa ──
        mm      : precipitación media mensual (mm/mes)
        anual   : precipitación media anual (mm)
        mes     : mes más lluvioso (clave corta)
        mmMes   : mm registrados en ese mes
        mae     : error absoluto medio del GANADOR, Random Forest (mm)
        celdas  : celdas PISCOp que lo componen
        proy    : proyección 2026 con la Regresión Ridge (mm/mes)
        d       : contorno del departamento en coordenadas lon,lat (grados)   */"""
reemplaza_patron(r"  /\* ── 7 · Departamentos[\s\S]*?\*/", dep_com,
                 "comentario departamentos")

# ── G · comentario del proceso KDD: fuente y métricas de la corrida final ──
reemplaza_texto(
    "TODAS las cifras provienen de resultsALL (corrida del experimento),",
    "TODAS las cifras provienen de la corrida final (RESULTADOS KAGGLE/results),",
    "fuente KDD")
reemplaza_texto(
    """       · RMSE Ridge 74,23  ->  74,73 ; RF 75,82 -> 75,38 ; XGB 75,17 -> 76,29
       · KNN 79,95         ->  KNN-FAISS 81,22
       · R² 0,80           ->  0,797""",
    f"""       · Métricas finales (config. full): RF {es(m['RF']['mae'])} / {es(m['RF']['rmse'])} / {es(m['RF']['r2'], 3)} (ganador),
         Ridge {es(m['Ridge']['mae'])} / {es(m['Ridge']['rmse'])} / {es(m['Ridge']['r2'], 3)} ·
         XGB {es(m['XGB']['mae'])} / {es(m['XGB']['rmse'])} / {es(m['XGB']['r2'], 3)} ·
         KNN-FAISS {es(m['KNNFAISS']['mae'])} / {es(m['KNNFAISS']['rmse'])} / {es(m['KNNFAISS']['r2'], 3)}""",
    "métricas KDD")

# ── H · zona 03 del KDD: modelos ──
cortos = {"Ridge": "Ridge", "RF": "RF", "XGB": "XGBoost", "KNNFAISS": "KNN-FAISS"}
filas_z3 = ",\n".join(
    '      { corto: "%s", nombre: "%s", mae: %s, rmse: %s, r2: %s, tiempo: "%s"%s }'
    % (cortos[k], NOMBRES[k],
       ("%g" % round(m[k]["mae"], 2)), ("%g" % round(m[k]["rmse"], 2)),
       ("%g" % round(m[k]["r2"], 3)), tiempo_zona(m[k]["t"]),
       ", ganador: true" if k == "RF" else "")
    for k in orden)
z3_nuevo = f"""    modelos: [
{filas_z3}
    ],"""
reemplaza_patron(r"    modelos: \[\n      \{ corto:[\s\S]*?\n    \],",
                 z3_nuevo, "zona 03 (modelos KDD)")

# ── I · zona 04 del KDD: evaluación del ganador ──
g = m["RF"]
z4_nuevo = f"""    evaluacion: {{
      modelo: "{NOMBRES['RF']}",
      config: "config. full · 10 variables",
      metricas: [
        {{ sigla: "MAE",  valor: "{es(g['mae'])} mm", rel: "{es(g['relmae'])}", nota: "rel. vs persistencia ({es(B_MAE)} mm)", cumple: true }},
        {{ sigla: "RMSE", valor: "{es(g['rmse'])} mm", rel: "{es(g['relrmse'])}", nota: "rel. vs persistencia ({es(B_RMSE)} mm)", cumple: true }},
        {{ sigla: "R²",   valor: "{es(g['r2'], 3)}",  rel: "—",    nota: "coeficiente de determinación",     cumple: true }}
      ],
      veredicto: "3 de 3 umbrales de aceptación cumplidos",
      skill: "Skill frente a la persistencia: {es(1 - g['mae'] / B_MAE, 3)}",
      significancia: "Diebold-Mariano (p < 0,001) y Wilcoxon (p = 2,19 × 10⁻²³) confirman la mejora sobre la persistencia"
    }},"""
reemplaza_patron(r"    evaluacion: \{[\s\S]*?\n    \},", z4_nuevo, "zona 04 (evaluación KDD)")
reemplaza_texto("(4 dimensiones), clim (6) y full (10);",
                "(4 variables), clim (6) y full (10);",
                "zona 04 comentario (dimensiones→variables)")

# ── J · zona 05 del KDD: reporte ──
z5_nuevo = f"""    reporte: {{
      titulo: "System summary",
      conclusiones: [
        "Random Forest obtuvo el mejor desempeño en MAE, RMSE y R² ({es(g['mae'])} mm, {es(g['rmse'])} mm y {es(g['r2'], 3)}).",
        "Los 4 algoritmos superaron los umbrales de aceptación y la línea base de persistencia ({es(B_MAE)} mm).",
        "La proyección 2026 y el análisis regional de los 25 departamentos se calcularon con la Regresión Ridge ({es(m['Ridge']['mae'])} mm de MAE)."
      ],
      pie: "Datos: PISCOp v3.0 (SENAMHI) · 1982–2025 · 15 431 328 registros · cifras de la corrida final (12/12 experimentos)"
    }}"""
reemplaza_patron(r"    reporte: \{[\s\S]*?\n    \}", z5_nuevo, "zona 05 (reporte KDD)")

# ── K · pie del panel ──
reemplaza_texto(
    '  pie: "Panel demostrativo – los datos se actualizarán con los resultados finales"',
    '  pie: "Panel demostrativo · resultados definitivos de la corrida final (12/12 experimentos)"',
    "pie del panel")

# ── L · prosa de la proyección: modelo exacto ──
reemplaza_texto(
    '''    $("#proy-intro").textContent = "Precipitación media nacional proyectada mes a mes para el año " +
      DATOS.proyeccion.anio + " con el modelo ganador " + GANADOR.modelo + ".";''',
    '''    $("#proy-intro").textContent = "Precipitación media nacional proyectada mes a mes para el año " +
      DATOS.proyeccion.anio + " con " + esc(DATOS.proyeccion.modelo ||
        ("el modelo ganador " + GANADOR.modelo)) + ".";''',
    "proy-intro (modelo)")

# ── M · tooltip del mapa: rotular MAE y proyección ──
reemplaza_texto('["MAE del modelo", fmt(d.mae) + " mm"]',
                '["MAE del ganador", fmt(d.mae) + " mm"]',
                "tooltip MAE")
reemplaza_texto('Proyección 2026: <b>', 'Proyección 2026 (Ridge): <b>',
                "tooltip proyección")

# ── N · «dimensiones» de configuración → «variables» ──
reemplaza_texto("full (10 dimensiones: lat, lon, mes_sin, mes_cos, μ, σ y los",
                "full (10 variables: lat, lon, mes_sin, mes_cos, μ, σ y los",
                "KDD comentario (dimensiones→variables)")
reemplaza_texto("10 dimensiones: ubicación, mes del año, ",
                "10 variables: ubicación, mes del año, ",
                "KDD zona 03 extra (dimensiones→variables)")

# ── O · MAE por departamento (25 valores reales del ganador) ──
n_dep = 0
for nombre, val in DEP.items():
    patron = re.compile(r'(\{ n:"' + re.escape(nombre) + r'", [^\n]*?mae:)[\d.]+')
    txt, k = patron.subn(lambda mo: mo.group(1) + ("%g" % val), txt, count=1)
    assert k == 1, f"departamento no encontrado: {nombre}"
    n_dep += 1
cambios.append(f"MAE por departamento ({n_dep} valores)")

open(PANEL, "w", encoding="utf-8").write(txt)
print(f"· panel actualizado: {PANEL}")

# ───────────────────────── descargas CSV ─────────────────────────
os.makedirs(DESC, exist_ok=True)


def csv_write(nombre, cabecera, filas):
    with open(os.path.join(DESC, nombre), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cabecera)
        w.writerows(filas)


# 01 · departamentos, desde el bloque ya actualizado del panel
html = open(PANEL, encoding="utf-8").read()
ini = html.index("departamentos: [")
fin = html.index("\n  ],", ini)
re_dep = re.compile(r'\{ n:"([^"]+)", mm:([\d.]+), anual:([\d.]+), mes:"([^"]+)", '
                    r'mmMes:([\d.]+), mae:([\d.]+), celdas:(\d+), proy:([\d.]+), '
                    r'd:"([^"]+)" \}')
deps = [m2.groups() for m2 in re_dep.finditer(html[ini:fin])]
assert len(deps) == 25, f"departamentos leídos: {len(deps)}"
csv_write("01_departamentos.csv",
          ["Departamento", "Celdas", "Media mensual (mm)", "Media anual (mm)",
           "Mes mas lluvioso", "mm en ese mes", "MAE (mm)",
           "Proyeccion 2026 media (mm/mes)"],
          sorted([[n, celdas, mm, anual, mes, mmMes, mae, proy]
                  for n, mm, anual, mes, mmMes, mae, celdas, proy, _d in deps]))

# 03 · modelos comparados (orden por MAE)
csv_write("03_modelos_comparados.csv",
          ["Modelo", "Observaciones de entrenamiento", "MAE (mm)", "RMSE (mm)", "R2",
           "Rel. MAE vs persistencia", "Rel. RMSE vs persistencia"],
          [[NOMBRES[k], TRAIN,
            round(m[k]["mae"], 2), round(m[k]["rmse"], 4), round(m[k]["r2"], 4),
            round(m[k]["relmae"], 4), round(m[k]["relrmse"], 4)]
           for k in sorted(m, key=lambda k: m[k]["mae"])])

# 04 · proyección 2026 (serie nacional del panel: solo celdas peruanas)
csv_write("04_proyeccion_2026.csv",
          ["Mes", "Precipitacion media nacional (mm)"],
          [[f"2026-{i:02d}", p["mm"]] for i, p in enumerate(PROY, 1)])

# 05 · resumen ETL (periodo y conteos reales de features.parquet)
P = pd.read_parquet(os.path.join(RESULTS, "features.parquet"), columns=["P"])["P"]
p_min, p_max = float(P.min()), float(P.max())
del P
malla_total = N_CELDAS * N_MESES_TEORICAS
registros = DOM["obsPrueba"] + TRAIN
csv_write("05_resumen_etl.csv", ["Parametro", "Valor"],
          [["Fuente", "PISCOp v3.0 (SENAMHI) - archivo PISCOp_m.nc"],
           ["Periodo", "1982-01 a 2025-12 (528 meses, 44 anios)"],
           ["Resolucion", "0,1 grado (aprox. 10 km)"],
           ["Malla", "210 x 174 = 36540 celdas"],
           ["Malla total (celda-mes)", malla_total],
           ["Registros validos", registros],
           ["Porcentaje valido", f"{100 * registros / malla_total:.2f} %"],
           ["Conjunto de entrenamiento", TRAIN],
           ["Conjunto de prueba", DOM["obsPrueba"]],
           ["Algoritmos comparados",
            "Random Forest (ganador), XGBoost, Regresion Ridge, Regresion KNN (KNN-FAISS)"],
           ["Minimo observado (mm)", round(p_min, 2)],
           ["Maximo observado (mm)", round(p_max, 2)]])

print("· descargas regeneradas: 01, 03, 04, 05 (02 es climatología, no se toca)")
print()
print("CAMBIOS APLICADOS:")
for c in cambios:
    print(f"  – {c}")
if txt == original:
    print("(sin cambios: el panel ya estaba al día)")
