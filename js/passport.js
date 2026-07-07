/* ============================================================
   PASSPORT — multi-country stamps, notes, stats
   Data-driven across every enabled region.
   ============================================================ */
async function initPassport() {
  // Shared cross-page-cached loader. Each location keeps its own real
  // `continent` field (stamped in the data), so the continents stat counts
  // actual continents — not map regions.
  const all = (await Destinations.loadAll())
    .map(l => ({ ...l, sub: l.region || l.province || '' }));

  const visited = State.visited;
  const isV = id => visited.includes(id);
  const byId = Object.fromEntries(all.map(l => [l.id, l]));

  // ---- Stats ----
  const visitedLocs = all.filter(l => isV(l.id));
  const countries  = new Set(visitedLocs.map(l => l.country));
  const continents = new Set(visitedLocs.map(l => l.continent));

  // Distance travelled along the route, in chronological visit order.
  const route = visited.map(id => byId[id]).filter(Boolean);
  let distance = 0;
  for (let i = 1; i < route.length; i++) distance += Geo.km(route[i - 1].coordinates, route[i].coordinates);

  setStat('stat-total-visited', visitedLocs.length);
  setStat('stat-countries', countries.size);
  setStat('stat-continents', continents.size);
  setStat('stat-distance', distance.toLocaleString());
  setStat('stat-pct', all.length ? Math.round((visitedLocs.length / all.length) * 100) + '%' : '0%');
  setStat('stat-total-locations', all.length);
  setStat('rank-name', rankFor(visitedLocs.length));

  renderAchievements(all, visitedLocs, countries, continents);

  const body = document.getElementById('passport-body');

  if (visitedLocs.length === 0) {
    document.getElementById('empty-passport').style.display = 'block';
    renderWishlist(body, all, isV);   // a wishlist can still exist with 0 visits
    return;
  }

  // ---- Group by country ----
  const byCountry = {};
  all.forEach(l => { (byCountry[l.country] ||= []).push(l); });

  // Countries with at least one stamp → full sections, most-complete first.
  const started = Object.keys(byCountry)
    .filter(c => byCountry[c].some(l => isV(l.id)))
    .sort((a, b) => {
      const va = byCountry[a].filter(l => isV(l.id)).length;
      const vb = byCountry[b].filter(l => isV(l.id)).length;
      return vb - va || a.localeCompare(b);
    });

  started.forEach(country => body.appendChild(countrySection(country, byCountry[country], isV)));

  renderWishlist(body, all, isV);

  // Countries not yet started → compact "still to discover" strip.
  const untouched = Object.keys(byCountry)
    .filter(c => !byCountry[c].some(l => isV(l.id)))
    .sort();
  if (untouched.length) {
    const wrap = document.createElement('div');
    wrap.className = 'discover';
    wrap.innerHTML = `<p class="section-label">Still to discover</p>
      <div class="discover-chips">${untouched.map(c => {
        const flag = byCountry[c][0].country_flag || '🌍';
        return `<a class="discover-chip" href="index.html">${flag} ${c}
          <span>0 / ${byCountry[c].length}</span></a>`;
      }).join('')}</div>`;
    body.appendChild(wrap);
  }
}

function setStat(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }

function rankFor(n) {
  if (n >= 100) return 'Master Voyager';
  if (n >= 60)  return 'World Explorer';
  if (n >= 30)  return 'Jet Setter';
  if (n >= 15)  return 'Globetrotter';
  if (n >= 5)   return 'Wanderer';
  if (n >= 1)   return 'Day Tripper';
  return 'Armchair Traveler';
}

/* ---- Achievements ---- */
function renderAchievements(all, visitedLocs, countries, continents) {
  const n = visitedLocs.length;
  const hidden = visitedLocs.filter(l => l.tag === 'hidden').length;
  const inRegion = id => visitedLocs.filter(l => l.region_id === id || l.continent === id).length;
  const euro = visitedLocs.filter(l => l.continent === 'Europe').length;
  const usa  = visitedLocs.filter(l => l.country === 'United States').length;
  const cad  = visitedLocs.filter(l => l.country === 'Canada').length;
  const saved = State.saved.length;

  const defs = [
    ['🛂', 'First Stamp',          n >= 1,                  'Visit your first place'],
    ['🧭', 'Pathfinder',           n >= 5,                  `Visit 5 places (${Math.min(n,5)}/5)`],
    ['🌍', 'Globetrotter',         n >= 25,                 `Visit 25 places (${Math.min(n,25)}/25)`],
    ['👑', 'Grand Tour',           n >= 50,                 `Visit 50 places (${Math.min(n,50)}/50)`],
    ['🛂', 'Border Hopper',        countries.size >= 5,     `Reach 5 countries (${Math.min(countries.size,5)}/5)`],
    ['🌐', 'Continental',          continents.size >= 2,    `Explore 2 continents (${Math.min(continents.size,2)}/2)`],
    ['🗺️', 'Off the Beaten Path',  hidden >= 5,             `Find 5 hidden gems (${Math.min(hidden,5)}/5)`],
    ['🇪🇺', 'Euro Trip',            euro >= 10,              `Visit 10 European spots (${Math.min(euro,10)}/10)`],
    ['🦅', 'Coast to Coast',       usa >= 10,               `Visit 10 US spots (${Math.min(usa,10)}/10)`],
    ['🍁', 'True North',           cad >= 6,                `Visit 6 Canadian spots (${Math.min(cad,6)}/6)`],
    ['♥',  'Dreamer',              saved >= 5,              `Save 5 places to your wishlist (${Math.min(saved,5)}/5)`],
    ['✅', 'Completionist',        n >= all.length && all.length > 0, `See the whole world (${n}/${all.length})`],
  ];

  const grid = document.getElementById('achievements-grid');
  const earned = defs.filter(d => d[2]).length;
  grid.innerHTML = defs.map(([icon, name, ok, hint]) => `
    <div class="badge-card ${ok ? 'earned' : 'locked'}" title="${hint}">
      <div class="badge-icon">${icon}</div>
      <div class="badge-name">${name}</div>
      <div class="badge-hint">${ok ? 'Unlocked' : hint}</div>
    </div>`).join('');
  document.getElementById('ach-count').textContent = `${earned} / ${defs.length} unlocked`;
  document.getElementById('achievements-section').style.display = 'block';
}

/* ---- Wishlist (saved but not yet visited) ---- */
function renderWishlist(body, all, isV) {
  const saved = State.saved;
  const wish = all.filter(l => saved.includes(l.id) && !isV(l.id));
  if (!wish.length) return;

  const sec = document.createElement('div');
  sec.className = 'country-section';
  sec.innerHTML = `<div class="country-heading">
      <span class="country-flag">♥</span><h2>Wishlist</h2>
      <span class="country-progress">${wish.length} place${wish.length > 1 ? 's' : ''} saved</span>
    </div>`;
  const list = document.createElement('div');
  list.className = 'wishlist-grid';
  wish.forEach(l => {
    const a = document.createElement('a');
    a.className = 'wishlist-card';
    a.href = `location.html?id=${l.id}`;
    a.innerHTML = `<span class="wishlist-emoji">${l.emoji}</span>
      <span><strong>${l.name}</strong><small>${l.country_flag} ${l.country}</small></span>`;
    list.appendChild(a);
  });
  sec.appendChild(list);
  body.appendChild(sec);
}

function countrySection(country, locs, isV) {
  const section = document.createElement('div');
  section.className = 'country-section';
  const flag = locs[0].country_flag || '🌍';
  const vCount = locs.filter(l => isV(l.id)).length;

  const heading = document.createElement('div');
  heading.className = 'country-heading';
  heading.innerHTML = `<span class="country-flag">${flag}</span>
    <h2>${country}</h2>
    <span class="country-progress">${vCount} / ${locs.length} visited</span>`;
  section.appendChild(heading);

  const grid = document.createElement('div');
  grid.className = 'stamps-grid';

  // Earned stamps first within a country.
  locs.sort((a, b) => (isV(b.id) - isV(a.id)) || a.name.localeCompare(b.name));

  locs.forEach(l => {
    const earned = isV(l.id);
    const note = State.getNote(l.id);
    const shortName = l.name.split('&')[0].split('/')[0].trim();

    const wrap = document.createElement('div');
    wrap.className = 'stamp-wrapper';
    wrap.innerHTML = `
      <div class="stamp ${earned ? '' : 'unearned'}" title="${l.name}">
        <div class="stamp-emoji">${l.emoji}</div>
        <div class="stamp-name">${shortName}</div>
      </div>
      <label>${l.sub || country}</label>
      <textarea class="stamp-note" rows="2" data-id="${l.id}"
        ${earned ? `placeholder="Add a note…"` : `placeholder="Not yet visited" disabled`}
      >${earned ? (note || '') : ''}</textarea>`;
    grid.appendChild(wrap);

    if (earned) {
      wrap.querySelector('.stamp-note').addEventListener('blur', e => State.saveNote(l.id, e.target.value));
    }
  });

  section.appendChild(grid);
  return section;
}

document.getElementById('reset-btn').addEventListener('click', () => {
  if (confirm('Clear all passport progress? This cannot be undone.')) {
    localStorage.removeItem('owt_visited');
    localStorage.removeItem('owt_notes');
    window.location.reload();
  }
});

initPassport();
