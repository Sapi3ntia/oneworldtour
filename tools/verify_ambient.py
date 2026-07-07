#!/usr/bin/env python3
"""Verify candidate ambient-window YouTube videos.

For each `key=VIDEOID[:start]` argument, checks:
  * PUBLIC      — oEmbed returns 200 (+ title/author)
  * EMBEDDABLE  — watch page playerResponse has "playableInEmbed": true
  * RECORDED    — not currently a live broadcast (isLiveNow / isLive absent)

Ambient windows should be EMBEDDABLE + PUBLIC. RECORDED is preferred (a
recorded loop is the whole point) but a permanently-live cam is fine too —
the caller decides. Prints a table; never trust a candidate it can't confirm.
"""
import json, sys, urllib.request, urllib.error

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
# consent cookie avoids the EU consent wall returning a stub page
COOKIE = "CONSENT=YES+cb; SOCS=CAI"

def _get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cookie": COOKIE,
                                               "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")

def oembed(vid):
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    try:
        st, body = _get(url)
        if st == 200:
            j = json.loads(body)
            return True, j.get("title", "")[:60], j.get("author_name", "")[:30]
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}", ""
    except Exception as e:
        return False, str(e)[:40], ""
    return False, "?", ""

def watch_flags(vid):
    url = f"https://www.youtube.com/watch?v={vid}&hl=en&gl=US"
    try:
        st, body = _get(url)
    except Exception as e:
        return None, None, str(e)[:40]
    embeddable = '"playableInEmbed":true' in body
    live = ('"isLiveNow":true' in body) or ('"isLive":true' in body)
    return embeddable, live, ""

def main():
    rows = []
    for arg in sys.argv[1:]:
        key, _, rest = arg.partition("=")
        vid, _, start = rest.partition(":")
        pub, title, author = oembed(vid)
        emb, live, err = (None, None, "skipped") if not pub else watch_flags(vid)
        verdict = "OK" if (pub and emb) else "REJECT"
        rows.append((verdict, key, vid, start or "0",
                     "pub" if pub else "PRIV",
                     "emb" if emb else ("NOEMB" if emb is False else "-"),
                     "LIVE" if live else ("rec" if live is False else "-"),
                     title or err))
    w = max((len(r[1]) for r in rows), default=4)
    for r in rows:
        print(f"{r[0]:7} {r[1]:<{w}} {r[2]:12} s={r[3]:<5} {r[4]:5} {r[5]:6} {r[6]:5} {r[7]}")

if __name__ == "__main__":
    main()
