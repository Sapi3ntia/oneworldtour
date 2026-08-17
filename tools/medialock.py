#!/usr/bin/env python3
"""
medialock.py — one writer at a time on data/media.json, and never a lost update.

WHY THIS EXISTS
    Three tools write `data/media.json`, and all three used the same shape:
    read the whole file into memory at startup, mutate the dict, then rewrite
    the whole file. That is a read-modify-write with no lock and no re-read,
    and it loses data in a way nobody notices, because the file that survives
    is *valid* — it is just older.

      enrich_media.py   holds `media` in memory for HOURS (4 s of politeness
                        sleep per seat, per place) and rewrites the entire
                        file after every single place
      harvest_cams.py   rewrites the entire file after every vetted cam
      prune_media.py    rewrites the entire file once, at the end

    So: start a long `enrich_media.py --max 200`, then run `harvest_cams.py
    --apply` in the other terminal while it works. harvest writes 40 cams.
    enrich finishes its next place three seconds later and writes its own
    startup snapshot back over the top — all 40 gone, no error, no diff to
    read, and the next `prune_media.py` reports nothing wrong because nothing
    is wrong with what's left. The only symptom is seats that were filled
    being empty again, which reads exactly like "the sweep found nothing" —
    the same failure-looks-like-success shape as the `--max` truncation bug.

WHAT THIS DOES
    `update()` is the only supported way to write the file:

      1. take an exclusive `flock` on a sidecar lockfile, so two processes
         cannot be inside the critical section at once
      2. **re-read media.json from disk** — this is the half a plain lock
         would not fix, because the caller's in-memory copy may be hours stale
      3. hand that FRESH document to the caller's mutate function, which
         applies only *this* process's change (one place, one seat, one drop)
      4. write it back atomically (`tmp` + `os.replace`), so a killed process
         leaves the previous complete file rather than a truncated one

    The rule that falls out of step 3 and is easy to get wrong: a mutate
    function must never assign a whole subtree it captured earlier. Write
    `doc["places"][pid] = entry`, never `doc["places"] = my_places`.

    Reads stay lock-free. A torn read is impossible because writes are atomic
    renames, and every writer re-reads inside the lock anyway.

Usage:
    import medialock

    media = medialock.load()                  # planning snapshot, no lock
    ...
    medialock.update(lambda doc: doc["places"].__setitem__(pid, entry))
    medialock.update(lambda doc: doc["places"].pop(pid, None))
"""
import fcntl
import json
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "data" / "media.json"
# A sidecar, not the file itself: `update()` finishes with os.replace(), which
# swaps in a NEW inode. An flock held on the old inode would guard nothing —
# the next process opens the replacement and locks something else entirely.
LOCK = ROOT / "data" / ".media.lock"

# media.json is written at indent=1 and has been since it was created. Writing
# any other value here reindents all 300 KB and buries the real change in a
# whole-file diff (the same trap prune_monuments.py documents at its own
# write site).
INDENT = 1
TIMEOUT = 300.0


def _empty():
    return {"generated": None, "places": {}}


def load(path=MEDIA):
    """The current document, or an empty one. No lock — see module docstring.

    For planning only. Anything you intend to WRITE back must go through
    `update()`, which re-reads inside the lock.
    """
    if not Path(path).exists():
        return _empty()
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    doc.setdefault("places", {})
    return doc


@contextmanager
def held(timeout=TIMEOUT, quiet=False):
    """Exclusive advisory lock, waited for rather than failed on.

    A sweep that dies because a 200 ms prune had the lock would be worse than
    the race it replaces, so this blocks — but it says so, because a silent
    multi-minute stall is its own kind of unreadable failure.
    """
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOCK, "w")
    deadline = time.time() + timeout
    announced = False
    try:
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.time() > deadline:
                    raise TimeoutError(
                        f"media.json is locked by another tool and did not "
                        f"free up in {timeout:.0f}s. If nothing else is "
                        f"running, delete {LOCK}."
                    )
                if not announced and not quiet:
                    print("  … waiting for the media.json lock (another tool "
                          "is writing)", file=sys.stderr)
                    announced = True
                time.sleep(0.2)
        yield fh
    finally:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()


def _write_atomic(doc, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".media-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=INDENT, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def update(mutate, path=MEDIA, stamp=True, quiet=False):
    """Apply `mutate(doc)` to the CURRENT on-disk document, atomically.

    `mutate` receives a freshly-read document and edits it in place. Touch
    only the keys this process is responsible for — assigning a whole subtree
    captured before the lock is exactly the lost update this exists to stop.

    Returns the document that was written.
    """
    with held(quiet=quiet):
        doc = load(path)
        mutate(doc)
        doc.setdefault("places", {})
        if stamp:
            doc["generated"] = datetime.now(timezone.utc).isoformat(
                timespec="seconds")
        _write_atomic(doc, path)
        return doc


def put(pid, entry, path=MEDIA):
    """Checkpoint one place's seats. Drops the record when it has none left."""
    def mutate(doc):
        if entry:
            doc["places"][pid] = entry
        else:
            doc["places"].pop(pid, None)
    return update(mutate, path=path)
