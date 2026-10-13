# -*- coding: utf-8 -*-
"""
Genera la GUÍA DE PALABRAS CLAVE (PDF) del proyecto Precipitación Perú OS:
términos que hay que saber explicar, utilidad del trabajo, resultados reales
y preparación para la exposición de tesis.

Uso:  python3 generar_guia_palabras_clave.py
Salida: ../guia_palabras_clave.pdf
"""
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether)

# ── identidad del proyecto ────────────────────────────────────────────────
NAVY  = colors.HexColor('#0B2545')
ORANGE= colors.HexColor('#D9600A')
TEXT  = colors.HexColor('#1E293B')
GRAY  = colors.HexColor('#475569')
LINE  = colors.HexColor('#CBD5E1')
BG    = colors.HexColor('#F1F5F9')
W, H = A4

S_TITLE = ParagraphStyle('t', fontName='Helvetica-Bold', fontSize=17, leading=21,
                         textColor=NAVY, spaceAfter=2)
S_SUB   = ParagraphStyle('s', fontName='Helvetica', fontSize=10, leading=14,
                         textColor=GRAY, spaceAfter=1)
S_META  = ParagraphStyle('m', fontName='Helvetica', fontSize=8.5, leading=12,
                         textColor=GRAY)
S_H2    = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=12.5, leading=15,
                         textColor=ORANGE, spaceBefore=13, spaceAfter=5)
S_H3    = ParagraphStyle('h3', fontName='Helvetica-Bold', fontSize=10.5, leading=13,
                         textColor=NAVY, spaceBefore=8, spaceAfter=3)
S_BODY  = ParagraphStyle('b', fontName='Helvetica', fontSize=10, leading=14.5,
                         textColor=TEXT, spaceAfter=5)
S_TERM  = ParagraphStyle('tm', fontName='Helvetica', fontSize=10, leading=14,
                         textColor=TEXT, spaceAfter=4, leftIndent=8)
S_BUL   = ParagraphStyle('bu', fontName='Helvetica', fontSize=10, leading=14,
                         textColor=TEXT, spaceAfter=3, leftIndent=12,
                         bulletIndent=2)
S_CELL  = ParagraphStyle('c', fontName='Helvetica', fontSize=9, leading=11.5,
                         textColor=TEXT)
S_CELLB = ParagraphStyle('cb', fontName='Helvetica-Bold', fontSize=9, leading=11.5,
                         textColor=colors.white)
S_NOTE  = ParagraphStyle('n', fontName='Helvetica-Oblique', fontSize=9, leading=12,
                         textColor=GRAY, spaceAfter=6)

def T(name, text):
    return Paragraph('<b>%s:</b> %s' % (name, text), S_TERM)

def B(text):
    return Paragraph(text, S_BUL, bulletText='•')

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE); canvas.setLineWidth(.5)
    canvas.line(18*mm, 13*mm, W-18*mm, 13*mm)
    canvas.setFont('Helvetica', 7.5); canvas.setFillColor(GRAY)
    canvas.drawString(18*mm, 9*mm,
        'Precipitación Perú OS · Comparación de algoritmos de regresión de aprendizaje supervisado '
        'para la predicción de la precipitación mensual en el Perú')
    canvas.drawRightString(W-18*mm, 9*mm, 'Página %d' % doc.page)
    canvas.restoreState()

def tabla(cells, widths, header=True):
    t = Table(cells, colWidths=widths, hAlign='LEFT')
    st = [('VALIGN', (0,0), (-1,-1), 'TOP'),
          ('GRID', (0,0), (-1,-1), .5, LINE),
          ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5),
          ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]
    if header:
        st += [('BACKGROUND', (0,0), (-1,0), NAVY)]
    st += [('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG])]
    t.setStyle(TableStyle(st))
    return t

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out  = os.path.join(here, '..', 'guia_palabras_clave.pdf')
    doc = SimpleDocTemplate(out, pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=18*mm,
                            title='Guía de palabras clave · Precipitación Perú OS',
                            author='Atahualpa Palomino, Kevin Anthony')
    E = []
    # ── cabecera ──────────────────────────────────────────────────────────
    E.append(Paragraph('GUÍA DE PALABRAS CLAVE', S_TITLE))
    E.append(Paragraph('Qué tienes que explicar, qué significa cada término y para qué sirve todo',
                       S_SUB))
    E.append(Spacer(1, 4))
    E.append(HRFlowable(width='100%', thickness=1.4, color=ORANGE, spaceAfter=6))
    E.append(Paragraph(
        'Tesis: <b>Comparación de algoritmos de regresión de aprendizaje supervisado para la '
        'predicción de la precipitación mensual en el Perú</b><br/>'
        'Autor: Atahualpa Palomino, Kevin Anthony · Asesor: Mg. Flores Chacon, Erick Giovanny<br/>'
        'Universidad César Vallejo · Sede Lima Este · Línea: Sistemas de Información y '
        'Comunicaciones · Año académico 2026', S_META))
    E.append(Spacer(1, 8))

    # ── 1 · la tesis en 30 segundos ──────────────────────────────────────
    E.append(Paragraph('1 · La tesis en 30 segundos', S_H2))
    E.append(Paragraph(
        'Se compararon <b>cuatro algoritmos de regresión de aprendizaje supervisado</b> '
        '(Regresión Ridge, Regresión KNN, Random Forest y XGBoost) para predecir la '
        '<b>precipitación mensual</b> en cada celda del territorio peruano, usando el dataset '
        '<b>PISCOp v3.0</b> del SENAMHI (540 meses: 1981-2025). Todos los modelos superaron los '
        'criterios de aceptación y el ganador fue <b>Regresión Ridge</b> (RMSE 74,23 mm · '
        'R² 0,80), elegido por tener el menor RMSE y el mayor R². El resultado se entrega en un '
        'prototipo web con forma de sistema operativo científico: <b>Precipitación Perú OS</b>.',
        S_BODY))

    # ── 2 · el flujo en 5 pasos ─────────────────────────────────────────
    E.append(Paragraph('2 · El flujo del trabajo en 5 pasos', S_H2))
    pasos = [[Paragraph('PASO', S_CELLB), Paragraph('QUÉ SE HIZO', S_CELLB),
              Paragraph('CIFRA CLAVE', S_CELLB)],
             [Paragraph('<b>1 · Recolección</b>', S_CELL),
              Paragraph('Dataset PISCOp v3.0 (SENAMHI): 540 meses × 210 × 174 celdas de 0,1°.', S_CELL),
              Paragraph('19 731 600 celda-mes', S_CELL)],
             [Paragraph('<b>2 · Limpieza (ETL)</b>', S_CELL),
              Paragraph('Eliminación de centinelas (valores sin dato).', S_CELL),
              Paragraph('15 782 040 válidos (79,98 %)', S_CELL)],
             [Paragraph('<b>3 · Variables</b>', S_CELL),
              Paragraph('D1 = objetivo · D2 = estadísticos climatológicos · D3 = rezagos.', S_CELL),
              Paragraph('k = 1, 2, 3, 12', S_CELL)],
             [Paragraph('<b>4 · Partición</b>', S_CELL),
              Paragraph('Entrenamiento y prueba separados y fijos para los 4 modelos.', S_CELL),
              Paragraph('11 573 496 train · 3 857 832 test', S_CELL)],
             [Paragraph('<b>5 · Modelos</b>', S_CELL),
              Paragraph('Regresión Ridge · Regresión KNN · Random Forest · XGBoost (semilla 42).', S_CELL),
              Paragraph('4 algoritmos', S_CELL)],
             [Paragraph('<b>6 · Evaluación</b>', S_CELL),
              Paragraph('MAE, RMSE, R² y métricas relativas frente a la línea base de persistencia.', S_CELL),
              Paragraph('3 de 3 umbrales cumplidos', S_CELL)],
             [Paragraph('<b>7 · Aplicación</b>', S_CELL),
              Paragraph('Proyección 2026 y análisis regional de los 25 departamentos.', S_CELL),
              Paragraph('media anual 184,54 mm/mes', S_CELL)]]
    E.append(tabla(pasos, [26*mm, 100*mm, 38*mm]))

    # ── 3 · palabras clave ──────────────────────────────────────────────
    E.append(Paragraph('3 · Palabras clave que debes poder explicar', S_H2))

    E.append(Paragraph('Fundamentos de aprendizaje supervisado', S_H3))
    E.append(T('Aprendizaje supervisado',
        'El modelo aprende de ejemplos ya resueltos: se le dan las entradas y la respuesta '
        'correcta (la lluvia real) y él encuentra el patrón para predecir casos nuevos.'))
    E.append(T('Regresión',
        'Tipo de problema donde lo que se predice es un número continuo (milímetros de lluvia), '
        'no una categoría. Por eso se usan algoritmos de regresión y no de clasificación.'))
    E.append(T('Variable objetivo (D1)',
        'Lo que queremos predecir: P(c,t), la precipitación de la celda c en el mes t.'))
    E.append(T('Características o entradas (features)',
        'Los datos con los que el modelo adivina: estadísticos climatológicos (D2) y rezagos (D3).'))
    E.append(T('Conjunto de entrenamiento y de prueba',
        'El entrenamiento (11 573 496 registros) sirve para aprender; el de prueba '
        '(3 857 832 registros) se guarda aparte para medir si el modelo acierta en datos que '
        'nunca vio. Si se mezclan, la evaluación es falsa.'))
    E.append(T('Semilla 42',
        'Valor fijo que hace reproducible todo lo aleatorio del experimento (submuestras, '
        'bosques). Con la misma semilla, cualquiera obtiene los mismos números.'))
    E.append(T('Sobreajuste (overfitting)',
        'Cuando el modelo memoriza el entrenamiento y falla en datos nuevos. Su opuesto, el '
        'subajuste, es quedarse corto y no capturar el patrón. La regularización existe para '
        'evitar el sobreajuste.'))
    E.append(T('Hiperparámetro',
        'Configuración que se elige antes de entrenar (por ejemplo la k del KNN). No se aprende '
        'de los datos: se decide en el experimento.'))

    E.append(Paragraph('Los datos', S_H3))
    E.append(T('PISCOp v3.0 (SENAMHI)',
        'Producto de precipitación del Servicio Nacional de Meteorología e Hidrología del Perú '
        'que combina observaciones de estaciones con datos satelitales. Cubre 1981-2025.'))
    E.append(T('Malla o grilla de 0,1°',
        'El país dividido en 210 × 174 celdas cuadradas de 0,1° (unos 10 km de lado). Cada celda '
        'tiene su propia serie de lluvia mensual.'))
    E.append(T('Celda-mes',
        'Una celda en un mes concreto: la unidad básica del dataset. En total 19 731 600; tras la '
        'limpieza quedan 15 782 040 válidos (79,98 %).'))
    E.append(T('Centinela',
        'Valor de relleno que significa "aquí no hay dato". No es un cero de lluvia: se elimina '
        'en el preprocesamiento para no ensuciar el aprendizaje.'))
    E.append(T('D2 · estadísticos climatológicos',
        'Para cada celda y cada mes del calendario: la media histórica μ(c,m), la desviación '
        'estándar σ(c,m) con corrección N−1 y la media total P̄(c). Le dan al modelo el "clima '
        'normal" de cada lugar.'))
    E.append(T('D3 · rezagos (lags)',
        'La lluvia de meses anteriores como entrada: k = 1, 2, 3 y 12 (el mes pasado, hace dos, '
        'hace tres y hace un año). La precipitación tiene memoria y estacionalidad.'))
    E.append(T('Rango de los datos',
        'Precipitación mensual de 0,00 a 6 153,58 mm. Los valores extremos son justo lo que más '
        'cuesta predecir.'))

    E.append(Paragraph('Los cuatro algoritmos', S_H3))
    alg = [[Paragraph('ALGORITMO', S_CELLB), Paragraph('QUÉ ES EN UNA FRASE', S_CELLB),
            Paragraph('DATO DEL EXPERIMENTO', S_CELLB)],
           [Paragraph('<b>Regresión Ridge</b><br/>GANADOR', S_CELL),
            Paragraph('Regresión lineal con regularización L2: castiga los coeficientes muy '
                      'grandes para que el modelo no se sobreajuste. Simple, rápido y estable '
                      'aunque las variables estén correlacionadas.', S_CELL),
            Paragraph('MAE 48,29 · RMSE 74,23 · R² 0,80 · 1 500 000 obs.', S_CELL)],
           [Paragraph('<b>Regresión KNN</b>', S_CELL),
            Paragraph('K vecinos más cercanos: para predecir busca los k registros parecidos al '
                      'caso nuevo y promedia sus lluvias reales (k = 7). No asume ninguna forma '
                      'matemática, pero es costoso con millones de datos.', S_CELL),
            Paragraph('MAE 51,81 · RMSE 79,95 · R² 0,77 · 300 000 obs.', S_CELL)],
           [Paragraph('<b>Random Forest</b>', S_CELL),
            Paragraph('Bosque aleatorio: muchos árboles de decisión entrenados con muestras '
                      'diferentes; la predicción es el promedio de todos. Robusto ante ruido y '
                      'relaciones no lineales.', S_CELL),
            Paragraph('MAE 48,87 · RMSE 75,82 · R² 0,79 · 300 000 obs.', S_CELL)],
           [Paragraph('<b>XGBoost</b>', S_CELL),
            Paragraph('Impulso de gradiente (gradient boosting): árboles que se entrenan en '
                      'secuencia, cada uno corrigiendo los errores del anterior. Muy potente '
                      'con datos tabulares.', S_CELL),
            Paragraph('MAE 48,26 · RMSE 75,17 · R² 0,79 · 300 000 obs.', S_CELL)]]
    E.append(tabla(alg, [30*mm, 82*mm, 52*mm]))
    E.append(Paragraph('Submuestra técnica: por el costo computacional de trabajar sobre millones '
                       'de observaciones, Regresión KNN, Random Forest y XGBoost se entrenaron '
                       'con 300 000 observaciones extraídas aleatoriamente del conjunto de '
                       'entrenamiento con semilla fija (42); esta limitación se documenta en la '
                       'interpretación de los resultados. Regresión Ridge, al ser lineal, procesó '
                       '1 500 000 observaciones.', S_NOTE))

    E.append(Paragraph('Las métricas (cómo se mide el desempeño)', S_H3))
    E.append(T('MAE · error absoluto medio',
        'En promedio, cuántos milímetros se equivoca el modelo. Fácil de explicar: "se equivoca '
        'como media unos 48 mm".'))
    E.append(T('RMSE · raíz del error cuadrático medio',
        'Parecido al MAE pero castiga mucho más los errores grandes. Es la métrica clave cuando '
        'los extremos importan (inundaciones, sequías).'))
    E.append(T('R² · coeficiente de determinación',
        'Qué proporción de la variabilidad de la lluvia explica el modelo (1,00 = perfecto; '
        '0,80 = explica el 80 %).'))
    E.append(T('Métricas relativas (rel. MAE y rel. RMSE)',
        'El error del modelo dividido por el de la línea base de persistencia. El ganador obtuvo '
        '0,47 y 0,49, es decir, reduce el error un 53 % (MAE) y un 51 % (RMSE) frente a esa base.'))
    E.append(T('Línea base de persistencia',
        'La predicción más simple posible: asumir que el mes siguiente lloverá como el mes '
        'pasado. También se comparó con la climatología (predecir siempre el valor medio de cada '
        'celda). Todo modelo debe superar a estas bases para tener valor práctico.'))
    E.append(T('Criterios de aceptación',
        'Los tres umbrales definidos en la metodología: rel. MAE menor que 0,90 · rel. RMSE '
        'menor que 0,90 · R² mayor o igual que 0,75 (nivel excelente). Los cuatro algoritmos '
        'cumplieron 3 de 3.'))

    # ── 4 · resultados y cómo explicarlos ────────────────────────────────
    E.append(Paragraph('4 · Los resultados y cómo explicarlos', S_H2))
    res = [[Paragraph('MODELO', S_CELLB), Paragraph('OBS. ENTREN.', S_CELLB),
            Paragraph('MAE (mm)', S_CELLB), Paragraph('RMSE (mm)', S_CELLB),
            Paragraph('R²', S_CELLB), Paragraph('REL. MAE', S_CELLB),
            Paragraph('REL. RMSE', S_CELLB), Paragraph('ESTADO', S_CELLB)],
           [Paragraph('<b>Regresión Ridge</b>', S_CELL), Paragraph('1 500 000', S_CELL),
            Paragraph('48,29', S_CELL), Paragraph('<b>74,23</b>', S_CELL),
            Paragraph('<b>0,80</b>', S_CELL), Paragraph('0,47', S_CELL),
            Paragraph('0,49', S_CELL), Paragraph('GANADOR', S_CELL)],
           [Paragraph('XGBoost', S_CELL), Paragraph('300 000', S_CELL),
            Paragraph('<b>48,26</b>', S_CELL), Paragraph('75,17', S_CELL),
            Paragraph('0,79', S_CELL), Paragraph('0,47', S_CELL),
            Paragraph('0,50', S_CELL), Paragraph('CUMPLE', S_CELL)],
           [Paragraph('Random Forest', S_CELL), Paragraph('300 000', S_CELL),
            Paragraph('48,87', S_CELL), Paragraph('75,82', S_CELL),
            Paragraph('0,79', S_CELL), Paragraph('0,48', S_CELL),
            Paragraph('0,50', S_CELL), Paragraph('CUMPLE', S_CELL)],
           [Paragraph('Regresión KNN', S_CELL), Paragraph('300 000', S_CELL),
            Paragraph('51,81', S_CELL), Paragraph('79,95', S_CELL),
            Paragraph('0,77', S_CELL), Paragraph('0,51', S_CELL),
            Paragraph('0,53', S_CELL), Paragraph('CUMPLE', S_CELL)]]
    E.append(tabla(res, [30*mm, 20*mm, 17*mm, 19*mm, 12*mm, 17*mm, 19*mm, 18*mm]))
    E.append(Paragraph('Métricas del modelo ganador verificadas: MAE 48,29 · RMSE 74,23 · '
                       'R² 0,80 · rel. MAE 0,47 · rel. RMSE 0,49.', S_NOTE))

    E.append(Paragraph('Cómo defender la elección de Regresión Ridge', S_H3))
    E.append(B('El criterio de selección fue <b>menor RMSE y mayor R²</b>: Ridge tiene el RMSE '
               'más bajo (74,23 frente a 75,17 de XGBoost) y el R² más alto (0,80 frente a 0,79).'))
    E.append(B('XGBoost sí tiene el MAE más bajo (48,26), pero solo por <b>0,03 mm</b> sobre '
               'Ridge (48,29): una diferencia prácticamente nula, dentro del ruido del experimento.'))
    E.append(B('El RMSE penaliza los errores grandes, y en precipitación los errores grandes son '
               'los meses extremos: por eso pesa más que el MAE en la decisión.'))
    E.append(B('Ridge además es más simple, más rápido de entrenar y de interpretar, y trabajó '
               'con más datos (1 500 000 observaciones). Entre dos modelos casi iguales, se '
               'elige el más simple: menos riesgo de sobreajuste.'))
    E.append(B('Los cuatro modelos cumplieron los 3 criterios de aceptación: la comparación no '
               'busca "malos y buenos", sino el mejor equilibrio.'))

    # ── 5 · utilidad ─────────────────────────────────────────────────────
    E.append(Paragraph('5 · La utilidad: para qué sirve todo esto', S_H2))
    E.append(T('Gestión del agua',
        'Estimar con antelación la lluvia de cada mes ayuda a planificar reservas para consumo '
        'urbano, riego y generación hidroeléctrica.'))
    E.append(T('Agricultura',
        'Permite decidir cuándo sembrar y cosechar según la lluvia esperada en cada región, '
        'reduciendo pérdidas por sequías o excesos de agua.'))
    E.append(T('Riesgo hidrológico',
        'Anticipar meses muy lluviosos o muy secos apoya la prevención de inundaciones, '
        'deslizamientos y sequías, y el seguimiento de fenómenos como El Niño.'))
    E.append(T('Planeamiento regional',
        'El ranking departamental permite priorizar recursos: Loreto 244,96 · Madre de Dios '
        '214,66 · Pasco 209,16 · Ucayali 191,37 · Amazonas 186,45 mm/mes.'))
    E.append(T('Proyección operativa',
        'La proyección 2026 entrega los 12 meses del año (media anual 184,54 mm/mes), generada '
        'de forma recursiva con el modelo ganador y recortada a valores no negativos.'))
    E.append(T('Ciencia reproducible',
        'Datos oficiales del SENAMHI, semilla fija, metodología documentada y prototipo '
        'publicado: cualquiera puede verificar y repetir el experimento.'))

    # ── 6 · qué explicar en la exposición ────────────────────────────────
    E.append(Paragraph('6 · Qué explicar en la exposición (guion de 5 minutos)', S_H2))
    E.append(B('<b>1 · El problema (30 s):</b> predecir la lluvia mensual en el Perú importa '
               'para el agua, la agricultura y la prevención de desastres.'))
    E.append(B('<b>2 · Los datos (45 s):</b> PISCOp v3.0 del SENAMHI, 540 meses (1981-2025), '
               'malla de 0,1°, 15 782 040 registros válidos (79,98 %).'))
    E.append(B('<b>3 · La comparación (60 s):</b> cuatro algoritmos de regresión supervisada, '
               'las mismas particiones de entrenamiento y prueba, semilla 42.'))
    E.append(B('<b>4 · Los resultados (90 s):</b> los cuatro cumplen los criterios; gana '
               'Regresión Ridge por el menor RMSE (74,23) y el mayor R² (0,80).'))
    E.append(B('<b>5 · La aplicación (60 s):</b> proyección 2026, análisis de los 25 '
               'departamentos y el prototipo Precipitación Perú OS publicado en la web.'))
    E.append(B('<b>6 · Cierre (15 s):</b> el trabajo es reproducible y está disponible en '
               'internet para consulta.'))

    # ── 7 · preguntas probables ──────────────────────────────────────────
    E.append(Paragraph('7 · Preguntas probables del jurado (y cómo responderlas)', S_H2))
    qa = [
        ('¿Por qué gana Ridge si XGBoost tiene el MAE más bajo?',
         'Porque la selección se definió por menor RMSE y mayor R². XGBoost solo gana el MAE por '
         '0,03 mm (48,26 frente a 48,29), una diferencia despreciable, mientras que Ridge tiene '
         'mejor RMSE (74,23 frente a 75,17) y mejor R² (0,80 frente a 0,79).'),
        ('¿Qué es la regularización L2 (la base de Ridge)?',
         'Un castigo matemático a los coeficientes muy grandes del modelo lineal. Evita que el '
         'modelo se ajuste en exceso al ruido de los datos de entrenamiento (sobreajuste).'),
        ('¿Por qué KNN con k = 7?',
         'El valor de k se fijó durante la fase de validación del experimento. La k define '
         'cuántos vecinos se promedian: k pequeña se ajusta mucho al ruido, k grande pierde '
         'detalle local.'),
        ('¿Por qué algunos algoritmos usaron 300 000 registros y Ridge 1 500 000?',
         'Por costo computacional: buscar vecinos o entrenar ensambles sobre los 11 573 496 '
         'registros de entrenamiento es muy demandante, por eso se usó una submuestra técnica '
         'de 300 000 observaciones con semilla fija, igual para los tres. Es una limitación '
         'documentada en la interpretación de resultados.'),
        ('¿Qué significa el R² de 0,80?',
         'Que el modelo explica el 80 % de la variabilidad de la precipitación mensual en los '
         'datos de prueba que nunca había visto.'),
        ('¿Para qué sirven los rezagos?',
         'La lluvia de un mes se parece a la de los meses anteriores. Los rezagos k = 1, 2, 3 y 12 '
         'aportan esa memoria (incluido el ciclo anual) como entradas del modelo.'),
        ('¿Qué es la línea base de persistencia?',
         'Predecir asumiendo que lloverá como el mes anterior. Es la referencia mínima: nuestro '
         'modelo logra 0,47 y 0,49 en métricas relativas, es decir, reduce el error más de la '
         'mitad frente a esa base.'),
        ('¿De dónde salen los datos y son confiables?',
         'Del PISCOp v3.0, producto oficial del SENAMHI (1981-2025), que combina estaciones y '
         'satélites. Es la fuente de referencia para precipitación en el Perú.'),
        ('¿Qué aporta el prototipo web?',
         'Hace accesible la investigación: cualquiera puede recorrer los datos, las métricas, los '
         'resultados, el flujo metodológico y la proyección 2026 desde cualquier dispositivo, '
         'sin instalar nada.'),
    ]
    for q, a in qa:
        E.append(KeepTogether([Paragraph('<b>%s</b>' % q, S_H3),
                               Paragraph(a, S_BODY)]))

    E.append(Spacer(1, 6))
    E.append(HRFlowable(width='100%', thickness=1, color=ORANGE, spaceAfter=5))
    E.append(Paragraph('Documento de apoyo para la exposición · Tesis: Comparación de algoritmos '
                       'de regresión de aprendizaje supervisado para la predicción de la '
                       'precipitación mensual en el Perú · Atahualpa Palomino, Kevin Anthony · '
                       'Universidad César Vallejo, Sede Lima Este · 2026', S_META))

    doc.build(E, onFirstPage=footer, onLaterPages=footer)
    print('PDF generado:', os.path.abspath(out))

if __name__ == '__main__':
    main()
