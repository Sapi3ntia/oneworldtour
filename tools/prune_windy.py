#!/usr/bin/env python3
"""Apply tools/windy_overrides.json to data/windy.json (idempotent, offline).

The overrides file is the hand-audited verdict list from the 2026-07-07 window
review — cams that were junk views (airports, highway mileposts, sky cams) or
pointed at the wrong place entirely (Ushuaia's cam was Puerto Williams, Chile).
Run this after any fetch_windy.py re-crawl that was made with an older checkout
(current fetch_windy.py already applies the overrides itself); running it twice
is harmless.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WINDY = os.path.join(ROOT, "data", "windy.json")
OVR = os.path.join(ROOT, "tools", "windy_overrides.json")


def apply_overrides(windy, ovr):
    """Mutates and returns (windy, stats). Shared with fetch_windy.py."""
    stats = {"entry": 0, "live": 0, "window": 0}
    for lid in ovr.get("drop_entry", {}):
        if lid in windy:
            del windy[lid]; stats["entry"] += 1
    for lid in ovr.get("drop_live", {}):
        w = windy.get(lid)
        if w and "live" in w:
            del w["live"]; stats["live"] += 1
            if "window" not in w:
                del windy[lid]
    for lid in ovr.get("drop_window", {}):
        w = windy.get(lid)
        if w and "window" in w:
            del w["window"]; stats["window"] += 1
            if "live" not in w:
                del windy[lid]
    return windy, stats


def main():
    windy = json.load(open(WINDY))
    ovr = json.load(open(OVR))
    before = len(windy)
    windy, stats = apply_overrides(windy, ovr)
    windy = dict(sorted(windy.items()))
    with open(WINDY, "w") as f:
        json.dump(windy, f, ensure_ascii=False, indent=0, separators=(",", ":"))
    n_live = sum(1 for w in windy.values() if w.get("live"))
    n_win = sum(1 for w in windy.values() if w.get("window"))
    print(f"entries {before} -> {len(windy)} "
          f"(dropped {stats['entry']} whole, {stats['live']} live tiers, "
          f"{stats['window']} window tiers)")
    print(f"now: {n_win} window cams, {n_live} live cams")


if __name__ == "__main__":
    main()
