# 💡 Ideas Parking Lot — One World Tour

Future ideas captured here so they aren't lost. **Nothing in this file is built yet.**
Pick one up only when explicitly asked — don't start these speculatively.

---

## 🕰️ "Back in Time" — watch borders change through history

**The big one.** A time-travel layer over the map: scrub a timeline and watch the world's
borders morph through history.

- Drag a year slider (or hit "play") and the map's political boundaries animate through
  every major border change and world event.
- Go all the way back — past modern nation-states — to the **original Indigenous /
  First Nations territories and clan/nation names across North America** (Canada + USA),
  before colonial borders existed.
- Each major shift (wars, treaties, independence, partitions, unifications) becomes a
  "moment" you can land on, with a short note on what changed and why.

**Why it's a big lift / "note for later":**
- Needs real historical GeoJSON border datasets per era (this is the hard part — sourcing
  accurate, respectfully-researched boundaries, *especially* Indigenous territories, which
  deserve care and good sources like native-land.ca rather than guesswork).
- Likely a **rethink of the app's architecture** — right now it's point markers on a
  static basemap; this wants time-indexed polygon layers, a timeline UI, and probably a
  data pipeline to build/host the era files.
- Could live as its own mode ("History" toggle) or even a separate page.

**Possible data leads to investigate when we tackle it:**
- native-land.ca (Indigenous territories, languages, treaties — has an API)
- Historical Basemaps / "historical-basemaps" open GeoJSON sets (border polygons by year)
- Natural Earth (modern baseline)

> Treat Indigenous territory data with extra care and clear sourcing/attribution.

---

## 📹 Live webcams per city — ✅ v1 shipped (room to grow)

Shipped: a **"Live View"** section on each location page (`setupWebcam()` in `js/location.js`).
- Curated cities embed a real YouTube live cam via an optional `"webcam"` field in the
  location JSON (a YouTube video id string, or `{ "yt" } / { "channel" } / { "poster" }`).
  Seeded so far: Venice, New York City (Times Square), Niagara Falls.
- Every other city falls back to a launcher that opens YouTube's **live** search filter —
  honest and always works, matching the Virtual Walk pattern.
- Streams lazy-load on click (poster first) so we never auto-pull a third-party iframe.

Why not just embed any webcam URL: most dedicated cam sites (EarthCam pages, many Skyline
pages) send `X-Frame-Options`/`frame-ancestors` and refuse to be framed. YouTube live
streams (which is what those providers also publish) embed fine, so that's the channel.

Verified working so far (via YouTube oEmbed): Venice (`a1mcaV3Sf9U`, "I Love You Venice"),
New York / Times Square (`z-jYdOIKcTQ`, EarthCam), Niagara Falls (`qx7gry390YA`, EarthCam).
To vet a candidate id before adding it, hit
`https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=<id>&format=json` — a
200 with a sensible title means the id is real (live-stream ids do rotate, so re-check).

Still to grow:
- Curate `"webcam"` ids for many more cities (Paris, Rome, London, Amsterdam, Prague, …).
- Consider `{ "channel": "UC…" }` (`embed/live_stream?channel=`) for cams that restart
  their stream daily — more durable than a fixed video id.
- Optional: Windy Webcams API (keyed) for coordinate-based auto-discovery, no curation.

---

## 🤫 Ancient Apocalypse (Graham Hancock) — ✅ shipped

A themed collection of **every site from Graham Hancock's Netflix series** (Seasons 1 & 2,
"The Americas"), as its own region: `data/ancient.json` (25 sites), registered in
`data/index.json` with flag `🤫`. It auto-generates the **"🤫 Ancient" filter chip** on the
map, and the sites get a distinct violet marker (`marker-ancient`, see `css/map.css`).

Each entry carries `aa_season`, `aa_episode`, and `aa_claim`; the location page renders a
**"Ancient Apocalypse 🤫"** section (`setupHancock()` in `js/location.js`) showing the episode
and Hancock's claim — framed clearly as *his* claim, with a "Watch on Netflix" link. New
country culture profiles (Mexico, Indonesia, Micronesia, Bahamas, Brazil, Chile, Peru) were
added to `js/culture.js` so these pages have language/currency/facts/radio.

Sites covered: Gunung Padang, Nan Madol, Cholula, Xochicalco, Tetzcotzinco, Ġgantija,
Ħal Saflieni Hypogeum, Bimini Road, Göbekli Tepe, Karahan Tepe, Poverty Point, Serpent
Mound, Derinkuyu, Kaymaklı, Channeled Scablands, Murray Springs, White Sands, Amazon
geoglyphs, Caverna da Pedra Pintada, Rapa Nui, Paracas Candelabra, Sacsayhuamán, Chaco
Canyon, Palenque, Chichén Itzá.

Room to grow: add exact episode *titles*, more secondary sites as `highlights`, and the
"mainstream view vs Hancock's claim" as two explicit lines per site.

---

## 🚶 Virtual Walkthroughs — for places with no live cam — ✅ v1 shipped

The Live View webcam only exists for living cities; ruins and remote sites will never
have one. So the **Virtual Walk** button now opens an **in-page walkthrough overlay**
(`setupWalkthrough()` in `js/location.js`) instead of redirecting to YouTube. It resolves
the best available tier for the place:

- **Tier 1 — curated walking-tour video.** Add `"walk": "<ytid>"` (or `{ "yt": "…" }`) to
  any location and it embeds that 4K walking tour inline.
- **Tier 5 — Ken Burns photo flythrough (universal floor).** With no curated video, it
  pulls ~8 Wikimedia images for the place and plays a slow pan/zoom slideshow with
  captions drawn from the blurb → highlights → fun fact → (for Ancient sites) Hancock's
  claim. Works for *any* place, including all 25 no-cam Ancient sites. Counts toward the
  stamp like Street View. A "more on YouTube" link stays as an honest escape hatch.

**Still to build (the middle tiers, in priority order):**
- **Satellite "descend from orbit"** zoom (Esri World Imagery, free) — and make it the
  *default* for the aerial Ancient sites (geoglyphs, Poverty Point, Serpent Mound) that are
  literally meant to be seen from above.
- **360° photosphere** viewer (Pannellum / Photo Sphere Viewer) for Wikimedia/Flickr 360s.
- **Mapillary / KartaView** street-level sequences (open, covers trails & ruins Google
  Street View doesn't) — could augment the main street-view pane too.
- Optional **narrated mini-tour** via browser `SpeechSynthesis` over the flythrough.

---

## 🧱 Architecture: themed collections are now data-driven — ✅ done

Reassessment outcome (keep the vanilla/static/Leaflet/per-region-JSON foundation — it's
right-sized — but remove the seams that would hurt as collections multiply):

- **Collections are no longer special-cased in code.** A region in `data/index.json` can
  carry `"accent": "#rrggbb"`; that single hex drives both its filter chip
  (`.region-chip-collection`, via `--chip-accent`) and its map markers
  (`.marker-collection`, via `--marker-accent`). Adding the next collection (UNESCO, dark
  tourism, film locations…) needs **zero new CSS** — just the region + accent. Replaces the
  old hardcoded `region_id === 'ancient'` / `.marker-ancient` path.
- **`street_view` is now optional** — `setupMap()` falls back to the plain coordinates, so a
  missing panorama can't crash a page and new entries are lighter to author.

**Still to do (deferred until scale demands it):** a slim generated
`data/locations-index.json` manifest so the map + location pages stop loading *every* region
JSON on every load; canvas marker rendering only if we reach thousands of points.

---

## 🌏 More regions

Asia, South America, Africa, Oceania — extend `data/` with new region JSON files and
register them in `data/index.json`.
