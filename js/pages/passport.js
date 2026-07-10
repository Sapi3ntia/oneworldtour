/* ============================================================
   PASSPORT — stamps, achievements, notes, wishlist.
   ============================================================ */
import { loadAll } from '../lib/data.js';
import { State } from '../lib/state.js';
import { km } from '../lib/geo.js';
import { el, qs } from '../lib/dom.js';

function rankFor(n) {
  if (n >= 100) return 'Master Voyager';
  if (n >= 60) return 'World Explorer';
  if (n >= 30) return 'Jet Setter';
  if (n >= 15) return 'Globetrotter';
  if (n >= 5) return 'Wanderer';
  if (n >= 1) return 'Day Tripper';
  return 'Armchair Traveler';
}

async function boot() {
  const all = await loadAll();
  const visited = State.visited;
  const isV = id => visited.includes(id);
  const byId = Object.fromEntries(all.map(l => [l.id, l]));

  const visitedLocs = all.filter(l => isV(l.id));
  const countries = new Set(visitedLocs.map(l => l.country));
  const continents = new Set(visitedLocs.map(l => l.continent));

  const route = visited.map(id => byId[id]).filter(Boolean);
  let distance = 0;
  for (let i = 1; i < route.length; i++) distance += km(route[i - 1].coordinates, route[i].coordinates);

  qs('#pp-rank').textContent = rankFor(visitedLocs.length);

  const stat = (v, k) => el('div', { class: 'pp-stat' },
    el('div', { class: 'v' }, String(v)), el('div', { class: 'k' }, k));
  qs('#pp-stats').append(
    stat(visitedLocs.length, `of ${all.length} places`),
    stat(countries.size, 'countries'),
    stat(continents.size, 'continents'),
    stat(distance.toLocaleString() + ' km', 'travelled'),
    stat((all.length ? Math.round(visitedLocs.length / all.length * 100) : 0) + '%', 'of the world'),
    stat(State.saved.length, 'wishlisted'),
  );

  /* achievements */
  const n = visitedLocs.length;
  const hidden = visitedLocs.filter(l => l.tag === 'hidden').length;
  const euro = visitedLocs.filter(l => l.continent === 'Europe').length;
  const usa = visitedLocs.filter(l => l.country === 'United States').length;
  const cad = visitedLocs.filter(l => l.country === 'Canada').length;
  const ancient = visitedLocs.filter(l => l.region_id === 'ancient').length;
  const defs = [
    ['🛂', 'First Stamp', n >= 1, 'Visit your first place'],
    ['🧭', 'Pathfinder', n >= 5, `Visit 5 places (${Math.min(n, 5)}/5)`],
    ['🌍', 'Globetrotter', n >= 25, `Visit 25 places (${Math.min(n, 25)}/25)`],
    ['👑', 'Grand Tour', n >= 50, `Visit 50 places (${Math.min(n, 50)}/50)`],
    ['🛃', 'Border Hopper', countries.size >= 5, `Reach 5 countries (${Math.min(countries.size, 5)}/5)`],
    ['🌐', 'Continental', continents.size >= 3, `Explore 3 continents (${Math.min(continents.size, 3)}/3)`],
    ['🗺️', 'Off the Beaten Path', hidden >= 5, `Find 5 hidden gems (${Math.min(hidden, 5)}/5)`],
    ['🇪🇺', 'Euro Trip', euro >= 10, `Visit 10 European spots (${Math.min(euro, 10)}/10)`],
    ['🦅', 'Coast to Coast', usa >= 10, `Visit 10 US spots (${Math.min(usa, 10)}/10)`],
    ['🍁', 'True North', cad >= 6, `Visit 6 Canadian spots (${Math.min(cad, 6)}/6)`],
    ['🤫', 'Alternative Historian', ancient >= 5, `See 5 Ancient Apocalypse sites (${Math.min(ancient, 5)}/5)`],
    ['♥', 'Dreamer', State.saved.length >= 5, `Save 5 places (${Math.min(State.saved.length, 5)}/5)`],
    ['✅', 'Completionist', n >= all.length && all.length > 0, `See the whole world (${n}/${all.length})`],
  ];
  qs('#ach-count').textContent = `${defs.filter(d => d[2]).length} of ${defs.length} earned`;
  qs('#ach-grid').append(...defs.map(([i, name, ok, hint]) =>
    el('div', { class: 'ach ' + (ok ? 'earned' : 'locked'), title: hint },
      el('div', { class: 'i' }, i), el('div', { class: 'n' }, name), el('div', { class: 'h' }, hint))));

  if (!visitedLocs.length) qs('#pp-empty').hidden = false;

  /* stamps grouped by country, most complete first */
  const byCountry = {};
  for (const l of all) (byCountry[l.country] ||= []).push(l);
  const started = Object.keys(byCountry)
    .filter(c => byCountry[c].some(l => isV(l.id)))
    .sort((a, b) => {
      const va = byCountry[a].filter(l => isV(l.id)).length;
      const vb = byCountry[b].filter(l => isV(l.id)).length;
      return vb - va || a.localeCompare(b);
    });

  const cWrap = qs('#pp-countries');
  for (const country of started) {
    const list = byCountry[country];
    const done = list.filter(l => isV(l.id));
    const sec = el('section', { class: 'pp-country' },
      el('h3', {}, `${list[0].country_flag || '🌍'} ${country} `,
        el('span', { class: 'prog' }, `${done.length} / ${list.length}`)),
      el('div', { class: 'stamp-grid' },
        list.filter(l => isV(l.id)).map(l => el('a', {
          class: 'stamp v', href: `location.html?id=${encodeURIComponent(l.id)}`,
        },
          el('div', { class: 's-name' }, `${l.emoji || ''} ${l.name}`),
          el('div', { class: 's-sub' }, l.region || l.province || l.continent || ''),
          el('span', { class: 's-mark' }, '📘'),
          State.getNote(l.id) ? el('div', { class: 's-note' }, State.getNote(l.id)) : null,
        ))),
    );
    cWrap.append(sec);
  }

  /* wishlist */
  const saved = all.filter(l => State.isSaved(l.id));
  if (saved.length) {
    qs('#pp-wishlist').append(
      el('div', { class: 'section-head' }, el('h2', {}, '♥ Wishlist')),
      el('div', { class: 'stamp-grid' },
        saved.map(l => el('a', {
          class: 'stamp' + (isV(l.id) ? ' v' : ''), href: `location.html?id=${encodeURIComponent(l.id)}`,
        },
          el('div', { class: 's-name' }, `${l.emoji || ''} ${l.name}`),
          el('div', { class: 's-sub' }, `${l.country_flag || ''} ${l.country}`),
          isV(l.id) ? el('span', { class: 's-mark' }, '📘') : null,
        ))),
    );
  }

  /* still to discover */
  const untouched = Object.keys(byCountry).filter(c => !byCountry[c].some(l => isV(l.id))).sort();
  if (untouched.length && visitedLocs.length) {
    cWrap.append(
      el('div', { class: 'section-head' }, el('h2', {}, '🧭 Still to discover')),
      el('div', { class: 'discover-chips' },
        untouched.map(c => el('a', { class: 'discover-chip', href: 'index.html' },
          `${byCountry[c][0].country_flag || '🌍'} ${c}`,
          el('span', {}, `0 / ${byCountry[c].length}`)))),
    );
  }
}

boot().catch(console.error);
