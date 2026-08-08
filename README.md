# 🌍 One World Tour

Step into 540 places across 94 countries — **walk their streets, drive their
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

Three collections extend the idea (2026-07 → 2026-08):

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
- **🔭 Observatories & Telescopes** (`data/observatory.json`, 2026-08) — the places
  we built to look away from Earth, as destinations in their own right: the Very
  Large Array on the Plains of San Agustin, Green Bank inside the US National Radio
  Quiet Zone, FAST in its Guizhou sinkhole, Arecibo (the dish is gone; the site and
  the story are not), Parkes and Siding Spring, ALMA · Paranal · La Silla · Cerro
  Tololo on the Atacama ridges, Mauna Kea and Haleakalā, Palomar · Mount Wilson ·
  Lick · Kitt Peak · Yerkes · Griffith, the Sphinx bolted to its pinnacle at 3,571 m,
  Pic du Midi, Roque de los Muchachos and Teide, Jodrell Bank and Effelsberg, Royal
  Observatory Greenwich (where the prime meridian is a line in the courtyard),
  Paris, Uraniborg, the Vatican's, Sutherland, Mount John, and the two naked-eye
  instruments that predate the telescope entirely — Beijing's Ancient Observatory
  and the Jantar Mantar at Jaipur. A 🔭 map filter and an "Observatories" rail.
  Same honesty rule, and the seats mostly stay empty on purpose: a mountaintop with
  no walking tour shows *"No walking tour yet — nothing fake stands in."*

**The honesty rule:** a scene either embeds the real thing or the place simply
doesn't offer that tab yet. Nothing fake ever stands in — no stills posing as
windows, no frozen widgets posing as live cams.

---

## Pages

- **Explore** (`index.html`) — hero search with ranked autocomplete, the SVG world
  map (country nodes → glide into a country → city dots), content filters
  (🚶/🔴/🪟/🏛️/🌃/♥/🤫/🦁/🔭), and Netflix-style rails: *Start here*, *Live right now*,
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
- **Trips** (`trips.html`, `trips.html?id=…`) — 18 curated routes people actually
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
│   ├── <region>.json      # 540 places (curated walks/webcams/monuments live here)
│   ├── wild.json          # 🦁 wildlife & national-park live cams as places
│   ├── observatory.json   # 🔭 observatories & telescopes as places
│   ├── tv.json            # 📺 live national TV channels per country (verified live)
│   ├── windy.json         # retired Windy index — kept as archive, not loaded
│   ├── media.json         # yt-dlp enrichment sidecar (auto-found, vetted scenes)
│   └── media_denylist.json# ids a human watched and rejected (global + per_place) ★
├── assets/world.json      # pre-projected country outlines (see build_worldmap.py)
├── tools/
│   ├── build_worldmap.py  # TopoJSON → Natural-Earth-projected SVG paths
│   ├── enrich_media.py    # yt-dlp: auto-find + vet walks and live cams  ★
│   ├── enrich_monuments.py# yt-dlp: auto-find + vet 🏛️ landmark tours     ★
│   ├── build_monuments.py # hand-curated monument tabs (beats the above)
│   ├── prune_media.py     # re-apply today's rules; drop picks that now fail
│   ├── prune_monuments.py # the same, for 🏛️ tabs; --titles backfills them
│   ├── test_vetting.py    # the bad picks, frozen — run after any rule edit  ★
│   ├── check_trips.py     # every trip stop must resolve to a real place  ★
│   ├── verify_cams.py     # re-check the HAND-CURATED cams (prune only does media.json) ★
│   └── (v1 data builders: fetch_windy.py etc.)
└── api/
    └── ask.py             # serverless proxy for Ask-the-Guide (keeps the key server-side)
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
- Pan = drag or arrow keys, zoom = wheel-toward-cursor / two-finger pinch /
  buttons / `+`/`−` / double-click; all camera moves are one rAF viewBox tween.
  Software-rendering safe: flat fills, non-scaling strokes, no filters, and
  exactly one infinite animation (the live-cam pulse, fenced in — see below).
- The same engine runs the City Guesser in `pick` mode — clicks return exact
  lat/lng through the projection inverse.

**Hit testing is geometric, not DOM (2026-07).** Osaka was almost unclickable:
Kyoto and Nara sit a few map units away, and the browser hands a click to whatever
was *painted last*, so the neighbours ate it. Worse, dot radii were expressed in
map units and divided by zoom — at k≈40 a "4 px" dot covered a ~64 px radius, so
zooming in to separate a cluster made aiming **harder**. Two changes:

- `_pickTarget()` resolves a click to the **nearest centre** within a radius
  (Voronoi-style), not to the topmost painted node. Both marker layers are
  `pointer-events: none`; `elementFromPoint` is only consulted for land/sea.
- `DOT_PX = 4` / `HIT_PX = 12` are **real screen pixels at every zoom** —
  converted through `_u` (a ResizeObserver-cached measurement, so the rAF loop
  never reads layout). The tap target is a constant 12 px; neighbour separation
  grows with zoom the way you'd expect (Toronto cluster: 3 px apart at k=3,
  35 px at k=40).
- `.wm-hot` — not CSS `:hover` — highlights the marker, driven by the *same*
  hit test. The highlighted dot is therefore always the one a click would take,
  which `:hover` could not promise inside a tight cluster.

**Labels are label-sized too (2026-07).** Same bug one layer up, and it survived
that pass. A city name is drawn with a dark outline so it reads over land — a
`stroke` on the `<text>`, and a stroke lives in **map units**. The font-size was
divided by the zoom; the 2.5 stroke-width was not. So zooming into Japan grew
each name's outline to a ~60 px black slab that swallowed Tokyo, Osaka and Kyoto
whole. (They stayed clickable the entire time — hit testing is geometric — you
just couldn't see what you were aiming at.) `HALO_PX = 2.5` is now re-pinned
through `_u` every zoom, exactly like `DOT_PX` and `HIT_PX`.

With the slabs gone the plain text still collided, so `_placeLabels()` decides
each frame which names get printed:

- every dot in view claims its patch **first** — a caption may cover another
  caption, never a place you could have clicked;
- names go out in a fixed priority order (`famous` outranks `hidden`, then scene
  count, then id — global and stable, so panning can't make two neighbours swap
  captions frame by frame), each trying the right of its dot and then the **left**
  (that flip is what keeps Osaka *and* Nara named, 14 px apart);
- a name with nowhere clean to sit isn't drawn. Its dot, tooltip and click target
  stay, and hovering gives the name back.

Boxes are estimated from the character count, never measured — `getBBox()` on a
few hundred `<text>` nodes would force a layout flush on every tween frame, the
exact thrash this engine exists to avoid. Measured cost of the whole pass in the
worst view we ship (117 places on screen over Europe): **~0.8 ms**.

**Per-frame work is bounded by the viewport (2026-07).** `_applyZoomStyling()`
runs on every frame of every tween, and it used to write four attributes to all
377 dots — to resize the ~340 the camera had clipped away. It now walks
`_inView()` instead: the dots inside the viewBox plus 15 %.

That turned out to be a correctness rule, not just a saving. A marker you stop
restyling keeps the size it last had, **in map units** — and a dot sized for the
world view is ~3 units across, which at k = 40 is a 200 px disc. Tokyo, sitting
just past the top edge, painted a red blob over the Kanto coast; a stale caption
would have bled its halo in the same way. So markers are **born parked**
(`display: none`) and mounted only while the camera contains them. Off-screen
means not drawn, so no off-screen size can leak in.

Measured on this machine, restyle + forced style/layout flush per frame:

| view | places mounted | viewport-bounded | whole atlas |
|---|---|---|---|
| Europe, k≈7.7 | 110 / 377 | **3.2 ms** | 6.6 ms |
| Japan, k≈25 | 5 / 377 | **0.4 ms** | 7.2 ms |

The win grows with zoom, which is where the tweens actually live.

**A live cam should look alive (2026-07).** `🔴 streaming right now` is the thing
this atlas has that an atlas doesn't, and it was rendering as one more coloured
dot. Live dots now carry a slow pulse ring (2.4 s, staggered by a negative
`animation-delay` so a cluster shimmers rather than blinks in unison). It is the
engine's *only* infinite animation, so it is fenced in accordingly: mounted only
on live dots **currently in view**, dropped entirely under
`prefers-reduced-motion: reduce` — re-checked live, since that preference can be
toggled mid-session — and drawn in its own layer beneath the dots, because
`_setHot()` re-appends a city group to raise it and a re-append restarts a CSS
animation (the ring would visibly stutter every time the cursor passed).

**Keyboard and touch parity (2026-07).** The map was pointer-only. Two gaps:

- **Touch could pan but never zoom.** Only `wheel` was bound, and fingers don't
  emit one, so a phone could reach the country nodes and go no further. Pointer
  events are now tracked in a map: one is a drag, two are a pinch, and lifting one
  finger re-seats the drag under the survivor instead of jumping.
- **The keyboard could do nothing at all.** The container is now focusable with
  `role="application"` (so a screen reader doesn't swallow the arrows for its own
  cursor): arrows pan, `+`/`−` zoom, `0` goes home, `n`/`p` walk the places in
  view, `Enter` opens the highlighted one — or, in the Guesser, drops the guess at
  the centre crosshair. The walk drives the *same* `.wm-hot` highlight the cursor
  does, so what a screen reader announces through the `aria-live` region is always
  what `Enter` would take.

**Country names in city mode (2026-07).** Past `COUNTRY_K` the gold nodes are
gone and the coastline is the only clue left — fine over Italy, useless over the
Balkans. Hovering land now names the country and how many places we hold there.
Natural Earth spells four of them differently from our data (`LAND_ALIAS`); four
more have no polygon at this resolution and simply never match. In `pick` mode
this is deliberately **off** — naming the land is the one thing the City Guesser
must never do.

**Some places can't be separated by zooming (2026-08).** Cape Town, Table
Mountain and Camps Bay are 5 km apart. Every fix above makes crowded dots
resolve *as you zoom in* — but these three are 0.08–0.14 map units apart, which
is 5 px at the old ceiling of k = 40 and still under one dot's width at any zoom
this camera could reach. Three places, one dot. The zoom ceiling went to
**k = 90** (which buys the trio 11 px, not enough on its own), and the rest is
handled by **fanning**:

- `_buildFans()` runs once, at data time: single-linkage clustering (grid buckets
  + union-find) over places within `FAN_U = 0.34` map units — about 14 km, i.e.
  *"the same spot"*, not *"the same region"*. Membership is **static** on
  purpose. Groups that re-form during a zoom would make dots jump.
- `_fanOut()` slides each member toward its own slot on a small ring around the
  group's centroid, sized so neighbours sit `FAN_PX = 15` screen px apart. Slots
  are dealt in order of true bearing from the centroid, so a dot never crosses a
  sibling on its way out. Each keeps a hairline **leader** back to where it
  really is — a 5 px stub for a trio, a legible starburst for the 9 places
  crowded onto Hong Kong island, which is the right way round: the cue appears
  exactly when the nudge is big enough to matter.
- The fan **lets go** as real geography opens up: the group-wide blend `t` falls
  to 0 once its tightest pair is genuinely `FAN_OFF_PX = 30` px apart, so zooming
  really does resolve a cluster and the fan only covers the last stretch the
  camera can't.

Two things that ramp had to be argued into. A **per-member** `t` let Victoria
Peak and Cheung Chau land **0.8 px apart at k ≈ 38** — members relaxing at
different rates cross each other. `t` is now group-wide. And releasing at
`FAN_PX` rather than `2 × FAN_PX` made drawn separation *dip mid-ramp*
(`15·[1 − τ + τ²]` bottoms out at 11.25 px): the dots slide in straight lines, so
the halfway point is tighter than either end. At `FAN_OFF_PX = 30` the
derivative `2(D−F)(τ−1)` is ≤ 0 throughout and the ramp is monotone.

Driving the real module under a DOM shim over all 540 places — 27 groups, 71
dots fanned, largest group 9 — the measured result across k = 3…90 is: **worst
drawn separation 14.9 px** (any pair, any group, any zoom), **426/426**
centre-aimed clicks resolve to the dot aimed at, and **0** of the 469 unfanned
dots move by so much as a sub-pixel. Raising the ceiling also meant pinning
`flyToPlaces`' fit floor to its own constant (`FIT_MIN_W = 75`); it was derived
from `K_MAX`, so a deeper ceiling would have silently changed how far every
country click zooms.

### Scene resolution (`js/lib/media.js`)

Per scene, curation beats automation:

```
walk        : loc.walk        (hand-curated) → media.json walk        → none
drive       : loc.drive       (hand-curated) → media.json drive       → none
live        : loc.webcam      (hand-curated) → media.json live        → none
window      : loc.window      (hand-curated) → media.json window      → none
night_walk  : loc.night_walk  (hand-curated) → media.json night_walk  → none
night_drive : loc.night_drive (hand-curated) → media.json night_drive → none
```

🔴/🪟 must be **live streams** — the recorded-loop and day-timelapse tiers of v1
were removed by owner decision (2026-07). Windy embeds were cut too: their "live"
player is a poster frame that links out to windy.com and never autoplays a stream
(`data/windy.json` stays on disk as an archive but is not fetched). A rotted
YouTube id removes its own tab at runtime (`yt.js` onError) instead of showing a
broken frame.

**That runtime check is not redundant with the pipeline's.** yt-dlp reports
`playable_in_embed: true` for videos that still throw **error 150** the moment an
embedded player calls `playVideo()` — a rights-holder block that is only
observable in a real browser embed. Cancún's first Coco Bongo pick looked clean to
every offline check and died on mount. So `yt.js` onError is the last line of the
honesty rule, not a belt-and-braces nicety.

### After dark ★

Night is **not** a fifth and sixth pane. It's the same walk and drive seats with
the lights off, so the stage keeps its exact four-pane geometry and only swaps
what's mounted in the two seekable seats:

| Seat | By day | After dark |
|---|---|---|
| top-left | 🚶 walking tour | 🌙 night walk |
| top-right | 🚗 driving tour | 🌃 night drive |
| bottom-left | 🔴 live cam | 🔴 live cam — *unchanged* |
| bottom-right | 🪟 window | 🪟 window — *unchanged* |
| chip bar | 🏛️ monuments | 🍸 nightlife venues |

The two live seats deliberately have **no night twin**: a live cam is already
whatever time it is there, so labelling one "night" would be a promise the feed
can't keep for more than a few hours a day. They are also left mounted across a
mode switch — remounting would restart the stream for nothing.

`loc.nightlife` reuses the `{ name, yt, start }` shape of `loc.monuments` on
purpose, so venues ride the same chip bar and the same borrowed walk seat. The
☀️/🌙 switch lives at the head of that same bar — no new row, no new section,
no second grid.

The stage **opens after dark by itself** when it's actually dark there, using the
`isDay` flag `api.weather()` already returns; an explicit click pins the choice.
Home gets a 🌃 After dark map filter and rail off `sceneFlags().night`.

```bash
python3 tools/enrich_media.py --need night --only osaka,tokyo,seoul --max 50
```

Night seats are **opt-in** in the enricher (`--need night`, or `night_walk` /
`night_drive` individually) rather than part of the `any` sweep — otherwise every
city without one would read as permanently incomplete. They call the same
`find_seekable()` as the day seats with one extra filter, `also=NIGHT_WORDS`, so
they inherit every guard the day seats earned for free.

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

Guards keep the seats honest — each one was added after a real bad pick:

| Guard | Caught in the wild |
|---|---|
| `AGGREGATOR_CAM` | "1200 TOP LIVE WEBCAMS around the World" sold as one city's window — it *is* live, it just isn't **there** |
| `WILDLIFE_CAM` | a kestrel nest box at the UN as **Vienna's** live cam; peregrine boxes as San José's *both* seats; an otter tank as Seattle's window (exempt for `nature` places — `wild.json` exists so animal cams can be their own destination) |
| US postal abbreviations | Manchester **England** showing feeds from Manchester **NH** and Manchester **IA** |
| `scrub_persons` | **a person is not a place.** "Mississauga 4K Drive \| Hwy 403 → Winston Churchill" shipped as the driving tour of Churchill, **Manitoba** — a 900-person Arctic town. `scrub_streets` only fires when the road type is spelled out, and this title never says "Blvd". Deliberately excluded: `saint`/`st` (Saint Petersburg, St John's) and bare given names that are real places on their own (Victoria, Nelson, Charlotte) |
| `BAD_NIGHT` | night seats only: "Saturday Night Live", "A Night at the Museum", `nightcore`, "3 nights in…" — "night" in the title that isn't the time of day |
| `daylight_title` | the mirror of the night rule, and the one that was missing: **Las Vegas offered "Las Vegas 4K - Midnight Drive" as its Driving tour**, and the same video as its Night drive. A day seat has to be daylight. `DAY_WORDS` rescues honestly mixed titles ("Jaipur Daytime and Evening Walk" really is a daytime walk) |
| US state vs US state | the postal-abbreviation rule above deliberately skipped US places — every US cam title names a US state — so nothing compared **Flagstaff, Arizona** against Flagstaff Lake in **Eustis, Maine**, or Rocky Mountain NP against **Gatlinburg, Tennessee**. Now it compares against the place's own `region`, and a title where our name is still the headline is exempt ("Flagstaff, Arizona \| LIVE Train Camera" stays) |
| `re-?live` / `digest` / `tv\d` / `model rail` / `fr24` | streaming right now, and still not a view of the place: **"RE-LIVE Planespotting at Frankfurt Airport"** is genuinely live and genuinely a replay; TV7 is a Bordeaux television channel; the Oklahoma Model Railroad Association's PTZ cam is pointed at a model |
| disaster words / `documentary` | a newsroom pointing a camera at a place is not that place's cam: **"France Wildfires LIVE \| Macron Declares Emergency! Giant Fire Threatens Bordeaux"** passed every earlier rule — it is live, and it does name Bordeaux. Same for a deep-ocean **documentary** looping as the Great Barrier Reef |
| `feeds from … and more` | an open-ended list of places is a rotator no matter how few it names: "Ukraine LIVE HD Camera Feeds from Donetsk, Sumy, Kyiv, Kharkiv **and more**" is not Kyiv's cam |
| **distinctive tokens only** | the big one from the 2026-08 China sweep. A title used to match a place on *any* word of its name longer than three letters — so **"Mount Athos Healing Prayer"** became **Mount Tai's** live cam, **"Driving Tour Along the Yellow River Highway"** became **Li River's** drive, and a **Hong Kong Island** drive became car-free **Lamma Island's**. Strip the short word and `mount`, `river` and `island` are all that is left of those names. Now only tokens outside `GENERIC_TOKENS` count, and a place with none has to be named in full — with the trailing feature noun optional, so "Driving Through Ha Long" still counts for **Ha Long Bay** |
| Canadian provinces | the US-abbreviation rule's mirror: **"Ross Bay, Victoria BC"** shipped as **Victoria Peak's** window. `ON` is deliberately *not* in the abbreviation list — ", on" is ordinary English in a way ", BC" never is |
| lottery streams | a draw streams 24/7 and names its city, but it is a studio ticking numbers: **"LIVE DRAW TOTO MACAU"** as **Macau's** window |
| `abandoned` / `urbex` | urbex is a subject, not a drive: **"Road Trip: Exploring abandoned mountainside CCP Buildings (Nanchang)"** as **Nanchang's** driving tour |
| `music_loop_not_a_cam` | **"24/7 Chill Italian Vibes & Mediterranean Music 🎶 Scenic Amalfi Coast & Lake Como Relaxation 4K"** — two coastlines 700 km apart under a backing track — as the **Amalfi Coast's** live seat. A pair of conditions, not a word list: a music framing *and* no claim of a camera anywhere in the title, which is what lets "Hong Kong's ONLY 24/7 LIVE camera from The Peak with Relaxing Music BGM" through. "Chill" alone doesn't count either — it describes the scene as often as the soundtrack, as in **Malta's** real "LIVE 24/7: Malta Ship Spotting by day, chilling by night" |
| `city_tour_of_the_wild` | a city tour standing in for somewhere it isn't — **Zhangye's streets** as the walk for **Zhangye Danxia**, the rainbow-striped landform park outside the city (Zhangye is the park's own first highlight, so the phrase matched), and **downtown Brantford** as **Brant Conservation Area's**. Only fires when the title never names the place itself, because plenty of `nature`/`mountain`/`desert` entries genuinely *are* towns ("Downtown SEDONA", "Flagstaff — 4K Downtown Drive") and plenty of honest drives merely start in one ("from Downtown Yan'An to China's Famous Hukou Waterfall") |

A **landmark** may still anchor a title — a region entry has no other way in, since
Catalonia can only ever be filmed as Barcelona and Cinque Terre as Vernazza — but
the landmark now needs a distinctive token of its own. Wuzhen's first highlight is
"Grand Canal", so `Grand Canal live webcam` returned a **Venice** hotel feed and
the phrase matched it happily.

That inheritance used to be the one hole left open, and it is now closed by
`INHERITS_HIGHLIGHTS` — an explicit list of the places whose highlights lie
*inside* them. It has to be explicit. Nothing in the data separates a container
from a site: `type` calls both `catalonia` and `zhangye-danxia` `nature`, and
`region` is the administrative one, so the French Riviera's says
"Provence-Alpes-Côte d'Azur". Until the list existed, every site quietly borrowed
its neighbour's footage — Dunhuang's city drive as **Mogao Caves'**, Jiaxing's as
**Xitang's**, Luoyang's as **Longmen Grottoes'**, a Lake Powell marina cam as
**Antelope Canyon's**, a walk through Brantford as **Brant Conservation Area's**,
and, five thousand kilometres out, *"Plaza de Armas de Querétaro en vivo"* as
**Cusco's** live cam, on a plaza name half of Latin America shares.

Adding an id to that list is a claim about geography, so leaving one out is the
safe direction: it costs a scene, and a missing scene is an honest gap. Four
picks that the rule would have cost were kept by naming them in `ALIASES`
instead — each was anchored on a province ("Tibet", "Beijing", "Guizhou") that
proves nothing, yet each title *does* name the place, just not the way the corpus
spells it: `Nam co` for **Namtso**, `爨底下` for **Cuandixia**, `Fanjing` for
**Fanjingshan**.

One more matching bug fell out of that sweep, worth naming because it is
invisible: a **possessive** apostrophe welds the `s` onto the word, so
"Mallorca's Crazy Snake Road" searched for `mallorcas` and **Balearic Islands**
lost a drive that is plainly Mallorca's. `Portugal's Coast` was hunting for
`portugals` and had matched nothing by its own name since the day it was added.

#### `data/media_denylist.json` — the reviewed rejections ★

Heuristics can't see that a cam captioned "Monteverde" is a *barangay in the
Philippines* rather than the cloud forest in Costa Rica, or that explore.org's
"Utopia Village reef cam" is in **Belize**, not on the Great Barrier Reef. Some
bad picks only give themselves away to a person who opens them.

Without a memory of that judgement the next sweep finds the same video again, so
reviewed rejections live in `data/media_denylist.json` as `id → why`. It outranks
every heuristic in **both** tools: `enrich_media.py` never proposes a denied id,
`prune_media.py` deletes one it finds. Only ever add an id you actually watched.

A **global** ban is the wrong shape for the commonest failure, though, which the
2026-08-07 observatory sweep made obvious: the video is honest, just not *here*.
"Walking tour of the Mt Wilson Observatory" is exactly right for
`mount-wilson-observatory` and completely wrong for **Yerkes**, which the same
sweep also gave it — 3,000 km away in Williams Bay, Wisconsin. Banning the id
would have deleted the good seat to fix the bad one. So the file also carries
`per_place`, keyed `place id → {video id: why not here}`, checked by the same
`em.denied(place, vid)` in both tools:

```json
"per_place": {
  "la-silla-observatory": {
    "<id>": "ESO's PARANAL, 600 km up the ridge — and the same tape already fills paranal-observatory's drive seat"
  }
}
```

It also covers the one case no heuristic can see: **the same camera under two
ids**. Djuma's waterhole publishes a public stream *and* an ad-free members
re-upload of the identical Gowrie dam view, and the sweep filed one as `live` and
the other as `window` — two seats, one camera, which makes one of the two labels
a lie.

`prune_media.py` re-applies the current rules to what is already on disk and
deletes whatever no longer passes — `media.json` is a checkpoint, so without it
a pick made under looser rules would live forever. It also refuses a video that
holds a seat **and** its own night twin: one tape under two labels is a lie in
one of the two seats. `--network` re-checks `is_live`, retiring cams that died
since they were verified. The 2026-07 sweep retired **39** dead feeds; the
follow-up sweep dropped **36** more picks under the rules above, and re-checked
all **178** surviving cams over the network — every one still live.

```bash
python3 tools/prune_media.py                     # dry run, title rules only
python3 tools/prune_media.py --apply --network   # also re-check is_live
```

`prune_media.py` only ever looks at `media.json`, which left a hole: the
**hand-curated** `webcam` / `window` fields in the region JSONs *outrank* the
sidecar, were verified once on the day they were added, and were then never
looked at again. A curated cam that ends its broadcast keeps being promised — a
red dot on the map, a card in "Live right now", a number in the hero stat — and
only dies honestly at runtime when `yt.mount`'s `onError` pulls its own tab.
`verify_cams.py` asks yt-dlp the same two questions the enricher asks at hunt
time (`is_live` **and** `playable_in_embed`) and `--apply` deletes what fails,
dropping the place back to whatever `media.json` can offer or to an honest gap.
First run (2026-08-07): **35 curated cams, 33 still live** — New Orleans and
Djuma (Sabi Sands) had both ended.

```bash
python3 tools/verify_cams.py                     # report only
python3 tools/verify_cams.py --apply             # delete the dead ones
```

Run it in the same sweep as `prune_media.py --network`, and **never `--apply` a
verdict you haven't re-probed on its own**: a throttled lookup returns nothing,
which reads identically to "gone".

`prune_monuments.py` is the same idea for 🏛️ tabs, and it exists because the
2026-08-01 China run shipped 69 that were not monuments. `candidate_landmarks()`
searches every `highlight`, and highlights are written for the blurbs, so the
China ones carried people, dishes, dynasties and species beside the buildings —
Foshan's "Ip Man" tab was the 2008 feature film, Haikou's "Hainanese chicken
rice" tab was a food walk in *Singapore*, Wudang's "Tai chi" tab was a 40-minute
workout. `NOT_A_MONUMENT` now covers those categories, and `is_a_region()`
rejects a highlight that names a country, province or region, filled from the
corpus so it needs no per-country list.

The name rules need no title and run first, because they are the strong ones: a
landmark that is a dish or a province has no honest video *whatever the search
returned*. The title rules need a `title` on the entry — `find_monument()` has
always returned one and the caller used to drop it, which left the entire
monument set unauditable offline. Tabs written before 2026-08-02 have none, so
backfill once:

```bash
python3 tools/prune_monuments.py            # dry run; name rules work offline
python3 tools/prune_monuments.py --titles   # fetch missing titles, ~2s each
python3 tools/prune_monuments.py --apply
```

Two bugs in the shared wrong-place guard surfaced while auditing that batch, and
both had been silently costing honest media picks too. `wrong_place_title`
compares a title's US state against `place["region"]`, and six US places — the
2026-07-18 Route 66 additions — had that field **empty**, so their own-state
exemption never fired. And `mexico-city`'s distinctive tokens reduce to just
`("mexico",)` because "city" is generic, so any title containing **"New Mexico"**
was read as a video of Mexico City. That guard has to stay asymmetric: "New
Mexico" is not Mexico, but "New York" *is* New York City, so a place may be
matched inside a `New <token>` phrase only when its own name starts with "New".

All five tools load the gazetteer through `em.register_place()` rather than
repeating the three-line dance — the duplication is precisely how a new global
like `NEW_NAMED` ends up loaded in one caller and missing from four.

`test_vetting.py` freezes the whole argument. Every `want=False` case in it is a
scene that actually shipped; every `want=True` case is honest footage that some
rule refused until it was loosened correctly. The rules only ever get stricter,
and each tightening is one character from killing good picks — the 2026-08 sweep
took four rounds to settle, undone in turn by `Kauaʻi` (whose ʻokina splits the
name), `SedonaLiveCam.com` (cam operators run words together), Malta's
"chilling by night" (a real harbour camera, not a music loop) and a Hukou
Waterfall drive that merely *starts* downtown. Run it after touching any regex:

```bash
python3 tools/test_vetting.py    # no network; exits 1 on any failure
```

Two operational traps, both of which cost time. `enrich_media.py` and
`enrich_monuments.py` each rewrite `data/media.json` **whole**, so never run them
concurrently — the second to finish wins and silently discards the other's work.
And `pgrep -f "tools/enrich_media.py"` matches the *waiting shell's own command
line*, so `until ! pgrep -f …; do sleep; done` waits forever on a process that
exited an hour earlier. Wait on the pid: `until ! kill -0 "$PID"; do sleep 30;
done`. Redirected output block-buffers too, so pass `PYTHONUNBUFFERED=1` or the
log stays empty for the entire run.

#### Why the cam seats stay empty ★

Refilling the 36 pruned seats measured something worth writing down. The
**seekable** seats came back clean, 14 for 14 — right place, daylight, recent. The
**cam** seats came back 4 for 15.

That asymmetry isn't a bug in the finder, it's the shape of what exists. A walking
tour of Vilnius has been filmed, so the finder returns it. A live camera pointed at
Olympic National Park has not — and when nothing matches, a ranked search still
returns its best-scoring candidate. So Olympic NP got Calgary's Central Memorial
Park, Glacier NP got a wolf centre in Minnesota, Porto got the **Port of Santos**,
Flagstaff got a general store in Stratton **Maine**, and London got a "virtual Tube
journey" of recorded footage. One stream reported `is_live` and served no frames at
all.

Under the honesty rule the answer for those places is the gap, and the denylist is
what makes the gap *stay* a gap across sweeps. Two consequences to expect:

- A broader query does not help. Widening the search for Vienna, Manila, Casablanca,
  Cairo and Nairobi returned a political interview, a Eucharistic adoration stream, a
  clock, and a radio station — more noise, no signal.
- The denylist grows every sweep, and that is the design. Each sweep re-hunts the
  empty seats and finds the *next*-best wrong answer; each rejection is one fewer
  wrong answer available. `live` and `window` are the two seats with no night twin
  and no fallback, so they are the two that stay honestly empty most often.

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

`data/trips.json` holds 18 hand-ordered routes. A trip stores only **place ids**
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

### Filling a region out ★

Three batches went in this way, and the rules they turned up apply to any new place.

**The Grand River watershed** (`canada.json` 17 → 36). Every Grand River
Conservation Area now exists as a place — Luther Marsh at the source down to Byng
Island at Lake Erie — with facts taken from GRCA's own property pages, and
**The Grand River Run** (`trips.json`) walks all 21 of them in river order, source
to mouth, 274 km as the crow flies.

**China** (`asia.json` 79 → 190). The six places we had were name-and-coordinate
skeletons: empty `blurb`, empty `fun_fact`, empty `highlights`, null
`hidden_gem_tip`. They're filled, and 111 more went in — the tier-one cities, the
"new first-tier" ones, the tier-2 and tier-3/4 cities nobody outside China has
heard of, the water towns, the Hui and Miao and Dong villages, the terraces, the
big nature, the grottoes, Tibet, ten Hong Kong districts and outlying islands,
and Macau. The Silk Road trip used to jump Samarkand straight to Xi'an because
the whole Chinese corridor was missing; it now runs Kashgar → Turpan → Dunhuang →
Mogao → Jiayuguan → Zhangye → Lanzhou, and **The Middle Kingdom Line** is the
first-timer's rail route, Beijing round to Shanghai.

**The observatories** (`observatory.json`, 32 places, 2026-08). Built to the rules
below rather than discovering them, which is the point of writing them down. Two
things it did add:

- **One deliberate coordinate override, documented in the file.** Paris Observatory
  is the only entry that ignores its own P625: both Wikidata and Wikipedia point the
  article at the institution's **Meudon** campus, 9 km southwest of the Perrault
  building on Avenue de l'Observatoire that the entry is actually about. The `_note`
  in `observatory.json` says so, so nobody "corrects" it back.
- **The China monument lesson, applied before it could bite.** The first draft's
  highlights included Frank Drake, Apollo 11, the Arecibo message and the Event
  Horizon Telescope. `enrich_monuments.py` spends every `highlight` as a *search
  term*, so those become monument tabs for a person, a mission, a transmission and a
  telescope network. Thirteen were cut and the content moved into the prose:
  **highlights here are structures, mountains and towns only.**
- `type` is `mountain` / `desert` / `history`, never `nature` — which keeps the
  `city_tour_of_the_wild` guard live for remote sites while stopping a wildlife cam
  from filling an observatory's 🔴 seat.

| rule | why |
| --- | --- |
| coordinates from **Wikidata P625**, not an OSM administrative centroid | a Chinese prefecture-level city is a *region*. OSM's "Chongqing" node sits at 30.06N 107.87E, ~200 km out in the rural east; P625 puts it in Yuzhong, which is the city. Nominatim is for villages and scenic areas that Wikidata has no point for, and the matched object gets eyeballed |
| every `wikipedia_slug` **checked live**, and stored as the article's *canonical* title | `arrivalPhoto()` queries pageimages without `redirects=1`, so a slug that is a redirect returns no thumbnail and the card silently degrades to its emoji. A redirect is not a broken link on Wikipedia but it is one here |
| no article → point at the **containing** settlement or watercourse | GRCA owns properties Wikipedia has never heard of. Same precedent as `big-bear-eagles → Big_Bear_Lake,_California`. Never a namesake elsewhere: Wikipedia's "Pinehurst Lake" is in **Alberta**, so Ontario's kettle lake points at `County_of_Brant` |
| `highlights` slugs get the same check | 15 of them pointed at articles that don't exist and 2 at the wrong subject ("Outlying Islands" redirects to a generic geography concept, not Hong Kong's district). 12 repointed, 5 dropped to plain text — the UI renders highlights as text chips anyway, so a name with no link costs nothing and a dead link is rot |
| `sounds` must name one of the **six recipes** `soundscape.js` knows | `typeFor()` matches on keyword — arctic / wind / ocean-wave-tidal / waterfall / plaza-city / wilderness-forest. Any other filename silently falls through to wind, and nobody notices |
| **city tiers live in the prose, hedged — never in a field** | there is no government tier list. The ranking is a Chinese business magazine's, revised yearly, and "new first-tier" is that magazine's coinage. A `tier: 1` key would read as official |
| `region` is **user-visible** | `passport.js` prints it under the place name, so a municipality needs "Beijing Municipality" or the card reads "Beijing / Beijing" |

---

## Quick start

```bash
cd oneworldtour
python3 -m http.server 8099 --bind 127.0.0.1
# open http://127.0.0.1:8099
```

No install, no keys. (Serve it — don't open `file://` — it fetches local JSON.)

Everything except **Ask-the-Guide** works from that plain static server. That one
feature calls `/api/ask`, a serverless function, so it needs the Vercel CLI:

```bash
npm i -g vercel                      # once
echo "ANTHROPIC_API_KEY=sk-..." > .env.local
vercel dev                           # serves the site + the function together
```

`.env.local` is gitignored. The key is read only inside `api/ask.py` and never
reaches the browser. Without it the Ask box says so honestly instead of failing
silently.

### Deploying

`Sapi3ntia/oneworldtour` is connected to the Vercel project, so **a push to
`main` deploys to production on its own** and any other branch gets a preview
URL. The CLI is still there for a deploy that skips git:

```bash
vercel login
vercel env add ANTHROPIC_API_KEY production
vercel --prod                        # optional — pushing already deploys
```

Connecting it needs the **Vercel GitHub App** installed on the GitHub account,
and installed *with this repo in scope* — a fresh install defaults to whichever
repositories you tick, so a project whose repo wasn't ticked never appears in
Vercel's picker and `vercel git connect` fails with a misleading "make sure
there aren't any typos". The fix is **Settings → Git → "Adjust GitHub App
Permissions"**, which lands on GitHub's own install settings.

`api/ask.py` is deliberately hostile to anyone who isn't the site — same-origin
only, per-IP and per-instance rate limits, hard input caps, and `max_tokens`
pinned at 220 — because every call bills a real Anthropic account. Tune the
limits at the top of that file; set `GUIDE_MODEL` to override the model.

**`"framework": null` in `vercel.json` is load-bearing.** Left to itself, Vercel
sees a Python dependency and builds the whole repo as a Python *application* —
one entrypoint answering every route — and the atlas disappears behind
`/api/ask`, which returns `{"status": "ok"}` at `/`. Null keeps it a static site
whose `api/*.py` files are individual functions. Two related traps: the
zero-config static builder looks in `public/`, so the site has to sit at the
repo root with no output directory override; and the per-file Python builder
rejects `maxDuration`/`memory`, so don't add a `functions` block. `pyproject.toml`,
`uv.lock` and `.python-version` are generated at build time from
`requirements.txt` and are gitignored on purpose.

There is deliberately no `cleanUrls` or `trailingSlash`: the pages fetch their
data with relative paths, so `/location/` would look for
`/location/data/index.json` and 404.

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
