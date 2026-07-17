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

   data/media.json is written by tools/enrich_media.py (yt-dlp): it
   searches YouTube per city, keeps only live_status == is_live for
   cams, and classifies street-level vs window vantage by title.

   Windy embeds were CUT (2026-07): their "live" player is a poster
   frame that links out to windy.com — it never autoplays a stream,
   which fails the owner rule above. Legacy `ambient` (recorded
   loops) is likewise deliberately NOT used here.
   ============================================================ */
import { mediaIndex } from './data.js';

/* Accept 'id', 'id?start=SS', { yt, start? } or { channel } shapes. */
function parseYt(v) {
  if (!v) return null;
  if (typeof v === 'string') {
    const m = v.match(/^([A-Za-z0-9_-]{11})(?:[?&].*?start=(\d+))?/);
    return m ? { yt: m[1], start: parseInt(m[2], 10) || 0 } : null;
  }
  if (v.yt) return { yt: v.yt, start: parseInt(v.start, 10) || 0 };
  if (v.channel) return { channel: v.channel };
  return null;
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
  const cur = parseYt(loc.webcam);
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
    const cur = parseYt(loc.window);
    if (cur) return { ...cur, kind: 'window', source: 'curated' };
    const m = mediaIndex()[loc.id];
    if (m?.window?.yt) return { yt: m.window.yt, kind: 'window', source: 'auto', title: m.window.title };
    return null;
  })();
  if (pick?.yt && pick.yt === liveFor(loc)?.yt) return null;
  return pick;
}

/* Best single live view for the standalone Virtual Window page —
   the window vantage first (that's the page), else the street cam. */
export function bestWindow(loc) {
  return windowFor(loc) || liveFor(loc);
}

export function monumentsFor(loc) {
  return (loc?.monuments || []).filter(m => m && m.yt && m.name);
}

/* Scene inventory — drives map badges, filters, and rail membership. */
export function sceneFlags(loc) {
  return {
    walk: !!walkFor(loc),
    drive: !!driveFor(loc),
    live: !!liveFor(loc),
    window: !!windowFor(loc),
    monuments: monumentsFor(loc).length > 0,
  };
}
