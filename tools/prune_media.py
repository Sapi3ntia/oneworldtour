#!/usr/bin/env python3
"""
prune_media.py — drop auto-picked scenes that today's rules would refuse.

The vetting rules in enrich_media.py get stricter as bad picks are found in
the wild. But data/media.json is a CHECKPOINT: once a city has a scene, the
enricher never revisits it, so a pick made under looser rules lives forever.
This tool re-applies the CURRENT rules to what is already on disk and deletes
whatever no longer passes. The next enrich_media.py run then re-hunts those
seats under the stricter rules.

Title-only by default (free, no network). What that catches:
  • multi-city rotators sold as one place's cam
  • wildlife nest boxes sold as a CITY's live cam or window
  • namesake towns ("Manchester, NH" for Manchester, England)
  • news/war streams

With --network it additionally re-checks each cam's `is_live`, so feeds that
died since they were verified stop being promised. That is the honest fix for
"live means live" drifting over time — until now a dead cam only died at
runtime via the player's onError.

Usage:
  python3 tools/prune_media.py                # dry run, title rules only
  python3 tools/prune_media.py --apply
  python3 tools/prune_media.py --apply --network   # also re-check is_live
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import enrich_media as em

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "data" / "media.json"


def reason_to_drop(place, seat, entry, network=False):
    """Why today's rules refuse this pick, or None if it still passes."""
    title = entry.get("title") or ""
    if not entry.get("yt"):
        return "no video id"
    if em.BAD_CAM.search(title) and seat in ("live", "window"):
        return "news/war stream"
    if seat in ("live", "window"):
        if em.AGGREGATOR_CAM.search(title):
            return "multi-city rotator, not this place"
        if not em.nature_place(place) and em.WILDLIFE_CAM.search(title):
            return "wildlife/nest cam, not a view of the place"
    if title and not em.mentions_place(title, place):
        return "title never names the place"
    if title and em.wrong_place_title(title, place):
        return "title anchors a different place"
    if network and seat in ("live", "window"):
        info = em.full_info(entry["yt"])
        time.sleep(1)
        if not info:
            return "video gone"
        if not info.get("is_live"):
            return "no longer live"
        if not em.embeddable(info):
            return "no longer embeddable"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the deletions")
    ap.add_argument("--network", action="store_true", help="also re-check is_live")
    ap.add_argument("--seat", choices=["walk", "drive", "live", "window"],
                    help="only this seat")
    args = ap.parse_args()

    media = json.load(open(MEDIA))
    places = {p["id"]: p for p in em.load_places()}
    for p in places.values():
        c = p.get("coordinates") or {}
        em.OTHER_PLACES[p["id"]] = (em.name_tokens_of(p), c.get("lat", 0), c.get("lng", 0))
        em.COUNTRY_NAMES.add(em.norm(p.get("country") or ""))

    dropped = 0
    for pid, seats in list(media.get("places", {}).items()):
        place = places.get(pid)
        if not place:
            continue
        for seat in ("walk", "drive", "live", "window"):
            if args.seat and seat != args.seat:
                continue
            entry = seats.get(seat)
            if not isinstance(entry, dict):
                continue
            why = reason_to_drop(place, seat, entry, args.network)
            if not why:
                continue
            dropped += 1
            print(f"  drop {pid:24} [{seat:6}] {why}")
            print(f"       {(entry.get('title') or '')[:74]}")
            if args.apply:
                seats.pop(seat, None)
        if args.apply and not seats:
            media["places"].pop(pid, None)

    if args.apply and dropped:
        MEDIA.write_text(json.dumps(media, indent=1, ensure_ascii=False))
        print(f"\n{dropped} pick(s) dropped — re-run enrich_media.py to refill "
              f"those seats under the current rules.")
    else:
        print(f"\n{dropped} pick(s) would be dropped"
              f"{' (dry run — pass --apply)' if dropped else ''}.")


if __name__ == "__main__":
    main()
