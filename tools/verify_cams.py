#!/usr/bin/env python3
"""
verify_cams.py — re-check the HAND-CURATED live cams. "Live means live", later.

prune_media.py --network already re-verifies the auto-picked cams in
data/media.json. Nothing re-verified the curated ones: `webcam` and `window`
in the region JSONs outrank media.json (js/lib/media.js), were checked once by
hand on the day they were added, and then never again. A curated cam that ends
its broadcast keeps being promised — on the map as a red dot, on the home page
in the "Live right now" rail, in the hero stat — and only dies honestly at
runtime when yt.mount's onError pulls its own tab.

This closes that loop. For every curated cam it asks yt-dlp the same two
questions enrich_media.py asks at hunt time:

    live_status == is_live   and   playable_in_embed

A curated cam may also be { "hls": "https://.../stream.m3u8" }. Those get
the equivalent interrogation from tools/hlscam.py — CORS-open, and segment
names that actually advance — so an HLS cam cannot rot any more quietly
than a YouTube one.

Anything that fails is no longer a live cam and should not sit in a 🔴 or 🪟
seat. --apply deletes the field, which drops the place back to whatever
media.json can offer, or to an honest gap.

Usage:
  python3 tools/verify_cams.py                 # report only
  python3 tools/verify_cams.py --apply         # delete the dead ones
  python3 tools/verify_cams.py --only tokyo,paris
"""
import argparse
import glob
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import enrich_media as em
import hlscam

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"index.json", "countries.json", "windy.json", "media.json",
        "trips.json", "tv.json", "media_denylist.json"}
CAM_FIELDS = ("webcam", "window")          # the two seats that must be live


def cam_pick(value):
    """The curated field accepts 'id', 'id?start=SS', {yt} or {hls}.
       Returns (kind, what) so the caller knows which question to ask."""
    if not value:
        return None, None
    if isinstance(value, dict):
        if value.get("hls"):
            return "hls", value["hls"]
        return ("yt", value["yt"]) if value.get("yt") else (None, None)
    return "yt", str(value)[:11]


def verdict(vid):
    """None if the cam is still a live, embeddable stream — else why not."""
    info = em.full_info(vid)
    if not info:
        return "gone (deleted, private, or the stream ended)"
    if not info.get("is_live"):
        return "no longer live"
    if not em.embeddable(info):
        return "no longer embeddable"
    return None


def hls_verdict(url):
    """The same question for a raw .m3u8 — see tools/hlscam.py for why
       'the segments advanced' is the honest equivalent of is_live."""
    return hlscam.vet(url)["why"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="delete the dead fields")
    ap.add_argument("--only", help="comma-separated place ids")
    args = ap.parse_args()
    only = set(args.only.split(",")) if args.only else None

    checked = dead = 0
    for f in sorted(glob.glob(str(ROOT / "data" / "*.json"))):
        if Path(f).name in SKIP:
            continue
        doc = json.load(open(f))
        if "locations" not in doc:
            continue
        touched = False
        for loc in doc["locations"]:
            if only and loc["id"] not in only:
                continue
            for field in CAM_FIELDS:
                kind, pick = cam_pick(loc.get(field))
                if not pick:
                    continue
                checked += 1
                why = hls_verdict(pick) if kind == "hls" else verdict(pick)
                time.sleep(1)
                shown = pick if kind == "yt" else pick[:64]
                if not why:
                    print(f"  ok   {loc['id']:28} [{field:6}] {shown}")
                    continue
                dead += 1
                touched = True
                print(f"  DEAD {loc['id']:28} [{field:6}] {shown} — {why}")
                if args.apply:
                    loc.pop(field, None)
        if args.apply and touched:
            Path(f).write_text(json.dumps(doc, indent=2, ensure_ascii=False))

    print(f"\n{checked} curated cam(s) checked, {dead} dead"
          f"{'' if args.apply or not dead else ' (report only — pass --apply)'}.")
    if dead and args.apply:
        print("Re-run enrich_media.py on those places to see if media.json can "
              "refill the seat honestly.")


if __name__ == "__main__":
    main()
