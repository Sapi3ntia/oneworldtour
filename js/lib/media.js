/* ============================================================
   MEDIA — resolve every place's four scenes, honestly labelled.

   The four scenes (the product):
     🚶 WALK   — a real walking-tour video of that place, seekable.
     🚗 DRIVE  — a real driving-tour video: the place through a
                 windshield, seekable like a walk.
     🔴 LIVE   — a real 24/7 live cam: street / intersection level.
     🪟 WINDOW — ALSO LIVE, but the out-a-window vantage: skyline,
                 rooftop, harbor, panorama. A window you look out of.

   OWNER RULE (2026-07): both cam scenes must be actually live.
   No recorded loop, no still, no day-timelapse ever stands in for
   a window. Can't find a live feed? The place honestly doesn't
   have that scene yet — resolvers return null and the UI shows
   nothing rather than a fake.

   Tier order per scene (curation beats automation):
     walk   : loc.walk (hand-curated) → media.json walk → null
     drive  : loc.drive (hand-curated) → media.json drive → null
     live   : loc.webcam (hand-curated) → media.json live → null
     window : loc.window (hand-curated) → media.json window → null

   A curated cam may be a YouTube id OR { hls } — a raw .m3u8. See
   parseCam() below for what an HLS cam has to prove to sit in a seat.
   media.json stays YouTube-only: it is written by yt-dlp.

   AFTER DARK (2026-07): the walk and drive seats each have a night
   twin — loc.night_walk / loc.night_drive → media.json night_walk /
   night_drive — plus loc.nightlife, the after-dark counterpart to
   loc.monuments. See the section at the bottom of this file for why
   the two LIVE seats deliberately have no night twin.

   data/media.json is written by tools/enrich_media.py (yt-dlp): it
   searches YouTube per city, keeps only live_status == is_live for
   cams, and classifies street-level vs window vantage by title.

   Windy embeds were CUT (2026-07): their "live" player is a poster
   frame that links out to windy.com — it never autoplays a stream,
   which fails the owner rule above. Legacy `ambient` (recorded
   loops) is likewise deliberately NOT used here.

   THE ONE THING THAT IS NOT A SCENE (2026-08): js/lib/satellite.js
   draws the geostationary sky over a place into the window seat when
   windowFor() returns null. It is NOT a fifth scene and NOT a
   stand-in window — it never passes through this file, never appears
   in sceneFlags(), never reaches the Virtual Window page, and wears
   its own 🛰️ badge with a title that says out loud there is no
   window cam. Nothing here needs to change to keep that true; it is
   written down so the next person to add a resolver knows why the
   satellite is missing from all of them.
   ============================================================ */
import { mediaIndex } from './data.js';

/* Accept 'id', 'id?start=SS', { yt, start?, title? } or { channel } shapes. */
function parseYt(v) {
  if (!v) return null;
  if (typeof v === 'string') {
    const m = v.match(/^([A-Za-z0-9_-]{11})(?:[?&].*?start=(\d+))?/);
    return m ? { yt: m[1], start: parseInt(m[2], 10) || 0 } : null;
  }
  /* A curated cam may name its own vantage — "out over the harbour, live".
     The { hls } shape has carried a title since the HLS cams landed; a
     YouTube one earns the same, so a hand-picked cam reads the same way
     whichever pipe it arrives through. */
  if (v.yt) {
    const p = { yt: v.yt, start: parseInt(v.start, 10) || 0 };
    return v.title ? { ...p, title: v.title } : p;
  }
  if (v.channel) return { channel: v.channel };
  return null;
}

/* The two CAM seats take one shape the seekable seats never do:
   { hls: 'https://.../stream.m3u8', title? } — a raw HLS stream, mounted
   through the same player the TV uses. Walks and drives deliberately
   cannot: those seats must be seekable, and a live stream is not.

   An HLS cam earns its seat exactly the way a YouTube one does — it is
   verified live at build time, and re-verified by tools/verify_cams.py.
   The check is 200 + `Access-Control-Allow-Origin: *` + an m3u8
   content-type + segment names that ADVANCE between two reads, which is
   the HLS way of asking the question live_status == is_live asks of
   YouTube. A playlist that never advances is a loop or a dead stream,
   and neither one is allowed to sit in a 🔴 or 🪟 seat. */
function parseCam(v) {
  if (v && typeof v === 'object' && v.hls) {
    return v.title ? { hls: v.hls, title: v.title } : { hls: v.hls };
  }
  return parseYt(v);
}

export function walkFor(loc) {
  if (!loc) return null;
  const cur = parseYt(loc.walk);
  if (cur) return { ...cur, kind: 'walk', source: 'curated' };
  const m = mediaIndex()[loc.id];
  if (m?.walk?.yt) {
    return { yt: m.walk.yt, start: m.walk.start || 0, kind: 'walk',
             source: 'auto', title: m.walk.title, date: m.walk.date };
  }
  return null;
}

/* Driving tour — same contract as a walk, windshield vantage. */
export function driveFor(loc) {
  if (!loc) return null;
  const cur = parseYt(loc.drive);
  if (cur) return { ...cur, kind: 'drive', source: 'curated' };
  const m = mediaIndex()[loc.id];
  if (m?.drive?.yt) {
    return { yt: m.drive.yt, start: m.drive.start || 0, kind: 'drive',
             source: 'auto', title: m.drive.title, date: m.drive.date };
  }
  return null;
}

/* Street-level live cam. */
export function liveFor(loc) {
  if (!loc) return null;
  const cur = parseCam(loc.webcam);
  if (cur) return { ...cur, kind: 'live', source: 'curated' };
  const m = mediaIndex()[loc.id];
  if (m?.live?.yt) return { yt: m.live.yt, kind: 'live', source: 'auto', title: m.live.title };
  return null;
}

/* Live out-a-window view. Never a loop, never a timelapse — and never
   the same feed the Live tab already shows. */
export function windowFor(loc) {
  if (!loc) return null;
  const pick = (() => {
    const cur = parseCam(loc.window);
    if (cur) return { ...cur, kind: 'window', source: 'curated' };
    const m = mediaIndex()[loc.id];
    if (m?.window?.yt) return { yt: m.window.yt, kind: 'window', source: 'auto', title: m.window.title };
    return null;
  })();
  // one feed cannot fill both cam seats — compare on whichever key it uses
  const live = liveFor(loc);
  if (pick?.yt && pick.yt === live?.yt) return null;
  if (pick?.hls && pick.hls === live?.hls) return null;
  return pick;
}

/* Best single live view for the standalone Virtual Window page —
   the window vantage first (that's the page), else the street cam. */
export function bestWindow(loc) {
  return windowFor(loc) || liveFor(loc);
}

/* ---------------- after dark ----------------
   Night is NOT a fifth and sixth pane. It's the same walk and drive
   seats with the lights off, so the stage keeps its four-pane layout
   and just swaps what's mounted in the two seekable seats.

   The two live seats have no night twin ON PURPOSE: a live cam is
   already whatever time it is there. Labelling one "night" would be
   a promise the feed can't keep for more than a few hours a day. */
export function nightWalkFor(loc) {
  if (!loc) return null;
  const cur = parseYt(loc.night_walk);
  if (cur) return { ...cur, kind: 'night_walk', source: 'curated' };
  const m = mediaIndex()[loc.id];
  if (m?.night_walk?.yt) {
    return { yt: m.night_walk.yt, start: m.night_walk.start || 0, kind: 'night_walk',
             source: 'auto', title: m.night_walk.title, date: m.night_walk.date };
  }
  return null;
}

export function nightDriveFor(loc) {
  if (!loc) return null;
  const cur = parseYt(loc.night_drive);
  if (cur) return { ...cur, kind: 'night_drive', source: 'curated' };
  const m = mediaIndex()[loc.id];
  if (m?.night_drive?.yt) {
    return { yt: m.night_drive.yt, start: m.night_drive.start || 0, kind: 'night_drive',
             source: 'auto', title: m.night_drive.title, date: m.night_drive.date };
  }
  return null;
}

export function monumentsFor(loc) {
  return (loc?.monuments || []).filter(m => m && m.yt && m.name);
}

/* 🍸 Nightlife venues — the after-dark answer to monuments, and
   deliberately the same { name, yt, start } shape, so they ride the
   exact same chip bar and the same borrowed walk seat. */
export function nightlifeFor(loc) {
  return (loc?.nightlife || []).filter(v => v && v.yt && v.name);
}

/* Does this place have anything to show after dark at all? */
export function hasNight(loc) {
  return !!(nightWalkFor(loc) || nightDriveFor(loc) || nightlifeFor(loc).length);
}

/* Scene inventory — drives map badges, filters, and rail membership. */
export function sceneFlags(loc) {
  return {
    walk: !!walkFor(loc),
    drive: !!driveFor(loc),
    live: !!liveFor(loc),
    window: !!windowFor(loc),
    monuments: monumentsFor(loc).length > 0,
    night: hasNight(loc),
  };
}
