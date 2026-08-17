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
import medialock

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "data" / "media.json"


def reason_to_drop(place, seat, entry, network=False):
    """Why today's rules refuse this pick, or None if it still passes."""
    title = entry.get("title") or ""
    if not entry.get("yt"):
        return "no video id"
    why = em.denied(place, entry["yt"])
    if why:
        return f"reviewed and rejected — {why}"
    if em.BAD_CAM.search(title) and seat in ("live", "window"):
        return "news/war stream"
    if seat in ("live", "window"):
        if em.AGGREGATOR_CAM.search(title):
            return "multi-city rotator, not this place"
        if em.music_loop_not_a_cam(title):
            return "scenery under a music bed, not a camera"
        if not em.nature_place(place) and em.WILDLIFE_CAM.search(title):
            return "wildlife/nest cam, not a view of the place"
    if seat in em.NIGHT_SEATS and title:
        # a night seat that isn't at night is just the day seat twice
        if not em.NIGHT_WORDS.search(title):
            return "night seat, but the title never says it's dark"
        if em.BAD_NIGHT.search(title):
            return "'night' in the title, but not the time of day"
    if seat in ("walk", "drive") and title and not em.daylight_title(title):
        # the mirror rule, and the one that was missing: a day seat has
        # to be daylight, or "Midnight Drive" ships as the Driving tour
        return "day seat, but the title says it's shot at night"
    # the subject guards the enricher applies at search time, re-applied here
    # so a pick made before a guard existed doesn't outlive it
    if seat in ("walk", "night_walk") and title and em.BAD_WALK.search(title):
        return "not a walk"
    if seat in ("drive", "night_drive") and title and em.BAD_DRIVE.search(title):
        return "not a drive"
    if title and em.city_tour_of_the_wild(title, place):
        return "a city tour, offered as a wild place's scene"
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
    ap.add_argument("--seat", choices=[*em.SEATS, *em.NIGHT_SEATS],
                    help="only this seat")
    args = ap.parse_args()

    media = medialock.load()
    # Exactly which (place, seat) pairs this run refuses, so --apply can remove
    # those and nothing else. Overwriting a whole place's seat dict would
    # revert any seat a concurrent enrich_media sweep filled meanwhile.
    drops = []
    places = {p["id"]: p for p in em.load_places()}
    for p in places.values():
        em.register_place(p)
        em.OTHER_PLACE_NAMES.add(em.norm(p["name"]))
        em.COUNTRY_NAMES.add(em.norm(p.get("country") or ""))

    dropped = 0
    for pid, seats in list(media.get("places", {}).items()):
        place = places.get(pid)
        if not place:
            continue
        gone = set()          # so the dry run reports what --apply would do
        for seat in (*em.SEATS, *em.NIGHT_SEATS):
            if args.seat and seat != args.seat:
                continue
            entry = seats.get(seat)
            if not isinstance(entry, dict):
                continue
            why = reason_to_drop(place, seat, entry, args.network)
            if not why:
                continue
            dropped += 1
            gone.add(seat)
            drops.append((pid, seat, entry.get("yt")))
            print(f"  drop {pid:24} [{seat:6}] {why}")
            print(f"       {(entry.get('title') or '')[:74]}")
            if args.apply:
                seats.pop(seat, None)

        # cross-seat: a title carrying both "daytime" and "evening" can
        # legitimately pass day AND night vetting, so one video can land
        # in both twins. The night seat loses — it's the one making the
        # more specific promise.
        for day, nite in (("walk", "night_walk"), ("drive", "night_drive")):
            if gone & {day, nite}:
                continue          # already resolved by a rule above
            a, b = seats.get(day), seats.get(nite)
            if isinstance(a, dict) and isinstance(b, dict) and a.get("yt") == b.get("yt"):
                dropped += 1
                drops.append((pid, nite, b.get("yt")))
                print(f"  drop {pid:24} [{nite:6}] same video as the {day} seat")
                print(f"       {(b.get('title') or '')[:74]}")
                if args.apply:
                    seats.pop(nite, None)

        if args.apply and not seats:
            media["places"].pop(pid, None)

    if args.apply and dropped:
        # Remove the refused seats from whatever is on disk NOW, keyed by video
        # id: if a concurrent sweep has already refilled a seat with a
        # DIFFERENT video, that pick was never judged here and stays.
        stale = []

        def mutate(doc):
            for pid, seat, yt in drops:
                seats = doc["places"].get(pid)
                if not seats:
                    continue
                cur = seats.get(seat)
                if isinstance(cur, dict) and cur.get("yt") != yt:
                    stale.append((pid, seat))
                    continue
                seats.pop(seat, None)
                if not seats:
                    doc["places"].pop(pid, None)
        medialock.update(mutate)
        for pid, seat in stale:
            print(f"  kept {pid:24} [{seat:6}] refilled since this run read "
                  f"the file — not judged, not dropped")
        print(f"\n{dropped - len(stale)} pick(s) dropped — re-run "
              f"enrich_media.py to refill those seats under the current rules.")
    else:
        print(f"\n{dropped} pick(s) would be dropped"
              f"{' (dry run — pass --apply)' if dropped else ''}.")


if __name__ == "__main__":
    main()
