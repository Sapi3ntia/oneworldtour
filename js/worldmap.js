/* ============================================================
   WORLDMAP — the app's own map engine. One SVG, zero libraries.

   Why not Leaflet: raster tiles + markercluster on a software-
   rendered machine produced years of "pins slide / thrown into the
   ocean / Europe bubbles over Africa" bugs. This engine draws the
   pre-projected country shapes from assets/world.json (Natural
   Earth I, baked at build time) and projects only city dots at
   runtime. Everything is deterministic:

     • World view (k < COUNTRY_K): one node per country, sized by
       how many places it holds. Click → glide into that country.
     • Zoomed in: real city dots, labels fade in as you go deeper.
       Click a dot → callback. No clustering library, no bounding-
       box camera jumps — the camera only ever glides to where you
       pointed.
     • Pan = pointer drag, zoom = wheel toward cursor / buttons /
       double-click. All camera motion is one rAF viewBox tween.
     • 'pick' mode (City Guesser): clicks emit {lat,lng} via the
       exact projection inverse.

   Perf guardrails: no filters, no shadows, no infinite animations;
   strokes use vector-effect:non-scaling-stroke; dot radii are
   updated once per zoom change (~350 circles — cheap).
   ============================================================ */
import { project, unproject, MAP_W, MAP_H } from './lib/geo.js';

const NS = 'http://www.w3.org/2000/svg';
const COUNTRY_K = 2.6;   // below this zoom: country nodes; above: city dots
const LABEL_K = 4.2;     // city labels appear from this zoom
const K_MAX = 40, K_MIN = 1;

const svgEl = (tag, attrs = {}) => {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  return n;
};

export class WorldMap {
  /**
   * @param {HTMLElement} container
   * @param {object} opts { onPlaceClick(place), onCountryClick(name),
   *                        onPick({lat,lng}), mode: 'explore'|'pick' }
   */
  constructor(container, opts = {}) {
    this.container = container;
    this.opts = opts;
    this.mode = opts.mode || 'explore';
    this.places = [];
    this.filterFn = null;
    this.vb = { x: 0, y: 0, w: MAP_W, h: MAP_H };
    this._anim = null;
    this._pins = [];

    container.classList.add('wmap');
    this.svg = svgEl('svg', {
      viewBox: `0 0 ${MAP_W} ${MAP_H}`,
      preserveAspectRatio: 'xMidYMid meet',
      role: 'img', 'aria-label': 'World map',
    });
    this.gLand = svgEl('g', { class: 'wmap-land' });
    this.gGrat = svgEl('g', { class: 'wmap-grat' });
    this.gMarks = svgEl('g', { class: 'wmap-marks' });
    this.gDots = svgEl('g', { class: 'wmap-dots' });
    this.svg.append(this.gGrat, this.gLand, this.gDots, this.gMarks);
    container.appendChild(this.svg);

    this.tip = document.createElement('div');
    this.tip.className = 'wmap-tip';
    container.appendChild(this.tip);

    this._graticule();
    this._bind();
  }

  /* Faint meridians/parallels every 30° — the "atlas" texture. */
  _graticule() {
    const path = pts => 'M' + pts.map(({ x, y }) => `${x.toFixed(1)} ${y.toFixed(1)}`).join('L');
    for (let lng = -150; lng <= 180; lng += 30) {
      const pts = [];
      for (let lat = -85; lat <= 85; lat += 5) pts.push(project(lat, lng));
      this.gGrat.appendChild(svgEl('path', { d: path(pts) }));
    }
    for (let lat = -60; lat <= 60; lat += 30) {
      const pts = [];
      for (let lng = -180; lng <= 180; lng += 5) pts.push(project(lat, lng));
      this.gGrat.appendChild(svgEl('path', { d: path(pts) }));
    }
  }

  /* ---------------- data ---------------- */

  async loadWorld(url = 'assets/world.json') {
    const world = await fetch(url).then(r => r.json());
    for (const c of world.countries) {
      this.gLand.appendChild(svgEl('path', {
        d: c.p, 'fill-rule': 'evenodd', 'data-name': c.n,
        'vector-effect': 'non-scaling-stroke',
      }));
    }
  }

  /* places: [{...place, _flags:{walk,live,window,monuments}}] */
  setPlaces(places) {
    this.places = places.map(p => ({
      ...p,
      _pt: project(p.coordinates.lat, p.coordinates.lng),
    }));
    this._rebuildDots();
  }

  setFilter(fn) { this.filterFn = fn; this._rebuildDots(); }

  _visible() { return this.filterFn ? this.places.filter(this.filterFn) : this.places; }

  _rebuildDots() {
    this.gDots.innerHTML = '';
    this._countryNodes = [];
    this._cityDots = [];
    const vis = this._visible();

    // country aggregation nodes — anchored on a real member place.
    // A mean would drift into open sea for countries with far-flung
    // islands (Portugal + Azores put the node in the Atlantic), so:
    // take the median point and snap to the member nearest it.
    const median = arr => {
      const s = [...arr].sort((a, b) => a - b);
      const m = s.length >> 1;
      return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
    };
    const by = new Map();
    for (const p of vis) {
      if (!by.has(p.country)) by.set(p.country, []);
      by.get(p.country).push(p);
    }
    for (const [country, list] of by) {
      const mx = median(list.map(p => p._pt.x));
      const my = median(list.map(p => p._pt.y));
      let anchor = list[0], bd = Infinity;
      for (const p of list) {
        const d = (p._pt.x - mx) ** 2 + (p._pt.y - my) ** 2;
        if (d < bd) { bd = d; anchor = p; }
      }
      const cx = anchor._pt.x, cy = anchor._pt.y;
      const g = svgEl('g', { class: 'wmap-cnode', 'data-country': country });
      const r0 = Math.min(11, 5.5 + Math.sqrt(list.length) * 1.6);
      g.appendChild(svgEl('circle', { cx, cy, r: r0, class: 'cnode-halo' }));
      g.appendChild(svgEl('circle', { cx, cy, r: r0 * 0.62, class: 'cnode-core' }));
      const t = svgEl('text', { x: cx, y: cy, class: 'cnode-count', 'text-anchor': 'middle', dy: '0.34em' });
      t.textContent = list.length;
      g.appendChild(t);
      this.gDots.appendChild(g);
      this._countryNodes.push({ g, country, list, cx, cy, r0 });
    }

    // city dots (+labels), hidden until zoomed
    for (const p of vis) {
      const g = svgEl('g', { class: 'wmap-city', 'data-id': p.id });
      const f = p._flags || {};
      let cls = 'city-dot';
      if (f.live) cls += ' has-live';
      else if (f.walk) cls += ' has-walk';
      // invisible oversized hit circle — the visible dot is a few px,
      // the click/tap target shouldn't be
      const hit = svgEl('circle', { cx: p._pt.x, cy: p._pt.y, r: 6, class: 'city-hit' });
      const dot = svgEl('circle', { cx: p._pt.x, cy: p._pt.y, r: 2.4, class: cls });
      const label = svgEl('text', {
        x: p._pt.x, y: p._pt.y, dx: 4, dy: '0.32em', class: 'city-label',
      });
      label.textContent = `${p.emoji || ''} ${p.name}`.trim();
      g.append(hit, dot, label);
      this.gDots.appendChild(g);
      this._cityDots.push({ g, hit, dot, label, p });
    }
    this._applyZoomStyling();
  }

  /* Route pins / extra markers (guesser answers etc.) */
  addPin(lat, lng, cls = 'wmap-pin') {
    const { x, y } = project(lat, lng);
    const g = svgEl('g', { class: cls });
    g.appendChild(svgEl('circle', { cx: x, cy: y, r: 5, class: 'pin-ring' }));
    g.appendChild(svgEl('circle', { cx: x, cy: y, r: 2.2, class: 'pin-core' }));
    this.gMarks.appendChild(g);
    this._pins.push(g);
    this._applyZoomStyling();
    return g;
  }

  /* A numbered, clickable stop on a route (Trips). Same marks layer as
     addPin, so clearMarks() drops it and zoom styling keeps it legible. */
  addStop(lat, lng, label, opts = {}) {
    const { x, y } = project(lat, lng);
    const g = svgEl('g', { class: `wmap-stop ${opts.cls || ''}`.trim() });
    /* Rendered size works out to base * (container height / MAP_H) px,
       independent of zoom — 11 gives a ~22px disc on the trips map. */
    const disc = svgEl('circle', { cx: x, cy: y, r: 11, class: 'stop-disc' });
    disc.dataset.r = 11;
    g.appendChild(disc);
    const t = svgEl('text', {
      x, y, dy: '0.34em', 'text-anchor': 'middle', class: 'stop-num',
    });
    t.textContent = label;
    g.appendChild(t);
    if (opts.title) {
      const ttl = svgEl('title');
      ttl.textContent = opts.title;
      g.appendChild(ttl);
    }
    if (opts.onClick) {
      g.style.cursor = 'pointer';
      g.addEventListener('click', ev => { ev.stopPropagation(); opts.onClick(ev); });
    }
    this.gMarks.appendChild(g);
    this._pins.push(g);
    this._applyZoomStyling();
    return g;
  }

  /* NOTE: a straight line in projected space. Correct for every route
     we ship; a leg that crossed the antimeridian would draw the long
     way round the map and need splitting at ±180 first. */
  drawLine(a, b, cls = 'wmap-line') {
    const p1 = project(a.lat, a.lng), p2 = project(b.lat, b.lng);
    const line = svgEl('line', {
      x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y, class: cls,
      'vector-effect': 'non-scaling-stroke',
    });
    this.gMarks.appendChild(line);
    this._pins.push(line);
    return line;
  }
  clearMarks() { this.gMarks.innerHTML = ''; this._pins = []; }

  /* ---------------- camera ---------------- */

  get k() { return MAP_W / this.vb.w; }

  _setVb(x, y, w, h) {
    // clamp
    w = Math.min(MAP_W, Math.max(MAP_W / K_MAX, w));
    h = w * (MAP_H / MAP_W);
    x = Math.max(-w * 0.05, Math.min(MAP_W - w * 0.95, x));
    y = Math.max(-h * 0.05, Math.min(MAP_H - h * 0.95, y));
    this.vb = { x, y, w, h };
    this.svg.setAttribute('viewBox', `${x} ${y} ${w} ${h}`);
    this._applyZoomStyling();
  }

  _applyZoomStyling() {
    const k = this.k;
    const cityMode = k >= COUNTRY_K;
    this.container.classList.toggle('wmap-citymode', cityMode);
    const showLabels = k >= LABEL_K;
    if (this._cityDots) {
      const r = Math.max(1.6, 3.4 / Math.sqrt(k));
      const fs = 11 / k;
      for (const d of this._cityDots) {
        d.dot.setAttribute('r', r);
        d.hit.setAttribute('r', r * 2.4);
        if (showLabels) {
          d.label.style.display = '';
          d.label.setAttribute('font-size', fs);
          d.label.setAttribute('dx', r * 1.8);
        } else {
          d.label.style.display = 'none';
        }
      }
    }
    if (this._countryNodes) {
      for (const n of this._countryNodes) {
        const t = n.g.querySelector('.cnode-count');
        if (t) t.setAttribute('font-size', Math.max(7, 8.5 / Math.sqrt(k)));
      }
    }
    /* Guesser pins scale by 1/√k — they grow a little as you zoom, which
       reads well for two pins and a line. Trip stops must instead hold a
       CONSTANT on-screen size (1/k): a tight route like the Grand Circle
       zooms hard, and at 1/√k the discs bloat until they cover the route
       they're labelling. */
    for (const pin of this._pins || []) {
      if (!pin.querySelectorAll) continue;
      for (const c of pin.querySelectorAll('circle')) {
        if (c.classList.contains('stop-disc')) {
          c.setAttribute('r', (Number(c.dataset.r) || 11) / k);
          continue;
        }
        c.setAttribute('r', (c.classList.contains('pin-ring') ? 5 : 2.2) / Math.sqrt(k));
      }
      for (const t of pin.querySelectorAll('.stop-num')) {
        t.setAttribute('font-size', 12 / k);
      }
    }
  }

  /* Glide the camera. target: {x,y,w} in map units. */
  _glide(tx, ty, tw, ms = 650) {
    if (this._anim) cancelAnimationFrame(this._anim);
    const s = { ...this.vb };
    const th = tw * (MAP_H / MAP_W);
    const t0 = performance.now();
    const ease = t => t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
    const step = now => {
      const f = Math.min(1, (now - t0) / ms);
      const e = ease(f);
      this._setVb(
        s.x + (tx - s.x) * e,
        s.y + (ty - s.y) * e,
        s.w + (tw - s.w) * e,
        s.h + (th - s.h) * e,
      );
      if (f < 1) this._anim = requestAnimationFrame(step);
      else { this._anim = null; if (this.onSettle) this.onSettle(); }
    };
    this._anim = requestAnimationFrame(step);
  }

  /* Fly so that lat/lng is centered at zoom k. */
  flyTo(lat, lng, k = 6, ms = 700) {
    const { x, y } = project(lat, lng);
    const w = MAP_W / k, h = w * (MAP_H / MAP_W);
    this._glide(x - w / 2, y - h / 2, w, ms);
  }

  setMode(m) { this.mode = m; }

  /* Fly to fit a set of places (padded). forceCity guarantees landing
     past the country→city threshold (used by country-node clicks). */
  flyToPlaces(list, ms = 700, forceCity = false, minW = 0) {
    if (!list.length) return;
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (const p of list) {
      const pt = p._pt || project(p.coordinates.lat, p.coordinates.lng);
      x0 = Math.min(x0, pt.x); x1 = Math.max(x1, pt.x);
      y0 = Math.min(y0, pt.y); y1 = Math.max(y1, pt.y);
    }
    const pad = Math.max((x1 - x0), (y1 - y0) * (MAP_W / MAP_H)) * 0.35 + 14;
    let w = (x1 - x0) + pad * 2;
    w = Math.max(w, MAP_W / K_MAX * 3);           // don't overshoot into the ground
    w = Math.max(w, minW);                        // caller's floor (trip routes)
    w = Math.min(w, MAP_W);
    // ensure we land in city mode — the whole point of a country click
    if (forceCity && MAP_W / w < COUNTRY_K) w = MAP_W / (COUNTRY_K * 1.15);
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    const h = w * (MAP_H / MAP_W);
    this._glide(cx - w / 2, cy - h / 2, w, ms);
  }

  reset(ms = 600) { this._glide(0, 0, MAP_W, ms); }

  /* ---------------- interaction ---------------- */

  _clientToMap(ev) {
    const r = this.svg.getBoundingClientRect();
    // viewBox is fit with xMidYMid meet — account for letterboxing
    const scale = Math.min(r.width / this.vb.w, r.height / this.vb.h);
    const ox = (r.width - this.vb.w * scale) / 2;
    const oy = (r.height - this.vb.h * scale) / 2;
    return {
      x: this.vb.x + (ev.clientX - r.left - ox) / scale,
      y: this.vb.y + (ev.clientY - r.top - oy) / scale,
    };
  }

  _bind() {
    const c = this.container;
    let drag = null, moved = false;

    c.addEventListener('pointerdown', ev => {
      if (ev.button !== 0) return;
      drag = { px: ev.clientX, py: ev.clientY, vb: { ...this.vb } };
      moved = false;
      try { c.setPointerCapture(ev.pointerId); } catch { /* synthetic events */ }
    });
    c.addEventListener('pointermove', ev => {
      if (drag) {
        const r = this.svg.getBoundingClientRect();
        const scale = Math.min(r.width / this.vb.w, r.height / this.vb.h);
        const dx = (ev.clientX - drag.px) / scale;
        const dy = (ev.clientY - drag.py) / scale;
        if (Math.abs(ev.clientX - drag.px) + Math.abs(ev.clientY - drag.py) > 4) moved = true;
        if (moved) {
          if (this._anim) { cancelAnimationFrame(this._anim); this._anim = null; }
          this._setVb(drag.vb.x - dx, drag.vb.y - dy, drag.vb.w, drag.vb.h);
        }
      } else {
        this._hover(ev);
      }
    });
    const endDrag = ev => {
      if (drag && !moved) this._click(ev);
      drag = null;
    };
    c.addEventListener('pointerup', endDrag);
    c.addEventListener('pointercancel', () => { drag = null; });
    c.addEventListener('pointerleave', () => { this._tipHide(); });

    c.addEventListener('wheel', ev => {
      ev.preventDefault();
      const pt = this._clientToMap(ev);
      const factor = ev.deltaY < 0 ? 0.82 : 1.22;
      let w = this.vb.w * factor;
      w = Math.min(MAP_W, Math.max(MAP_W / K_MAX, w));
      const fx = (pt.x - this.vb.x) / this.vb.w;
      const fy = (pt.y - this.vb.y) / this.vb.h;
      const h = w * (MAP_H / MAP_W);
      if (this._anim) { cancelAnimationFrame(this._anim); this._anim = null; }
      this._setVb(pt.x - fx * w, pt.y - fy * h, w, h);
    }, { passive: false });

    c.addEventListener('dblclick', ev => {
      const pt = this._clientToMap(ev);
      const w = Math.max(MAP_W / K_MAX, this.vb.w * 0.45);
      const h = w * (MAP_H / MAP_W);
      this._glide(pt.x - w / 2, pt.y - h / 2, w, 420);
    });
  }

  _pickTarget(ev) {
    // NEVER trust ev.target here: while the pointer is captured
    // (pointerdown → pointerup), events are retargeted to the
    // container, so ev.target on release is the div — which made
    // every dot/node click silently miss. Resolve the element under
    // the cursor ourselves instead.
    const under = document.elementFromPoint(ev.clientX, ev.clientY);
    if (!under) return { type: 'sea' };
    const cityMode = this.k >= COUNTRY_K;
    if (cityMode) {
      const g = under.closest('.wmap-city');
      if (g) {
        const hit = this._cityDots.find(d => d.g === g);
        if (hit) return { type: 'city', place: hit.p };
      }
    } else {
      const g = under.closest('.wmap-cnode');
      if (g) {
        const hit = this._countryNodes.find(n => n.g === g);
        if (hit) return { type: 'country', country: hit.country, list: hit.list };
      }
    }
    const land = under.closest('.wmap-land path');
    if (land) return { type: 'land', name: land.getAttribute('data-name') };
    return { type: 'sea' };
  }

  _click(ev) {
    const pt = this._clientToMap(ev);
    if (this.mode === 'pick') {
      if (pt.x < 0 || pt.x > MAP_W || pt.y < 0 || pt.y > MAP_H) return;
      const { lat, lng } = unproject(pt.x, pt.y);
      if (Math.abs(lat) > 90 || Math.abs(lng) > 180) return;
      this.opts.onPick?.({ lat, lng });
      return;
    }
    const t = this._pickTarget(ev);
    if (t.type === 'city') this.opts.onPlaceClick?.(t.place);
    else if (t.type === 'country') {
      this.opts.onCountryClick?.(t.country, t.list);
      this.flyToPlaces(t.list, 700, true);
    }
  }

  _hover(ev) {
    const t = this._pickTarget(ev);
    if (t.type === 'city') {
      const f = t.place._flags || {};
      const tags = [f.live && '🔴', f.window && '🪟', f.walk && '🚶', f.monuments && '🏛️'].filter(Boolean).join(' ');
      this._tipShow(ev, `${t.place.emoji || '📍'} <b>${t.place.name}</b> · ${t.place.country}${tags ? ` &nbsp;${tags}` : ''}`);
      this.container.style.cursor = 'pointer';
    } else if (t.type === 'country') {
      // one-place countries get named outright — a bare "Chile · 1
      // place" node sitting on Easter Island looks like a bug
      const tip = t.list.length === 1
        ? `${t.list[0].emoji || '📍'} <b>${t.list[0].name}</b> · ${t.country} — click to explore`
        : `<b>${t.country}</b> · ${t.list.length} places — click to explore`;
      this._tipShow(ev, tip);
      this.container.style.cursor = 'pointer';
    } else if (this.mode === 'pick') {
      this.container.style.cursor = 'crosshair';
      this._tipHide();
    } else {
      this.container.style.cursor = 'grab';
      this._tipHide();
    }
  }

  _tipShow(ev, html) {
    const r = this.container.getBoundingClientRect();
    this.tip.innerHTML = html;
    this.tip.style.display = 'block';
    const x = Math.min(ev.clientX - r.left + 14, r.width - 220);
    const y = Math.max(ev.clientY - r.top - 34, 8);
    this.tip.style.transform = `translate(${x}px, ${y}px)`;
  }
  _tipHide() { this.tip.style.display = 'none'; }
}
