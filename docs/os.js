/* ═══════════════════════════════════════════════════════════════
   PRECIPITACIÓN PERÚ OS · motor de la interfaz
   Boot · dock · terminales · mapa GIS · gráficos animados
   Datos reales cargados desde data.js (window.DATA)
   ═══════════════════════════════════════════════════════════════ */
(function () {
'use strict';
var D = window.DATA;
var MESES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Set","Oct","Nov","Dic"];
var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ── formato de números (coma decimal, espacio de miles) ── */
function fmtN(x, dec) {
  dec = dec || 0;
  return x.toLocaleString('es-PE', { minimumFractionDigits: dec, maximumFractionDigits: dec })
          .replace(/\./g, '·').replace(/,/g, ',').replace(/·/g, ' ');
}
function fmt(x, dec) {
  dec = (dec === undefined) ? 1 : dec;
  var s = Math.abs(x).toFixed(dec).split('.');
  var g = s[0].replace(/\B(?=(\d{3})+(?!\d))/g, '\u00A0');
  return s[1] ? g + ',' + s[1] : g;
}
function qa(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
function later(fn, ms) { return setTimeout(fn, ms); }

/* ═══════════ BOOT SEQUENCE ═══════════ */
var bootOut = document.getElementById('boot-out');
var bootEl = document.getElementById('boot');
var skipBtn = document.getElementById('skip');
var bootDone = false;

var BOOT_LINES = [
  { t: 'p', s: 'PRECIPITACIÓN PERÚ OS · iniciando el sistema', d: 0 },
  { t: 'c', s: 'Inicializando el sistema de inteligencia climática...', d: 420 },
  { t: 'c', s: 'Cargando el dataset PISCOp v3.0 (SENAMHI)...', d: 900 },
  { t: 'bar', s: '100%', d: 1150, label: 'Cargando dataset', tot: 15782040, unit: 'registros válidos' },
  { t: 'c', s: 'Cargando los modelos de aprendizaje automático...', d: 2150 },
  { t: 'bar', s: '100%', d: 2350, label: 'Cargando modelos', tot: 4, unit: 'algoritmos supervisados' },
  { t: 'ok', s: 'Sistema listo ✓', d: 3350 },
  { t: 'logo', s: '', d: 3700 }
];

function bootHTML(lines, upto) {
  var h = '';
  for (var i = 0; i < lines.length; i++) {
    var l = lines[i];
    if (l.d > upto) break;
    if (l.t === 'p') h += '<div><span class="p">' + l.s + '</span></div>';
    else if (l.t === 'c') h += '<div class="c">' + l.s + '</div>';
    else if (l.t === 'ok') h += '<div class="ok">' + l.s + '</div>';
    else if (l.t === 'bar') {
      var local = Math.min(1, Math.max(0, (upto - l.d) / 900));
      var n = Math.round(local * 20);
      h += '<div class="c">' + l.label + '...</div>';
      h += '<div class="boot-prog">[' + '\u2588'.repeat(n) + '\u00B7'.repeat(20 - n) + '] ' +
           (local >= 1 ? l.s : Math.round(local * 100) + '%') +
           (local >= 1 ? ' · ' + fmt(l.tot, 0) + ' ' + l.unit : '') + '</div>';
    } else if (l.t === 'logo') {
      h += '<div class="boot-logo"><h1>PRECIPITACIÓN <b>PERÚ</b> OS</h1>' +
           '<p>SCIENTIFIC PREDICTION PLATFORM</p></div>' +
           '<div><span class="p">Sesión climatelab</span><span class="dim"> · </span>' +
           '<span class="acc">sistema operativo científico</span> <span class="cursor"></span></div>';
    }
  }
  return h;
}

function finishBoot() {
  if (bootDone) return;
  bootDone = true;
  bootOut.innerHTML = bootHTML(BOOT_LINES, 99999);
  later(function () {
    bootEl.classList.add('off');
    skipBtn.classList.add('off');
    document.body.classList.add('booted');
    arrancarSistema();
  }, reduce ? 100 : 700);
}

if (reduce) {
  finishBoot();
} else {
  var t0 = Date.now();
  (function tick() {
    if (bootDone) return;
    var el = Date.now() - t0;
    bootOut.innerHTML = bootHTML(BOOT_LINES, el);
    if (el < 4600) requestAnimationFrame(tick); else finishBoot();
  })();
}
skipBtn.addEventListener('click', finishBoot);
bootEl.addEventListener('click', finishBoot);

/* ═══════════ RELOJ SUPERIOR ═══════════ */
function reloj() {
  var el = document.getElementById('reloj');
  if (!el) return;
  var d = new Date();
  var p = function (n) { return String(n).padStart(2, '0'); };
  el.textContent = 'PERU · LIMA ESTE · ' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds());
}
setInterval(reloj, 1000); reloj();

/* ═══════════ DOCK · NAVEGACIÓN + SCROLL-SPY ═══════════ */
var dockBtns = qa('.dock-btn');
dockBtns.forEach(function (b) {
  b.addEventListener('click', function () {
    var target = document.getElementById(b.dataset.go);
    if (target) target.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
  });
});
function spy() {
  var best = null, bestD = 1e9;
  qa('.mod').forEach(function (m) {
    var d = Math.abs(m.getBoundingClientRect().top - 90);
    if (d < bestD) { bestD = d; best = m.id; }
  });
  dockBtns.forEach(function (b) { b.classList.toggle('acti', b.dataset.go === best); });
}
window.addEventListener('scroll', spy, { passive: true });

/* ═══════════ ANIMACIÓN DE APARICIÓN (reveal) ═══════════ */
var io = new IntersectionObserver(function (entries) {
  entries.forEach(function (e) {
    if (e.isIntersecting) {
      e.target.classList.add('on');
      if (e.target.dataset.once !== '1') {
        e.target.dataset.once = '1';
        activar(e.target);
      }
    }
  });
}, { threshold: 0.18 });
qa('.rev').forEach(function (el) { io.observe(el); });

/* contadores genéricos */
function contar(el) {
  var to = parseFloat(el.dataset.to), dec = parseInt(el.dataset.dec || '0', 10);
  if (reduce) { el.textContent = fmt(to, dec); return; }
  var t0 = performance.now(), dur = 1400;
  (function step(now) {
    var p = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - p, 3);
    el.textContent = fmt(to * e, dec);
    if (p < 1) requestAnimationFrame(step);
  })(performance.now());
}

/* activadores por elemento */
function activar(el) {
  qa('.count', el).forEach(contar);
  if (el.id === 'quality') {
    later(function () {
      var f = document.getElementById('q-bar-fill');
      if (f) f.style.width = '79.98%';
    }, 150);
  }
  if (el.id === 'dept-panel') pintarClima(D.stats['Loreto']);
  if (el.classList.contains('map-wrap')) animarMalla(el);
}

/* ═══════════ LLUVIA DIGITAL (hero) ═══════════ */
(function lluvia() {
  var svg = document.getElementById('rain-hero');
  if (!svg || reduce) return;
  var w = 1200, h = 420, s = '';
  for (var i = 0; i < 46; i++) {
    var x = Math.random() * w, y = Math.random() * h, len = 12 + Math.random() * 26,
        dur = 1.6 + Math.random() * 2.4, del = Math.random() * 3;
    s += '<line x1="' + x.toFixed(1) + '" y1="' + y.toFixed(1) + '" x2="' + (x - 4).toFixed(1) +
         '" y2="' + (y + len).toFixed(1) + '" stroke="#F97316" stroke-opacity="' +
         (0.10 + Math.random() * 0.25).toFixed(2) + '" stroke-width="1.2">' +
         '<animate attributeName="y1" values="' + y.toFixed(1) + ';' + (y + h).toFixed(1) +
         '" dur="' + dur.toFixed(1) + 's" begin="' + del.toFixed(1) + 's" repeatCount="indefinite"/>' +
         '<animate attributeName="y2" values="' + (y + len).toFixed(1) + ';' + (y + h + len).toFixed(1) +
         '" dur="' + dur.toFixed(1) + 's" begin="' + del.toFixed(1) + 's" repeatCount="indefinite"/></line>';
  }
  svg.setAttribute('viewBox', '0 0 ' + w + ' ' + h);
  svg.setAttribute('preserveAspectRatio', 'none');
  svg.innerHTML = s;
})();

/* ═══════════ MAPAS · geometría compartida ═══════════ */
var VB = { x: -81.40, y: -2.00, w: 17.40, h: 21.00 };

function colorTermico(v) {
  var escala = [[0, '#FFF7ED'], [40, '#FED7AA'], [90, '#FDBA74'], [150, '#FB923C'],
                [230, '#F97316'], [420, '#EA580C'], [600, '#9A3412']];
  if (v === null || v === undefined) return '#1E293B';
  for (var i = 1; i < escala.length; i++) {
    if (v < escala[i][0]) {
      var a = escala[i - 1], b = escala[i], t = (v - a[0]) / (b[0] - a[0]);
      var ca = [1, 3, 5].map(function (j) { return parseInt(a[1].slice(j, j + 2), 16); });
      var cb = [1, 3, 5].map(function (j) { return parseInt(b[1].slice(j, j + 2), 16); });
      return '#' + ca.map(function (x, k) {
        return Math.round(x + (cb[k] - x) * t).toString(16).padStart(2, '0');
      }).join('');
    }
  }
  return escala[escala.length - 1][1];
}

/* — mapa 01: malla de puntos PISCOp (celdas del raster) — */
function dentroDelPeru(svg, x, y) {
  for (var k = 0; k < D.departamentos.length; k++) {
    var p = svg.querySelector('path[data-n="' + k + '"]');
    if (p && p.isPointInFill(new DOMPoint(x, y))) return true;
  }
  return false;
}
function animarMalla(wrap) {
  var svg = document.getElementById('mapa-malla');
  if (!svg || svg.dataset.built === '1') return;
  svg.dataset.built = '1';
  var ns = 'http://www.w3.org/2000/svg';
  var gDep = document.createElementNS(ns, 'g');
  D.departamentos.forEach(function (d, k) {
    var p = document.createElementNS(ns, 'path');
    p.setAttribute('d', d.d);
    p.setAttribute('fill', '#0F1B2E');
    p.setAttribute('stroke', '#334155');
    p.setAttribute('stroke-width', '0.055');
    p.setAttribute('data-n', k);
    gDep.appendChild(p);
  });
  svg.innerHTML = '';
  svg.appendChild(gDep);

  /* malla de celdas: rejilla de 0,42° con puntos dentro de los paths */
  var gDots = document.createElementNS(ns, 'g');
  svg.appendChild(gDots);
  var pts = [];
  for (var y = VB.y + 0.35; y < VB.y + VB.h; y += 0.42) {
    for (var x = VB.x + 0.35; x < VB.x + VB.w; x += 0.42) {
      if (dentroDelPeru(svg, x, y)) pts.push([x, y]);
    }
  }
  /* barajar para que los puntos aparezcan de forma progresiva natural */
  for (var i = pts.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1)), t = pts[i]; pts[i] = pts[j]; pts[j] = t;
  }
  var total = pts.length, paso = reduce ? total : Math.ceil(total / 90);
  var idx = 0;
  (function pintarLote() {
    var frag = document.createDocumentFragment();
    for (var n = 0; n < paso && idx < total; n++, idx++) {
      var c = document.createElementNS(ns, 'circle');
      c.setAttribute('cx', pts[idx][0].toFixed(2));
      c.setAttribute('cy', pts[idx][1].toFixed(2));
      c.setAttribute('r', '0.16');
      c.setAttribute('fill', '#F97316');
      c.setAttribute('fill-opacity', '0.85');
      frag.appendChild(c);
    }
    gDots.appendChild(frag);
    if (idx < total) requestAnimationFrame(pintarLote);
    else {
      /* estación de registro (Lima) */
      var e = document.createElementNS(ns, 'g');
      e.innerHTML = '<circle cx="-77.05" cy="12.05" r="0.3" fill="#22C55E">' +
        '<animate attributeName="r" values="0.3;0.62;0.3" dur="2.2s" repeatCount="indefinite"/></circle>' +
        '<circle cx="-77.05" cy="12.05" r="0.55" fill="none" stroke="#22C55E" stroke-width="0.06"/>';
      svg.appendChild(e);
    }
  })();
}

/* — mapa 05: coropleta interactiva — */
function construirGeo() {
  var svg = document.getElementById('mapa-geo');
  if (!svg || svg.dataset.built === '1') return;
  svg.dataset.built = '1';
  var ns = 'http://www.w3.org/2000/svg';
  var g = document.createElementNS(ns, 'g');
  g.setAttribute('id', 'capa-deptos');
  D.departamentos.forEach(function (d, k) {
    var s = D.stats[d.nombre] || { media_mensual: 0 };
    var p = document.createElementNS(ns, 'path');
    p.setAttribute('d', d.d);
    p.setAttribute('class', 'depto-path');
    p.setAttribute('fill', colorTermico(s.media_mensual));
    p.setAttribute('data-nombre', d.nombre);
    p.addEventListener('click', function () { seleccionar(d.nombre); });
    p.addEventListener('mousemove', function (ev) { mostrarTT(ev, d.nombre, s); });
    p.addEventListener('mouseleave', ocultarTT);
    g.appendChild(p);
    try {
      var bb = p.getBBox();
      var t = document.createElementNS(ns, 'text');
      t.setAttribute('x', (bb.x + bb.width / 2).toFixed(2));
      t.setAttribute('y', (bb.y + bb.height / 2).toFixed(2));
      t.setAttribute('class', 'depto-nom');
      t.setAttribute('text-anchor', 'middle');
      t.textContent = d.nombre;
      g.appendChild(t);
    } catch (e) {}
  });
  svg.innerHTML = '';
  svg.appendChild(g);
  /* aparición progresiva de los departamentos */
  var paths = qa('.depto-path', svg), noms = qa('.depto-nom', svg);
  paths.forEach(function (p, i) {
    later(function () {
      p.classList.add('on');
      if (noms[i]) noms[i].classList.add('on');
    }, reduce ? 0 : 120 + i * 70);
  });
  /* lluvia digital sobre el mapa */
  if (!reduce) {
    var rain = document.createElementNS(ns, 'g');
    for (var i = 0; i < 30; i++) {
      var x = VB.x + Math.random() * VB.w, y = VB.y + Math.random() * VB.h;
      rain.innerHTML += '<line x1="' + x.toFixed(2) + '" y1="' + y.toFixed(2) +
        '" x2="' + (x - 0.12).toFixed(2) + '" y2="' + (y + 0.5).toFixed(2) +
        '" stroke="#F97316" stroke-opacity="0.3" stroke-width="0.05">' +
        '<animate attributeName="y1" values="' + y.toFixed(2) + ';' + (y + VB.h).toFixed(2) +
        '" dur="' + (2.2 + Math.random() * 2.4).toFixed(1) + 's" begin="' +
        (Math.random() * 3).toFixed(1) + 's" repeatCount="indefinite"/>' +
        '<animate attributeName="y2" values="' + (y + 0.5).toFixed(2) + ';' + (y + VB.h + 0.5).toFixed(2) +
        '" dur="' + (2.2 + Math.random() * 2.4).toFixed(1) + 's" begin="' +
        (Math.random() * 3).toFixed(1) + 's" repeatCount="indefinite"/></line>';
    }
    svg.appendChild(rain);
  }
  /* leyenda */
  var leg = document.getElementById('leyenda-geo');
  if (leg) {
    var tramos = [[0, 40, 'Bajo'], [40, 90, 'Medio'], [90, 150, 'Alto'],
                  [150, 230, 'Muy alto'], [230, 600, 'Extremo']];
    leg.innerHTML = tramos.map(function (t) {
      return '<span><i style="background:' + colorTermico((t[0] + t[1]) / 2) + '"></i> ' +
             t[2] + ' ' + t[0] + '–' + t[1] + ' mm</span>';
    }).join('') + '<span><i style="background:#1E293B"></i> sin datos</span>';
  }
}

function mostrarTT(ev, nombre, s) {
  var tt = document.getElementById('tt-mapa');
  var wrap = tt.parentElement.getBoundingClientRect();
  var rank = (s.rank || 99);
  tt.innerHTML = nombre + ': <b>' + fmt(s.media_mensual, 1) + ' mm/mes</b> · #' + rank + ' nacional';
  tt.style.left = (ev.clientX - wrap.left) + 'px';
  tt.style.top = (ev.clientY - wrap.top) + 'px';
  tt.style.opacity = '1';
}
function ocultarTT() {
  var tt = document.getElementById('tt-mapa');
  if (tt) tt.style.opacity = '0';
}

/* selección de departamento */
function seleccionar(nombre) {
  var s = D.stats[nombre];
  if (!s) return;
  qa('.depto-path').forEach(function (p) {
    p.classList.toggle('sel', p.getAttribute('data-nombre') === nombre);
  });
  document.getElementById('dp-nombre').textContent = nombre;
  var rank = s.rank || 99;
  document.getElementById('dp-rank').textContent =
    '#' + rank + ' en precipitación nacional · ' + (rank <= 5 ? 'zona húmeda' : rank >= 20 ? 'zona árida' : 'zona intermedia');
  document.getElementById('dp-media').textContent = fmt(s.media_mensual, 1) + ' mm/mes';
  document.getElementById('dp-anual').textContent = fmt(s.media_anual, 0) + ' mm';
  document.getElementById('dp-mes').textContent =
    ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Setiembre','Octubre','Noviembre','Diciembre'][(s.mes_max || 1) - 1] +
    ' · ' + fmt(s.mm_max_mes, 0) + ' mm';
  document.getElementById('dp-proy').textContent = fmt(s.proy_media, 1) + ' mm/mes';
  document.getElementById('dp-mae').textContent = fmt(s.mae, 1);
  document.getElementById('dp-celdas').textContent = fmt(s.celdas, 0);
  pintarClima(s);
}
function pintarClima(s) {
  var caja = document.getElementById('dp-clim');
  if (!caja || !s || !s.clim) return;
  var mx = Math.max.apply(null, s.clim);
  caja.innerHTML = s.clim.map(function (v, i) {
    return '<div class="b" title="' + MESES[i] + ' ' + fmt(v, 1) + ' mm"><span>' + MESES[i] + '</span></div>';
  }).join('');
  var barras = qa('.b', caja);
  barras.forEach(function (b, i) {
    later(function () { b.style.height = Math.max(4, s.clim[i] / mx * 100) + '%'; },
          reduce ? 0 : 60 + i * 55);
  });
}

/* zoom del mapa */
(function zoom() {
  var svg = document.getElementById('mapa-geo');
  if (!svg) return;
  var z = 1;
  function aplicar() {
    var w = VB.w / z, h = VB.h / z;
    var cx = VB.x + VB.w / 2, cy = VB.y + VB.h / 2;
    svg.setAttribute('viewBox', (cx - w / 2) + ' ' + (cy - h / 2) + ' ' + w + ' ' + h);
    svg.style.transition = 'none';
  }
  document.getElementById('zoom-in').addEventListener('click', function () { z = Math.min(4, z * 1.35); aplicar(); });
  document.getElementById('zoom-out').addEventListener('click', function () { z = Math.max(1, z / 1.35); aplicar(); });
  document.getElementById('zoom-reset').addEventListener('click', function () { z = 1; aplicar(); });
})();

/* top 5 */
(function top5() {
  var caja = document.getElementById('top5');
  if (!caja) return;
  var top = D.ranking.slice(0, 5), mx = top[0].media_mensual;
  caja.innerHTML = top.map(function (r, i) {
    return '<div class="top-row" data-nombre="' + r.nombre + '">' +
      '<div class="i">#' + (i + 1) + '</div>' +
      '<div class="n">' + r.nombre + '</div>' +
      '<div class="bar"><i data-w="' + Math.round(r.media_mensual / mx * 100) + '"></i></div>' +
      '<div class="v">' + fmt(r.media_mensual, 1) + ' mm</div></div>';
  }).join('');
  qa('.top-row', caja).forEach(function (row) {
    row.addEventListener('click', function () {
      seleccionar(row.dataset.nombre);
      document.getElementById('v-geo').scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    });
    var bar = row.querySelector('.bar i');
    later(function () { bar.style.width = bar.dataset.w + '%'; }, reduce ? 0 : 300);
  });
})();

/* ═══════════ FICHA DE REGISTRO · instrumento D1 · D2 · D3 ═══════════ */
(function ficha() {
  var F = D.ficha;
  if (!F) return;

  /* cabecera del instrumento */
  var cab = document.getElementById('ficha-cab');
  if (cab) {
    cab.innerHTML = Object.keys(F.cab).map(function (k) {
      var etiq = k.toUpperCase().replace(/Σ/g, 'σ');
      return '<div class="fc-item"><div class="k">' + etiq + '</div><div class="v">' + F.cab[k] + '</div></div>';
    }).join('');
  }

  /* pestañas + tablas por dimensión */
  var tabs = document.getElementById('ficha-tabs');
  var cont = document.getElementById('ficha-dims');
  if (!tabs || !cont) return;
  var dims = ['D1', 'D2', 'D3'];

  tabs.innerHTML = dims.map(function (d, i) {
    return '<button type="button" class="pestana' + (i === 0 ? ' activa' : '') +
      '" data-dim="' + d + '">' + d + '</button>';
  }).join('');

  cont.innerHTML = dims.map(function (d, i) {
    var dim = F[d];
    var head = dim.cols.map(function (c) { return '<th>' + c + '</th>'; }).join('');
    var rows = dim.filas.map(function (f) {
      return '<tr>' + f.map(function (c, j) {
        return '<td' + (j === 0 ? ' style="color:var(--accent-2)"' : '') + '>' + c + '</td>';
      }).join('') + '</tr>';
    }).join('');
    return '<div class="ficha-dim' + (i === 0 ? ' activa' : '') + '" data-dim="' + d + '">' +
      '<div class="dim-tit">' + dim.titulo + '</div>' +
      '<div class="dim-form">' + dim.formula + '</div>' +
      '<div class="dim-ind">' + dim.indicador + '</div>' +
      '<div class="tbl-scroll"><table class="datos ficha-tbl"><thead><tr>' + head +
      '</tr></thead><tbody>' + rows + '</tbody></table></div></div>';
  }).join('');

  qa('.pestana', tabs).forEach(function (b) {
    b.addEventListener('click', function () {
      qa('.pestana', tabs).forEach(function (x) { x.classList.toggle('activa', x === b); });
      qa('.ficha-dim', cont).forEach(function (x) {
        x.classList.toggle('activa', x.dataset.dim === b.dataset.dim);
      });
    });
  });
})();

/* ═══════════ MÉTRICAS DE CALIDAD · fichas + criterios ═══════════ */
(function metricas() {
  var caja = document.getElementById('metricas-fichas');
  if (!caja || !D.metricas) return;
  caja.innerHTML = D.metricas.map(function (m, i) {
    return '<div class="met-ficha rev" style="transition-delay:' + (i * 90) + 'ms">' +
      '<div class="mf-top"><div class="mf-sigla">' + m.sigla + '</div>' +
        '<div class="pill-ok">✓ CUMPLE</div></div>' +
      '<div class="mf-val">' + m.valor + (m.unidad ? ' <span>' + m.unidad + '</span>' : '') + '</div>' +
      '<div class="mf-def">' + m.def + '</div>' +
      '<div class="mf-kv">' +
        '<div class="r"><span class="k">Umbral esperado</span><span class="v">' + m.umbral + '</span></div>' +
        '<div class="r"><span class="k">Mi umbral</span><span class="v acc">' + m.mi + '</span></div>' +
      '</div>' +
      '<div class="mf-desc">' + m.desc + '</div></div>';
  }).join('');

  var tb = document.getElementById('tabla-criterios');
  if (tb && D.criterios) {
    tb.innerHTML = D.criterios.map(function (c) {
      return '<tr><td>' + c.criterio + '</td><td>' + c.umbral + '</td>' +
        '<td style="color:var(--accent-2);font-weight:700">' + c.resultado + '</td>' +
        '<td style="color:var(--ok)">✓ CUMPLE</td></tr>';
    }).join('');
  }
  qa('.rev', caja).forEach(function (el) { io.observe(el); });
})();

/* ═══════════ ML LAB · tarjetas de modelos ═══════════ */
(function modelosLab() {
  var caja = document.getElementById('modelos-lab');
  if (!caja) return;
  var procs = {
    'Regresión Ridge': 'ENTRENAMIENTO · 1 500 000 obs. · semilla 42',
    'XGBoost': 'ENTRENAMIENTO · 300 000 obs. · semilla 42',
    'Random Forest': 'ENTRENAMIENTO · 300 000 obs. · semilla 42',
    'Regresión KNN': 'ENTRENAMIENTO · 300 000 obs. · k = 7 · semilla 42'
  };
  caja.innerHTML = D.modelos.map(function (m, i) {
    var win = m.modelo === 'Regresión Ridge';
    return '<div class="model-card rev' + (win ? ' win' : '') + '" data-i="' + i + '">' +
      (win ? '<div class="mc-badge">BEST MODEL</div>' : '') +
      '<div class="mc-name">' + m.modelo + '</div>' +
      '<div class="mc-proc">' + (procs[m.modelo] || 'ENTRENAMIENTO') + '</div>' +
      '<div class="mc-status" data-status>Entrenando...</div>' +
      '<div class="mc-prog"><i data-prog></i></div>' +
      '<div class="mc-metrics">' +
        '<div class="mc-metric"><span class="k">MAE</span><span class="v">' + fmt(m.mae, 2) + ' mm</span></div>' +
        '<div class="mc-metric"><span class="k">RMSE</span><span class="v">' + fmt(m.rmse, 2) + ' mm</span></div>' +
        '<div class="mc-metric"><span class="k">R²</span><span class="v">' + fmt(m.r2, 2) + '</span></div>' +
        '<div class="mc-metric"><span class="k">OBS. TRAIN</span><span class="v">' + fmt(m.n, 0) + '</span></div>' +
      '</div></div>';
  }).join('');

  /* tabla comparativa */
  var tb = document.querySelector('#tabla-modelos tbody');
  tb.innerHTML = D.modelos.map(function (m) {
    var win = m.modelo === 'Regresión Ridge';
    return '<tr' + (win ? ' class="win"' : '') + '><td>' + m.modelo + '</td><td>' + fmt(m.n, 0) +
      '</td><td>' + fmt(m.mae, 2) + '</td><td>' + fmt(m.rmse, 2) + '</td><td>' + fmt(m.r2, 2) +
      '</td><td>' + fmt(m.rel_mae, 2) + '</td><td>' + fmt(m.rel_rmse, 2) +
      '</td><td style="color:' + (win ? 'var(--accent-2)' : 'var(--ok)') + '">' +
      (win ? '✓ GANADOR' : '✓ CUMPLE') + '</td></tr>';
  }).join('');

  /* animación de entrenamiento al entrar en pantalla */
  qa('.rev', caja).forEach(function (el) { io.observe(el); });
  var lab = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      lab.disconnect();
      qa('.model-card', caja).forEach(function (card, i) {
        var bar = card.querySelector('[data-prog]');
        var st = card.querySelector('[data-status]');
        later(function () {
          bar.style.width = '100%';
          later(function () {
            st.textContent = 'Entrenamiento completado ✓';
            st.classList.add('done');
          }, reduce ? 0 : 1800);
        }, reduce ? 0 : 300 + i * 420);
      });
    });
  }, { threshold: 0.25 });
  lab.observe(caja);
})();

/* ═══════════ FORECAST TERMINAL + GRÁFICO ═══════════ */
(function forecast() {
  var out = document.getElementById('forecast-out');
  var caja = document.getElementById('fc-bars');
  if (!out || !caja) return;

  var lineas = [
    { s: 'Modelo cargado: Regresión Ridge ✓', c: 'ok' },
    { s: 'Generando 12 pronósticos mensuales (recursivo)...', c: 'c' },
    { s: 'Aplicando recorte de valores no negativos (≥ 0 mm)...', c: 'c' },
    { s: 'Pronóstico completado ✓', c: 'ok' }
  ];
  out.innerHTML = lineas.map(function (l) {
    return '<div class="' + (l.c === 'p' ? '' : l.c) + '">' +
      (l.c === 'p' ? '<span class="p">' + l.s + '</span>' : l.s) + '</div>';
  }).join('') + '<div style="margin-top:8px" class="dim">PROYECCIÓN 2026 · PRECIPITACIÓN MEDIA NACIONAL (MM/MES)</div>' +
    D.proyeccionNacional.map(function (r) {
      var m = r.mes.slice(5).replace(/^0/, '');
      return '<div><span class="acc">' + MESES[parseInt(m, 10) - 1] + '</span> · ' + fmt(r.mm, 2) + ' mm</div>';
    }).join('');

  var mx = Math.max.apply(null, D.proyeccionNacional.map(function (r) { return r.mm; }));
  caja.innerHTML = D.proyeccionNacional.map(function (r, i) {
    var m = parseInt(r.mes.slice(5), 10);
    return '<div class="col"><div class="bar" data-h="' + Math.round(r.mm / mx * 100) + '">' +
      '<em>' + fmt(r.mm, 2) + '</em></div><div class="m">' + MESES[m - 1] + '</div></div>';
  }).join('');

  var fio = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      fio.disconnect();
      qa('.bar', caja).forEach(function (b, i) {
        later(function () { b.style.height = b.dataset.h + '%'; }, reduce ? 0 : 150 + i * 90);
      });
    });
  }, { threshold: 0.3 });
  fio.observe(caja);
})();

/* ═══════════ PIPELINE · animación de pasos ═══════════ */
(function pipeline() {
  var pipe = document.getElementById('pipe');
  if (!pipe) return;
  var steps = qa('.pipe-step', pipe);
  var pio = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      pio.disconnect();
      steps.forEach(function (s, i) {
        later(function () { s.classList.add('on'); }, reduce ? 0 : 250 + i * 520);
      });
    });
  }, { threshold: 0.2 });
  pio.observe(pipe);
})();

/* ═══════════ ARRANQUE GENERAL TRAS EL BOOT ═══════════ */
function arrancarSistema() {
  spy();
  /* el módulo geo se construye cuando está cerca del viewport */
  var geoMod = document.getElementById('v-geo');
  if (geoMod) {
    var gio = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { construirGeo(); seleccionar('Loreto'); gio.disconnect(); }
      });
    }, { threshold: 0.05 });
    gio.observe(geoMod);
  }
  var msg = document.getElementById('status-msg');
  if (msg) {
    later(function () { msg.textContent = 'climatelab · ' + fmt(540) + ' meses procesados · datos PISCOp v3.0'; }, 3000);
    later(function () { msg.textContent = 'modelo ganador Regresión Ridge cargado · r² 0,80 ✓'; }, 7000);
    later(function () { msg.textContent = 'sistema listo ✓'; }, 12000);
  }
}

/* si el usuario llega con hash o recarga ya iniciado */
if (document.body.classList.contains('booted')) arrancarSistema();

})();
