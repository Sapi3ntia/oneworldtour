#!/usr/bin/env python3
"""
verify_wiki.py — the slug + coordinate audit that every batch has run by hand.

WHY THIS EXISTS
    The rules in README "Filling a region out" are all checkable, and every
    one of them was checked with a throwaway script that then got thrown away:

      • a `wikipedia_slug` that is a REDIRECT returns no `pageimages` thumbnail,
        so `arrivalPhoto()` degrades to the emoji without complaining
      • a slug that resolves to NOTHING is a dead chip
      • a highlight that redirects to the record's OWN subject is a chip that
        reopens the page you are already on (Gardens by the Bay's "Flower Dome")
      • a highlight can keep its name and cross a border ("Santa Elena Canyon"
        → the Mexican reserve; "El Paso del Norte" → Ciudad Juárez)
      • and the only thing that ever catches the last one is COORDINATES:
        `Paradise_Cave` is in Poland, 8,204 km from Phong Nha, and the video
        title was right the whole time.

    Wikidata P625 answers all of it, so this asks it once and keeps the answer.

WHAT IT REPORTS (it never edits anything)
    MISSING     no article under that title
    REDIRECT    resolves elsewhere — store the canonical title instead
    SELF        a highlight that resolves to the place's own article
    DUP         two highlights on one place resolving to the same article
    NOCOORD     no P625 (fine for a museum-less concept, suspicious for a site)
    FAR         P625 is far from where the record says the place is

    Distance is measured, not argued about. A long FAR list is not a bug list:
    the P625 of a river or a range is one arbitrary point along it, and an
    island inside an archipelago is genuinely 80 km from its centre. Read them.

Usage:
  python3 tools/verify_wiki.py                       # the whole corpus
  python3 tools/verify_wiki.py --file data/latinamerica.json
  python3 tools/verify_wiki.py --only quito,cuenca
  python3 tools/verify_wiki.py --slugs 'Quito|Cuenca,_Ecuador'   # ad-hoc
  python3 tools/verify_wiki.py --far 120             # loosen the distance bar
"""
import argparse
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(__file__).resolve().parent / ".wiki_slugs.json"
UA = "OneWorldTour/2.0 (educational virtual-travel project; contact: local)"
WP = "https://en.wikipedia.org/w/api.php"
WD = "https://www.wikidata.org/w/api.php"

SKIP_FILES = {"index.json", "countries.json", "windy.json", "media.json",
              "tv.json", "trips.json", "media_denylist.json"}

# A place whose article is an area rather than a point is expected to sit far
# from its own P625 — the entry is about one town in it, or one trailhead.
# These are the record `type`s where a big distance is information, not alarm.
AREA_TYPES = {"nature", "desert", "island", "mountain", "region"}


# Wikimedia rate-limits anonymous callers hard, and it answers 429 rather than
# lying — so a 429 that we shrug off would show up as "MISSING", i.e. as a
# report that a real article does not exist. That is the throttled-yt-dlp
# lesson from TODO.md in a second API: never read a refusal as a verdict.
_LAST = [0.0]
GAP = 1.1                                            # seconds between requests


def api(url, params):
    extra = {}
    if url != WD:
        # `maxlag` is the polite way to back off a lagging cluster, but on
        # Wikidata it also reports the QUERY SERVICE's lag, which sits in the
        # hundreds of seconds as a matter of course — so every wbgetentities
        # call answers `maxlag` forever and no coordinate ever arrives.
        extra["maxlag"] = "5"
    q = urllib.parse.urlencode({**params, "format": "json",
                                "formatversion": "2", **extra})
    req = urllib.request.Request(f"{url}?{q}", headers={"User-Agent": UA})
    for attempt in range(5):
        wait = GAP - (time.time() - _LAST[0])
        if wait > 0:
            time.sleep(wait)
        _LAST[0] = time.time()
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            if d.get("error", {}).get("code") == "maxlag":
                time.sleep(5)
                continue
            return d
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(20 * (attempt + 1))
                continue
            print(f"  ! {e}", file=sys.stderr)
            return {}
        except Exception as e:                       # noqa: BLE001 — retry anything
            if attempt == 4:
                print(f"  ! {e}", file=sys.stderr)
                return {}
            time.sleep(3 * (attempt + 1))
    print("  ! gave up after 5 tries — rerun, the cache keeps what landed",
          file=sys.stderr)
    return {}


def haversine(a, b):
    """km between two (lat, lng) pairs."""
    r = 6371.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = p2 - p1
    dl = math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


class Resolver:
    """slug -> {title, redirect, missing, qid, lat, lng}, cached on disk.

    Batched 40 titles at a time because the audit asks about ~2,600 slugs and
    the polite thing is 70 requests rather than 2,600.
    """

    def __init__(self, refresh=False):
        self.cache = {}
        if CACHE.exists() and not refresh:
            self.cache = json.loads(CACHE.read_text(encoding="utf-8"))
        self.dirty = False

    def save(self):
        if self.dirty:
            CACHE.write_text(json.dumps(self.cache, ensure_ascii=False, indent=1),
                             encoding="utf-8")
            self.dirty = False

    def resolve(self, slugs):
        want = [s for s in dict.fromkeys(slugs) if s and s not in self.cache]
        for i in range(0, len(want), 40):
            chunk = want[i:i + 40]
            self._fetch_titles(chunk)
            self.save()
        # second pass: the P625 (and P17) of everything that got a wikidata item.
        # `country_qid` is checked separately from `lat` so entries cached
        # before P17 was extracted get topped up on their next resolve rather
        # than reporting a country of None forever — a stale cache that answers
        # confidently is the `Cairo_Citadel` failure again.
        need = [s for s in dict.fromkeys(slugs)
                if s in self.cache and self.cache[s].get("qid")
                and ("lat" not in self.cache[s]
                     or "country_qid" not in self.cache[s])]
        qids = list(dict.fromkeys(self.cache[s]["qid"] for s in need))
        for i in range(0, len(qids), 40):
            self._fetch_coords(qids[i:i + 40], need)
            self.save()
        return {s: self.cache.get(s, {"missing": True}) for s in slugs}

    def _fetch_titles(self, titles):
        d = api(WP, {"action": "query", "prop": "pageprops",
                     "ppprop": "wikibase_item", "redirects": "1",
                     "titles": "|".join(t.replace("_", " ") for t in titles)})
        q = d.get("query")
        if not q:
            # The request failed, which is not the same as "these articles do
            # not exist". Cache nothing; a rerun asks again.
            print(f"  ! no answer for {len(titles)} title(s) — left unresolved",
                  file=sys.stderr)
            return

        # the API answers about CANONICAL titles, so walk normalization and
        # redirects back to the string we actually asked about
        back = {}
        for n in q.get("normalized") or []:
            back[n["to"]] = n["from"]
        chain = {}
        for r in q.get("redirects") or []:
            chain[r["to"]] = r["from"]

        def asked(title):
            src = chain.get(title, title)
            return back.get(src, src)

        seen = set()
        for p in q.get("pages") or []:
            title = p.get("title")
            src = asked(title)
            missing = bool(p.get("missing"))
            qid = ((p.get("pageprops") or {}).get("wikibase_item"))

            def put(k, redirect):
                entry = {"title": title.replace(" ", "_"),
                         "redirect": redirect, "missing": missing}
                if qid:
                    entry["qid"] = qid
                self.cache[k] = entry
                seen.add(k)
                self.dirty = True

            # the title we asked about, flagged if it wasn't the canonical one
            for k in (src.replace(" ", "_"), src):
                put(k, title in chain)

            # ...and the canonical title under its OWN key, which by definition
            # is not a redirect. Without this, asking about a redirect AND its
            # target in one chunk reported the target as MISSING: the API
            # answers once, in canonical form, and asked() attributes that lone
            # answer to the redirect, so the canonical string never lands in
            # `seen` and falls through to the not-in-seen branch below. That is
            # how `Cairo_Citadel` — a real article, with a thumbnail — verified
            # as "no article", purely because something else in the same batch
            # of 40 linked to `Citadel_of_Cairo`. The verdict then persisted in
            # .wiki_slugs.json, which nothing but --refresh ever clears.
            if not missing:
                for k in (title.replace(" ", "_"), title):
                    if k not in seen:
                        put(k, False)
        for t in titles:                              # nothing came back at all
            if t not in seen and t.replace("_", " ") not in seen:
                self.cache[t] = {"title": t, "missing": True, "redirect": False}
                self.dirty = True

    def _fetch_coords(self, qids, slugs):
        d = api(WD, {"action": "wbgetentities", "ids": "|".join(qids),
                     "props": "claims"})
        ents = d.get("entities") or {}
        for s in slugs:
            qid = self.cache[s].get("qid")
            e = ents.get(qid)
            if not e:
                continue
            claims = (e.get("claims") or {}).get("P625") or []
            val = None
            for c in claims:
                v = ((c.get("mainsnak") or {}).get("datavalue") or {}).get("value")
                if v and "latitude" in v:
                    val = v
                    if c.get("rank") == "preferred":
                        break
            self.cache[s]["lat"] = val["latitude"] if val else None
            self.cache[s]["lng"] = val["longitude"] if val else None

            # P17 (country) — a stronger namesake guard than any bounding box.
            # A box says "somewhere on this continent", which is exactly the
            # question a namesake is best at slipping past: Lagos, Portugal is
            # at 37.1N -8.7E, INSIDE any box drawn around Africa, and would
            # have passed. The country claim answers the question the record
            # actually makes — "this is the Lagos in Nigeria" — and it is one
            # field away in a response we were already asking for.
            p17 = (e.get("claims") or {}).get("P17") or []
            cq = None
            for c in p17:
                v = ((c.get("mainsnak") or {}).get("datavalue") or {}).get("value")
                if isinstance(v, dict) and v.get("id"):
                    cq = v["id"]
                    if c.get("rank") == "preferred":
                        break
            self.cache[s]["country_qid"] = cq
            self.dirty = True


def slug_of(h):
    return (h.get("wikipedia_slug") if isinstance(h, dict) else None) or ""


def load_places(args):
    out = []
    only = set(args.only.split(",")) if args.only else None
    files = [ROOT / args.file] if args.file else sorted((ROOT / "data").glob("*.json"))
    for f in files:
        if f.name in SKIP_FILES:
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(d, dict) or "locations" not in d:
            continue
        for loc in d["locations"]:
            if only and loc.get("id") not in only:
                continue
            out.append((f.name, loc))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="one region file")
    ap.add_argument("--only", help="comma-separated place ids")
    ap.add_argument("--slugs", help="ad-hoc: PIPE-separated slugs (half of "
                                    "them contain a comma), resolved and printed")
    ap.add_argument("--far", type=float, default=75.0, help="km before FAR")
    ap.add_argument("--refresh", action="store_true", help="ignore the cache")
    ap.add_argument("--quiet", action="store_true", help="findings only")
    args = ap.parse_args()
    r = Resolver(refresh=args.refresh)

    if args.slugs:
        slugs = [s.strip() for s in args.slugs.split("|") if s.strip()]
        got = r.resolve(slugs)
        for s in slugs:
            e = got[s]
            where = (f"{e.get('lat'):.5f},{e.get('lng'):.5f}"
                     if e.get("lat") is not None else
                     "no P625" if "lat" in e else "unresolved")
            state = ("MISSING" if e.get("missing") else
                     f"redirect → {e['title']}" if e.get("redirect") else "ok")
            print(f"{s:<44} {state:<34} {where}  {e.get('qid') or ''}")
        r.save()
        return

    places = load_places(args)
    slugs = []
    for _, loc in places:
        if loc.get("wikipedia_slug"):
            slugs.append(loc["wikipedia_slug"])
        for h in loc.get("highlights") or []:
            if slug_of(h):
                slugs.append(slug_of(h))
    print(f"{len(places)} place(s), {len(set(slugs))} distinct slug(s)")
    got = r.resolve(slugs)
    r.save()

    findings, checked = [], 0
    for fname, loc in places:
        pid, pname = loc.get("id"), loc.get("name")
        own = loc.get("wikipedia_slug") or ""
        e = got.get(own) or {}
        coords = loc.get("coordinates") or {}
        here = (coords.get("lat"), coords.get("lng"))

        def add(kind, what, detail):
            findings.append((kind, fname, pid, pname, what, detail))

        if own:
            checked += 1
            if e.get("missing"):
                add("MISSING", own, "no article")
            elif e.get("redirect"):
                add("REDIRECT", own, f"→ {e['title']}")
            elif e.get("lat") is None:
                add("NOCOORD", own, "no P625")
            elif here[0] is not None:
                km = haversine(here, (e["lat"], e["lng"]))
                if km > args.far:
                    note = " (area type)" if loc.get("type") in AREA_TYPES else ""
                    add("FAR", own, f"{km:,.0f} km from the record{note}")

        canon = (e.get("title") or own).lower()
        seen = {}
        for h in loc.get("highlights") or []:
            s = slug_of(h)
            if not s:
                continue
            checked += 1
            he = got.get(s) or {}
            name = h.get("name") if isinstance(h, dict) else h
            if he.get("missing"):
                add("MISSING", f"{name} [{s}]", "no article")
                continue
            title = he.get("title") or s
            if title.lower() == canon:
                add("SELF", f"{name} [{s}]", "resolves to the place itself")
                continue
            if he.get("redirect"):
                add("REDIRECT", f"{name} [{s}]", f"→ {title}")
            if title.lower() in seen:
                add("DUP", f"{name} [{s}]", f"same article as {seen[title.lower()]}")
            seen[title.lower()] = name
            if he.get("lat") is None:
                add("NOCOORD", f"{name} [{s}]", "no P625")
            elif here[0] is not None:
                km = haversine(here, (he["lat"], he["lng"]))
                if km > args.far:
                    add("FAR", f"{name} [{s}]", f"{km:,.0f} km from {pname}")

    order = {"MISSING": 0, "SELF": 1, "REDIRECT": 2, "DUP": 3, "FAR": 4, "NOCOORD": 5}
    findings.sort(key=lambda x: (order.get(x[0], 9), x[1], x[2]))
    for kind, fname, pid, pname, what, detail in findings:
        if args.quiet and kind == "NOCOORD":
            continue
        print(f"{kind:<8} {pid:<26} {what:<52} {detail}")

    counts = {}
    for f in findings:
        counts[f[0]] = counts.get(f[0], 0) + 1
    print(f"\n{checked} slug(s) checked — " +
          (", ".join(f"{v} {k}" for k, v in sorted(counts.items())) or "all clean"))


if __name__ == "__main__":
    main()
