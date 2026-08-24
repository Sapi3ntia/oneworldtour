#!/usr/bin/env python3
"""seat_stats.py — count the scene seats the way the FRONTEND counts them.

Every batch note in README.md and TODO.md quotes a line like
"walk 1,154 · drive 1,145 · live 252 · window 152 · no window 1,670".
Those numbers were being produced ad hoc, and two of the rules that decide
them are easy to miss, so successive batches quoted figures that were not on
the same scale as each other:

  * `liveFor()` reads `loc.webcam`, NOT `loc.live`. A counter that looks for
    `loc.live` silently undercounts every hand-curated cam in the atlas.
  * `windowFor()` returns null when the window id EQUALS the live id — one
    feed cannot fill both seats. A counter without that rule credits about
    eleven places with a window the UI never draws.

and one that is easy to define differently on different days:

  * a place whose stage is "empty" is one the arrival page has nothing to
    show for — which includes monument tabs, not just the four scenes.

So this is a port of `js/lib/media.js`, not an independent measure. If the
two ever disagree, media.js is right and this file is the bug. Quote a
before/after delta only when both ends came out of the same script:

  python3 tools/seat_stats.py                  # working tree
  python3 tools/seat_stats.py --rev HEAD       # what shipped last
  python3 tools/seat_stats.py --continent Antarctica
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(path, rev):
    """Read a repo file from the working tree, or from a git revision."""
    if not rev:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    out = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{path}"],
                         capture_output=True, text=True)
    if out.returncode:
        sys.exit(f"cannot read {path} at {rev}: {out.stderr.strip()}")
    return json.loads(out.stdout)


def parse_yt(v):
    """parseYt() in media.js: 'id', 'id?start=SS', {yt}, or {channel}."""
    if not v:
        return None
    if isinstance(v, str):
        m = re.match(r"^([A-Za-z0-9_-]{11})", v)
        return m.group(1) if m else None
    if isinstance(v, dict):
        return v.get("yt") or ("CHANNEL" if v.get("channel") else None)
    return None


def flags(loc, media):
    m = media.get(loc.get("id"), {})
    walk = parse_yt(loc.get("walk")) or parse_yt(m.get("walk"))
    drive = parse_yt(loc.get("drive")) or parse_yt(m.get("drive"))
    live = parse_yt(loc.get("webcam")) or parse_yt(m.get("live"))
    win = parse_yt(loc.get("window")) or parse_yt(m.get("window"))
    if win and win == live:
        win = None                      # one feed, one seat — windowFor()
    return {"walk": bool(walk), "drive": bool(drive), "live": bool(live),
            "window": bool(win), "monuments": bool(loc.get("monuments"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rev", help="git revision to measure instead of the working tree")
    ap.add_argument("--continent", help="also break out one continent")
    args = ap.parse_args()

    media = load("data/media.json", args.rev)["places"]
    regions = load("data/index.json", args.rev)["regions"]

    KEYS = ("walk", "drive", "live", "window", "monuments")
    def blank():
        return dict({"n": 0, "tabs": 0, "nowin": 0, "empty": 0},
                    **{k: 0 for k in KEYS})
    tot, one = blank(), blank()

    for r in regions:
        if not r.get("enabled"):
            continue
        for loc in load(r["file"], args.rev)["locations"]:
            f = flags(loc, media)
            buckets = [tot]
            if args.continent and loc.get("continent") == args.continent:
                buckets.append(one)
            for b in buckets:
                b["n"] += 1
                b["tabs"] += len(loc.get("monuments") or [])
                for k in KEYS:
                    b[k] += f[k]
                if not f["window"]:
                    b["nowin"] += 1
                if not any(f.values()):
                    b["empty"] += 1

    def line(label, b):
        if not b["n"]:
            return f"{label:<12} nothing"
        return (f"{label:<12} {b['n']:>5} places · walk {b['walk']:>5} · "
                f"drive {b['drive']:>5} · live {b['live']:>4} · "
                f"window {b['window']:>4} · monuments {b['monuments']:>5} "
                f"({b['tabs']} tabs) · no window {b['nowin']:>5} · "
                f"empty stage {b['empty']:>4} · window-less "
                f"{b['nowin'] / b['n'] * 100:.1f}%")

    print(line(args.rev or "working", tot))
    if args.continent:
        print(line(args.continent, one))


if __name__ == "__main__":
    main()
