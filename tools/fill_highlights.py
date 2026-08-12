#!/usr/bin/env python3
"""
fill_highlights.py — give the last skeleton places something to say (2026-08).

WHY
    68 places across africa/ancient/asia/europe/oceania had an empty
    `highlights` array AND no `monuments`. That pairing is not a coincidence:
    `enrich_monuments.py` spends highlights as its search terms, so a place
    with none can never earn a monument tab however famous it is. Uluru, Dubai,
    Cape Town, Vatican City and Lake Baikal were all in that state — the map
    had a pin, the arrival card had an emoji, and the sweep had nothing to
    search for. This is the other half of "add monuments to every place that
    has none": for these, the missing thing was never the video.

WHAT
    A merge-only pass. It never creates a place and never touches coordinates,
    `walk`, `webcam`, `window` or `monuments` — those belong to the scene
    pipeline. It fills `highlights`, `blurb`, `fun_fact`, `hidden_gem_tip` and
    `region`, and only where the field is empty, so a re-run is a no-op and a
    human edit is never overwritten.

    Editorial choice is ours; every slug is resolved live against Wikipedia and
    stored as the article's CANONICAL title, per README "Filling a region out".
    A redirect does not return a `pageimages` thumbnail, so an uncanonicalised
    slug silently degrades the arrival card to its emoji.

    highlights are STRUCTURES, TOWNS AND LANDFORMS ONLY — never a people, a
    dish, a dynasty, a deity, an era or a festival (enrich_monuments
    .NOT_A_MONUMENT). A `None` slug is deliberate: the UI renders highlights as
    text chips, so an unlinked name costs nothing and a dead link is rot.

Run:  python3 tools/fill_highlights.py            # report only
      python3 tools/fill_highlights.py --apply
      python3 tools/fill_highlights.py --only uluru,dubai
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_wiki import Resolver, haversine

ROOT = Path(__file__).resolve().parent.parent
SKIP_FILES = {"index.json", "countries.json", "windy.json", "media.json",
              "tv.json", "trips.json", "media_denylist.json"}
FAR_KM = 75.0
AREA_TYPES = {"nature", "desert", "island", "mountain", "region"}

from fill_highlights_data import FILL          # noqa: E402  (the content table)


class Notes:
    def __init__(self):
        self.rows = []
        self.unresolved = 0

    def add(self, kind, where, what, why=""):
        self.rows.append((kind, where, what, why))
        if kind == "UNRESOLVED":
            self.unresolved += 1

    def print(self):
        order = {"UNRESOLVED": 0, "MISSING": 1, "SELF": 2, "FAR": 3, "REDIRECT": 4}
        for kind, where, what, why in sorted(
                self.rows, key=lambda r: (order.get(r[0], 9), r[1], r[2])):
            print(f"{kind:<10} {where:<24} {what:<46} {why}")
        counts = {}
        for kind, *_ in self.rows:
            counts[kind] = counts.get(kind, 0) + 1
        if counts:
            print("\n" + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))


def load():
    """Every region file, and an id -> (file, record) index across all of them."""
    files, index = {}, {}
    for f in sorted((ROOT / "data").glob("*.json")):
        if f.name in SKIP_FILES:
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(d, dict) or "locations" not in d:
            continue
        files[f] = d
        for loc in d["locations"]:
            index[loc["id"]] = (f, loc)
    return files, index


def link(slug, got, notes, where, own):
    """Canonical title to store, or None to leave the chip unlinked."""
    e = got.get(slug) or {}
    if "title" not in e and not e.get("missing"):
        notes.add("UNRESOLVED", where, slug, "no answer from the API — rerun")
        return None
    if e.get("missing"):
        notes.add("MISSING", where, slug, "no article — kept as a text chip")
        return None
    title = e["title"]
    if own and title == own:
        # Worse than a dead link: it promises a second place and delivers the
        # one you are already standing in.
        notes.add("SELF", where, slug, "resolves to the place itself — unlinked")
        return None
    if e.get("redirect"):
        notes.add("REDIRECT", where, slug, f"-> {title}")
    return title


def far_check(loc, hl, got, notes):
    if loc.get("type") in AREA_TYPES:
        return
    here = loc.get("coordinates") or {}
    if here.get("lat") is None:
        return
    for h in hl:
        s = h.get("wikipedia_slug")
        e = got.get(s) or {}
        if e.get("lat") is None:
            continue
        d = haversine((here["lat"], here["lng"]), (e["lat"], e["lng"]))
        if d > FAR_KM:
            notes.add("FAR", loc["id"], f"{h['name']} [{s}]",
                      f"{d:,.0f} km from {loc['name']}")


def fill(loc, spec, got, notes):
    wrote = []
    if spec.get("region") and not loc.get("region"):
        loc["region"] = spec["region"]
        wrote.append("region")
    if spec.get("highlights") and not loc.get("highlights"):
        own = loc.get("wikipedia_slug")
        hl = []
        for name, slug in spec["highlights"]:
            h = {"name": name}
            t = link(slug, got, notes, loc["id"], own) if slug else None
            if t:
                h["wikipedia_slug"] = t
            hl.append(h)
        loc["highlights"] = hl
        far_check(loc, hl, got, notes)
        wrote.append("highlights")
    for key, src in (("blurb", "blurb"), ("fun_fact", "fact"),
                     ("hidden_gem_tip", "tip")):
        if spec.get(src) and not loc.get(key):
            loc[key] = spec[src]
            wrote.append(key)
    return wrote


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", help="comma-separated place ids")
    ap.add_argument("--refresh", action="store_true",
                    help="ignore the slug cache and ask Wikipedia again")
    args = ap.parse_args()

    files, index = load()
    only = set(args.only.split(",")) if args.only else None
    todo = {p: s for p, s in FILL.items() if not only or p in only}

    unknown = [p for p in todo if p not in index]
    if unknown:
        sys.exit(f"no such place id: {unknown}")

    want = [s for spec in todo.values()
            for _, s in spec.get("highlights", []) if s]
    print(f"{len(todo)} place(s), resolving {len(set(want))} slug(s) …")
    got = Resolver(refresh=args.refresh).resolve(want)

    notes, done, dirty = Notes(), [], set()
    for pid, spec in todo.items():
        f, loc = index[pid]
        wrote = fill(loc, spec, got, notes)
        if wrote:
            done.append((f.name, pid, wrote))
            dirty.add(f)

    notes.print()
    print(f"\n{len(done)} place(s) filled across {len(dirty)} file(s)")
    for fn, pid, wrote in done:
        print(f"  {fn:<18} {pid:<24} {', '.join(wrote)}")

    if notes.unresolved:
        # A throttled request is not a verdict. Refuse to write a half-checked
        # file rather than quietly drop the links the API never answered about.
        sys.exit(f"\n{notes.unresolved} slug(s) unresolved — rerun before --apply")
    if not args.apply:
        print("\ndry run — pass --apply to write")
        return
    for f in dirty:
        f.write_text(json.dumps(files[f], ensure_ascii=False, indent=2),
                     encoding="utf-8")
    print(f"✓ rewrote {len(dirty)} file(s)")


if __name__ == "__main__":
    main()
