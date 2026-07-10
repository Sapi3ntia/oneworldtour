/* ============================================================
   PHOTOS — lazy Wikipedia thumbnails with a sessionStorage cache
   so card photos survive page hops without refetching.
   ============================================================ */
import { arrivalPhoto, galleryPhotos } from './api.js';

/* A pageimage thumbnail is sometimes the place's FLAG or seal — a flag
   is not a photo of a place. Detect by filename and fall back to the
   page's first real gallery photo. */
const NOT_A_PHOTO = /flag|coat[_ ]of[_ ]arms|seal[_ ]of|escudo|bandera|locator|(^|[_\-.%/])map([_\-.%]|$)|map[_ ]of|\.svg/i;

const KEY = 'owt_photos_v1';
let cache = null;
function load() {
  if (!cache) {
    try { cache = JSON.parse(sessionStorage.getItem(KEY)) || {}; }
    catch { cache = {}; }
  }
  return cache;
}
function save() {
  try { sessionStorage.setItem(KEY, JSON.stringify(cache)); } catch {}
}

/* Resolve a place's card photo URL (or null). Deduped + cached. */
const inflight = new Map();
export function photoFor(place, size = 640) {
  const c = load();
  const k = `${place.id}:${size}`;
  if (k in c) return Promise.resolve(c[k]);
  if (inflight.has(k)) return inflight.get(k);
  const slug = place.wikipedia_slug || place.name;
  const p = arrivalPhoto(slug, size)
    .then(async url => {
      if (url && NOT_A_PHOTO.test(url)) {
        const alt = await galleryPhotos(slug, 1);
        url = alt[0] || url;
      }
      c[k] = url; save(); inflight.delete(k);
      return url;
    });
  inflight.set(k, p);
  return p;
}

/* Attach a photo to a card element when it scrolls into view. */
const io = ('IntersectionObserver' in window)
  ? new IntersectionObserver(entries => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        io.unobserve(e.target);
        const fn = e.target._loadPhoto;
        if (fn) { fn(); delete e.target._loadPhoto; }
      }
    }, { rootMargin: '250px' })
  : null;

export function lazyPhoto(el, place, size = 640) {
  const apply = () => photoFor(place, size).then(url => {
    if (url) {
      el.style.backgroundImage = `url("${url}")`;
      el.textContent = '';
    }
  });
  if (io) { el._loadPhoto = apply; io.observe(el); }
  else apply();
}
