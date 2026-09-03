#!/usr/bin/env python3
"""
openwebcamdb.py — a metered, build-time client for the OpenWebcamDB API.

WHAT THIS IS FOR (and what it is deliberately not)
    OpenWebcamDB catalogues ~1,500 webcams. We use it as a **lead generator at
    build time**: it tells a human where cameras exist, and for the small slice
    of its catalogue that is YouTube-backed it hands over ids that our existing
    `enrich_media.py` vetting can verify for real. Nothing this tool fetches is
    ever written into `data/` and nothing is ever displayed on a page.

    That is not squeamishness, it is arithmetic and it is the honesty rule.

    THE ARITHMETIC. The free tier allows **25 requests per rolling 24 h** (and
    5 per minute) — confirmed from live response headers, not from the docs:

        x-ratelimit-limit: 25          x-ratelimit-window: 24h-sliding
        x-ratelimit-limit-minute: 5

    25 requests / 24 h is **one request every 57.6 minutes**, sustained. The
    free tier also caps caching at 1 hour. So a runtime integration — the site
    calling the API and refreshing at the cache cap — costs 24 requests a day
    for ONE query shape serving ALL visitors, i.e. 96% of the entire daily
    budget before a second query, a cache miss, a preview deploy or a retry.
    There is no configuration of a live integration that fits. Any claim that
    "we stay in limit" would be false the first time two query shapes existed.
    Build-time only is the only version of this that is mathematically safe.

    THE HONESTY RULE. A 🔴 or 🪟 seat requires a stream we have verified is
    live and embeddable (README, "the scene either embeds the real thing or the
    place doesn't offer that tab"). 89 of the 124 Russian cams here are
    third-party `iframe` embeds (Ivideon and friends) and **the schema has no
    `is_live` field at all**, so there is nothing to verify against; `city` is
    null on 102 of 124; and the catalogue skews to car washes, pizzeria
    kitchens, auto-repair yards and laundries. The 11 `stream_type: "youtube"`
    cams are the exception — those are YouTube ids, and yt-dlp can tell us the
    truth about them. That slice is the whole reason this file exists.

HOW THE RULES ARE ENFORCED IN CODE, NOT IN A COMMENT
    Attribution — "Powered by OpenWebcamDB.com" is printed on every run. The
        free tier requires a visible link on *pages displaying API data*; no
        page displays any, because none of it reaches `data/`. If that ever
        changes, the link becomes mandatory: see README.
    Caching ≤ 1 h — `CACHE_TTL_S = 3600`, and expiry **deletes** the file
        rather than serving it stale. Every run also sweeps the cache dir
        first, so a response older than an hour does not exist on disk even
        if this tool is never asked for it again.
    Rate limits — a persistent ledger (`tools/.owdb_budget.json`) records the
        timestamp of every request ever made and refuses to exceed
        DAY_LIMIT - DAY_RESERVE in any rolling 24 h, and MINUTE_LIMIT per
        minute. It refuses rather than 429s: a rejected request still costs
        the provider work, and being rate-limited is the thing we promised not
        to do. After every call the ledger is reconciled against the server's
        own `x-ratelimit-remaining`, and the server always wins.
    Image fair use — thumbnails are never downloaded, only their URLs printed.

THE KEY
    Never in the browser, never in git. Read from `$OPENWEBCAMDB_KEY` or from
    `tools/openwebcamdb.key` (gitignored, same pattern as `tools/windy.key`).

Usage:
  python3 tools/openwebcamdb.py --status                 # free, no request
  python3 tools/openwebcamdb.py --list RU                # 1 request (cached 1 h)
  python3 tools/openwebcamdb.py --youtube RU             # the vettable slice
  python3 tools/openwebcamdb.py --cam <slug>             # 1 request, stream_url
  python3 tools/openwebcamdb.py --gaps RU --km 60        # cams far from our map
  python3 tools/openwebcamdb.py --list RU --dry-run      # cost, spend nothing
  python3 tools/openwebcamdb.py --purge-cache
"""
import argparse
import glob
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
KEYF = HERE / "openwebcamdb.key"
LEDGER = HERE / ".owdb_budget.json"
CACHE = HERE / ".owdb_cache"
BASE = "https://openwebcamdb.com/api/v1"

# From the live headers, not the docs. Both windows are enforced.
DAY_LIMIT = 25          # x-ratelimit-limit, 24h-sliding
MINUTE_LIMIT = 5        # x-ratelimit-limit-minute
DAY_RESERVE = 3         # never spend the last few — leaves room for a human
CACHE_TTL_S = 3600      # free tier: cache for at most 1 hour. Hard.
DAY_S = 24 * 3600

ATTRIBUTION = "Powered by OpenWebcamDB.com — https://openwebcamdb.com"


# ---------------------------------------------------------------------------
# THE BUDGET LEDGER
# ---------------------------------------------------------------------------
class Budget:
    """Every request this machine has ever made, and what the server thinks.

    The ledger is the reason we can say "we stay in limit" and mean it. It
    survives across runs, across days and across branches, because the limit
    it is tracking does too.
    """

    def __init__(self):
        self.calls = []
        self.server = {}
        if LEDGER.exists():
            try:
                d = json.loads(LEDGER.read_text(encoding="utf-8"))
                self.calls = list(d.get("calls") or [])
                self.server = dict(d.get("server") or {})
            except (ValueError, OSError):
                pass                       # a corrupt ledger reads as "spent 0"
        self._prune()

    def _prune(self):
        cut = time.time() - DAY_S
        self.calls = [t for t in self.calls if t > cut]

    def save(self):
        LEDGER.write_text(json.dumps(
            {"_comment": "openwebcamdb.py rate-limit ledger — gitignored, "
                         "delete only if you want to lie to yourself",
             "calls": self.calls, "server": self.server},
            indent=1), encoding="utf-8")

    # -- what we believe we have left -------------------------------------
    def spent_day(self):
        self._prune()
        return len(self.calls)

    def spent_minute(self):
        cut = time.time() - 60
        return len([t for t in self.calls if t > cut])

    def remaining(self):
        """The conservative answer: the smaller of our count and the server's."""
        ours = DAY_LIMIT - DAY_RESERVE - self.spent_day()
        srv = self.server.get("remaining")
        at = self.server.get("at", 0)
        if srv is not None and time.time() - at < DAY_S:
            ours = min(ours, srv - DAY_RESERVE)
        return ours

    def next_free_at(self):
        """When the oldest call in the window ages out — i.e. when we can spend."""
        if not self.calls:
            return time.time()
        return min(self.calls) + DAY_S

    # -- spending ----------------------------------------------------------
    def check(self, cost=1):
        """Raise unless `cost` requests fit inside every window we know about."""
        if self.remaining() < cost:
            wait = self.next_free_at() - time.time()
            raise Budget.Exhausted(
                f"daily budget: {self.spent_day()}/{DAY_LIMIT} spent in the last "
                f"24 h, {max(self.remaining(), 0)} spendable (reserve "
                f"{DAY_RESERVE}). Next slot frees in "
                f"{wait / 3600:.1f} h.")

    def wait_for_minute(self):
        """Block, briefly, rather than trip the 5/minute limit."""
        while self.spent_minute() >= MINUTE_LIMIT:
            oldest = min(t for t in self.calls if t > time.time() - 60)
            nap = max(1.0, oldest + 60 - time.time() + 0.5)
            print(f"  · minute limit reached — waiting {nap:.0f}s", flush=True)
            time.sleep(nap)

    def record(self, headers):
        self.calls.append(time.time())
        rem = headers.get("x-ratelimit-remaining")
        if rem is not None:
            try:
                self.server = {"remaining": int(rem), "at": time.time(),
                               "limit": int(headers.get("x-ratelimit-limit",
                                                        DAY_LIMIT))}
            except ValueError:
                pass
        self.save()

    class Exhausted(RuntimeError):
        pass


# ---------------------------------------------------------------------------
# THE CACHE — one hour, and expiry means deletion
# ---------------------------------------------------------------------------
def sweep_cache():
    """Delete anything older than the licence allows. Runs on every invocation."""
    gone = 0
    for f in glob.glob(str(CACHE / "*.json")):
        try:
            if time.time() - os.path.getmtime(f) > CACHE_TTL_S:
                os.remove(f)
                gone += 1
        except OSError:
            pass
    return gone


def cache_path(url):
    return CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".json")


def cache_get(url):
    p = cache_path(url)
    if not p.exists():
        return None
    age = time.time() - p.stat().st_mtime
    if age > CACHE_TTL_S:
        p.unlink(missing_ok=True)          # stale is deleted, never served
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8")), age
    except (ValueError, OSError):
        p.unlink(missing_ok=True)
        return None


def cache_put(url, body):
    CACHE.mkdir(exist_ok=True)
    cache_path(url).write_text(json.dumps(body), encoding="utf-8")


# ---------------------------------------------------------------------------
# THE CLIENT
# ---------------------------------------------------------------------------
def api_key():
    k = os.environ.get("OPENWEBCAMDB_KEY", "").strip()
    if k:
        return k
    if KEYF.exists():
        return KEYF.read_text(encoding="utf-8").strip()
    sys.exit(f"no API key — put it in {KEYF.relative_to(ROOT)} (gitignored) "
             f"or export OPENWEBCAMDB_KEY")


def get(path, params=None, budget=None, dry=False):
    """One metered GET. Returns (body, source) where source is 'cache' or 'api'."""
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)

    hit = cache_get(url)
    if hit:
        body, age = hit
        print(f"  · cache hit ({age / 60:.0f} min old, expires at 60) — 0 requests")
        return body, "cache"

    if dry:
        print(f"  · would cost 1 request: {url}")
        return None, "dry"

    budget.check(1)
    budget.wait_for_minute()
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + api_key(),
        "Accept": "application/json",
        "User-Agent": "atlas/1.0 (build-time lead generation)",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            headers = {k.lower(): v for k, v in r.headers.items()}
            body = json.loads(r.read())
    except urllib.error.HTTPError as e:
        # A 429 means the ledger was wrong. Believe the server, then stop.
        if e.code == 429:
            budget.server = {"remaining": 0, "at": time.time(),
                             "limit": DAY_LIMIT}
            budget.calls.append(time.time())
            budget.save()
            sys.exit("429 from the API — the ledger has been corrected to 0 "
                     "remaining. Nothing else will be requested.")
        sys.exit(f"HTTP {e.code} for {url}: {e.read()[:300]!r}")

    budget.record(headers)
    cache_put(url, body)
    left = headers.get("x-ratelimit-remaining", "?")
    print(f"  · 1 request spent — server says {left}/{DAY_LIMIT} left today")
    return body, "api"


# ---------------------------------------------------------------------------
# COMMANDS
# ---------------------------------------------------------------------------
def haversine(a, b):
    r = 6371.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def country_slug(arg):
    """Their `country=` filter takes a slugified NAME, not an ISO code.

    `country=RU` is not an error — it is a silent empty result set, which is
    the worst possible failure for a tool with 25 requests a day to spend.
    So a two-letter argument is resolved through our own country registry
    ("RU" → "Russia" → "russia") and anything else is slugified as given.
    """
    a = arg.strip()
    if len(a) == 2 and a.isalpha():
        reg = json.loads((ROOT / "data" / "countries.json")
                         .read_text(encoding="utf-8"))
        for c in reg.get("countries", []):
            if c.get("code", "").upper() == a.upper():
                a = c["name"]
                break
        else:
            sys.exit(f"{arg!r} is not a country code in data/countries.json — "
                     f"pass the name instead (e.g. russia)")
    return re.sub(r"[^a-z0-9]+", "-", a.lower()).strip("-")


def our_places():
    """Every place on our map, as (id, name, lat, lng). Read-only."""
    out = []
    idx = json.loads((ROOT / "data" / "index.json").read_text(encoding="utf-8"))
    files = {os.path.basename(r["file"]) for r in idx.get("regions", [])}
    files |= {"europe.json", "asia.json", "usa.json", "canada.json"}
    for fn in sorted(files):
        p = ROOT / "data" / fn
        if not p.exists():
            continue
        for loc in json.loads(p.read_text(encoding="utf-8")).get("locations", []):
            c = loc.get("coordinates") or {}
            if c.get("lat") is not None:
                out.append((loc["id"], loc["name"], c["lat"], c["lng"]))
    return out


def coords(cam):
    try:
        return float(cam["latitude"]), float(cam["longitude"])
    except (TypeError, ValueError, KeyError):
        return None


def show(cam, extra=""):
    ll = coords(cam)
    where = f"{ll[0]:.3f},{ll[1]:.3f}" if ll else "no coords"
    city = cam.get("city") or (cam.get("country") or {}).get("name") or "?"
    print(f"  {cam['stream_type']:<8} {cam['title'][:52]:<52} {where:<18} "
          f"{city[:16]:<16} {extra}")


def cmd_list(body, only_youtube=False):
    cams = body.get("data") or []
    meta = body.get("meta") or {}
    if only_youtube:
        cams = [c for c in cams if c.get("stream_type") == "youtube"]
    print(f"\n{len(cams)} cam(s) shown of {meta.get('total', '?')} total "
          f"(page {meta.get('current_page', '?')}/{meta.get('last_page', '?')})\n")
    for c in sorted(cams, key=lambda c: c.get("title") or ""):
        show(c, c.get("permalink", ""))
    if only_youtube:
        print("\nThese are the only ones our vetting can verify: a YouTube id "
              "can be checked for is_live + playable_in_embed with yt-dlp.\n"
              "Get one's id with:  --cam <slug>   (1 request), then hand it to\n"
              "enrich_media.py's vetting before it is allowed anywhere near a "
              "🔴 or 🪟 seat.")


def cmd_gaps(body, km):
    """Cams that are nowhere near anything we have — i.e. places worth adding."""
    cams = [c for c in (body.get("data") or []) if coords(c)]
    mine = our_places()
    far = []
    for c in cams:
        ll = coords(c)
        d, who = min(((haversine(ll, (p[2], p[3])), p[1]) for p in mine),
                     default=(9e9, "—"))
        if d > km:
            far.append((d, who, c))
    far.sort(reverse=True)
    print(f"\n{len(far)} cam(s) more than {km} km from any place on our map "
          f"— candidate towns, not candidate embeds:\n")
    for d, who, c in far:
        show(c, f"{d:,.0f} km from {who}")


def cmd_cam(body):
    c = body.get("data") or {}
    print()
    for k in ("title", "slug", "stream_type", "stream_url", "latitude",
              "longitude", "permalink"):
        print(f"  {k:<12} {c.get(k)}")
    url = c.get("stream_url") or ""
    if c.get("stream_type") == "youtube":
        vid = ""
        for pat in ("v=", "/embed/", "youtu.be/"):
            if pat in url:
                vid = url.split(pat, 1)[1].split("&")[0].split("?")[0].split("/")[0]
                break
        if vid:
            print(f"\n  YouTube id: {vid}\n"
                  f"  Verify before use:  yt-dlp -J 'https://youtu.be/{vid}' "
                  f"| python3 -c \"import json,sys; d=json.load(sys.stdin); "
                  f"print(d['live_status'], d['playable_in_embed'])\"")
    else:
        print("\n  Not a YouTube stream — there is no `is_live` field anywhere "
              "in this schema, so this can never honestly fill a 🔴 or 🪟 seat.")


def cmd_status(budget):
    srv = budget.server
    age = (time.time() - srv["at"]) / 3600 if srv.get("at") else None
    print(f"\n  ledger      {budget.spent_day()}/{DAY_LIMIT} spent in the last 24 h "
          f"({budget.spent_minute()}/{MINUTE_LIMIT} this minute)")
    print(f"  spendable   {max(budget.remaining(), 0)}  (reserve {DAY_RESERVE} "
          f"held back)")
    if srv.get("remaining") is not None:
        print(f"  server said {srv['remaining']} remaining, {age:.1f} h ago")
    if budget.calls:
        free = (budget.next_free_at() - time.time()) / 3600
        print(f"  next slot   frees in {free:.1f} h")
    n = len(glob.glob(str(CACHE / "*.json")))
    print(f"  cache       {n} live response(s), TTL {CACHE_TTL_S // 60} min\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--status", action="store_true", help="budget report, free")
    ap.add_argument("--list", metavar="COUNTRY", help="cams for a country (name or ISO code)")
    ap.add_argument("--youtube", metavar="COUNTRY",
                    help="only the YouTube-backed cams for a country")
    ap.add_argument("--gaps", metavar="COUNTRY",
                    help="cams far from anything on our map")
    ap.add_argument("--cam", metavar="SLUG", help="one cam's detail + stream_url")
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--per-page", type=int, default=100)
    ap.add_argument("--km", type=float, default=60.0, help="--gaps threshold")
    ap.add_argument("--dry-run", action="store_true",
                    help="say what it would cost, spend nothing")
    ap.add_argument("--purge-cache", action="store_true")
    args = ap.parse_args()

    swept = sweep_cache()
    if swept:
        print(f"  · swept {swept} expired cache file(s) — the 1 h cap is a "
              f"deletion, not a preference")
    if args.purge_cache:
        for f in glob.glob(str(CACHE / "*.json")):
            os.remove(f)
        print("cache purged")
        return

    budget = Budget()
    if args.status or not any((args.list, args.youtube, args.gaps, args.cam)):
        cmd_status(budget)
        print(ATTRIBUTION)
        return

    try:
        if args.cam:
            body, _ = get(f"/webcams/{args.cam}", None, budget, args.dry_run)
            if body:
                cmd_cam(body)
        else:
            iso = country_slug(args.list or args.youtube or args.gaps)
            params = {"country": iso, "per_page": args.per_page,
                      "page": args.page}
            body, _ = get("/webcams", params, budget, args.dry_run)
            if body:
                if args.gaps:
                    cmd_gaps(body, args.km)
                else:
                    cmd_list(body, only_youtube=bool(args.youtube))
    except Budget.Exhausted as e:
        sys.exit(f"refusing to send: {e}")

    print("\n" + ATTRIBUTION)


if __name__ == "__main__":
    main()
