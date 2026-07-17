#!/usr/bin/env python3
"""
build_worldmap.py — bake the world into a tiny, framework-free map asset.

Input : countries-110m TopoJSON (world-atlas@2, Natural Earth derived)
Output: assets/world.json  { w, h, countries:[{ n(ame), p(ath) }] }

Every country outline is decoded from TopoJSON and PRE-PROJECTED with the
Natural Earth I projection at build time, so the runtime (js/lib/geo.js)
only ever projects single points (city dots) with the same closed-form
polynomial — no Leaflet, no tiles, no plugin, nothing to glitch.

The projection constants here MUST match js/lib/geo.js:
  W=1000, H=520, S=182.7832…  (S = (W/2) / (pi * 0.8707))

Usage:
  python3 tools/build_worldmap.py <countries-110m.json> [out=assets/world.json]
"""
import json
import math
import sys

W = 1000.0
RX_MAX = math.pi * 0.8707          # Natural Earth I max |x| in raw units
S = (W / 2.0) / RX_MAX             # raw → svg scale  (≈ 182.7832)
H = 520.0                          # fits raw |y|max ≈ 1.4224 → 260.03 ≈ H/2


def ne1(lon_deg, lat_deg):
    """Natural Earth I raw projection (d3-geo polynomial), then svg coords."""
    lam = math.radians(lon_deg)
    phi = math.radians(lat_deg)
    p2 = phi * phi
    p4 = p2 * p2
    rx = lam * (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)))
    ry = phi * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4)))
    return (W / 2.0 + rx * S, H / 2.0 - ry * S)


def decode_arcs(topo):
    """TopoJSON delta-decoded arcs → list of [(lon,lat), …]."""
    tr = topo.get("transform")
    sx, sy = (tr["scale"] if tr else (1, 1))
    tx, ty = (tr["translate"] if tr else (0, 0))
    arcs = []
    for arc in topo["arcs"]:
        pts, x, y = [], 0, 0
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)
    return arcs


def ring_points(arc_idx_list, arcs):
    """Stitch one ring from signed arc indices (~i means reversed)."""
    pts = []
    for i in arc_idx_list:
        seg = arcs[i] if i >= 0 else list(reversed(arcs[~i]))
        if pts:
            seg = seg[1:]          # shared endpoint
        pts.extend(seg)
    return pts


def unwrap(pts):
    """Make ring longitudes continuous (no ±360 jumps between neighbours)."""
    out = [pts[0]]
    for lon, lat in pts[1:]:
        prev = out[-1][0]
        while lon - prev > 180:
            lon -= 360
        while lon - prev < -180:
            lon += 360
        out.append((lon, lat))
    return out


def close_polar(pts):
    """A ring that nets a full 360° lap encircles a pole (Antarctica):
    close it along the pole line so it clips into a solid shape."""
    if abs(pts[0][0] - pts[-1][0]) > 180:
        pole = -90.0 if (sum(p[1] for p in pts) / len(pts)) < 0 else 90.0
        pts = pts + [(pts[-1][0], pole), (pts[0][0], pole)]
    return pts


def clip_lon(poly, lo, hi):
    """Sutherland–Hodgman clip of a (lon,lat) ring to the lon strip [lo,hi]."""
    def half(pl, bound, keep_ge):
        out = []
        for i in range(len(pl)):
            a, b = pl[i], pl[(i + 1) % len(pl)]
            a_in = (a[0] >= bound) if keep_ge else (a[0] <= bound)
            b_in = (b[0] >= bound) if keep_ge else (b[0] <= bound)
            if a_in:
                out.append(a)
            if a_in != b_in:
                t = (bound - a[0]) / (b[0] - a[0])
                out.append((bound, a[1] + t * (b[1] - a[1])))
        return out
    poly = half(poly, lo, True)
    return half(poly, hi, False) if poly else []


def split_ring(pts):
    """Ring → list of rings, all inside lon [-180,180]. Rings that cross the
    antimeridian (Fiji, Russia) get cut there instead of smearing a
    horizontal band across the whole map; polar rings are closed first."""
    pts = close_polar(unwrap(pts))
    lons = [p[0] for p in pts]
    rings = []
    k = math.floor((min(lons) + 180.0) / 360.0)
    while -180.0 + 360.0 * k <= max(lons):
        piece = clip_lon(pts, -180.0 + 360.0 * k, 180.0 + 360.0 * k)
        if len(piece) >= 3:
            rings.append([(lon - 360.0 * k, lat) for lon, lat in piece])
        k += 1
    return rings


def ring_to_path(pts):
    out = []
    last = None
    for lon, lat in pts:
        x, y = ne1(lon, lat)
        x, y = round(x, 1), round(y, 1)
        if (x, y) == last:
            continue
        out.append(f"{'M' if last is None else 'L'}{x} {y}")
        last = (x, y)
    if len(out) < 3:
        return ""
    return "".join(out) + "Z"


def geom_to_path(geom, arcs):
    polys = geom["arcs"] if geom["type"] == "MultiPolygon" else [geom["arcs"]]
    d = []
    for poly in polys:
        for ring in poly:                     # outer + holes; fill-rule evenodd
            for part in split_ring(ring_points(ring, arcs)):
                p = ring_to_path(part)
                if p:
                    d.append(p)
    return "".join(d)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "countries-110m.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "assets/world.json"
    topo = json.load(open(src))
    arcs = decode_arcs(topo)
    countries = []
    for geom in topo["objects"]["countries"]["geometries"]:
        name = (geom.get("properties") or {}).get("name", "")
        path = geom_to_path(geom, arcs)
        if path:
            countries.append({"n": name, "p": path})
    data = {"w": W, "h": H, "countries": countries}
    with open(out, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    size = len(json.dumps(data, separators=(",", ":"))) / 1024
    print(f"{out}: {len(countries)} countries, {size:.0f} KB")


if __name__ == "__main__":
    main()
