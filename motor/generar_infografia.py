# -*- coding: utf-8 -*-
"""
Generador de la INFOGRAFÍA ANIMADA de la tesis (GIF + MP4 + PNG).
Tema: flujo completo PISCOp v3.0 -> ETL -> 4 algoritmos -> XGBoost ganador -> resultados.
Paleta: gris pizarra + naranja. Sin emojis, sin logotipos de terceros (solo siglas).
Salidas: docs/infografia/infografia_animada.gif | .mp4 | infografia_estatica.png
Uso: python3 motor/generar_infografia.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(BASE, "docs", "infografia")

# ── Paleta institucional ─────────────────────────────────────────────
SLATE = (30, 41, 59)
SLATE2 = (51, 65, 85)
SLATE3 = (100, 116, 139)
ORANGE = (234, 88, 12)
ORANGE2 = (251, 146, 60)
ORANGE_SOFT = (255, 241, 232)
ORANGE_BAR = (253, 186, 116)
BG = (248, 250, 252)
LINE = (226, 232, 240)
SOFT = (241, 245, 249)
WHITE = (255, 255, 255)
GREEN = (14, 122, 70)
GREEN_SOFT = (231, 246, 236)
MUTED = (148, 163, 184)

# ── Fuentes ─────────────────────────────────────────────────────────
RUTAS = {
    False: ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    True: ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-ExtraBold.ttf"],
}
_cache = {}


def font(size, bold=False):
    clave = (size, bold)
    if clave not in _cache:
        f = None
        for ruta in RUTAS[bold]:
            if os.path.exists(ruta):
                f = ImageFont.truetype(ruta, size)
                break
        _cache[clave] = f if f else ImageFont.load_default()
    return _cache[clave]


# ── Formato de números (coma decimal, espacio de miles) ─────────────
def ent(n, p=1.0):
    return f"{int(round(n * p)):,}".replace(",", " ")


def dec(v, d=2, p=1.0):
    return f"{v * p:.{d}f}".replace(".", ",")


def suave(p):
    p = 0.0 if p < 0 else (1.0 if p > 1 else p)
    return p * p * (3 - 2 * p)


# ── Lienzo con escala (permite PNG nítido a 2x) ─────────────────────
class Lienzo:
    def __init__(self, s=1, fondo=BG):
        self.s = s
        self.img = Image.new("RGB", (1280 * s, 720 * s), fondo)
        self.d = ImageDraw.Draw(self.img)

    def _b(self, box):
        return [v * self.s for v in box]

    def rrect(self, box, r, fill=None, outline=None, w=1):
        self.d.rounded_rectangle(self._b(box), radius=r * self.s,
                                 fill=fill, outline=outline,
                                 width=max(1, int(w * self.s)))

    def rect(self, box, fill=None, outline=None, w=1):
        self.d.rectangle(self._b(box), fill=fill, outline=outline,
                         width=max(1, int(w * self.s)))

    def linea(self, xy, fill, w=1):
        self.d.line(self._b(xy), fill=fill, width=max(1, int(w * self.s)))

    def circ(self, box, fill=None, outline=None, w=1):
        self.d.ellipse(self._b(box), fill=fill, outline=outline,
                       width=max(1, int(w * self.s)))

    def texto(self, xy, s, size, fill, bold=False, anchor="la"):
        self.d.text((xy[0] * self.s, xy[1] * self.s), s,
                    font=font(int(size * self.s), bold), fill=fill, anchor=anchor)

    def ancho(self, s, size, bold=False):
        return self.d.textlength(s, font=font(int(size * self.s), bold)) / self.s


# ── Datos reales de la corrida (corregidos) ─────────────────────────
MODELOS = [
    ("Regresión Ridge", 74.23, False),
    ("Regresión KNN", 79.95, False),
    ("Random Forest", 75.82, False),
    ("XGBoost", 75.17, True),
]
TOTAL_REG = 19_731_600
VALIDOS = 15_782_040
TRAIN = 11_573_496
TEST = 3_857_832

random.seed(42)
PUNTOS = []
for _ in range(150):
    x = random.uniform(0, 500)
    y = 0.78 * x + 37.90 + random.gauss(0, 55)
    PUNTOS.append((x, max(0.0, y)))
SENTINELAS = sorted(random.sample(range(16 * 8), 26))


# ── Dibujos por zona ────────────────────────────────────────────────
def cabecera(c, t):
    p = suave(t / 0.35)
    dy = int((1 - p) * -12)
    c.rect((0, 0, 1280, 92 + dy), fill=SLATE)
    c.rect((0, 92 + dy, 1280, 95 + dy), fill=ORANGE)
    c.texto((24, 14 + dy), "UNIVERSIDAD CÉSAR VALLEJO  ·  SEDE LIMA ESTE",
            11.5, ORANGE2, bold=True)
    c.texto((24, 32 + dy), "Predicción de la precipitación mensual en el Perú",
            23, WHITE, bold=True)
    c.texto((24, 66 + dy),
            "Comparación de algoritmos de regresión de aprendizaje supervisado  ·  2026",
            11, (203, 213, 225))
    c.rrect((1092, 26 + dy, 1152, 66 + dy), 8, fill=SLATE2, outline=(71, 85, 105))
    c.texto((1122, 46 + dy), "UCV", 13, WHITE, bold=True, anchor="mm")
    c.rrect((1160, 26 + dy, 1256, 66 + dy), 8, fill=SLATE2, outline=(71, 85, 105))
    c.texto((1208, 46 + dy), "SENAMHI", 9.5, WHITE, bold=True, anchor="mm")


def flechas(c, t):
    if t < 0.35:
        return
    for x in (310, 629, 948):
        c.linea((x, 334, x + 18, 334), fill=(203, 213, 225), w=2)
        c.d.line([(x + 18 * c.s, 329 * c.s), (x + 25 * c.s, 334 * c.s),
                  (x + 18 * c.s, 339 * c.s)], fill=ORANGE2, width=int(2 * c.s),
                 joint="curve")
        for i in range(3):
            fase = ((t * 0.55) + i / 3.0) % 1.0
            cx = x + 2 + fase * 18
            c.circ((cx - 2.6, 331.4, cx + 2.6, 336.6), fill=ORANGE)


def tarjeta(c, x, num, titulo, dy):
    if dy > 0:
        return
    c.rrect((x, 112, x + 291, 556), 12, fill=WHITE, outline=LINE, w=2)
    c.texto((x + 16, 124), num, 19, ORANGE, bold=True)
    c.texto((x + 52, 130), titulo, 10.5, SLATE, bold=True)
    c.linea((x + 16, 156, x + 275, 156), fill=LINE, w=2)


def zona_a(c, t, dy):
    if dy > 0:
        return
    x = 16
    p = suave((t - 0.45) / 0.55)
    if p <= 0:
        return
    tarjeta(c, x, "01", "RECOLECCIÓN DE DATOS", 0)
    c.rrect((x + 16, 172, x + 222, 200), 7, fill=ORANGE_SOFT)
    c.texto((x + 26, 179), "PISCOp v3.0  ·  SENAMHI", 10, ORANGE, bold=True)
    c.texto((x + 16, 214), "Periodo 1981–2025  ·  45 años", 10.5, SLATE2)
    c.texto((x + 16, 236), "540 meses consecutivos", 10.5, SLATE2)
    c.texto((x + 16, 258), "Malla 210 × 174 celdas  ·  0,1°", 10.5, SLATE2)
    c.texto((x + 16, 284), ent(TOTAL_REG, p), 21, SLATE, bold=True)
    c.texto((x + 16, 316), "registros celda-mes", 9.5, SLATE3)
    for i in range(16 * 8):
        fila, col = divmod(i, 16)
        gx, gy = x + 16 + col * 16, 344 + fila * 16
        tono = ORANGE_BAR if (i * 7) % 5 else ORANGE2
        c.rrect((gx, gy, gx + 11, gy + 11), 2, fill=tono)
    c.texto((x + 16, 500), "malla PISCOp de 0,1° (≈ 10 km)", 9.5, SLATE3)
    c.texto((x + 16, 518), "celdas recortadas al territorio peruano", 9.5, SLATE3)


def zona_b(c, t, dy):
    if dy > 0:
        return
    x = 335
    p = suave((t - 1.15) / 0.55)
    if p <= 0:
        return
    tarjeta(c, x, "02", "PREPROCESAMIENTO (ETL)", 0)
    c.texto((x + 16, 174), f"{ent(TOTAL_REG, 1)}   →   {ent(VALIDOS, p)}",
            12, SLATE, bold=True)
    c.texto((x + 16, 198), f"válidos ({dec(79.98, 2, p)} %)", 11, ORANGE, bold=True)
    pl = suave((t - 1.45) / 1.0)
    for i in range(16 * 8):
        fila, col = divmod(i, 16)
        gx, gy = x + 16 + col * 16, 228 + fila * 16
        if i in SENTINELAS:
            pos = SENTINELAS.index(i) / max(1, len(SENTINELAS) - 1)
            gris = pl > pos
            c.rrect((gx, gy, gx + 11, gy + 11), 2,
                    fill=LINE if gris else ORANGE_BAR)
        else:
            c.rrect((gx, gy, gx + 11, gy + 11), 2, fill=ORANGE_BAR)
    c.texto((x + 16, 366), "celdas grises = centinelas eliminados", 9.5, SLATE3)
    etiquetas = ["Limpieza de centinelas", "Variables D1 · D2 · D3",
                 f"Entrenamiento {ent(TRAIN, p)}", f"Prueba {ent(TEST, p)}"]
    for k, txt in enumerate(etiquetas):
        cy = 390 + k * 34
        c.rrect((x + 16, cy, x + 275, cy + 26), 7, fill=SOFT)
        c.texto((x + 145.5, cy + 13), txt, 9.8, SLATE2, bold=(k >= 2),
                anchor="mm")
    c.texto((x + 16, 534), "partición temporal 75 % / 25 %", 9.5, SLATE3)


def zona_c(c, t, dy):
    if dy > 0:
        return
    x = 654
    if t < 1.85:
        return
    tarjeta(c, x, "03", "MODELOS PREDICTIVOS", 0)
    c.texto((x + 16, 172), "RMSE de prueba (mm)  ·  menor es mejor", 9.5, SLATE3)
    for k, (nombre, rmse, ganador) in enumerate(MODELOS):
        y = 198 + k * 82
        pb = suave((t - 2.05 - k * 0.14) / 0.6)
        c.texto((x + 16, y), nombre, 10.8, SLATE, bold=True)
        c.texto((x + 275, y), f"{dec(rmse)} mm", 10.8,
                ORANGE if ganador else SLATE2, bold=True, anchor="ra")
        c.rrect((x + 16, y + 22, x + 275, y + 36), 7, fill=SOFT)
        ancho = (rmse / 90.0) * 259 * pb
        if ancho > 4:
            c.rrect((x + 16, y + 22, x + 16 + ancho, y + 36), 7,
                    fill=ORANGE if ganador else SLATE2)
        if ganador:
            pulso = 0.5 + 0.5 * math.sin((t - 3.2) * 2 * math.pi / 1.2)
            base = tuple(int(ORANGE[i] + (ORANGE2[i] - ORANGE[i]) * pulso * 0.7)
                         for i in range(3))
            c.rrect((x + 16, y + 44, x + 112, y + 66), 6, fill=base)
            c.texto((x + 64, y + 55), "GANADOR", 8.8, WHITE, bold=True,
                    anchor="mm")
            c.texto((x + 122, y + 55),
                    "MAE 48,26 mm  ·  R² 0,79", 9.2, SLATE2, anchor="lm")
        else:
            c.texto((x + 16, y + 50),
                    ["Regresión con penalización L2",
                     "Vecinos más cercanos (k = 7)",
                     "Bosque de 200 árboles"][k], 9, SLATE3)
    c.texto((x + 16, 534), "4 algoritmos de la tesis · semilla 42", 9.5, SLATE3)


def zona_d(c, t, dy):
    if dy > 0:
        return
    x = 973
    if t < 2.55:
        return
    tarjeta(c, x, "04", "RESULTADOS", 0)
    ax, ay, aw, ah = x + 16, 172, 259, 158
    c.rrect((ax, ay, ax + aw, ay + ah), 8, fill=WHITE, outline=LINE, w=2)

    def px(v):
        return ax + 14 + (v / 520.0) * (aw - 26)

    def py(v):
        return ay + ah - 14 - (v / 520.0) * (ah - 26)

    c.linea((ax + 14, py(0), ax + aw - 12, py(0)), fill=LINE, w=1)
    c.linea((ax + 14, py(0), ax + 14, ay + 12), fill=LINE, w=1)
    for k in range(1, 6):
        xx = ax + 14 + k * (aw - 26) / 6.0
        c.linea((xx, ay + 12, xx, py(0)), fill=(238, 242, 247), w=1)
    vis = int(len(PUNTOS) * suave((t - 2.8) / 1.2))
    for (ox, oy) in PUNTOS[:vis]:
        c.circ((px(ox) - 1.8, py(oy) - 1.8, px(ox) + 1.8, py(oy) + 1.8),
               fill=ORANGE_BAR)
    pl = suave((t - 3.1) / 0.8)
    if pl > 0:
        c.linea((px(0), py(0), px(520 * pl), py(520 * pl)), fill=SLATE3, w=1)
        c.linea((px(0), py(37.90), px(520 * pl), py(0.78 * 520 * pl + 37.90)),
                fill=ORANGE, w=3)
    c.texto((ax + 8, ay + 6), "Predicho vs observado", 9.2, SLATE, bold=True)
    c.texto((x + 16, 338), "ŷ = 0,78·y + 37,90  ·  ref. y = x", 9.6, SLATE3)
    filas = [("MAE", "48,26 mm", "rel. vs persistencia 0,47"),
             ("RMSE", "75,17 mm", "rel. vs persistencia 0,50"),
             ("R²", "0,79", "coeficiente de determinación")]
    for k, (nom, val, rel) in enumerate(filas):
        y = 358 + k * 58
        c.rrect((x + 16, y, x + 275, y + 50), 8, fill=BG, outline=LINE, w=1)
        c.texto((x + 26, y + 8), f"{nom}  {val}", 10.4, SLATE, bold=True)
        c.texto((x + 26, y + 28), rel, 8.6, SLATE3)
        c.rrect((x + 186, y + 14, x + 267, y + 37), 6, fill=GREEN_SOFT)
        c.texto((x + 226.5, y + 25.5), "CUMPLE", 8.4, GREEN, bold=True,
                anchor="mm")
    c.texto((x + 16, 532), "3 de 3 umbrales de aceptación", 9.5, SLATE3)


def banner(c, t):
    if t < 3.25:
        return
    p = suave((t - 3.25) / 0.5)
    dy = int((1 - p) * 14)
    c.rrect((16, 568 + dy, 1264, 652 + dy), 12, fill=SLATE)
    c.texto((36, 582 + dy), "CONCLUSIONES", 10, ORANGE2, bold=True)
    textos = [("XGBoost superó a las líneas base de", "persistencia y climatología"),
              ("Los 4 algoritmos pasaron los", "umbrales de aceptación"),
              ("Proyección 2026 y análisis regional", "de 25 departamentos")]
    for k, (l1, l2) in enumerate(textos):
        bx = 36 + k * 412
        c.rrect((bx, 612 + dy, bx + 10, 622 + dy), 2, fill=ORANGE)
        c.texto((bx + 20, 603 + dy), l1, 10, (226, 232, 240))
        c.texto((bx + 20, 621 + dy), l2, 10, (226, 232, 240))


def pie(c, t):
    c.texto((640, 672),
            "Datos: PISCOp v3.0 (SENAMHI) · 1981–2025 · 15 782 040 registros válidos "
            "· Cifras de la corrida del experimento · Siglas institucionales sin logotipos de terceros",
            8.6, MUTED, anchor="ma")


# ── Ensamblado de un fotograma ──────────────────────────────────────
def fotograma(t, s=1):
    c = Lienzo(s=s)
    cabecera(c, t)
    flechas(c, t)

    def off(t0):
        p = suave((t - t0) / 0.45)
        return int((1 - p) * 26)

    zona_a(c, t, off(0.45))
    zona_b(c, t, off(1.15))
    zona_c(c, t, off(1.85))
    zona_d(c, t, off(2.55))
    banner(c, t)
    pie(c, t)
    return c.img


# ── Generación ──────────────────────────────────────────────────────
def main():
    os.makedirs(SALIDA, exist_ok=True)
    fps = 12
    segundos = 10
    fotogramas = []
    for i in range(fps * segundos):
        t = i / fps
        fotogramas.append(fotograma(t))
    ruta_gif = os.path.join(SALIDA, "infografia_animada.gif")
    fotogramas[0].save(ruta_gif, save_all=True, append_images=fotogramas[1:],
                       duration=int(1000 / fps), loop=0, optimize=True)
    ruta_png = os.path.join(SALIDA, "infografia_estatica.png")
    fotograma(4.6, s=2).save(ruta_png)
    print("GIF :", ruta_gif, f"({os.path.getsize(ruta_gif) / 1e6:.1f} MB)")
    print("PNG :", ruta_png, f"({os.path.getsize(ruta_png) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
