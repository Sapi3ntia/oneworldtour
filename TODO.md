# 🌍 One World Tour — Ideas & Guardrails

A short, living document. Two parts: **ideas not yet built** (the fun part) and a
compact **don't-break-these** list (hard-won, keeps regressions from coming back).
No sprawling manual — read the code; it's vanilla HTML/CSS/JS with comments.

---

## What it is

A static, no-build travel site: a clustered world map → a per-place page that lets you
*be there right now*. Vanilla JS only (Leaflet + the YouTube IFrame API are the only
libs). Serve it and open it:

```
python3 -m http.server 8099 --bind 127.0.0.1   # then http://127.0.0.1:8099/
```

### The four principles (every feature honors these)
1. **In-app, no off-site redirects.** Embed the real thing, or honestly say it doesn't
   exist yet. No "watch it on YouTube ↗" escape hatches.
2. **No fake or forever-loading states.** Honest empty states only.
3. **Skippable / seekable.** The walk keeps native controls — that's the edge over
   virtualvacation.us (their videos give you none).
4. **Alive.** Live local time, weather, radio. A place should feel like *right now*.

---

## The place page — how it's laid out now

Three fixed frames, same position for every city (predictable, not shuffled):

- **Frame 1 · 🚶 Walking tour** — the big hero. No walk yet → the arrival photo (📷),
  honestly chipped. Live clock + weather float over it.
- **Frame 2 · 🔴 Live cam** — a real curated YouTube live stream, or an honest
  placeholder. *Only* real streams sit here.
- **Frame 3 · 🪟 Window** — smaller. A looping curated "out-the-window" clip
  (virtualvacation-style, chrome-free), or an honest empty window. Curated YouTube only —
  no Windy on this page.
- **🏛️ Monuments** — tabbed below (tabs appear when a city has more than one).

Media resolution lives in `js/webcam.js` + `js/location.js`; the honest-fallback
(rotted YouTube id → honest empty frame) is `js/ytembed.js`.

### The window frame is curated-YouTube only (Windy dropped here — decided)
The location-page 🪟 window shows **only a curated, looping YouTube clip** (chrome-free).
Windy was **dropped from this frame** by owner decision: its embed forces the windy.com
logo (attribution ToS) and is a tap-to-play widget with off-site links — not honest as an
always-on window. A place without a curated `ambient`/`webcam` clip now shows an **honest
empty window**, never someone else's branded static frame. The cure is content: add more
`webcam` (🔴 live) / `ambient` (🪟 loop) ids and real windows fill in city by city.

> Windy is **still used** by the standalone **Virtual Window** (`window.html`) and the
> map's 🪟/🔴 marker badges via `js/webcam.js` (`forWindow`/`liveFor`/`windowFor` +
> `windyLiveFor`/`windyWindowFor`) — that's deliberate; only the *location page* frame
> dropped it. Revisit those surfaces separately if the logo should go site-wide.

---

## 🎯 Ideas not yet built

### Content depth (the steady grind — "beef it up")
- 🚶 **More walks** — ~60 of 345 places have one. Method: `WebSearch → YouTube oEmbed
  vet → add `loc.walk``. Next obvious set: SE-Asia capitals, secondary LatAm/Africa
  cities (Medellín, Cartagena, Casablanca, Mombasa…). Look up the real `id` in the region
  file first.
- 🏛️ **More monuments** — most cities have none. Author 1–3 each for marquee cities
  (Sydney→Opera House, Dubai→Burj Khalifa, Cape Town→Table Mountain, Agra→Taj Mahal…).
- 🪟🔴 **More curated windows & live cams** — now the *only* way a place gets a location-
  page window or live cam (Windy was dropped from that page). Add a `webcam` (🔴 live) or
  `ambient` (🪟 loop) id to fill an empty frame.
- ✍️ **Author `highlights` + `blurb`/`fun_fact`** for content-thin marquee places (they
  fall back to the live Wikipedia summary today — honest, but the big ones deserve copy).

### Creative map ideas (additive, none touch the stable core)
- **Cluster hover / long-press preview** — a small popover listing the cities in a bubble.
- **"Spin the globe"** — fly to a random *cluster*, not just a pin.
- **Visited-progress heat** — tint clusters by how many of their cities you've explored
  (`_visited` is already tracked; `owt-cluster-done` exists for all-visited).
- **Live-content badges** — when the 🔴/🪟 filter is on, badge clusters with a live count.

### Bigger swings (only when asked — none are built)
- 🕰️ **"Back in Time" — borders through history.** Scrub a year slider; political
  boundaries morph through wars/treaties/partitions, back to the original Indigenous /
  First Nations territories of North America. Big lift: time-indexed GeoJSON polygon
  layers + a timeline UI (not point markers). Data leads: native-land.ca (has an API —
  treat Indigenous data with care + clear sourcing), historical-basemaps, Natural Earth.
  Probably its own "History" mode.
- 🛰️ **Richer walkthroughs** — satellite "descend-from-orbit" zoom (Esri World Imagery),
  360° photospheres (Pannellum) for Wikimedia 360s, Mapillary/KartaView street-level for
  trails & ruins Street View misses, optional narrated mini-tour via `SpeechSynthesis`.
- 🤫 **Ancient Apocalypse depth** — episode titles, "mainstream view vs Hancock's claim"
  as two explicit lines per site.

**Parked / declined:** standalone "descend from orbit" mode (we have the map);
multiplayer Guesser rooms (big lift).

---

## 🛑 Don't break these (measured, learned the hard way)

**The owner's machine renders in SOFTWARE (VM, no GPU).** Anything that's smooth on a
GPU can tank here to 25–40fps. Specifically:
- **No `backdrop-filter` anywhere.** **No infinite `box-shadow`/paint animations** on map
  markers. Keep Leaflet `zoomAnimation:false` + `fadeAnimation:false`.
- **When something "feels slow/glitchy," measure frame times (rAF) and screenshot real
  viewport widths.** A console-error sweep proves no JS errors and *nothing* about lag or
  layout overlap — that mistake shipped "verified" bugs twice.

**Map clustering:**
- **Per-continent cluster groups** (`clusterGroupFor` keys on `loc.continent`). One world
  group merged Iberia+Morocco / Balkans+Egypt across the sea and drew "Europe" bubbles
  over Africa. Never collapse back to one group.
- **Never `zoomToBounds`/`fitBounds` on cluster click.** Fitting the members' bounding box
  centres the camera on its *midpoint* — open ocean for any dispersed cluster (the
  recurring "click a circle, get thrown into the water / Ireland in Africa" bug). The
  handler zooms *toward the clicked bubble* or spiderfies in place. See `map.js` →
  `clusterclick`.
- **`animate:false` on the cluster group; never add `disableClusteringAtZoom`.** Both
  caused "pins slide / everything vanishes on zoom."
- The map needs the **borders/labels overlay** — bare dark tiles make a correct pin look
  like the wrong country. **Esri tile URL is `{z}/{y}/{x}`** (y before x), unlike CARTO.

**Media honesty:**
- **"Live cam" must be actually live.** A YouTube oEmbed 200 only proves *public* — check
  `"isLiveNow":true`. A frozen webcam widget is never allowed in the 🔴 live frame.
- **No still ever stands in for a window** (a Wikipedia lead image is often a map/globe).
- Curated ids rot — keep the `ytembed.js` `onError` → honest-empty path (the location
  page drops a rotted frame straight to its empty state; no Windy substitute there).

**Env / tooling:**
- **Serve on `127.0.0.1:8099`, not `0.0.0.0`** (sandbox classifier blocks `0.0.0.0`).
- Everything is **keyless at runtime.** `tools/*.py` are hand-run build helpers;
  `tools/windy.key` is build-time only and gitignored. Region JSON is HTTP-cached —
  hard-refresh after editing a data file.
- **Don't re-run the stale one-off builders** (`build_europe.py`/`build_usa.py`) — they
  clobber the normalized, enriched live JSON.
- Verify headlessly with chromium + CDP (see `scratchpad` scripts): open a page, click to
  skip the arrival overlay, screenshot, assert on the DOM. Always *look* at the shot.

---

## Recently landed (so it isn't re-litigated)
- **Map cluster-click rewritten** — zooms toward the clicked bubble / spiderfies in place;
  never fits a bounding box. Kills the ocean/Africa jump.
- **Place page → three fixed frames** (walk hero + live + window) replacing the old
  single-hero + "More Views" shuffle. Monuments stay tabbed.
- **Windy dropped from the location-page window** — 🔴 live and 🪟 window are both
  curated-YouTube-only now (window loops chrome-free, `controls=0`); no curated clip → an
  honest empty window, no windy.com logo. (Windy still powers `window.html` + map badges.)
