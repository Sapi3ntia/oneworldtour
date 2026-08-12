#!/usr/bin/env python3
"""The content table for fill_highlights.py — see that file for the rules.

Kept separate because it is 90% prose and 10% structure, and a 1,500-line
literal in the middle of the merge logic makes the logic unreadable. Each entry
is keyed by an existing place id:

    "uluru": dict(
        region=...,                       # optional, only if the record has none
        highlights=[(name, slug_or_None), ...],
        blurb=..., fact=..., tip=...),

Slugs here are a first guess; fill_highlights.py resolves every one of them
live and canonicalises redirects, so what lands on disk is what Wikipedia
actually calls the article. A slug that turns out not to exist is reported and
the chip is written unlinked rather than broken.
"""

FILL = {

# ═══════════════════════════════ AFRICA ═══════════════════════════════
"chefchaouen": dict(
    region="Tangier-Tetouan-Al Hoceima",
    highlights=[("Plaza Uta el-Hammam", None),
                ("Kasbah of Chefchaouen", None),
                ("Spanish Mosque", None),
                ("Ras el-Maa", None),
                ("Rif Mountains", "Rif")],
    blurb="A whole hill town painted in blue, folded into the Rif Mountains of "
          "northern Morocco. Founded in 1471 as a fortress against the "
          "Portuguese, it stayed closed to outsiders for centuries, and the "
          "blue washes over walls, steps, doors and flowerpots alike.",
    fact="Nobody agrees why it is blue. The stories run from Jewish refugees "
         "in the 1930s bringing the colour with them, to a belief that blue "
         "keeps mosquitoes off, to the simple fact that it sells.",
    tip="Walk up to the ruined Spanish Mosque on the eastern hill for sunset — "
        "half an hour up, and the whole blue town is below you at once."),
"sahara-at-merzouga": dict(
    region="Drâa-Tafilalet",
    highlights=[("Erg Chebbi", "Erg_Chebbi"),
                ("Merzouga", None),
                ("Dayet Srji", None),
                ("Khamlia", None)],
    blurb="The edge of the Sahara at Erg Chebbi, where a sea of orange dunes "
          "rises 150 m straight out of flat stony desert with no warning at "
          "all. Camel caravans go out from the village of Merzouga at the foot "
          "of them and camp between the crests.",
    fact="Erg Chebbi is only about 22 km long — a single isolated dune field, "
         "not the endless Sahara of the films, which is why you can stand on "
         "its highest crest and see hard desert on every side.",
    tip="A seasonal lake, Dayet Srji, appears west of the dunes after rain and "
        "fills with flamingos. Most visitors never look behind them."),
"casablanca": dict(
    region="Casablanca-Settat",
    highlights=[("Hassan II Mosque", "Hassan_II_Mosque"),
                ("Old Medina", None),
                ("Corniche", None),
                ("Mahkama du Pacha", None),
                ("Villa des Arts", None)],
    blurb="Morocco's largest city and its economic engine — a working Atlantic "
          "port of art deco boulevards and glass towers rather than a tourist "
          "medina. The film was shot in Hollywood and the city has been "
          "living that down ever since.",
    fact="The Hassan II Mosque stands partly over the water, has room for "
         "105,000 worshippers, and carries the tallest minaret in the world at "
         "210 m, with a laser on top aimed at Mecca.",
    tip="It is one of the very few mosques in Morocco non-Muslims may enter, "
        "on guided tours several times a day — the glass floor over the "
        "Atlantic is the reason to go."),
"nairobi": dict(
    region="Nairobi County",
    highlights=[("Nairobi National Park", "Nairobi_National_Park"),
                ("Kenyatta International Convention Centre",
                 "Kenyatta_International_Convention_Centre"),
                ("David Sheldrick Wildlife Trust", None),
                ("Karen Blixen Museum", "Karen_Blixen_Museum"),
                ("Uhuru Park", "Uhuru_Park")],
    blurb="East Africa's business capital, a fast, green, high-altitude city "
          "of five million on the edge of the Rift Valley — and the only "
          "capital city on Earth with a full national park inside its limits.",
    fact="Lions, rhinos and giraffes range across Nairobi National Park with "
         "the city skyline directly behind them; the park is fenced on three "
         "sides and left open on the fourth so the herds can still migrate.",
    tip="The elephant orphanage opens to the public for one hour a day, when "
        "the keepers bring the calves in for their milk."),
"maasai-mara": dict(
    region="Narok County",
    highlights=[("Mara River", "Mara_River"),
                ("Serengeti", "Serengeti"),
                ("Oloololo Escarpment", None),
                ("Talek River", None)],
    blurb="1,500 km² of open savanna in southwestern Kenya, continuous with "
          "the Serengeti across the Tanzanian border — flat gold grass, "
          "scattered acacias, and the highest density of big cats anywhere in "
          "Africa.",
    fact="Around 1.3 million wildebeest and several hundred thousand zebra "
         "cross the Mara River here between July and October, and the "
         "crossings are chaotic enough that the drownings alone feed the "
         "river's crocodiles for the year.",
    tip="Balloon safaris lift off before dawn and land for breakfast on the "
        "grass — the only way to see how far the herds actually stretch."),
"mombasa": dict(
    region="Mombasa County",
    highlights=[("Fort Jesus", "Fort_Jesus"),
                ("Old Town", None),
                ("Diani Beach", "Diani_Beach"),
                ("Haller Park", "Haller_Park"),
                ("Nyali Beach", None)],
    blurb="Kenya's port and second city, on an island in a creek on the Indian "
          "Ocean — a Swahili trading town for a thousand years, with Arab, "
          "Portuguese, Omani and British layers stacked on top of each other "
          "in the same few streets.",
    fact="Fort Jesus changed hands at least nine times between 1631 and 1875; "
         "one Omani siege of the Portuguese garrison lasted 33 months and "
         "ended with eleven survivors.",
    tip="Haller Park is a rehabilitated cement quarry — a limestone pit "
        "replanted into forest with giraffes and hippos in it, and the best "
        "argument in East Africa that industrial land can be given back."),
"banjul": dict(
    region="Banjul",
    highlights=[("Arch 22", "Arch_22"),
                ("Albert Market", None),
                ("Kachikally Crocodile Pool", None),
                ("Gambia River", "Gambia_River"),
                ("Kunta Kinteh Island", "Kunta_Kinteh_Island")],
    blurb="One of Africa's smallest capitals — about 30,000 people on a sand "
          "island at the mouth of the Gambia River, reached by bridge or "
          "ferry, with a market, a cathedral, a mosque and not much traffic.",
    fact="The whole country is essentially the river plus a few kilometres "
         "either side of it: Gambia is 50 km across at its widest and 480 km "
         "long, drawn around a waterway rather than a territory.",
    tip="The upriver boat to Kunta Kinteh Island, the old slave-trading post "
        "in the middle of the Gambia, takes most of a day and is the country's "
        "most serious visit."),
"cape-town": dict(
    region="Western Cape",
    highlights=[("Table Mountain", "Table_Mountain"),
                ("Robben Island", "Robben_Island"),
                ("V&A Waterfront", "Victoria_&_Alfred_Waterfront"),
                ("Bo-Kaap", "Bo-Kaap"),
                ("Cape of Good Hope", "Cape_of_Good_Hope")],
    blurb="A city wrapped around a flat-topped mountain where two oceans meet "
          "— beaches, vineyards and townships within half an hour of each "
          "other, and a skyline dominated by a 1,000 m cliff that is often "
          "wearing a cloud.",
    fact="Table Mountain is roughly six times older than the Himalayas, and "
         "its 2,200 plant species — more than the whole of the United Kingdom "
         "— grow in an area smaller than greater London.",
    tip="Bo-Kaap's painted houses are a living neighbourhood, not a set. Buy "
        "something, ask before photographing doorways, and walk up to the "
        "mosque at the top for the view back over the bowl."),
"table-mountain": dict(
    region="Western Cape",
    highlights=[("Cape Town", "Cape_Town"),
                ("Lion's Head", "Lion's_Head_(Cape_Town)"),
                ("Table Mountain National Park", "Table_Mountain_National_Park"),
                ("Kirstenbosch", "Kirstenbosch_National_Botanical_Garden"),
                ("Devil's Peak", "Devil's_Peak_(Cape_Town)")],
    blurb="A three-kilometre level plateau of sandstone standing over Cape "
          "Town, reached by a rotating cable car or on foot up Platteklip "
          "Gorge. The 'tablecloth' of cloud pours over its northern edge when "
          "the southeaster blows and evaporates halfway down.",
    fact="The cable car's floor rotates through 360° during the five-minute "
         "ascent, so every passenger gets the whole view without moving — and "
         "the cars carry water up for the summit buildings as ballast.",
    tip="Walk down instead of riding down. Platteklip Gorge takes about 90 "
        "minutes on the way down and the light on the city is better in the "
        "late afternoon than from any photograph taken at the top."),
"kruger-national-park": dict(
    region="Mpumalanga",
    highlights=[("Skukuza", "Skukuza"),
                ("Sabie River", "Sabie_River"),
                ("Olifants River", "Olifants_River_(Limpopo)"),
                ("Blyde River Canyon", "Blyde_River_Canyon"),
                ("Punda Maria", None)],
    blurb="Nearly 20,000 km² of bushveld along South Africa's Mozambique "
          "border — the size of Wales, with 900 km of tarred road through it, "
          "which makes it one of the few great African parks you can drive "
          "yourself around in an ordinary car.",
    fact="Kruger holds the largest rhino population of any protected area on "
         "Earth, and the exact locations are a state secret: the park no "
         "longer publishes rhino counts by region, to keep them from poachers.",
    tip="Book a camp inside the gates and be on the road at opening. The first "
        "and last hour of light are when everything moves, and the gates shut "
        "hard at dusk — the fines are real."),

# ═════════════════════════ ANCIENT ANOMALIES ═════════════════════════
"aa-murray-springs": dict(
    highlights=[("San Pedro River", "San_Pedro_River_(Arizona)"),
                ("Sierra Vista", "Sierra_Vista,_Arizona"),
                ("Clovis points", None),
                ("Black mat layer", None)],
    fact="The dark 'black mat' layer that seals the Clovis-era surface here is "
         "found at dozens of sites across North America, always at the same "
         "depth and always with no mammoth bones above it.",
    tip="The site is open ground on the San Pedro Riparian National "
        "Conservation Area — no gate, no ticket, and interpretive signs where "
        "the mammoth kill was excavated."),
"aa-acre-geoglyphs": dict(
    highlights=[("Acre", "Acre_(state)"),
                ("Rio Branco", "Rio_Branco,_Acre"),
                ("Amazon rainforest", "Amazon_rainforest"),
                ("Jaco Sá", None)],
    fact="More than 450 geometric earthworks have been found in Acre since "
         "cattle ranching cleared the forest off them from the 1970s onward — "
         "perfect circles and squares up to 300 m across, and the forest that "
         "hid them turns out to have grown over the people who dug them.",
    tip="Fazenda Colorada and Jaco Sá are the two enclosures set up for "
        "visitors, both within an hour or two of Rio Branco on the BR-317."),
"aa-monte-alegre": dict(
    highlights=[("Monte Alegre", "Monte_Alegre,_Pará"),
                ("Serra da Lua", None),
                ("Amazon River", "Amazon_River"),
                ("Caverna da Pedra Pintada", None)],
    fact="The painted cave at Monte Alegre was dated to about 11,200 years "
         "ago, which put people deep in the Amazon at the same time as Clovis "
         "hunters in North America — and overturned the idea that rainforest "
         "was too poor to support early settlement.",
    tip="The park is reached by boat from Santarém and then a climb up the "
        "escarpment; the ochre handprints are on the ceiling of the rock "
        "shelter, best seen with the low sun coming in."),


# ══════════════════════════════ ASIA ══════════════════════════════
"osaka": dict(
    region="Kansai",
    highlights=[("Osaka Castle", "Osaka_Castle"),
                ("Dotonbori", "Dōtonbori"),
                ("Tsutenkaku", "Tsutenkaku"),
                ("Umeda Sky Building", "Umeda_Sky_Building"),
                ("Sumiyoshi Taisha", "Sumiyoshi_Taisha")],
    blurb="Japan's kitchen and its loudest city — a merchant town rather than "
          "an imperial one, flat, neon-lit and much less formal than Kyoto an "
          "hour away. Everything here points at food and at the canal-side "
          "signs above Dotonbori.",
    fact="Osaka's motto is *kuidaore* — roughly 'eat yourself bankrupt' — and "
         "the city takes it seriously enough that the Glico running man sign "
         "over the Ebisu bridge has been relit six times since 1935.",
    tip="The Umeda Sky Building's Floating Garden Observatory is an open-air "
        "ring 170 m up, reached by an escalator that crosses the gap between "
        "the two towers in mid-air."),
"mount-fuji": dict(
    region="Chūbu",
    highlights=[("Chureito Pagoda", "Arakurayama_Sengen_Park"),
                ("Lake Kawaguchi", "Lake_Kawaguchi"),
                ("Fuji Five Lakes", "Fuji_Five_Lakes"),
                ("Aokigahara", "Aokigahara"),
                ("Fujinomiya", "Fujinomiya,_Shizuoka")],
    blurb="A near-perfect volcanic cone of 3,776 m, visible from Tokyo on a "
          "clear winter morning and hidden behind cloud for much of the "
          "summer. It has been climbed as a pilgrimage for over a thousand "
          "years and painted more often than any other mountain on Earth.",
    fact="Fuji is still an active volcano; its last eruption, in 1707, dropped "
         "ash on Edo 100 km away for two weeks and left the Hōei crater on the "
         "southeastern flank that you can see from the Tokaido line.",
    tip="The official climbing season is only July to early September. Outside "
        "it the huts are shut and the mountain is a serious winter ascent — "
        "but the Chureito Pagoda view is best in the cold months anyway."),
"new-delhi": dict(
    region="Delhi",
    highlights=[("India Gate", "India_Gate"),
                ("Humayun's Tomb", "Humayun's_Tomb"),
                ("Rashtrapati Bhavan", "Rashtrapati_Bhavan"),
                ("Lodhi Gardens", "Lodhi_Gardens"),
                ("Connaught Place", "Connaught_Place,_New_Delhi")],
    blurb="The planned imperial capital laid out by Lutyens and Baker from "
          "1911 and inaugurated in 1931 — wide avenues, sandstone ministries "
          "and roundabouts, grafted onto a site where seven earlier cities had "
          "already been built and abandoned.",
    fact="Humayun's Tomb, finished in 1572, is the first great Mughal garden "
         "tomb and the direct architectural ancestor of the Taj Mahal, which "
         "borrowed its dome, its plinth and its four-part garden.",
    tip="Lodhi Gardens is 36 hectares of park with 15th-century tombs standing "
        "in it, free and open from sunrise — Delhi's best morning walk."),
"mumbai": dict(
    region="Maharashtra",
    highlights=[("Gateway of India", "Gateway_of_India"),
                ("Chhatrapati Shivaji Terminus", "Chhatrapati_Shivaji_Terminus"),
                ("Marine Drive", "Marine_Drive,_Mumbai"),
                ("Elephanta Caves", "Elephanta_Caves"),
                ("Haji Ali Dargah", "Haji_Ali_Dargah")],
    blurb="India's financial capital and the home of its film industry, built "
          "on seven islands joined by land reclamation into one dense, "
          "vertical, relentlessly busy peninsula of 20 million people.",
    fact="Chhatrapati Shivaji Terminus handles around three million passengers "
         "a day inside a Victorian Gothic building with gargoyles and stained "
         "glass — a working commuter station that is also a World Heritage "
         "Site.",
    tip="Haji Ali is reached by a causeway that the sea covers at high tide, "
        "so the shrine is cut off twice a day. Check the tide before you walk "
        "out to it."),
"kerala-backwaters": dict(
    region="Kerala",
    highlights=[("Alappuzha", "Alappuzha"),
                ("Vembanad Lake", "Vembanad"),
                ("Kumarakom", "Kumarakom"),
                ("Kollam", "Kollam"),
                ("Pathiramanal", None)],
    blurb="900 km of interlocking canals, rivers and lagoons running parallel "
          "to the Malabar coast behind a strip of sand — rice paddies below "
          "sea level, coconut palms, and converted rice barges that now carry "
          "people instead of grain.",
    fact="Much of the Kuttanad farmland here is farmed one to two metres below "
         "sea level, kept dry by dykes and pumps — one of very few places in "
         "the world where that is done, and the only one in India.",
    tip="Take a small punted canoe into the narrow canals rather than a big "
        "houseboat on the open lake. The village life the backwaters are "
        "famous for happens on channels a houseboat cannot enter."),
"busan": dict(
    region="Yeongnam",
    highlights=[("Gamcheon Culture Village", "Gamcheon_Culture_Village"),
                ("Haeundae Beach", "Haeundae_Beach"),
                ("Jagalchi Market", "Jagalchi_Market"),
                ("Beomeosa", "Beomeosa"),
                ("Gwangan Bridge", "Gwangandaegyo")],
    blurb="South Korea's second city and its biggest port, wrapped around "
          "mountains on the southeast coast — beaches inside the city, a fish "
          "market the size of a stadium, and a much slower pace than Seoul.",
    fact="Gamcheon began as a hillside refugee settlement during the Korean "
         "War, when Busan was the last unoccupied city in the country; it was "
         "repainted in blocks of colour by artists and residents in 2009.",
    tip="Jagalchi is at its best at 6am, when the boats land. The women who "
        "run the stalls — *jagalchi ajumma* — have been the market's public "
        "face for three generations."),
"jeju-island": dict(
    region="Jeju",
    highlights=[("Hallasan", "Hallasan"),
                ("Seongsan Ilchulbong", "Seongsan_Ilchulbong"),
                ("Manjanggul", "Manjanggul"),
                ("Jeongbang Falls", "Jeongbang_Waterfall"),
                ("Udo", "Udo_(Jeju_Province)")],
    blurb="A volcanic island 80 km south of the Korean mainland, built around "
          "a 1,947 m shield volcano and ringed by lava tubes, crater cones and "
          "black basalt coastline. It is Korea's honeymoon island and its "
          "warmest place.",
    fact="Jeju's *haenyeo* — women who free-dive for shellfish without air, "
         "often into their seventies — are on UNESCO's intangible heritage "
         "list, and the island's diving culture was historically matrilineal.",
    tip="Manjanggul is one of the longest lava tubes in the world and the "
        "public kilometre of it stays at 11°C year-round; take a jacket in "
        "August."),
"taipei": dict(
    region="Northern Taiwan",
    highlights=[("Taipei 101", "Taipei_101"),
                ("Chiang Kai-shek Memorial Hall",
                 "Chiang_Kai-shek_Memorial_Hall"),
                ("Longshan Temple", "Mengjia_Longshan_Temple"),
                ("Beitou", "Beitou_District"),
                ("Elephant Mountain", None)],
    blurb="A city in a basin ringed by green mountains, with hot springs "
          "inside the city limits, night markets on most blocks and one of the "
          "densest concentrations of good cheap food anywhere in Asia.",
    fact="Taipei 101 holds a 660-tonne steel pendulum between the 87th and "
         "92nd floors to damp typhoon sway — it is the largest such damper "
         "open to the public, and it visibly swings during storms.",
    tip="The Xiangshan (Elephant Mountain) trail is twenty minutes of steps "
        "from the metro and gives the postcard view of the tower — go an hour "
        "before sunset and stay for the lights."),
"taroko-gorge": dict(
    region="Hualien County",
    highlights=[("Swallow Grotto", None),
                ("Eternal Spring Shrine", "Eternal_Spring_Shrine"),
                ("Qingshui Cliff", "Qingshui_Cliff"),
                ("Liwu River", "Liwu_River"),
                ("Shakadang Trail", "Shakadang_Trail")],
    blurb="A marble canyon on Taiwan's east coast where the Liwu River has cut "
          "19 km of near-vertical gorge, and a road has been cut into the "
          "walls beside it — tunnels, overhangs and a river a long way down.",
    fact="Taiwan is rising about 5 mm a year as two plates collide, and the "
         "Liwu cuts down through the marble at roughly the same rate — the "
         "gorge is being deepened as fast as the island is being lifted.",
    tip="Sections close after earthquakes and typhoons and the 2024 quake shut "
        "much of the park. Check what is actually open before travelling, and "
        "wear the helmet they hand you at the Swallow Grotto."),
"ulaanbaatar": dict(
    region="Ulaanbaatar",
    highlights=[("Gandantegchinlen Monastery", "Gandantegchinlen_Monastery"),
                ("Sükhbaatar Square", "Sükhbaatar_Square"),
                ("Genghis Khan Equestrian Statue",
                 "Equestrian_statue_of_Genghis_Khan"),
                ("Zaisan Memorial", "Zaisan_Memorial"),
                ("Bogd Khan Palace", "Winter_Palace_of_the_Bogd_Khan")],
    blurb="The coldest capital city in the world, in a valley on the Tuul "
          "River with half of Mongolia's population in it — Soviet blocks, "
          "glass towers and whole districts of felt gers on the hillsides "
          "above them.",
    fact="Ulaanbaatar moved at least 25 times in its first 140 years as a "
         "mobile monastery town before settling on this site in 1778 — a "
         "capital city that was, quite literally, nomadic.",
    tip="The 26 m stainless-steel Genghis Khan statue is 54 km east of the "
        "city, and you take a lift up through the horse's mane to stand on its "
        "head and look at the steppe."),
"gobi-desert": dict(
    highlights=[("Khongoryn Els", "Khongoryn_Els"),
                ("Yolyn Am", "Yolyn_Am"),
                ("Bayanzag", "Bayanzag"),
                ("Gurvan Saikhan National Park",
                 "Gobi_Gurvansaikhan_National_Park")],
    blurb="1.3 million km² of cold desert across southern Mongolia and "
          "northern China — mostly bare rock and gravel steppe rather than "
          "sand, grazed by camels, and swinging from +40°C to −40°C over the "
          "year.",
    fact="Roy Chapman Andrews found the first scientifically recognised "
         "dinosaur eggs at the Flaming Cliffs of Bayanzag in 1923, and "
         "protoceratops and velociraptor fossils are still weathering out of "
         "that same red sandstone.",
    tip="Yolyn Am is a narrow gorge in the Gobi that holds a sheet of ice deep "
        "into the summer — desert at the entrance, ice underfoot an hour's "
        "walk in."),
"colombo": dict(
    region="Western Province",
    highlights=[("Galle Face Green", "Galle_Face_Green"),
                ("Gangaramaya Temple", "Gangaramaya_Temple"),
                ("Lotus Tower", "Lotus_Tower"),
                ("Independence Memorial Hall", "Independence_Memorial_Hall"),
                ("Pettah", "Pettah,_Colombo")],
    blurb="Sri Lanka's commercial capital and its port — a humid, green, "
          "low-rise city of colonial arcades, Buddhist and Hindu temples, "
          "mosques and churches within streets of each other, and a sea "
          "promenade that fills every evening.",
    fact="Colombo's natural harbour made it a stop on Indian Ocean trade "
         "routes 2,000 years ago; the Portuguese, Dutch and British each took "
         "it in turn, and the street grid of Pettah is still the Dutch one.",
    tip="Galle Face Green at dusk is the whole city out at once — kite "
        "sellers, isso wade stalls and families on the sea wall. It costs "
        "nothing and it is the best hour of the day."),
"tel-aviv": dict(
    region="Tel Aviv District",
    highlights=[("White City", "White_City_(Tel_Aviv)"),
                ("Jaffa", "Jaffa"),
                ("Rothschild Boulevard", "Rothschild_Boulevard"),
                ("Carmel Market", "Carmel_Market"),
                ("Tel Aviv Port", "Tel_Aviv_Port")],
    blurb="A Mediterranean beach city built on sand dunes from 1909, joined "
          "to the ancient port of Jaffa at its southern end — the modernist "
          "half is barely a century old and the harbour beside it has been "
          "working for four thousand years.",
    fact="Tel Aviv holds the largest concentration of Bauhaus and "
         "International Style buildings in the world — some 4,000 of them, put "
         "up by architects who had trained in Germany and left in the 1930s.",
    tip="Rothschild Boulevard has a shaded central walkway with kiosks along "
        "it and the best of the white buildings on either side — the Bauhaus "
        "Center runs a walking tour on Fridays."),
"dubai": dict(
    region="Dubai",
    highlights=[("Burj Khalifa", "Burj_Khalifa"),
                ("Palm Jumeirah", "Palm_Jumeirah"),
                ("Burj Al Arab", "Burj_Al_Arab"),
                ("Al Fahidi Historical Neighbourhood", "Al_Bastakiya"),
                ("Dubai Fountain", "Dubai_Fountain")],
    blurb="A city that has built almost everything it has since 1990 — the "
          "tallest building on Earth, an artificial palm-shaped island, indoor "
          "ski slopes — on a creek that was a pearling and trading harbour "
          "within living memory.",
    fact="The Burj Khalifa is 828 m tall and has no municipal sewer "
         "connection deep enough for it, so its waste is trucked out daily; "
         "people on the upper floors also break their Ramadan fast later, "
         "because the sun sets after it has set on the ground.",
    tip="Al Fahidi is the old coral-and-gypsum quarter with wind towers "
        "instead of air conditioning, and an abra across the creek to Deira "
        "still costs one dirham."),
"abu-dhabi": dict(
    region="Abu Dhabi",
    highlights=[("Sheikh Zayed Grand Mosque", "Sheikh_Zayed_Mosque"),
                ("Louvre Abu Dhabi", "Louvre_Abu_Dhabi"),
                ("Qasr Al Watan", "Qasr_Al_Watan"),
                ("Corniche", None),
                ("Yas Marina Circuit", "Yas_Marina_Circuit")],
    blurb="The UAE's capital, on an island connected by causeways — quieter, "
          "greener and more deliberate than Dubai, with the oil money spent on "
          "museums, a very large mosque and a Formula 1 circuit.",
    fact="The Sheikh Zayed Grand Mosque holds the world's largest hand-knotted "
         "carpet — 5,600 m², made by about 1,200 weavers in Iran — and 82 "
         "domes of white Macedonian marble.",
    tip="The mosque is free, open to non-Muslims outside prayer times, and "
        "best at dusk, when the lighting shifts through the phases of the moon "
        "across the whole facade."),
"riyadh": dict(
    region="Riyadh Province",
    highlights=[("Kingdom Centre", "Kingdom_Centre"),
                ("Masmak Fortress", "Masmak_Fortress"),
                ("Diriyah", "Diriyah"),
                ("Edge of the World", None),
                ("National Museum of Saudi Arabia",
                 "National_Museum_of_Saudi_Arabia")],
    blurb="Saudi Arabia's capital, a city of eight million in the middle of "
          "the Najd desert plateau — mud-brick fort at its historic core, "
          "glass towers around it, and an enormous amount of construction "
          "going on in between.",
    fact="Diriyah's At-Turaif district, the mud-brick capital of the first "
         "Saudi state until it was razed in 1818, is a World Heritage Site and "
         "has been rebuilt in the same Najdi technique it was destroyed in.",
    tip="The Edge of the World is a 300 m escarpment about 90 km northwest of "
        "the city where the Tuwaiq cliffs drop straight to an old sea floor — "
        "you need four-wheel drive and a full tank."),
"jeddah": dict(
    region="Mecca Province",
    highlights=[("Al-Balad", "Al-Balad,_Jeddah"),
                ("King Fahd's Fountain", "King_Fahd's_Fountain"),
                ("Jeddah Corniche", None),
                ("Al-Rahmah Mosque", "Al-Rahmah_Mosque")],
    blurb="Saudi Arabia's Red Sea port and the gateway for pilgrims to Mecca "
          "for fourteen centuries — humid, open and far less formal than "
          "Riyadh, with coral-stone merchant houses and carved wooden "
          "balconies in the old town.",
    fact="King Fahd's Fountain throws seawater 260 m into the air, higher than "
         "the Eiffel Tower, at around 375 km/h — the tallest fountain of its "
         "kind anywhere.",
    tip="Al-Balad's coral houses are being restored one at a time and the "
        "district comes alive after dark, when the heat drops and the cafés in "
        "the courtyards open."),
"doha": dict(
    region="Doha",
    highlights=[("Museum of Islamic Art", "Museum_of_Islamic_Art,_Doha"),
                ("Souq Waqif", "Souq_Waqif"),
                ("The Pearl", "The_Pearl_Island"),
                ("Katara Cultural Village", "Katara_Cultural_Village"),
                ("Doha Corniche", "Doha_Corniche")],
    blurb="Qatar's capital on a shallow bay, almost entirely built since the "
          "1990s — a wall of towers across the water from a restored souq, "
          "with the money from the world's third-largest gas reserves visible "
          "everywhere.",
    fact="I. M. Pei came out of retirement at 91 to design the Museum of "
         "Islamic Art, and insisted it be built on its own artificial island "
         "so that no future development could ever crowd it.",
    tip="Souq Waqif's falcon souq is upstairs and open to walk through — a row "
        "of shops selling hunting birds, with a dedicated falcon hospital at "
        "the end of it."),
"amman": dict(
    region="Amman Governorate",
    highlights=[("Amman Citadel", "Amman_Citadel"),
                ("Roman Theatre", "Roman_Theatre_(Amman)"),
                ("Rainbow Street", "Rainbow_Street"),
                ("King Abdullah I Mosque", "King_Abdullah_I_Mosque"),
                ("Jabal al-Weibdeh", None)],
    blurb="A white limestone city spread over nineteen hills, layered from "
          "Neolithic settlement through Roman Philadelphia to a modern Arab "
          "capital that has absorbed wave after wave of refugees since 1948.",
    fact="The Citadel hill has been occupied more or less continuously since "
         "the Bronze Age; the Temple of Hercules, a Byzantine church and an "
         "Umayyad palace all stand on the same summit within a few metres of "
         "each other.",
    tip="The Roman theatre still seats 6,000 and the acoustics work — stand on "
        "the orchestra floor and speak normally, and the top row hears you."),
"wadi-rum": dict(
    region="Aqaba Governorate",
    highlights=[("Jebel Rum", None),
                ("Khazali Canyon", None),
                ("Lawrence's Spring", None),
                ("Um Fruth Rock Bridge", None),
                ("Jebel Umm ad Dami", None)],
    blurb="A desert of red sand and sandstone-and-granite mountains rising "
          "sheer out of it in southern Jordan, inhabited by Bedouin and used "
          "as Mars by a dozen films. T. E. Lawrence campaigned through it and "
          "called it vast, echoing and godlike.",
    fact="Rock inscriptions across the valley record 12,000 years of human "
         "presence in Thamudic, Nabataean, Arabic and Greek — one canyon wall "
         "carries several scripts, several centuries apart, side by side.",
    tip="Sleep out. The camps run by Bedouin families put mattresses on the "
        "sand away from any light, and the sky over Rum is the point of the "
        "whole trip."),
"tehran": dict(
    region="Tehran Province",
    highlights=[("Golestan Palace", "Golestan_Palace"),
                ("Azadi Tower", "Azadi_Tower"),
                ("Milad Tower", "Milad_Tower"),
                ("Grand Bazaar", "Grand_Bazaar,_Tehran"),
                ("Tabiat Bridge", "Tabiat_Bridge")],
    blurb="A capital of nine million climbing the southern slope of the Alborz "
          "mountains, with snow on the peaks above the smog for half the year "
          "and a 600 m altitude difference between the north and south of the "
          "city.",
    fact="Tehran's Grand Bazaar runs for more than 10 km of covered corridors "
         "and has its own banks, mosques and guesthouses — historically it was "
         "powerful enough that closing it could bring down a government.",
    tip="Tabiat Bridge is a three-level pedestrian-only bridge over a motorway "
        "with cafés built into it — Tehranis go there to walk in the evening, "
        "and it was designed by a woman in her twenties."),
"yerevan": dict(
    region="Yerevan",
    highlights=[("Republic Square", "Republic_Square,_Yerevan"),
                ("Cascade", "Yerevan_Cascade"),
                ("Matenadaran", "Matenadaran"),
                ("Erebuni Fortress", "Erebuni_Fortress"),
                ("Mount Ararat", "Mount_Ararat")],
    blurb="A pink tuff-stone capital rebuilt to a radial plan in the 1920s, "
          "looking straight at Mount Ararat across a closed border. It is "
          "older than Rome — the Urartian fortress of Erebuni was founded here "
          "in 782 BC.",
    fact="Ararat, the mountain on Armenia's coat of arms and in the view from "
         "half the city's windows, has been inside Turkey since 1921 and no "
         "Armenian can reach it directly.",
    tip="Climb the Cascade steps at night. The sculpture terraces are open, "
        "free, and there is an escalator inside the structure if the 572 steps "
        "are too much."),
"lake-sevan": dict(
    region="Gegharkunik Province",
    highlights=[("Sevanavank", "Sevanavank"),
                ("Hayravank", "Hayravank_Monastery"),
                ("Noratus cemetery", "Noratus_cemetery"),
                ("Dilijan", "Dilijan")],
    blurb="One of the largest high-altitude freshwater lakes in the world, at "
          "1,900 m in the Armenian highlands — 1,240 km² of very blue water "
          "ringed by bare mountains, with medieval monasteries on the "
          "headlands.",
    fact="Soviet drainage schemes dropped the lake about 19 m between the "
         "1930s and 1960s, turning Sevanavank's island into a peninsula; the "
         "level has been slowly restored since, and the monastery's causeway "
         "is a monument to the mistake.",
    tip="Noratus, on the western shore, holds nearly a thousand carved "
        "khachkar cross-stones in an open field — the largest surviving "
        "cemetery of them, and almost nobody stops there."),
"baku": dict(
    region="Baku",
    highlights=[("Icherisheher", "Old_City_(Baku)"),
                ("Maiden Tower", "Maiden_Tower_(Baku)"),
                ("Flame Towers", "Flame_Towers"),
                ("Palace of the Shirvanshahs", "Palace_of_the_Shirvanshahs"),
                ("Heydar Aliyev Center", "Heydar_Aliyev_Center")],
    blurb="A Caspian capital below sea level, where a walled medieval core "
          "sits inside a ring of oil-boom mansions and then a ring of glass "
          "towers shaped like flames. The wind it is named for blows most of "
          "the year.",
    fact="Baku sits on one of the oldest oil fields in the world — surface "
         "seepage here was burning long enough to be sacred to Zoroastrians, "
         "and by 1900 the region was producing about half the planet's oil.",
    tip="The Heydar Aliyev Center, Zaha Hadid's white curve with no straight "
        "lines in it, is worth the trip out even if you never go inside."),
"tbilisi": dict(
    region="Tbilisi",
    highlights=[("Narikala", "Narikala"),
                ("Abanotubani", "Abanotubani"),
                ("Holy Trinity Cathedral", "Holy_Trinity_Cathedral_of_Tbilisi"),
                ("Rustaveli Avenue", "Rustaveli_Avenue"),
                ("Bridge of Peace", "Bridge_of_Peace")],
    blurb="A Georgian capital in a narrow river gorge, with carved wooden "
          "balconies leaning over the streets, a fortress on the ridge and "
          "sulphur bathhouses steaming in the middle of the old town.",
    fact="The city is named after the hot springs — *tbili* means warm — and "
         "the legend has a king's wounded pheasant falling into one and coming "
         "out cooked, which is why the capital was moved here in the 5th "
         "century.",
    tip="The domed brick roofs in Abanotubani are the tops of the bathhouses, "
        "which are underground. A private room for an hour costs less than a "
        "restaurant meal."),
"gergeti-kazbegi": dict(
    region="Mtskheta-Mtianeti",
    highlights=[("Gveleti Waterfalls", "Gveleti"),
                ("Mount Kazbek", "Mount_Kazbek"),
                ("Stepantsminda", "Stepantsminda"),
                ("Dariali Gorge", "Darial_Gorge"),
                ("Georgian Military Road", "Georgian_Military_Road")],
    blurb="A 14th-century church standing alone at 2,170 m on a green shoulder "
          "below the 5,047 m glaciated cone of Kazbek, an hour's walk above "
          "the village of Stepantsminda near the Russian border.",
    fact="In the Georgian telling of the Prometheus myth it is Kazbek that the "
         "chained giant Amirani was bound to, and a cave high on the mountain "
         "was long believed to hold the tent of Abraham.",
    tip="Walk up rather than taking a 4×4. It is about two hours through "
        "forest and meadow, and the church only detaches itself from the "
        "mountain behind it when you arrive on foot."),

# ══════════════════════════════ EUROPE ══════════════════════════════
"kyiv": dict(
    region="Kyiv",
    highlights=[("Saint Sophia Cathedral", "Saint_Sophia_Cathedral,_Kyiv"),
                ("Kyiv Pechersk Lavra", "Kyiv_Pechersk_Lavra"),
                ("Golden Gate", "Golden_Gate,_Kyiv"),
                ("Andriyivskyy Descent", "Andriyivskyy_Descent"),
                ("Maidan Nezalezhnosti", "Maidan_Nezalezhnosti")],
    blurb="Ukraine's capital on the high right bank of the Dnieper, and one of "
          "the oldest cities in eastern Europe — gold domes above the river, "
          "chestnut avenues, and a deep metro that doubles as a shelter.",
    fact="Saint Sophia was begun in 1011 and still holds its 11th-century "
         "mosaics and frescoes; both it and the Lavra caves are World Heritage "
         "Sites, and both have been sandbagged and monitored since 2022.",
    tip="Andriyivskyy Descent is the cobbled street that drops from the upper "
        "town to Podil, with Saint Andrew's Church at the top and Bulgakov's "
        "house halfway down."),
"lviv": dict(
    region="Lviv Oblast",
    highlights=[("Rynok Square", "Market_Square_(Lviv)"),
                ("Lviv Theatre of Opera and Ballet",
                 "Lviv_Theatre_of_Opera_and_Ballet"),
                ("Lychakiv Cemetery", "Lychakiv_Cemetery"),
                ("High Castle", "Lviv_High_Castle"),
                ("Dominican Church", None)],
    blurb="A central European city that has been Polish, Austrian, Soviet and "
          "Ukrainian without moving — cobbled squares, coffee houses and a "
          "largely intact old town that came through the 20th century with its "
          "architecture unusually undamaged.",
    fact="Lviv's historic centre survived the Second World War almost intact "
         "and is a World Heritage Site; since 2022 its stained glass has been "
         "boarded and its statues wrapped in fireproof sheeting.",
    tip="Walk up the High Castle hill in the morning — the whole tiled roofscape "
        "is below you, and the climb takes twenty minutes from Rynok Square."),
"odesa": dict(
    region="Odesa Oblast",
    highlights=[("Potemkin Stairs", "Potemkin_Stairs"),
                ("Odesa Opera and Ballet Theater",
                 "Odesa_Opera_and_Ballet_Theater"),
                ("Prymorskyi Boulevard", None),
                ("Odesa Catacombs", "Odessa_Catacombs"),
                ("Deribasivska Street", "Deribasivska_Street")],
    blurb="A Black Sea port founded by decree in 1794 and built as a free "
          "port — neoclassical, cosmopolitan and famously sharp-tongued, with "
          "a grand staircase running from the boulevard down to the harbour.",
    fact="Beneath the city lie roughly 2,500 km of catacombs — old limestone "
         "quarries, far longer than the Paris ones — which sheltered "
         "partisans in the Second World War and are largely unmapped.",
    tip="The Potemkin Stairs are built with an optical trick: 192 steps that "
        "widen as they descend, so from the top you see only landings and from "
        "the bottom only steps."),
"belgrade": dict(
    region="Belgrade",
    highlights=[("Belgrade Fortress", "Belgrade_Fortress"),
                ("Kalemegdan", None),
                ("Church of Saint Sava", "Church_of_Saint_Sava"),
                ("Skadarlija", "Skadarlija"),
                ("Zemun", "Zemun")],
    blurb="A capital on the ridge where the Sava meets the Danube, fought over "
          "more than almost any city in Europe and rebuilt every time. It is "
          "loud, unpolished and stays open extremely late.",
    fact="Belgrade has been destroyed and rebuilt around 40 times in its "
         "history; the fortress at the confluence has been Celtic, Roman, "
         "Byzantine, Serbian, Ottoman and Austrian in turn.",
    tip="Kalemegdan park inside the fortress walls is free and open all hours, "
        "and the terrace above the two rivers is where the city goes to watch "
        "the sun go down."),
"novi-sad": dict(
    region="Vojvodina",
    highlights=[("Petrovaradin Fortress", "Petrovaradin_Fortress"),
                ("Name of Mary Church", "Name_of_Mary_Church"),
                ("Štrand", "Štrand"),
                ("Fruška Gora", "Fruška_Gora"),
                ("Dunavska Street", None)],
    blurb="Serbia's second city, on the Danube in the flat Vojvodina plain, "
          "with an Austrian fortress on the cliff across the river and a "
          "central European feel the rest of the country does not have.",
    fact="Petrovaradin is known as the Gibraltar of the Danube and has 16 km "
         "of galleries on four levels tunnelled into the rock beneath it, most "
         "of them closed and only partly surveyed.",
    tip="The fortress clock has its hands reversed — the big hand shows the "
        "hour — so that boatmen on the Danube could read the time from the "
        "river."),
"luxembourg-city": dict(
    region="Luxembourg District",
    highlights=[("Bock Casemates", "Bock_(Luxembourg)"),
                ("Grand Ducal Palace", "Grand_Ducal_Palace,_Luxembourg"),
                ("Chemin de la Corniche", None),
                ("Notre-Dame Cathedral", "Notre-Dame_Cathedral,_Luxembourg"),
                ("Grund", None)],
    blurb="A capital built on and around a gorge, with the old town on the "
          "cliff tops and the Grund quarter down at river level below it, "
          "joined by lifts, stairs and viaducts.",
    fact="The rock the city stands on is honeycombed with 17 km of casemates "
         "cut by successive occupiers; 35,000 people sheltered in them during "
         "the Second World War.",
    tip="The Chemin de la Corniche has been called the most beautiful balcony "
        "in Europe — it runs along the top of the old ramparts and costs "
        "nothing."),
"vilnius": dict(
    region="Vilnius County",
    highlights=[("Gediminas' Tower", "Gediminas'_Tower"),
                ("Vilnius Cathedral", "Vilnius_Cathedral"),
                ("Gate of Dawn", "Gate_of_Dawn"),
                ("Užupis", "Užupis"),
                ("St. Anne's Church", "St._Anne's_Church,_Vilnius")],
    blurb="One of the largest surviving baroque old towns in eastern Europe, "
          "spread over hills at the meeting of two rivers — a city of "
          "courtyards, church spires and a self-declared artists' republic "
          "across a footbridge.",
    fact="Užupis declared itself an independent republic on 1 April 1997 and "
         "has a constitution mounted on a wall in twenty-odd languages, "
         "including the article 'a dog has the right to be a dog'.",
    tip="Climb Gediminas' hill at dusk — the funicular is often out of action "
        "and the path takes ten minutes — for the red roofs and the spires all "
        "at once."),
"trakai-castle": dict(
    region="Vilnius County",
    highlights=[("Lake Galvė", "Lake_Galvė"),
                ("Trakai", "Trakai"),
                ("Trakai Historical National Park",
                 "Trakai_Historical_National_Park"),
                ("Karaim kenesa", None)],
    blurb="A red-brick Gothic island castle on Lake Galvė, built by the grand "
          "dukes of Lithuania in the 14th century, reached by a wooden "
          "footbridge and surrounded by water on every side.",
    fact="Trakai is home to the Karaim, a Turkic community brought here from "
         "Crimea around 1400 as the grand duke's bodyguard; a few hundred "
         "remain, with their own language, prayer house and wooden houses that "
         "always have three windows facing the street.",
    tip="Rent a rowing boat or a pedalo on the lake. The castle only makes "
        "sense as an island fortress when you are looking up at it from the "
        "water."),
"riga": dict(
    region="Riga",
    highlights=[("House of the Blackheads", "House_of_the_Blackheads_(Riga)"),
                ("Riga Cathedral", "Riga_Cathedral"),
                ("Riga Central Market", "Riga_Central_Market"),
                ("Freedom Monument", "Freedom_Monument"),
                ("Art Nouveau district", None)],
    blurb="The largest city in the Baltics, a Hanseatic port on the Daugava "
          "with a compact medieval core and, just north of it, street after "
          "street of extravagant Art Nouveau facades.",
    fact="About a third of the buildings in central Riga are Art Nouveau — the "
         "highest concentration anywhere in the world — and many of the best "
         "are by Mikhail Eisenstein, father of the film director.",
    tip="Riga Central Market is housed in five converted Zeppelin hangars from "
        "the First World War, and it is where the city actually shops."),
"chisinau": dict(
    region="Chișinău",
    highlights=[("Nativity Cathedral", "Nativity_Cathedral,_Chișinău"),
                ("Triumphal Arch", "Triumphal_Arch,_Chișinău"),
                ("Stephen the Great Park", None),
                ("Cricova", "Cricova"),
                ("Orheiul Vechi", "Orheiul_Vechi")],
    blurb="Europe's least-visited capital: a low, green, unhurried city of "
          "parks and Soviet-era boulevards in the middle of Moldova's wine "
          "country, rebuilt after an earthquake and a war flattened most of "
          "it.",
    fact="The Cricova cellars just outside the city are 120 km of limestone "
         "tunnels used as a wine store, with street signs and traffic rules "
         "underground — and Milestii Mici nearby holds the largest wine "
         "collection in the world.",
    tip="Orheiul Vechi, an hour away, is a cave monastery cut into a limestone "
        "cliff above a river bend, still occupied by monks and still reached "
        "on foot."),
"bratislava": dict(
    region="Bratislava Region",
    highlights=[("Bratislava Castle", "Bratislava_Castle"),
                ("St. Martin's Cathedral", "St_Martin's_Cathedral,_Bratislava"),
                ("Michael's Gate", "Michael's_Gate"),
                ("Devín Castle", "Devín_Castle"),
                ("UFO Bridge", "Most_SNP")],
    blurb="A compact capital on the Danube within sight of two borders, with a "
          "white castle on the hill, a small pedestrian old town below it, and "
          "a flying-saucer restaurant on a bridge pylon.",
    fact="Eleven Hungarian kings and eight queens were crowned in St Martin's "
         "Cathedral between 1563 and 1830, while Buda was under Ottoman "
         "control — a gilded crown on the spire marks it.",
    tip="Devín Castle, where the Morava joins the Danube, was the westernmost "
        "point of the Eastern Bloc; the Iron Curtain ran along the river below "
        "it and there is a memorial to the people shot trying to cross."),
"high-tatras": dict(
    region="Prešov Region",
    highlights=[("Gerlachovský štít", "Gerlachovský_štít"),
                ("Lomnický štít", "Lomnický_štít"),
                ("Štrbské Pleso", "Štrbské_Pleso"),
                ("Tatra National Park", "Tatra_National_Park,_Slovakia"),
                ("Poprad", "Poprad")],
    blurb="The smallest high-alpine range in the world — 26 km end to end, "
          "with granite peaks over 2,600 m, glacial lakes and marked trails, "
          "packed into an area you can see across on a clear day.",
    fact="Despite topping out at 2,655 m the Tatras behave like much bigger "
         "mountains: they carry alpine tundra, chamois and marmots, and the "
         "weather changes fast enough that the trails above the huts close in "
         "winter by law.",
    tip="The cable car to Lomnický štít puts you on a 2,634 m summit in "
        "minutes, but tickets are timed and sell out — book the day before."),
"ljubljana": dict(
    region="Upper Carniola",
    highlights=[("Ljubljana Castle", "Ljubljana_Castle"),
                ("Triple Bridge", "Triple_Bridge"),
                ("Dragon Bridge", "Dragon_Bridge_(Ljubljana)"),
                ("Central Market", None),
                ("Tivoli Park", "Tivoli_City_Park")],
    blurb="A small green capital on a river, with a castle on the hill, a "
          "car-free centre and an unusual amount of one architect's work in "
          "it — Jože Plečnik redesigned much of the city between the wars.",
    fact="Ljubljana closed its historic centre to traffic entirely and was "
         "named European Green Capital in 2016; the river embankments, "
         "bridges, market and cemetery were all designed by the same man.",
    tip="Walk up to the castle rather than taking the funicular — twenty "
        "minutes through woods — and come back down the other side into "
        "Tivoli Park."),
"lake-bled": dict(
    region="Upper Carniola",
    highlights=[("Bled Island", None),
                ("Bled Castle", "Bled_Castle"),
                ("Church of the Assumption", None),
                ("Vintgar Gorge", "Vintgar_Gorge"),
                ("Julian Alps", "Julian_Alps")],
    blurb="A glacial lake in the Julian Alps with a church on a small island "
          "in the middle of it and a castle on a cliff above — rowed to in "
          "flat-bottomed *pletna* boats by a handful of licensed families.",
    fact="The 99 steps up from the island's jetty are traditionally climbed by "
         "a groom carrying his bride, and the church bell is said to grant a "
         "wish — which is why it rings more or less continuously all day.",
    tip="Vintgar Gorge, 4 km away, is a wooden walkway pinned to the rock "
        "above a green river for 1.6 km. Book a slot; entry is now capped."),
"piran": dict(
    region="Slovene Istria",
    highlights=[("Tartini Square", "Tartini_Square"),
                ("St. George's Parish Church",
                 "St._George's_Parish_Church,_Piran"),
                ("Piran town walls", None),
                ("Sečovlje Salina Nature Park", "Sečovlje_Salina_Nature_Park"),
                ("Portorož", "Portorož")],
    blurb="A Venetian fishing town on a narrow point of Slovenia's 46 km of "
          "coast — stone alleys, a marble square where the harbour used to be, "
          "and walls on the hill you can walk along.",
    fact="Piran was Venetian for over 500 years, and the town still speaks a "
         "little Italian officially; the salt pans south of it have been "
         "worked by hand using the same medieval method since the 13th "
         "century.",
    tip="Climb the town walls in the late afternoon for a couple of euros. "
        "From up there the whole peninsula, the church and the Adriatic line "
        "up at once."),
"vatican-city": dict(
    highlights=[("St. Peter's Basilica", "St._Peter's_Basilica"),
                ("Sistine Chapel", "Sistine_Chapel"),
                ("Vatican Museums", "Vatican_Museums"),
                ("St. Peter's Square", "St._Peter's_Square"),
                ("Apostolic Palace", "Apostolic_Palace")],
    blurb="The smallest sovereign state in the world — 49 hectares inside "
          "Rome, with about 800 residents, its own post office and railway "
          "station, and the largest church in Christendom at the centre of it.",
    fact="The Vatican has the highest crime rate per capita of any state on "
         "Earth, which is an artefact of arithmetic: a few hundred pickpocket "
         "reports a year divided by a population smaller than a village.",
    tip="St Peter's dome can be climbed — 551 steps, or a lift to the roof and "
        "320 after that — and the last stretch leans with the curve of the "
        "dome itself."),
"saint-petersburg": dict(
    region="Northwestern Russia",
    highlights=[("Winter Palace", "Winter_Palace"),
                ("Hermitage Museum", "Hermitage_Museum"),
                ("Church of the Savior on Spilled Blood",
                 "Church_of_the_Savior_on_Blood"),
                ("Peter and Paul Fortress", "Peter_and_Paul_Fortress"),
                ("Peterhof Palace", "Peterhof_Palace")],
    blurb="Built from nothing on a swamp by decree in 1703 as Russia's window "
          "on Europe — granite embankments, canals, pastel palaces and a grid "
          "of straight prospects laid across the Neva delta.",
    fact="The Hermitage holds around three million items across more than a "
         "thousand rooms; at a minute apiece you would need years to see them "
         "all, and the museum has employed cats to control mice since the "
         "1740s.",
    tip="The Peterhof fountains run on gravity alone — no pumps, just a "
        "20 km aqueduct and a drop in the land — and they are switched on with "
        "music every morning in season."),
"kazan": dict(
    region="Tatarstan",
    highlights=[("Kazan Kremlin", "Kazan_Kremlin"),
                ("Qolşärif Mosque", "Qolşärif_Mosque"),
                ("Söyembikä Tower", "Söyembikä_Tower"),
                ("Bauman Street", "Bauman_Street"),
                ("Temple of All Religions", "Temple_of_All_Religions")],
    blurb="The capital of Tatarstan on the Volga, where a mosque and an "
          "Orthodox cathedral stand inside the same white kremlin — a Muslim "
          "Tatar city that has been part of Russia since 1552 and is comfortable "
          "being both.",
    fact="The Söyembikä Tower leans nearly two metres off vertical, more than "
         "the tilt is usually noticed for, because it was built on the "
         "foundations of an earlier structure without deep piling.",
    tip="Bauman Street is the pedestrian spine and the place to try tatar "
        "echpochmak; the kremlin above it is free to walk into."),
"lake-baikal": dict(
    region="Siberia",
    highlights=[("Olkhon Island", "Olkhon_Island"),
                ("Listvyanka", "Listvyanka,_Irkutsk_Oblast"),
                ("Shaman Rock", None),
                ("Circum-Baikal Railway", "Circum-Baikal_Railway"),
                ("Barguzin Range", "Barguzin_Range")],
    blurb="The deepest and oldest lake on Earth — 1,642 m down, 25 million "
          "years old, and holding about a fifth of all the unfrozen fresh "
          "water on the planet. In winter it freezes hard enough to drive "
          "across.",
    fact="Baikal has around 2,000 species found nowhere else, including the "
         "nerpa, the world's only exclusively freshwater seal — and nobody is "
         "quite sure how a seal got 3,000 km from the nearest ocean.",
    tip="February and March are the season for the ice: it goes clear and "
        "turquoise, cracks into slabs metres thick, and the hovercraft run to "
        "Olkhon over the top of it."),

# ═════════════════════════════ OCEANIA ═════════════════════════════
"melbourne": dict(
    region="Victoria",
    highlights=[("Federation Square", "Federation_Square"),
                ("Royal Exhibition Building", "Royal_Exhibition_Building"),
                ("Queen Victoria Market", "Queen_Victoria_Market"),
                ("Hosier Lane", "Hosier_Lane"),
                ("Melbourne Cricket Ground", "Melbourne_Cricket_Ground")],
    blurb="Australia's coffee and arts capital — a grid of Victorian arcades "
          "and graffitied laneways on the Yarra, with trams through the middle "
          "of it and famously four seasons in one day.",
    fact="The Royal Exhibition Building was the first building in Australia to "
         "get World Heritage status, and the first federal parliament sat in "
         "it in 1901 while Canberra did not yet exist.",
    tip="The laneways are the point. Start at Hosier Lane, then work through "
        "Centre Place and Degraves Street — the street art is repainted often "
        "enough that nobody sees the same walls twice."),
"uluru": dict(
    region="Northern Territory",
    highlights=[("Kata Tjuta", "Kata_Tjuta"),
                ("Uluru-Kata Tjuta National Park",
                 "Uluru-Kata_Tjuta_National_Park"),
                ("Mutitjulu Waterhole", None),
                ("Valley of the Winds", None),
                ("Yulara", "Yulara,_Northern_Territory")],
    blurb="A single sandstone inselberg 348 m high and 9.4 km around, standing "
          "alone in the red centre of Australia — the most sacred site of the "
          "Anangu, who have lived alongside it for tens of thousands of years.",
    fact="What you see is the tip: the rock continues underground for an "
         "estimated 2.5 km, and its colour changes because the iron in the "
         "surface arkose rusts and catches low sun.",
    tip="Climbing has been banned since October 2019 at the Anangu's long-"
        "standing request. Walk the base loop instead — 10.6 km, flat, and the "
        "caves and paintings around the foot are what the rock is actually "
        "about."),
"great-barrier-reef": dict(
    region="Queensland",
    highlights=[("Whitsunday Islands", "Whitsunday_Islands"),
                ("Heart Reef", None),
                ("Lady Elliot Island", "Lady_Elliot_Island"),
                ("Ribbon Reefs", None),
                ("Heron Island", "Heron_Island_(Queensland)")],
    blurb="The largest living structure on Earth — 2,300 km of coral along the "
          "Queensland coast, made of some 2,900 individual reefs and 900 "
          "islands, and the only living thing visible from orbit with the "
          "naked eye.",
    fact="The reef has suffered repeated mass bleaching events since 2016, "
         "driven by marine heatwaves; the northern third lost roughly half its "
         "shallow-water coral in 2016–17 alone.",
    tip="The outer ribbon reefs off Cairns and Port Douglas are in far better "
        "condition than the inshore ones — go further out, and pick an "
        "operator that carries a reef biologist."),
"cairns": dict(
    region="Queensland",
    highlights=[("Daintree Rainforest", "Daintree_Rainforest"),
                ("Kuranda", "Kuranda,_Queensland"),
                ("Cairns Esplanade", None),
                ("Fitzroy Island", "Fitzroy_Island_(Queensland)"),
                ("Cape Tribulation", "Cape_Tribulation,_Queensland")],
    blurb="A tropical town in far north Queensland that exists as the door to "
          "two World Heritage Sites at once — the Great Barrier Reef offshore "
          "and the Daintree rainforest starting an hour up the coast road.",
    fact="The Daintree is around 180 million years old, which makes it the "
         "oldest continuously surviving rainforest on the planet — tens of "
         "millions of years older than the Amazon.",
    tip="Cape Tribulation is the one place where the reef and the rainforest "
        "meet at the shoreline. Do not swim: this is estuarine crocodile and "
        "box jellyfish country, and the signs are not decorative."),
"perth": dict(
    region="Western Australia",
    highlights=[("Kings Park", "Kings_Park,_Western_Australia"),
                ("Fremantle", "Fremantle"),
                ("Rottnest Island", "Rottnest_Island"),
                ("Swan River", "Swan_River_(Western_Australia)"),
                ("Cottesloe Beach", "Cottesloe_Beach")],
    blurb="The most isolated major city in the world — the nearest city of "
          "comparable size is 2,100 km away — sitting on the Swan River with "
          "white beaches on one side and an enormous amount of sunshine.",
    fact="Kings Park is 400 hectares in the middle of the city, larger than "
         "Central Park, and two thirds of it is left as native bushland rather "
         "than landscaped.",
    tip="Rottnest Island is a half-hour ferry from Fremantle, has no private "
        "cars, and is full of quokkas — small marsupials with no fear of "
        "people at all."),
"auckland": dict(
    region="North Island",
    highlights=[("Sky Tower", "Sky_Tower_(Auckland)"),
                ("Rangitoto Island", "Rangitoto_Island"),
                ("Waiheke Island", "Waiheke_Island"),
                ("Mount Eden", "Maungawhau_/_Mount_Eden"),
                ("Auckland War Memorial Museum",
                 "Auckland_War_Memorial_Museum")],
    blurb="New Zealand's largest city, spread across an isthmus between two "
          "harbours and built on top of a volcanic field — about 50 cones "
          "inside the urban area, most of them now parks.",
    fact="Auckland's volcanic field is dormant, not extinct: Rangitoto, the "
         "island in the middle of the harbour view, erupted out of the sea "
         "only about 600 years ago, and Māori living nearby saw it happen.",
    tip="Climb Mount Eden at dawn. It is a fifteen-minute walk to a grassy "
        "crater 50 m deep, and you can see both harbours and half the other "
        "cones from the rim."),
"queenstown": dict(
    region="Otago",
    highlights=[("Lake Wakatipu", "Lake_Wakatipu"),
                ("The Remarkables", "The_Remarkables"),
                ("Skyline Gondola", None),
                ("Arrowtown", "Arrowtown"),
                ("Kawarau Gorge Suspension Bridge",
                 "Kawarau_Gorge_Suspension_Bridge")],
    blurb="The adventure capital of the southern hemisphere, on a "
          "zigzag-shaped alpine lake under a mountain range called The "
          "Remarkables — bungee, jetboats, skiing, and a very small town "
          "centre holding it all.",
    fact="Commercial bungee jumping was invented here: A. J. Hackett opened "
         "the world's first permanent site on the 43 m Kawarau Bridge in 1988, "
         "and it is still running.",
    tip="Arrowtown, twenty minutes away, is a preserved gold-rush village with "
        "the remains of a Chinese miners' settlement along the creek — the "
        "part of the story the main street leaves out."),
"wellington": dict(
    region="North Island",
    highlights=[("Te Papa", "Museum_of_New_Zealand_Te_Papa_Tongarewa"),
                ("Wellington Cable Car", "Wellington_Cable_Car"),
                ("Mount Victoria", "Mount_Victoria_(Wellington_hill)"),
                ("Cuba Street", "Cuba_Street,_Wellington"),
                ("Zealandia", "Zealandia_(wildlife_sanctuary)")],
    blurb="New Zealand's capital, wedged between a harbour and steep hills at "
          "the bottom of the North Island — compact, walkable, full of cafés "
          "and film studios, and reliably the windiest city in the world.",
    fact="Wellington averages gusts over 60 km/h on more than 170 days a year, "
         "and its airport approach is rated among the most difficult in the "
         "world for exactly that reason.",
    tip="Zealandia is a 225-hectare valley behind a predator-proof fence, ten "
        "minutes from downtown, where kākā and takahē live wild — go at night "
        "for the kiwi tour."),
"rotorua": dict(
    region="North Island",
    highlights=[("Te Puia", "New_Zealand_Māori_Arts_and_Crafts_Institute"),
                ("Pōhutu Geyser", "Pōhutu_Geyser"),
                ("Wai-O-Tapu", "Wai-O-Tapu"),
                ("Lake Rotorua", "Lake_Rotorua"),
                ("Whakarewarewa", "Whakarewarewa")],
    blurb="A geothermal town on the edge of a crater lake, where steam comes "
          "up through drains and gardens, the air smells of sulphur, and Māori "
          "culture is more visible than anywhere else in the country.",
    fact="At Whakarewarewa people still live on the thermal field and cook in "
         "it — food is boiled in the hot pools and steamed in ground vents, as "
         "it has been for several hundred years.",
    tip="Pōhutu erupts up to twenty times a day, sometimes 30 m high, and the "
        "smaller Prince of Wales Feathers geyser next to it always goes off "
        "first — that is your cue to look up."),
"milford-sound": dict(
    region="Fiordland",
    highlights=[("Mitre Peak", "Mitre_Peak"),
                ("Fiordland National Park", "Fiordland_National_Park"),
                ("Stirling Falls", None),
                ("Homer Tunnel", "Homer_Tunnel"),
                ("Milford Track", "Milford_Track")],
    blurb="A fiord 16 km long with cliffs rising 1,200 m straight out of black "
          "water, seals on the rocks and waterfalls that blow back upwards in "
          "the wind. Rudyard Kipling called it the eighth wonder of the world.",
    fact="Milford gets around 6,800 mm of rain a year — one of the wettest "
         "inhabited places on the planet — which is why hundreds of temporary "
         "waterfalls appear down the cliffs within minutes of a downpour.",
    tip="Go on a wet day, not a clear one. Sun gives you a photograph; rain "
        "gives you the waterfalls the fiord is actually famous for."),
}
