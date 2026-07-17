/* ============================================================
   HOME — hero search, the world map, destination rails.
   ============================================================ */
import { loadAll, search } from '../lib/data.js';
import { sceneFlags } from '../lib/media.js';
import { State } from '../lib/state.js';
import { WorldMap } from '../worldmap.js';
import { el, qs } from '../lib/dom.js';
import { lazyPhoto } from '../lib/photos.js';

const go = p => { location.href = `location.html?id=${encodeURIComponent(p.id)}`; };

function toast(msg) {
  const t = qs('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._h);
  t._h = setTimeout(() => t.classList.remove('show'), 2600);
}

/* ---------------- place card ---------------- */
function placeCard(p) {
  const f = p._flags;
  const card = el('a', { class: 'card place-card', href: `location.html?id=${encodeURIComponent(p.id)}` },
    el('div', { class: 'ph' }, p.emoji || '📍'),
    el('div', { class: 'badges' },
      f.live ? el('span', { class: 'badge badge-live' }, el('span', { class: 'dot' }), 'Live') : null,
      f.window ? el('span', { class: 'badge badge-window' }, '🪟') : null,
      f.walk ? el('span', { class: 'badge badge-walk' }, '🚶') : null,
      f.monuments ? el('span', { class: 'badge badge-monu' }, '🏛️') : null,
    ),
    State.isVisited(p.id) ? el('span', { class: 'stamp', title: 'Visited' }, '📘') : null,
    el('div', { class: 'meta' },
      el('div', { class: 'name' }, p.name),
      el('div', { class: 'sub' }, `${p.country_flag || ''} ${p.country}`.trim()),
    ),
  );
  lazyPhoto(card.querySelector('.ph'), p, 480);
  return card;
}

function rail(title, list, note) {
  if (!list.length) return null;
  return el('div', { class: 'rail-block' },
    el('div', { class: 'rail-head' },
      el('h2', {}, title),
      el('span', { class: 'count' }, note || `${list.length} places`),
    ),
    el('div', { class: 'rail' }, list.map(placeCard)),
  );
}

/* ---------------- boot ---------------- */
async function boot() {
  const places = (await loadAll()).map(p => ({ ...p, _flags: sceneFlags(p) }));
  const rnd = a => a[Math.floor(Math.random() * a.length)];

  /* hero stats */
  const nLive = places.filter(p => p._flags.live).length;
  const nWalk = places.filter(p => p._flags.walk).length;
  const nCountries = new Set(places.map(p => p.country)).size;
  qs('#hero-stats').append(
    el('span', {}, el('b', {}, String(places.length)), ' places'),
    el('span', {}, el('b', {}, String(nCountries)), ' countries'),
    el('span', { class: 'live' }, el('b', {}, String(nLive)), ' live cams'),
    el('span', {}, el('b', {}, String(nWalk)), ' walking tours'),
  );
  qs('#foot-stats').textContent =
    `${places.length} places · ${nCountries} countries · ${State.visited.length} visited`;

  /* surprise */
  qs('#surprise-top').addEventListener('click', () => go(rnd(places)));

  /* ---------------- search ---------------- */
  const input = qs('#search'), sug = qs('#suggest');
  let hot = -1, results = [];
  const render = () => {
    sug.innerHTML = '';
    results.forEach((r, i) => {
      const f = r.p._flags;
      sug.append(el('button', {
        class: 'suggest-item' + (i === hot ? ' hot' : ''), role: 'option',
        onclick: () => go(r.p),
      },
        el('span', { class: 's-emoji' }, r.p.emoji || '📍'),
        el('span', {},
          el('span', { class: 's-name' }, r.p.name),
          ' ',
          el('span', { class: 's-sub' }, r.label ? `${r.label} · ${r.p.country}` : r.p.country),
        ),
        el('span', { class: 's-badges' },
          f.live ? '🔴' : '', f.window ? '🪟' : '', f.walk ? '🚶' : '', f.monuments ? '🏛️' : ''),
      ));
    });
    input.setAttribute('aria-expanded', results.length ? 'true' : 'false');
  };
  input.addEventListener('input', () => {
    results = search(places, input.value); hot = -1; render();
  });
  input.addEventListener('keydown', ev => {
    if (ev.key === 'ArrowDown') { hot = Math.min(hot + 1, results.length - 1); render(); ev.preventDefault(); }
    else if (ev.key === 'ArrowUp') { hot = Math.max(hot - 1, -1); render(); ev.preventDefault(); }
    else if (ev.key === 'Enter' && results.length) go(results[Math.max(hot, 0)].p);
    else if (ev.key === 'Escape') { results = []; render(); }
  });
  document.addEventListener('click', ev => {
    if (!ev.target.closest('.hero-search')) { results = []; render(); }
  });

  /* ---------------- map ---------------- */
  const map = new WorldMap(qs('#worldmap'), {
    onPlaceClick: go,
    onCountryClick: name => { qs('#map-hint').textContent = `${name} — click a dot to arrive`; },
  });
  await map.loadWorld();
  map.setPlaces(places);

  qs('#zoom-in').addEventListener('click', () => {
    const { x, y, w, h } = map.vb;
    map._glide(x + w * 0.175, y + h * 0.175, w * 0.65, 300);
  });
  qs('#zoom-out').addEventListener('click', () => {
    const { x, y, w, h } = map.vb;
    map._glide(x - w * 0.27, y - h * 0.27, Math.min(1000, w * 1.54), 300);
  });
  qs('#zoom-reset').addEventListener('click', () => map.reset());

  /* map filters */
  const filters = {
    all: null,
    walk: p => p._flags.walk,
    live: p => p._flags.live,
    window: p => p._flags.window,
    monuments: p => p._flags.monuments,
    saved: p => State.isSaved(p.id),
    ancient: p => p.region_id === 'ancient',
    // wildlife = the wild collection + any nature place with a live cam
    // (kruger, maasai mara, yellowstone live via the media.json pipeline)
    wild: p => p.region_id === 'wild' || (p.type === 'nature' && p._flags.live),
  };
  qs('#map-filters').addEventListener('click', ev => {
    const b = ev.target.closest('.chip');
    if (!b) return;
    for (const c of qs('#map-filters').children) c.classList.toggle('active', c === b);
    map.setFilter(filters[b.dataset.f] || null);
    const vis = filters[b.dataset.f] ? places.filter(filters[b.dataset.f]).length : places.length;
    qs('#map-hint').textContent = b.dataset.f === 'all'
      ? 'Click a gold node to enter a country'
      : `${vis} place${vis === 1 ? '' : 's'} match`;
    if (b.dataset.f === 'saved' && !vis) toast('Nothing saved yet — ♥ a place on its page.');
  });

  /* ---------------- rails ---------------- */
  const shuffled = a => [...a].sort(() => Math.random() - 0.5);
  const railsEl = qs('#rails');
  const fullyLoaded = shuffled(places.filter(p => p._flags.walk && p._flags.live)).slice(0, 16);
  const liveNow = shuffled(places.filter(p => p._flags.live)).slice(0, 16);
  const walks = shuffled(places.filter(p => p._flags.walk)).slice(0, 16);
  const monus = shuffled(places.filter(p => p._flags.monuments)).slice(0, 16);
  const saved = places.filter(p => State.isSaved(p.id));
  const ancient = shuffled(places.filter(p => p.region_id === 'ancient')).slice(0, 16);
  const wild = shuffled(places.filter(filters.wild)).slice(0, 16);

  railsEl.append(...[
    rail('✨ Start here', fullyLoaded, 'walk + live cam, ready to go'),
    rail('🔴 Live right now', liveNow, 'real cameras, streaming this second'),
    rail('🦁 Wild live cams', wild, 'bears, gorillas, waterholes — streaming now'),
    rail('🚶 Best walking tours', walks, 'seekable, real footage'),
    rail('🏛️ Monumental cities', monus, 'landmark tours inside'),
    saved.length ? rail('♥ Your saved places', saved) : null,
    rail('🤫 Ancient Apocalypse', ancient, 'every site from the series'),
  ].filter(Boolean));

  /* continent rails */
  const byCont = new Map();
  for (const p of places) {
    if (p.region_id === 'ancient') continue;
    const c = p.continent || 'Elsewhere';
    if (!byCont.has(c)) byCont.set(c, []);
    byCont.get(c).push(p);
  }
  for (const [cont, list] of [...byCont.entries()].sort((a, b) => b[1].length - a[1].length)) {
    railsEl.append(rail(cont, shuffled(list).slice(0, 16), `${list.length} places`));
  }
}

boot().catch(err => {
  console.error(err);
  toast('Something broke loading the world — check the console.');
});
