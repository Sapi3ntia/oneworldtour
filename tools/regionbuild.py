#!/usr/bin/env python3
"""
regionbuild.py — the frame every region generator has been copy-pasting.

WHY THIS EXISTS
    `build_africa.py`, `build_oceania.py` and `build_latinamerica.py` are the
    same 300 lines of machinery with a different roster bolted on top:
    resolve every slug live, refuse a record whose P625 lands outside the
    region, warn when P17 disagrees with the country the record claims, store
    the article's *canonical* title, keep highlights honest, and never
    overwrite a field that already has something in it.

    Three copies is a coincidence; five is a maintenance bug waiting to be
    found in exactly one of them. The Canada batch would have made five, so
    the frame moved here and the two new generators are rosters plus a box.

    The existing three are deliberately NOT ported. They already ran, their
    output shipped, and a refactor of a script whose only job is behind it
    buys nothing and risks a silent behaviour change in data nobody would
    re-diff. If a fourth region needs re-running, port it then.

WHAT A CALLER PROVIDES
    A `Region` describing the target file and its guards, plus `NEW` (records
    to create) and `FILL` (fields to add to records that already exist).
    Everything else — CLI, resolution, reporting, the write — is here.

THE ONE GUARD THAT IS NEW HERE
    `subregion_box`. Every previous batch could lean on the country as its
    namesake guard, because the regions were continents and a namesake was
    almost always in another country: Lagos/Lagos, Tripoli/Tripoli,
    Victoria/Victoria. Canada breaks that. Its worst collisions are entirely
    INTERNAL — Windsor (Ontario / Nova Scotia / Quebec), Victoria (BC and a
    Newfoundland outport), Sydney (Nova Scotia), Hamilton, Kingston,
    Stratford, Perth, Delta, Richmond, Chatham, Miramichi. P17 answers
    "Canada" for the right article and for the wrong one, and the country box
    contains both. So the box test is available one level down: a record that
    claims a province is checked against that province's own rectangle.

    Like P17 it is a WARNING, not a refusal — a province box is drawn by hand
    and a place legitimately sits on a border (Wood Buffalo is Alberta and the
    Northwest Territories; the Icefields Parkway ends in a national park that
    touches BC). Print it, read it, don't automate it.
"""
import argparse
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_wiki import Resolver, haversine

ROOT = Path(__file__).resolve().parent.parent

# How far a record may sit from its own article's P625 before a human should
# look. An `area` type legitimately sits far from its centroid: a park's
# article points at the middle of the park, a river's at one arbitrary bend.
FAR_KM = 60.0
AREA_TYPES = {"nature", "desert", "island", "mountain", "coastal", "wilderness"}


class Region:
    """Everything a generator knows that this module does not.

    target        data/<file>.json to read and write
    continent     the `continent` field every record gets
    country_code  country name -> ISO alpha-2. The NAME is a join key:
                  `build_countries.py` counts places by matching it against
                  the registry's canonical spelling, so copy it, never retype
    country_slug  country name -> article title, where they differ
    expect_p17    country name -> the sovereign whose QID we accept instead
    in_box        (lat, lng) -> bool. The coarse net; the hard refusal
    subregion_box region name -> (lat_min, lat_max, lng_min, lng_max), the
                  warning-level namesake guard described in the docstring
    """

    def __init__(self, target, continent, country_code, in_box,
                 country_slug=None, expect_p17=None, subregion_box=None,
                 far_km=FAR_KM, subregion_key="region"):
        self.target = ROOT / "data" / target
        self.continent = continent
        self.country_code = country_code
        self.in_box = in_box
        self.country_slug_map = country_slug or {}
        self.expect_p17 = expect_p17 or {}
        self.subregion_box = subregion_box or {}
        self.far_km = far_km
        self.subregion_key = subregion_key

    def slug_for_country(self, name):
        return self.country_slug_map.get(name, name.replace(" ", "_"))


def flag(code):
    """ISO alpha-2 -> flag emoji, the same derivation build_countries.py uses."""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


class Notes:
    """One line per verdict, so a dry run reads like verify_wiki."""

    ORDER = {"UNRESOLVED": 0, "NOCOORD": 1, "OUTSIDE": 2, "COUNTRY": 3,
             "PROVINCE": 4, "MISSING": 5, "SELF": 6, "FAR": 7, "REDIRECT": 8,
             "FIXENC": 9, "TERRITORY": 10}

    def __init__(self):
        self.rows = []
        self.unresolved = 0

    def add(self, kind, where, what, why=""):
        self.rows.append((kind, where, what, why))
        if kind == "UNRESOLVED":
            self.unresolved += 1

    def print(self):
        for kind, where, what, why in sorted(
                self.rows, key=lambda r: (self.ORDER.get(r[0], 99), r[1], r[2])):
            print(f"{kind:<11} {where:<28} {what:<46} {why}")
        counts = {}
        for kind, *_ in self.rows:
            counts[kind] = counts.get(kind, 0) + 1
        if counts:
            print("\n" + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))


def link(slug, got, notes, where, own=None):
    """The canonical title to store for `slug`, or None to keep the chip text-only.

    A highlight that resolves to the record's own article is worse than a dead
    link — it promises a second place and delivers the one you are standing in.
    """
    e = got.get(slug) or {}
    if "title" not in e and not e.get("missing"):
        notes.add("UNRESOLVED", where, slug, "no answer from the API — rerun")
        return None
    if e.get("missing"):
        notes.add("MISSING", where, slug, "no article — kept as a text chip")
        return None
    title = e["title"]
    if own and title == own:
        notes.add("SELF", where, slug, "resolves to the place itself — unlinked")
        return None
    if e.get("redirect"):
        notes.add("REDIRECT", where, slug, f"-> {title}")
    return title


def highlights(spec, got, notes, where, own):
    out = []
    for name, slug in spec.get("highlights", []):
        h = {"name": name}
        t = link(slug, got, notes, where, own) if slug else None
        if t:
            h["wikipedia_slug"] = t
        out.append(h)
    return out


def far_check(region, loc, hl, got, notes, where):
    """Every highlight with a coordinate, measured against the record itself."""
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
        if d > region.far_km:
            notes.add("FAR", where, f"{h['name']} [{s}]",
                      f"{d:,.0f} km from {loc['name']}")


def country_check(region, pid, spec, e, got, notes):
    """P17 against the country the record claims. A WARNING, never a refusal.

    A territory legitimately answers its sovereign state here, and a lake or a
    range routinely names a neighbour. When the surprise is exactly the one we
    expect, say so quietly as TERRITORY so the COUNTRY lines left over are the
    ones worth reading.
    """
    name = spec["country"]
    want = got.get(region.slug_for_country(name)) or {}
    mine, theirs = e.get("country_qid"), want.get("qid")
    if not theirs:
        notes.add("COUNTRY", pid, name,
                  "no QID for the country article — check by hand")
        return
    if not mine:
        notes.add("COUNTRY", pid, e.get("title", spec["slug"]),
                  "article has no P17 — check by hand")
        return
    if mine == theirs:
        return
    sovereign = region.expect_p17.get(name)
    if sovereign:
        sov_qid = (got.get(sovereign) or {}).get("qid")
        if sov_qid and mine == sov_qid:
            notes.add("TERRITORY", pid, e.get("title", spec["slug"]),
                      f"P17 is {sovereign} — expected for {name}")
            return
    notes.add("COUNTRY", pid, e.get("title", spec["slug"]),
              f"P17 is {mine}, {name} is {theirs} — check by hand")


def subregion_check(region, pid, spec, lat, lng, notes):
    """The coordinate against the province/state the record claims.

    The guard the continental batches never needed — see the module docstring.
    A warning, because these boxes are hand-drawn and real places sit on real
    borders.
    """
    box = region.subregion_box.get(spec.get("region"))
    if not box:
        return
    lat_min, lat_max, lng_min, lng_max = box
    if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
        return
    notes.add("PROVINCE", pid, spec["slug"],
              f"P625 {lat:.3f},{lng:.3f} is outside {spec['region']} — "
              f"namesake, or a place on the border")


def make(region, pid, spec, got, notes):
    """A complete record from a NEW entry, or None if it cannot be trusted."""
    title = link(spec["slug"], got, notes, pid)
    if not title:
        notes.add("NOCOORD", pid, spec["slug"], "no article — place not added")
        return None
    e = got[spec["slug"]]
    lat, lng = e.get("lat"), e.get("lng")
    if lat is None:
        notes.add("NOCOORD", pid, title, "no P625 — place not added")
        return None
    if not region.in_box(lat, lng):
        notes.add("OUTSIDE", pid, title,
                  f"P625 is {lat:.3f},{lng:.3f} — outside the region")
        return None
    country_check(region, pid, spec, e, got, notes)
    subregion_check(region, pid, spec, lat, lng, notes)

    code = region.country_code[spec["country"]]
    loc = {
        "id": pid,
        "name": spec["name"],
        "country": spec["country"],
        "country_code": code,
        "country_flag": flag(code),
        "continent": region.continent,
        region.subregion_key: spec["region"],
        "type": spec["type"],
        "tag": spec["tag"],
        "emoji": spec["emoji"],
        "coordinates": {"lat": lat, "lng": lng},
        "street_view": {"lat": lat, "lng": lng,
                        "heading": 0, "pitch": 0, "fov": 90},
        "wikipedia_slug": title,
        "sounds": list(spec["sounds"]),
        "highlights": highlights(spec, got, notes, pid, title),
        "blurb": spec["blurb"],
        "fun_fact": spec["fact"],
        "hidden_gem_tip": spec["tip"],
    }
    # `search_name` sharpens the media/monument query when the bare name has a
    # namesake somewhere else. No downstream title guard can catch a namesake,
    # so it has to be said here, at the only point where we know.
    if spec.get("search_name"):
        loc["search_name"] = spec["search_name"]
    if spec.get("sets"):
        loc["sets"] = list(spec["sets"])
    far_check(region, loc, loc["highlights"], got, notes, pid)
    return loc


def fill(region, loc, spec, got, notes):
    """Fill only what is empty. Returns the field names actually written."""
    wrote = []
    key = region.subregion_key
    if spec.get("region") and not loc.get(key):
        loc[key] = spec["region"]
        wrote.append(key)
    if spec.get("highlights") and not loc.get("highlights"):
        loc["highlights"] = highlights(spec, got, notes, loc["id"],
                                       loc.get("wikipedia_slug"))
        far_check(region, loc, loc["highlights"], got, notes, loc["id"])
        wrote.append("highlights")
    for k, src in (("blurb", "blurb"), ("fun_fact", "fact"),
                   ("hidden_gem_tip", "tip"), ("search_name", "search_name"),
                   ("emoji", "emoji")):
        if spec.get(src) and not loc.get(k):
            loc[k] = spec[src]
            wrote.append(k)
    return wrote


def fix_encoding(locs, notes):
    """`Maracan%C3%A3_Stadium` is a URL, not a title.

    MediaWiki decodes a percent-encoded slug and answers anyway, so an audit
    never sees it — but every consumer that concatenates it into a URL is one
    encode away from a 404. Decode it back to the title it always was.
    """
    n = 0
    for loc in locs:
        for holder in [loc] + list(loc.get("highlights") or []):
            s = holder.get("wikipedia_slug")
            if s and "%" in s:
                dec = urllib.parse.unquote(s)
                if dec != s:
                    holder["wikipedia_slug"] = dec
                    notes.add("FIXENC", loc["id"], s, f"-> {dec}")
                    n += 1
    return n


def slugs_wanted(region, NEW, FILL, extra_slugs=None):
    """Every slug this batch needs an answer about, place-level and highlight.

    `extra_slugs` is for a batch whose `extra` callable touches slugs that
    appear in neither NEW nor FILL — a repair of a record this generator did
    not author. Those slugs still have to be resolved live, or the repair
    would store a title nobody checked.
    """
    out = list(extra_slugs or [])
    for spec in NEW.values():
        out.append(spec["slug"])
        out.append(region.slug_for_country(spec["country"]))
        out += [s for _, s in spec["highlights"] if s]
    for spec in FILL.values():
        out += [s for _, s in spec.get("highlights", []) if s]
    # The sovereigns named in expect_p17 are QIDs we have to *compare* against,
    # so they get resolved live too rather than typed from memory.
    out += list(region.expect_p17.values())
    return out


def run(region, NEW, FILL, extra=None, migrate=None, argv=None,
        extra_slugs=None):
    """The CLI every generator shares.

    extra        optional callable(locs, got, notes) run over the final list,
                 for a batch that also has to repair records it did not author
    migrate      optional callable(locs, notes) run over the EXISTING list
                 before anything else, for a field rename
    extra_slugs  slugs `extra` will need resolved, since they are in neither
                 NEW nor FILL
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="ignore the slug cache and ask Wikipedia again")
    ap.add_argument("--only", help="comma-separated ids from NEW/FILL, so "
                                   "adding one place doesn't re-resolve 900 slugs")
    args = ap.parse_args(argv)

    doc = json.loads(region.target.read_text(encoding="utf-8"))
    locs = doc["locations"]
    by_id = {l["id"]: l for l in locs}

    if args.only:
        keep = set(args.only.split(","))
        NEW = {k: v for k, v in NEW.items() if k in keep}
        FILL = {k: v for k, v in FILL.items() if k in keep}
        unknown = keep - set(NEW) - set(FILL)
        if unknown:
            sys.exit(f"--only names ids that are in neither NEW nor FILL: "
                     f"{sorted(unknown)}")

    missing = [p for p in FILL if p not in by_id]
    if missing:
        sys.exit(f"FILL names places that are not in the file: {missing}")
    clash = [p for p in NEW if p in by_id]
    if clash:
        sys.exit(f"NEW would collide with existing ids: {clash}")
    nocode = sorted({s["country"] for s in NEW.values()} - set(region.country_code))
    if nocode:
        sys.exit(f"NEW names countries with no ISO code here: {nocode}")

    want = slugs_wanted(region, NEW, FILL, extra_slugs)
    print(f"resolving {len(set(want))} slug(s) against Wikipedia/Wikidata …")
    got = Resolver(refresh=args.refresh).resolve(want)

    notes = Notes()
    if migrate:
        migrate(locs, notes)
    added, filled = [], []
    for pid, spec in NEW.items():
        loc = make(region, pid, spec, got, notes)
        if loc:
            added.append(loc)
    for pid, spec in FILL.items():
        wrote = fill(region, by_id[pid], spec, got, notes)
        if wrote:
            filled.append((pid, wrote))
    if extra:
        extra(locs + added, got, notes)
    enc = fix_encoding(locs + added, notes)

    notes.print()
    print(f"\n{len(added)}/{len(NEW)} new place(s), {len(filled)} filled, "
          f"{enc} slug(s) decoded")
    for pid, wrote in filled:
        print(f"  fill {pid:<28} {', '.join(wrote)}")
    skipped = [p for p in NEW if p not in {l['id'] for l in added}]
    if skipped:
        print(f"  ⚠ not added: {skipped}")
    have = {}
    for l in locs + added:
        have[l["country"]] = have.get(l["country"], 0) + 1
    print(f"  {len(locs) + len(added)} place(s) in the file after this run, "
          f"{len(have)} country/countries: "
          + ", ".join(f"{k} {v}" for k, v in sorted(have.items())))

    if notes.unresolved:
        # A throttled request is not a verdict. Refuse to write a half-checked
        # file rather than silently drop links the API never answered about.
        sys.exit(f"\n{notes.unresolved} slug(s) unresolved — rerun before --apply")
    if not args.apply:
        print("\ndry run — pass --apply to write")
        return

    doc["locations"] = locs + added
    region.target.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    print(f"✓ wrote {len(doc['locations'])} locations -> "
          f"{region.target.relative_to(ROOT)}")
