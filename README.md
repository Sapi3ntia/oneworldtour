# 🌍 One World Tour

Step into 1,126 places across 170 countries — **walk their streets, drive their
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
- **Trips** (`trips.html`, `trips.html?id=…`) — 21 curated routes people actually
  travel (the Euro Trip, Route 66, the Trans-Siberian, Cape to Cairo…),
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
│   ├── <region>.json      # 1,126 places (curated walks/webcams/monuments live here)
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
│   ├── harvest_cams.py    # the same cams, found the cheap way round      ★
│   ├── openwebcamdb.py    # metered cam DISCOVERY — build-time only       ★
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
  captions frame by frame), each taking the first clear slot from `LABEL_SLOTS`;
- a name with nowhere clean to sit isn't drawn. Its dot, tooltip and click target
  stay, and hovering gives the name back.

**Sixteen slots, not two (2026-08).** The original pass offered a caption the
right of its dot and then the left — that flip is what keeps Osaka *and* Nara
named, 14 px apart, so it earned its place. But a single row is also exactly why
Mount Wilson Observatory stayed nameless until you were most of the way to
`K_MAX`. It sits in a chain of eight places strung along one line of latitude —
Santa Monica · Los Angeles · Griffith · Mount Wilson · Big Bear · Joshua Tree ·
Palomar · San Diego — where every caption is 15–20 map units wide inside a
125-unit viewport. On one row the first name printed eats every position the rest
of the chain could have used, and the ones that lose are the ones with the longest
names, which are the observatories. `LABEL_SLOTS` now offers sixteen positions
around the dot — beside it, stacked over or under it, out on a diagonal, up to
three caption-heights away — right before left and above before below all the way
down, so the map stays predictable as you pan. Stacking rows is what a chain like
that needs, and it's also just how an atlas draws them. Over a sweep of 140 random
viewports: **64 % of in-view places named → 80 %**, and Mount Wilson is named
continuously from k ≈ 7 instead of appearing at k ≈ 30.

Boxes are estimated from the character count, never measured — `getBBox()` on a
few hundred `<text>` nodes would force a layout flush on every tween frame, the
exact thrash this engine exists to avoid. Eight times the slots would have been
eight times the collision tests, so claimed boxes are indexed by horizontal
**band** rather than scanned end to end: a caption is one line tall and a viewport
is ~50 lines, so a candidate only ever compares against the two or three bands it
crosses. The worst frame in that same sweep went from **39 k tests to 11 k** — the
richer placement is cheaper than the old one was. Measured cost of the whole pass
in the worst view we ship (117 places on screen over Europe): **~0.8 ms**.

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

Driving the real module under a DOM shim over the atlas as it stood that day —
540 places, 27 groups, 71 dots fanned, largest group 9 — the measured result
across k = 3…90 is: **worst
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

**The trap that cost the most: `--max` used to silently truncate `--only`.**
Both enrichers ended with `todo = todo[:args.max]` while `--max` defaulted to
10, so naming 94 places processed the first ten and dropped 84 without a word
in the log. Months of "filling a region out" were quietly losing most of each
batch; that is where the bulk of the no-scene backlog came from. Both tools now
default `--max` to `None` and treat *naming the places as the limit* — `--max`
caps an open-ended sweep only. They also warn about ids that are on no map,
instead of letting a typo vanish. If you add a third tool that walks the corpus,
do not reintroduce the pattern.

Two more operational traps. `enrich_media.py`,
`harvest_cams.py --apply` and `enrich_monuments.py` each rewrite
`data/media.json` **whole**, so never run them concurrently — the second to
finish wins and silently discards the other's work.
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

**Auditing a batch (2026-08).** The Southeast Asia and Texas / Blues Highway
places arrived carrying `highlights` and no tabs, so one sweep over 119 of them
added 278 — the atlas now holds 964. Three checks ran before they landed, none of
which the offline pruner can answer: is one video standing in for two landmarks
(0), does a stored `title` name some *other* place we cover (0), and — the useful
one — how far is the landmark from the place it hangs on? Every slug resolves to
a Wikidata **P625** point, so that distance is measurable rather than argued
about.

Thirteen tabs sat more than 75 km out, and twelve were right anyway: the P625 of
a river or a range is one arbitrary point along it (the Natchez Trace Parkway is
715 km long), Misool and Salawati are islands *inside* Raja Ampat, and Pie Town
really does host a VLBA antenna. The thirteenth was **8,204 km** out.
`Paradise_Cave` is Jaskinia Raj, in Poland; the Vietnamese one is
`Thiên_Đường_Cave`. The video was right — *"Visiting Paradise Cave, Phong Nha,
Vietnam"* — and only the chip's link was wrong, which is precisely the failure a
title rule cannot see and a distance check cannot miss. It is the River Kwai
lesson (below) in a second form, and it will keep recurring: a landmark name is
not a unique key, and only coordinates ever say so.

The same pass re-checked every new slug for a missing article *and* for a
redirect, because a redirect slug returns no `pageimages` thumbnail and the
arrival card degrades to its emoji without complaining (see `arrivalPhoto()`
below). All 278 were clean; two older Route 66 chips were not.
`Gathering_Place_(park)` is a dead title — the article is
`Gathering_Place_(Tulsa_park)` — and Stockyards City has no article under any
spelling, so it joins the 195 highlights that carry a real name and no link.

**Sweeping the remainder, and what the sweep got wrong (2026-08-12).** With
South America filled in, every place that had `highlights` and no tabs got swept
— coverage went **419/643 → 690/706 places (65% → 97%)** and **964 → 1,651
tabs**. Two streams ran at once, taking opposite ends of the queue, because
`enrich_monuments.py` writes only the region file of the place it is on: two
streams are safe exactly as long as they are never in the same file. That halves
the wall clock and doubles the request rate, and a throttled search returns an
empty result set byte-for-byte identical to *"there is no such video"* — so a
sequential re-run pass over everything still empty is not optional, it is the
only thing that tells a rate limit apart from an honest absence. Of 16 empty
places re-asked on a quiet line, one filled (`giethoorn`); the rest were real.

**45 tabs were then cut, and the audit that found them is the point.** A search
that finds *something* is not a search that finds the *right* thing.
`mentions_landmark()` passes on a token subset, so "Jaco Beach, Costa Rica"
served the Amazonian geoglyph site *Jacó Sá*, and "Mill Creek Marsh Trail in
Secaucus NJ" served a conservation area in Ontario. Three checks, all offline,
all reading the stored `title`:

1. **one video, two places** — the same id on two different records
2. **the title names another place we carry** — the original check, and the
   weakest: it can only see a wrong place that is *in the atlas*, which is why
   Secaucus, Jacó and Al Wathba all sailed through it
3. **the title covers only *part* of a multi-word landmark name** — full
   coverage is strong evidence of the right subject; partial coverage on one
   common word is how the impostors get in. Fold diacritics first, or
   "Chichen Itza Tour 4k" reads as a mismatch for Chichén Itzá
4. **anchored to nothing** — the strongest. A video really shot here almost
   always says so: it names the place, its region, or its country, *or* it names
   the landmark in full. A tab that does neither is a guess

Check 3 found two more bad tabs in `latinamerica.json` *after* checks 1–2 had
declared that file clean. `canada.json` was structurally the worst (18 of 91),
because a tiny Ontario conservation area's highlights are townships, creeks,
habitat types and species — names with famous namesakes abroad. The failures
sort into wrong continent (Bloomingdale's for a Buenos Aires arcade, a Kansas
prairie, a Moon Boots DJ set), wrong region of the right country (Charlotte NC
for Santa Fe, Chongqing for Langzhong), right city and wrong building (Dakar's
Mosquée de la Divinité for its Grand Mosque), a compilation that opens somewhere
else, and — twice — not a place at all: a species, and a charity.

**Deleting a tab was not enough.** The re-run pass put seven of eight straight
back, because removing a tab also removes its id from the in-run `exclude` set:
the search reran, found the same top hit, and told the same lie. `enrich_media.py`
has read `data/media_denylist.json` since the walk seats were audited;
`enrich_monuments.py` had no such memory and now shares the same
`load_denylist()`/`denied()` reader rather than reimplementing it. 28 entries
were added (18 global, 10 scoped to the one place they lied about). Verified the
only way that counts — re-running `--only santa-fe` now reports *"nothing
verifiable — honest gap"* instead of re-adding the Charlotte video.

Two gaps stay open on purpose. 15 places with highlights end the sweep with no
tab, which is the honest outcome for a hamlet with nothing to shoot. And 49
places — Tokyo, Petra, Giza, Chichén Itzá, Sydney, Moscow — have empty
`highlights` while already carrying hand-picked monuments: a cosmetic gap in the
About chips, not a hole in the tabs.

### Trips ★

```bash
python3 tools/check_trips.py --scenes    # exits 1 if any stop is unknown
```

`data/trips.json` holds 19 hand-ordered routes. A trip stores only **place ids**
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

Six batches went in this way, and the rules they turned up apply to any new place.

**Russia, Ukraine and the wider Eurasian belt** (`europe.json` + `asia.json`,
94 new places, 2026-08-13). Built with `tools/build_eurasia.py`, which grew an
`--only` flag so adding one more place doesn't mean regenerating — and
overwriting — the whole region. **Taganrog** went in that way: Peter the
Great's first naval base, 1698, on a cape in the Sea of Azov, two decades older
than Saint Petersburg, tagged `hidden` because it honestly is. Its six
highlights are all real structures rather than districts, so
`enrich_monuments.py` can actually spend them.

This batch is also where the `--max` truncation bug surfaced, and the reason it
went unnoticed for so long is worth recording: the failure looked exactly like
success. The log said what it was doing for ten places, then said `done`. A
silent truncation reads as a completed run, so the only thing that catches it
is counting the output against the input — which is now what the ghost warning
is for.

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

**The observatories** (`observatory.json`, 35 places, 2026-08). Built to the rules
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
- **All six NRAO facilities** are now in (32 → 35, 2026-08-11): the VLA, Green Bank
  and ALMA were already here; **ngVLA**, the **VLBA** and the **Central Development
  Lab** went in beside them. Two of the three needed a coordinate that isn't their
  P625 and the file's `_note` says why — Wikidata gives the VLBA the *VLA's* point on
  the Plains of San Agustin, where the VLBA has no antenna at all, so it is pinned at
  the Socorro operations centre where the ten stations' recordings are correlated. The
  ngVLA legitimately shares the VLA's point (its one prototype dish stands on that
  site); the map's fanning is what keeps them apart, and fixing that fan is why
  `_placeLabels` was rewritten.

**Southeast Asia** (`asia.json` 190 → 273, 2026-08-11). Same shape as China: the 24
places we had were skeletons, and 83 more went in beside them — 24 → **107**. Four
countries went from nothing at all: **Indonesia 20** (Yogyakarta and Borobudur through
Bromo and Ijen out to Raja Ampat, Wae Rebo and the Bandas), **Myanmar 8**, **Brunei 2**
and **Timor-Leste 2**, all of which had to be added to `tools/build_countries.py` first
— an unregistered country is counted but never listed, and the generator only says so
in a `⚠` line you have to be reading for. Thailand 4 → 15, Vietnam 4 → 14, Malaysia
4 → 13, the Philippines 4 → 13, Cambodia 3 → 8, Laos 2 → 8, Singapore 3 → 4. **The
Banana Pancake Trail** already existed and every stop still resolves; what changed is
that the trail now has a country either side of each stop. Two traps this batch added
to the list:

- **A highlight that redirects to the record's own subject is worse than a dead link.**
  Gardens by the Bay's "Flower Dome" and "Supertree Grove" both redirect to *Gardens by
  the Bay*, and Phú Quốc's "Dương Đông" redirects to *Phú Quốc* — a chip that reopens
  the page you are already on. The resolver reports the redirect target, so compare it
  against the record's own slug, not just against nothing.
- **The namesake trap has a literary form.** "Bridge over the River Kwai" resolves to
  Pierre Boulle's *novel*, which has no coordinates and no monument; the bridge's own
  article isn't under any name close to it. Dropped for Kanchanaburi War Cemetery
  rather than guessed at.
- **Chasing that `⚠` line down to nothing found five older countries missing too.**
  Registering Myanmar, Brunei and Timor-Leste is what made the warning readable, and it
  was still naming **DR Congo, Namibia, Zimbabwe, North Korea and Uzbekistan** — all
  five carrying places since the wildlife and Silk Road batches, all five counted in
  the totals and none of them listed anywhere you could browse to. They are registered
  now, so the registry holds all **97** countries the atlas actually covers and the
  warning prints nothing. A generator that only whispers when it's wrong needs someone
  to go looking; the useful state is the one where its whisper is silence.

**Texas and the Blues Highway** (`usa.json` 57 → 74, 2026-08-11). Texas had three
places for the second-largest state in the country, one of which was a Route 66 fuel
stop. It has twelve more now: **Houston**, **Dallas** and **Fort Worth**, **El Paso**
where the range runs into the middle of the city, **Big Bend** and **Marfa** out in
the Chihuahuan Desert, **Galveston**, **Fredericksburg** in the Hill Country,
**Palo Duro Canyon**, **Guadalupe Mountains**, **South Padre Island**, and **Caddo
Lake**, which is a cypress swamp and looks nothing like the rest of it. Austin was a
skeleton and is filled.

The new route is **The Blues Highway** 🎷 (`trips.json`, 19 routes now) — Nashville ·
Memphis · Clarksdale · Vicksburg · Natchez · Baton Rouge · New Orleans, 985 km as the
crow flies. It is the drive Route 66 isn't: US-61 down the Mississippi, run southward
along the road the music came *up* during the Great Migration. Five of its stops did
not exist yet, so **Memphis** went in, **Nashville** got filled, and **Mississippi**
became a state the atlas covers at all — Clarksdale, Vicksburg and Natchez. What this
batch added to the list:

- **A redirect can cross a border.** "El Paso del Norte" is a perfectly reasonable
  highlight for El Paso and it redirects to **Ciudad Juárez** — the right history,
  the wrong country, and a chip that sends you to Mexico. The namesake check has to
  compare the *resolved* article against what the record is actually about, not just
  confirm that something resolved.
- **And it can cross a border while keeping the name.** "Santa Elena Canyon" resolves
  to the *Cañón de Santa Elena Flora and Fauna Protection Area*, which is the Mexican
  reserve on the far bank, not the canyon you walk into from Big Bend. Demoted to a
  plain text chip — right name, no link, no lie.
- **Two more had no article at all** (Galveston's Pleasure Pier, Palo Duro's
  Lighthouse). The Lighthouse is the canyon's signature rock and still earns its chip
  as plain text; the pier was dropped.

**South America** (`latinamerica.json` 30 → 93, 2026-08-12). Four countries had a
flag on the map and nothing behind it — **Ecuador**, **Venezuela**, **Guyana** and
**Suriname** were all zero — and Chile was zero walkable places despite being 4,300 km
long. Sixty-three places went in and the twenty-nine skeletons already there were
filled: Ecuador 0 → **9** (Quito, Cuenca, Baños, Cotopaxi, Quilotoa, the Galápagos),
Chile 0 → **10**, Venezuela 0 → **5** (Angel Falls, Roraima, Mérida, Los Roques),
Guyana 0 → **2**, Suriname 0 → **2**, Brazil 1 → **12**, Peru 2 → **8**, Argentina
5 → **11**, Colombia 3 → **8**, Bolivia 3 → **7**, Uruguay 3 → **4**, Paraguay
1 → **3**. The four new countries went into `tools/build_countries.py` first — the
registry holds **101** now — and `tools/build_latinamerica.py` is the generator, with
`SA_BOX` as its own namesake trap: every new place is in South America, so a P625 that
lands outside a box around the continent means the slug resolved to somewhere else and
the record is refused rather than written.

- **A highlight can resolve to a *people*.** Puno's "Uros" redirects to `Uru_people`,
  which is an ethnic group — a monument search term that can only return something
  wrong. `NOT_A_MONUMENT` is about structures, towns and landforms, and the check has
  to survive a redirect: the slug looked like an island chain and the article was not.
  Unlinked to the text chip "Uros floating islands".
- **A namesake can be on another continent.** Medellín's `Comuna_13` resolved 4,879 km
  away; the article that means the district is `Comuna_13,_Medellín`. The distance
  check is what caught it, which is why every new record gets one.
- **An article can exist and still have no coordinate.** Elqui Valley has a good
  Wikipedia article and its Wikidata item carries no P625 at all, so there was nothing
  to pin. The record was re-anchored on **Pisco Elqui**, the village in it, with the
  valley kept as the first highlight — a place we can point at, described by the thing
  we cannot.

**Highlights for the last 68 skeletons** (`tools/fill_highlights.py`, 2026-08-12).
Uluru, Dubai, Cape Town, Vatican City, Lake Baikal, Kyiv and 62 others had an empty
`highlights` array *and* no monuments, and those two facts were the same fact:
`enrich_monuments.py` spends highlights as its search terms, so a place with none can
never earn a monument tab however famous it is. The pass is merge-only — it writes
`highlights`, `blurb`, `fun_fact`, `hidden_gem_tip` and `region`, and only where the
field is empty, so a rerun is a no-op and a hand edit is never overwritten. Every
place in the atlas now has at least one of the two.

- **Four highlights resolved to their own record.** Bled Island redirects to *Lake
  Bled*, Merzouga to the Sahara entry that is named for it, Taroko National Park to
  the gorge, and Gergeti Trinity Church to the mountain record that *is* the church.
  Compare against the record's own slug, always.
- **Three namesakes, one of them a whole country off.** Jeddah's "Al-Rahma Mosque"
  resolves to the **Liverpool** mosque of that name, 4,700 km away; Rotorua's "Te
  Puia" to *Te Puia Springs*, a town 180 km up the coast in Gisborne; and Baku's
  "Icherisheher" to the article about the reserve's *administration* rather than the
  walled city. Repointed to `Al-Rahmah_Mosque`, `New_Zealand_Māori_Arts_and_Crafts
  _Institute` and `Old_City_(Baku)`.
- **A bare name can be a disambiguation page.** Luxembourg's `Grund` and Wellington's
  `Mount_Victoria` both land on "may refer to" lists. The Wellington hill has a real
  article under `Mount_Victoria_(Wellington_hill)`; Grund does not, so it is a text
  chip.
- **A FAR verdict is a question, not a fault.** Ten survived, and every one is a
  containing region or a long feature reporting its centroid — Acre state, the Amazon
  rainforest, the Rif, the Daintree, three islands on a reef that is 2,300 km end to
  end. What was *not* kept is `Great_Barrier_Reef_Marine_Park` as a highlight of the
  Great Barrier Reef: the same subject under a second name is a chip that goes nowhere
  new.

**Hovden, and the 📡 shelf** (`europe.json` 188 → 189, 2026-08-13). One village and
one new kind of category. **Hovden** is a fishing village in Bø Municipality,
Vesterålen — the northern tip of a peninsula on Langøya, ocean on two sides, a road
that stops when the land does, lived on since at least 400–800 CE because the fishing
banks start just offshore.

Getting it in cost two rejected videos and one new field, and the reason is a trap
none of the existing guards could see. **Norway has two Hovdens.** The other is a ski
resort in Setesdal, Agder, 1,000 km south and vastly more famous, and `"Hovden Norway"`
returns it almost exclusively. Both picks the sweep made were that one: a trucker's
POV whose description gives it away as *"the 9th road in Norway"* — Route 9 up
Setesdal — and a winter drive that needed a frame pulled to settle it, showing an
inland alpine valley of birch scrub, spruce and dark-timber *hytter* with no sea in
any direction. `wrong_place_title` could not have caught either: it works by finding
a **different** place named in the title, and both videos honestly say "Hovden" and
honestly say "Norway". The only witness against them is a coordinate the text never
mentions.

So the fix had to land *before* the search rather than after — `search_name`, which
sharpens the query to `"Hovden Vesterålen"` while `name` stays short enough for a map
pin. Both rejections are recorded in `media_denylist.json` under `per_place`, because
the videos aren't bad, they're just not here. Two things worth keeping from this:

- **A namesake inside the same country is invisible to every title guard we have.**
  The guards are built to notice a competing name; they cannot notice a competing
  *place with the same name*. When a place shares its name with something more famous
  in the same country, assume the sweep will find the famous one and say so up front.
- **"Nothing verifiable" is only honest if the search actually ran.** The first
  post-fix sweep returned an honest gap *and* the line `YouTube search is refusing us
  (8+ empty responses in a row)`. Those two facts together do not mean the footage
  doesn't exist — they mean nobody looked. The throttle notice is printed for exactly
  this reason; read it before recording a gap.
- **And when it has run, `wrong_place_title` can still be right in general and wrong
  here.** With the query fixed, the search returns a 49-minute 4K drive whose burned-in
  caption reads `EIDET - NYKVÅG - HOVDEN` — the correct village, beyond doubt. The
  sweep refuses it anyway, because the channel titles it *"4K **Lapland** Scenic
  Drive"*, `lapland` is a real place in this atlas 397 km away, and the title names it
  **before** it names Hovden. That is precisely the pattern the guard is built to
  catch, and loosening it to admit this one video would cost the protection on the
  other 800 places. The override is **curation**, which is what it has always been
  for: the pick sits in `europe.json` as a `drive` field with a `_note` recording why
  the sweep can't have it. Debugging that took one wrong turn worth remembering —
  calling `find_drive()` from a scratch script *succeeded*, because a bare import
  never runs `register_place()` and `wrong_place_title` had an empty corpus to compare
  against. **Reproduce a sweep rejection with the places registered, or you are
  testing a different function than the one that ran.**

The **📡 category** is the other half. It is deliberately not a theme, and there is no
rule to derive it from — membership is the author's, by hand, and it holds exactly
**Taganrog** and **Hovden** for now. That is also why it isn't a region file like
`ancient` / `wild` / `observatory` are: those are exclusive by construction, since
`data.js` reads `region_id` from whichever file a place lives in, so a fourth one
would have *moved* Taganrog out of Europe. `sets` is the additive form instead — both
places keep their home region and join the shelf as well. The chip carries no label,
on purpose.

**Africa** (`africa.json` 23 → 182, 2026-08-17). The largest gap the atlas had: a
continent of 54 countries represented by 23 places in **7** of them, eight of which
were name-and-coordinate skeletons. Every country is now on the map — **54 of 54**,
none of them empty — built with `tools/build_africa.py`. Egypt 4 → 12, Morocco
5 → 13, South Africa 5 → 14, Tanzania 0 → 8, Namibia 0 → 6, Ethiopia 3 → 8, Kenya
3 → 8, and forty-four countries that had nothing at all now have between one and
eight, from Malabo and Bissau's Bijagós to the Ennedi Plateau and Lac Assal.

The registry had to be fixed before any of it counted: `tools/build_countries.py`
knew about **10** African countries and the atlas now covers 54, so 44 went in
(106 → **150** countries registered). Five of them — Guinea, Guinea-Bissau,
Equatorial Guinea, Liberia and the Central African Republic — had never been
registered *or* populated, so each got authored places of its own rather than a
registry row pointing at nothing.

- **The country name is a join key, and nothing says so.** `live_counts()` matches
  `loc["country"]` against the registry's **canonical name string**. The first draft
  of the generator's `COUNTRY_CODE` said `"Ivory Coast"` and `"Democratic Republic of
  the Congo"` — both perfectly correct English, both a spelling the registry doesn't
  use, and the result would have been Côte d'Ivoire and DR Congo showing **zero
  places** while quietly holding four apiece. Nothing errors; the count is just wrong.
  Every name in the generator is now copied from the registry verbatim, with the
  reason written next to it.
- **A bounding box cannot catch an African namesake.** Every other regional generator
  refuses a record whose P625 lands outside the continent, and here that guard is not
  enough: any box wide enough to hold Bizerte at 37.28°N also holds **Lagos,
  *Portugal*** at 37.10°N. So the box stays as the hard refusal and a second check
  went in beside it — **Wikidata P17 against the country the record claims**, reported
  as a warning. A warning rather than a refusal because P17 legitimately disagrees:
  `Tripoli,_Libya` carries Q3433694, **Tripolitania**, not Libya. Five warnings
  survived this batch and all five are real — Laas Geel is in Somaliland, Lake
  Malawi's P17 is Tanzania, the Drakensberg's is Lesotho, Koutammakou's is Benin.
- **Four highlights resolved somewhere else entirely, and the same box would have
  passed all four.** Abidjan's `Le_Plateau` → **Le Plateau-Mont-Royal, Montreal**.
  Windhoek's `Independence_Memorial_Museum` → the one in **Colombo**, 7,571 km away.
  Skeleton Coast's `Terrace_Bay` → a township in **Ontario**. Soweto's
  `Vilakazi_Street` → **Benedict Wallet Vilakazi**, the poet the street is named for,
  which is a person and therefore a monument search term that can only return
  something wrong. Fourteen more had a real article under a different title —
  `Sibebe_Rock`→`Sibebe`, `Ducor_Palace_Hotel`→`Ducor_Hotel`,
  `Old_Fort,_Zanzibar`→`Old_Fort_of_Zanzibar`, `Red_Castle,_Tripoli`→`Red_Castle
  _Museum` — and thirteen have no article at all and ship as plain text chips.
- **The "highlights are structures, not peoples" rule is unusually easy to break
  here.** *Dogon*, *Ashanti*, *Maasai*, *Berber*, *Zulu*, *Himba*, *Nubian* all read
  like places on the page and are all peoples. The authored highlights name the
  Bandiagara Escarpment, Manhyia Palace and the Nubian pyramids instead — things a
  camera can point at.
- **`search_name` earned its second outing seven times over.** Tripoli (Lebanon),
  Lagos (Portugal), Saint-Louis (Missouri), Victoria (British Columbia, Hong Kong,
  Australia), Moroni (Italy), Djibouti the city inside Djibouti the country, and
  Livingstone (the man). Each one is a collision no title guard can see, so the fix
  lands on the query rather than on the result.

Two routes went in with it (`trips.json`, **21** now). **Cape to Cairo** 🚂 is the
north–south spine — Cape Town · Johannesburg · Matobo · Victoria Falls · South
Luangwa · Lake Malawi · Ngorongoro · Nairobi · Lalibela · Khartoum · Meroë · Aswan
· Cairo, 8,691 km as the crow flies and thirteen stops that did not all exist
before this batch. It is named for a railway that was never finished and for a
politics that is gone; the blurb says so rather than pretending the name is
neutral. **The Swahili Coast** ⛵ is the other axis — Lamu · Mombasa · Stone Town ·
Dar es Salaam · Moroni · Ilha de Moçambique, read north to south because that is
the direction the northeast monsoon carried the dhows.

**The three loose ends from the Hovden batch, closed.** All of them were about a
run that lies by omission rather than by error:

- **`tools/medialock.py`** — `media.json` had three concurrent writers
  (`enrich_media`, `harvest_cams`, `prune_media`) and no lock, each of which read the
  whole file at startup and wrote the whole file back at every checkpoint. Two
  overlapping runs meant the second one silently reverted the first. The module gives
  them `flock` on a `data/.media.lock` **sidecar** (a sidecar because `os.replace()`
  swaps inodes, so a lock on the file itself is a lock on a file nobody has any more),
  a re-read *inside* the lock, and an atomic `mkstemp`+`fsync`+`os.replace` write. The
  rule it documents: a mutate function must never assign back a subtree it captured
  earlier — `doc["places"][pid] = entry`, never `doc["places"] = my_places`.
- **`--max` now reports its backlog.** Both enrichers defaulted to 10 places per run
  and printed nothing about the rest, so a truncated sweep and a complete one produced
  identical-looking logs — which is how batch after batch ran at 10 against a corpus
  of 900 and every one read as finished. They now count candidates *before* capping,
  warn in the header, and end with `done — this run only` versus `done — every
  candidate place was looked at`. Turning that on immediately surfaced what the
  Hovden notes predicted: **786** places want a monument search and **893** want a
  media seat, corpus-wide. That backlog was always there; it just had nothing that
  printed it.
- **"Nothing verifiable — honest gap" no longer prints when nobody looked.** The
  streak abort only fired at eight consecutive empty responses, so the first seven
  throttled places recorded a permanent-looking verdict on a search that never ran.
  Each place now measures the empty responses that occurred *during it* and prints
  `NOT LOOKED AT` instead. A gap is a finding; a throttle is not. **And the first
  version of that fix over-corrected, which the Africa sweep caught:** counting
  empties alone flagged Loango and Ranomafana as throttled on every re-run, forever.
  They weren't. `find_monument`'s second query drops the city — `Iguéla Lagoon 4K
  walking tour` — and for an obscure landmark YouTube genuinely answers zero. The
  premise "empty means throttled" only holds for a *broad* query. The evidence that
  separates the two is whether YouTube served **any** search during that place: if it
  answered even once it was not refusing us, so an empty is a real zero. Both
  enrichers now share `em.verdict(found, blind, served)` and print the reason
  (`3 narrow search(es) came back genuinely empty; YouTube was answering us`). An
  instrument that cries throttle at a real gap is the same bug wearing the other mask
  — it just wastes re-runs instead of hiding them.

**A fourth one this batch went looking for, and found.** Registering 44 countries is
not the same as *supporting* them. `js/lib/culture.js` keys its four tables on the
country **name**, and none of the 44 had rows — so every new African place rendered
"Language —, Currency —, Local specialities", no phrases, no fast facts and no
currency converter, while still looking like a finished page (the radio list kept
working, because that reads `country_code` off the place record and never touches
these tables — which is exactly why the hole was easy to miss). Auditing the registry
against all four tables turned up **59 more** already-shipped places in the same state
from the Eurasia and Latin America batches — Ecuador, Myanmar, Uzbekistan, Belarus and
nine others. `tools/build_culture.py` now covers all **150** registry countries, and:

- its output path was still `js/culture.js`, a file that has since moved — the script
  had been un-runnable for some time, which is why it drifted;
- it emits into single-quoted JS strings and **escaped nothing**, so `Côte d'Ivoire`
  and `N'Djamena` would have written a syntactically broken `culture.js`;
- it replaces its marked block wholesale, and four countries hand-added to that block
  (DR Congo, Namibia, North Korea, Zimbabwe) were never mirrored back into `ROWS` — so
  the next run would have silently deleted them. They are back in `ROWS`, and
  `check_no_orphans()` now **aborts the run** rather than dropping a key it doesn't
  recognise. Verified purely additive: 95 → 152 keys per table, nothing lost, no
  pre-existing value changed.

The general lesson, worth applying to the next region: *finish the country, not just
the place*. Adding rows to `data/countries.json` silently promises culture rows,
currency codes and radio codes that nothing checks for you.

**Oceania** (`oceania.json` 11 → 168, 2026-08-17). Eleven places for a third of the
planet's surface: six in Australia, five in New Zealand, and **nothing at all** in the
Pacific — the ocean that holds fourteen sovereign states was represented by zero
records. It now holds **168 places in 23 countries and territories**, built with
`tools/build_oceania.py` on the frame `build_africa.py` set: Wikidata **P625** for
every coordinate, every `wikipedia_slug` resolved live and stored as the article's
canonical title, prose from memory and nothing else. Australia 6 → **73**, New Zealand
5 → **36**, and **59** across the Pacific — Papua New Guinea's Sepik and Highlands,
Vanuatu's land divers, Chuuk's sunken fleet, Bikini Atoll, and Adamstown, population
35. The registry went 150 → **170** countries, all 23 Oceania rows non-zero.

- **A single bounding box cannot express this region.** Every other generator refuses a
  record whose P625 lands outside a `lat_min…lat_max, lng_min…lng_max` net. Oceania runs
  from Christmas Island at **96.8°E** to Pitcairn at **130.1°W**, so that test either
  spans the whole globe (`-180…180`, which refuses nothing) or splits the Pacific down
  the middle and throws away everything past the date line. `in_box()` therefore ORs
  **two** longitude ranges, `(96.5…180)` and `(-180…-124)`, and the same crossing shows
  up again in the map (below) and in the trips.
- **Wikidata P17 answers the sovereign state, not the territory.** The Africa batch
  added P17 as the soft warning beside the box, and in the Pacific that warning fires
  on every place that is *correct*: Bora Bora's P17 is **France**, Nouméa's is France,
  Hagåtña's and Saipan's are the **United States**, Adamstown's is the **United
  Kingdom**. Refusing on P17 here would delete French Polynesia, New Caledonia, Guam,
  the Marianas, American Samoa and Pitcairn — the entire Pacific outside the
  independent states. `EXPECT_P17` names the nine expected sovereign answers, and a
  match against the expected one prints as a quiet `TERRITORY` note instead of a
  warning. 18 fired; 0 real `COUNTRY` mismatches survived.
- **A redirect is a namesake trap the title never shows.** `MacKenzie_Falls`, the
  waterfall in the Grampians, is not an article — the slug redirects to
  **`Sonny_with_a_Chance`**, a Disney sitcom whose show-within-a-show is called
  Mackenzie Falls. The *title* looked perfect; only the redirect target gave it away.
  It is now a plain-text chip, as are twelve others with no article of their own, and
  28 more were repointed (`Ikara-Flinders_Ranges_NP` needed the en-dash;
  `Ulva_Island` is a disambiguation page; Neiafu's article is `Neiafu_(Vavaʻu)`).
- **`sounds` filenames are a closed set of six, and a wrong one fails silently.**
  Eight invented names (`tropical-birds.mp3`, `geyser.mp3`, `cave-drip.mp3`…) would have
  fallen straight through `soundscape.js`'s `typeFor()` to the generic wind bed, on 40
  places, with nothing in any log. Caught by reading `typeFor()` rather than by testing.
- **Territories get their own registry row, not their sovereign's.** The browse axis is
  Continent → Country → Place, so filing Bora Bora under "France" buries it inside
  Europe. New Caledonia, French Polynesia, Guam, the Northern Marianas, American Samoa,
  the Cooks, Niue, Norfolk Island and Pitcairn each carry their own ISO 3166-1 alpha-2
  code, and their flag derives from that code exactly as every other row's does.
  Christmas Island and Cocos stay `region` names under Australia, because that is how
  the atlas already treats them.
- **The four culture tables, kept as a promise this time.** The Africa batch's closing
  lesson was *finish the country, not just the place*, so the 20 new Pacific countries
  went into `build_culture.py`'s `ROWS` in the same sitting: 131 countries across
  `COUNTRY_PROFILES` / `COUNTRY_CODES` / `CURRENCY_CODES` / `COUNTRY_FACTS`, and a
  re-audit of the registry against all four now reports **zero gaps** for all 170
  countries. Every Pacific currency the converter needs — PGK, FJD, SBD, VUV, XPF, WST,
  TOP — was checked against `open.er-api.com` before being written down.

Two bugs the batch surfaced outside the generator, both of which had been waiting for
a region that crosses 180° or sits in Australasia:

- **The map drew routes the long way round.** `WorldMap.drawLine()` projected both
  endpoints and drew one straight line, with a comment saying a leg crossing the
  antimeridian "would need splitting at ±180 first". The Polynesian Triangle's
  Auckland → Nukuʻalofa leg is 1,998 km and **350° of raw longitude**, so it drew as a
  line straight across the entire map. It now splits at the edge, taking the crossing
  latitude off the same great circle `trips.js` measures the leg with, so the drawn
  route and the printed distance agree; the two halves of that leg sum to 1,998 km
  exactly, from either direction.
- **`fetch_windy.py` rebuilt `data/windy.json` from nothing on every run**, so any
  place whose lookup raised — one rate-limited afternoon, one network blip — silently
  lost its verified cam. It now starts from the file, drops an entry only after
  re-checking it and finding nothing, and takes `--only` so a region batch costs 157
  API calls instead of 1,126. That run added **74 windows and 16 live cams** to the new
  places (205 → 279 entries atlas-wide) — *on a file the app does not currently load*.
  Windy's embed player was cut in 2026-07 for failing the autoplay rule and
  `data/windy.json` has been dormant since; this fixes the generator and refreshes the
  data so the file is honest if the tier is ever revived, and it changes nothing a
  visitor sees today. Said plainly because a "74 new live cams" line would read like a
  shipped feature.
- **Airport cams don't say "airport".** The 2026-07-07 audit taught the picker to
  refuse sky, traffic, milepost and airport cams *by word*, and Australasian aviation
  cams name themselves by **ICAO code and bearing** — "Broken Hill - YBHI -> Facing
  East", "Ballarat - YBLT -> SW", "AYMH - Mt Hagen -> Facing North". Eleven of them
  came through as windows. Australia is Y+3, New Zealand NZ+2, PNG AY+2, and the
  pattern has to be **case-sensitive**: under `re.I`, `Y[A-Z]{3}` also matches "your",
  "yard" and "Yarra". Every four-letter capital token in an 887-cam Australasian sample
  was one of these codes.

**Trips.** 21 → **24 routes**. The Big Lap was six stops for a 14,500 km circuit —
Sydney, Cairns, the Reef, Uluru, Perth, Melbourne — which is a sketch, not a lap; it is
now **26 stops** clockwise around Highway 1 with the Red Centre spur. Three new routes
came with the region: **The Aotearoa Arc** (25 stops, Cape Reinga to Stewart Island,
one ferry in the middle), **The Melanesian Arc** (17 stops, Port Moresby to Taveuni
along the chain that carries a quarter of the world's languages), and **The Polynesian
Triangle** (17 stops, Auckland → Rapa Nui → Honolulu — the three corners of the
greatest feat of navigation in human history, and the route that found the
antimeridian bug).

| rule | why |
| --- | --- |
| coordinates from **Wikidata P625**, not an OSM administrative centroid | a Chinese prefecture-level city is a *region*. OSM's "Chongqing" node sits at 30.06N 107.87E, ~200 km out in the rural east; P625 puts it in Yuzhong, which is the city. Nominatim is for villages and scenic areas that Wikidata has no point for, and the matched object gets eyeballed |
| every `wikipedia_slug` **checked live**, and stored as the article's *canonical* title | `arrivalPhoto()` queries pageimages without `redirects=1`, so a slug that is a redirect returns no thumbnail and the card silently degrades to its emoji. A redirect is not a broken link on Wikipedia but it is one here |
| no article → point at the **containing** settlement or watercourse | GRCA owns properties Wikipedia has never heard of. Same precedent as `big-bear-eagles → Big_Bear_Lake,_California`. Never a namesake elsewhere: Wikipedia's "Pinehurst Lake" is in **Alberta**, so Ontario's kettle lake points at `County_of_Brant` |
| `highlights` slugs get the same check | 15 of them pointed at articles that don't exist and 2 at the wrong subject ("Outlying Islands" redirects to a generic geography concept, not Hong Kong's district). 12 repointed, 5 dropped to plain text — the UI renders highlights as text chips anyway, so a name with no link costs nothing and a dead link is rot |
| an empty `highlights` array is also an **empty monuments tab** — *unless the place is its own monument* | `enrich_monuments.py` has no other source of search terms, so the sweep skips the place silently and the gap reads as "nothing verifiable" when the truth is "nothing asked". 68 places sat in that state, Uluru and Vatican City among them. Author the highlights first; the videos follow. **But count the exception before you panic:** `SELF_MONUMENT_TYPES = {ruin, history, natural}` searches the place's *own* name, because Nan Madol and Göbekli Tepe have no sub-landmarks to list. Of the 47 places that still show an empty `highlights` array, 43 are those types and 42 already have monuments. The genuinely stuck list was four cities — Cairo, Tokyo, Seoul, Sydney — now authored by hand. A raw count of empty `highlights` overstates this gap by 10×; filter by `type` first |
| `sounds` must name one of the **six recipes** `soundscape.js` knows | `typeFor()` matches on keyword — arctic / wind / ocean-wave-tidal / waterfall / plaza-city / wilderness-forest. Any other filename silently falls through to wind, and nobody notices |
| **city tiers live in the prose, hedged — never in a field** | there is no government tier list. The ranking is a Chinese business magazine's, revised yearly, and "new first-tier" is that magazine's coinage. A `tier: 1` key would read as official |
| `region` is **user-visible** | `passport.js` prints it under the place name, so a municipality needs "Beijing Municipality" or the card reads "Beijing / Beijing" |
| a namesake **inside the same country** needs `search_name` — no downstream guard can catch it | `wrong_place_title` works by spotting a *different* place named in the title, and two Norwegian Hovdens defeat that completely: both videos honestly say "Hovden", both honestly say "Norway", and the only thing that disagrees is a coordinate the text never mentions. The fix has to land before the search, not after — `search_name` sharpens the query (`"Hovden Vesterålen"`) while `name` stays short enough for a map pin. Set it **only** for genuine collisions; it is not a relevance knob |
| membership in more than one category goes in `sets`, never a second region file | `data.js` derives `region_id` from *which file a place lives in*, so the collections (`ancient`, `wild`, `observatory`) are mutually exclusive by construction — moving Taganrog into a fourth would delete it from Europe. `sets` is the additive form: the place declares extra memberships in its own record and keeps its home region. Adding any such field to the merge means **bumping `CACHE_KEY`** — a place cached under the old version has no `sets` key and a filter calling `.includes()` on it throws for as long as the entry stays warm |
| a country name written into a place is a **join key** — copy it from the registry, never retype it | `build_countries.py`'s `live_counts()` matches `loc["country"]` against the registry's canonical name *string*. "Ivory Coast" and "Democratic Republic of the Congo" are both correct English and neither is the spelling the registry uses, so a country would have shown **zero places** while holding four. Nothing errors, nothing warns — the number is just wrong |
| the continent box is the refusal; **Wikidata P17** is the warning beside it | a box wide enough for Bizerte (37.28°N) also contains **Lagos, Portugal** (37.10°N), so on this continent the box cannot catch a namesake on its own. P17 can, but only as a warning: `Tripoli,_Libya` carries **Tripolitania**, and lakes, ranges and cultural landscapes routinely name a neighbour. Print it, read it, don't automate it |
| every writer of `data/media.json` goes through **`tools/medialock.py`** | three tools wrote it concurrently, each reading the whole file at startup and writing the whole file back at every checkpoint — so two overlapping runs meant the second silently reverted the first. The lock is on a `.media.lock` **sidecar**, because `os.replace()` swaps inodes and a lock on the file itself is a lock on a file nobody holds any more. Re-read inside the lock, and never assign back a subtree captured before it |
| a capped run must say **what it did not do** | `--max` defaulted to 10 and printed nothing about the remainder, so a truncated sweep and a finished one produced the same-shaped log. Both enrichers now count candidates before capping and end with `done — this run only` or `done — every candidate place was looked at`. Switching it on revealed a standing backlog of 786 monument searches and 893 media seats that nothing had ever printed |
| **"nothing verifiable" is a finding; a throttle is not** — but an empty search is only evidence of a throttle if **nothing** answered | the streak abort fires at eight consecutive empty YouTube responses, which left the first seven places of a throttled run recording an honest-looking gap on a search that never ran. Each place now measures what happened during *it*. The counter-example is just as important: a narrow query (`Iguéla Lagoon 4K walking tour`, city dropped) genuinely returns zero, and counting empties alone flagged Loango and Ranomafana as "re-run this place" *permanently*. `em.verdict()` asks whether YouTube served any search during that place before it calls anything a refusal. Related: reproduce a sweep rejection with the places **registered** — a bare import never runs `register_place()`, so `wrong_place_title` compares against an empty corpus and cheerfully approves what the real run refused |
| adding a country to the registry is a promise to **four other tables** | `culture.js` keys `COUNTRY_PROFILES` / `COUNTRY_CODES` / `CURRENCY_CODES` / `COUNTRY_FACTS` on the country *name*. A place in a country missing from them renders "Language —, Currency —, Local specialities" with no phrases, no fast facts and no converter — and still looks finished, because the radio list reads `country_code` off the place and never consults these tables. Run `build_culture.py` and diff the registry against all four after **any** region batch; that audit found 44 new African gaps and 59 already-shipped places from earlier batches |
| a generator that **replaces a marked block** must refuse to drop keys it doesn't know | `build_culture.py` rewrites its block wholesale from `ROWS`, so four countries hand-added to `culture.js` and never mirrored back would have vanished on the next run — no error, no diff anyone reads. `check_no_orphans()` now exits non-zero and names them. Same shape as the `--max` lie: the dangerous run is the one whose log looks normal |
| anything emitted into a **single-quoted JS string** gets escaped, not just the strings that need it today | `build_culture.py` interpolated raw values, which was fine until the data contained `Côte d'Ivoire` and `N'Djamena` — an apostrophe closes the string early and breaks the whole module for every page. `esc()` is applied to keys and all fields, including the ones that look safe |
| a region that **crosses ±180** needs two longitude ranges, and so does everything downstream of them | Oceania spans 96.8°E to 130.1°W. One `lng_min <= lng <= lng_max` test either accepts the whole globe or drops everything past the date line, and the same crossing breaks any code that treats longitude as a number line: `WorldMap.drawLine()` drew Auckland → Nukuʻalofa, 1,998 km apart, as a line straight across the map. Split the leg at the edge and take the crossing latitude off the great circle, not off a linear blend |
| **P17 names the sovereign state, not the territory** | the Africa batch's country warning fires on every *correct* Pacific record: Bora Bora → France, Saipan → United States, Adamstown → United Kingdom. Automating it would have deleted the entire non-independent Pacific. `EXPECT_P17` lists the nine expected sovereign answers and downgrades those to a `TERRITORY` note; anything else is still a warning a human reads |
| read a slug's **redirect target**, not just whether it resolves | `MacKenzie_Falls` resolves, 200 OK, correct-looking title — and redirects to **`Sonny_with_a_Chance`**, a Disney sitcom with a show-within-a-show of that name. The Grampians waterfall has no article at all. A slug that resolves to a *different subject* is the failure a link checker cannot see |
| a picker that refuses junk **by word** misses every naming convention that doesn't use the word | Australasian aviation cams are named "Broken Hill - YBHI -> Facing East", never "airport", so eleven of them landed in `data/windy.json` as windows. The ICAO rule has to be case-**sensitive**: under `re.I`, `Y[A-Z]{3}` eats "your", "yard" and "Yarra" |
| a generator that rewrites a whole data file must **merge**, not replace | `fetch_windy.py` built its output dict from empty and wrote it wholesale, so any place whose API call raised vanished from `data/windy.json` with its verified cam — the same shape as the `build_culture.py` orphan bug, one file over. It now starts from what shipped and drops an entry only after re-checking that one and finding nothing |

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

**Build-time only, and deliberately never in the browser:** Wikidata SPARQL
(P625 coordinate checks), Windy Webcams v3, and OpenWebcamDB. The last one is
worth spelling out, because the arithmetic is what decides it: the free tier
allows **25 requests per 24 h** — one every 57.6 minutes — and caps caching at
**one hour**. A single runtime query shape, cached at the maximum the licence
permits, therefore costs 24 requests a day: 96% of the entire budget, for one
query, before a second visitor loads a second page. It cannot be a runtime
integration, so `tools/openwebcamdb.py` is a discovery tool that runs on our
machines and writes ordinary vetted seats into `data/media.json`. It keeps a
persistent rolling-24 h ledger, reconciles it against the server's own
`x-ratelimit-*` headers and believes whichever number is lower, holds 3
requests in reserve, sleeps rather than burst past 5/min, hard-stops on a 429,
and deletes cached responses at 60 minutes rather than serving them stale.
Because no OpenWebcamDB data ever reaches a visitor, their attribution
requirement attaches to no page; the tool prints the credit on its own output,
which is where their data actually surfaces.

Credentials live in gitignored files at mode 600 — `tools/windy.key`,
`tools/openwebcamdb.key`, `tools/nps.key`, `tools/geonames.user`. GeoNames
authenticates by *username*, which makes it look like it isn't a secret; it is,
because a leaked one spends someone else's daily quota.

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
