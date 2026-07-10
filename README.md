# 🌍 One World Tour

Step into 345 places across 89 countries — **walk their streets, watch their
intersections live, look out their windows live**, tune into their radio, and read
their news — all in-app, all real. Inspired by
[virtualvacation.us](https://virtualvacation.us/), rebuilt to be better: every scene
is seekable, every "live" is actually live, and every gap is honest.

> **v2 — full redesign (2026-07).** Leaflet + markercluster are gone; the glitchy
> raster map is gone. The app is now a framework-free ES-module app with its own
> SVG map engine, a tabbed scene "stage" per place, and a yt-dlp pipeline that
> auto-finds and vets walking tours + live cams city by city.

---

## The product in one idea

Every place has up to **three real scenes**, one tap apart, on one stage:

| Scene | What it is | Rule |
|---|---|---|
| 🚶 **Walking tour** | Real recent footage of walking that place — muted, fully seekable | never a slideshow |
| 🔴 **Live cam** | A 24/7 live stream at street / intersection level | must be live **right now** |
| 🪟 **Window** | Also a **live** stream — the out-a-window vantage: skyline, rooftop, harbor | never a loop, never a timelapse, never a still |

Famous cities also get 🏛️ **monument tabs** (Colosseum, Pantheon, Eiffel Tower…) on
the same stage — switch between the walk and each landmark tour like TV channels.

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
  currency + live FX, dish), live local radio, headlines, photo gallery, procedural
  ambience, Ask-the-Guide (optional Claude backend), and a "Nearby from here" rail.
- **Virtual Window** (`window.html`) — a framed, chrome-free **live** window with a
  local-time + weather sill plate and "open another window" world-hopping.
- **City Guesser** (`guess.html`) — dropped into a mystery scene (the walk video,
  title hidden), pin the world map, scored on great-circle distance, 5 rounds,
  spoiler-free emoji share.
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
│   │   ├── api.js         # weather / wiki / radio / news / FX (all keyless)
│   │   ├── photos.js      # lazy Wikipedia thumbnails (flag/map-aware) + cache
│   │   ├── state.js       # localStorage passport (same owt_* keys as v1)
│   │   ├── culture.js · radio.js · soundscape.js · dom.js
│   └── pages/             # one module per page
├── data/
│   ├── index.json         # region registry
│   ├── <region>.json      # 345 places (curated walks/webcams/monuments live here)
│   ├── windy.json         # retired Windy index — kept as archive, not loaded
│   └── media.json         # yt-dlp enrichment sidecar (auto-found, vetted scenes)
├── assets/world.json      # pre-projected country outlines (see build_worldmap.py)
├── tools/
│   ├── build_worldmap.py  # TopoJSON → Natural-Earth-projected SVG paths
│   ├── enrich_media.py    # yt-dlp: auto-find + vet walks and live cams  ★
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
honestly) · open.er-api.com (FX) · YouTube embeds (walks, monuments, live cams) ·
Claude API (optional guide backend).

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
