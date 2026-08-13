#!/usr/bin/env python3
"""
build_eurasia.py — the Russia / Ukraine / post-Soviet batch (2026-08).

WHAT WAS WRONG
    Russia had **7 places for 17 million km² and eleven time zones** — Moscow,
    Saint Petersburg, Kazan, Yekaterinburg, Novosibirsk, Irkutsk and Baikal.
    No Pacific, no Arctic, no Caucasus, no Kamchatka, nothing between the Volga
    and the Yenisei. Ukraine had three. And **five whole countries had nothing
    at all**: Belarus, Kazakhstan, Kyrgyzstan, Tajikistan and Turkmenistan — the
    Silk Road trip crossed Central Asia by jumping from Bukhara straight out of
    it, because there was no ground in between to stand on.

    Moscow was worse than thin: it had an **empty `highlights` array**, which
    per `fill_highlights.py` is the same fact as "can never earn a monument
    tab" — `enrich_monuments.py` spends highlights as its search terms, so the
    capital of the largest country on Earth had nothing for the sweep to ask
    about. It had two hand-curated tabs and no way to earn a third.

WHAT THIS DOES
    Adds the new places and fills the skeletons in one pass, across **two**
    region files — `europe.json` for Russia through the Baltics and the Balkans,
    `asia.json` for the Caucasus, the five Central Asian republics and Mongolia.
    That split is the one the atlas already uses (Russia files under Europe for
    browsing, per `build_countries.py`), not a geographic claim.

    Editorial choice is ours. Every **coordinate comes from Wikidata P625** and
    every **slug is resolved live** and stored as the article's canonical title,
    per README "Filling a region out". Nothing here is recalled from memory
    except the prose.

    Re-runnable and additive: an existing place keeps every field it already has
    (and always keeps `walk`/`webcam`/`window`/`monuments` — those belong to the
    scene pipeline, not to us). Only empty fields get filled.

THE NAMESAKE TRAP IS WORSE HERE THAN ANYWHERE
    South America could use one continent-sized box (`SA_BOX`) because every
    new place was inside it. This region cannot: it spans 12°E to 170°W, and its
    place names are the most heavily reused on Earth. **Odessa is in Texas.
    Moscow is in Idaho. Saint Petersburg is in Florida. Vienna, Berlin, Warsaw,
    Kiev and Lebanon are all towns in Ohio.** A box around "Eurasia" would admit
    every one of them that happens to fall inside it, and reject nothing.

    So the guard here is **per-country**: `COUNTRY_BOX` holds a bounding box for
    each of the nineteen countries this batch touches, and a P625 that lands
    outside the box *of the country the record claims* is refused. That is the
    check that catches an American namesake, because Odessa, Texas is not inside
    Ukraine's box — a Eurasia-wide box would never have noticed.

    Russia's box is the one exception that needs saying out loud: it crosses the
    antimeridian at Chukotka, so its longitude test is a two-arc union rather
    than a single min/max span. A naive `-180 <= lng <= 180` on Russia is not a
    test at all.

Run:  python3 tools/build_eurasia.py                # report only
      python3 tools/build_eurasia.py --apply
      python3 tools/build_eurasia.py --refresh      # ignore the slug cache
"""
import argparse
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_wiki import Resolver, haversine

ROOT = Path(__file__).resolve().parent.parent
EUROPE = ROOT / "data" / "europe.json"
ASIA = ROOT / "data" / "asia.json"

# How far a record may sit from its own article's P625 before a human should
# look. An area type legitimately sits far from its own centroid.
FAR_KM = 60.0
AREA_TYPES = {"nature", "desert", "island", "mountain", "region"}

# ---------------------------------------------------------------------------
# THE CURATED CONTENT.
#
# highlights are STRUCTURES, TOWNS AND LANDFORMS ONLY — never a people, a dish,
# a dynasty, an era or a festival. `enrich_monuments.py` spends each one as a
# search term, so "the Cossacks", "borscht", "the Soviet Union" and "Navy Day"
# can only ever return something wrong. Each name below is a thing that stands
# somewhere, so a video of it can exist.
#
# A `None` slug is deliberate: the UI renders highlights as text chips, so a
# name with no link costs nothing and a dead link is rot.
# ---------------------------------------------------------------------------
NEW_EUROPE = {
# ============================== RUSSIA ==============================
"vladivostok": dict(
    name="Vladivostok", slug="Vladivostok", country="Russia",
    region="Primorsky Krai", type="city", tag="famous", emoji="🌉",
    sounds=["ocean-waves.mp3"],
    highlights=[("Russky Bridge", "Russky_Bridge"),
                ("Golden Horn Bay", "Zolotoy_Rog"),
                ("Vladivostok Fortress", "Vladivostok_Fortress"),
                ("Russky Island", "Russky_Island"),
                ("Eagle's Nest Hill", None)],
    blurb="The Pacific end of Russia, built over a ridge above a deep-water "
          "bay that curls back on itself like a horn. It is a naval city first "
          "and a port second, closed to outsiders entirely from 1958 to 1992, "
          "and it looks east rather than west — Seoul and Tokyo are closer than "
          "almost any Russian city of comparable size.",
    fact="The Trans-Siberian's kilometre post here reads 9,288 — the distance "
         "back to Moscow by rail, and the longest single train journey in the "
         "world.",
    tip="Ride the funicular up to Eagle's Nest at dusk: the whole Golden Horn, "
        "both bridges and the naval yards line up below in one frame."),
"murmansk": dict(
    name="Murmansk", slug="Murmansk", country="Russia",
    region="Murmansk Oblast", type="city", tag="hidden", emoji="🌌",
    sounds=["arctic-wind.mp3"],
    highlights=[("Alyosha Monument", "Alyosha_Monument"),
                ("Kola Bay", "Kola_Bay"),
                ("Lenin, the first nuclear icebreaker", "Lenin_(1957_icebreaker)"),
                ("Semyonovskoye Lake", None)],
    blurb="The largest city anywhere above the Arctic Circle, and a port that "
          "never freezes — the last warm breath of the North Atlantic current "
          "reaches this far and keeps the Kola Bay open while the White Sea to "
          "the south locks solid. Founded in 1916, it is also one of the "
          "youngest cities in Russia.",
    fact="The sun does not rise here for about forty days from early December, "
         "and then does not set for two months in summer.",
    tip="The world's first nuclear-powered surface ship, the icebreaker Lenin, "
        "is tied up at the passenger terminal and you can walk her reactor "
        "control room."),
"yakutsk": dict(
    name="Yakutsk", slug="Yakutsk", country="Russia",
    region="Sakha Republic", type="city", tag="hidden", emoji="🥶",
    sounds=["arctic-wind.mp3"],
    highlights=[("Lena River", "Lena_(river)"),
                ("Permafrost Kingdom", None),
                ("Mammoth Museum", None),
                ("Old Town", None)],
    blurb="The coldest city on Earth, built on permafrost 450 m deep on the "
          "left bank of the Lena. Nothing here sits on the ground: the whole "
          "city stands on concrete piles driven into frozen soil, because a "
          "heated building set directly on it would thaw its own foundation "
          "and sink.",
    fact="January averages about −38 °C and the record is −64.4 °C — cold "
         "enough that exhaled breath falls as ice crystals with an audible "
         "rustle locals call the whisper of the stars.",
    tip="There is still no bridge over the Lena. In summer you cross by ferry, "
        "in winter you drive over the river itself, and for six weeks each "
        "spring and autumn you cannot cross at all."),
"lena-pillars": dict(
    name="Lena Pillars", slug="Lena Pillars", country="Russia",
    region="Sakha Republic", type="nature", tag="hidden", emoji="🪨",
    sounds=["wilderness.mp3"],
    highlights=[("Lena River", "Lena_(river)"),
                ("Sinsky Pillars", None),
                ("Tukulan sands", None)],
    blurb="A wall of limestone columns up to 100 m tall standing along the "
          "Lena for roughly 40 km, cut by 400,000 years of freeze and thaw in "
          "a climate that swings 100 degrees between winter and summer. The "
          "rock itself is Cambrian — laid down when the first complex animals "
          "appeared.",
    fact="Inside the same park are the Tukulan — real sand dunes, drifting in "
         "the middle of Siberia at 61° north, only a few hundred kilometres "
         "from permafrost.",
    tip="The pillars only read at their true scale from the water, which is "
        "why every visit here is a river trip rather than a walk."),
"petropavlovsk-kamchatsky": dict(
    name="Petropavlovsk-Kamchatsky", slug="Petropavlovsk-Kamchatsky",
    country="Russia", region="Kamchatka Krai", type="coastal", tag="famous",
    emoji="🌋", sounds=["ocean-waves.mp3"],
    highlights=[("Avacha Bay", "Avacha_Bay"),
                ("Koryaksky", "Koryaksky"),
                ("Avachinsky", "Avachinsky"),
                ("Vilyuchik", "Vilyuchik")],
    blurb="A city of 180,000 on a Pacific bay with three active volcanoes "
          "standing over the rooftops, on a peninsula with no road to the rest "
          "of the country — everything and everyone arrives by ship or plane. "
          "The bay behind it is one of the largest natural harbours in the "
          "world and could hold any fleet afloat.",
    fact="Kamchatka has around 300 volcanoes, 29 of them active, packed into a "
         "peninsula the size of Japan and sitting on the busiest corner of the "
         "Pacific Ring of Fire.",
    tip="Locals call the two cones behind the city 'the home volcanoes'. On a "
        "clear morning Koryaksky is visible from the bus stops downtown."),
"valley-of-geysers": dict(
    name="Valley of Geysers", slug="Valley of Geysers", country="Russia",
    region="Kamchatka Krai", type="nature", tag="hidden", emoji="♨️",
    sounds=["wilderness.mp3"],
    highlights=[("Kronotsky Nature Reserve", "Kronotsky_Nature_Reserve"),
                ("Kronotsky Volcano", "Kronotsky"),
                ("Geyzernaya River", None)],
    blurb="The second-largest concentration of geysers on the planet, packed "
          "into a six-kilometre river canyon inside a reserve with no roads "
          "into it. It was only found in 1941, by a hydrologist following a "
          "warm tributary upstream on foot.",
    fact="A landslide in 2007 buried two thirds of the valley under rock and "
         "dammed the river; a mudflow in 2014 partly reopened it. The geysers "
         "are still rearranging themselves.",
    tip="Access is by helicopter from Yelizovo and strictly capped — this is a "
        "place almost everyone who knows it has only ever seen on film."),
"kizhi": dict(
    name="Kizhi", slug="Kizhi Pogost", country="Russia",
    region="Republic of Karelia", type="history", tag="hidden", emoji="⛪",
    sounds=["wilderness.mp3"],
    highlights=[("Church of the Transfiguration", None),
                ("Lake Onega", "Lake_Onega"),
                ("Kizhi Island", "Kizhi_Island")],
    blurb="A wooden church of twenty-two silver aspen domes on a long thin "
          "island in Lake Onega, raised in 1714 without a single nail in its "
          "structure — the joinery alone holds it up. Around it stand a second "
          "church, a bell tower and a fence, the whole enclosure moved here "
          "log by log from across Karelia.",
    fact="The Transfiguration church was dismantled and rebuilt from the "
         "inside out over four decades, its frame lifted on jacks so rotten "
         "logs could be swapped without taking the domes down.",
    tip="Come by hydrofoil from Petrozavodsk. The island is car-free and about "
        "7 km long, and the crowds stay within 300 m of the jetty."),
"veliky-novgorod": dict(
    name="Veliky Novgorod", slug="Veliky Novgorod", country="Russia",
    region="Novgorod Oblast", type="history", tag="hidden", emoji="🏰",
    sounds=["european-plaza.mp3"],
    highlights=[("Novgorod Detinets", "Novgorod_Detinets"),
                ("Saint Sophia Cathedral", "Cathedral_of_St._Sophia,_Novgorod"),
                ("Yaroslav's Court", "Yaroslav's_Court"),
                ("Millennium of Russia", "Millennium_of_Russia"),
                ("Yuriev Monastery", "Yuriev_Monastery")],
    blurb="For three centuries this was a merchant republic that elected its "
          "own princes and could dismiss them, ran a parliament by public "
          "assembly, and traded as the eastern anchor of the Hanseatic League. "
          "Mongol armies never reached it, so its eleventh-century churches "
          "are still standing.",
    fact="More than a thousand letters written on birch bark have been dug out "
          "of the waterlogged soil here — laundry lists, love notes, a boy's "
          "schoolwork — proof that ordinary medieval townspeople could read.",
    tip="Cross the footbridge to Yaroslav's Court at low sun; the row of "
        "merchant churches on the far bank is the skyline the Hansa saw."),
"suzdal": dict(
    name="Suzdal", slug="Suzdal", country="Russia",
    region="Vladimir Oblast", type="village", tag="hidden", emoji="🧅",
    sounds=["european-plaza.mp3"],
    highlights=[("Suzdal Kremlin", "Suzdal_Kremlin"),
                ("Cathedral of the Nativity", "Cathedral_of_the_Nativity,_Suzdal"),
                ("Monastery of Saint Euthymius", "Monastery_of_Saint_Euthymius"),
                ("Intercession Monastery", None),
                ("Kamenka River", None)],
    blurb="A town of 9,000 people with more than forty churches and five "
          "monasteries in it, and a local law that has kept anything taller "
          "than two storeys out since the 1960s. The Golden Ring's least "
          "compromised town: cows still graze the meadow inside the bend of "
          "the river, in sight of the cathedral.",
    fact="Suzdal was passed over by the railway in the nineteenth century and "
         "by industry in the twentieth, which is exactly why it survived — the "
         "line went to Vladimir instead, 35 km south.",
    tip="Walk the Kamenka's water meadow rather than the main street: from "
        "down there the whole town is domes above a treeline, with no wires."),
"vladimir": dict(
    name="Vladimir", slug="Vladimir, Russia", country="Russia",
    region="Vladimir Oblast", type="history", tag="hidden", emoji="⛪",
    sounds=["city-hum.mp3"],
    highlights=[("Golden Gate", "Golden_Gate,_Vladimir"),
                ("Dormition Cathedral", "Dormition_Cathedral,_Vladimir"),
                ("Cathedral of Saint Demetrius", "Cathedral_of_Saint_Demetrius"),
                ("Church of the Intercession on the Nerl", "Church_of_the_Intercession_on_the_Nerl")],
    blurb="The capital of Rus before Moscow was anything, on a bluff above the "
          "Klyazma. Its twelfth-century white-stone cathedrals set the pattern "
          "every Russian church copied afterwards, and the frescoes inside the "
          "Dormition include Andrei Rublev's Last Judgement, painted in 1408.",
    fact="The Dormition Cathedral was the model Moscow's Kremlin cathedral was "
         "explicitly commissioned to imitate — the capital moved, and took the "
         "architecture with it.",
    tip="The Church of the Intercession on the Nerl stands alone in a flood "
        "meadow 10 km east, reached only on foot across a field. It is the "
        "most photographed building in Russia that has no road to it."),
"nizhny-novgorod": dict(
    name="Nizhny Novgorod", slug="Nizhny Novgorod", country="Russia",
    region="Nizhny Novgorod Oblast", type="city", tag="hidden", emoji="🏰",
    sounds=["city-hum.mp3"],
    highlights=[("Nizhny Novgorod Kremlin", "Nizhny_Novgorod_Kremlin"),
                ("Chkalov Stairs", "Chkalov_Stairs"),
                ("Bolshaya Pokrovskaya Street", None),
                ("Volga River", "Volga"),
                ("Rukavishnikov Mansion", None)],
    blurb="Russia's fifth city, set where the Oka runs into the Volga on a "
          "high right bank, with a red-brick kremlin along the crest and the "
          "whole confluence spread out below it. It was the empire's trade "
          "fair for a century, then a closed defence city for forty years.",
    fact="The Chkalov Staircase down to the Volga has 560 steps in a figure "
         "of eight — it was built by German prisoners of war and finished in "
         "1949, and it is the longest staircase on any Russian riverbank.",
    tip="Walk the kremlin wall itself. The circuit reopened whole in 2021 for "
        "the first time since the seventeenth century, and it looks straight "
        "down onto the confluence."),
"volgograd": dict(
    name="Volgograd", slug="Volgograd", country="Russia",
    region="Volgograd Oblast", type="city", tag="hidden", emoji="🗿",
    sounds=["city-hum.mp3"],
    highlights=[("Mamayev Kurgan", "Mamayev_Kurgan"),
                ("The Motherland Calls", "The_Motherland_Calls"),
                ("Pavlov's House", "Pavlov's_House"),
                ("Volga River", "Volga")],
    blurb="A city strung 60 km along one bank of the Volga and almost none of "
          "the other — the longest city in Russia, and one rebuilt from "
          "essentially nothing. As Stalingrad it was fought over street by "
          "street through the winter of 1942, and the battle turned the "
          "Eastern Front.",
    fact="The Motherland Calls stood as the tallest statue in the world when "
         "it was finished in 1967. It is unanchored — 8,000 tonnes of concrete "
         "held down by its own weight alone.",
    tip="A ruined mill by the riverfront was deliberately left exactly as the "
        "fighting ended, shell holes and all, as the one un-restored building "
        "in the city."),
"kaliningrad": dict(
    name="Kaliningrad", slug="Kaliningrad", country="Russia",
    region="Kaliningrad Oblast", type="city", tag="hidden", emoji="🐟",
    sounds=["city-hum.mp3"],
    highlights=[("Königsberg Cathedral", "Königsberg_Cathedral"),
                ("Fish Village", None),
                ("Amber Museum", "Kaliningrad_Amber_Museum"),
                ("Curonian Spit", "Curonian_Spit"),
                ("Brandenburg Gate", None)],
    blurb="Russia without a Russian border: an exclave on the Baltic between "
          "Poland and Lithuania, and until 1945 this was Königsberg, capital "
          "of East Prussia. The old city was bombed and then rebuilt as "
          "something else entirely, so the surviving German fragments stand in "
          "isolation among Soviet blocks.",
    fact="Around 90% of the world's amber comes out of one open pit 40 km up "
          "the coast at Yantarny, where it is washed from a blue clay seam "
          "45 million years old.",
    tip="Kant is buried against the cathedral's north wall, in the one corner "
        "of the old town that was rebuilt — he taught here his whole life and "
        "reportedly never travelled more than 150 km from the city."),
"sochi": dict(
    name="Sochi", slug="Sochi", country="Russia",
    region="Krasnodar Krai", type="coastal", tag="famous", emoji="🌴",
    sounds=["ocean-waves.mp3"],
    highlights=[("Krasnaya Polyana", "Krasnaya_Polyana,_Krasnodar_Krai"),
                ("Sochi Arboretum", "Sochi_Arboretum"),
                ("Olympic Park", "Sochi_Olympic_Park"),
                ("Mount Akhun", None),
                ("Agura Waterfalls", None)],
    blurb="Russia's subtropics — a 145 km strip of humid coast pressed between "
          "the Black Sea and the Caucasus, where palms and tea plantations sit "
          "an hour's drive below a snowline. It has been the country's summer "
          "resort since the 1930s and hosted a Winter Olympics in 2014.",
    fact="Sochi is the longest city in Europe and one of the few places on "
          "Earth where you can swim in the sea and ski in the mountains on the "
          "same day, in the same weather system.",
    tip="Take the old Stalin-era Riviera side rather than the Olympic coast: "
        "the arboretum's cable car ends in a terrace of Himalayan cedars above "
        "the whole bay."),
"mount-elbrus": dict(
    name="Mount Elbrus", slug="Mount Elbrus", country="Russia",
    region="Kabardino-Balkaria", type="mountain", tag="famous", emoji="🏔️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Baksan Valley", None),
                ("Terskol", None),
                ("Caucasus Mountains", "Caucasus_Mountains")],
    blurb="The highest mountain in Europe at 5,642 m, and a dormant volcano "
          "rather than a fold in the range — two cones on one massif, capped "
          "by 22 glaciers that feed the rivers of the whole north Caucasus. "
          "The cable car up its southern flank is the highest in Europe.",
    fact="Whether Elbrus counts as European at all depends on where you draw "
          "the continental divide through the Caucasus, which is why it is "
          "both 'the roof of Europe' and, to some geographers, in Asia.",
    tip="The Barrels — a cluster of converted fuel tanks at 3,800 m — are "
        "still where most climbers sleep before a summit attempt."),
"derbent": dict(
    name="Derbent", slug="Derbent", country="Russia",
    region="Republic of Dagestan", type="history", tag="hidden", emoji="🏯",
    sounds=["city-hum.mp3"],
    highlights=[("Naryn-Kala", "Naryn-Kala"),
                ("Juma Mosque", "Juma_Mosque_of_Derbent"),
                ("Caspian Sea", "Caspian_Sea")],
    blurb="The oldest continuously inhabited city in Russia, wedged into a "
          "three-kilometre gap between the Caucasus and the Caspian — the one "
          "land gate between the steppe and Persia. The Sasanians walled the "
          "gap shut in the sixth century and the walls are still standing, "
          "running from the citadel down into the sea.",
    fact="Its name is Persian for 'closed gates', and its Friday mosque, "
          "founded in 733, is the oldest in Russia and one of the oldest "
          "anywhere in the former Soviet Union.",
    tip="The old quarters between the two parallel walls are still laid out on "
        "the medieval plan, with the alleys narrowing as they climb."),
"solovetsky-islands": dict(
    name="Solovetsky Islands", slug="Solovetsky Islands", country="Russia",
    region="Arkhangelsk Oblast", type="island", tag="hidden", emoji="⛪",
    sounds=["ocean-waves.mp3"],
    highlights=[("Solovetsky Monastery", "Solovetsky_Monastery"),
                ("White Sea", "White_Sea"),
                ("Bolshoy Zayatsky Island", "Bolshoy_Zayatsky_Island")],
    blurb="A monastery fortress of house-sized granite boulders on an "
          "archipelago in the White Sea, 165 km from the Arctic Circle. It was "
          "a spiritual centre for four centuries, and then, from 1923, the "
          "prototype of the Soviet labour camp system — the first island of "
          "the Gulag, in the phrase that named the rest.",
    fact="The islands carry Bronze Age stone labyrinths whose purpose nobody "
          "has settled, and a sixteenth-century canal system dug by monks that "
          "still links the freshwater lakes.",
    tip="Boats run from Kem on the mainland in the short ice-free season only; "
        "for most of the year the archipelago is reachable by air or not at "
        "all."),
"arkhangelsk": dict(
    name="Arkhangelsk", slug="Arkhangelsk", country="Russia",
    region="Arkhangelsk Oblast", type="city", tag="hidden", emoji="🪵",
    sounds=["city-hum.mp3"],
    highlights=[("Malye Korely", "Malye_Korely"),
                ("Northern Dvina", "Northern_Dvina"),
                ("Chumbarova-Luchinskogo Avenue", None),
                ("Solombala", None)],
    blurb="Russia's first seaport, at the mouth of the Northern Dvina on the "
          "White Sea, and for a century and a half its only one — everything "
          "the country traded with Europe passed through here until Peter the "
          "Great built Saint Petersburg and deliberately strangled it.",
    fact="Malye Korely, just upriver, is an open-air museum of northern wooden "
          "architecture: over a hundred chapels, windmills, barns and houses "
          "moved log by log from villages across the region.",
    tip="Timber is still the city's material and its trade — whole streets of "
          "two-storey wooden apartment houses stand on the sand, slowly and "
          "visibly leaning."),
"ulan-ude": dict(
    name="Ulan-Ude", slug="Ulan-Ude", country="Russia",
    region="Republic of Buryatia", type="city", tag="hidden", emoji="☸️",
    sounds=["city-hum.mp3"],
    highlights=[("Ivolginsky Datsan", "Ivolginsky_Datsan"),
                ("Rinpoche Bagsha", None),
                ("Selenga River", "Selenga_River"),
                ("Odigitrievsky Cathedral", None)],
    blurb="The capital of Buryatia, where the Trans-Mongolian branches south "
          "off the Trans-Siberian and runs for Ulaanbaatar and Beijing. The "
          "Buryats are a Mongol people and this is the centre of Buddhism in "
          "Russia, so the city reads as Siberian and Central Asian at once.",
    fact="The main square holds the largest Lenin head in the world — 7.7 m "
          "tall, 42 tonnes, and nothing else of him at all.",
    tip="Ivolginsky Datsan, 35 km out, is the seat of Russian Buddhism and "
        "keeps the body of a lama who died in 1927 in the lotus position he "
        "was buried in."),
"krasnoyarsk": dict(
    name="Krasnoyarsk", slug="Krasnoyarsk", country="Russia",
    region="Krasnoyarsk Krai", type="city", tag="hidden", emoji="🪨",
    sounds=["city-hum.mp3"],
    highlights=[("Stolby Nature Sanctuary", "Stolby_Nature_Sanctuary"),
                ("Yenisei River", "Yenisei"),
                ("Paraskeva Pyatnitsa Chapel", "Paraskeva_Pyatnitsa_Chapel"),
                ("Karaulnaya Mountain", None)],
    blurb="A million people on the Yenisei with a taiga nature reserve "
          "starting at the edge of the suburbs — the Stolby, a scatter of "
          "granite pillars in dense forest that the city has been free-climbing "
          "without ropes for a century and a half, in its own local style.",
    fact="The little chapel on the hill above town is the building on the "
          "Russian ten-rouble note, and the river below it does not freeze "
          "downstream of the dam even at −40 °C.",
    tip="Take the road out to Stolby on a weekday. The nearest pillars are a "
        "7 km walk from the gate and the forest closes over the city noise "
        "within the first kilometre."),
"pskov": dict(
    name="Pskov", slug="Pskov", country="Russia",
    region="Pskov Oblast", type="history", tag="hidden", emoji="🏰",
    sounds=["european-plaza.mp3"],
    highlights=[("Pskov Krom", "Pskov_Krom"),
                ("Trinity Cathedral", "Trinity_Cathedral,_Pskov"),
                ("Mirozhsky Monastery", "Mirozhsky_Monastery"),
                ("Velikaya River", "Velikaya_River")],
    blurb="A fortress city on the western frontier, sister republic to "
          "Novgorod and for centuries the shield that met whatever came from "
          "the Baltic first. Its churches are small, white and heavy-walled — "
          "a local school of building that looks nothing like Moscow's.",
    fact="Ten of Pskov's churches were added to the World Heritage list in "
          "2019 as a single entry, recognised as a distinct architectural "
          "tradition rather than ten separate buildings.",
    tip="The Mirozhsky Monastery holds twelfth-century frescoes painted by "
        "Byzantine Greeks — they survived because they were plastered over for "
        "six hundred years."),
"vyborg": dict(
    name="Vyborg", slug="Vyborg", country="Russia",
    region="Leningrad Oblast", type="history", tag="hidden", emoji="🗼",
    sounds=["european-plaza.mp3"],
    highlights=[("Vyborg Castle", "Vyborg_Castle"),
                ("Monrepos Park", "Monrepos_Park"),
                ("Round Tower", None),
                ("Vyborg Library", "Vyborg_Library")],
    blurb="A Swedish castle town that became Finnish and then Soviet, 30 km "
          "from the border and unlike anywhere else in Russia — cobbled lanes, "
          "a granite Hanseatic core and a thirteenth-century keep on its own "
          "islet, all of it changing hands four times in one century.",
    fact="Alvar Aalto's 1935 library here is a landmark of modernism; it sat "
          "half-ruined for decades and was restored by a joint Finnish-Russian "
          "team that finished in 2013.",
    tip="Monrepos, on the northern edge, is a romantic rock park of pines "
        "growing straight out of glacier-scoured granite along the bay."),
"rostov-on-don": dict(
    name="Rostov-on-Don", slug="Rostov-on-Don", country="Russia",
    region="Rostov Oblast", type="city", tag="hidden", emoji="🐟",
    sounds=["city-hum.mp3"],
    highlights=[("Don River", "Don_(river)"),
                ("Bolshaya Sadovaya Street", None),
                ("Central Market", None),
                ("Left Bank", None)],
    blurb="The gateway between Russia and the Caucasus, on the last stretch of "
          "the Don before the Sea of Azov. It grew as a customs post and a "
          "Cossack river port, and it still runs on the river and the market — "
          "a southern, mercantile, un-Moscow kind of city.",
    fact="Rostov sits at the centre of the historic lands of the Don Cossacks, "
          "and the city's own dialect and food are closer to the steppe than "
          "to anything north of it.",
    tip="The left bank of the Don is a long sandbank of grill shacks and "
        "riverside cafés; the city crosses over to it in summer and stays "
        "until the light goes."),
"taganrog": dict(
    name="Taganrog", slug="Taganrog", country="Russia",
    region="Rostov Oblast", type="city", tag="hidden", emoji="⚓",
    sounds=["city-hum.mp3", "ocean-waves.mp3"],
    highlights=[("Depaldo Stairs", "Depaldo_Stairs"),
                ("Pushkin Embankment", "Pushkin_Embankment_in_Taganrog"),
                ("Alferaki Palace", "Alferaki_Palace"),
                ("Chekhov Gymnasium", "Chekhov_Gymnasium"),
                ("Taganrog Fortress", "Taganrog_Fortress"),
                ("Taganrog Bay", "Taganrog_Bay")],
    blurb="Russia's first naval base, laid out by Peter the Great in 1698 on a "
          "cape sticking into the Sea of Azov — a purpose-built port two "
          "decades older than Saint Petersburg. Greek and Italian merchants "
          "made the money and built the town, which is why a provincial "
          "Russian port has an Italian architect's stone staircase running "
          "down to the water and a palace on Frunze Street.",
    fact="The Depaldo Stairs of 1823 predate Odesa's far more famous Potemkin "
          "Steps by two decades, and use the same trick: the flights narrow "
          "as they descend, so the staircase looks the same width the whole "
          "way down from the top and impossibly long from the bottom.",
    tip="Go down the stairs to Pushkin Embankment in the evening, when the "
        "whole town walks the seafront and the Azov — the shallowest sea in "
        "the world, barely 14 m at its deepest — goes flat and silver."),
"mount-belukha": dict(
    name="Mount Belukha", slug="Belukha Mountain", country="Russia",
    region="Altai Republic", type="mountain", tag="hidden", emoji="🏔️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Katun River", "Katun_River"),
                ("Akkem Lake", None),
                ("Altai Mountains", "Altai_Mountains")],
    blurb="The high point of Siberia at 4,506 m, a twin-peaked massif where "
          "Russia, Kazakhstan, China and Mongolia nearly meet. The Katun rises "
          "off its glaciers and runs milky green; the Altai people hold the "
          "mountain sacred and its upper slopes are closed to climbing on "
          "those grounds during certain seasons.",
    fact="Belukha is almost exactly equidistant from the Arctic, the Pacific, "
          "the Indian Ocean and the Atlantic — the furthest point on land from "
          "any ocean is not far away.",
    tip="The standard approach is a two-day walk up the Akkem valley to a lake "
        "directly under the north face, which stays frozen into June."),

# ============================== UKRAINE ==============================
"kharkiv": dict(
    name="Kharkiv", slug="Kharkiv", country="Ukraine",
    region="Kharkiv Oblast", type="city", tag="hidden", emoji="🏛️",
    sounds=["city-hum.mp3"],
    highlights=[("Freedom Square", "Freedom_Square_(Kharkiv)"),
                ("Derzhprom", "Derzhprom"),
                ("Shevchenko Garden", None),
                ("Annunciation Cathedral", "Annunciation_Cathedral,_Kharkiv"),
                ("Mirror Stream", None)],
    blurb="Ukraine's second city and its first Soviet capital, a university "
          "and engineering town of wide avenues 30 km from the Russian border. "
          "Its centre is a constructivist experiment: Derzhprom, finished in "
          "1928, was the first Soviet skyscraper and one of the first "
          "reinforced-concrete high-rises in Europe.",
    fact="Freedom Square is among the largest city squares in Europe — big "
         "enough that the buildings around it were designed to be read from "
         "the far side rather than from the pavement.",
    tip="Kharkiv has been shelled repeatedly since 2022 and Derzhprom itself "
        "was damaged in 2022 and again later; the footage here predates much "
        "of that, and the city is not a place to visit at present."),
"chernihiv": dict(
    name="Chernihiv", slug="Chernihiv", country="Ukraine",
    region="Chernihiv Oblast", type="history", tag="hidden", emoji="⛪",
    sounds=["european-plaza.mp3"],
    highlights=[("Transfiguration Cathedral", "Transfiguration_Cathedral,_Chernihiv"),
                ("Catherine's Church", "Catherine's_Church,_Chernihiv"),
                ("Antoniy Caves", None),
                ("Desna River", "Desna_(river)")],
    blurb="One of the oldest cities of Kievan Rus, on the Desna north of Kyiv, "
          "with a group of eleventh- and twelfth-century churches that survived "
          "the Mongols, the wars and the twentieth century — the densest "
          "concentration of pre-Mongol architecture anywhere in Ukraine.",
    fact="The Transfiguration Cathedral was begun around 1030 and is one of "
         "the oldest surviving buildings in the country, older than any "
         "standing church in Moscow by three centuries.",
    tip="Chernihiv was encircled and heavily bombarded in the spring of 2022 "
        "and parts of the centre were destroyed; the medieval core largely "
        "stands, but the city is still on a frontline oblast."),
"kamianets-podilskyi": dict(
    name="Kamianets-Podilskyi", slug="Kamianets-Podilskyi", country="Ukraine",
    region="Khmelnytskyi Oblast", type="history", tag="hidden", emoji="🏰",
    sounds=["european-plaza.mp3"],
    highlights=[("Kamianets-Podilskyi Castle", "Kamianets-Podilskyi_Castle"),
                ("Smotrych River", "Smotrych_River"),
                ("Cathedral of Saints Peter and Paul", None),
                ("Turkish Bridge", None)],
    blurb="An old town standing on a rock island inside a loop of canyon — the "
          "Smotrych has cut a 40 m gorge in an almost complete circle, leaving "
          "the medieval centre on a natural plinth with one narrow neck, and a "
          "castle guarding it. Poles, Ottomans, Armenians and Ruthenians all "
          "built here.",
    fact="Its cathedral carries a minaret: the Ottomans added one when they "
          "held the town in the 1670s, and when it returned to Poland a statue "
          "of the Virgin was simply placed on top rather than pulling it down.",
    tip="The view that explains the place is from the canyon floor, on the "
        "path that runs the whole ring below the town walls."),
"chernivtsi": dict(
    name="Chernivtsi", slug="Chernivtsi", country="Ukraine",
    region="Chernivtsi Oblast", type="history", tag="hidden", emoji="🎓",
    sounds=["european-plaza.mp3"],
    highlights=[("Residence of Bukovinian and Dalmatian Metropolitans",
                 "Residence_of_Bukovinian_and_Dalmatian_Metropolitans"),
                ("Chernivtsi University", "Chernivtsi_University"),
                ("Olha Kobylianska Street", None),
                ("Central Square", None)],
    blurb="The capital of Bukovina, Habsburg from 1775 to 1918 and built to "
          "look it — a small central-European city of ochre facades far from "
          "any border it now sits near. Its university occupies a red-brick "
          "metropolitan's residence that mixes Byzantine, Moorish and Gothic "
          "on one roofline.",
    fact="Before 1918 the city ran in four languages at once — German, "
          "Romanian, Ukrainian and Yiddish — and was known as 'little Vienna' "
          "by people who had been to both.",
    tip="The residence's courtyard is open even when the halls are not; the "
        "roof tiles are laid in geometric patterns you can only read from "
        "inside it."),
"uzhhorod": dict(
    name="Uzhhorod", slug="Uzhhorod", country="Ukraine",
    region="Zakarpattia Oblast", type="city", tag="hidden", emoji="🌸",
    sounds=["european-plaza.mp3"],
    highlights=[("Uzhhorod Castle", "Uzhhorod_Castle"),
                ("Transcarpathian Museum of Folk Architecture", None),
                ("Uzh River", "Uzh"),
                ("Cherry blossom alley", None)],
    blurb="Ukraine's westernmost city, over the Carpathians in Transcarpathia "
          "and closer to Budapest than to Kyiv. It has been Hungarian, "
          "Czechoslovak, Soviet and Ukrainian inside a century, and the mix "
          "shows in a small, low-rise centre along both banks of the Uzh.",
    fact="Its riverside linden alley is one of the longest in Europe, and the "
         "parallel avenue of Japanese cherries turns the embankment pink for "
         "about ten days each spring.",
    tip="Transcarpathia stayed out of the fighting and became a refuge region "
        "after 2022; the city's population swelled with people displaced from "
        "the east."),
"dnipro": dict(
    name="Dnipro", slug="Dnipro", country="Ukraine",
    region="Dnipropetrovsk Oblast", type="city", tag="hidden", emoji="🌉",
    sounds=["city-hum.mp3"],
    highlights=[("Dnieper", "Dnieper"),
                ("Monastyrskyi Island", None),
                ("Menorah Center", "Menorah_Center,_Dnipro"),
                ("Yavornytskoho Avenue", None)],
    blurb="A steel and rocket city on a wide bend of the Dnieper, closed to "
          "foreigners until 1987 because it built intercontinental missiles. "
          "Its long central avenue and its embankment — one of the longest in "
          "Europe — give it a scale that feels larger than its million people.",
    fact="The Menorah Center beside the old Golden Rose synagogue is one of "
         "the largest Jewish community complexes in the world, seven towers "
         "arranged as a candelabrum.",
    tip="Since 2022 Dnipro has been the main medical and logistics hub for the "
        "eastern front, and it has been struck by long-range missiles more "
        "than once."),
"poltava": dict(
    name="Poltava", slug="Poltava", country="Ukraine",
    region="Poltava Oblast", type="history", tag="hidden", emoji="🌻",
    sounds=["european-plaza.mp3"],
    highlights=[("Round Square", None),
                ("Holy Cross Monastery", "Holy_Cross_Exaltation_Monastery,_Poltava"),
                ("Vorskla River", "Vorskla"),
                ("Poltava Museum of Local Lore", None)],
    blurb="A green provincial capital on the Vorskla that gave its name to the "
          "1709 battle where Peter the Great broke Charles XII of Sweden and "
          "ended Swedish power in Europe. Its centre is an unusually complete "
          "circle of classical buildings around a single column.",
    fact="Poltava is the heartland of the Ukrainian literary language — the "
         "dialect spoken around here was the one nineteenth-century writers "
         "standardised into modern literary Ukrainian.",
    tip="The Round Square is a genuine circle 375 m across, laid out in 1805, "
        "and every street in the old centre runs into it."),
"uman": dict(
    name="Uman", slug="Uman", country="Ukraine",
    region="Cherkasy Oblast", type="history", tag="hidden", emoji="🌳",
    sounds=["waterfall.mp3"],
    highlights=[("Sofiyivka Park", "Sofiyivka_Park"),
                ("Grave of Nachman of Breslov", None),
                ("Kamianka River", None)],
    blurb="A small town in central Ukraine with one of the great landscape "
          "gardens of Europe in it — Sofiyivka, laid out in the 1790s by a "
          "Polish magnate as a gift to his wife, with granite grottoes, "
          "waterfalls and an underground river you travel by boat.",
    fact="Uman is also the burial place of Rabbi Nachman of Breslov, and tens "
         "of thousands of Hasidic pilgrims travel here every Rosh Hashanah — "
         "a pilgrimage that continued even through the war years.",
    tip="The park's underground stretch, the Acheron, is a 220 m tunnel you "
        "row through in the dark before emerging into the lake."),
"chernobyl": dict(
    name="Chernobyl & Pripyat", slug="Chernobyl Exclusion Zone",
    country="Ukraine", region="Kyiv Oblast", type="ruin", tag="famous",
    emoji="☢️", sounds=["wilderness.mp3"],
    highlights=[("Pripyat", "Pripyat"),
                ("Chernobyl Nuclear Power Plant", "Chernobyl_Nuclear_Power_Plant"),
                ("New Safe Confinement", "New_Safe_Confinement"),
                ("Duga radar", "Duga_radar"),
                ("Red Forest", "Red_Forest")],
    blurb="A 2,600 km² closed zone around the reactor that exploded on 26 "
          "April 1986, and inside it Pripyat — a city of 49,000 evacuated in "
          "three hours and never reoccupied. Forty years on the concrete is "
          "coming apart under trees, and the wildlife that moved into the "
          "emptiness is the densest in the region.",
    fact="The reactor is now sealed under the New Safe Confinement, a 36,000 "
         "tonne arch slid into place over the ruin in 2016 — the largest "
         "moveable land structure ever built. A drone strike damaged its outer "
         "skin in February 2025.",
    tip="Russian forces occupied the zone in 2022 and dug trenches in "
        "contaminated ground; tourist access has been suspended since, and "
        "nothing here is currently open to visitors."),
"carpathians-ukraine": dict(
    name="Ukrainian Carpathians", slug="Ukrainian Carpathians",
    country="Ukraine", region="Ivano-Frankivsk Oblast", type="mountain",
    tag="hidden", emoji="⛰️", sounds=["mountain-wind.mp3"],
    highlights=[("Hoverla", "Hoverla"),
                ("Yaremche", "Yaremche"),
                ("Bukovel", "Bukovel"),
                ("Synevyr", "Lake_Synevyr"),
                ("Carpathian Biosphere Reserve", "Carpathian_Biosphere_Reserve")],
    blurb="The soft green end of the Carpathian arc, rounded rather than "
          "alpine, with wooden churches on the ridges and Hutsul villages in "
          "the valleys. Hoverla, the country's high point, is 2,061 m — a walk "
          "rather than a climb, and a national pilgrimage of sorts.",
    fact="Some of the last primeval beech forest in Europe stands here, on the "
         "World Heritage list as part of a single site shared between eighteen "
         "countries.",
    tip="Lake Synevyr sits at 989 m in a bowl of spruce with no inflow you can "
        "see — it was dammed by a landslide about 10,000 years ago."),

# ============================== BELARUS ==============================
"minsk": dict(
    name="Minsk", slug="Minsk", country="Belarus", region="Minsk Region",
    type="city", tag="famous", emoji="🏛️", sounds=["city-hum.mp3"],
    highlights=[("Independence Avenue", "Independence_Avenue_(Minsk)"),
                ("Victory Square", "Victory_Square,_Minsk"),
                ("National Library of Belarus", "National_Library_of_Belarus"),
                ("Trinity Suburb", "Trinity_Suburb"),
                ("Island of Tears", None)],
    blurb="A capital rebuilt almost entirely after 1944, when the retreating "
          "front left perhaps a fifth of it standing — so the centre is a "
          "single sustained work of Stalinist planning, 15 km of colonnaded "
          "avenue laid out in one go. It is the most complete such ensemble "
          "anywhere, and unusually clean and quiet for its size.",
    fact="The National Library is a 72 m glass rhombicuboctahedron that lights "
         "up as an animated screen after dark, and has an observation deck on "
         "top of the reading rooms.",
    tip="Trinity Hill is the one pocket of pre-war city left on the Svislach — "
        "a few blocks of nineteenth-century houses kept as a reminder of what "
        "the rest looked like."),
"mir-castle": dict(
    name="Mir Castle", slug="Mir Castle Complex", country="Belarus",
    region="Grodno Region", type="history", tag="hidden", emoji="🏰",
    sounds=["wilderness.mp3"],
    highlights=[("Mir, Belarus", "Mir,_Belarus"),
                ("Radziwiłł family chapel", None),
                ("Castle park", None)],
    blurb="A sixteenth-century brick castle on the flat Belarusian plain, five "
          "towers around a courtyard, Gothic in its bones with Renaissance "
          "floors added on top by the Radziwiłłs. It survived being a fortress, "
          "a ruin, a Nazi ghetto and a block of flats before it was restored.",
    fact="The brickwork is deliberately patterned — bands of ochre plaster and "
         "red brick that make the towers read as striped from a distance, a "
         "local trick called Belarusian Gothic.",
    tip="The pond on the south side was dug so the castle would have a "
        "reflection; stand at its far bank for the view the builders intended."),
"nesvizh": dict(
    name="Nesvizh", slug="Nesvizh Castle", country="Belarus",
    region="Minsk Region", type="history", tag="hidden", emoji="👑",
    sounds=["wilderness.mp3"],
    highlights=[("Corpus Christi Church", "Corpus_Christi_Church,_Nesvizh"),
                ("Nesvizh", "Nesvizh"),
                ("Castle park", None)],
    blurb="The seat of the Radziwiłłs, the richest magnate family of the "
          "Polish-Lithuanian Commonwealth, 30 km from Mir — a palace rather "
          "than a fortress, wrapped in earthworks and moats and set in a park "
          "of five landscaped lakes.",
    fact="Its Corpus Christi church, consecrated in 1593, was the first Baroque "
         "building in eastern Europe and the family's crypt underneath holds "
         "over seventy Radziwiłłs.",
    tip="The park is free and enormous, and the palace only makes sense from "
        "across the water — the approach was designed as a long reveal."),
"brest-fortress": dict(
    name="Brest Fortress", slug="Brest Fortress", country="Belarus",
    region="Brest Region", type="history", tag="hidden", emoji="🗿",
    sounds=["wilderness.mp3"],
    highlights=[("Brest, Belarus", "Brest,_Belarus"),
                ("Kholm Gate", None),
                ("Bug River", "Bug_River")],
    blurb="A nineteenth-century star fort at the confluence of the Bug and the "
          "Mukhavets, right on the Polish border, and the first Soviet ground "
          "attacked on 22 June 1941. Its garrison held out for weeks inside "
          "the ruins after the front had moved hundreds of kilometres east.",
    fact="The fortress was left deliberately unrestored — the brickwork is "
         "still shot through, and the memorial built into it in 1971 is one of "
         "the starkest Soviet monuments anywhere.",
    tip="The Kholm Gate is the single most bullet-scarred surface on the site; "
        "the pattern of impacts is the exhibit."),
"belovezhskaya-pushcha": dict(
    name="Belovezhskaya Pushcha", slug="Belovezhskaya Pushcha National Park",
    country="Belarus", region="Brest Region", type="nature", tag="hidden",
    emoji="🦬", sounds=["wilderness.mp3"],
    highlights=[("Viskuli", "Viskuli"),
                ("Kamyenyets", "Kamyenyets"),
                ("Białowieża National Park", "Białowieża_National_Park")],
    blurb="The last great lowland primeval forest of Europe, straddling the "
          "Belarus-Poland border — woodland that was never cleared because it "
          "was a royal hunting reserve for six centuries, and which still has "
          "oaks five hundred years old standing where they fell.",
    fact="The European bison was extinct in the wild by 1927 and every one "
         "alive today descends from about a dozen zoo animals; the herd here "
         "is the largest, and this forest is where they were put back.",
    tip="The border runs straight through the forest and the fence across it "
        "is a real ecological problem — animals on the two halves of one wood "
        "no longer mix."),

# ============================== MOLDOVA ==============================
"orheiul-vechi": dict(
    name="Orheiul Vechi", slug="Orheiul Vechi", country="Moldova",
    region="Orhei District", type="history", tag="hidden", emoji="⛪",
    sounds=["wilderness.mp3"],
    highlights=[("Răut River", "Răut_River"),
                ("Cave monastery", None),
                ("Butuceni", None)],
    blurb="A limestone gorge on a bend of the Răut with a monastery cut into "
          "the cliff face, still occupied by monks, and a village of white "
          "stone houses on the plateau above. People have lived in these caves "
          "on and off since the Palaeolithic; Dacians, Mongols and Moldovans "
          "each built on top of the last.",
    fact="The cave church's bell tower sticks out of the top of the cliff, so "
         "from the far bank you see a cross and a small doorway in a blank "
         "rock wall and nothing else of the monastery at all.",
    tip="Walk the ridge from Butuceni at sunset — the whole meander of the "
        "river opens up and the gorge glows."),
"cricova": dict(
    name="Cricova", slug="Cricova", country="Moldova",
    region="Chișinău Municipality", type="history", tag="hidden", emoji="🍷",
    sounds=["wilderness.mp3"],
    highlights=[("Cricova winery", None),
                ("Underground streets", None)],
    blurb="An underground city of wine 80 m below a town north of Chișinău — "
          "120 km of galleries cut as limestone quarries in the fifteenth "
          "century and converted after 1952 into cellars where the temperature "
          "never moves off 12 °C. The tunnels have street names and you tour "
          "them by car.",
    fact="Moldova has the largest wine cellars in the world by length; Cricova "
          "and nearby Mileștii Mici between them hold millions of bottles, and "
          "one collection was assembled from confiscated European cellars "
          "after 1945.",
    tip="The galleries are named after what is stored down them — Cabernet "
        "Street, Feteasca Street — so the address system is also the map."),

# ============================== ESTONIA ==============================
"tartu": dict(
    name="Tartu", slug="Tartu", country="Estonia", region="Tartu County",
    type="city", tag="hidden", emoji="🎓", sounds=["european-plaza.mp3"],
    highlights=[("University of Tartu", "University_of_Tartu"),
                ("Toomemägi", "Toomemägi"),
                ("Raekoja plats", "Raekoja_plats,_Tartu"),
                ("Estonian National Museum", "Estonian_National_Museum")],
    blurb="Estonia's university town and its intellectual capital, on the "
          "Emajõgi in the south. A quarter of the population is students, the "
          "classical university building is the front of the town, and the "
          "cathedral on the hill behind it has been a picturesque ruin since "
          "the Reformation.",
    fact="The Estonian National Museum stands on a former Soviet military "
          "airfield, and its roof is a single plane that lifts off the end of "
          "the old runway like a continuation of it.",
    tip="The leaning house on the square — the Barclay House — tilts because "
        "one half stands on the old town wall and the other on soft riverbank."),
"saaremaa": dict(
    name="Saaremaa", slug="Saaremaa", country="Estonia", region="Saare County",
    type="island", tag="hidden", emoji="🏝️", sounds=["ocean-waves.mp3"],
    highlights=[("Kuressaare Castle", "Kuressaare_Castle"),
                ("Kaali crater", "Kaali_crater"),
                ("Panga cliff", None),
                ("Angla windmills", None)],
    blurb="Estonia's largest island, low and juniper-covered in the Baltic, "
          "with a black-stone bishop's castle at Kuressaare that is the "
          "best-preserved medieval fortress in the whole region. It was a "
          "closed Soviet border zone for fifty years, which is why so little "
          "was built on it.",
    fact="Kaali is a field of nine meteorite craters that fell within human "
          "memory, around 1500 BC — the main one is a perfectly round lake "
          "110 m across, and Bronze Age people walled it as a sacred site.",
    tip="The island's junipers are the reason everything here — the smoked "
        "fish, the beer, the sauna — tastes faintly of them."),
"lahemaa": dict(
    name="Lahemaa", slug="Lahemaa National Park", country="Estonia",
    region="Harju County", type="nature", tag="hidden", emoji="🌲",
    sounds=["wilderness.mp3"],
    highlights=[("Palmse Manor", "Palmse_Manor"),
                ("Viru Bog", None),
                ("Käsmu", None),
                ("Jägala Waterfall", None)],
    blurb="The Soviet Union's first national park, declared in 1971 on the "
          "north coast east of Tallinn — a landscape of bog, pine forest, "
          "erratic boulders left by the ice, and four peninsulas of fishing "
          "villages that were sealed border zones until 1991.",
    fact="Its 'boulder fields' are among the densest on Earth: glacial "
          "erratics the size of houses sitting in open forest, some of them "
          "named and used as landmarks for centuries.",
    tip="The Viru Bog boardwalk crosses 3.5 km of raised peat with pools you "
        "cannot see the bottom of — go at dawn, when the mist sits on it."),

# ============================== LATVIA ==============================
"sigulda": dict(
    name="Sigulda", slug="Sigulda", country="Latvia", region="Vidzeme",
    type="history", tag="hidden", emoji="🏰", sounds=["wilderness.mp3"],
    highlights=[("Turaida Castle", "Turaida_Castle"),
                ("Gauja National Park", "Gauja_National_Park"),
                ("Gūtmaņala", None),
                ("Sigulda Medieval Castle", None)],
    blurb="A town on the rim of the Gauja valley, with a red-brick crusader "
          "castle on one side, a bishop's castle on the other, and 90 m of "
          "sandstone gorge between them. Latvians call the valley the "
          "Livonian Switzerland, which is generous about the height and fair "
          "about the shape.",
    fact="Gūtmaņala is the largest cave in the Baltics and its sandstone walls "
          "are covered in visitors' carved inscriptions, the oldest dating to "
          "the seventeenth century.",
    tip="A cable car crosses the gorge at 43 m — the only one in the Baltics, "
        "and the best way to see the valley in autumn colour."),
"jurmala": dict(
    name="Jūrmala", slug="Jūrmala", country="Latvia", region="Jūrmala",
    type="coastal", tag="hidden", emoji="🏖️", sounds=["ocean-waves.mp3"],
    highlights=[("Jomas Street", None),
                ("Dzintari Forest Park", None),
                ("Ķemeri National Park", "Ķemeri_National_Park"),
                ("Gulf of Riga", "Gulf_of_Riga")],
    blurb="A 26 km beach of white quartz sand backed by pine forest and a "
          "strip of wooden Art Nouveau villas, half an hour by train from "
          "Riga. It was the Soviet Union's most fashionable Baltic resort, and "
          "the timber summer houses from before that are still standing among "
          "the pines.",
    fact="The sand is so fine and the shelf so shallow that you can wade out "
          "a hundred metres in the Gulf of Riga and still be waist-deep.",
    tip="Ķemeri, at the western end, is a raised bog with sulphur springs and "
        "a boardwalk — the smell is the point, and it is why the resort was "
        "built here in the first place."),
"rundale": dict(
    name="Rundāle Palace", slug="Rundāle Palace", country="Latvia",
    region="Bauska Municipality", type="history", tag="hidden", emoji="👑",
    sounds=["wilderness.mp3"],
    highlights=[("Bauska Castle", "Bauska_Castle"),
                ("French garden", None),
                ("Gold Hall", None)],
    blurb="A Baroque summer palace on the flat plain of Zemgale, built for the "
          "Duke of Courland by Bartolomeo Rastrelli — the architect of the "
          "Winter Palace — in the 1730s, with 138 rooms and a French garden of "
          "10 hectares behind it.",
    fact="It was a school, a granary and a hospital in turn during the "
          "twentieth century; the restoration that gave it back its interiors "
          "took over fifty years and finished in 2015.",
    tip="The rose garden holds more than two thousand varieties and peaks in "
        "late June, when it is arguably the better half of the visit."),

# ============================== LITHUANIA ==============================
"kaunas": dict(
    name="Kaunas", slug="Kaunas", country="Lithuania", region="Kaunas County",
    type="city", tag="hidden", emoji="🏛️", sounds=["european-plaza.mp3"],
    highlights=[("Kaunas Castle", "Kaunas_Castle"),
                ("Laisvės alėja", "Laisvės_alėja"),
                ("Ninth Fort", "Ninth_Fort"),
                ("Christ's Resurrection Basilica", "Christ's_Resurrection_Basilica,_Kaunas"),
                ("Pažaislis Monastery", "Pažaislis_Monastery")],
    blurb="Lithuania's second city and its provisional capital between the "
          "wars, when Vilnius was held by Poland — which is why an "
          "interwar-modernist city centre exists here and nowhere else in the "
          "Baltics. Some 6,000 buildings went up in twenty years, in a clean "
          "national style now on the World Heritage list.",
    fact="Its main street, Laisvės alėja, is 1.6 km long, entirely pedestrian, "
          "and by local ordinance a non-smoking street for its whole length.",
    tip="Ride the 1931 funicular up Žaliakalnis — it still has its original "
        "wooden car and the operator sells tickets by hand."),
"nida": dict(
    name="Nida", slug="Nida, Lithuania", country="Lithuania",
    region="Curonian Spit", type="coastal", tag="hidden", emoji="🏜️",
    sounds=["ocean-waves.mp3"],
    highlights=[("Curonian Spit", "Curonian_Spit"),
                ("Parnidis Dune", "Parnidis_Dune"),
                ("Curonian Lagoon", "Curonian_Lagoon"),
                ("Thomas Mann House", None)],
    blurb="A fishing village of blue-and-brown wooden houses on the Curonian "
          "Spit — a 98 km sandbar between a lagoon and the open Baltic, half "
          "Lithuanian and half Russian, nowhere more than 4 km wide and in "
          "places only 400 m.",
    fact="The spit's dunes buried fourteen villages between the seventeenth "
          "and nineteenth centuries after the forest was felled for timber; "
          "the pine plantations that now hold the sand still still are a "
          "200-year-old engineering project.",
    tip="A sundial stands on the Parnidis dune above the village. From it you "
        "can see the lagoon on one side and the sea on the other, with the "
        "Russian border a short walk south."),
"hill-of-crosses": dict(
    name="Hill of Crosses", slug="Hill of Crosses", country="Lithuania",
    region="Šiauliai County", type="history", tag="hidden", emoji="✝️",
    sounds=["wind.mp3"],
    highlights=[("Šiauliai", "Šiauliai"),
                ("Jurgaičiai hillfort", None)],
    blurb="A low mound 12 km north of Šiauliai carrying well over a hundred "
          "thousand crosses, left by pilgrims since at least the 1830s. The "
          "Soviet authorities bulldozed the hill at least three times between "
          "1961 and 1975 and it was rebuilt each time, overnight, by people "
          "who risked prison to do it.",
    fact="Nobody counts them officially any more; the last serious attempt, in "
          "the 1990s, reached about 55,000 and the number has at least doubled "
          "since.",
    tip="Go when there is wind. The small crosses and rosaries hung on the "
        "large ones knock together, and the whole hill sounds like rain."),

# ============================== POLAND ==============================
"warsaw": dict(
    name="Warsaw", slug="Warsaw", country="Poland", region="Masovia",
    type="city", tag="famous", emoji="🏙️", sounds=["european-plaza.mp3"],
    highlights=[("Old Town Market Place", "Old_Town_Market_Place,_Warsaw"),
                ("Royal Castle", "Royal_Castle,_Warsaw"),
                ("Łazienki Park", "Łazienki_Park"),
                ("Palace of Culture and Science", "Palace_of_Culture_and_Science"),
                ("Wilanów Palace", "Wilanów_Palace")],
    blurb="A capital that was deliberately destroyed — some 85% of the left "
          "bank was demolished by the Germans after the 1944 uprising — and "
          "then rebuilt from paintings, photographs and memory. The old town "
          "you walk is a 1950s reconstruction, and it is on the World Heritage "
          "list precisely for that.",
    fact="The rebuilders used Bernardo Bellotto's eighteenth-century "
          "cityscapes as working drawings, which is why the facades match a "
          "painter's view of the city rather than its last photographs.",
    tip="Łazienki's park concerts under the Chopin monument run every Sunday "
        "through summer and are free — the whole lawn fills up."),
"gdansk": dict(
    name="Gdańsk", slug="Gdańsk", country="Poland", region="Pomerania",
    type="coastal", tag="famous", emoji="⚓", sounds=["ocean-waves.mp3"],
    highlights=[("Długi Targ", "Long_Market"),
                ("Gdańsk Crane", "Gdańsk_Crane"),
                ("St. Mary's Church", "St._Mary's_Church,_Gdańsk"),
                ("European Solidarity Centre", "European_Solidarity_Centre"),
                ("Westerplatte", "Westerplatte")],
    blurb="A Hanseatic port at the mouth of the Vistula, rich for six hundred "
          "years on Polish grain and Baltic amber, and a free city between the "
          "wars belonging to nobody. The Second World War began at its harbour "
          "mouth and the Soviet bloc started coming apart in its shipyard "
          "forty years later.",
    fact="St. Mary's is the largest brick church in the world by volume, big "
          "enough for 25,000 people, and it has no spire because the tower was "
          "never finished.",
    tip="The medieval port crane on the waterfront was worked by men walking "
          "inside two enormous treadwheels, and you can still see them."),
"wroclaw": dict(
    name="Wrocław", slug="Wrocław", country="Poland",
    region="Lower Silesia", type="city", tag="hidden", emoji="🌉",
    sounds=["european-plaza.mp3"],
    highlights=[("Wrocław Market Square", "Market_Square,_Wrocław"),
                ("Ostrów Tumski", "Ostrów_Tumski,_Wrocław"),
                ("Centennial Hall", "Centennial_Hall"),
                ("Racławice Panorama", "Racławice_Panorama")],
    blurb="A city on twelve islands where the Oder splits, Bohemian then "
          "Austrian then Prussian then Polish, and repopulated almost entirely "
          "after 1945 when its German inhabitants left and Poles arrived from "
          "Lviv. Its market square is one of the largest in Europe and its "
          "cathedral island is where the city began.",
    fact="Several hundred small bronze dwarfs are scattered around the "
          "pavements — they began as the symbol of an absurdist anti-communist "
          "protest movement in the 1980s and have been multiplying since.",
    tip="Centennial Hall, 1913, was the largest reinforced-concrete dome in "
        "the world when built — a piece of engineering history a tram ride "
        "from the old town."),
"torun": dict(
    name="Toruń", slug="Toruń", country="Poland",
    region="Kuyavia-Pomerania", type="history", tag="hidden", emoji="🍪",
    sounds=["european-plaza.mp3"],
    highlights=[("Old Town Hall", None),
                ("Leaning Tower", None),
                ("Teutonic Castle ruins", None),
                ("Vistula", "Vistula")],
    blurb="A Teutonic Order town on the Vistula whose Gothic centre came "
          "through the Second World War essentially untouched — no "
          "reconstruction, no infill, the original brick. Copernicus was born "
          "in a house on one of its streets in 1473.",
    fact="Toruń gingerbread has been made here since the Middle Ages under "
          "guild rules, using carved wooden moulds, and the recipe was a "
          "protected civic secret.",
    tip="The town's leaning tower is part of the medieval wall and leans about "
        "1.5 m off vertical — a defensive tower built on sand rather than a "
        "folly."),
"malbork": dict(
    name="Malbork Castle", slug="Malbork Castle", country="Poland",
    region="Pomerania", type="history", tag="hidden", emoji="🏰",
    sounds=["wilderness.mp3"],
    highlights=[("Nogat", "Nogat"),
                ("Grand Master's Palace", None),
                ("Malbork", "Malbork")],
    blurb="The largest castle in the world by land area, and the headquarters "
          "of the Teutonic Knights from 1309 — three fortresses inside one "
          "ring of walls on the bank of the Nogat, built entirely of brick "
          "because northern Poland has no building stone.",
    fact="Something like 4.5 million bricks went into it. It was wrecked in "
          "1945 and rebuilt over the following decades using the same "
          "nineteenth-century survey drawings that had guided its first "
          "restoration.",
    tip="View it from the far bank of the Nogat in late afternoon — the whole "
        "1.5 km of wall turns red at once, which is the sight the order was "
        "buying."),
"zakopane": dict(
    name="Zakopane", slug="Zakopane", country="Poland",
    region="Lesser Poland", type="mountain", tag="hidden", emoji="⛷️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Tatra Mountains", "Tatra_Mountains"),
                ("Giewont", "Giewont"),
                ("Morskie Oko", "Morskie_Oko"),
                ("Krupówki", None),
                ("Gubałówka", "Gubałówka")],
    blurb="Poland's mountain capital, at 800 m directly under the Tatras — the "
          "only genuinely alpine range in the country, packed into 60 km. A "
          "distinctive timber architecture was invented here in the 1890s as a "
          "conscious national style, and the town is still built in it.",
    fact="Giewont, the ridge above the town, is said to be a sleeping knight "
          "in profile, and a 15 m iron cross has stood on its summit since "
          "1901.",
    tip="Morskie Oko is a glacial lake 9 km up a closed road — walk it early, "
        "because it is the single most visited spot in the Polish mountains."),
"wieliczka": dict(
    name="Wieliczka Salt Mine", slug="Wieliczka Salt Mine", country="Poland",
    region="Lesser Poland", type="history", tag="hidden", emoji="🧂",
    sounds=["wilderness.mp3"],
    highlights=[("Chapel of St. Kinga", None),
                ("Wieliczka", "Wieliczka"),
                ("Underground lakes", None)],
    blurb="A salt mine worked continuously from the thirteenth century until "
          "1996, 327 m deep and with over 245 km of galleries, in which "
          "miners carved chapels, chandeliers and whole rooms out of the rock "
          "salt itself. It was on the first World Heritage list in 1978.",
    fact="The Chapel of St. Kinga is 101 m down, took three miners more than "
          "sixty years to carve, and everything in it — the altar, the floor "
          "tiles, the chandelier crystals — is salt.",
    tip="The tourist route is about 3.5 km and 800 steps, and the air is "
        "brine-saturated; the mine ran an underground sanatorium for asthma "
        "on exactly that basis."),

# ============================== ROMANIA ==============================
"bucharest": dict(
    name="Bucharest", slug="Bucharest", country="Romania",
    region="Bucharest", type="city", tag="famous", emoji="🏛️",
    sounds=["city-hum.mp3"],
    highlights=[("Palace of the Parliament", "Palace_of_the_Parliament"),
                ("Romanian Athenaeum", "Romanian_Athenaeum"),
                ("Lipscani", "Lipscani"),
                ("Village Museum", "Dimitrie_Gusti_National_Village_Museum"),
                ("Stavropoleos Monastery", "Stavropoleos_Monastery")],
    blurb="A capital of Belle Époque boulevards with a Stalinist megaproject "
          "dropped through the middle of it: Ceaușescu levelled a fifth of the "
          "historic city in the 1980s to build the Palace of the Parliament "
          "and its approach avenue, deliberately one metre wider than the "
          "Champs-Élysées.",
    fact="The Palace of the Parliament is the heaviest building in the world "
         "and the largest administrative building outside the Pentagon — and "
         "roughly 70% of it stands empty.",
    tip="The Village Museum on Herăstrău lake is 300 real peasant buildings "
        "moved here from across the country — the counterweight to everything "
        "downtown."),
"brasov": dict(
    name="Brașov", slug="Brașov", country="Romania", region="Transylvania",
    type="history", tag="hidden", emoji="🏔️", sounds=["european-plaza.mp3"],
    highlights=[("Black Church", "Biserica_Neagră"),
                ("Council Square", "Piața_Sfatului"),
                ("Tâmpa", "Tâmpa_(Brașov)"),
                ("Bran Castle", "Bran_Castle"),
                ("Rope Street", "Strada_Sforii")],
    blurb="A Saxon town under a forested mountain in the bend of the "
          "Carpathians, founded by German settlers in the thirteenth century "
          "and run by them for seven hundred years. The square, the guild "
          "towers and the great hall church are all theirs; the mountain "
          "starts at the end of the streets.",
    fact="The Black Church is the largest Gothic church between Vienna and "
          "Istanbul and got its name from a 1689 fire that left the walls "
          "soot-stained for centuries.",
    tip="Rope Street is barely a metre wide and was built as a firefighters' "
        "access lane; Bran Castle, marketed as Dracula's, is 30 km south and "
        "has essentially nothing to do with him."),
"danube-delta": dict(
    name="Danube Delta", slug="Danube Delta", country="Romania",
    region="Tulcea County", type="nature", tag="hidden", emoji="🦢",
    sounds=["wilderness.mp3"],
    highlights=[("Sulina", "Sulina"),
                ("Letea Forest", "Letea_Forest"),
                ("Danube", "Danube"),
                ("Tulcea", "Tulcea")],
    blurb="Where the Danube finishes, spreading into 4,150 km² of reed bed, "
          "channel and floating island before the Black Sea — the largest and "
          "best-preserved delta in Europe, and the youngest land on the "
          "continent, still growing seaward by 40 m a year.",
    fact="Around 300 bird species use it, including the world's largest colony "
          "of great white pelicans, and the reed beds here are the biggest "
          "single expanse of reed anywhere on Earth.",
    tip="Nothing in the delta has roads. Villages like Mila 23 are reached by "
        "boat only, and the ferry down from Tulcea takes most of a day."),
"maramures": dict(
    name="Maramureș", slug="Maramureș County", country="Romania",
    region="Maramureș", type="village", tag="hidden", emoji="🪵",
    sounds=["wilderness.mp3"],
    highlights=[("Wooden Churches of Maramureș", "Wooden_Churches_of_Maramureș"),
                ("Merry Cemetery", "Merry_Cemetery"),
                ("Bârsana", None),
                ("Vaser Valley railway", "Mocăniță")],
    blurb="A valley region against the Ukrainian border where a pre-industrial "
          "peasant culture is still, in places, a working way of life — hay "
          "cut by scythe, carved wooden gates on every farmyard, and tall "
          "shingled churches with spires like sharpened pencils.",
    fact="The Merry Cemetery at Săpânța marks each grave with a painted blue "
          "cross carrying a comic verse about how the person lived and, often "
          "bluntly, how they died.",
    tip="The Mocănița on the Vaser valley is a working steam narrow-gauge "
        "forestry railway, not a heritage recreation — it still hauls timber."),

# ============================== BULGARIA ==============================
"plovdiv": dict(
    name="Plovdiv", slug="Plovdiv", country="Bulgaria",
    region="Plovdiv Province", type="history", tag="hidden", emoji="🏛️",
    sounds=["european-plaza.mp3"],
    highlights=[("Roman theatre of Philippopolis", "Roman_theatre_of_Philippopolis"),
                ("Old Town", None),
                ("Kapana", None),
                ("Nebet Tepe", None),
                ("Roman Stadium", None)],
    blurb="One of the oldest continuously inhabited cities in Europe — eight "
          "thousand years on the same hills — and layered accordingly: a "
          "Thracian citadel, a Roman theatre still used for opera, an Ottoman "
          "mosque, and a hillside of nineteenth-century merchant houses with "
          "overhanging upper floors.",
    fact="The Roman stadium ran 240 m under what is now the main pedestrian "
          "street; you can see one curved end of it through a glass floor in "
          "the middle of the shops.",
    tip="Kapana, the old craftsmen's quarter, is a grid of tiny lanes that has "
        "turned into the city's studio and bar district without being rebuilt."),
"rila-monastery": dict(
    name="Rila Monastery", slug="Rila Monastery", country="Bulgaria",
    region="Kyustendil Province", type="history", tag="hidden", emoji="⛪",
    sounds=["mountain-wind.mp3"],
    highlights=[("Hrelja's Tower", None),
                ("Rila Mountains", "Rila"),
                ("Church of the Nativity", None)],
    blurb="The largest monastery in Bulgaria, in a fold of the Rila mountains "
          "at 1,150 m — a fortress wall on the outside, and inside, four "
          "storeys of black-and-white striped arcades around a church covered "
          "end to end in frescoes. It held the language and the liturgy "
          "through five centuries of Ottoman rule.",
    fact="The monastery is on the back of the 1 lev note, and its stone "
          "defensive tower from 1335 is the one part of the medieval complex "
          "that survived the fire of 1833.",
    tip="Stay for the evening: the day-trip buses from Sofia leave by four and "
        "the courtyard goes completely quiet."),
"veliko-tarnovo": dict(
    name="Veliko Tarnovo", slug="Veliko Tarnovo", country="Bulgaria",
    region="Veliko Tarnovo Province", type="history", tag="hidden", emoji="🏰",
    sounds=["european-plaza.mp3"],
    highlights=[("Tsarevets", "Tsarevets"),
                ("Yantra", "Yantra_(river)"),
                ("Samovodska Charshia", None),
                ("Asen Dynasty Monument", None)],
    blurb="The capital of the Second Bulgarian Empire, built on three hills in "
          "the meanders of the Yantra with houses stacked so steeply that each "
          "roof is the next one's terrace. The royal fortress of Tsarevets "
          "occupies its own hill inside a loop of the river.",
    fact="For two centuries this was one of the largest and richest cities in "
          "south-eastern Europe, and contemporaries called it the Third Rome "
          "after Rome and Constantinople.",
    tip="The old craft street, Samovodska Charshia, still has working "
        "potters, coppersmiths and bakers rather than souvenir shops."),
"nessebar": dict(
    name="Nessebar", slug="Nesebar", country="Bulgaria",
    region="Burgas Province", type="coastal", tag="hidden", emoji="⛪",
    sounds=["ocean-waves.mp3"],
    highlights=[("Church of Christ Pantocrator", "Church_of_Christ_Pantocrator,_Nesebar"),
                ("Black Sea", "Black_Sea"),
                ("Old Windmill", None),
                ("Sveti Stefan Church", None)],
    blurb="A rocky peninsula on the Black Sea joined to the mainland by a "
          "300 m isthmus, occupied for three thousand years and holding the "
          "ruins of more than forty medieval churches — a Byzantine provincial "
          "style of brick and stone banding you find almost nowhere else "
          "intact.",
    fact="A third of the ancient town has been lost to the sea; foundations of "
          "Roman and medieval buildings lie in shallow water off the north "
          "shore and can be seen from a boat on a calm day.",
    tip="The upper town's wooden Black Sea houses, with their whitewashed "
        "stone ground floors and overhanging timber upper storeys, are the "
        "same pattern you meet all the way round the coast."),
}

# ---------------------------------------------------------------------------
# NEW_ASIA — appended to data/asia.json (continent "Asia")
# The Caucasus, the five Central Asian republics, and Mongolia.
# ---------------------------------------------------------------------------
NEW_ASIA = {

# ============================== GEORGIA ==============================
"mtskheta": dict(
    name="Mtskheta", slug="Mtskheta", country="Georgia",
    region="Mtskheta-Mtianeti", type="history", tag="hidden", emoji="⛪",
    sounds=["mountain-wind.mp3"],
    highlights=[("Svetitskhoveli Cathedral", "Svetitskhoveli_Cathedral"),
                ("Jvari Monastery", "Jvari_(monastery)"),
                ("Samtavro Monastery", "Samtavro_Monastery"),
                ("Aragvi", "Aragvi")],
    blurb="The old capital of the Georgian kingdom, at the meeting of the "
          "Aragvi and the Mtkvari 20 km from Tbilisi, and the country's "
          "spiritual centre since Georgia adopted Christianity here in the "
          "330s. Kings were crowned and buried in its cathedral for a "
          "thousand years.",
    fact="Svetitskhoveli means 'the life-giving pillar' — the cathedral is "
         "said to stand over the robe of Christ, brought back from Jerusalem "
         "by a Georgian Jew who was at the crucifixion.",
    tip="Jvari sits on the bluff above the confluence, and the two rivers meet "
        "without mixing — one grey with silt, one clear — for a long way "
        "downstream."),
"svaneti": dict(
    name="Svaneti", slug="Svaneti", country="Georgia",
    region="Samegrelo-Zemo Svaneti", type="mountain", tag="hidden", emoji="🗼",
    sounds=["mountain-wind.mp3"],
    highlights=[("Ushguli", "Ushguli"),
                ("Mestia", "Mestia"),
                ("Mount Ushba", "Ushba"),
                ("Svan towers", "Svan_towers"),
                ("Chalaadi Glacier", None)],
    blurb="A region of high valleys under the main Caucasus ridge, cut off by "
          "snow for much of the year and never conquered by anyone — which is "
          "why its villages still bristle with defensive stone towers, one per "
          "family, built between the ninth and thirteenth centuries.",
    fact="Ushguli, at 2,100 m, claims to be the highest continuously inhabited "
         "settlement in Europe, and its churches held medieval icons and "
         "manuscripts that survived because no invading army ever got up here.",
    tip="The Svan language is not Georgian — it split off perhaps four "
        "thousand years ago and has no written form."),
"vardzia": dict(
    name="Vardzia", slug="Vardzia", country="Georgia",
    region="Samtskhe-Javakheti", type="history", tag="hidden", emoji="🕳️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Khertvisi Fortress", "Khertvisi_fortress"),
                ("Mtkvari", "Kura_(Caspian_Sea)"),
                ("Church of the Dormition", None)],
    blurb="A cave city dug into a cliff above the Mtkvari in the 1180s under "
          "Queen Tamar — thirteen storeys, some six thousand rooms, with "
          "chapels, bakeries, wine cellars and a piped spring, all cut into "
          "soft volcanic tuff as a refuge from Mongol invasion.",
    fact="An earthquake in 1283 sheared the outer wall of rock clean off, "
         "opening the whole complex to the air like a cut-away drawing — what "
         "you see was meant to be hidden inside the cliff.",
    tip="The main church still has its twelfth-century frescoes, including "
        "what may be the only portrait of Tamar painted in her lifetime."),
"batumi": dict(
    name="Batumi", slug="Batumi", country="Georgia", region="Adjara",
    type="coastal", tag="hidden", emoji="🌴", sounds=["ocean-waves.mp3"],
    highlights=[("Batumi Boulevard", None),
                ("Alphabetic Tower", "Alphabetic_Tower"),
                ("Gonio Fortress", "Gonio_fortress"),
                ("Batumi Botanical Garden", "Batumi_Botanical_Garden"),
                ("Black Sea", "Black_Sea")],
    blurb="Georgia's Black Sea city, subtropical and rainy, where palms and "
          "bamboo grow at the foot of the Lesser Caucasus. A belle-époque oil "
          "port that has spent the last twenty years growing a skyline of "
          "deliberately strange towers along its pebble beach.",
    fact="The Alphabet Tower is a 130 m double helix with the 33 letters of "
         "the Georgian alphabet running up its steel strands — Georgian is "
         "written in a script used by no other language.",
    tip="The botanical garden 9 km north was laid out in 1912 across nine "
        "climate zones on a headland; it is the better half of Batumi."),
"kutaisi": dict(
    name="Kutaisi", slug="Kutaisi", country="Georgia", region="Imereti",
    type="history", tag="hidden", emoji="🏛️", sounds=["european-plaza.mp3"],
    highlights=[("Bagrati Cathedral", "Bagrati_Cathedral"),
                ("Gelati Monastery", "Gelati_Monastery"),
                ("Prometheus Cave", "Prometheus_Cave"),
                ("Rioni", "Rioni")],
    blurb="One of the oldest cities in Europe, capital of the kingdom of "
          "Colchis that the Argonauts sailed to for the Golden Fleece, and "
          "later of medieval Georgia. Its cathedral crowns the hill above the "
          "Rioni and the royal monastery of Gelati is 11 km out of town.",
    fact="Gelati was founded in 1106 with an academy attached, and its "
          "twelfth-century mosaic of the Virgin in the apse is one of the "
          "finest pieces of Byzantine-era work outside Constantinople.",
    tip="The canyons north of town — Okatse and Martvili — are half a day "
        "each and far less visited than the monasteries."),

# ============================== ARMENIA ==============================
"geghard": dict(
    name="Geghard", slug="Geghard", country="Armenia",
    region="Kotayk Province", type="history", tag="hidden", emoji="⛪",
    sounds=["mountain-wind.mp3"],
    highlights=[("Garni Temple", "Garni_Temple"),
                ("Azat River", "Azat_River"),
                ("Rock-cut chambers", None)],
    blurb="A monastery in the Azat gorge whose inner churches are not built "
          "but carved — hollowed straight out of the cliff, single blocks of "
          "living rock with domes cut downward from above, so there is not a "
          "seam or a joint anywhere inside them.",
    fact="Its name means 'spear' — the lance that pierced Christ's side was "
         "kept here for five hundred years, and the acoustics of the carved "
         "chambers are so exact that a single voice fills them.",
    tip="Garni, 9 km down the gorge, is a first-century Greco-Roman temple — "
        "the only classical colonnade left anywhere in the former Soviet "
        "Union."),
"khor-virap": dict(
    name="Khor Virap", slug="Khor Virap", country="Armenia",
    region="Ararat Province", type="history", tag="hidden", emoji="⛰️",
    sounds=["wind.mp3"],
    highlights=[("Mount Ararat", "Mount_Ararat"),
                ("Ararat Plain", "Ararat_Plain"),
                ("Artashat", "Artashat,_Armenia")],
    blurb="A small fortified monastery on a hillock in the flat Ararat plain, "
          "a kilometre from the closed Turkish border, and the single most "
          "photographed spot in Armenia — because Mount Ararat rises straight "
          "behind it, 5,137 m, the national symbol on the far side of a "
          "frontier no Armenian can cross.",
    fact="Gregory the Illuminator was imprisoned in a pit here for thirteen "
         "years before converting the king in 301 — which made Armenia the "
         "first state anywhere to adopt Christianity.",
    tip="You can climb down a ladder into the pit itself. Ararat is usually "
        "hazed out by midday, so come at first light."),
"dilijan": dict(
    name="Dilijan", slug="Dilijan", country="Armenia",
    region="Tavush Province", type="nature", tag="hidden", emoji="🌲",
    sounds=["wilderness.mp3"],
    highlights=[("Dilijan National Park", "Dilijan_National_Park"),
                ("Haghartsin Monastery", "Haghartsin_Monastery"),
                ("Goshavank", "Goshavank"),
                ("Parz Lake", None)],
    blurb="A forested spa town in the Aghstev valley that Armenians call their "
          "Switzerland — deciduous woodland rather than the bare volcanic "
          "highland of most of the country, with two thirteenth-century "
          "monasteries hidden in the trees above it.",
    fact="Haghartsin's refectory and churches sit in a clearing so enclosed by "
          "beech that you do not see the complex until you are inside it — the "
          "site was chosen for exactly that.",
    tip="Sharambeyan Street in town is a restored block of nineteenth-century "
        "wooden balconied houses, with working craft workshops behind them."),

# ============================== AZERBAIJAN ==============================
"gobustan": dict(
    name="Gobustan", slug="Gobustan Rock Art Cultural Landscape",
    country="Azerbaijan", region="Qobustan District", type="history",
    tag="hidden", emoji="🪨", sounds=["desert-wind.mp3"],
    highlights=[("Gobustan petroglyphs", None),
                ("Mud volcanoes", None),
                ("Caspian Sea", "Caspian_Sea")],
    blurb="A field of tumbled limestone boulders on a semi-desert plateau "
          "south of Baku carrying more than six thousand rock carvings — "
          "boats, dancers, hunters, aurochs — cut over a span of forty "
          "thousand years by people living on what was then a wetter coast.",
    fact="A Roman inscription here, left by a centurion of the Twelfth Legion "
          "in the first century AD, is the easternmost Roman inscription ever "
          "found.",
    tip="Azerbaijan has around half the world's mud volcanoes and a large "
        "field of them sits just beyond the reserve — cold grey cones that "
        "bubble continuously."),
"sheki": dict(
    name="Sheki", slug="Shaki, Azerbaijan", country="Azerbaijan",
    region="Shaki-Zaqatala", type="history", tag="hidden", emoji="🏯",
    sounds=["mountain-wind.mp3"],
    highlights=[("Palace of Shaki Khans", "Palace_of_Shaki_Khans"),
                ("Upper Caravanserai", None),
                ("Greater Caucasus", "Greater_Caucasus"),
                ("Church of Kish", "Church_of_Kish")],
    blurb="A silk town on the southern slope of the Greater Caucasus, "
          "terraced up a wooded hillside in red-tiled stone houses, with the "
          "summer palace of its eighteenth-century khans at the top of the "
          "town inside a walled citadel.",
    fact="The palace's windows are shebeke — stained glass held in a wooden "
         "lattice assembled with no nails and no glue, thousands of pieces per "
         "window, still made by a handful of craftsmen in the town.",
    tip="Sheki halva is a layered pastry of rice-flour threads and nuts, "
        "unrelated to the halva sold anywhere else, and is made in the bazaar."),
"khinalug": dict(
    name="Khinalug", slug="Khinalug", country="Azerbaijan",
    region="Quba District", type="village", tag="hidden", emoji="🏔️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Greater Caucasus", "Greater_Caucasus"),
                ("Quba", "Quba,_Azerbaijan"),
                ("Shahdag National Park", None)],
    blurb="A village at 2,300 m in the high Caucasus, houses stacked so that "
          "each roof is the terrace of the one above, reachable until 2006 "
          "only on foot or horseback. Its people speak Khinalug, a language "
          "related to nothing else and spoken nowhere else.",
    fact="Around 2,000 people speak Khinalug in total, all of them from this "
         "one village — it is among the most isolated languages in the world "
         "and has been spoken here for millennia.",
    tip="The road up from Quba climbs through a gorge and is one of the great "
        "mountain drives of the Caucasus; it closes with snow."),

# ============================== KAZAKHSTAN ==============================
"almaty": dict(
    name="Almaty", slug="Almaty", country="Kazakhstan",
    region="Almaty Region", type="city", tag="famous", emoji="🏔️",
    sounds=["city-hum.mp3"],
    highlights=[("Ascension Cathedral", "Ascension_Cathedral,_Almaty"),
                ("Medeu", "Medeu"),
                ("Shymbulak", "Shymbulak"),
                ("Kok Tobe", "Kok_Tobe"),
                ("Big Almaty Lake", "Big_Almaty_Lake")],
    blurb="Kazakhstan's largest city and its former capital, laid out on a "
          "grid of tree-lined streets on an alluvial fan with the Trans-Ili "
          "Alatau rising 4,000 m directly behind it. Every street running "
          "south goes uphill, which is how locals navigate.",
    fact="Ascension Cathedral, finished in 1907, is one of the tallest wooden "
         "buildings in the world at 56 m and came through the 1911 earthquake "
         "that flattened the rest of the city.",
    tip="Medeu, at 1,691 m, is the highest Olympic-size skating rink on Earth "
        "and is twenty minutes from downtown by bus."),
"astana": dict(
    name="Astana", slug="Astana", country="Kazakhstan", region="Akmola",
    type="city", tag="famous", emoji="🏙️", sounds=["city-hum.mp3"],
    highlights=[("Bayterek", "Bayterek"),
                ("Khan Shatyr", "Khan_Shatyr_Entertainment_Center"),
                ("Palace of Peace and Reconciliation", "Palace_of_Peace_and_Reconciliation"),
                ("Nur-Astana Mosque", "Nur-Astana_Mosque"),
                ("Ishim River", "Ishim_River")],
    blurb="A capital built from almost nothing on the open steppe after 1997, "
          "when the government moved 1,200 km north from Almaty — a planned "
          "city of monuments by Foster, Kurokawa and others, in a place where "
          "winter routinely reaches −40 °C.",
    fact="It is the second-coldest capital city in the world after Ulaanbaatar, "
         "and Khan Shatyr is a 150 m transparent tent designed to hold a "
         "climate-controlled park inside it through that winter.",
    tip="The ceremonial axis runs in a dead straight line from Khan Shatyr "
        "through Bayterek to the presidential palace — it is meant to be "
        "walked, and it takes about an hour."),
"charyn-canyon": dict(
    name="Charyn Canyon", slug="Charyn Canyon", country="Kazakhstan",
    region="Almaty Region", type="nature", tag="hidden", emoji="🏜️",
    sounds=["desert-wind.mp3"],
    highlights=[("Valley of Castles", None),
                ("Charyn River", "Charyn_River"),
                ("Temirlik Canyon", None)],
    blurb="A 154 km gorge cut 300 m into red sedimentary rock on the edge of "
          "the Kazakh steppe — a smaller, older Grand Canyon, its most famous "
          "stretch a corridor of eroded pillars that people have called the "
          "Valley of Castles for as long as anyone has come here.",
    fact="A relict grove of Sogdian ash survives on the canyon floor — a tree "
          "that has been growing here since before the last ice age and "
          "survives almost nowhere else on Earth.",
    tip="It is invisible until you are at the rim: the steppe runs flat to the "
        "horizon and then simply drops away."),
"kolsai-lakes": dict(
    name="Kolsai Lakes", slug="Kolsay Lakes National Park",
    country="Kazakhstan", region="Almaty Region", type="nature", tag="hidden",
    emoji="🏞️", sounds=["wilderness.mp3"],
    highlights=[("Lake Kaindy", "Lake_Kaindy"),
                ("Tian Shan", "Tian_Shan"),
                ("Saty", None)],
    blurb="Three lakes in a staircase up a spruce-forested valley of the "
          "northern Tian Shan, at 1,800, 2,250 and 2,700 m, with a pass at "
          "the top that drops into Kyrgyzstan. Kazakhs call them the pearls "
          "of the Tian Shan.",
    fact="Nearby Lake Kaindy was created by the 1911 earthquake, which dammed "
          "a valley and drowned a spruce forest — the bare trunks still stand "
          "upright underwater, preserved by the cold, and break the surface.",
    tip="Horses are the local transport between the first and second lakes, "
        "and are how most of the valley still moves."),
"turkestan": dict(
    name="Turkestan", slug="Turkistan, Kazakhstan", country="Kazakhstan",
    region="Turkistan Region", type="history", tag="hidden", emoji="🕌",
    sounds=["desert-wind.mp3"],
    highlights=[("Mausoleum of Khoja Ahmed Yasawi", "Mausoleum_of_Khoja_Ahmed_Yasawi"),
                ("Otrar", "Otrar"),
                ("Syr Darya", "Syr_Darya")],
    blurb="The spiritual capital of the Kazakh steppe, built around the tomb "
          "of a twelfth-century Sufi poet whose verse carried Islam to the "
          "Turkic nomads. Timur ordered the mausoleum in 1389 and it was left "
          "unfinished when he died — the scaffolding holes are still open.",
    fact="Its dome is the largest brick dome in Central Asia, 18 m across, and "
          "the building was the trial run for the architecture Timur then "
          "built at Samarkand.",
    tip="Otrar, 60 km away, is the ruined city whose governor murdered "
        "Genghis Khan's envoys in 1218 — the act that brought the Mongols "
        "west."),
"baikonur": dict(
    name="Baikonur Cosmodrome", slug="Baikonur Cosmodrome",
    country="Kazakhstan", region="Kyzylorda Region", type="history",
    tag="hidden", emoji="🚀", sounds=["desert-wind.mp3"],
    highlights=[("Gagarin's Start", "Gagarin's_Start"),
                ("Baikonur", "Baikonur"),
                ("Buran programme", "Buran_(spacecraft)")],
    blurb="The oldest and largest spaceport on Earth, 6,717 km² of Kazakh "
          "semi-desert leased to Russia until 2050. Sputnik went up from here "
          "in 1957 and Gagarin in 1961, and for nine years after the Shuttle "
          "retired it was the only way any human reached orbit.",
    fact="It is named after a town 320 km away — a deliberate Cold War "
          "misdirection, so that anyone reading a Soviet launch dateline would "
          "look in the wrong place.",
    tip="Gagarin's Start, pad number 1, launched both Sputnik and Gagarin and "
        "kept flying crews for sixty-two years before it was finally retired "
        "in 2019."),

# ============================== UZBEKISTAN ==============================
"khiva": dict(
    name="Khiva", slug="Khiva", country="Uzbekistan", region="Khorezm Region",
    type="history", tag="famous", emoji="🕌", sounds=["desert-wind.mp3"],
    highlights=[("Itchan Kala", "Itchan_Kala"),
                ("Kalta Minor Minaret", None),
                ("Kunya-Ark", None),
                ("Islamkhodja Madrasah", "Islamkhodja_Madrasah"),
                ("Juma Mosque", None)],
    blurb="The last of the three great Silk Road cities of Uzbekistan and the "
          "most complete — an entire walled inner town of mud brick, mosques "
          "and madrasas inside 10 m ramparts, preserved whole because the "
          "Khiva khanate was the final one to fall, in 1920.",
    fact="The Kalta Minor was meant to be the tallest minaret in the Islamic "
          "world; the khan died in 1855 with it 29 m up, so it stands as a "
          "wide turquoise stump — and is the city's emblem.",
    tip="The Juma Mosque has no dome and no courtyard: a flat roof carried on "
        "213 carved wooden columns, some of them a thousand years old, in "
        "near-darkness."),
"tashkent": dict(
    name="Tashkent", slug="Tashkent", country="Uzbekistan", region="Tashkent",
    type="city", tag="famous", emoji="🚇", sounds=["city-hum.mp3"],
    highlights=[("Chorsu Bazaar", "Chorsu_Bazaar"),
                ("Hazrati Imam Complex", "Hazrati_Imam_Complex"),
                ("Tashkent Metro", "Tashkent_Metro"),
                ("Amir Timur Square", "Amir_Timur_Square")],
    blurb="Central Asia's largest city, flattened by an earthquake in 1966 and "
          "rebuilt by work brigades sent from every Soviet republic — which is "
          "why its centre is wide, green, low-rise modernism, with the "
          "surviving old town clustered around one enormous domed bazaar.",
    fact="Its metro, opened in 1977, was built as a nuclear shelter and was a "
          "state secret — photography inside was banned until 2018, and every "
          "station is decorated to a different theme.",
    tip="The Hazrati Imam library holds the Uthman Quran, a seventh-century "
        "manuscript that is among the oldest surviving copies in the world."),
"shakhrisabz": dict(
    name="Shakhrisabz", slug="Shahrisabz", country="Uzbekistan",
    region="Qashqadaryo Region", type="history", tag="hidden", emoji="🏛️",
    sounds=["desert-wind.mp3"],
    highlights=[("Ak-Saray", "Ak-Saray_Palace"),
                ("Dorut Tilovat", None),
                ("Kok Gumbaz Mosque", None)],
    blurb="Timur's birthplace, over a 1,700 m pass south of Samarkand, where "
          "he built a summer palace intended to outdo anything in his capital. "
          "Two fragments of its gateway survive, 38 m tall, standing alone in "
          "an open square with nothing between them.",
    fact="The entrance arch of Ak-Saray spanned 22 m — the widest in the "
          "Islamic world — and its inscription read 'if you challenge our "
          "power, look at our buildings'.",
    tip="Timur meant to be buried here and had a crypt cut for it; he died in "
        "winter with the passes shut and was interred at Samarkand instead. "
        "The empty crypt is still open."),
"moynaq": dict(
    name="Moynaq", slug="Moʻynoq", country="Uzbekistan",
    region="Karakalpakstan", type="desert", tag="hidden", emoji="🚢",
    sounds=["desert-wind.mp3"],
    highlights=[("Aral Sea", "Aral_Sea"),
                ("Ship graveyard", None),
                ("Aralkum", "Aralkum_Desert"),
                ("Nukus", "Nukus")],
    blurb="A fishing port with no sea. Moynaq was on the Aral shore in the "
          "1960s, canning 25,000 tonnes of fish a year; the water is now "
          "150 km away, and a dozen rusting trawlers sit on the sand where "
          "the harbour was.",
    fact="The Aral was the fourth-largest lake on Earth and lost about 90% of "
          "its volume after its two feeder rivers were diverted to irrigate "
          "cotton — the seabed left behind is now a named desert, the "
          "Aralkum.",
    tip="The salt and pesticide dust blown off the dry bed reaches the "
        "Himalayas; the local rate of respiratory illness is among the "
        "highest anywhere."),

# ============================== KYRGYZSTAN ==============================
"issyk-kul": dict(
    name="Issyk-Kul", slug="Issyk-Kul", country="Kyrgyzstan",
    region="Issyk-Kul Region", type="nature", tag="hidden", emoji="🏞️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Cholpon-Ata", "Cholpon-Ata"),
                ("Jeti-Ögüz", "Jeti-Oguz"),
                ("Tian Shan", "Tian_Shan"),
                ("Grigorevka Gorge", None)],
    blurb="A lake 182 km long at 1,607 m, ringed by 4,000 m snow peaks and "
          "never freezing — the name means 'warm lake', and it is the "
          "second-largest alpine lake in the world after Titicaca. It is "
          "slightly saline and has no outflow.",
    fact="A submerged town lies off the northern shore in shallow water — "
         "walls, pottery and coins of a Silk Road settlement, possibly the "
         "medieval city of Chigu, drowned as the lake level rose.",
    tip="The Cholpon-Ata petroglyph field is a boulder plain of Bronze Age "
        "carvings — ibex, snow leopards and hunters — left exactly where they "
        "were made."),
"karakol": dict(
    name="Karakol", slug="Karakol", country="Kyrgyzstan",
    region="Issyk-Kul Region", type="mountain", tag="hidden", emoji="⛰️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Dungan Mosque", None),
                ("Holy Trinity Cathedral", None),
                ("Ala Kul", None),
                ("Altyn Arashan", None)],
    blurb="A Russian garrison town of 1869 at the east end of Issyk-Kul, now "
          "the base for the best trekking in Kyrgyzstan — valleys of spruce "
          "and hot springs running up into the Terskey Ala-Too within a day's "
          "walk of the main street.",
    fact="Its mosque was built in 1907 by Dungans — Chinese Muslims who fled "
          "the Qing — as a Chinese temple in wood, assembled without a single "
          "nail, and painted in colours that each carry a meaning.",
    tip="Sunday's animal market starts before dawn on the edge of town and is "
        "a working livestock bazaar, not a show — the largest in the country."),
"song-kol": dict(
    name="Song-Köl", slug="Song-Köl", country="Kyrgyzstan",
    region="Naryn Region", type="nature", tag="hidden", emoji="🐎",
    sounds=["mountain-wind.mp3"],
    highlights=[("Kalmak-Ashuu Pass", None),
                ("Kyzart Pass", None),
                ("Naryn", "Naryn")],
    blurb="A shallow lake at 3,016 m on a treeless high plateau, reached over "
          "passes that are snowed shut for eight months. From June to "
          "September herders drive their animals up here and the shore fills "
          "with yurts; the rest of the year there is nobody at all.",
    fact="The summer pasture — jailoo — is the surviving half of Kyrgyz "
         "nomadism: the same seasonal migration, the same felt yurts, still "
         "done because it is the only way to use this grass.",
    tip="There is no electricity and no phone signal on the plateau, and at "
        "3,000 m with no light for a hundred kilometres the night sky is "
        "the reason to stay."),
"osh": dict(
    name="Osh", slug="Osh", country="Kyrgyzstan", region="Osh Region",
    type="city", tag="hidden", emoji="⛰️", sounds=["city-hum.mp3"],
    highlights=[("Sulaiman-Too", "Sulayman_Mountain"),
                ("Jayma Bazaar", None),
                ("Fergana Valley", "Fergana_Valley")],
    blurb="Kyrgyzstan's second city and, at three thousand years, one of the "
          "oldest in Central Asia — a Silk Road crossroads at the mouth of the "
          "Fergana Valley, built around a five-peaked rock that rises straight "
          "out of the middle of it.",
    fact="Sulaiman-Too has been a place of pilgrimage for a millennium and a "
          "half and is Kyrgyzstan's first World Heritage site; Babur, founder "
          "of the Mughal empire, built a small mosque on its summit in 1510.",
    tip="Jayma Bazaar runs for kilometres along the Ak-Buura river and is the "
        "largest open-air market in Central Asia."),

# ============================== TAJIKISTAN ==============================
"dushanbe": dict(
    name="Dushanbe", slug="Dushanbe", country="Tajikistan", region="Dushanbe",
    type="city", tag="hidden", emoji="🏛️", sounds=["city-hum.mp3"],
    highlights=[("Rudaki Avenue", None),
                ("National Museum of Tajikistan", "National_Museum_of_Tajikistan"),
                ("Ismoil Somoni monument", None),
                ("Hisor Fortress", None)],
    blurb="A capital that was a village of 3,000 people in 1924 — its name "
          "means 'Monday', for the weekly market held there — and was built "
          "from scratch as a Soviet city, now a low, hot, tree-shaded grid "
          "under the Gissar range.",
    fact="The national museum holds a 13 m reclining Buddha from the fifth "
          "century, found at Ajina-Tepa and the largest in Central Asia — "
          "recovered in ninety-two pieces and reassembled over decades.",
    tip="Hisor Fortress, 30 km west, guarded the road to Samarkand and its "
        "gateway and madrasas are the oldest standing buildings near the "
        "capital."),
"pamirs": dict(
    # Was `pamir-highway`, pointed at the road. The M41's article has no P625 —
    # a road is a line, not a point — and the honesty rule wants a real
    # coordinate, so the record is the range and the highway is a chip on it.
    name="The Pamirs", slug="Pamir Mountains", country="Tajikistan",
    region="Gorno-Badakhshan", type="mountain", tag="hidden", emoji="🛣️",
    sounds=["mountain-wind.mp3"],
    highlights=[("Pamir Highway", "M41_highway"),
                ("Ak-Baital Pass", None),
                ("Karakul", "Karakul_(Tajikistan)"),
                ("Khorugh", "Khorugh"),
                ("Wakhan Corridor", "Wakhan_Corridor")],
    blurb="A cold desert of 4,000 m plateaus that Central Asians call the Roof "
          "of the World, where the Tian Shan, the Karakoram, the Hindu Kush and "
          "the Himalaya all meet. The M41 — the Pamir Highway, second-highest "
          "road on Earth — runs 1,200 km across it from Osh to Dushanbe with "
          "the Afghan border alongside for hundreds of kilometres.",
    fact="Its high point, the Ak-Baital pass, is 4,655 m; Lake Karakul below "
         "it sits in a 25 km meteorite impact crater and is frozen for more "
         "than half the year.",
    tip="The Wakhan branch follows the Panj river with Afghanistan visible "
        "across fifty metres of water and the Hindu Kush behind it — villages, "
        "fields and people, close enough to wave to."),
"iskanderkul": dict(
    name="Iskanderkul", slug="Iskanderkul", country="Tajikistan",
    region="Sughd Region", type="nature", tag="hidden", emoji="🏞️",
    sounds=["waterfall.mp3"],
    highlights=[("Fann Mountains", "Fann_Mountains"),
                ("Fann Niagara", None),
                ("Zeravshan Range", "Zeravshan_Range")],
    blurb="A turquoise glacial lake at 2,195 m in the Fann Mountains, dammed "
          "by an ancient landslide, with a 38 m waterfall at its outflow. The "
          "name means 'Alexander's lake' — the local story is that his horse "
          "drowned in it, and still comes out on moonlit nights.",
    fact="The Fanns are limestone and shale rather than granite, which is why "
         "their lakes run through that range of blues and greens — the colour "
         "is suspended rock flour.",
    tip="The waterfall is a twenty-minute walk downstream from the lake and "
        "you reach the top of it before you hear it."),
"khujand": dict(
    name="Khujand", slug="Khujand", country="Tajikistan", region="Sughd Region",
    type="history", tag="hidden", emoji="🕌", sounds=["city-hum.mp3"],
    highlights=[("Panjshanbe Bazaar", None),
                ("Syr Darya", "Syr_Darya"),
                ("Khujand Fortress", None),
                ("Sheikh Muslihiddin Mausoleum", None)],
    blurb="Tajikistan's second city, on the Syr Darya at the western gate of "
          "the Fergana Valley, and one of the oldest cities in Central Asia — "
          "Alexander founded Alexandria Eschate, 'the furthest', on this spot "
          "in 329 BC.",
    fact="Its citadel held out against Genghis Khan in 1220 under Timur Malik, "
          "who fought a retreat down the river on rafts; the Mongols levelled "
          "the city afterwards.",
    tip="Panjshanbe — 'Thursday' — is one of the great covered bazaars of "
        "Central Asia, a 1950s hall with a painted facade, and it trades every "
        "day despite the name."),

# ============================== TURKMENISTAN ==============================
"ashgabat": dict(
    name="Ashgabat", slug="Ashgabat", country="Turkmenistan",
    region="Ahal Region", type="city", tag="hidden", emoji="🏛️",
    sounds=["desert-wind.mp3"],
    highlights=[("Neutrality Monument", "Neutrality_Monument"),
                ("Türkmenbaşy Ruhy Mosque", "Türkmenbaşy_Ruhy_Mosque"),
                ("Nisa", "Nisa,_Turkmenistan"),
                ("Kopet Dag", "Kopet_Dag")],
    blurb="A capital rebuilt in white marble between the Karakum desert and "
          "the Iranian border — the government has clad hundreds of buildings "
          "in Italian marble since the 1990s, on empty ceremonial boulevards, "
          "in a place where summer passes 45 °C.",
    fact="It holds the Guinness record for the highest density of white marble "
         "buildings in the world: 543 of them covering over four and a half "
         "million square metres.",
    tip="Old Nisa, 18 km out, is the earth-walled capital of the Parthian "
        "empire — the power that fought Rome to a standstill for three "
        "centuries."),
"darvaza": dict(
    name="Darvaza Gas Crater", slug="Darvaza gas crater",
    country="Turkmenistan", region="Ahal Region", type="desert", tag="hidden",
    emoji="🔥", sounds=["desert-wind.mp3"],
    highlights=[("Karakum Desert", "Karakum_Desert"),
                ("Derweze", "Derweze")],
    blurb="A 69 m hole in the Karakum desert that has been on fire since at "
          "least the 1980s — a collapsed gas field that geologists set alight "
          "expecting it to burn out in weeks. Turkmens call it the Gates of "
          "Hell and it is the country's best-known sight.",
    fact="The president ordered it extinguished in 2010 and again in 2022, on "
          "environmental and economic grounds; it is still burning, and nobody "
          "has worked out how to put it out.",
    tip="It is unremarkable by day and extraordinary at night — the standard "
        "visit is to camp on the rim, three hours north of Ashgabat on a "
        "desert track."),
"merv": dict(
    name="Merv", slug="Merv", country="Turkmenistan", region="Mary Region",
    type="history", tag="hidden", emoji="🏜️", sounds=["desert-wind.mp3"],
    highlights=[("Great Kyz Kala", None),
                ("Mausoleum of Sultan Sanjar", None),
                ("Mary, Turkmenistan", "Mary,_Turkmenistan"),
                ("Murghab River", "Murghab_River")],
    blurb="Five walled cities built beside one another over two thousand "
          "years on an oasis in the Karakum — Achaemenid, Seleucid, Sasanian, "
          "Seljuk — and by the twelfth century, on some counts, the largest "
          "city in the world.",
    fact="The Mongols destroyed it in 1221 and the chroniclers' casualty "
          "figures run into the hundreds of thousands; the site was never "
          "fully reoccupied, which is why the plans of all five cities are "
          "still legible from the air.",
    tip="The Kyz Kala are corrugated mud-brick fortresses with walls like "
        "organ pipes — a Sasanian building type that survives essentially "
        "nowhere else."),
"konye-urgench": dict(
    name="Konye-Urgench", slug="Konye-Urgench", country="Turkmenistan",
    region="Daşoguz Region", type="history", tag="hidden", emoji="🗼",
    sounds=["desert-wind.mp3"],
    highlights=[("Kutlug Timur Minaret", None),
                ("Turabek Khanym Mausoleum", None),
                ("Amu Darya", "Amu_Darya")],
    blurb="The capital of Khorezm, sacked by the Mongols in 1221 and again by "
          "Timur in 1388, then abandoned when the Amu Darya changed course. "
          "What is left stands scattered across open ground: a few mausoleums "
          "and the tallest minaret in Central Asia.",
    fact="The Kutlug Timur minaret is 60 m of fourteenth-century brickwork "
          "with no mosque left around it, leaning slightly, standing alone in "
          "flat desert.",
    tip="The Turabek Khanym mausoleum's inner dome is a mosaic of 365 "
        "segments under a band of 24 arches and 12 windows — a calendar built "
        "into a ceiling."),

# ============================== MONGOLIA ==============================
"karakorum": dict(
    name="Karakorum", slug="Karakorum", country="Mongolia",
    region="Övörkhangai", type="history", tag="hidden", emoji="🐎",
    sounds=["wind.mp3"],
    highlights=[("Erdene Zuu Monastery", "Erdene_Zuu_Monastery"),
                ("Orkhon Valley", "Orkhon_Valley"),
                ("Orkhon Waterfall", None),
                ("Stone turtles", None)],
    blurb="The capital of the Mongol empire for forty years in the thirteenth "
          "century, on the Orkhon river in the grassland heart of the country "
          "— a city of perhaps ten thousand people administering the largest "
          "contiguous land empire in history, then abandoned and quarried "
          "away.",
    fact="William of Rubruck described a silver tree at the khan's palace "
         "with four pipes pouring wine, mare's milk, mead and rice beer, "
         "worked by a mechanical angel — built by a French goldsmith taken "
         "prisoner in Hungary.",
    tip="Erdene Zuu, built in 1585 from Karakorum's stones, is walled by 108 "
        "white stupas; the Orkhon valley around it has been the seat of "
        "steppe power since the Turkic khaganates."),
"khuvsgul": dict(
    name="Lake Khövsgöl", slug="Lake Khövsgöl", country="Mongolia",
    region="Khövsgöl Province", type="nature", tag="hidden", emoji="🏞️",
    sounds=["wilderness.mp3"],
    highlights=[("Khoridol Saridag", None),
                ("Khatgal", None),
                ("Hankh", None),
                ("Uushigiin Uvur deer stones", None)],
    blurb="A lake 136 km long in the northern taiga against the Russian "
          "border, holding 70% of Mongolia's fresh water and about 1% of the "
          "world's — and connected to Baikal, 200 km away, by its outflow. "
          "Mongolians call it the Younger Sister.",
    fact="It freezes solid enough by February for trucks to drive across it, "
         "and the ice can carry two metres of thickness; convoys used the "
         "lake as a winter road for decades.",
    tip="The Dukha, in the mountains west of the lake, are among the last "
        "reindeer herders in the world — a few hundred people in perhaps "
        "forty households."),
"terelj": dict(
    name="Gorkhi-Terelj", slug="Gorkhi-Terelj National Park",
    country="Mongolia", region="Töv Province", type="nature", tag="hidden",
    emoji="🪨", sounds=["wilderness.mp3"],
    highlights=[("Turtle Rock", None),
                ("Genghis Khan Equestrian Statue", "Equestrian_statue_of_Genghis_Khan"),
                ("Aryabal Meditation Temple", None),
                ("Tuul River", "Tuul_River")],
    blurb="An hour and a half from Ulaanbaatar and the easiest place in "
          "Mongolia to see the country proper: granite tors standing out of "
          "alpine meadow, larch forest, herders' gers, and horses grazing "
          "loose all summer.",
    fact="On the way out stands a 40 m stainless-steel Genghis Khan on "
          "horseback, the largest equestrian statue in the world; you take a "
          "lift up through the horse and come out on its head.",
    tip="Many of the gers along the valley are working households that take "
        "guests, not resorts — staying in one is the ordinary way to visit."),
"altai-tavan-bogd": dict(
    name="Altai Tavan Bogd", slug="Altai Tavan Bogd", country="Mongolia",
    region="Bayan-Ölgii", type="mountain", tag="hidden", emoji="🦅",
    sounds=["mountain-wind.mp3"],
    highlights=[("Khüiten Peak", "Khüiten_Peak"),
                ("Potanin Glacier", None),
                ("Ölgii", "Ölgii"),
                ("Tsagaan Salaa petroglyphs", "Tsagaan_Salaa_petroglyphs")],
    blurb="The five sacred peaks in Mongolia's far west, where the country "
          "meets Russia and China at a single point. Khüiten, 4,374 m, is the "
          "highest ground in Mongolia, and the Potanin below it is the "
          "longest glacier in the country at 14 km.",
    fact="This is Kazakh Mongolia — the province is mostly Kazakh-speaking, "
          "and hunting with golden eagles from horseback is still practised "
          "here by a few hundred berkutchi, one of the last places it "
          "survives.",
    tip="The petroglyph complex in the valleys below runs from about 11,000 BC "
        "to the Bronze Age — one continuous record of what people here hunted "
        "as the climate changed."),
}


# ---------------------------------------------------------------------------
# FILL — places already on disk that were left as skeletons.
#
# Moscow is the one that matters: it has an EMPTY `highlights` array, and
# `enrich_monuments.py` spends highlights as its search terms, so the capital of
# the largest country on Earth could never earn a monument tab no matter how
# many times the sweep ran. The rest are missing `region` (which `passport.js`
# prints under the place name, so an empty one is visible) or the three prose
# fields the arrival card reads.
#
# Nothing here overwrites a field that already has a value.
# ---------------------------------------------------------------------------
FILL = {
# --- region only (these already have their editorial content) ---
"yekaterinburg": dict(region="Sverdlovsk Oblast"),
"novosibirsk": dict(region="Siberia"),
"irkutsk": dict(region="Irkutsk Oblast"),
"samarkand": dict(region="Samarkand Region"),
"bukhara": dict(region="Bukhara Region"),
"gobi-desert": dict(region="Ömnögovi"),

# --- RUSSIA ---
"moscow": dict(
    region="Moscow",
    highlights=[("Red Square", "Red_Square"),
                ("Saint Basil's Cathedral", "Saint_Basil's_Cathedral"),
                ("Moscow Kremlin", "Moscow_Kremlin"),
                ("Moscow Metro", "Moscow_Metro"),
                ("Bolshoi Theatre", "Bolshoi_Theatre"),
                ("Novodevichy Convent", "Novodevichy_Convent")],
    blurb="A capital built in rings around a fortress, on a river that bends "
          "through the middle of it — the Kremlin walls, then the boulevard "
          "ring, then the garden ring, then everything else, out to twelve "
          "million people. Nine hundred years of Russian power have all been "
          "administered from the same 28 hectares.",
    fact="The Moscow Metro was built from 1935 as 'palaces for the people' — "
         "chandeliers, mosaics and marble 80 m down, deep enough that the "
         "stations served as bomb shelters and a command post during the war.",
    tip="Novodevichy's cemetery holds Chekhov, Gogol, Bulgakov, Shostakovich "
        "and Yeltsin, and the convent beside it is the quietest sixteenth-"
        "century thing in the city."),

# --- POLAND ---
"krakow": dict(
    region="Lesser Poland",
    blurb="Poland's royal capital until 1596 and the one large Polish city the "
          "Second World War left standing — so its market square, cloth hall "
          "and castle hill are original rather than rebuilt. A university town "
          "since 1364, and still visibly one.",
    fact="A trumpeter plays the hejnał from the tower of St. Mary's every hour "
         "and breaks off mid-note, for a bugler who was supposedly shot in the "
         "throat sounding the alarm during a thirteenth-century Mongol raid.",
    tip="Kazimierz, the old Jewish quarter, is a fifteen-minute walk south and "
        "has seven surviving synagogues within a few streets of each other."),

# --- BULGARIA ---
"sofia": dict(
    region="Sofia City Province",
    blurb="A capital under a 2,290 m mountain, with Roman streets exposed "
          "under the modern ones and a mosque, a synagogue, a Catholic church "
          "and an Orthodox cathedral within two hundred metres of one another "
          "in the centre. Its motto is 'grows but does not age'.",
    fact="Serdica was Constantine the Great's favourite city — he is said to "
         "have called it 'my Rome' and considered making it his capital before "
         "settling on Byzantium.",
    tip="Vitosha, the mountain on the skyline, is inside the city boundary; "
        "a bus and a chairlift from the last metro stop put you on a plateau "
        "at 2,000 m."),

# --- ESTONIA ---
"tallinn": dict(
    region="Harju County",
    blurb="The most complete medieval town in northern Europe — a Hanseatic "
          "port whose walls, towers, merchant houses and guild halls came "
          "through six centuries and one war essentially intact, on a "
          "limestone bluff over the Gulf of Finland.",
    fact="Two kilometres of the town wall and twenty of its towers still "
         "stand, and Tallinn's town hall pharmacy has been trading on the same "
         "square since 1422 — one of the oldest continuously running shops in "
         "Europe.",
    tip="Toompea, the upper town, was the nobility's; the lower town was the "
        "merchants'. They were separate walled towns with gates between them "
        "that were locked at night, and you can still see the gates."),

# --- ROMANIA ---
"sighisoara": dict(
    blurb="A Saxon hill citadel in Transylvania that is still lived in — nine "
          "surviving guild towers, a covered wooden stair of 175 steps up to "
          "the school, and a clock tower with a wooden figure for each day of "
          "the week rotating at midnight.",
    fact="Vlad Dracul, father of Vlad the Impaler, lived in a house on the "
          "citadel square while minting coin for Wallachia; his son was "
          "probably born there around 1431.",
    tip="Climb the covered stairway to the church on the hill at dusk, when "
        "the day buses have gone and the citadel is a residential village "
        "again."),
"transylvania": dict(
    blurb="A plateau ringed on three sides by the Carpathians, held by "
          "Hungary, then the Ottomans, then Austria, and Romanian since 1918 — "
          "which is why one region has Saxon fortified churches, Hungarian "
          "castles, Romanian wooden villages and three languages on the road "
          "signs.",
    fact="Its Saxon villages fortified their churches rather than building "
          "castles: about 150 survive, with granaries and bacon-stores built "
          "into the walls so a village could sit out a siege inside its own "
          "church.",
    tip="The Carpathians here hold the largest brown bear population in Europe "
        "outside Russia — roughly 6,000 animals, in forest that was never "
        "fully cleared."),

# --- ARMENIA ---
"tatev-monastery": dict(
    region="Syunik Province",
    highlights=[("Wings of Tatev", "Wings_of_Tatev"),
                ("Vorotan", "Vorotan"),
                ("Devil's Bridge", None),
                ("Halidzor", None)],
    blurb="A ninth-century monastery on a headland above the Vorotan gorge in "
          "Armenia's far south, deliberately built where the cliffs fall away "
          "on three sides. It ran a university from the fourteenth century "
          "with several hundred students working on philosophy, calligraphy "
          "and manuscript illumination.",
    fact="The cable car that reaches it, the Wings of Tatev, is the longest "
         "non-stop reversible aerial tramway in the world at 5,752 m, and "
         "crosses the gorge 320 m above the river.",
    tip="The Gavazan column in the courtyard is an eighth-century pillar "
        "engineered to sway on its hinge in an earth tremor — an earthquake "
        "warning built in stone."),
}


# ---------------------------------------------------------------------------
# MACHINERY
# ---------------------------------------------------------------------------
COUNTRY_CODE = {
    "Russia": "RU", "Ukraine": "UA", "Belarus": "BY", "Moldova": "MD",
    "Estonia": "EE", "Latvia": "LV", "Lithuania": "LT", "Poland": "PL",
    "Romania": "RO", "Bulgaria": "BG", "Georgia": "GE", "Armenia": "AM",
    "Azerbaijan": "AZ", "Kazakhstan": "KZ", "Uzbekistan": "UZ",
    "Kyrgyzstan": "KG", "Tajikistan": "TJ", "Turkmenistan": "TM",
    "Mongolia": "MN",
}

# lat_min, lat_max, lng_min, lng_max — generous national bounding boxes.
# These are not borders. They only have to be tight enough that an American or
# Ohioan namesake falls outside, and loose enough never to reject a real place.
COUNTRY_BOX = {
    "Ukraine":      (44.0, 52.5, 22.0, 40.3),
    "Belarus":      (51.2, 56.3, 23.1, 32.8),
    "Moldova":      (45.4, 48.6, 26.5, 30.2),
    "Estonia":      (57.4, 59.8, 21.7, 28.3),
    "Latvia":       (55.6, 58.2, 20.9, 28.3),
    "Lithuania":    (53.8, 56.5, 20.9, 26.9),
    "Poland":       (48.9, 55.0, 14.0, 24.2),
    "Romania":      (43.5, 48.3, 20.2, 29.8),
    "Bulgaria":     (41.2, 44.3, 22.3, 28.7),
    "Georgia":      (41.0, 43.6, 39.9, 46.8),
    "Armenia":      (38.8, 41.4, 43.4, 46.7),
    "Azerbaijan":   (38.3, 42.0, 44.7, 50.6),
    "Kazakhstan":   (40.5, 55.5, 46.4, 87.4),
    "Uzbekistan":   (37.1, 45.7, 55.9, 73.2),
    "Kyrgyzstan":   (39.1, 43.3, 69.2, 80.3),
    "Tajikistan":   (36.6, 41.1, 67.3, 75.2),
    "Turkmenistan": (35.1, 42.9, 52.4, 66.7),
    "Mongolia":     (41.5, 52.2, 87.5, 120.0),
}

# Russia is the exception the docstring promises. Its landmass runs from
# Kaliningrad at 19.6°E east across the antimeridian to Big Diomede at 169°W,
# so there is no single [lng_min, lng_max] span that contains it: the naive one
# is (-180, 180), which accepts every point on Earth and tests nothing. The
# longitude condition is a union of two arcs instead.
RU_LAT = (41.1, 82.1)
RU_ARCS = ((19.0, 180.0), (-180.0, -168.0))


def in_country(country, lat, lng):
    """Is this P625 plausibly inside the country the record claims?"""
    if country == "Russia":
        return (RU_LAT[0] <= lat <= RU_LAT[1]
                and any(a <= lng <= b for a, b in RU_ARCS))
    lo_lat, hi_lat, lo_lng, hi_lng = COUNTRY_BOX[country]
    return lo_lat <= lat <= hi_lat and lo_lng <= lng <= hi_lng


def flag(code):
    """ISO alpha-2 -> flag emoji, the same derivation build_countries.py uses."""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


def slugs_wanted():
    """Every slug this batch needs an answer about, place-level and highlight."""
    out = []
    for batch in (NEW_EUROPE, NEW_ASIA):
        for spec in batch.values():
            out.append(spec["slug"])
            out += [s for _, s in spec["highlights"] if s]
    for spec in FILL.values():
        out += [s for _, s in spec.get("highlights", []) if s]
    return out


class Notes:
    """Collects one line per verdict so the dry run reads like verify_wiki."""

    def __init__(self):
        self.rows = []
        self.unresolved = 0

    def add(self, kind, where, what, why=""):
        self.rows.append((kind, where, what, why))
        if kind == "UNRESOLVED":
            self.unresolved += 1

    def print(self):
        order = {"UNRESOLVED": 0, "NOCOORD": 1, "OUTSIDE": 2, "MISSING": 3,
                 "SELF": 4, "FAR": 5, "REDIRECT": 6, "FIXENC": 7}
        for kind, where, what, why in sorted(
                self.rows, key=lambda r: (order.get(r[0], 9), r[1], r[2])):
            print(f"{kind:<10} {where:<26} {what:<46} {why}")
        counts = {}
        for kind, *_ in self.rows:
            counts[kind] = counts.get(kind, 0) + 1
        if counts:
            print("\n" + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))


def link(slug, got, notes, where, own=None):
    """The canonical title to store for `slug`, or None to keep the chip text-only.

    A highlight that resolves to the record's own article is worse than a dead
    link — it promises a second place and delivers the one you are standing in.
    """
    e = got.get(slug) or {}
    if "title" not in e and not e.get("missing"):
        notes.add("UNRESOLVED", where, slug, "no answer from the API — rerun")
        return None
    if e.get("missing"):
        notes.add("MISSING", where, slug, "no article — kept as a text chip")
        return None
    title = e["title"]
    if own and title == own:
        notes.add("SELF", where, slug, "resolves to the place itself — unlinked")
        return None
    if e.get("redirect"):
        notes.add("REDIRECT", where, slug, f"-> {title}")
    return title


def highlights(spec, got, notes, where, own):
    out = []
    for name, slug in spec.get("highlights", []):
        h = {"name": name}
        t = link(slug, got, notes, where, own) if slug else None
        if t:
            h["wikipedia_slug"] = t
        out.append(h)
    return out


def far_check(loc, hl, got, notes, where):
    """Every highlight with a coordinate, measured against the record itself."""
    if loc.get("type") in AREA_TYPES:
        return
    here = loc.get("coordinates") or {}
    if here.get("lat") is None:
        return
    for h in hl:
        s = h.get("wikipedia_slug")
        e = got.get(s) or {}
        if e.get("lat") is None:
            continue
        d = haversine((here["lat"], here["lng"]), (e["lat"], e["lng"]))
        if d > FAR_KM:
            notes.add("FAR", where, f"{h['name']} [{s}]",
                      f"{d:,.0f} km from {loc['name']}")


def make(pid, spec, continent, got, notes):
    """A complete record from a NEW entry, or None if it cannot be trusted."""
    title = link(spec["slug"], got, notes, pid)
    if not title:
        notes.add("NOCOORD", pid, spec["slug"], "no article — place not added")
        return None
    e = got[spec["slug"]]
    lat, lng = e.get("lat"), e.get("lng")
    if lat is None:
        notes.add("NOCOORD", pid, title, "no P625 — place not added")
        return None
    if not in_country(spec["country"], lat, lng):
        notes.add("OUTSIDE", pid, title,
                  f"P625 is {lat:.3f},{lng:.3f} — not in {spec['country']}")
        return None

    code = COUNTRY_CODE[spec["country"]]
    loc = {
        "id": pid,
        "name": spec["name"],
        "country": spec["country"],
        "country_code": code,
        "country_flag": flag(code),
        "continent": continent,
        "region": spec["region"],
        "type": spec["type"],
        "tag": spec["tag"],
        "emoji": spec["emoji"],
        "coordinates": {"lat": lat, "lng": lng},
        "street_view": {"lat": lat, "lng": lng,
                        "heading": 0, "pitch": 0, "fov": 90},
        "wikipedia_slug": title,
        "sounds": list(spec["sounds"]),
        "highlights": highlights(spec, got, notes, pid, title),
        "blurb": spec["blurb"],
        "fun_fact": spec["fact"],
        "hidden_gem_tip": spec["tip"],
    }
    far_check(loc, loc["highlights"], got, notes, pid)
    return loc


def fill(loc, spec, got, notes):
    """Fill only what is empty. Returns the field names actually written."""
    wrote = []
    if spec.get("region") and not loc.get("region"):
        loc["region"] = spec["region"]
        wrote.append("region")
    if spec.get("highlights") and not loc.get("highlights"):
        loc["highlights"] = highlights(spec, got, notes, loc["id"],
                                       loc.get("wikipedia_slug"))
        far_check(loc, loc["highlights"], got, notes, loc["id"])
        wrote.append("highlights")
    for key, src in (("blurb", "blurb"), ("fun_fact", "fact"),
                     ("hidden_gem_tip", "tip")):
        if spec.get(src) and not loc.get(key):
            loc[key] = spec[src]
            wrote.append(key)
    return wrote


def fix_encoding(locs, notes):
    """A percent-encoded slug is a URL, not a title.

    MediaWiki decodes it and answers anyway, so an audit never sees it — but
    every consumer that concatenates it into a URL is one encode away from a
    404. Decode it back to the title it always was.
    """
    n = 0
    for loc in locs:
        for holder in [loc] + list(loc.get("highlights") or []):
            s = holder.get("wikipedia_slug")
            if s and "%" in s:
                dec = urllib.parse.unquote(s)
                if dec != s:
                    holder["wikipedia_slug"] = dec
                    notes.add("FIXENC", loc["id"], s, f"-> {dec}")
                    n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="ignore the slug cache and ask Wikipedia again")
    ap.add_argument("--only", help="comma-separated ids — build just these")
    args = ap.parse_args()

    # A batch script is a record of a batch, so a later addition shouldn't
    # mean deleting the record or forking a near-identical file: --only keeps
    # the roster intact and builds the one place you name. Without it the
    # collision guard below (correctly) refuses, because everything else in
    # the roster is already on disk.
    new_eu, new_as, fill_now = NEW_EUROPE, NEW_ASIA, FILL
    if args.only:
        want = {i.strip() for i in args.only.replace(" ", ",").split(",")} - {""}
        known = set(NEW_EUROPE) | set(NEW_ASIA) | set(FILL)
        stray = sorted(want - known)
        if stray:
            sys.exit(f"--only names ids this script doesn't define: {stray}")
        new_eu = {k: v for k, v in NEW_EUROPE.items() if k in want}
        new_as = {k: v for k, v in NEW_ASIA.items() if k in want}
        fill_now = {k: v for k, v in FILL.items() if k in want}

    # (path, continent, NEW dict) — one pass writes both region files.
    batches = [(EUROPE, "Europe", new_eu), (ASIA, "Asia", new_as)]
    docs = {p: json.loads(p.read_text(encoding="utf-8")) for p, _, _ in batches}
    by_id = {l["id"]: l for d in docs.values() for l in d["locations"]}

    unknown = [p for p in fill_now if p not in by_id]
    if unknown:
        sys.exit(f"FILL names places that are not on disk: {unknown}")
    clash = [p for _, _, n in batches for p in n if p in by_id]
    if clash:
        sys.exit(f"NEW would collide with existing ids: {clash}")
    dupes = set(new_eu) & set(new_as)
    if dupes:
        sys.exit(f"same id in both batches: {sorted(dupes)}")

    want = slugs_wanted()
    print(f"resolving {len(set(want))} slug(s) against Wikipedia/Wikidata …")
    got = Resolver(refresh=args.refresh).resolve(want)

    notes = Notes()
    added = {}          # path -> [new records]
    for path, continent, new in batches:
        rows = []
        for pid, spec in new.items():
            loc = make(pid, spec, continent, got, notes)
            if loc:
                rows.append(loc)
        added[path] = rows

    filled = []
    for pid, spec in fill_now.items():
        wrote = fill(by_id[pid], spec, got, notes)
        if wrote:
            filled.append((pid, wrote))

    every = [l for d in docs.values() for l in d["locations"]]
    every += [l for rows in added.values() for l in rows]
    enc = fix_encoding(every, notes)

    notes.print()
    total_new = len(new_eu) + len(new_as)
    total_added = sum(len(r) for r in added.values())
    print(f"\n{total_added}/{total_new} new place(s), {len(filled)} filled, "
          f"{enc} slug(s) decoded")
    for path, _, _ in batches:
        print(f"  {path.name:<14} +{len(added[path])}")
    for pid, wrote in filled:
        print(f"  fill {pid:<26} {', '.join(wrote)}")
    made = {l["id"] for rows in added.values() for l in rows}
    skipped = [p for _, _, n in batches for p in n if p not in made]
    if skipped:
        print(f"  ⚠ not added: {skipped}")

    if notes.unresolved:
        # A throttled request is not a verdict. Refuse to write a half-checked
        # file rather than silently drop the links the API never answered about.
        sys.exit(f"\n{notes.unresolved} slug(s) unresolved — rerun before --apply")
    if not args.apply:
        print("\ndry run — pass --apply to write")
        return

    for path, _, _ in batches:
        doc = docs[path]
        doc["locations"] = doc["locations"] + added[path]
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                        encoding="utf-8")
        print(f"✓ wrote {len(doc['locations'])} locations -> "
              f"{path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()



