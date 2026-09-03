#!/usr/bin/env python3
"""
hlscam.py — the "live means live" test, for cams that aren't on YouTube.

enrich_media.py asks yt-dlp two questions before a cam may sit in a 🔴 or
🪟 seat: live_status == is_live, and playable_in_embed. A raw .m3u8 has no
yt-dlp to ask, so this module asks the equivalent questions directly:

  1. 200, and the body is really a playlist (#EXTM3U).
  2. Access-Control-Allow-Origin: *  — the site is static and keyless, so
     a stream the browser can't fetch cross-origin is no use to us. This
     is the HLS analogue of playable_in_embed.
  3. an m3u8 content-type.
  4. THE SEGMENT NAMES ADVANCE between two reads a few seconds apart.
     This is the whole point. A playlist that never advances is a loop,
     a still, or a dead encoder — and the owner rule says none of those
     ever stands in for a window. This is the analogue of is_live.

Only all four together earn a seat. js/lib/media.js parseCam() documents
the same contract from the front-end side; tools/verify_cams.py re-runs
it so an HLS cam rots as honestly as a YouTube one.

Usage:
  python3 tools/hlscam.py <label>=<url-or-ipcamlive-alias> [...]
"""
import re
import sys
import time
import urllib.request

UA = "Atlas/1.0 (build-time cam verification; +https://atlas-world-live.vercel.app)"
ORIGIN = "https://atlas-world-live.vercel.app"

# ipcamlive spreads cameras over many edge hosts (s134, s137, s139, ...).
# Guessing from a short list misses the long tail, so we read the address
# the player itself was handed and only fall back to these.
FALLBACK_HOSTS = ("s137", "t1", "e1", "g1", "g3")


def get(url, timeout=20):
    rq = urllib.request.Request(
        url, headers={"User-Agent": UA, "Origin": ORIGIN})
    with urllib.request.urlopen(rq, timeout=timeout) as r:
        return r.status, dict(r.headers), r.read().decode("utf8", "replace")


def ipcamlive_player(alias, referer=None):
    """(streamid, address) for an ipcamlive alias, or (None, None) if the
       camera is gone — an alias whose player page names no streamid has
       been deleted or taken offline, and is an honest gap, not a cam."""
    rq = urllib.request.Request(
        f"https://g1.ipcamlive.com/player/player.php?alias={alias}&autoplay=1",
        headers={"User-Agent": UA, **({"Referer": referer} if referer else {})})
    with urllib.request.urlopen(rq, timeout=25) as r:
        body = r.read().decode("utf8", "replace")
    sid = re.search(r"streamid\s*=\s*'([^']+)'", body)
    # \bvar\s+ matters: 'groupaddress' and 'timelapseaddress' both end in
    # "address" and both come first in the page.
    addr = re.search(r"\bvar\s+address\s*=\s*'(https?://[^']+)'", body)
    return (sid.group(1) if sid else None,
            addr.group(1).rstrip("/").replace("http://", "https://") if addr else None)


def ipcamlive_m3u8(alias, referer=None):
    """Resolve an ipcamlive alias to a playable .m3u8, or None."""
    sid, addr = ipcamlive_player(alias, referer)
    if not sid:
        return None
    hosts = ([addr] if addr else []) + [
        f"https://{h}.ipcamlive.com" for h in FALLBACK_HOSTS]
    for base in hosts:
        url = f"{base}/streams/{sid}/stream.m3u8"
        try:
            status, _, body = get(url)
            if status == 200 and "#EXTM3U" in body:
                return url
        except Exception:
            continue
    return None


def _segments(body):
    return [ln.strip() for ln in body.splitlines()
            if ln.strip() and not ln.startswith("#")]


def vet(url, wait=10):
    """The four questions above. Returns a dict; `ok` is the verdict."""
    try:
        status, headers, first = get(url)
    except Exception as exc:
        return {"ok": False, "why": f"unreachable ({type(exc).__name__})", "url": url}

    cors = headers.get("Access-Control-Allow-Origin")
    ctype = headers.get("Content-Type", "")
    before = _segments(first)

    if status != 200:
        return {"ok": False, "why": f"HTTP {status}", "url": url}
    if "#EXTM3U" not in first:
        return {"ok": False, "why": "not a playlist", "url": url}
    if cors != "*":
        return {"ok": False, "why": f"CORS is {cors!r}, not '*'", "url": url}
    if "mpegurl" not in ctype.lower():
        return {"ok": False, "why": f"content-type {ctype!r}", "url": url}

    time.sleep(wait)
    try:
        _, _, second = get(url)
    except Exception as exc:
        return {"ok": False, "why": f"second read failed ({type(exc).__name__})",
                "url": url}
    after = _segments(second)

    if not before or not after:
        return {"ok": False, "why": "playlist has no segments", "url": url}
    if before[-1] == after[-1]:
        return {"ok": False,
                "why": f"not advancing after {wait}s — a loop or a dead encoder",
                "url": url}

    return {"ok": True, "why": None, "url": url,
            "cors": cors, "ctype": ctype, "last": after[-1]}


def resolve(target, referer=None):
    """A .m3u8 URL passes through; anything else is treated as an
       ipcamlive alias and resolved. Returns a URL or None."""
    if target.startswith("http") and ".m3u8" in target:
        return target
    return ipcamlive_m3u8(target, referer)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__.strip())
        return 2
    bad = 0
    for arg in args:
        label, _, target = arg.partition("=")
        if not target:
            label, target = target or arg, arg
        try:
            url = resolve(target)
        except Exception as exc:
            print(f"{label:24} ✗ {type(exc).__name__}: {exc}")
            bad += 1
            continue
        if not url:
            print(f"{label:24} ✗ no stream (camera deleted or offline)")
            bad += 1
            continue
        v = vet(url)
        if v["ok"]:
            print(f"{label:24} ✓ live, CORS-open")
            print(f"{'':24}   {url}")
        else:
            print(f"{label:24} ✗ {v['why']}")
            print(f"{'':24}   {url}")
            bad += 1
        time.sleep(2)   # be a good guest — one camera at a time
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
