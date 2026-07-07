# 🧭 One World Tour — Developer Manual

Practical notes for whoever (human or AI) works on this next. Conventions, the
non-obvious bits, the verification recipes, and — most importantly — **known
future problems** so they don't bite later.

- **What's next / priorities:** [`PLAN.md`](PLAN.md)
- **Long-term idea parking lot:** [`IDEAS.md`](IDEAS.md)
- **User-facing overview:** [`README.md`](README.md)

---

## 1. Architecture at a glance

Static site, vanilla JS, no build step. Pages are plain HTML that pull in shared
JS modules (each module is an IIFE or a set of top-level functions; no bundler).

| Page | Purpose | Key scripts |
|---|---|---|
| `index.html` | World map (home) | `map.js` |
| `location.html` | One destination | `location.js` (+ culture/radio/soundscape) |
| `guess.html` | City Guesser game | `guess.js` |
| `window.html` | Virtual Window | `window.js` |
| `passport.html` | Stamps / stats | `passport.js` |

**Shared modules** (used by several pages):
- `state.js` — `State` (localStorage) + `Geo` (great-circle `km`, `interpolate`, `bearing`).
- `api.js` — `API`: all external calls (Wikimedia photos, Open-Meteo weather, radio, news, FX).
- `destinations.js` — `Destinations.loadAll()`: reads `data/index.json`, fetches every
  enabled region, returns one flat, cached array of locations. **Use this on any new page**
  instead of re-implementing the fetch.
- `walkthrough.js` — `Walkthrough`: the shared **scene player** for *tours* (map **Drop In** +
  **City Guesser**). See §3. NOTE: neither the Virtual Window (§3a) **nor the location page**
  (§3c) uses this anymore — both have their own renderers on purpose.
- `webcam.js` — two tiers (see §3a). `Webcam.resolve(webcam)` → embeddable **live** URL (YouTube
  id string, or `{yt}` / `{channel}` / `{poster}`); `Webcam.resolveAmbient(ambient)` → looped
  **recorded** URL (`'id'`, `'id?start=SS'`, or `{yt,start}`); `Webcam.forWindow(loc)` →
  `{ src, kind:'live'|'ambient' }` (live wins) or `null`. Shared by the location page's "Step
  Outside" window tile (§3c, live-only by design), the Virtual Window (§3a, hybrid), and the
  map's "Window" filter + 🔴/🎬 badges (§3e). Loaded by `index.html` for that last use.

**Data model.** `data/index.json` registers regions `{id,name,flag,country,continent,file,
enabled, [collection], [accent]}`. Each region file is `{country,continent,code,[collection],
locations:[…]}`. A location needs at least `id, name, coordinates{lat,lng}, emoji, tag, blurb`,
plus optional `wikipedia_slug, street_view, webcam, walk, highlights, fun_fact, aa_claim`.

**Themed collections are data-driven.** Give a region an `"accent":"#rrggbb"` (and optional
`"collection":"Name"`) and that one hex colors both its filter chip and its map markers — no
new CSS. (See Ancient Apocalypse in `data/index.json`.)

---

## 2. Guiding principles (from the project owner — don't regress these)

1. **In-app, no off-site redirects.** Embed the real thing or honestly say it doesn't exist.
   No "watch on YouTube/Netflix" launcher links standing in for a feature. (A news headline
   linking to its source article is fine — that link *is* the content.)
2. **No fake / forever-loading states.** No perpetual shimmer. If there's no data, say so.
3. **Skippable / seekable is the differentiator** vs virtualvacation.us. Every scene must be.
4. **Creative, alive.** Live local radio/weather/time are the bar.

---

## 3. The scene player (`walkthrough.js`) — read before touching it

`renderScene(el, loc, opts)` paints a place's scene into **any** element and returns
`{ kind:'video'|'photos', ready:Promise<bool>, destroy() }`. Two features share it now:
map **Drop In** and **City Guesser**. `open()`/`close()` wrap it in the modal Drop In uses.
(The Virtual Window — §3a — and the location page — §3c — each have their own renderer.)

Tiers: **Tier 1** curated YouTube walk (`loc.walk`), **Tier 5** Ken Burns photo flythrough
(Wikimedia). Always call `.destroy()` before re-rendering / on close (it kills the YT player
+ the slideshow timer).

**`opts` flags — these two are distinct on purpose:**
- `blind:true` → hide every name-revealing caption.
- `noVideo:true` → never use the curated video (its YouTube **title bar reveals the place**),
  force Ken Burns.

| Consumer | opts | Why |
|---|---|---|
| Map Drop In | `{}` (or `{subtitle}`) | full experience, captions on |
| City Guesser | `{blind:true, noVideo:true}` | must hide the answer → photos only |

(The Virtual Window used to be a consumer here with `{blind:true}` — that was a **bug**. It
showed a *walking tour* or a panning slideshow inside a "window," which is the opposite of
looking out a window. The Window now has its own renderer — see §3a.)

**Link-rot / embeddability guard (important).** Tier 1 uses the **YouTube IFrame API**, not a
bare `<iframe>`, specifically so we get an `onError`. A deleted / private / embedding-disabled
video → `onError` → we tear down the YT host and **fall back to Ken Burns**, so the user never
sees YouTube's broken "Video unavailable" frame. This is what makes curated ids *safe*.
Verified headless (see §5).

---

## 3a. The Virtual Window (`window.js`) — HYBRID (live + ambient), deliberately NOT the scene player

A window onto a place is a **fixed view you look out of** — it does not move. It comes in two
tiers, and the UI **always says which is which** (badge + chip + a one-line legend):

- 🔴 **LIVE** — a real public webcam streaming *now* (`Webcam.resolve(loc.webcam)`).
- 🎬 **AMBIENT** — a curated *recorded* "out the window" video, seeked to a good moment and
  **looped** (`Webcam.resolveAmbient(loc.ambient)`). This is exactly the technique
  `virtualvacation.us/window` uses to reach *hundreds* of places — we inspected its source
  (it's all recorded YouTube videos with a hand-picked `?start=` offset, **none live**) and
  adopted the idea, but we **never pass recorded footage off as live**.

`Webcam.forWindow(loc)` returns `{ src, kind:'live'|'ambient' }` (live wins if a place has both)
or `null`. The ambient `src` uses the single-video loop trick `loop=1&playlist=<id>` plus
`&start=<secs>`. There is **no still fallback**: a Wikipedia/Wikimedia lead image is frequently a
map, a logo, or a satellite/globe shot (the "it's just an image of the earth" the owner reported
for Point Farms) — the opposite of looking out a window. A still photo *isn't a window*.

- `init()` builds the pool as `all.filter(l => l.coordinates && Webcam.forWindow(l))` —
  window-bearing locations only (live OR ambient). Everywhere else never enters the Window.
- Each window: the iframe (`.w-pane-cam`) + the kind badge (`🔴 Live` red `.w-kind.live` /
  `🎬 Ambient · recorded loop` blue `.w-kind.ambient`) + the **real** local-time / day-night /
  temperature plate. That plate is honest *even for ambient* — it's live data about the place
  right now, independent of whether the footage is live; it's what keeps the place feeling alive.
- "Drop by" chips list **live first** (🔴) then ambient (🎬), shuffled within each tier; the
  `#legend` line spells out both markers. "Open another window" hops across both; last one
  remembered (`owt_last_window`); `?id=<id>` deep links to any window-bearing id, else random.
- **No live AND no ambient anywhere** → honest empty state and the button disabled. No fake window.

**Do not reintroduce a still fallback, and do not "simplify" this back into
`Walkthrough.renderScene`.** Both were reported bugs: the scene-player reuse put a *walkable
YouTube tour* (it moves) inside the window frame; the still fallback put a *map/globe image*
there. A tour moves, a window doesn't, a photo isn't a window — and live ≠ ambient. Four
different things; keep them distinct.

> 12 **live** cams + 13 **ambient** views = 25 windows today. Live cams were **verified live at
> add time** (`"isLiveNow":true` on the watch page — *oEmbed 200 only proves public*, and a huge
> share of "live cam" uploads are archived recordings, e.g. SkylineWebcams titles them "Recorded
> live footage", or seasonal like Churchill polar bears). Ambient picks were verified **public +
> `"playableInEmbed":true`** with `tools/verify_ambient.py` (which also flags live-vs-recorded),
> and chosen to be genuinely *stationary* views of the *named place* — walking tours, drone
> montages, and geographically-vague "rain on a window" clips were rejected as not-a-window or
> mislabel risk. Add more via README "Adding destinations" step 3. Cam ids rot and the window
> iframe still has no onError fallback yet, so a dead id shows a broken frame until re-vetted
> (`tools/revet_walks.py --webcam`).

## 3b. YouTube embeds & the "no redirects" principle

Principle #1 is "in-app, no off-site redirects." A YouTube **embed** *is* the real thing playing
in-app, so it satisfies the spirit — but a YouTube player always keeps **some of its own links**
(logo, title, end-screen). You cannot fully remove them; `modestbranding=1`, `rel=0`,
`iv_load_policy=3` (set in `webcam.js` and `walkthrough.js`) minimise them. Don't claim "zero
redirects" for any YouTube surface — claim "embedded in-app, chrome minimised." A genuinely
*non-embeddable* video is the real failure: the `walkthrough.js` `onError`→Ken Burns fallback
catches that so the user never lands on a bare "Watch on YouTube" frame.

## 3c. The location page "Step Outside" section (`location.js`) — its own renderer

The old location page had a `▶ Virtual Walk` button (overlaid on the street-view pane) that
opened the `Walkthrough` **modal**, plus a separate "Live View" webcam panel. The owner asked
for that to become, instead, a **side-by-side pair that's just *there*** (no click): an
**auto-starting walk** next to a **real window**. That's the `#outside-section` panel, built by
`setupOutside()` → `setupWalkTile()` + `setupWindowTile()`:

- **Walk tile** — if the place has a curated `walk` id, a plain muted-autoplay `<iframe>`
  (`OUTSIDE_EMBED` = `autoplay=1&mute=1&rel=0&modestbranding=1&iv_load_policy=3`) just plays;
  native YT controls keep it skippable/seekable. **No curated walk → an honest "not available"
  empty state.** Deliberately **no Ken Burns fallback here**: a real walk or nothing. (The owner
  specifically dislikes a photo slideshow being passed off as a "walk" — that's why this tile,
  unlike the Drop In / Guesser modal, does *not* use `Walkthrough.renderScene`.)
- **Window tile** — deliberately **live-cam-only** (it uses `Webcam.resolve(loc.webcam)`, *not*
  `forWindow`): a live iframe (`🔴 Live view`) when one exists, otherwise an honest "No live
  window of this place yet" empty state (`🪟 Window`). This is an **intentional divergence** from
  the Virtual Window (§3a), which is now hybrid live+ambient — on a place's *own* page a 🔴 live
  cam is the strong promise; the ambient pool is for the standalone Window's "hop the world"
  browsing. If you want ambient here too, switch this one call to `forWindow` + show the kind
  badge. **No still fallback** —
  a Wikipedia lead image is often a map/satellite/globe shot, not a view out a window (this was
  the reported "just an image of the earth" bug). A window is a live view or it's not available.

Muted is intentional: the page already has the radio + ambient soundscape, and two autoplaying
audio sources would clash (also muted autoplay sidesteps the browser gesture requirement, so
there's never a "playing" UI with no sound). `walkthrough.js` is **no longer loaded** on
`location.html`. Don't reintroduce the `▶`-modal here — embedding the walk inline was the point.

## 3d. Map search autocomplete (`map.js`)

The home-map search (`#search-input`) is a real **combobox with a suggestion dropdown**
(`#search-suggest`), not just a marker filter — the owner asked to be able to *pick* a place
("type `poi` → Point Farms is right there"), not just see markers thin out.

- `buildSearchSuggestions(raw)` scores each location: name-prefix `0` < name-substring `1` <
  region/country-prefix `2` < substring `3` < highlight-match `4`, sorts by score then
  `localeCompare`, takes the top 8. (So `poi` ranks **Point Farms** above places that merely
  contain "…Point…" in a highlight.)
- `renderSuggest()` builds `.ss-item` buttons; a window-bearing place gets a kind badge —
  `🔴` for a live cam, `🎬` for an ambient view (via `windowKind(loc)`), plus `🚶` for a walk —
  that's why `index.html` now also loads `js/webcam.js`.
- Mouse handlers use **`mousedown`, not `click`**, so a selection lands before the input's
  `blur` closes the dropdown (the `blur` close is on a ~130ms timeout for the same reason).
- Keyboard: ↓/↑ cycle, Enter chooses the active row (or the first), Esc closes (then clears).
  `chooseSuggestion(loc)` sets the input to the name and `flyTo(loc)`. `aria-expanded` tracks
  open/closed for a11y.

## 3e. Map basemap (legible placement) + the "live content" filters (`map.js`)

**Basemap.** The base is CARTO **`dark_nolabels`** (the cinematic dark tone the gold theme is
tuned for) with a separate **Esri "Dark Gray Reference"** tile layer on top for **borders +
place labels**. Why two layers: plain CARTO Dark Matter draws country borders so faintly they're
invisible, so a correctly-placed pin reads as being in the wrong country — the owner reported
Lake Louise (genuinely at 51.4°N, −116.2°W in **Alberta**) looking like it sat in the US. The
Esri reference is keyless + CORS-safe; note its tile order is **`{z}/{y}/{x}`** (y before x),
unlike CARTO's `{z}/{x}/{y}`. The overlay is `zIndex:2` over the base's `zIndex:1`, both far
below the marker pane (600), so labels never cover pins. **The markers themselves were never
misplaced** — verified headless that the Lake Louise marker's DOM centre lands exactly on
`map.latLngToContainerPoint(latlng)` (`dx:0, dy:0`, `box-sizing:border-box`, anchor `[19,19]` on
a 38×38 icon). If someone reports "pins are off," it's almost always basemap legibility or the
cluster-centroid bubble sitting between markers — re-measure before touching coordinates.

**Content filters.** Alongside the curation filters (All / Famous / Hidden / Saved) the
filter bar has three **content** filters after a divider: **🪟 Window** (`hasWindow(loc)`, now
**live OR ambient** — `windowKind(loc)` non-null), **🚶 Tour** (`hasWalk(loc)` = `loc.walk`
truthy), and **✨ Both**. They flow through the same generic `.filter-btn` handler (sets
`tagFilter`, then `render()` **+ `fitToVisible()`** so the matching places come on-screen).
Counts today: ~29 tours, **25 windows (12 live + 13 ambient)**, a few both. The predicates also
drive at-a-glance hints so you can *see* what a place has without filtering: a small gold
**`.marker-live-dot`** on the pin, and a tooltip line that **distinguishes the tier** — "🔴 live
window" vs "🎬 ambient window" (via `windowKind`) · "🚶 walking tour" — plus the same 🔴/🎬/🚶
badges in the search dropdown. `index.html` loads `webcam.js` before `map.js` so `Webcam.forWindow`
exists when markers build.

**The filter bar must stay one row.** It's `flex-wrap: nowrap; overflow-x: auto` (scrollbar
hidden) on purpose: with 7 buttons it once wrapped to two rows and, being bottom-anchored, grew
*upward* into the stats bar and overlapped the bottom-left map FABs — so clicks landed on the
wrong control and the new filters seemed "dead." Keep it scrollable, not wrapping.

**Clustering uses `animate: false` — don't turn it back on.** With the markercluster zoom
animation on, zooming in makes each marker *slide* from the cluster-centroid to its true spot
over a few hundred ms (measured ~114px of transient drift at z7). That reads as "the pins keep
moving / are misplaced as you zoom" — the #1 thing the owner flagged. Resting placement was
always pixel-perfect; snapping (animate:false) removes the illusion. See §5.

**Clustering config — leave it on plain pixel-distance. DO NOT add `disableClusteringAtZoom`.**
The only options we set are `maxClusterRadius: 60`, `showCoverageOnHover: false`,
`spiderfyOnMaxZoom: true`, `animate: false`. This is the result of a multi-round bug the owner hit,
and it's a trap that looks tempting to "fix" — so here's the full reasoning:
- The owner's liked behaviour is the *default* markercluster one: **click a circle → it zooms to
  fit its members** (zoom-to-bounds, on by default — don't set `zoomToBoundsOnClick:false`). A lone
  city (no neighbour within `maxClusterRadius` px) renders as its **own pin that opens on one click**;
  only genuinely overlapping cities stay a bubble.
- We twice tried `disableClusteringAtZoom` (8, then 5) to "make cities clickable sooner." **Both made
  it worse.** A live CDP zoom-sweep proved why: at the threshold zoom the cluster count snaps from
  ~50 bubbles to **0**, dumping all 345 markers as loose pins that then scatter off the small
  viewport as you keep zooming → the owner's *"zoom in and everything disappears."* Forcing a global
  decluster at any fixed zoom destroys the guiding bubbles AND the graceful drill-down.
- `maxClusterRadius`: 80 (default) glues much of a continent into one blob; 32 declusters so early it
  feels scattered. **60** is the chosen middle — bubbles stay meaningful, cities separate into pins
  by country-level zoom. If you change it, re-run `scratchpad/sweep.py` and watch the z4→z8 bubble
  counts degrade smoothly (no snap-to-zero).
- Verifying clicks headlessly: trust `map.latLngToContainerPoint(latlng)` for the click pixel, NOT
  `marker._icon.getBoundingClientRect()` — under headless CDP after a programmatic zoom the icon's
  DOM rect goes stale (reports y off-screen) while the projection + the actual render are correct.
  `scratchpad/{flow2,verify2,backflow2}.py` are the reusable harnesses (launch chromium with the
  Bash `dangerouslyDisableSandbox` flag, drive via websocket-client + `Network.setCacheDisabled`).

## 3f. Windy webcams — the scale source for 🪟 Window + 🔴 Live (`webcam.js`, `tools/fetch_windy.py`)

Curating YouTube cams by hand (oEmbed-vetting each, and they rot) reaches a couple dozen places.
The **Windy Webcams API** (the old webcams.travel catalogue, ~70k geolocated cams) scales this to
hundreds. We use it **build-time only** so the API key never ships to the client.

**Pipeline.** `tools/fetch_windy.py` reads the key from `tools/windy.key` (gitignored, chmod 600),
does a `nearby={lat},{lng},{radius}` lookup for **every** location, picks the best cam per city
(in-city ≤25 km preferred, then by `viewCount`), and writes the **`data/windy.json`** sidecar:
```json
{ "berlin": { "window": "<id>", "title": "...", "km": 0, "live": "<id>" }, ... }
```
- `window` = the cam whose `/day` player (latest frame + day timelapse) backs the 🪟 Window tier.
- `live`   = a cam that also exposes a real `/live` stream, backs the 🔴 Live tier (omitted if none).
- A cam farther than 50 km is treated as "no window here" — we stay honest, never snap to another town.
Run `python3 tools/fetch_windy.py` (uses an on-disk cache in scratchpad so re-runs don't burn quota;
`--refresh` ignores it). Current yield: **247/345 windows, 105 live.** 0 errors.

**Runtime embed is KEYLESS.** `webcam.js` builds
`https://webcams.windy.com/webcams/public/embed/player/<id>/<day|live>` — verified iframe-able (no
`X-Frame-Options`/CSP frame-ancestors). The player carries Windy's own branding (ToS attribution) and
**its own play/scrub/fullscreen controls** — which actually satisfies our "skippable/seekable"
differentiator for free. The `/day` view shows a current still immediately (no gray wait); `/live` is
a continuous stream (may need a user play-click per autoplay policy).

**Resolver precedence (`webcam.js`).** Three public resolvers, all loc-keyed via the index set by
`Webcam.setWindyIndex(data/windy.json)` (each page fetches the sidecar before rendering):
- `liveFor(loc)`   — curated YouTube live → Windy live. (🔴 Live tier)
- `windowFor(loc)` — curated recorded ambient → Windy `/day` timelapse. (🪟 Window tier)
- `forWindow(loc)` = `liveFor || windowFor` — live always outranks the window. Used by map badges +
  the Window feature. **Curated always wins over Windy** (hand-picked is more iconic).

**The third tier `kind: 'timelapse'`.** Windy `/day` is neither a 24/7 stream (`'live'`) nor a fake
recorded loop (`'ambient'`) — it's a real *current* view, so it has its own honest kind/label
("🪟 live timelapse · updates through the day"). If you add a new consumer of `forWindow().kind`,
handle all THREE: `live` / `timelapse` / `ambient`. Today's consumers: `map.js` (marker tip +
search-dropdown mark), `window.js` (legend/suggestions/badge, `.w-kind.timelapse` CSS), `location.js`
(the two Step-Outside tiles via `liveFor`/`windowFor`).

## 4. Curating `walk` (walking-tour) video ids — the method

`walk` upgrades a place's scene from the photo flythrough to real footage in **all four**
consumers at once. ~29 marquee cities are curated as of this writing (1 CA, 4 US, 24 EU).

**Never recall video ids from memory — that's how you get wrong/dead embeds.** The process:

1. `WebSearch "<City> <Country> walking tour 4k"` with `allowed_domains:["youtube.com"]`.
   Results are real `https://www.youtube.com/watch?v=<id>` URLs with descriptive titles.
2. Pick a **central/comprehensive** city walk (skip narrow neighborhood/playlist/channel URLs).
3. **Vet every candidate via oEmbed** before trusting it:
   `https://www.youtube.com/oembed?url=<urlencoded watch url>&format=json`
   → `200` + JSON `{title, author_name}` means it exists & is public, and the title lets you
   confirm it's actually that city's walk. (See the one-off `scratchpad/vet.py` pattern, or
   the maintained `tools/revet_walks.py`.)
4. Write the verified id into the matching location: `"walk": "<id>"` (string) or `{"yt":"<id>"}`.

**Re-vetting (do this every few months — ids rot):**
```bash
python3 tools/revet_walks.py            # checks every walk id, exits 1 if any are dead
python3 tools/revet_walks.py --webcam   # also re-check curated webcam ids
```
Swap any `DEAD` id for a fresh one via the same search→oEmbed flow. Until you do, that place
just falls back to Ken Burns (no breakage).

**Caveat to remember:** oEmbed `200` proves *exists/public*, **not** that embedding is allowed
on third-party domains — there's no reliable API for that. Reputable walking-tour channels
(Prowalk Tours, Nomadic Ambience, Wanderlust Travel Videos, etc.) overwhelmingly allow it, and
the §3 `onError` fallback covers any that don't. Don't claim "verified embeddable" — claim
"verified exists; embedding guarded by fallback."

---

## 5. Verifying changes (headless + CDP recipes)

Serve first: `python3 -m http.server 8099 --directory <repo>`.

**Quick DOM smoke test** (renders the page, dumps final DOM):
```
chromium --headless --no-sandbox --disable-gpu --no-first-run --no-default-browser-check \
  --user-data-dir=$(mktemp -d) \
  --host-resolver-rules="MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE unpkg.com,
     EXCLUDE en.wikipedia.org, EXCLUDE upload.wikimedia.org, EXCLUDE api.open-meteo.com" \
  --virtual-time-budget=12000 --dump-dom http://localhost:8099/guess.html
```
Add `EXCLUDE www.youtube.com, EXCLUDE youtube.com, EXCLUDE s.ytimg.com, EXCLUDE i.ytimg.com`
when you need the YouTube embed/IFrame API to actually load.

**Interactive (clicks, function calls)** — CDP over a websocket:
- launch with `--remote-debugging-port=N --remote-allow-origins=*` (the `*` matters or the
  handshake is `403`),
- `GET http://localhost:N/json` → `webSocketDebuggerUrl`,
- `Runtime.enable` then `Runtime.evaluate {expression, awaitPromise:true, returnByValue:true}`.

**CDP gotchas (cost real time if forgotten):**
- Top-level `let`/`const` (e.g. `map`, `allLocations`, `Geo`) are **NOT** on `window` — you
  can't reach them by bare name in `Runtime.evaluate`. Top-level **`function` declarations
  ARE** global (e.g. `window.toggleDropIn`, `window.dropInAt`, `enterExperience`). `Walkthrough`
  is explicitly exported via `window.Walkthrough` for exactly this reason.
- **`--host-resolver-rules`: one host per `EXCLUDE`.** `EXCLUDE a b c` (multiple space-separated
  hosts after a single EXCLUDE) **silently fails** — even `localhost` won't resolve and every
  navigation lands on `chrome-error://chromewebdata/` (the DOM looks empty, every
  `getElementById` is null). Write `EXCLUDE localhost,EXCLUDE 127.0.0.1,EXCLUDE en.wikipedia.org`
  — comma-separated, one host each. (Burned a debugging cycle on this.)
- **The location page gates all content behind the arrival overlay.** `loadExperience()` (which
  builds Step Outside, conditions, radio, etc.) runs only ~4.1s after load — the overlay
  auto-dismisses at 3.5s, then a 600ms transition. In headless, just call `enterExperience()`
  first, then poll for the element you want (e.g. `#walk-stage` having children or
  `.outside-empty`). Don't assert at t≈0.
- Static buttons (e.g. `#ambient-toggle`, `#radio-play`) get their click handler wired **after**
  the page's async load — click in a short retry loop until it reacts, don't click once.
- Wait for `.country-pill` text to stop saying "Loading…" to know the map finished init.
- **Measuring marker placement: settle first.** To check a pin sits on its coordinate, compare
  its DOM-rect centre to `map.latLngToContainerPoint(latlng)` — but wait ~1.5s after `setView`.
  Sampling mid-zoom shows the markercluster slide-animation (up to ~114px, see §3e), not the real
  offset; the resting offset is `dx:0,dy:0` at every zoom. Don't "fix coordinates" off a mid-flight
  reading. Also note `fetch()`'d region JSON is HTTP-cached — `Network.clearBrowserCache` (or a
  `?bust=` query) before re-checking data edits, or the page shows the old counts.

The throwaway driver scripts for this all live in the session scratchpad; copy the pattern.

---

## 6. ⚠️ Known future problems / tech debt

Ordered roughly by when they'll bite.

1. **YouTube id rot (walk + webcam).** Inevitable. Mitigated by the `onError`→Ken Burns
   fallback and `tools/revet_walks.py`. Action: run the re-vet a few times a year.
2. **Every page fetches *every* region JSON on load** (`Destinations.loadAll` / `map.js` /
   `location.js`). Fine at ~191 locations across 4 files; will get heavy as regions grow.
   Plan: generate a slim `data/locations-index.json` manifest (id, name, coords, region) for
   list/map/guesser/window, and only fetch a full region file when a location page needs it.
   Deferred until 2–3 more regions land.
3. **`location.js` is ~860 lines.** Keep peeling self-contained pieces into modules alongside
   a visible feature (next candidates: `postcard.js`, `culture-panel.js`), leaving a thin
   orchestrator. `walkthrough.js`, `destinations.js`, and now `webcam.js` are split out.
4. **GDELT news API rate-limits hard (429).** The news section already hides itself rather than
   showing a broken state and recovers after a cooldown — keep that behavior if you touch it.
5. **City Guesser pool quality depends on Wikimedia imagery.** Some `wikipedia_slug`s return no
   photos (the old Brazil "forever loading" bug). The Guesser already **skips/rerolls** past
   empty places via the `ready` promise — preserve that when editing. (The Virtual Window no
   longer touches Wikimedia at all — it's webcam/ambient-video only, so this doesn't apply to it;
   see §3a.)
6. **Embeddability isn't guaranteed** (see §4). Don't assume a `200` video will embed; trust
   the fallback.
7. **No automated test suite.** Verification is the headless/CDP recipes in §5, run by hand.
   If this grows, a tiny Playwright smoke test over the 5 pages would pay off.

---

## 7. House style

- Match the surrounding code: vanilla JS, 2-space indent, design tokens from `css/main.css`
  (`--gold`, `--void`, `--panel`, `--rim`, `--text-*`, `--r-*`, `--sp-*`, `--fast/med/slow`).
- Data files: 2-space JSON, UTF-8 (raw emoji/accents — `ensure_ascii=False` when rewriting).
- Keep new shared logic in a module other pages can reuse, not copy-pasted per page.
