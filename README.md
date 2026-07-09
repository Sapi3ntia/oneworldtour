# ✈️ One World Tour

An immersive **virtual tourism** web app. Spin a dark, cinematic world map, fly to a
city, and *arrive* — live local time and weather, local radio on air right now, ambient
soundscapes, today's headlines, a phrasebook, food, a virtual walking tour, and a real
window onto the place. Collect passport stamps as you explore.

Inspired by the spirit of [virtualvacation.us](https://virtualvacation.us/) — the goal is
to make the map *feel* like being somewhere, not just look at a pin. The one rule that
makes it ours: **every scene is skippable and seekable**, and a feature either embeds the
real thing in-app or honestly says it doesn't exist — no off-site "watch on YouTube"
escape hatches, no still photo posing as a live view.

> Status: **playable and feature-complete**, now at **345 places across 89 countries**.
> Windows (live cams + timelapses) and walking tours are live across the map. The single
> orientation doc is [`TODO.md`](TODO.md) — ideas not yet built, and the guardrails
> (perf, map clustering, media honesty) worth not relearning.

---

## ✨ Features

| Feature | What it does | Source |
|---|---|---|
| 🗺️ **World map** | Leaflet dark map with crisp country **borders + labels**, marker clustering (click a circle → it opens to the places inside), region/tag filters **plus content filters — 🪟 Window / 🚶 Tour / ✨ Both**, search-as-you-type with an **autocomplete dropdown** (🔴/🪟/🎬/🚶 flagged), "Surprise me" teleport, real-time day/night terminator | local data |
| ✈️ **Flight arrival** | Great-circle plane animation flies from your last stop to the new one | client-side math |
| 🧳 **Fly the Tour** | Plan an ordered multi-city route, then watch the plane fly the whole journey leg by leg | client-side |
| 🎬 **Arrival cinematic** | Full-screen hero photo + name on entry, click to explore | Wikimedia |
| 🕐 **Right now** | Live local clock + current weather at the destination | Open-Meteo |
| 🚶🪟 **Step Outside** | On every place page, three fixed frames in the same spot every city: a big **auto-starting walking tour** (curated footage, muted, fully seekable), a **🔴 live cam**, and a smaller **🪟 window** (a chrome-free looping "out-the-window" clip) — all curated YouTube, with an honest empty frame when one doesn't exist yet, never a still or a branded widget standing in for a live view | YouTube |
| 🪟 **Virtual Window** | Open a framed window and *look out* — a **🔴 live cam**, a **🪟 live timelapse** (a real current view that updates through the day), or a **🎬 ambient view** (a curated recorded "out the window" loop), **always labelled which is which** (badge + chip + legend). Real local-time / day-night / temperature plate, optional ambient soundscape, "open another window" to hop the world | Windy + YouTube + Open-Meteo |
| 🏛️ **Monument tours** | Up to 3 named landmark videos per city (Eiffel Tower, Colosseum…), a tab-picker feeding one in-app player | YouTube |
| 🤫 **Ancient Apocalypse** | Every site from Graham Hancock's Netflix series, mapped — filter with the 🤫 chip; each page shows the episode + the claim | bundled + Wikipedia |
| 📻 **Local radio** | Real radio streams from the destination's country, playing live | Radio Browser API |
| 🔊 **Ambient soundscape** | Procedural ambience synthesized in-browser (no audio files) | Web Audio API |
| 📰 **Today's headlines** | Recent local news for the place, with timestamps | GDELT DOC 2.0 |
| 🍽️ **Local flavor** | Language, key phrases (native + phonetic), currency + live FX, signature dish | bundled + open.er-api |
| 🎬 **Drop In** | Toggle on, tap *anywhere* on the map → instantly watch a skippable walkthrough of the nearest place (a better "videarth"). Tap open ocean and it says so | client-side + Wikimedia / YouTube |
| 🌍 **City Guesser** | Dropped into a mystery place's blind scene; click the map to guess, scored GeoGuessr-style on distance over 5 rounds, copy a spoiler-free Wordle-style score | client-side + Wikimedia / YouTube |
| 🖼️ **Photo gallery + highlights** | Place imagery and per-landmark stories | Wikimedia / Wikipedia |
| 💬 **Ask the Guide** | Conversational Q&A about the place (optional, needs backend) | Claude API |
| 📮 **Postcard studio** | Compose a captioned postcard on a canvas and download it | client-side |
| 📘 **Passport** | Stamps, notes, and stats for everywhere you've visited | localStorage |
| 🌍 **345 destinations / 89 countries** | Canada, USA, Europe, Asia, Africa, Oceania, Latin America + 25 Ancient Apocalypse sites | bundled JSON |

Everything except **Ask the Guide** works with **no API keys and no backend** — all the
runtime external APIs used are free and CORS/embed-friendly. (One build-time tool uses a
Windy key; it never ships to the browser — see [`TODO.md`](TODO.md).)

---

## 🚀 Quick start

No build step. It's a static site — just serve the folder.

```bash
cd oneworldtour
python3 -m http.server 8099
# open http://localhost:8099
```

> Open it through a server, not `file://` — the app fetches local JSON and calls browser
> APIs that won't work from the filesystem.

### Optional: the "Ask the Guide" backend

The guide Q&A is the only feature that needs a server and a key. Without it the rest of
the app runs fine; the guide box just won't answer.

```bash
cd backend
pip install -r requirements.txt
ANTHROPIC_API_KEY=sk-... uvicorn server:app --reload --port 8000
```

The frontend calls the proxy so your API key never ships to the browser.

---

## 🗂️ Project structure

```
oneworldtour/
├── index.html            # The world map (home)
├── location.html         # A single destination experience
├── window.html           # Virtual Window
├── guess.html            # City Guesser game
├── passport.html         # Stamps, notes, stats
├── css/                  # main.css (tokens) + per-page sheets
├── js/
│   ├── state.js          # localStorage state + Geo math helpers
│   ├── api.js            # External API calls (weather, photos, radio, news, FX…)
│   ├── destinations.js   # Shared region loader (Destinations.loadAll)
│   ├── map.js            # Map, clustering, filters, search, flight animation
│   ├── location.js       # Arrival + the full destination experience
│   ├── culture.js        # Per-country language / phrases / currency / dish
│   ├── radio.js          # Live radio player
│   ├── soundscape.js     # Procedural Web Audio ambience
│   ├── webcam.js         # Window resolver — live cams, Windy timelapses, ambient views
│   ├── walkthrough.js    # Shared scene player (Drop In, City Guesser)
│   ├── window.js         # Virtual Window logic
│   ├── guess.js          # City Guesser game logic
│   └── passport.js       # Passport page logic
├── data/
│   ├── index.json        # Region registry (which JSON files load)
│   ├── countries.json    # Canonical 89-country registry (ISO code / flag / continent)
│   ├── canada.json · usa.json · europe.json · asia.json
│   ├── africa.json · oceania.json · latinamerica.json · ancient.json
│   └── windy.json        # Build-time webcam sidecar (keyless runtime embeds)
├── tools/                # Python scripts used to build/enrich the data
└── backend/              # Optional FastAPI proxy for "Ask the Guide"
```

---

## 🔌 External services (all free; no runtime key needed)

| Service | Used for |
|---|---|
| [Open-Meteo](https://open-meteo.com/) | Current weather + timezone |
| [Radio Browser](https://www.radio-browser.info/) | Live local radio streams |
| [GDELT DOC 2.0](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) | Local news headlines |
| [Wikipedia / Wikimedia REST](https://www.mediawiki.org/wiki/API:REST_API) | Blurbs, highlights, photos, Ken Burns frames |
| [open.er-api.com](https://www.exchangerate-api.com/docs/free) | Currency exchange rates |
| [Windy Webcams](https://www.windy.com/webcams) | Live cams + day timelapses (keyless **public embed** at runtime; a keyed API is used **build-time only**) |
| [YouTube](https://www.youtube.com/) | Curated live cams, ambient window loops, walking tours, monument tours (in-app, no redirect) |
| [CARTO basemaps](https://carto.com/basemaps/) + [Esri](https://www.esri.com/) | Dark map tiles (base) + country borders/labels overlay |
| Anthropic Claude API | "Ask the Guide" (optional, via backend) |

> **Note on GDELT:** it rate-limits aggressively (HTTP 429). The news section degrades
> gracefully — it hides itself rather than showing a broken state — and recovers on its own.

---

## 💾 Data & privacy

All your progress — visited places, wishlist, notes, passport stamps — lives in your
browser's **localStorage**. Nothing is uploaded; clearing site data resets it.

localStorage keys: `owt_visited`, `owt_saved`, `owt_notes`, `owt_sound_off`,
`owt_last_pos` (flight departure point), `owt_trip` (planned route),
`owt_last_window` (the last Virtual Window you opened).

---

## 🛠️ Adding destinations

1. Add an entry to the relevant `data/<region>.json` (or add a new file and register it in
   `data/index.json`).
2. Minimum fields: `id`, `name`, `country`, `coordinates {lat,lng}`, `emoji`, `tag`
   (`famous` | `hidden`), and a short `blurb`. See existing entries for the full shape.
3. *Windows happen automatically.* `tools/fetch_windy.py` already maps a Windy webcam to
   ~247 cities (`data/windy.json`). To **override** the Windy pick with a hand-curated cam
   (it always wins), add a `webcam` (🔴 live) or `ambient` (🎬 recorded loop) field — verify
   first (a curated feed always outranks the Windy fallback; see [`TODO.md`](TODO.md)).
4. *(Optional)* Add a curated walking tour with `"walk": "<youtube-id>"` and/or up to three
   `monuments` (`[{name, yt, start?}]`). **Don't recall ids from memory** — find one, then
   confirm it via YouTube's oEmbed endpoint before committing.
5. Reload — no rebuild needed.

To register a **themed collection** (like Ancient Apocalypse): add a region in
`data/index.json` with an `"accent": "#rrggbb"` (and optional `"collection": "Name"`). That
one hex drives its filter chip *and* its map markers — no new CSS needed.

---

## 🧰 Tech

Vanilla JavaScript (no framework, no bundler) · [Leaflet](https://leafletjs.com/) 1.9.4 +
markercluster · CARTO dark tiles + Esri reference overlay · Windy public webcam embeds ·
Web Audio API · HTML canvas · Playfair Display + Inter. Optional backend: FastAPI + Uvicorn.

---

## 🗺️ Roadmap (short version)

**Shipped:** world map (clustering, borders/labels, filters, autocomplete, Surprise me,
Fly-the-Tour, Drop In, day/night) · location page (arrival, Step Outside, culture, radio,
weather, news, photos, monuments, postcard, Ask the Guide) · **Virtual Window** (live /
timelapse / ambient) · **City Guesser** · **Passport** · **Ancient Apocalypse** collection ·
procedural soundscapes · **345 places / 89 countries** · **247 windows (105 live)** ·
**51 walks** · **24 monument tours**.

**Next up (depth over breadth):** more curated walks + monuments for marquee cities ·
author `highlights`/`blurb` for the content-thin new countries · `onError`→honest-fallback
on the curated YouTube window iframe · map findability dropdown + creative cluster ideas ·
native-speaker review of the 50 new culture profiles.

**Bigger future bets:** "Back in Time" historical/Indigenous borders timeline · walkthrough
middle tiers (satellite descend-from-orbit, 360° photospheres, Mapillary street-level).

> Ideas not yet built and the guardrails worth keeping live in **[`TODO.md`](TODO.md)**.

---

*A joint creative project. Built to make the whole world feel a little closer.* 🌍
