#!/usr/bin/env python3
"""
harvest_cams.py — fill 🔴/🪟 seats from the other end of the telescope.

WHY THIS EXISTS
    enrich_media.py hunts cams by asking YouTube "{place} live cam" and four
    other phrasings, once per place. That is a *pull* from 808 places against
    an index that mostly doesn't have what we're asking for: as of this
    writing the corpus has 808 places and only 107 live + 96 window seats
    filled, so ~75% of those searches cost 5 queries and 20 s of politeness
    sleep and come back with nothing. The searches also compete with junk —
    aggregator montages, wildlife loops, the wrong Monteverde.

    This tool goes the other way. A handful of operators run *networks* of
    per-location 24/7 streams on YouTube, each titled with the place it points
    at. One `yt-dlp --flat-playlist` on a channel returns that operator's
    entire live inventory in a single request. Match those titles against our
    gazetteer and you get, for the price of ~8 requests, a list of cams that
    (a) exist, (b) are live right now, and (c) name the place in the title —
    which is precisely the evidence the per-place search was fishing for.

    The leftovers are the other half of the value: a live cam whose title
    names a town we do NOT have is a candidate place that arrives with its
    hardest seat already filled. `--gaps` prints those.

WHAT IT DOES NOT DO
    It does not lower the bar. Every candidate still goes through the same
    vetting enrich_media uses — mentions_place, wrong_place_title, the
    aggregator/wildlife/music-loop guards, and on --apply a full_info fetch
    that must come back is_live AND playable_in_embed. A harvested cam that
    fails is dropped exactly like a searched one. The honesty rule is the
    whole point of the project; a faster way to find candidates is not a
    reason to trust them more.

WHICH CHANNELS, AND WHY NOT THE OBVIOUS ONE
    Measured 2026-08 by listing each channel's /streams and counting
    live_status == is_live in the first 60-80 entries:

      @earthcam                 44 live  "EarthCam Live: {place}"      ✅
      @VirtualRailfan           80 live  "{Town}, {State}, USA | ..."  ✅
      @webcamsdemexico(_live)   17 live  Spanish, names the place      ✅
      @ExploreLiveNatureCams     8 live  wildlife — nature places only ✅
      @MontereyBayAquarium       9 live  one site, many tanks          ✅
      @NASA                      2 live  ISS                           ✅
      @SkylineWebcams            6 live  ❌ ALL montages ("1200 TOP LIVE
                                  WEBCAMS ... with relaxing Music"). Their
                                  2,500 destinations are tokenized HLS on
                                  their own site, NOT on YouTube. The channel
                                  is worthless to us and our AGGREGATOR_CAM
                                  guard already rejects everything on it.
      EarthCam's 2nd channel     0 live  ❌ dormant (UCnG2czp…)

Usage:
  python3 tools/harvest_cams.py                 # what's out there, matched
  python3 tools/harvest_cams.py --gaps          # cams for places we lack
  python3 tools/harvest_cams.py --apply         # vet + write empty seats
  python3 tools/harvest_cams.py --apply --overwrite   # also replace filled ones
  python3 tools/harvest_cams.py --source earthcam
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import medialock                                             # noqa: E402
from enrich_media import (                                   # noqa: E402
    AGGREGATOR_CAM, BAD_CAM, MEDIA, STREET_WORDS, WILDLIFE_CAM, WINDOW_WORDS,
    denied, embeddable, full_info, load_places, mentions_place,
    music_loop_not_a_cam, nature_place, norm, register_place, ytdlp_json,
    OTHER_PLACE_NAMES,
)

CACHE = Path(__file__).resolve().parent / ".cam_harvest.json"
CACHE_TTL_S = 6 * 3600      # a channel's live inventory barely moves in 6 h


class Source:
    def __init__(self, handle, label, nature=False, note=""):
        self.handle = handle
        self.label = label
        self.nature = nature      # wildlife titles are legitimate here
        self.note = note

    @property
    def url(self):
        return f"https://www.youtube.com/{self.handle}/streams"


SOURCES = [
    Source("@earthcam", "EarthCam", note="global, US-heavy, 'EarthCam Live: X'"),
    Source("@VirtualRailfan", "Virtual Railfan",
           note="US/Canada small towns, every one a rail depot"),
    Source("@webcamsdemexico_live", "Webcams de México"),
    Source("@webcamsdemexico", "Webcams de México (main)"),
    Source("@ExploreLiveNatureCams", "explore.org", nature=True,
           note="the largest nature-cam network; nature places only"),
    Source("@MontereyBayAquarium", "Monterey Bay Aquarium", nature=True),
    Source("@NASA", "NASA", note="ISS — matches no ground place, see --gaps"),
]
BY_HANDLE = {s.handle.lstrip("@").lower(): s for s in SOURCES}


# --------------------------------------------------------------- harvesting
def channel_live(src, fresh=False):
    """Every currently-live stream on one channel. One yt-dlp call, cached 6 h."""
    cache = {}
    if CACHE.exists():
        try:
            cache = json.loads(CACHE.read_text())
        except ValueError:
            cache = {}
    hit = cache.get(src.handle)
    if hit and not fresh and time.time() - hit["at"] < CACHE_TTL_S:
        return hit["live"], "cache"

    rows = ytdlp_json(["--flat-playlist", "-j", "--playlist-end", "120", src.url],
                      timeout=240)
    live = [{"id": r.get("id"), "title": (r.get("title") or "").strip()}
            for r in rows if r.get("live_status") == "is_live" and r.get("id")]
    cache[src.handle] = {"at": time.time(), "live": live}
    CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
    return live, "fetched"


# ------------------------------------------------------------------ matching
def name_re(name):
    """A pattern for one place name, tolerant of how a cam operator punctuates.

    `\\b` is the wrong tool here: the name "Washington, D.C." ends in a dot, and
    in "…(Washington, D.C.)" the next character is a bracket, so \\b — which
    needs a word char on one side — never fires and EarthCam's Washington
    Monument cam looked like a cam for a city we don't have. Match on
    alphanumeric runs instead and let any punctuation sit between them.
    """
    parts = [re.escape(w) for w in re.findall(r"[a-z0-9]+", norm(name))]
    if not parts:
        return None
    return re.compile(r"(?<![a-z0-9])" + r"[^a-z0-9]*".join(parts) +
                      r"(?![a-z0-9])")


def index_places(places):
    """[(pattern, place)] — the cheap prefilter before the guards.

    Matching every cam title against every place with the full guard stack is
    200 × 808 regex storms; testing the name first cuts that to a handful of
    candidates per title and changes nothing about the verdict, because a title
    that doesn't contain the name can't pass mentions_place anyway.

    Aliases come along for the ride: enrich_media already knows Mexico City
    answers to "Ciudad de México", and cam operators write in their own
    language far more often than in ours.
    """
    from enrich_media import ALIASES
    idx = []
    for p in places:
        seen = set()
        for label in [p["name"], *(ALIASES.get(p.get("id") or "") or [])]:
            rx = name_re(label)
            if rx and len(re.findall(r"[a-z0-9]+", norm(label))) and \
                    rx.pattern not in seen and len(norm(label)) >= 3:
                seen.add(rx.pattern)
                idx.append((rx, len(label), p))
    return idx


def candidates_for(title, idx):
    t = norm(title)
    out = [(ln, p) for rx, ln, p in idx if rx.search(t)]
    # longest name first: "Salt Lake City" beats a stray "Lake" place
    seen, ranked = set(), []
    for _, p in sorted(out, key=lambda x: -x[0]):
        if p["id"] not in seen:
            seen.add(p["id"])
            ranked.append(p)
    return ranked


def seat_of(title):
    """street → live seat, skyline/harbour → window seat, unclear → either."""
    if WINDOW_WORDS.search(title) and not STREET_WORDS.search(title):
        return "window"
    if STREET_WORDS.search(title):
        return "live"
    return "either"


def usable(title, place, src):
    """The same title rules find_cams applies, in the same order."""
    if BAD_CAM.search(title) or AGGREGATOR_CAM.search(title):
        return False
    if music_loop_not_a_cam(title):
        return False
    if WILDLIFE_CAM.search(title) and not (nature_place(place) or src.nature):
        return False
    if not mentions_place(title, place):
        return False
    from enrich_media import wrong_place_title
    return not wrong_place_title(title, place)


# -------------------------------------------------------------------- report
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--source", help="only this channel handle (e.g. earthcam)")
    ap.add_argument("--gaps", action="store_true",
                    help="show live cams that match NO place we have")
    ap.add_argument("--apply", action="store_true",
                    help="vet the matches and write them into media.json")
    ap.add_argument("--overwrite", action="store_true",
                    help="with --apply, also replace seats that are already full")
    ap.add_argument("--fresh", action="store_true", help="ignore the 6 h cache")
    args = ap.parse_args()

    sources = SOURCES
    if args.source:
        key = args.source.lstrip("@").lower()
        if key not in BY_HANDLE:
            sys.exit(f"unknown source {args.source!r} — have: "
                     f"{', '.join(sorted(BY_HANDLE))}")
        sources = [BY_HANDLE[key]]

    places = load_places()
    for p in places:
        register_place(p)
        OTHER_PLACE_NAMES.add(norm(p["name"]))
    idx = index_places(places)

    media = medialock.load()
    media.setdefault("places", {})

    matched, orphans = [], []
    for src in sources:
        live, how = channel_live(src, fresh=args.fresh)
        print(f"{src.label:<24} {len(live):>3} live  ({how})"
              + (f"  — {src.note}" if src.note else ""))
        for cam in live:
            hits = [p for p in candidates_for(cam["title"], idx)
                    if usable(cam["title"], p, src) and not denied(p, cam["id"])]
            if hits:
                matched.append((src, cam, hits[0]))
            else:
                orphans.append((src, cam))
        if len(sources) > 1:
            time.sleep(2)

    if args.gaps:
        print(f"\n── {len(orphans)} live cam(s) matching no place on our map ──")
        print("   (each is a place we could add that arrives with its hardest "
              "seat already filled)\n")
        for src, cam in orphans:
            print(f"  {src.label:<22} {cam['title'][:78]}")
            print(f"  {'':<22} https://youtu.be/{cam['id']}")
        return

    print(f"\n── {len(matched)} cam(s) matched to places we have ──\n")
    todo = []
    for src, cam, place in matched:
        want = seat_of(cam["title"])
        entry = media["places"].get(place["id"], {})
        seats = ("live", "window") if want == "either" else (want,)
        open_seats = [s for s in seats
                      if not entry.get(s) and not place.get(
                          "webcam" if s == "live" else "window")]
        flag = "NEW " if open_seats else "have"
        print(f"  {flag} {place['id']:<26} {want:<7} {cam['title'][:56]}")
        if open_seats or args.overwrite:
            todo.append((place, cam, (open_seats or list(seats))[0]))

    if not args.apply:
        print(f"\n{len(todo)} seat(s) would be filled. Re-run with --apply to "
              f"vet and write them.")
        return

    # ---- the same vetting gate as enrich_media: live NOW, embeddable NOW ----
    print(f"\nvetting {len(todo)} candidate(s) — is_live + playable_in_embed…")
    now = datetime.now(timezone.utc).date().isoformat()
    wrote = 0
    for place, cam, seat in todo:
        info = full_info(cam["id"])
        ok = bool(info) and info.get("is_live") and embeddable(info)
        if not ok:
            print(f"  ✗ {place['id']:<26} {seat:<7} not live/embeddable now")
            continue
        entry = media["places"].setdefault(place["id"], {})
        twin = "window" if seat == "live" else "live"
        if (entry.get(twin) or {}).get("yt") == info["id"]:
            print(f"  ✗ {place['id']:<26} {seat:<7} already in the {twin} seat")
            continue
        entry[seat] = {"yt": info["id"], "title": info.get("title", ""),
                       "verified": now}
        wrote += 1
        print(f"  ✓ {place['id']:<26} {seat:<7} {info['id']}")
        # One seat, through the lock, onto the CURRENT file — `media` is a
        # startup snapshot and a long enrich_media sweep may have written
        # since. Capture the loop vars so the closure can't drift.
        medialock.update(lambda doc, _p=place["id"], _s=seat, _v=entry[seat]:
                         doc["places"].setdefault(_p, {}).__setitem__(_s, _v))
        time.sleep(1)
    print(f"\nwrote {wrote} seat(s) → {MEDIA}")


if __name__ == "__main__":
    main()
