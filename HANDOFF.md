# 🌍 One World Tour — Engineering Handoff & Developer Manual

> **The single doc.** Everything a human or AI needs to pick up this project: the vision,
> the architecture, every file, the deep "why" behind each subsystem, what's built, **what's
> left to do**, and how to verify changes. This file *is* the dev manual and the handoff
> report — there used to be five separate docs (`PLAN`, `DEVNOTES`, `IDEAS`, `OVERHAUL`,
> `COUNTRIES`); they've all been folded in here. The only other doc is [`README.md`](README.md)
> (the public-facing overview). Older docs, if present, live under `docs/archive/` for history.
>
> Counts in this doc were taken straight from the data on 2026-06-30 (walks updated 2026-07-03,
> monuments updated 2026-07-04; map performance + layout-collision fixes 2026-07-06 — see §6e ⚡):
> **345 locations · 89 countries · 60 walks · 204 Windy windows (73 live) · 30 curated
> windows (17 live + 13 ambient) · 35 monument tours across 25 cities.**

---

## 0. Read-me-first (context for the next agent)

- **This is a creative web-dev project, NOT a security engagement.** The global
  `~/.claude/CLAUDE.md` on this machine is a bug-bounty methodology doc — **it is not
  relevant here. Ignore it for this project.**
- **Standing creative permission:** the owner has granted full latitude to change, refactor,
  and optimize anything. You don't need permission to improve things — but the four governing
  principles below are *binding*.
- **No build step, no framework, no package manager.** Hand-written vanilla HTML/CSS/JS
  served as static files. Don't introduce a bundler/React/etc. unless explicitly asked.
- **Serving it in this environment:** `python3 -m http.server 8099 --bind 127.0.0.1`.
  **Must bind `127.0.0.1`, not `0.0.0.0`** — the sandbox safety classifier blocks `0.0.0.0`.
- **Build-time Windy key** lives in `tools/windy.key` (gitignored, `chmod 600). Build-time
  only — it must never be printed, committed, or shipped to the client. Runtime uses the
  keyless public Windy embed.

### The four governing principles (binding — every feature must honor these)
1. **Immersive / in-app. No off-site redirect links.** Embed the real thing, or honestly
   say it doesn't exist. (A *content* link that **is** the feature — e.g. a news article from
   its source — is fine. A "browse it on YouTube/Netflix" escape hatch is what we avoid.)
2. **No fake or forever-loading states.** Honest empty states only. If data isn't there, say
   so; never a spinner that never resolves or a placeholder posing as real content.
3. **Skippable / seekable is THE differentiator** vs. virtualvacation.us. Their videos/windows
   give no controls and no length; ours always keep native controls.
4. **Creative / alive.** Live local radio, live weather, live local time are the bar. A place
   should feel like *right now*.

### The reference competitor
We deliberately study and then one-up **virtualvacation.us** (and its sub-apps `/window`,
`/videarth`, `/livecam`, `/monument`). We inspected their source (curl + grep the inline JS;
see §12). **Key finding:** their "windows" and "videarth" are all *recorded* YouTube videos
seeked to a `?start=` offset and looped — none are live. That's how they reach hundreds of
places. We adopted the technique (our "ambient" tier) but **label it honestly**, and we add a
genuinely-live tier (Windy + curated cams) on top.

---

## 1. Tech stack

- **Frontend:** vanilla HTML + CSS + JS (ES2017+, no modules/bundler). Each HTML page loads a
  handful of `<script src>` files in dependency order.
- **Map:** Leaflet 1.9.4 + Leaflet.markercluster (CDN).
- **Tiles:** CARTO `dark_nolabels` (base) + Esri "Dark Gray Reference" (borders + labels
  overlay). Keyless, CORS-safe.
- **Media:** Windy public webcam embeds + YouTube IFrame API / plain iframes (cams, ambient
  videos, walks, monuments).
- **Audio:** Web Audio API (synthesised soundscapes, no audio files) + a plain `<audio>`
  element for live radio.
- **Persistence:** `localStorage` only (no accounts, no DB). Keys are `owt_*`.
- **Backend (optional):** a tiny FastAPI proxy (`backend/server.py`) for "Ask the Guide". The
  whole app works fully without it.

---

## 2. Repository map (every file, what it does)

### HTML pages (each a standalone entry point)
| Page | Purpose | Key script |
|---|---|---|
| `index.html` | Home — world map, filters, search, Surprise me, Fly-the-Tour, Drop In | `js/map.js` |
| `location.html` | One place: arrival cinematic, Step Outside, culture, radio, weather, news, monuments, photos, Ask the Guide | `js/location.js` |
| `window.html` | **Virtual Window** — framed window onto a place (live / timelapse / ambient) | `js/window.js` |
| `guess.html` | **City Guesser** — GeoGuessr-style, guess from the scene | `js/guess.js` |
| `passport.html` | Stamps / notes / stats for visited places | `js/passport.js` |

### JS modules (`js/`)
| File | Role |
|---|---|
| `state.js` | `State` + `Geo` — localStorage source of truth (visited, saved, notes); great-circle helpers (`km`, `interpolate`, `bearing`) |
| `api.js` | `API` — all external data: Wikimedia photos/summary, Open-Meteo weather, open.er-api FX, Radio-Browser, GDELT news, `askGuide` (backend proxy) |
| `destinations.js` | `Destinations.loadAll()` — reads `data/index.json`, fetches every enabled region, returns one flat cached array. Use this on any new page |
| `culture.js` | `COUNTRY_PROFILES` — per-country language/phrases/currency/dish, keyed by country name (all 89 countries) |
| `radio.js` | `Radio` — live local radio via one `<audio>`; loading/playing/error/stopped states |
| `soundscape.js` | `Soundscape` — procedural ambient audio (Web Audio); maps a data `sounds` filename → synth recipe |
| `walkthrough.js` | `Walkthrough` — **shared scene player** for *tours*. `renderScene()` paints Tier 1 curated `walk` video (YT IFrame API) → Tier 5 Ken Burns photo flythrough. Powers **Drop In + City Guesser**. Has `onError`→Ken Burns fallback. See §6a |
| `webcam.js` | `Webcam` — **window resolver, three tiers** + Windy index. `liveFor` / `windowFor` / `forWindow` + `windyLiveFor` / `windyWindowFor` (Windy-only, for rot fallback) + `setWindyIndex`. See §6b/§6c |
| `ytembed.js` | `YTEmbed.mount(host, {videoId, start?, loop?, muted?, frameClass?, onReady?, onError?})` — mounts a YouTube embed via the **IFrame API** so a rotted id (deleted/private/embedding-off) fires `onError`. Packages `walkthrough.js`'s guard so the location page (hero/More Views/monuments) + Virtual Window share one honest fallback. Named `YTEmbed`, **not** `YT` (the API's own global). See §6b/§6d |
| `window.js` | Virtual Window page logic (live + timelapse + ambient, badges, legend, chips, local-moment plate). See §6b |
| `location.js` | The place page: arrival, **Step Outside** tiles, culture/radio/weather/news, **monuments**, photos, Hancock section, postcard studio. **Largest file (~860 lines) — a refactor target** |
| `map.js` | The home map: clustering, search+autocomplete, region/tag/content filters, Surprise me, Fly-the-Tour, Drop In, night layer, stats |
| `guess.js` | City Guesser game loop (5 rounds, distance scoring, region picker, shareable score) |
| `passport.js` | Passport stamps/notes/stats, data-driven across regions |

### CSS (`css/`) — design tokens live in `main.css`
`main.css` (tokens + base), `map.css`, `location.css`, `window.css`, `guess.css`,
`passport.css`. **Design tokens:** `--gold #c9a84c`, `--gold-light`, `--void`, `--rim`,
`--panel`, `--earth`, `--text-hi/mid/lo`, radii `--r-sm/md/lg/full`, spacing `--sp-xs…2xl`,
transitions `--fast/med/slow`; fonts Playfair Display (display) + Inter (body).

### Data (`data/`)
- `index.json` — region registry. **8 regions:** canada, usa, europe, asia, africa, oceania,
  latinamerica, ancient.
- `countries.json` — **canonical 89-country registry** (ISO code / flag / continent /
  live-status). Every location also carries `country_code` + `continent`.
- Region files: `canada.json` (17), `usa.json` (50), `europe.json` (119), `asia.json` (76),
  `africa.json` (22), `oceania.json` (11), `latinamerica.json` (25), `ancient.json` (25) →
  **345 locations.**
- `windy.json` — **build-time webcam sidecar** `{ id: { window, live?, title, km } }` for
  204 places (73 with a live stream) after the 2026-07-07 cam audit. Runtime embeds the
  keyless Windy player. See §6c.

### Tools (`tools/`) — Python helpers, run by hand
| File | What it does |
|---|---|
| `fetch_windy.py` | **The scale source.** Build-time Windy `nearby` lookup per city, picks the best in-city cam, writes `data/windy.json`. Reads the key from `tools/windy.key`. On-disk cache so re-runs don't burn quota; `--refresh` ignores it. See §6c |
| `revet_walks.py` | Re-validate curated `walk` ids (and `--webcam` for live cams) — they rot |
| `verify_ambient.py` | Verify an ambient/cam candidate: public (oEmbed 200) + embeddable (`playableInEmbed`) + live-vs-recorded flag. Usage: `python3 tools/verify_ambient.py key=VIDEOID:STARTSECS …` |
| `build_monuments.py` | Generates/patches the `monuments` arrays (idempotent; re-vet via oEmbed) |
| `build_webcams.py` | Idempotent patch of curated `webcam` (live) ids |
| `build_countries.py` | Generates `data/countries.json` (counts live locations from `index.json`) |
| `normalize_countries.py` | In-place fix: England/Scotland→UK, Faroe→Denmark, stamps `country_code`+`continent`. Idempotent |
| `build_world.py` | Generated the 50 world-coverage countries (154 places) with coords/slugs **verified live via the MediaWiki API** (handles pagination + secondary coords + 429 backoff; cache `tools/.wiki_cache.json`) |
| `build_culture.py` | Patches `js/culture.js`'s 4 lookup tables for all 50 new countries. Idempotent (marked block) |
| `build_europe.py`, `build_usa.py`, `enrich_canada.py` | **⚠ STALE one-off builders.** The live JSON has since been normalized + given ambient/walk/monument entries; **re-running clobbers them. Treat the live JSON as source — don't re-run these.** |

### Backend (`backend/`)
`server.py` — FastAPI proxy, one `POST /ask` → Claude (`claude-sonnet-4-6`), for "Ask the
Guide". `requirements.txt` lists deps. Run:
`ANTHROPIC_API_KEY=sk-... uvicorn server:app --reload --port 8000`. **Optional** — the app
degrades gracefully without it.

---

## 3. Data model

### Region registry — `data/index.json`
```jsonc
{ "regions": [
  { "id":"canada", "name":"Canada", "flag":"🇨🇦", "file":"data/canada.json", "enabled":true },
  …,
  { "id":"ancient", "name":"Ancient", "flag":"🤫", "file":"data/ancient.json",
    "enabled":true, "collection":"Ancient Apocalypse", "accent":"#a776dd" }
]}
```
A region with `"accent":"#rrggbb"` becomes a **data-driven themed collection**: that one hex
drives its filter chip *and* its marker colour — **no new CSS** to add the next collection.

### Location schema (fields actually in use)
- **Required:** `id`, `name`, `country`, `coordinates {lat,lng}`, `emoji`, `tag`
  (`famous`|`hidden`), `blurb`.
- **Common:** `country_flag`, `country_code`, `continent`, `region`/`province`, `type`,
  `street_view`, `wikipedia_slug`, `highlights[]`, `fun_fact`, `hidden_gem_tip`, `sounds[]`,
  `unsplash_query`.
- **Window/scene fields (the interesting ones):**
  - `walk` — curated walking-tour YouTube id (string or `{yt}`). **60 locations.**
  - `webcam` — 🔴 **live** cam (string id / `{yt}` / `{channel}` / `{poster}`). **17.**
  - `ambient` — 🎬 **recorded** window loop (`{yt,start}` / `'id'` / `'id?start=ss'`). **13.**
  - `monuments` — up to 3 `{name, yt, start?}` landmark videos. **35 across 25 cities.**
  - Ancient-only: `aa_season`, `aa_episode`, `aa_claim`.
- **Windy sidecar** (`data/windy.json`, keyed by location `id`, not in the region files):
  `{ window, live?, title, km }`. Covers **205** places — **204** with a `window` cam, **73**
  also `live` — after the **2026-07-07 hand audit** (owner found Nara/Osaka's "window" was a
  sky-cam slideshow; 63 cams were junk or the wrong place — Ushuaia's was Puerto Williams,
  Chile). Verdicts live in `tools/windy_overrides.json`; `tools/prune_windy.py` applies them
  to an existing windy.json, and `fetch_windy.py` applies them itself on re-crawls **and**
  refuses junk-titled cams (airport/traffic/milepost/sky) outright. `title`/`km` describe the
  WINDOW cam only — the live id is bare; `tools/audit_windy_live.py` re-derives live-cam
  metadata when you need to audit that tier again.

### Current content inventory (as of 2026-06-30)
- **345 locations across 89 countries** — Canada 17, USA 50, Europe 119, Asia 76, Africa 22,
  Oceania 11, Latin America 25, Ancient 25. *(Was 191/39 before the 2026-06-29 world-coverage
  expansion. The 154 new places are coordinate-verified but **content-thin** — no curated
  windows/walks/highlights yet; see §11 I-9.)*
- **Windows:** 204 via Windy (73 live) **plus** 30 hand-curated (17 live + 13 ambient).
  Curated always outranks the Windy pick. *(Was 247/105 before the 2026-07-07 audit pruned
  wrong-place and junk cams — honest count beats inflated count.)*
- **60 walking tours · 35 monument tours (25 cities).**

---

## 4. External services (all keyless at runtime unless noted)
| Service | Used for | Key? |
|---|---|---|
| Wikipedia / Wikimedia Commons | Arrival photo, gallery, summary, Ken Burns frames | no |
| Open-Meteo | Live weather + UTC offset (local time / day-night) | no |
| Radio-Browser | Live local radio streams | no |
| GDELT | Local news (rate-limits hard → self-hides on 429) | no |
| open.er-api.com | Currency rates | no |
| **Windy Webcams** | Live cams + day timelapses | runtime: **no** (public embed); build: **yes** (`tools/windy.key`) |
| YouTube (iframe / IFrame API / oEmbed) | Curated cams, ambient videos, walks, monuments | no |
| CARTO basemaps + Esri ArcGIS | Map tiles (base + borders/labels overlay) | no |
| Unsplash | *Optional* higher-quality arrival photos | yes (placeholder in `js/api.js`) |
| Google Maps | *Optional* real Street View upgrade | yes (placeholder in `js/location.js`) |
| Anthropic (via backend) | "Ask the Guide" | yes (server-side) |

Inline code placeholders worth knowing: `js/location.js` `GMAPS_KEY` (Street View works
without it via embed), `js/api.js` `UNSPLASH_KEY` (Wikimedia is the keyless default) and
`BACKEND_URL` (`http://localhost:8000`).

---

## 5. The scene player (`walkthrough.js`) — §6a · read before touching it

`renderScene(el, loc, opts)` paints a place's scene into **any** element and returns
`{ kind:'video'|'photos', ready:Promise<bool>, destroy() }`. Two features share it: map
**Drop In** and **City Guesser**. `open()`/`close()` wrap it in the Drop In modal. (The
Virtual Window — §6b — and the location page — §6d — each have their *own* renderer on
purpose; don't route them back through this.)

Tiers: **Tier 1** curated YouTube walk (`loc.walk`), **Tier 5** Ken Burns photo flythrough
(Wikimedia). Always call `.destroy()` before re-rendering / on close.

**`opts` flags (distinct on purpose):**
- `blind:true` → hide every name-revealing caption.
- `noVideo:true` → never use the curated video (its YouTube **title bar reveals the place**),
  force Ken Burns.

| Consumer | opts | Why |
|---|---|---|
| Map Drop In | `{}` (or `{subtitle}`) | full experience, captions on |
| City Guesser | `{blind:true, noVideo:true}` | must hide the answer → photos only |

**Link-rot guard.** Tier 1 uses the **YouTube IFrame API**, not a bare `<iframe>`, so we get
an `onError`. A deleted/private/embedding-disabled video → `onError` → tear down the YT host
and **fall back to Ken Burns**. This is what makes curated ids *safe*.

---

## 6. Subsystem deep-dives

### 6b. The Virtual Window (`window.js`, `webcam.js`) — THREE tiers, deliberately NOT the scene player
A window is a **fixed view you look out of** — it does not move. Three tiers, and the UI
**always says which is which** (badge + chip + a one-line legend):

- 🔴 **LIVE** — a real public webcam streaming *now* (`Webcam.liveFor(loc)`): curated YouTube
  live → Windy `/live`.
- 🪟 **TIMELAPSE** — Windy's `/day` view: a real *current* still that updates through the day
  (`kind:'timelapse'`). Neither a 24/7 stream nor a fake loop — its own honest label, worded
  **"🪟 webcam stills · updated through the day"** everywhere since 2026-07-07. It plays as a
  slideshow of stills, and the old "live timelapse" wording oversold it — the owner opened one
  expecting live video and reported it as fake. Don't re-word it back toward "live".
- 🎬 **AMBIENT** — a curated *recorded* "out the window" video, seeked to a good moment and
  **looped** (`loop=1&playlist=<id>&start=<s>`). The technique virtualvacation uses for *all*
  its windows; we use it **only as a fallback** and never pass it off as live.

`Webcam.forWindow(loc)` = `liveFor(loc) || windowFor(loc)` → `{ src, kind }` (live wins) or
`null`. `windowFor` = curated ambient → Windy `/day` timelapse. **Curated always beats Windy.**

- `init()` fetches `data/windy.json`, calls `Webcam.setWindyIndex(...)`, then builds the pool
  as window-bearing locations only. Everywhere else never enters the Window.
- Each window: the iframe + the kind badge (`.w-kind.live` red / `.w-kind.timelapse` gold /
  `.w-kind.ambient` blue) + the **real** local-time / day-night / temperature plate. That
  plate is honest even for ambient — it's live data about the place right now.
- "Drop by" chips list live → timelapse → ambient; `#legend` spells out the markers; "open
  another window" hops all tiers; last one remembered (`owt_last_window`); `?id=<id>` deep
  links.
- **No window anywhere of any tier → honest empty state, button disabled.** No fake window.

**Honesty rules baked in (do not regress):** no still ever stands in for a window (a Wikipedia
lead image is often a map/satellite/globe — the "it's just an image of the earth" bug);
ambient is never presented as live; the four things — a live stream, a timelapse, a recorded
loop, and a walking tour — are kept distinct. **Don't "simplify" this back into
`Walkthrough.renderScene`** (that put a *walking tour* inside a window frame — a reported bug).

> ⚠️ If you add a new consumer of `forWindow().kind`, handle all **THREE** kinds:
> `live` / `timelapse` / `ambient`. Today's consumers: `map.js` (marker tip + search mark),
> `window.js` (legend/chips/badge + `.w-kind.timelapse` CSS), `location.js` (Step Outside).

### 6c. The Windy pipeline (`tools/fetch_windy.py` + `webcam.js`) — the scale source
Hand-curating YouTube cams (oEmbed-vetting each, and they rot) reaches a couple dozen places.
The **Windy Webcams API** (the old webcams.travel catalogue, ~70k geolocated cams) scales it to
hundreds. We use it **build-time only** so the key never ships.

- **Pipeline.** `fetch_windy.py` reads the key from `tools/windy.key`, does a
  `nearby={lat},{lng},{radius}` lookup (radius 50 km) for **every** location, picks the best
  cam per city (in-city ≤25 km preferred, then by `viewCount`), and writes `data/windy.json`:
  `{ "berlin": { "window":"<id>", "title":"…", "km":0, "live":"<id>" }, … }`.
  `window` = the cam whose `/day` player backs the 🪟 timelapse tier; `live` = a cam that also
  exposes a real `/live` stream. A cam farther than 50 km is "no window here" (stay honest).
  Re-run `python3 tools/fetch_windy.py` anytime (cached; `--refresh` ignores cache).
- **Runtime embed is KEYLESS.** `webcam.js` builds
  `https://webcams.windy.com/webcams/public/embed/player/<id>/<day|live>` — verified
  iframe-able (no `X-Frame-Options`/CSP frame-ancestors). The player carries Windy's branding
  (ToS attribution) **and its own play/scrub/fullscreen controls — which satisfies our
  "skippable/seekable" rule for free.** `/day` shows a current still immediately; `/live` is a
  continuous stream (may need a user play-click per autoplay policy).

### 6d. The location page "Step Outside" section (`location.js`) — its own renderer
The owner asked for a **side-by-side pair that's just *there*** (no click): an auto-starting
walk next to a real window. Built by `setupOutside()` → tiles:
- **📹 Live cam** — `Webcam.liveFor(loc)` (live only): a live iframe when one exists, else an
  honest "no live cam yet" empty state.
- **🪟 Window** — `Webcam.windowFor(loc)`: a curated ambient loop or a Windy `/day` timelapse,
  labelled by kind; honest empty state otherwise.
- **🚶 Walk** — full-width underneath, bigger: a plain muted-autoplay `<iframe>` (`OUTSIDE_EMBED`
  = `autoplay=1&mute=1&rel=0&modestbranding=1&iv_load_policy=3`); native YT controls keep it
  skippable. **No Ken Burns fallback here** — a real walk or an honest "not available" (the
  owner dislikes a slideshow posing as a "walk"). So `location.js` does **not** load
  `walkthrough.js`.

Muted is intentional (the page already has radio + soundscape; two autoplaying audio sources
would clash, and muted autoplay sidesteps the gesture requirement). **Never a still posing as a
window. 🔴 is reserved for genuinely-live cams** — a recorded frame must never sit under
"streaming now".

### 6e. The map (`map.js`) — basemap, clustering, search, filters
**Basemap (legible placement).** Base is CARTO **`dark_nolabels`** + a separate **Esri "Dark
Gray Reference"** overlay for **borders + place labels**. Plain dark tiles draw borders so
faintly a correctly-placed pin reads as the wrong country (the "Lake Louise looks like it's in
the US" report — markers were *never* misplaced; DOM centre lands exactly on
`map.latLngToContainerPoint(latlng)`, `dx:0,dy:0`). Esri tile order is **`{z}/{y}/{x}`** (y
before x), unlike CARTO's `{z}/{x}/{y}`. Overlay `zIndex:2` over base `zIndex:1`, both far below
the marker pane (600).

**⭐ Clustering — ONE cluster group PER CONTINENT (2026-07-06), pixel-distance within each.
DO NOT add `disableClusteringAtZoom`.**
A single world-wide group let pixel-distance clustering merge **across seas** at low zoom —
Iberia fused with Morocco, Greece/Turkey with Egypt — and markercluster parks the bubble at the
members' *average* position, so bubbles made mostly of European cities rendered **over Africa**
(the owner's "Europe is appearing in Africa" report; reproduced at 1100×800 → zoom 2). The fix:
`clusterGroupFor(continent)` creates one `L.markerClusterGroup` per `loc.continent` (all 345
records carry it; verified) and `render()` buckets markers by continent, so a bubble can never
span two continents. Continental-scale bubbles (zoom ≤ 4, n ≥ 6, holding ≥ 22% of the
continent's visible markers via `contTotals`) also get a **name caption** (`.owt-cluster-label`,
"Europe" / "N. America") — an anonymous number near a coastline reads as misplaced even when it
isn't; the ≥22% share rule keeps it to ~1 caption per continent instead of stamping "EUROPE"
three times into the same 200px. Bubbles from *different* groups can still visually overlap at
world zoom (e.g. the Levant cluster near Giza's pin) — that resolves on zoom and is the accepted
cost of geographic honesty. The base tiles get `className:'base-tiles'` + a per-tile
`brightness(1.5)` CSS filter so the landmass is actually visible at world zoom (raw CARTO dark
renders continents nearly as black as the ocean; per-tile = paint-time cost only, 60fps held).
Within each continent the behaviour is unchanged, and the old hard-won rules still bind:
- The owner's liked behaviour is the *default* markercluster one: **click a circle → it zooms
  to fit its members** — but via the CUSTOM `clusterclick` handler, not the built-in: small
  bubbles (**n ≤ 5**) **spiderfy in place** instead, because for island+mainland pairs
  (Iceland+Ireland, Canaries+Lisbon) the bounds midpoint is open ocean — clicking a "2" near
  Ireland "threw me into the empty water left of Portugal" (owner, 2026-07-07). Big clusters
  are dense land, so bounds-fit stays right for them. A lone city still renders as its own
  pin that **opens on one click**; only overlapping cities stay a bubble.
- We twice tried `disableClusteringAtZoom` (8, then 5) to make cities clickable sooner. **Both
  made it worse.** A live CDP zoom-sweep proved why: at the threshold zoom the cluster count
  snaps from ~50 bubbles to **0**, dumping all 345 markers as loose pins that scatter off the
  small viewport → the owner's *"zoom in and everything disappears."*
- Config is exactly: `maxClusterRadius: 60, showCoverageOnHover: false, animate: false` plus
  `spiderfyOnMaxZoom: false, zoomToBoundsOnClick: false` — BOTH built-in click behaviours off
  because the custom `clusterclick` handler replaces them (spiderfy ≤5 / zoom-to-bounds >5 /
  spiderfy at maxZoom). Leaving either true double-handles the click.
  `maxClusterRadius` 80 (default) glues a continent into one blob; 32
  declusters too early; **60** is the chosen middle. If you change it, re-run a zoom-sweep and
  watch z4→z8 bubble counts degrade *smoothly* (no snap-to-zero).
- **`animate:false` is required.** The decluster animation *slides* markers from the cluster
  centroid to their true spot (~114px transient drift at z7), reading as "pins keep moving /
  are misplaced." Snapping removes the illusion; resting placement is pixel-perfect. **Don't
  re-enable it.**
- Verifying clicks headlessly: trust `map.latLngToContainerPoint(latlng)` for the click pixel,
  NOT `marker._icon.getBoundingClientRect()` — under headless CDP after a programmatic zoom the
  icon's DOM rect goes stale (reports y off-screen) while the projection + real render are
  correct.

**Map sizing.** `map.invalidateSize()` runs before fit, again after first paint, plus a
`ResizeObserver` on `#map` — Leaflet caches pixel size at init, and a stale size causes
offset markers + a mis-computed drag origin ("Stockholm sits mid-Europe at rest, can't pan
until I click"). A `pageshow` handler resets `flying`, calls `map.stop()`, and re-enables
zoom/drag when restored from the bfcache (Back button).

**Single-click open.** A marker click does a short safe `flyTo` ease then navigates on a
**guaranteed timer** — no `fitBounds`, no plane animation, no strandable `flying` lock (that
lock + an interrupted animated zoom was the old "can't zoom / 3rd click finally opens" bug).
The plane flight stays only in Fly-the-Tour (which removes layers, never navigates).

**Search autocomplete.** `#search-input` is a real **combobox with a dropdown** (`#search-suggest`),
not just a marker filter. `buildSearchSuggestions(raw)` scores each location (name-prefix `0` <
name-substring `1` < region/country-prefix `2` < substring `3` < highlight-match `4`, top 8),
so `poi` puts **Point Farms** at the top. `renderSuggest()` adds a kind badge per place — 🔴
live / 🪟 timelapse / 🎬 ambient (via `windowKind`) + 🚶 walk. Mouse handlers use **`mousedown`,
not `click`** (so a pick lands before `blur` closes the dropdown). Keyboard ↓/↑/Enter/Esc.

**Content filters.** After the curation filters (All / Famous / Hidden / Saved), a divider then
**🔴 Live** (`windowKind(loc)==='live'` — only true live cams, ~85 places), **🪟 Window**
(`hasWindow` = any window tier), **🚶 Tour** (`hasWalk`), **✨ Both**. They set `tagFilter`,
`render()`, and `fitToVisible()`. The 🔴 Live filter (added 2026-07-07 alongside the cam audit)
deliberately excludes the 🪟 timelapse/stills tier — after the audit renamed that tier "webcam
stills," a "show me only what's streaming *now*" filter had to mean live cams only. Same
predicates power a gold `.marker-live-dot` and a tooltip line distinguishing the tier. **The filter bar must stay one row** —
`flex-wrap:nowrap; overflow-x:auto` (scrollbar hidden): it once wrapped to two rows, grew
*upward* into the stats bar, and overlapped the bottom-left FABs so clicks hit the wrong control.

**FAB layout (2026-07-06).** The four FABs (Drop In / Plan Tour / My Journey / Day-Night) are a
**vertical column on the left edge**, lifted above the stats + filter rows. They used to be a
horizontal row sharing the filter bar's bottom line — which *collided with the centered filter
bar at any window under ~1670px wide*, burying the "All"/"Famous" buttons under the FABs. (The
earlier "one-row filter bar" fix above solved the *wrapping* overlap but not this horizontal
one; a screenshot at 1366×768 caught it.) Verified overlap-free at 1366/1920/mobile widths.

**⚡ Performance — measured 2026-07-06, and BINDING (the "map is laggy/glitchy" report).**
The owner runs this in a VM (VMware SVGA II — software rendering, no GPU). Three things were
dragging the map from 60fps to ~25–41fps with 50–133ms frame stalls, each proven by an A/B
rAF-frame-time measurement over CDP (fps at idle / during a wheel-zoom sweep):
- **Infinite `box-shadow` "pulse" keyframes on every pin** → full map repaint every frame:
  idle 41fps → **60fps flat** with them removed. Markers now wear a **static halo**. Never
  re-add an always-on animation to marker/cluster CSS; state-scoped opacity/transform pulses
  on single elements (radio-on dot, shimmer placeholders) are fine.
- **`backdrop-filter: blur()` on the 21 chrome elements over the map** (chips, pills, bars,
  FABs) → every map repaint re-blurs each panel in software. All removed project-wide
  (map/location/window/guess/main.css), backgrounds bumped to ~0.9 alpha instead — visually
  near-identical on this dark theme.
- **Animated zoom scaling two tile layers** (CARTO base + Esri overlay) → zoom sweep 25fps;
  and the smooth tile scale + instant cluster snap (`animate:false`) read as *glitching*.
  `zoomAnimation:false, fadeAnimation:false` on the map makes the whole zoom one coherent
  instant snap: zoom sweep **60fps**, and the Esri legibility overlay stays (removing it was
  the alternative; instant zoom made that unnecessary).
Final numbers: idle 60fps/0 janky frames (even with ~120 icons on screen), zoom sweep 60fps.
**A console-error sweep does NOT verify performance** — measure rAF frame deltas before
declaring the map healthy.

### 6f. Monuments (`location.js`)
`loc.monuments` = up to 3 `{name, yt, start?}`, rendered as a tab-picker feeding one player
(`#monuments-section`, `setupMonuments()`, `.mon-tab*` CSS), hidden when none. 35 tours across
25 cities. The original 24 were harvested from `virtualvacation.us/monument` (anonymous
`ytid?start=ss` list), *identified by real YouTube oEmbed title*, given clean names. The 11 added
2026-07-04 (LatAm/Africa capitals: Bogotá, Havana, Montevideo, La Paz, Asunción, San José, Dakar,
Addis Ababa, Johannesburg) were authored via `WebSearch → oEmbed-vet → apply`, then each confirmed
to actually play (not just mount) via a headless settle-check — held 9 s with no `onError`. Every
id is guarded at runtime by `js/ytembed.js`, so a future rot falls to an honest empty state.
Tool: `tools/build_monuments.py` (idempotent).

### 6g. Curating window/walk/monument video ids — the method
**Never recall video ids from memory — that's how you get wrong/dead embeds.**
1. `WebSearch "<City> <Country> walking tour 4k"` with `allowed_domains:["youtube.com"]` →
   real `watch?v=<id>` URLs with descriptive titles. Pick a central/comprehensive one (skip
   narrow neighborhood/playlist/channel URLs).
2. **Vet every candidate via oEmbed:**
   `https://www.youtube.com/oembed?url=<urlencoded watch url>&format=json` → `200` + `{title,
   author_name}` means it exists & is public, and the title confirms it's the right place.
3. For a **live cam** also confirm `"isLiveNow":true` on the watch page (oEmbed 200 only proves
   *public*; most "live cam" uploads are archived recordings — SkylineWebcams literally titles
   them "Recorded live footage" — or seasonal). For an **ambient window** confirm
   `"playableInEmbed":true` and that it's a genuinely *stationary* view of the *named* place
   (reject walking tours, drone montages, "rain on a window" clips).
   Tool: `tools/verify_ambient.py key=VIDEOID:START …`.
4. Write the verified id into the location (`"walk":"<id>"`, `"webcam":…`, etc.).
5. **Re-vet periodically — ids rot:** `python3 tools/revet_walks.py` (and `--webcam`). A dead
   `walk` just falls back to Ken Burns (no breakage); a dead curated cam currently shows a
   broken frame until re-vetted (see §10 the `onError` TODO).

**Caveat:** oEmbed `200` proves *exists/public*, not that third-party embedding is allowed —
there's no reliable API for that. Reputable channels (Prowalk Tours, Nomadic Ambience,
Wanderlust Travel Videos…) overwhelmingly allow it, and the §6a `onError` fallback covers the
rest. Don't claim "verified embeddable" — claim "verified exists; embedding guarded by fallback."

### 6h. YouTube embeds & the "no redirects" principle
A YouTube **embed** *is* the real thing playing in-app, so it satisfies principle #1 — but a
YouTube player always keeps **some** of its own chrome (logo, title, end-screen). You can't
remove it fully; `modestbranding=1`, `rel=0`, `iv_load_policy=3` minimise it. **Don't claim
"zero redirects" for a YouTube surface** — claim "embedded in-app, chrome minimised." A
genuinely non-embeddable video is the real failure → that's what the `onError` fallbacks are for.

---

## 7. Verifying changes (headless + CDP recipes)

Serve first: `python3 -m http.server 8099 --bind 127.0.0.1`.

**Quick DOM smoke test:**
```
chromium --headless --no-sandbox --disable-gpu --no-first-run --no-default-browser-check \
  --user-data-dir=$(mktemp -d) \
  --host-resolver-rules="MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE unpkg.com,
     EXCLUDE en.wikipedia.org, EXCLUDE upload.wikimedia.org, EXCLUDE api.open-meteo.com" \
  --virtual-time-budget=12000 --dump-dom http://localhost:8099/guess.html
```
Add YouTube/Windy hosts to `EXCLUDE` when you need those embeds to load.

**Interactive (clicks, function calls) — CDP over a websocket.** The reusable win: a real
interactive Chrome **IS allowed if the Bash call sets `dangerouslyDisableSandbox: true`**.
Launch `chromium --headless=new --no-sandbox --remote-debugging-port=9222
--remote-allow-origins=*` (the `*` matters or the handshake is 403), drive it with Python
`websocket-client` + a `PUT /json/new?<url>`, set `Network.setCacheDisabled {cacheDisabled:true}`
(the static server lets Chrome cache JS), then `Runtime.evaluate {expression, awaitPromise:true,
returnByValue:true}`.

**CDP gotchas (cost real time if forgotten):**
- **Top-level `let`/`const` are NOT on `window`** (e.g. `map`, `allLocations`, `tagFilter`,
  `Geo`) — you can't reach them by bare name in `Runtime.evaluate`. Top-level **`function`
  declarations ARE** global (`hasWindow`, `windowKind`, `enterExperience`, `openWindow`).
  `Walkthrough` is explicitly exported via `window.Walkthrough`.
- **`--host-resolver-rules`: one host per `EXCLUDE`, comma-separated.** `EXCLUDE a b c`
  (multiple hosts after one EXCLUDE) **silently fails** — even `localhost` won't resolve and
  every navigation lands on `chrome-error://chromewebdata/` (DOM looks empty). Write
  `EXCLUDE localhost,EXCLUDE 127.0.0.1,EXCLUDE en.wikipedia.org`.
- **The location page gates content behind the arrival overlay.** `loadExperience()` runs
  ~4.1s after load (overlay auto-dismisses at 3.5s + a 600ms transition). In headless, call
  `enterExperience()` first, then poll for the element (`#walk-stage` having children,
  `.outside-empty`, etc.). Don't assert at t≈0.
- Static buttons get their handler wired **after** the async load — click in a short retry loop.
- **Measuring marker placement: settle ~1.5s after `setView`.** Mid-zoom readings show the
  cluster slide-animation (up to ~114px), not the real offset (which is `dx:0,dy:0` at every
  zoom). `fetch()`'d region JSON is HTTP-cached — `Network.clearBrowserCache` or a `?bust=`
  query before re-checking data edits.

**Node sanity check for pure logic:** `node --check js/webcam.js`.

**Frame-rate check (the lag instrument — use it for any "feels slow" report):** in a CDP
`Runtime.evaluate`, run a `requestAnimationFrame` loop for 4–5s and record fps + the longest
frame + frames >33ms, once at idle and once while dispatching a synthetic `WheelEvent` to
`#map` every 100ms (zoom sweep). Healthy = 60fps idle with zero frames >33ms. The 2026-07-06
scripts live at the session scratchpad's `measure_ab.py` pattern; they're ~40 lines and easy
to recreate. Screenshot at 1366×768 + 390×844 too — that's how the FAB/filter-bar collision
was caught after a console-only sweep had called the page clean.

> No automated test suite — verification is these recipes, run by hand. A tiny Playwright smoke
> test over the 5 pages would pay off if this grows.

---

## 8. Gotchas / hard-won lessons (don't relearn these)

- **markercluster: `animate:false` required; never add `disableClusteringAtZoom`.** Both cause
  the "pins move / everything disappears on zoom" reports. Full reasoning in §6e.
- **The owner's machine renders in SOFTWARE (VM, no GPU).** No infinite `box-shadow`/paint
  animations on map markers, no `backdrop-filter` anywhere, keep `zoomAnimation:false` —
  each of these alone measurably tanked the map to 25–41fps. Full numbers in §6e ⚡.
- **Clusters must not span continents.** Pixel-distance clustering in one world group merged
  Iberia+Morocco and Balkans+Egypt at low zoom and drew "Europe" bubbles over Africa. Keep the
  per-continent cluster groups (§6e ⭐). Never collapse them back into one group.
- **"Verified" needs the right instrument.** A 5-page console sweep proves no JS errors — it
  proved nothing about the lag the owner kept reporting. For anything "feels slow/glitchy",
  measure rAF frame times (recipe in §7) and screenshot real viewport sizes for layout overlap.
- **The map needs the borders/labels overlay** — plain dark tiles make a correct pin look like
  the wrong country. Markers were never misplaced.
- **Esri tile URL order is `{z}/{y}/{x}`** (y before x), unlike CARTO's `{z}/{x}/{y}`.
- **"Live cam" ≠ live.** oEmbed 200 only proves *public*. Verify `"isLiveNow":true` for live,
  `"playableInEmbed":true` for ambient. A window must be *stationary* + the *named* place.
- **No still ever stands in for a window** — a Wikipedia lead image is often a map/satellite/globe.
- **Region JSON is HTTP-cached** — hard-refresh / cache-bust after editing a data file.
- **GDELT rate-limits (429)** — the news section self-hides and recovers; keep that.
- **Top-level `let`/`const` are not on `window`; top-level `function`s are.** Matters for CDP.
- **YouTube embeds always keep some chrome** — don't claim "no redirects" for a YT surface.
- **Serve on `127.0.0.1:8099`, not `0.0.0.0`** (sandbox classifier blocks `0.0.0.0`).
- **Don't re-run the stale one-off builders** (`build_europe.py`/`build_usa.py`) — they clobber
  the normalized + enriched live JSON.

---

## 9. What's shipped (condensed)

World map (clustering, dark base + borders/labels overlay, region/tag/content filters,
search-with-autocomplete, Surprise me, Fly-the-Tour planner, Drop In, night/day terminator) ·
location page (skippable arrival cinematic, Step Outside = live cam + window + full-width walk,
culture panel, live radio, live weather/time, local news, photo gallery, **monument tours**,
postcard studio, Ask the Guide, Ancient-Apocalypse section) · **Virtual Window** (live /
timelapse / ambient, labelled, ambient sound, remember-last, hop-the-world) · **City Guesser**
(5-round distance scoring, region picker, Wordle-style shareable score, skippable scenes) ·
**Passport** (stamps/notes/stats) · **Ancient Apocalypse** collection (25 sites, data-driven
accent) · **procedural soundscapes** · **world coverage 39→89 countries / 191→345 locations** ·
**windows at scale via Windy** (204 windows / 73 live, hand-audited) · **60 walks · 35 monuments**.

---

## 10. ✅ What's next — the actual TODO (prioritized)

### A. Content depth (the main thrust right now — "beef it up")
- 🚶 **More walks.** 60/345 today (2026-07-03: +9 verified capital walks — LatAm: Bogotá, Havana,
  Montevideo, La Paz, Asunción, San José; Africa: Dakar, Addis Ababa, Johannesburg — each
  oEmbed-vetted, and now guarded by `ytembed.js` if they rot). Continue the verified
  `WebSearch → oEmbed → apply` method for the ~285 without one — next obvious set: **SE-Asia
  capitals** + secondary LatAm/Africa cities (Medellín, Cartagena, Casablanca, Mombasa…).
  (Note: Rio, Mexico City, Jakarta, Ho Chi Minh, Lima, Santiago weren't found under those exact
  ids — look up the real `id` in the region files first.)
- 🏛️ **More monuments.** 35 across 25 cities (2026-07-04: +11 for the 9 new-walk capitals —
  Bogotá→Monserrate, Havana→El Capitolio+Malecón, Montevideo→Palacio Salvo, La Paz→Mi Teleférico,
  Asunción→Palacio de los López+Panteón, San José→National Theatre, Dakar→African Renaissance
  Monument, Addis Ababa→National Museum, Johannesburg→Apartheid Museum — each settle-checked to
  actually play). Still 0 for most cities. Author 1–3 each for the next marquee set — Sydney→Opera
  House/Harbour Bridge, Dubai→Burj Khalifa, Cape Town→Table Mountain, Agra→Taj Mahal, etc. Same
  vetted process; `build_monuments.py`.
- 🪟 **Curated windows for marquee cities** where the Windy cam is too far or weak. A curated
  `webcam` (live) or `ambient` auto-outranks Windy. Verify with `tools/verify_ambient.py`.
- ✍️ **Author `highlights` + `blurb`/`fun_fact`** for the strongest content-thin new places
  (today they fall back to the live Wikipedia summary — honest, but the marquee ones deserve
  curated copy). **Done 2026-07-03 for the 9 capitals above** (blurb + fun_fact + hidden_gem_tip
  + 3–5 highlights each, every `wikipedia_slug` verified live against the MediaWiki API). Continue
  for the next content-thin tier. See §11 I-9.
- 🔴 **Curated live-cam upgrades (quality over the Windy default).** Where a famous YouTube live
  cam beats the nearest Windy cam, add it as `loc.webcam`. Re-check Berlin Brandenburg Gate
  `v5OUHl8c9Es`, Prague `0FvTdT3EJY4` when they flip LIVE; Times Square / Venice / Shibuya /
  Bondi are usually strong.
- 🗣️ **Native-speaker review of the 50 new culture profiles** (phrases/dishes — §11 I-10).

### B. Polish / correctness
- ✅ ~~**World-view geography: "Europe appearing in Africa".**~~ **DONE (2026-07-06, second pass —
  the owner re-tested after the perf fixes and the *look* was still wrong).** Single-group
  pixel-distance clustering merged across the Mediterranean and parked bubbles at member
  centroids (Iberia+Morocco bubble on the Western Sahara coast; Balkans+Egypt over Egypt).
  Redesigned: per-continent cluster groups + continent captions on the major bubbles + brightened
  land tiles (§6e ⭐). Verified: bubbles land on their own continents at 1100/1366/1920 widths,
  cluster-click zoom-in / spiderfy / filters / search all work, 60fps idle & zoom held, 0 console
  errors.
- ✅ ~~**Map lag/glitch on the owner's machine + FAB/filter-bar collision.**~~ **DONE (2026-07-06).**
  The owner reported the cluster map "super laggy and glitchy" *after* two sessions had declared
  the map verified — those verifications were console-error sweeps, which can't see frame rate.
  Root causes (all measured, see §6e ⚡): infinite box-shadow pulse animations on every pin,
  21 `backdrop-filter` panels over the map, and animated zoom scaling two tile layers in a
  software-rendered VM. Fixed (static halos, blur removed project-wide, `zoomAnimation:false`),
  plus the FAB row → left-edge column (it was covering the "All"/"Famous" filter buttons at any
  window narrower than ~1670px), plus the country pill → compact summary (the flag list wrapped
  into the region chips below ~1450px). Verified 60fps idle & zoom, overlap-free at 3 sizes,
  0 console errors on all 5 pages.
- ✅ ~~**`onError`→honest-fallback on the curated YouTube window iframe.**~~ **DONE (2026-07-03)**
  via the new `js/ytembed.js` module. A curated YouTube surface (hero, More Views cam/window,
  monuments, Virtual Window) now mounts through the IFrame API; a rotted id fires `onError` →
  auto-falls-back to the place's Windy window (`Webcam.windyWindowFor`/`windyLiveFor`, which skip
  the curated id and can't re-introduce a broken frame) → and only then an honest empty state.
  The walk has no Windy equivalent, so it drops straight to "walking tour no longer available".
- 🔎 **Map findability dropdown.** Vienna/Prague/Budapest already exist but were hard to find —
  add a continent→country→city filter dropdown and surface the existing search better.
- 🪟 **Window radio bed (optional):** let the ambient *sound* be the place's live local radio
  (via `radio.js`) instead of the synth, for cities with stations.
- 🌍 **Guesser polish:** optional timed / "no-skip" hard mode (opt-in; skippable stays default);
  remember the last region picked.

### C. Creative map ideas (additive; none touch the now-stable core)
- **Cluster hover/long-press preview** — a small popover listing the city names inside a bubble.
- **"Spin the globe" / Surprise-region** — zoom-fly to a random *cluster* (not just a pin).
- **Visited-progress heat** — tint clusters by how many of their cities you've explored (we
  already track `_visited`; `owt-cluster-done` exists for all-visited — add a partial gradient).
- **Live-content clusters** — when the 🔴/🪟 filter is on, badge clusters with a count of live
  cams inside.
- **Mini-map "you are here" graticule** on deep zoom so a lone pin in empty terrain feels located.

### D. Code organization (do alongside a visible feature, never solo)
- `location.js` is ~860 lines — peel off self-contained pieces (`postcard.js`,
  `culture-panel.js`); `walkthrough.js`, `destinations.js`, `webcam.js` are already split out.
- Defer a slim generated `data/index.geo.json` manifest (one tiny record per place) so the map +
  pages stop fetching *every* region JSON on load — land it once 2–3 more regions arrive (§11 I-5).
- Convert `ancient` from a region into a `collections:["ancient"]` tag on the host-country files
  (§11 I-3).

---

## 11. Bigger future ideas (the parking lot — only when asked)

**Nothing here is built.** Pick one up only when explicitly asked.

- 🕰️ **"Back in Time" — watch borders change through history.** The big one. Scrub a year slider
  and the map's political boundaries morph through major changes — all the way back past modern
  nation-states to the **original Indigenous / First Nations territories** of North America.
  Each shift (wars, treaties, partitions) is a "moment" you can land on. *Big lift:* needs real
  historical GeoJSON per era and likely an architecture rethink (time-indexed polygon layers + a
  timeline UI), not point markers. Data leads: **native-land.ca** (has an API — treat Indigenous
  data with extra care + clear sourcing), **historical-basemaps** open GeoJSON sets, **Natural
  Earth** (modern baseline). Could be its own "History" mode/page.
- 🛰️ **Walkthrough middle tiers** (between curated video and Ken Burns): **satellite
  "descend-from-orbit"** zoom via Esri World Imagery — and make it the *default* for the aerial
  Ancient sites (geoglyphs, Poverty Point, Serpent Mound) that are meant to be seen from above ·
  **360° photospheres** (Pannellum / Photo Sphere Viewer) for Wikimedia 360s · **Mapillary /
  KartaView** street-level sequences (open; covers trails & ruins Google Street View doesn't) ·
  optional **narrated mini-tour** via browser `SpeechSynthesis` over the flythrough.
- 🤫 **Ancient Apocalypse depth:** exact episode *titles*, the "mainstream view vs Hancock's
  claim" as two explicit lines per site, more secondary sites as `highlights`.

### 🅿️ Parked / explicitly declined
- **Satellite "descend from orbit" as a *standalone* mode** — owner dropped it (we have the map).
  *(The middle-tier descend-zoom inside the walkthrough above is a different, still-open idea.)*
- **Multiplayer / private Guesser rooms** — virtualvacation has these; big lift.

---

## 12. World-coverage record + open data-architecture issues

### The expansion (2026-06-29): 39 → 89 countries, 191 → 345 locations
We studied virtualvacation's full country set (84, from `/videarth`'s `countriesAndCities`),
gap-analysed vs ours, and built a **country-first data model** to expand into:
1. `data/countries.json` — canonical 89-country registry (ISO code / flag / continent /
   live-status) via `build_countries.py`.
2. Normalized existing data (`normalize_countries.py`): **England/Scotland → United Kingdom**
   (Edinburgh was mis-tagged "England"), Faroe→Denmark, every record stamped `country_code` +
   `continent`.
3. Generated all **50 missing countries / 154 new destinations** with **every coordinate +
   Wikipedia slug verified live against the MediaWiki API** — never recalled from memory
   (`build_world.py`; new `asia/africa/oceania/latinamerica.json` + europe appends; 4 new map
   regions).
4. Extended `culture.js` so all 89 countries have a culture profile + currency + facts
   (`build_culture.py`).

The **6 countries we have that virtualvacation does NOT** (our genuine edge — keep them):
Albania, Bahamas, Bosnia & Herzegovina, Micronesia, Montenegro, Romania. Beyond-parity targets
worth adding later: Nigeria, Tanzania, Ghana, Nepal, Pakistan, Bangladesh, Kazakhstan,
Greenland, Fiji, Vanuatu.

**Reproducible build order** (same "generate data with a script" pattern):
```bash
python3 tools/build_countries.py      # data/countries.json (registry)
python3 tools/normalize_countries.py  # UK fold + code/continent
python3 tools/build_world.py          # asia/africa/oceania/latinamerica + europe appends
python3 tools/build_culture.py        # patches js/culture.js (4 tables × 50 countries)
python3 tools/build_countries.py      # re-run to flip backlog → live
```

### Open issues (severity 🔴 correctness · 🟡 tech-debt · 🔵 nice-to-have)
- **I-3 🟡** — `ancient` region conflates theme with geography (25 sites physically in 10
  countries, siloed in `ancient.json`). Convert to a `collections:["ancient"]` tag on host
  files. Country counts are already honest; only the file/region grouping is theme-shaped.
- **I-5 🟡** — `Destinations.loadAll()` fetches **every** region file on every page load (8 files
  / 345 locations). Still fine; the case for a slim `data/index.geo.json` + lazy detail grows
  with each region.
- **I-7 ✅ RESOLVED (2026-07-03)** — the `onError`→Windy→honest-empty fallback now exists for every
  curated YouTube surface via `js/ytembed.js` (see §10 B). A rotted cam id no longer shows a broken
  frame.
- **I-9 🟡** — the 154 new destinations are **coordinates-only**: verified coords + valid
  `wikipedia_slug` (photos/summary/weather/time resolve live), but **no authored `highlights`,
  no curated `walk`/`webcam`/`ambient` beyond what's since been added, and `blurb` falls back to
  Wikipedia.** Honest baseline, not finished — see §10 A.
- **I-10 🟡** — culture phrases/dishes for the 50 new countries are **best-effort** (ISO codes /
  currencies / capitals are factual; greetings + signature dishes need a native/fluent reviewer).
- **I-11 🔵** — stale culture keys: `'England'` and `'Faroe Islands'` remain in `culture.js`'s
  tables but no location uses them (folded into UK/Denmark). Drop on the next `culture.js` edit.

---

## 13. House style

- Match the surrounding code: vanilla JS, 2-space indent, design tokens from `css/main.css`
  (`--gold`, `--void`, `--panel`, `--rim`, `--text-*`, `--r-*`, `--sp-*`, `--fast/med/slow`).
- Data files: 2-space JSON, UTF-8 (raw emoji/accents — `ensure_ascii=False` when rewriting).
- Keep new shared logic in a module other pages can reuse, not copy-pasted per page.
- When you finish a unit of work, update the counts at the top of this doc and the TODO in §10.
