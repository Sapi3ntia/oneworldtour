#!/usr/bin/env python3
"""
enrich_canada.py — add `highlights` to the existing Canada destinations
without touching the hand-authored blurbs / fun-facts / tips.

Reads data/canada.json, injects a highlights list per id (and a country_flag
for consistency with the other regions), and writes the file back in place.
Idempotent — safe to re-run.

Run:  python3 tools/enrich_canada.py
"""
import json
import os


def H(*pairs):
    return [{"name": n, "wikipedia_slug": s} for (n, s) in pairs]


HIGHLIGHTS = {
 "niagara-falls": H(
    ("Horseshoe Falls", "Horseshoe_Falls"),
    ("American Falls", "American_Falls"),
    ("Clifton Hill", "Clifton_Hill,_Ontario"),
    ("Niagara Parkway", "Niagara_River")),
 "cn-tower": H(
    ("CN Tower EdgeWalk", "CN_Tower"),
    ("Toronto Harbourfront", "Harbourfront,_Toronto"),
    ("Toronto Islands", "Toronto_Islands"),
    ("Rogers Centre", "Rogers_Centre")),
 "old-quebec": H(
    ("Château Frontenac", "Château_Frontenac"),
    ("Rue du Petit-Champlain", "Petit_Champlain"),
    ("Plains of Abraham", "Plains_of_Abraham"),
    ("The City Walls", "Ramparts_of_Quebec_City")),
 "banff-lake-louise": H(
    ("Lake Louise", "Lake_Louise"),
    ("Moraine Lake", "Moraine_Lake"),
    ("Town of Banff", "Banff,_Alberta"),
    ("Banff Gondola", "Banff_Gondola")),
 "stanley-park": H(
    ("The Seawall", "Stanley_Park"),
    ("Vancouver Aquarium", "Vancouver_Aquarium"),
    ("Lions Gate Bridge", "Lions_Gate_Bridge"),
    ("Brockton Point Totems", "Brockton_Point_Lighthouse")),
 "peggys-cove": H(
    ("Peggys Point Lighthouse", "Peggys_Point_Lighthouse"),
    ("The Granite Boulders", "Peggy's_Cove,_Nova_Scotia"),
    ("St. Margarets Bay", "St._Margarets_Bay")),
 "tofino": H(
    ("Long Beach", "Long_Beach_(Vancouver_Island)"),
    ("Pacific Rim National Park", "Pacific_Rim_National_Park_Reserve"),
    ("Hot Springs Cove", "Maquinna_Marine_Provincial_Park"),
    ("Clayoquot Sound", "Clayoquot_Sound")),
 "churchill": H(
    ("Hudson Bay", "Hudson_Bay"),
    ("Polar Bears", "Polar_bear"),
    ("Northern Lights", "Aurora"),
    ("Tundra Buggy Safari", "Churchill,_Manitoba")),
 "dawson-city": H(
    ("Klondike Gold Rush", "Klondike_Gold_Rush"),
    ("Historic Boardwalk", "Dawson_City"),
    ("Midnight Dome", "Dawson_City")),
 "lunenburg": H(
    ("Old Town Lunenburg", "Lunenburg,_Nova_Scotia"),
    ("Bluenose II", "Bluenose_II"),
    ("Fisheries Museum of the Atlantic", "Fisheries_Museum_of_the_Atlantic")),
 "icefields-parkway": H(
    ("Columbia Icefield", "Columbia_Icefield"),
    ("Peyto Lake", "Peyto_Lake"),
    ("Athabasca Glacier", "Athabasca_Glacier"),
    ("Bow Lake", "Bow_Lake_(Alberta)")),
 "hopewell-rocks": H(
    ("Bay of Fundy", "Bay_of_Fundy"),
    ("The Flowerpot Rocks", "Hopewell_Rocks"),
    ("Ocean Floor Walk", "Tide")),
}


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "data", "canada.json")
    doc = json.load(open(path, encoding="utf-8"))

    n = 0
    for loc in doc["locations"]:
        loc.setdefault("country", "Canada")
        loc.setdefault("country_flag", "🇨🇦")
        if loc["id"] in HIGHLIGHTS:
            loc["highlights"] = HIGHLIGHTS[loc["id"]]
            n += 1

    json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(path, "a", encoding="utf-8").write("\n")
    hl = sum(len(l.get("highlights", [])) for l in doc["locations"])
    print(f"✓ enriched {n}/{len(doc['locations'])} Canada destinations, {hl} highlights")


if __name__ == "__main__":
    main()
