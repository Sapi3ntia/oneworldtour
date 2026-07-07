#!/usr/bin/env python3
"""
build_webcams.py — attach a REAL live webcam to cities that have one.

The window/live-cam slot is the strictest category in the app: it must show
ACTUAL live footage, or honestly say "none yet". So every id below was confirmed
with tools/verify_ambient.py as **public + embeddable + isLiveNow** at the time
it was added. A cam that only verifies as "rec" (a 24/7 stream that happens to be
between broadcasts) is deliberately NOT added here — a recorded clip must never
sit under a "🔴 streaming now" label.

Re-vet over time:  /usr/bin/python3 tools/verify_ambient.py <id>=<id> ...
If a cam stops verifying LIVE, remove it here and re-run so the city honestly
falls back to "No live cam of this place yet" instead of showing a dead frame.

Idempotent: sets each location's `webcam` to exactly MAP[id]. Run from root:
    /usr/bin/python3 tools/build_webcams.py
"""
import json, glob, os, sys

# location id -> "<youtube live id>"   (each verified pub+emb+LIVE on add)
MAP = {
    # ---- Asia ----
    "tokyo":         "dfVK7ld38Ys",  # Shibuya Scramble Crossing (FNN, live)
    # ---- Europe ----
    "london":        "M3EYAY2MftI",  # Abbey Road Crossing (EarthCam, live)
    # ---- North America ----
    "new-orleans":   "Ksrleaxxxhw",  # New Orleans Street View (EarthCam, live)
    "chicago":       "O0UGT7AT3aw",  # Chicago Skydeck Cam (EarthCam, live)
    "san-francisco": "CXYr04BWvmc",  # SF-Oakland Bay Bridge (24/7, live)
}


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = sorted(glob.glob(os.path.join(root, "data", "*.json")))
    remaining = set(MAP)
    changed = 0
    for f in files:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        locs = d.get("locations") if isinstance(d, dict) else None
        if not locs:
            continue
        touched = False
        for l in locs:
            lid = l.get("id")
            if lid in MAP:
                if l.get("webcam") != MAP[lid]:
                    l["webcam"] = MAP[lid]
                    touched = True
                    changed += 1
                remaining.discard(lid)
                print(f"  {lid:18} <- webcam {MAP[lid]}")
        if touched:
            json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"WROTE {os.path.basename(f)}")
    if remaining:
        print("\n!! ids in MAP not found in any data file:", ", ".join(sorted(remaining)), file=sys.stderr)
    print(f"\n=== {changed} location(s) updated; {len(MAP)-len(remaining)}/{len(MAP)} ids matched ===")


if __name__ == "__main__":
    main()
