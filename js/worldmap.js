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

   Hit testing is GEOMETRIC, not DOM (2026-07). Dots and country
   nodes are pointer-events:none; a click resolves to the marker
   whose CENTRE is nearest the cursor, within a fixed pixel radius.
   Two reasons, both reported from the wild:
     • elementFromPoint returns whatever was painted last, so a city
       drawn later stole its neighbour's clicks — Osaka sat under
       Kyoto and Kobe, the Toronto cluster fought over one pixel.
       Nearest-centre gives every dot its own Voronoi cell instead.
     • dot radii used to be floored in MAP units, which meant they
       grew linearly on screen once zoomed past k≈4.5 (a 64px blob
       at k=40) and swallowed their neighbours. Radii are now pinned
       in real pixels, exactly like the label text always was.

   Some places, though, cannot be separated by zooming at all. Cape Town,
   Table Mountain and Camps Bay are 5 km apart — three dots inside one
   dot's worth of screen at EVERY zoom this camera can reach. Those get
   FANNED (2026-08): places within FAN_U map units of each other form a
   group, and each member slides toward a ring slot of its own, keeping a
   hairline leader back to where it really is. The whole group slides by
   the same fraction, and that fraction falls to zero the moment real
   geography has opened FAN_PX between its tightest pair — so zooming in
   still resolves a cluster for real, and the fan only covers the last
   stretch the camera can't. See _buildFans / _fanOut.

   Everything drawn per-place is pinned that way now (2026-07). The
   label's dark outline was the last hold-out: its font-size shrank
   with the zoom but its stroke-width stayed 2.5 MAP units, so by the
   time you'd zoomed into Japan each name sat in a ~60px black slab
   that hid Tokyo, Osaka and Kyoto behind their neighbours' captions.
   Halo width is now screen pixels too. Labels also declutter: each
   name takes the best free slot of sixteen around its own dot —
   beside it, stacked over or under it, or out on a diagonal — and
   where every slot is taken the lower-priority one steps aside and
   leaves its dot. See _placeLabels.

   Input is pointer, touch AND keyboard: two fingers pinch-zoom, and a
   focused map pans on the arrows, zooms on +/-, and steps through the
   places in view on n/p (see _key). Everything a mouse can reach, a
   keyboard can reach.

   Perf guardrails: no filters, no shadows; strokes use
   vector-effect:non-scaling-stroke. Per-frame DOM work is bounded by
   the VIEWPORT, not by the atlas — _applyZoomStyling restyles the ~40
   places you can actually see, not all ~377. The one infinite
   animation (the live-cam pulse) is likewise mounted only on in-view
   dots, and not at all under prefers-reduced-motion.
   ============================================================ */
import { project, unproject, MAP_W, MAP_H } from './lib/geo.js';

const NS = 'http://www.w3.org/2000/svg';
const COUNTRY_K = 2.6;   // below this zoom: country nodes; above: city dots
const LABEL_K = 4.2;     // city labels appear from this zoom
const K_MAX = 90, K_MIN = 1;
const FIT_MIN_W = 75;    // narrowest viewBox flyToPlaces will fit to, in map units
const DOT_PX = 4;        // city dot radius, in real screen pixels at any zoom
const HIT_PX = 12;       // click/tap radius around a dot centre, likewise
const HALO_PX = 2.5;     // label outline width, likewise (see _applyZoomStyling)
const LABEL_CAP = 150;   // most labels we'll consider placing in one pass
/* Where a caption is allowed to sit, best first, as [side, row]: side is
   right / left / centred over the dot, row is how many caption-heights
   above (-) or below (+) it. Right before left and above before below
   all the way down, so the map stays predictable as you pan. See
   _placeLabels for why two slots was not enough. */
const LABEL_SLOTS = [
  [1, 0], [-1, 0],                                    // beside it — the classic
  [0, -1], [0, 1],                                    // stacked over / under
  [1, -1], [-1, -1], [1, 1], [-1, 1],                 // the diagonals
  [0, -2], [0, 2], [1, -2], [-1, 2], [1, 2], [-1, -2],
  [0, -3], [0, 3],                                    // last resort, 3 lines out
];
const VIEW_PAD = 0.15;   // restyle/declutter this far outside the viewBox
const PAN_STEP = 0.18;   // arrow-key pan, as a fraction of the viewport
/* Fanning overlapping places. FAN_U is deliberately tiny — a third of a
   map unit is ~14 km, i.e. "the same spot", not "the same region". Open
   it up and single-linkage chains the whole of Hong Kong into one
   twenty-dot flower; at 0.34 the biggest group we hold is 9 (Hong Kong
   island + Kowloon), and the one that started this is 3 (Cape Town). */
const FAN_U = 0.34;      // group places closer than this, in map units
const FAN_PX = 15;       // and hold fanned neighbours this far apart, in screen px
/* Where the fan lets go. It has to be comfortably MORE than FAN_PX: the
   dots travel in a straight line from true to slot, so if the group let
   go the instant real separation reached FAN_PX, the halfway point of
   that slide would be tighter than either end (a measured 11 px dip at
   t≈0.5). Releasing at twice the target makes the whole ramp monotone —
   drawn separation never falls below FAN_PX at any zoom. */
const FAN_OFF_PX = 30;   // real separation at which a group stops fanning

/* Natural Earth spells a handful of countries differently from our own
   data. Four names, so: four aliases, not a fuzzy matcher. (Malta,
   Micronesia, Singapore and Vatican City have no polygon at this
   resolution at all — nothing to alias them to.) */
const LAND_ALIAS = {
  'United States of America': 'United States',
  'Dem. Rep. Congo': 'DR Congo',
  'Bosnia and Herz.': 'Bosnia and Herzegovina',
  Czechia: 'Czech Republic',
};

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
    container.classList.toggle('wmap-pick', this.mode === 'pick');
    /* Focusable, and announced as what it is. role=application because
       the arrows are ours here — a screen reader that swallowed them to
       move its own cursor would leave the map unpannable. */
    if (!container.hasAttribute('tabindex')) container.tabIndex = 0;
    container.setAttribute('role', 'application');
    container.setAttribute('aria-label', this.mode === 'pick'
      ? 'World map. Arrow keys pan, plus and minus zoom, Enter drops your guess.'
      : 'World map. Arrow keys pan, plus and minus zoom, 0 for the whole world, '
        + 'n and p step through the places in view, Enter opens the highlighted place.');
    this.svg = svgEl('svg', {
      viewBox: `0 0 ${MAP_W} ${MAP_H}`,
      preserveAspectRatio: 'xMidYMid meet',
      'aria-hidden': 'true',           // the container carries the label
    });
    this.gLand = svgEl('g', { class: 'wmap-land' });
    this.gGrat = svgEl('g', { class: 'wmap-grat' });
    this.gMarks = svgEl('g', { class: 'wmap-marks' });
    this.gDots = svgEl('g', { class: 'wmap-dots' });
    this.gPulse = svgEl('g', { class: 'wmap-pulse' });
    this.svg.append(this.gGrat, this.gLand, this.gPulse, this.gDots, this.gMarks);
    container.appendChild(this.svg);

    this.tip = document.createElement('div');
    this.tip.className = 'wmap-tip';
    container.appendChild(this.tip);

    /* Whatever the highlight lands on gets said out loud. The keyboard
       walk (n/p) would otherwise be silent to a screen reader — the
       tooltip is a div nobody is watching. */
    this.live = document.createElement('div');
    this.live.className = 'wmap-sr';
    this.live.setAttribute('aria-live', 'polite');
    container.appendChild(this.live);

    this._rect = null;
    this._hot = null;
    this._tipPin = null;
    /* The live-cam pulse is the one animation here, so it asks first —
       and keeps asking, because this can be toggled mid-session. */
    this._pulseOK = true;
    if (typeof matchMedia === 'function') {
      const mq = matchMedia('(prefers-reduced-motion: reduce)');
      this._pulseOK = !mq.matches;
      mq.addEventListener?.('change', e => {
        this._pulseOK = !e.matches;
        this._applyZoomStyling();
      });
    }
    this._measure();
    if (typeof ResizeObserver !== 'undefined') {
      this._ro = new ResizeObserver(() => { this._measure(); this._applyZoomStyling(); });
      this._ro.observe(container);
    }

    this._graticule();
    this._bind();
  }

  /* Cached size of the SVG box. Measured on resize only: _applyZoomStyling
     runs on every tween frame, and a getBoundingClientRect in there would
     force a layout flush right after we've dirtied ~350 circle radii —
     exactly the thrash this engine exists to avoid. Only the SCALE is
     cached; _clientToMap still reads left/top live, because those move
     when the page scrolls and the cache would silently offset every click. */
  _measure() {
    const r = this.svg.getBoundingClientRect();
    if (r.width && r.height) this._rect = { width: r.width, height: r.height };
  }

  /* Map units per on-screen pixel at the current zoom. */
  get _u() {
    const r = this._rect;
    if (!r) return this.vb.w / MAP_W;
    return 1 / Math.min(r.width / this.vb.w, r.height / this.vb.h);
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
    this.gPulse.innerHTML = '';
    this._countryNodes = [];
    this._cityDots = [];
    this._liveDots = [];
    this._shown = null;
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
    /* Country → what we hold there, for the land tooltip. Built here, off
       the same VISIBLE set the nodes are built from (so a filtered map
       doesn't promise places it isn't showing), and once per data change
       rather than per hover — pointermove fires a lot. */
    this._byCountry = by;
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

    // city dots (+labels), hidden until zoomed. No invisible hit circle
    // any more — the click target is a radius around the centre, computed
    // in _nearestCity, so overlapping targets can't shadow each other.
    for (const p of vis) {
      const g = svgEl('g', { class: 'wmap-city', 'data-id': p.id });
      const f = p._flags || {};
      let cls = 'city-dot';
      if (f.live) cls += ' has-live';
      else if (f.walk) cls += ' has-walk';
      const dot = svgEl('circle', { cx: p._pt.x, cy: p._pt.y, r: 2.4, class: cls });
      const label = svgEl('text', {
        x: p._pt.x, y: p._pt.y, dx: 4, dy: '0.32em', class: 'city-label',
      });
      label.textContent = `${p.emoji || ''} ${p.name}`.trim();
      g.append(dot, label);
      /* Born parked. Only _applyZoomStyling mounts a marker, and only
         when the camera actually contains it — see the note there. */
      g.style.display = 'none';
      this.gDots.appendChild(g);
      /* rx/ry = where this dot is DRAWN, which is its true point until a
         fan pushes it off (see _fanOut). ax/ay = what we last wrote to
         the DOM, so an unfanned dot — almost all of them — costs zero
         attribute writes per frame. */
      const d = { g, dot, label, p, parked: true, fan: null,
        rx: p._pt.x, ry: p._pt.y, ax: p._pt.x, ay: p._pt.y };
      /* A camera that is live RIGHT NOW is the thing this atlas has that
         an atlas doesn't, and it was reading as one more flat red dot.
         It gets a ring that breathes. The ring lives in its own layer,
         not in the city group: _setHot re-appends that group to raise
         it, and a re-append restarts CSS animations — the pulse would
         visibly stutter every time the cursor passed by. */
      if (f.live) {
        d.pulse = svgEl('circle', { cx: p._pt.x, cy: p._pt.y, r: 2.4, class: 'dot-pulse' });
        // negative delay = each ring starts mid-breath, so a cluster of
        // live cams shimmers instead of blinking in lockstep
        d.pulse.style.animationDelay = `-${(this._liveDots.length * 0.37 % 2.4).toFixed(2)}s`;
        this.gPulse.appendChild(d.pulse);
        this._liveDots.push(d);
      }
      this._cityDots.push(d);
    }
    /* Label priority, decided once here rather than per frame. A famous
       place outranks any hidden gem (the +4 beats every flag combined —
       nobody expects Nara's caption to win over Osaka's), then it's
       whoever has more to actually watch. The id tiebreak makes the
       order total and stable, so panning can't leave two neighbours
       swapping captions frame by frame. */
    const rank = ({ tag, _flags: f = {} }) =>
      (tag === 'famous' ? 4 : 0)
      + (f.live ? 1 : 0) + (f.window ? 1 : 0) + (f.walk ? 1 : 0) + (f.monuments ? 1 : 0);
    this._cityDots.sort((a, b) =>
      rank(b.p) - rank(a.p) || String(a.p.id).localeCompare(String(b.p.id)));
    this._buildFans();
    this._hot = null;
    this._applyZoomStyling();
  }

  /* ---------------- fanning stacked places ---------------- */

  /* Who is standing on whose toes. Single-linkage over a grid of FAN_U
     cells: bucket every dot, compare only the 3×3 neighbourhood, union
     anything closer than FAN_U. Once per data change (not per frame),
     and the membership is fixed for the life of that data — a group that
     re-formed as you zoomed would make its dots jump.

     Each member gets a slot on a ring: the smallest radius at which
     ADJACENT slots sit FAN_PX apart. Slots are handed out in order of
     each place's true bearing from the group's centre, so the flower
     keeps the shape the real places have, and sliding onto it never
     makes two members cross over each other.

     `near` is the group's tightest pair — the one that decides whether
     the group still needs fanning at all. */
  _buildFans() {
    this._fans = [];
    const dots = this._cityDots;
    if (!dots || dots.length < 2) return;

    const cells = new Map();
    const key = (x, y) => `${Math.floor(x / FAN_U)}:${Math.floor(y / FAN_U)}`;
    dots.forEach((d, i) => {
      const k = key(d.p._pt.x, d.p._pt.y);
      if (!cells.has(k)) cells.set(k, []);
      cells.get(k).push(i);
    });

    const par = dots.map((_, i) => i);
    const find = a => { while (par[a] !== a) { par[a] = par[par[a]]; a = par[a]; } return a; };
    dots.forEach((d, i) => {
      const cx = Math.floor(d.p._pt.x / FAN_U), cy = Math.floor(d.p._pt.y / FAN_U);
      for (let gx = cx - 1; gx <= cx + 1; gx++) {
        for (let gy = cy - 1; gy <= cy + 1; gy++) {
          for (const j of cells.get(`${gx}:${gy}`) || []) {
            if (j <= i) continue;
            const e = dots[j];
            if (Math.hypot(e.p._pt.x - d.p._pt.x, e.p._pt.y - d.p._pt.y) >= FAN_U) continue;
            const ra = find(i), rb = find(j);
            if (ra !== rb) par[ra] = rb;
          }
        }
      }
    });

    const groups = new Map();
    dots.forEach((d, i) => {
      const r = find(i);
      if (!groups.has(r)) groups.set(r, []);
      groups.get(r).push(d);
    });

    for (const members of groups.values()) {
      const n = members.length;
      if (n < 2) continue;
      const cx = members.reduce((s, d) => s + d.p._pt.x, 0) / n;
      const cy = members.reduce((s, d) => s + d.p._pt.y, 0) / n;
      const ring = FAN_PX / (2 * Math.sin(Math.PI / n));
      const fan = { members, ring, cx, cy, near: Infinity, t: 0 };
      const bys = members
        .map(d => ({ d, a: Math.atan2(d.p._pt.y - cy, d.p._pt.x - cx) }))
        // coincident points have no bearing at all — id keeps the order total
        .sort((u, v) => u.a - v.a || String(u.d.p.id).localeCompare(String(v.d.p.id)));
      const a0 = bys[0].a;
      bys.forEach(({ d }, i) => {
        const a = a0 + (i * 2 * Math.PI) / n;
        d.fan = fan;
        d.fanDir = { x: Math.cos(a), y: Math.sin(a) };
        for (const e of members) {
          if (e === d) continue;
          fan.near = Math.min(fan.near,
            Math.hypot(e.p._pt.x - d.p._pt.x, e.p._pt.y - d.p._pt.y));
        }
        /* The hairline home. Drawn UNDER its own dot, and only while the
           dot is actually off its mark — a fan you can't trace is just a
           map that lies about where things are. */
        const { x, y } = d.p._pt;
        d.leader = svgEl('line', {
          x1: x, y1: y, x2: x, y2: y, class: 'city-leader',
          'vector-effect': 'non-scaling-stroke',
        });
        d.leader.style.display = 'none';
        d.g.insertBefore(d.leader, d.g.firstChild);
      });
      this._fans.push(fan);
    }
  }

  /* Where each fanned dot sits at this zoom: somewhere on the line from
     where it really is to its slot on the ring. Pure geometry, no DOM —
     the writes happen in _applyZoomStyling with everything else, and
     only for dots whose position actually moved.

     ONE t for the whole group, not one per member. A per-member push
     looks tempting (leave the members that already have room alone) but
     it lets a crowded dot be flung onto a slot that a roomy one is
     already sitting in — Victoria Peak landed on Cheung Chau at k≈38,
     which is the bug this whole thing exists to kill. Moving together
     preserves the bearing order the slots were dealt in, so members can
     never cross, and at t=1 the ring guarantees the spacing outright. */
  _fanOut(u) {
    for (const fan of this._fans || []) {
      // 1 while the group's tightest pair is still inside FAN_PX of each
      // other, easing off to 0 as the zoom opens FAN_OFF_PX between them
      const near = fan.near / u;                        // in screen pixels
      const t = Math.max(0, Math.min(1,
        (FAN_OFF_PX - near) / (FAN_OFF_PX - FAN_PX)));
      fan.t = t;
      for (const d of fan.members) {
        const { x, y } = d.p._pt;
        if (!t) { d.rx = x; d.ry = y; continue; }
        d.rx = x + (fan.cx + d.fanDir.x * fan.ring * u - x) * t;
        d.ry = y + (fan.cy + d.fanDir.y * fan.ring * u - y) * t;
      }
    }
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
    this._showLabels = showLabels;
    if (this._cityDots) {
      /* Pinned in screen pixels. The old `max(1.6, 3.4/√k)` floor was in
         MAP units, so past k≈4.5 every dot grew linearly with the zoom
         and neighbouring cities merged into one blob you couldn't aim at. */
      const u = this._u;
      const r = DOT_PX * u;
      this._hitR = HIT_PX * u;
      const fs = 11 / k;
      // decide where the stacked ones sit before anything measures them
      this._fanOut(u);
      /* ONLY what's on screen. This used to walk all ~377 dots and write
         four attributes to each, every frame of every tween, to restyle
         the ~340 of them the viewBox had clipped away — the single
         biggest cost in the engine. Anything entering view is restyled
         in the same frame the camera brings it in, before paint.

         Whatever LEAVES has to be parked, though, and that part is a
         correctness rule rather than a saving: a marker we stop
         restyling keeps the size it last had, in MAP units, and a dot
         sized for the world view is ~3 units across — at k=40 that is a
         200px disc. Tokyo, sitting just past the top edge, painted a red
         blob over the Kanto coast; a stale caption would have bled its
         halo in the same way. Off-screen markers aren't drawn at all
         now, so the size they're holding cannot leak in. */
      const inView = this._inView();
      const keep = new Set(inView);
      for (const d of this._shown || []) {
        if (keep.has(d)) continue;
        d.g.style.display = 'none';
        d.parked = true;
      }
      this._shown = inView;
      for (const d of inView) {
        if (d.parked) { d.g.style.display = ''; d.parked = false; }
        d.dot.setAttribute('r', r);
        /* Only a fanned dot ever moves off its projected point, and only
           while the fan is open — so this costs nothing at all for the
           ~500 places that aren't stacked on anything. */
        if (d.rx !== d.ax || d.ry !== d.ay) {
          d.ax = d.rx; d.ay = d.ry;
          d.dot.setAttribute('cx', d.rx);
          d.dot.setAttribute('cy', d.ry);
          d.label.setAttribute('x', d.rx);
          d.label.setAttribute('y', d.ry);
          if (d.pulse) { d.pulse.setAttribute('cx', d.rx); d.pulse.setAttribute('cy', d.ry); }
          const off = d.fan.t > 0.02;
          d.leader.style.display = off ? '' : 'none';
          if (off) { d.leader.setAttribute('x2', d.rx); d.leader.setAttribute('y2', d.ry); }
        }
        if (showLabels) {
          d.label.setAttribute('font-size', fs);
          /* The halo is a STROKE on the text, so it lives in map units
             like everything else and has to be re-pinned every zoom —
             a fixed 2.5 in the stylesheet became a 100px black slab at
             k=40. Inline style: it has to beat the sheet's value. */
          d.label.style.strokeWidth = `${HALO_PX * u}px`;
        } else {
          d.labelHidden = true;
          d.label.style.display = 'none';
        }
      }
      if (showLabels) this._placeLabels(fs, r, inView);
      this._pulses(cityMode, r);
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
    // a pinned (keyboard) tooltip rides along with the marker it names
    if (this._tipPin) this._tipMove(this._mapToClient(this._tipPin.x, this._tipPin.y));
  }

  /* The dots inside the viewBox, padded a little so nothing pops the
     instant it clears an edge. Every per-frame loop over places goes
     through here — the atlas is 377 places, a view is ~40. */
  _inView(dots = this._cityDots) {
    const vb = this.vb;
    const mx = vb.w * VIEW_PAD, my = vb.h * VIEW_PAD;
    const x0 = vb.x - mx, x1 = vb.x + vb.w + mx;
    const y0 = vb.y - my, y1 = vb.y + vb.h + my;
    const out = [];
    for (const d of dots || []) {
      // drawn position, so a fanned dot pushed over the edge still counts
      if (d.rx >= x0 && d.rx <= x1 && d.ry >= y0 && d.ry <= y1) out.push(d);
    }
    return out;
  }

  /* "Live" was reading as one more coloured dot. Now a live cam breathes
     — but only where it can be seen. An infinite animation on every live
     dot in the atlas is the background work this engine refuses to do;
     the handful on screen is affordable, and under
     prefers-reduced-motion none of them mount at all. */
  _pulses(cityMode, r) {
    if (!this._liveDots) return;
    const ok = cityMode && this._pulseOK;
    const vb = this.vb;
    const mx = vb.w * VIEW_PAD, my = vb.h * VIEW_PAD;
    for (const d of this._liveDots) {
      const { x, y } = d.p._pt;
      const on = ok
        && x >= vb.x - mx && x <= vb.x + vb.w + mx
        && y >= vb.y - my && y <= vb.y + vb.h + my;
      if (on) d.pulse.setAttribute('r', r);
      if (d.pulsing === on) continue;   // don't touch the DOM to say nothing
      d.pulsing = on;
      d.pulse.classList.toggle('on', on);
    }
  }

  /* Which captions actually get printed. Two names a few pixels apart
     used to overprint each other ("Osaka" struck through "Nara"), and a
     long one would lie across its neighbour's dot — the same complaint
     as the old giant halo, just one layer down.

     Rule: every dot in view claims its own patch FIRST — a caption may
     cover another caption, it may never cover a place you could have
     clicked. Then names go out in priority order, each trying the slots
     in LABEL_SLOTS around its own dot and taking the first one that is
     clear. A name with nowhere clean to sit is simply not drawn: that
     place keeps its dot, its tooltip and its click target, and gets its
     name back the moment you hover it.

     SIXTEEN slots, not two (2026-08). Right-then-left along a single
     row is exactly why Mount Wilson Observatory had no name until you
     were most of the way to K_MAX: it sits in a chain of eight places
     strung along one line of latitude — Santa Monica · Los Angeles ·
     Griffith · Mount Wilson · Big Bear · Joshua Tree · Palomar · San
     Diego — where every caption is 15-20 map units wide inside a
     125-unit viewport. On one row the first name printed eats every
     position the rest of the chain could have used, and the ones that
     lose are the ones with the longest names, which are the
     observatories. Stacking rows is what a chain like that needs; it's
     also just how an atlas draws them. Over a sweep of 140 random
     viewports: 64% of in-view places named → 80%, and Mount Wilson is
     named continuously from k≈7 instead of appearing at k≈30.

     Boxes are ESTIMATED from the character count, never measured:
     getBBox() on a few hundred <text> nodes would force a layout flush
     on every tween frame — exactly the thrash this engine exists to
     avoid — and an estimate is plenty to spot an overlap.

     Eight times the slots would have been eight times the collision
     tests, so the claimed boxes are indexed by horizontal BAND rather
     than scanned end to end. A caption is one line tall and a viewport
     is ~50 lines, so a candidate only ever compares against the two or
     three bands it actually crosses. The worst frame in that same sweep
     went from 39k tests to 11k — the richer placement is cheaper than
     the old one was. */
  _placeLabels(fs, r, inView) {
    const hits = (a, b) => a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1;
    const gap = r * 1.8;
    const step = r + fs * 0.95;              // one caption-height of vertical travel
    const band = Math.max(fs * 1.1, r * 2);  // index bucket, ~one caption tall
    const bands = new Map();
    const claim = b => {
      for (let i = Math.floor(b.y0 / band); i <= Math.floor(b.y1 / band); i++) {
        const cell = bands.get(i);
        if (cell) cell.push(b); else bands.set(i, [b]);
      }
    };
    const free = c => {
      for (let i = Math.floor(c.y0 / band); i <= Math.floor(c.y1 / band); i++) {
        for (const b of bands.get(i) || []) if (hits(c, b)) return false;
      }
      return true;
    };
    // every dot claims its own patch before a single caption is placed
    for (const d of inView) claim({ x0: d.rx - r, y0: d.ry - r, x1: d.rx + r, y1: d.ry + r });

    let placed = 0;
    for (const d of inView) {
      const x = d.rx, y = d.ry;
      const w = ([...d.label.textContent].length + 1) * fs * 0.58;
      let box = null, side = 1, vy = 0;
      if (placed < LABEL_CAP) {
        for (const [s, row] of LABEL_SLOTS) {
          const dy = row * step;
          const cand = s > 0 ? { x0: x + gap, x1: x + gap + w }
            : s < 0 ? { x0: x - gap - w, x1: x - gap }
              : { x0: x - w / 2, x1: x + w / 2 };
          cand.y0 = y - fs * 0.62 + dy;
          cand.y1 = y + fs * 0.42 + dy;
          if (!free(cand)) continue;
          box = cand; side = s; vy = dy;
          break;
        }
      }
      // no slot? fall back beside the dot, so a hover-revealed name is sane
      d.label.setAttribute('dx', side > 0 ? gap : side < 0 ? -gap : 0);
      d.label.setAttribute('text-anchor', side > 0 ? 'start' : side < 0 ? 'end' : 'middle');
      /* dy rides in em so it tracks font-size for free; 0.32 is the
         vertical centring the marker was born with, vy/fs the row. */
      d.label.setAttribute('dy', `${(0.32 + vy / fs).toFixed(3)}em`);
      if (box) { claim(box); placed++; }
      d.labelHidden = !box;
      d.label.style.display = box ? '' : 'none';
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

  setMode(m) {
    this.mode = m;
    this.container.classList.toggle('wmap-pick', m === 'pick');
  }

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
    /* Don't overshoot into the ground. A fixed floor, NOT one derived
       from K_MAX: raising the ceiling so a stacked cluster can be pulled
       apart by hand must not also make every one-place country click
       dive twice as deep as it used to. */
    w = Math.max(w, FIT_MIN_W);
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

  /* The exact inverse — where a map point is on screen right now. Shaped
     like a pointer event so anything taking one (_tipMove) takes this. */
  _mapToClient(x, y) {
    const r = this.svg.getBoundingClientRect();
    const scale = Math.min(r.width / this.vb.w, r.height / this.vb.h);
    const ox = (r.width - this.vb.w * scale) / 2;
    const oy = (r.height - this.vb.h * scale) / 2;
    return {
      clientX: r.left + ox + (x - this.vb.x) * scale,
      clientY: r.top + oy + (y - this.vb.y) * scale,
    };
  }

  /* Zoom to `w` map units wide, keeping the map point `anchor` under the
     screen fraction `fx,fy` of the viewBox. Wheel, pinch and the +/-
     keys are all this, differing only in where they anchor. */
  _zoomTo(w, anchor, fx, fy) {
    w = Math.min(MAP_W, Math.max(MAP_W / K_MAX, w));
    const h = w * (MAP_H / MAP_W);
    if (this._anim) { cancelAnimationFrame(this._anim); this._anim = null; }
    this._setVb(anchor.x - fx * w, anchor.y - fy * h, w, h);
  }

  /* The same zoom, anchored on a client point (cursor, pinch midpoint). */
  _zoomAt(w, ev) {
    const pt = this._clientToMap(ev);
    this._zoomTo(w, pt, (pt.x - this.vb.x) / this.vb.w, (pt.y - this.vb.y) / this.vb.h);
  }

  _bind() {
    const c = this.container;
    let drag = null, moved = false;
    /* Live pointers, by id. One is a drag; two are a pinch. Touch was
       pan-only before this — `wheel` never fires from fingers, so a
       phone could reach the country nodes and no further. */
    const pts = new Map();
    let pinch = null;
    const mid = () => {
      const [a, b] = [...pts.values()];
      return { clientX: (a.x + b.x) / 2, clientY: (a.y + b.y) / 2,
               d: Math.hypot(a.x - b.x, a.y - b.y) };
    };

    c.addEventListener('pointerdown', ev => {
      if (ev.pointerType === 'mouse' && ev.button !== 0) return;
      pts.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
      try { c.setPointerCapture(ev.pointerId); } catch { /* synthetic events */ }
      if (pts.size === 2) {
        // grab the map point under the midpoint and hold it there
        const m = mid();
        pinch = { d: m.d, w: this.vb.w, at: this._clientToMap(m) };
        drag = null;
        moved = true;                       // a pinch is never a click
      } else if (pts.size === 1) {
        drag = { px: ev.clientX, py: ev.clientY, vb: { ...this.vb } };
        moved = false;
      }
    });
    c.addEventListener('pointermove', ev => {
      if (pts.has(ev.pointerId)) pts.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
      if (pinch && pts.size >= 2) {
        const m = mid();
        if (m.d < 8 || pinch.d < 8) return;          // fingers too close to divide
        const cur = this._clientToMap(m);
        this._zoomTo(pinch.w * (pinch.d / m.d), pinch.at,
          (cur.x - this.vb.x) / this.vb.w, (cur.y - this.vb.y) / this.vb.h);
        return;
      }
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
    const lift = ev => {
      const wasClick = drag && !moved;
      pts.delete(ev.pointerId);
      if (pinch && pts.size < 2) {
        pinch = null;
        // one finger left: re-seat the drag under it, or the map jumps
        const [rest] = [...pts.values()];
        drag = rest ? { px: rest.x, py: rest.y, vb: { ...this.vb } } : null;
      } else if (pts.size === 0) {
        if (wasClick) this._click(ev);
        drag = null;
      }
    };
    c.addEventListener('pointerup', lift);
    c.addEventListener('pointercancel', ev => {
      pts.delete(ev.pointerId);
      if (pts.size < 2) pinch = null;
      if (pts.size === 0) drag = null;
    });
    c.addEventListener('pointerleave', () => { this._tipHide(); this._setHot(null); });

    c.addEventListener('wheel', ev => {
      ev.preventDefault();
      this._zoomAt(this.vb.w * (ev.deltaY < 0 ? 0.82 : 1.22), ev);
    }, { passive: false });

    c.addEventListener('dblclick', ev => {
      const pt = this._clientToMap(ev);
      const w = Math.max(MAP_W / K_MAX, this.vb.w * 0.45);
      const h = w * (MAP_H / MAP_W);
      this._glide(pt.x - w / 2, pt.y - h / 2, w, 420);
    });

    c.addEventListener('keydown', ev => this._key(ev));
    c.addEventListener('blur', () => { this._tipHide(); this._setHot(null); });
  }

  /* Keyboard parity. Arrows pan, +/- zoom on the centre, 0 goes home,
     n/p walk the places in view (reusing the very same highlight the
     cursor drives, so what you hear is what a click would take), Enter
     opens the highlighted one. */
  _key(ev) {
    const pan = (dx, dy) => {
      if (this._anim) { cancelAnimationFrame(this._anim); this._anim = null; }
      this._setVb(this.vb.x + this.vb.w * PAN_STEP * dx,
        this.vb.y + this.vb.h * PAN_STEP * dy, this.vb.w, this.vb.h);
    };
    const zoom = f => this._zoomTo(this.vb.w * f,
      { x: this.vb.x + this.vb.w / 2, y: this.vb.y + this.vb.h / 2 }, 0.5, 0.5);

    switch (ev.key) {
      case 'ArrowLeft': pan(-1, 0); break;
      case 'ArrowRight': pan(1, 0); break;
      case 'ArrowUp': pan(0, -1); break;
      case 'ArrowDown': pan(0, 1); break;
      case '+': case '=': zoom(0.7); break;
      case '-': case '_': zoom(1 / 0.7); break;
      case '0': this.reset(); break;
      case 'n': case 'N': this._step(1); break;
      case 'p': case 'P': this._step(-1); break;
      case 'Enter': case ' ': {
        ev.preventDefault();                 // Space scrolls the page otherwise
        if (this.mode === 'pick') {
          // the crosshair is the middle of the view: pan it onto your
          // guess, then commit. Same contract as a click.
          const { lat, lng } = unproject(this.vb.x + this.vb.w / 2, this.vb.y + this.vb.h / 2);
          if (Math.abs(lat) <= 90 && Math.abs(lng) <= 180) this.opts.onPick?.({ lat, lng });
          return;
        }
        const hot = this._hot;
        if (!hot) return;
        if (hot.p) this.opts.onPlaceClick?.(hot.p);
        else if (hot.country) {
          this.opts.onCountryClick?.(hot.country, hot.list);
          this.flyToPlaces(hot.list, 700, true);
        }
        return;
      }
      case 'Escape': this._setHot(null, true); this._tipHide(); return;
      default: return;
    }
    ev.preventDefault();
  }

  /* Step the highlight to the next/previous marker in view — city dots
     when we're zoomed in, country nodes when we're not. Ordered by
     position (top-left to bottom-right) rather than by the label
     priority the array is sorted in, because "next" should mean the
     next one across the screen. */
  _step(dir) {
    const order = (a, b) => (a.cy ?? a.ry) - (b.cy ?? b.ry)
      || (a.cx ?? a.rx) - (b.cx ?? b.rx);
    const list = this.k >= COUNTRY_K
      ? this._inView().sort(order)
      : (this._countryNodes || []).slice().sort(order);
    if (!list.length) return;
    const at = list.indexOf(this._hot);
    // nothing highlighted yet: n starts at the top-left, p at the end
    const next = at < 0
      ? list[dir > 0 ? 0 : list.length - 1]
      : list[(at + dir + list.length) % list.length];
    this._setHot(next, true);
    const x = next.cx ?? next.rx, y = next.cy ?? next.ry;
    this._tipShow(this._mapToClient(x, y), this._tipFor(next), { x, y });
    /* Nudge the camera only if the target sits outside the real viewBox
       — _inView is padded, so "in view" can still mean just off-screen. */
    const { vb } = this;
    if (x < vb.x || x > vb.x + vb.w || y < vb.y || y > vb.y + vb.h) {
      this._glide(x - vb.w / 2, y - vb.h / 2, vb.w, 300);
    }
  }

  /* The city dot whose centre is nearest `pt`, within the tap radius.
     Nearest-centre — not topmost-painted — is the whole fix: every dot
     owns the patch of map that is closer to it than to any neighbour,
     so a tight cluster (Osaka/Kyoto/Kobe, Toronto/Hamilton/Niagara)
     splits cleanly instead of the last-drawn dot taking every click. */
  _nearestCity(pt) {
    let best = null, bd = (this._hitR || 6) ** 2;
    for (const d of this._cityDots || []) {
      // rx/ry, not the projected point: you aim at the dot you can see,
      // and a fanned dot is not where its place is
      const q = (d.rx - pt.x) ** 2 + (d.ry - pt.y) ** 2;
      if (q <= bd) { bd = q; best = d; }
    }
    return best;
  }

  /* Same rule for the world-view country nodes, each within its own halo. */
  _nearestCountryNode(pt) {
    let best = null, bd = Infinity;
    for (const n of this._countryNodes || []) {
      const q = (n.cx - pt.x) ** 2 + (n.cy - pt.y) ** 2;
      if (q <= n.r0 ** 2 && q < bd) { bd = q; best = n; }
    }
    return best;
  }

  _pickTarget(ev) {
    // Markers resolve geometrically (see _nearestCity). elementFromPoint
    // is kept only for the land/sea fallback, where the target really is
    // an arbitrary country path — and it can be trusted there now that
    // dots and nodes are pointer-events:none and no longer cover it.
    // (ev.target is still never usable: during pointer capture every
    // event retargets to the container.)
    const pt = this._clientToMap(ev);
    if (this.k >= COUNTRY_K) {
      const hit = this._nearestCity(pt);
      if (hit) return { type: 'city', place: hit.p, dot: hit };
    } else {
      const hit = this._nearestCountryNode(pt);
      if (hit) return { type: 'country', country: hit.country, list: hit.list, node: hit };
    }
    const under = document.elementFromPoint(ev.clientX, ev.clientY);
    const land = under && under.closest('.wmap-land path');
    if (land) return { type: 'land', name: land.getAttribute('data-name') };
    return { type: 'sea' };
  }

  /* Highlight exactly what a click would take, and lift it above its
     neighbours so its label is readable. CSS :hover can't do this any
     more: the dot under the cursor and the dot that owns the click are
     different elements inside a cluster, and highlighting the wrong one
     is worse than highlighting none. */
  _setHot(hit, say = false) {
    if (this._hot === hit) return;
    if (this._hot) {
      this._hot.g.classList.remove('wm-hot');
      // a caption _placeLabels dropped goes back into hiding on the way out
      if (this._hot.labelHidden) this._hot.label.style.display = 'none';
      this._setKin(this._hot, false);
    }
    this._hot = hit || null;
    if (hit) {
      hit.g.classList.add('wm-hot');
      // whatever the cursor owns is named, decluttered or not
      if (this._showLabels && hit.label) hit.label.style.display = '';
      hit.g.parentNode.appendChild(hit.g);   // re-append = drawn last = on top
      this._setKin(hit, true);
    }
    /* Only the keyboard walk speaks. A live region that fired on every
       pointermove would narrate the whole map at anyone who happens to
       run a screen reader with a mouse in hand. */
    if (say) this.live.textContent = hit ? this._sayText(hit) : '';
  }

  /* Light up the rest of a fanned group with whichever of them the
     highlight is on. Three dots over Cape Town are one place to the eye,
     and touching any of them should say so — the siblings' leaders
     brighten and their names come back, decluttered or not, which is
     usually how you find out there were three at all. */
  _setKin(hit, on) {
    if (!hit || !hit.fan) return;
    for (const m of hit.fan.members) {
      if (m === hit) continue;
      m.g.classList.toggle('wm-kin', on);
      if (on) { if (this._showLabels) m.label.style.display = ''; }
      else if (m.labelHidden) m.label.style.display = 'none';
    }
  }

  /* What the highlight is, in words. The flags are emoji in the tooltip,
     which a screen reader would read as "large red circle". */
  _sayText(hit) {
    if (hit.p) {
      const f = hit.p._flags || {};
      const bits = [f.live && 'live cam', f.window && 'window view',
        f.walk && 'walking tour', f.monuments && 'monuments'].filter(Boolean);
      const kin = hit.fan && hit.fan.t > 0.02 ? hit.fan.members.length - 1 : 0;
      return `${hit.p.name}, ${hit.p.country}${bits.length ? `. ${bits.join(', ')}` : ''}`
        + (kin ? `. ${kin} more place${kin === 1 ? '' : 's'} within a few kilometres` : '');
    }
    return `${hit.country}, ${hit.list.length} place${hit.list.length === 1 ? '' : 's'}`;
  }

  /* Tooltip copy for a marker, shared by hover and the keyboard walk. */
  _tipFor(hit) {
    if (hit.p) {
      const f = hit.p._flags || {};
      const tags = [f.live && '🔴', f.window && '🪟', f.walk && '🚶', f.monuments && '🏛️']
        .filter(Boolean).join(' ');
      // a fanned dot isn't drawn where its place is; the tip owns up to it
      const kin = hit.fan && hit.fan.t > 0.02 ? hit.fan.members.length - 1 : 0;
      return `${hit.p.emoji || '📍'} <b>${hit.p.name}</b> · ${hit.p.country}`
        + (tags ? ` &nbsp;${tags}` : '')
        + (kin ? `<i class="tip-fan">+${kin} nearby, nudged apart</i>` : '');
    }
    // one-place countries get named outright — a bare "Chile · 1 place"
    // node sitting on Easter Island looks like a bug
    return hit.list.length === 1
      ? `${hit.list[0].emoji || '📍'} <b>${hit.list[0].name}</b> · ${hit.country} — click to explore`
      : `<b>${hit.country}</b> · ${hit.list.length} places — click to explore`;
  }

  /* Which country that land belongs to, and what we have there. Once
     you're past COUNTRY_K the gold nodes are gone and the coastline is
     the only clue left — fine over Italy, useless over the Balkans. */
  _landTip(raw) {
    const name = LAND_ALIAS[raw] || raw;
    const list = this._byCountry?.get(name);
    if (!list) return `<b>${name}</b>`;
    const flag = list[0].country_flag || '';
    return `${flag} <b>${name}</b> · ${list.length} place${list.length === 1 ? '' : 's'}`.trim();
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
    this._setHot(t.type === 'city' ? t.dot : t.type === 'country' ? t.node : null);
    if (t.type === 'city' || t.type === 'country') {
      this._tipShow(ev, this._tipFor(t.type === 'city' ? t.dot : t.node));
      this.container.style.cursor = 'pointer';
    } else if (this.mode === 'pick') {
      // NEVER name the land here: the whole game is not knowing where
      // you are. This branch sits above the land one for that reason.
      this.container.style.cursor = 'crosshair';
      this._tipHide();
    } else if (t.type === 'land' && this.k >= COUNTRY_K) {
      this._tipShow(ev, this._landTip(t.name));
      this.container.style.cursor = 'grab';
    } else {
      this.container.style.cursor = 'grab';
      this._tipHide();
    }
  }

  /* Show the tooltip against a client point. `pin` (map coords) makes it
     STICK to that spot on the map instead: the keyboard walk names a
     marker that may still be gliding into view, and a tip parked at the
     coords it had when the glide started would spend it in the wrong
     place. Pinned tips are re-seated from _applyZoomStyling, i.e. once a
     frame, but only while one is up. */
  _tipShow(ev, html, pin = null) {
    this.tip.innerHTML = html;
    this.tip.style.display = 'block';
    this._tipPin = pin;
    this._tipMove(ev);
  }
  _tipMove(ev) {
    const r = this.container.getBoundingClientRect();
    const x = Math.min(ev.clientX - r.left + 14, r.width - 220);
    const y = Math.max(ev.clientY - r.top - 34, 8);
    this.tip.style.transform = `translate(${x}px, ${y}px)`;
  }
  _tipHide() { this.tip.style.display = 'none'; this._tipPin = null; }
}
