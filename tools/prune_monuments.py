#!/usr/bin/env python3
"""Re-apply the CURRENT monument rules to the tabs already on disk.

Same job prune_media.py does for media seats, and for the same reason: a
monument tab is a checkpoint of what the rules said on the day it was written.
When the rules get stricter the old tabs do not re-vet themselves, so the lies
that the new rule was written to stop are still sitting in the region files.

Needs no network — it reads the stored `title`. Auto picks only; a curated
monument is a human decision and this script does not overrule it.

    python3 tools/prune_monuments.py            # dry run, prints what would go
    python3 tools/prune_monuments.py --apply
    python3 tools/prune_monuments.py --titles   # backfill missing titles (slow)

The name rules run without a title, so a dry run is useful immediately. The
title rules skip any tab that has none, which is every tab written before
2026-08-02 — run --titles once to make the whole set auditable.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import enrich_media as em
import enrich_monuments as en

ROOT = Path(__file__).resolve().parent.parent


def verdict(loc, m):
    """Why this tab should go, or None to keep it."""
    name, title = m.get("name") or "", m.get("title")
    key = em.norm(name)
    # The name rules need no title, so they run on tabs written before
    # enrich_monuments.py started storing one. They are also the strongest
    # rules: a landmark that is a dish or a province cannot have an honest
    # video, whatever the search happened to return.
    if en.NOT_A_MONUMENT.search(name):
        return "not a monument"
    if en.is_a_region(loc, key):
        return "an area, not a landmark in one"
    if title is None:
        return None                    # can't judge the video; --titles first
    if en.BAD_MONU.search(title):
        return "title is about something else"
    if not en.mentions_landmark(title, name):
        return "title never names the landmark"
    if em.wrong_place_title(title, loc):
        return "title names somewhere else"
    h = m.get("height")
    if isinstance(h, int) and h < en.MIN_HEIGHT:
        return f"{h}p"
    return None


def backfill_titles(files, places):
    """Store the YouTube title of every auto tab that has none.

    One write per region file, as soon as that file is done, rather than one
    write at the very end: the first attempt at this was a scratchpad script
    that batched all 706 lookups and wrote last, so when it was interrupted at
    250 it had nothing to show for twenty minutes of network. Checkpointing
    costs a few extra json.dump calls and makes the run resumable — re-running
    skips whatever already landed.
    """
    byfile = {}
    for f, loc in places:
        for m in (loc.get("monuments") or []):
            if m.get("source") == "auto" and not m.get("title"):
                byfile.setdefault(f, []).append(m)
    total = sum(len(v) for v in byfile.values())
    print(f"{total} auto tab(s) missing a title")

    cache, done = {}, 0
    for f, mons in byfile.items():
        for m in mons:
            yt = m.get("yt")
            if yt not in cache:
                info = em.full_info(yt)
                cache[yt] = (info or {}).get("title") or "<gone>"
                time.sleep(0.3)
            m["title"] = cache[yt]
            done += 1
            if done % 25 == 0:
                print(f"  {done}/{total}", flush=True)
        # indent=2 — that is what every region file on disk uses (only
        # media.json is indent=1). Writing 1 here reindented eight whole files
        # and buried a 4-line change in a 17,000-line diff.
        json.dump(files[f], open(f, "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        print(f"  wrote {f.name}", flush=True)
    print("done — now run a dry prune to see what the titles reveal")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--titles", action="store_true",
                    help="fetch and store the title of every auto tab missing one")
    args = ap.parse_args()

    files, places = {}, []
    for f in sorted((ROOT / "data").glob("*.json")):
        if f.name in ("index.json", "countries.json", "windy.json", "media.json"):
            continue
        d = json.load(open(f, encoding="utf-8"))
        if not isinstance(d, dict) or "locations" not in d:
            continue
        files[f] = d
        for loc in d["locations"]:
            places.append((f, loc))

    for _, loc in places:                # the guards need the whole gazetteer
        em.register_place(loc)
        for v in (loc.get("country"), loc.get("province"),
                  loc.get("region"), loc.get("_region")):
            if v:
                en.ADMIN_AREAS.add(em.norm(v))

    if args.titles:
        backfill_titles(files, places)
        return

    drops, kept, dirty = 0, 0, set()
    for f, loc in places:
        mons = loc.get("monuments") or []
        if not mons:
            continue
        keep = []
        for m in mons:
            if m.get("source") != "auto":
                keep.append(m)
                continue
            why = verdict(loc, m)
            if why is None:
                keep.append(m)
                kept += 1
                continue
            drops += 1
            dirty.add(f)
            print(f"  {loc['id']:<28} {m.get('name','')[:26]:<28} {why}")
            print(f"      {(m.get('title') or '')[:96]}")
        if len(keep) != len(mons):
            if keep:
                loc["monuments"] = keep
            else:
                loc.pop("monuments", None)

    print(f"\n{drops} to drop, {kept} auto tabs kept")
    if args.apply and dirty:
        for f in dirty:
            json.dump(files[f], open(f, "w", encoding="utf-8"),
                      indent=2, ensure_ascii=False)
        print(f"rewrote {len(dirty)} file(s)")
    elif drops:
        print("dry run — pass --apply to write")


if __name__ == "__main__":
    main()
