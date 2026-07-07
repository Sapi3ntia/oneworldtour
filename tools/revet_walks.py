#!/usr/bin/env python3
"""
revet_walks.py — re-check every curated `walk` (and `webcam`) YouTube id still
exists and is public, via YouTube's oEmbed endpoint.

Why: curated video ids rot over time (videos get deleted / made private). The
app already degrades gracefully (the scene player's onError falls back to the
Ken Burns photo flythrough), but this catches dead ids so we can swap in a fresh
walking-tour video and keep real footage everywhere.

Usage:
    python3 tools/revet_walks.py            # check walks
    python3 tools/revet_walks.py --webcam   # also check webcam ids

oEmbed 200 = exists & public. NOTE: 200 does NOT guarantee third-party embedding
is allowed (no reliable API for that) — but reputable walking-tour channels allow
it, and the player's onError fallback covers the rest. Run this every few months.
"""
import json, sys, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK_WEBCAM = "--webcam" in sys.argv


def vid_of(field):
    """A walk/webcam field may be a string id or { yt: id }."""
    if isinstance(field, str):
        return field
    if isinstance(field, dict):
        return field.get("yt")
    return None


def oembed(vid):
    inner = urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}", safe="")
    url = f"https://www.youtube.com/oembed?url={inner}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return 200, json.load(r).get("title", "")[:70]
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return str(e)[:40], ""


def main():
    index = json.loads((ROOT / "data/index.json").read_text())
    targets = []  # (place_id, kind, vid)
    for region in index["regions"]:
        if not region.get("enabled"):
            continue
        data = json.loads((ROOT / region["file"]).read_text())
        for loc in data["locations"]:
            for kind in (["walk", "webcam"] if CHECK_WEBCAM else ["walk"]):
                v = vid_of(loc.get(kind))
                if v:
                    targets.append((loc["id"], kind, v))

    dead = []
    for pid, kind, v in targets:
        status, title = oembed(v)
        ok = status == 200
        print(f"{'OK ' if ok else 'DEAD'} {pid:18} {kind:6} {v}  {title}")
        if not ok:
            dead.append((pid, kind, v, status))
        time.sleep(0.15)

    print(f"\n{len(targets)-len(dead)}/{len(targets)} alive.")
    if dead:
        print("DEAD ids (swap these out):")
        for pid, kind, v, status in dead:
            print(f"  {pid} {kind} {v} -> {status}")
        sys.exit(1)


if __name__ == "__main__":
    main()
