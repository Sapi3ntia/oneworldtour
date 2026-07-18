# 🌍 One World Tour

Step into 362 places across 93 countries — **walk their streets, drive their
roads, watch their intersections live, look out their windows live**, tune into
their radio, **watch their national TV live**, and read their news — all in-app,
all real. Inspired by
[virtualvacation.us](https://virtualvacation.us/), rebuilt to be better: every scene
is seekable, every "live" is actually live, and every gap is honest.

> **v2 — full redesign (2026-07).** Leaflet + markercluster are gone; the glitchy
> raster map is gone. The app is now a framework-free ES-module app with its own
> SVG map engine, a tabbed scene "stage" per place, and a yt-dlp pipeline that
> auto-finds and vets walking tours + live cams city by city.

---

## The product in one idea

Every place has up to **four real scenes**, one tap apart, on one stage:

| Scene | What it is | Rule |
|---|---|---|
| 🚶 **Walking tour** | Real recent footage of walking that place — muted, fully seekable | never a slideshow |
| 🚗 **Driving tour** | The place through a windshield — same vetting as a walk | never a slideshow |
| 🔴 **Live cam** | A 24/7 live stream at street / intersection level | must be live **right now** |
| 🪟 **Window** | Also a **live** stream — the out-a-window vantage: skyline, rooftop, harbor | never a loop, never a timelapse, never a still |

Famous cities also get 🏛️ **monument tabs** (up to 5 per city) on the same stage —
switch between the walk and each landmark tour like TV channels: Eiffel Tower ·
Big Ben · Colosseum · Trevi Fountain · Times Square · Statue of Liberty · the
Kremlin · Golden Gate Bridge & Park · Castro Street · Salesforce Park ·
Christ the Redeemer · Copacabana · Sugarloaf · Sydney Opera House · Santorini ·
Gateway Arch · Great Wall · Shibuya Crossing · and more (see
`tools/build_monuments.py`). Rio de Janeiro and St. Louis joined the map with
this batch.

Two collections extend the idea (2026-07):

- **📺 Live TV** — a Location-page panel with the country's own national channels,
  streaming live: CGTN / CCTV-4 / CCTV-13 for China, KCTV for North Korea, RT for
  Russia, NHK · KBS · Al Jazeera · DW · France 24 · TRT elsewhere. Data lives in
  `data/tv.json` (country code → channels), every channel verified actually live at
  generation time. YouTube channels mount through `yt.js` (rot → the channel removes
  itself); state TV that YouTube removed (RT) or that never had an official channel
  there (KCTV) plays from the broadcaster's own CORS-enabled HLS stream via a
  lazy-loaded hls.js — the one runtime dependency, fetched only when someone
  actually presses play on an HLS channel.
- **🦁 Wildlife & National Parks** (`data/wild.json`) — live nature cams as real
  places on the map: Brooks Falls bears (Katmai), GRACE gorillas and Lola ya Bonobo
  (DR Congo), Tembe & Djuma & Kruger (southern Africa), Mpala / Amboseli-under-
  Kilimanjaro / ol Donyo (Kenya), Etosha's floodlit waterhole and a Namib Desert
  waterhole (Namibia), a Victoria Falls waterhole (Zimbabwe), the Big Bear and
  Decorah eagle nests, and Chengdu's pandas. Same honesty rule: every cam vetted
  `is_live` + embeddable when curated; a rotted feed drops its own tab at runtime.
  The home page gets a 🦁 map filter + a "Wild live cams" rail (which also picks up
  live `nature` places like Yellowstone, Kruger and the Maasai Mara from the
  enrichment pipeline).

**The honesty rule:** a scene either embeds the real thing or the place simply
doesn't offer that tab yet. Nothing fake ever stands in — no stills posing as
windows, no frozen widgets posing as live cams.

---

## Pages

- **Explore** (`index.html`) — hero search with ranked autocomplete, the SVG world
  map (country nodes → glide into a country → city dots), content filters
  (🚶/🔴/🪟/🏛️/♥/🤫), and Netflix-style rails: *Start here*, *Live right now*,
  *Best walking tours*, *Monumental cities*, per-continent shelves — with real
  Wikipedia photos, lazy-loaded and cached.
- **Location** (`location.html?id=…`) — the tabbed stage plus: live local clock +
  weather, About (Wikipedia), fun fact, highlights, culture (language, phrases,
  currency + live FX, dish), live local radio, **📺 live national TV** (see below),
  headlines, photo gallery, procedural ambience, Ask-the-Guide (optional Claude
  backend), and a "Nearby from here" rail.
- **Virtual Window** (`window.html`) — a framed, chrome-free **live** window with a
  local-time + weather sill plate and "open another window" world-hopping.
- **City Guesser** (`guess.html`) — dropped into a mystery scene (the walk video,
  title hidden), pin the world map, scored on great-circle distance, 5 rounds,
  spoiler-free emoji share.
- **Trips** (`trips.html`, `trips.html?id=…`) — 15 curated routes people actually
  travel (the Euro Trip, Route 66, the Trans-Siberian, the Banana Pancake Trail…),
  each drawn on the world map as numbered stops, then listed stop by stop with a
  line on why that stop is on the route. See below.
- **Passport** (`passport.html`) — stamps by country, rank, achievements, notes,
  wishlist, distance travelled.

---

## Architecture (v2)

No framework, no bundler, no build step for the app itself — modern **ES modules**
served statically. Two small Python tools do the heavy lifting **at build time** so
the runtime stays keyless and dependency-free.

```
oneworldtour/
├── index.html · location.html · window.html · guess.html · passport.html
├── css/
│   ├── theme.css          # design system: tokens, buttons, chips, cards, badges
│   ├── map.css            # SVG map engine styles
│   └── home/location/window/guess/passport.css
├── js/
│   ├── worldmap.js        # THE map engine: one SVG, zero libraries (see below)
│   ├── lib/
│   │   ├── geo.js         # Natural Earth I projection + inverse, km, great-circle
│   │   ├── data.js        # region loader + media.json merge, search
│   │   ├── media.js       # scene resolution: walk/live/window tiers + honesty rules
│   │   ├── yt.js          # YouTube IFrame mounts with onError → honest fallback
│   │   ├── tv.js          # live national TV: tv.json loader + HLS mounts (lazy hls.js)
│   │   ├── api.js         # weather / wiki / radio / news / FX (all keyless)
│   │   ├── photos.js      # lazy Wikipedia thumbnails (flag/map-aware) + cache
│   │   ├── state.js       # localStorage passport (same owt_* keys as v1)
│   │   ├── culture.js · radio.js · soundscape.js · dom.js
│   └── pages/             # one module per page
├── data/
│   ├── index.json         # region registry
│   ├── trips.json         # 🧭 curated routes — ordered stop ids + editorial notes
│   ├── <region>.json      # 348 places (curated walks/webcams/monuments live here)
│   ├── wild.json          # 🦁 wildlife & national-park live cams as places
│   ├── tv.json            # 📺 live national TV channels per country (verified live)
│   ├── windy.json         # retired Windy index — kept as archive, not loaded
│   └── media.json         # yt-dlp enrichment sidecar (auto-found, vetted scenes)
├── assets/world.json      # pre-projected country outlines (see build_worldmap.py)
├── tools/
│   ├── build_worldmap.py  # TopoJSON → Natural-Earth-projected SVG paths
│   ├── enrich_media.py    # yt-dlp: auto-find + vet walks and live cams  ★
│   ├── enrich_monuments.py# yt-dlp: auto-find + vet 🏛️ landmark tours     ★
│   ├── build_monuments.py # hand-curated monument tabs (beats the above)
│   ├── prune_media.py     # re-apply today's rules; drop picks that now fail
│   ├── check_trips.py     # every trip stop must resolve to a real place  ★
│   └── (v1 data builders: fetch_windy.py etc.)
└── backend/               # optional FastAPI proxy for Ask-the-Guide
```

### The map engine (why the glitches can't come back)

`js/worldmap.js` draws pre-projected country shapes from `assets/world.json`
(Natural Earth I, baked by `tools/build_worldmap.py`) into a single SVG and
projects only city dots at runtime. There are **no tiles, no clustering plugin, no
bounding-box camera fits**:

- World view shows **one gold node per country** (sized by place count). Clicking
  it glides *into that country* — deterministic, never into the ocean.
- Zoomed in, real **city dots** appear (red = live cam, green = has walk), labels
  fade in deeper. Click a dot → arrive.
- Pan = drag, zoom = wheel-toward-cursor / buttons / double-click; all camera moves
  are one rAF viewBox tween. Software-rendering safe: flat fills, non-scaling
  strokes, no filters, no infinite animations.
- The same engine runs the City Guesser in `pick` mode — clicks return exact
  lat/lng through the projection inverse.

### Scene resolution (`js/lib/media.js`)

Per scene, curation beats automation:

```
walk   : loc.walk   (hand-curated) → media.json walk   → none
live   : loc.webcam (hand-curated) → media.json live   → none
window : loc.window (hand-curated) → media.json window → none
```

🔴/🪟 must be **live streams** — the recorded-loop and day-timelapse tiers of v1
were removed by owner decision (2026-07). Windy embeds were cut too: their "live"
player is a poster frame that links out to windy.com and never autoplays a stream
(`data/windy.json` stays on disk as an archive but is not fetched). A rotted
YouTube id removes its own tab at runtime (`yt.js` onError) instead of showing a
broken frame.

### The enrichment pipeline ★

```bash
python3 tools/enrich_media.py --tag famous --max 60   # or --only rome,paris
```

For each city, `yt-dlp` (no API key) searches YouTube for walking tours and live
cams, then **vets before it ships**: embeddable, not age-gated, duration sane,
title matches the place, walks ≤ ~6 years old, and cams `is_live` **at vet time**.
Street-level vs window vantage is classified from the title. Results land in
`data/media.json` (checkpointed per city, resumable), which the app merges under
hand-curated fields — so a bad auto-pick is always overridable in the region JSON.

Cam search asks several ways on purpose. A single `"{name} live cam"` returned
**zero** live results for Copenhagen, Kraków and Marrakesh while `"webcam live"`
and `"live webcam 24/7"` surfaced real streams for the same cities — YouTube
ranks those phrasings almost independently — so the hunt also tries the local
language (`kamera na żywo`, `ライブカメラ`, `cámara en vivo`) and the place's own
top landmark, which is what cam operators actually name the stream.

Three guards keep the cam seats honest, each one added after a real bad pick:

| Guard | Caught in the wild |
|---|---|
| `AGGREGATOR_CAM` | "1200 TOP LIVE WEBCAMS around the World" sold as one city's window — it *is* live, it just isn't **there** |
| `WILDLIFE_CAM` | a kestrel nest box at the UN as **Vienna's** live cam; peregrine boxes as San José's *both* seats; an otter tank as Seattle's window (exempt for `nature` places — `wild.json` exists so animal cams can be their own destination) |
| US postal abbreviations | Manchester **England** showing feeds from Manchester **NH** and Manchester **IA** |

`prune_media.py` re-applies the current rules to what is already on disk and
deletes whatever no longer passes — `media.json` is a checkpoint, so without it
a pick made under looser rules would live forever. `--network` also re-checks
`is_live`, retiring cams that died since they were verified.

### Monuments ★

```bash
python3 tools/enrich_monuments.py --tag famous --per-city 3 --max 90
```

196 places already carried curated `highlights` naming their real landmarks
(Château Frontenac, Lincoln Memorial, Liberty Bell) while only 30 had monument
tabs. Those names are the search terms. Each candidate is vetted at the same bar
as a walk and then **ranked by resolution**, because the whole point of a
monument tab is clear footage — a 4K walk-through beats a 720p slideshow. A
landmark that can't be verified simply gets no tab.

For a city, the city is not its own monument. For a **ruin** it is: Nan Madol and
Göbekli Tepe have no sub-landmarks to list, which is much of why `ancient.json`
sat at 0.72 scenes per place — so those search their own name.

Auto picks are written `"source": "auto"` and carry `start: 0`. We can verify
*what* a video shows but not *where it gets good*; claiming a hand-picked moment
nobody watched would be the same species of lie as a fake live cam. Curation
still wins — `build_monuments.py` keeps its hand-timed entries first and
preserves auto ones after them (cap 5), so the two tools compose instead of
clobbering each other. Promote a good auto pick by moving it into that file's
`MAP` with a real `start`.

### Trips ★

```bash
python3 tools/check_trips.py --scenes    # exits 1 if any stop is unknown
```

`data/trips.json` holds 15 hand-ordered routes. A trip stores only **place ids**
plus a one-line note per stop, so it can never invent a destination — it can only
point at somewhere the atlas already goes. `js/lib/trips.js` resolves those ids
against the loaded places; a stop that doesn't resolve is dropped loudly to the
console rather than rendered as a placeholder, and `check_trips.py` makes that
path unreachable in a shipped build. That check matters more than it looks: a
typo'd id yields a route that still renders, still looks fine, and quietly skips a
city — the same failure mode as a fake live cam, so it gets the same treatment.

**Distance is computed, never authored** — the sum of great-circle hops between
consecutive stops. That is *not* road or rail mileage (the Grand Circle drives
~2,250 km but measures 1,127 km this way), so the UI always says "as the crow
flies". Authored mileage would rot the moment a stop changed; this can't.

Each trip reports what it can honestly show — `🚶10 🚗10 🔴7 🪟6 🏛️10` for the Euro
Trip, and a dimmed `🔴0 🪟0` for the Balkan Run, which genuinely has no verified
live cam on it. Cards use stop 1's photo unless an optional `hero` stop id says
otherwise (the Grand Circle starts in a Las Vegas car park).

Arriving from a trip carries `&trip=` into the location page, which turns the
place into "stop 4 of 10" with prev/next along the route. Nothing is stored for
that — the route lives in the URL, so a shared link drops someone into the same
place on the same trip. A place that sits on a route but was reached directly
still says so, which is how most people find the trips at all.

---

## Quick start

```bash
cd oneworldtour
python3 -m http.server 8099 --bind 127.0.0.1
# open http://127.0.0.1:8099
```

No install, no keys. (Serve it — don't open `file://` — it fetches local JSON.)

Optional Ask-the-Guide backend:

```bash
cd backend && pip install -r requirements.txt
ANTHROPIC_API_KEY=sk-... uvicorn server:app --reload --port 8000
```

Rebuilding the map asset (only needed if you want fresher borders):

```bash
curl -L -o /tmp/w.json https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json
python3 tools/build_worldmap.py /tmp/w.json assets/world.json
```

---

## External services (all free, keyless at runtime)

Open-Meteo (weather/timezone) · Wikipedia/Wikimedia (summaries, photos) ·
Radio Browser (live radio) · GDELT (headlines; rate-limits → section hides
honestly) · open.er-api.com (FX) · YouTube embeds (walks, monuments, live cams,
most TV) · broadcaster HLS streams + hls.js from jsdelivr (lazy, only for
non-YouTube state TV: RT, KCTV) · Claude API (optional guide backend).

---

## Adding / fixing a place's scenes

1. `data/<region>.json` → the place entry.
2. `"walk": "<yt-id>"` · `"webcam": "<yt-id>"` (street live) ·
   `"window": "<yt-id>"` (live window vantage) · `"monuments": [{name, yt, start?}]`.
3. Hand-curated always wins over `media.json`. Verify ids before committing
   (oEmbed 200 + actually live for cams). Reload — no build step.

Or just run the enrichment tool and review its picks in `data/media.json`.

---

## Data & privacy

Progress lives in your browser's localStorage (`owt_visited`, `owt_saved`,
`owt_notes`, `owt_last_window`, …— unchanged from v1, so old stamps survive).
Nothing is uploaded.

*A joint creative project. Built to make the whole world feel a little closer.* 🌍
