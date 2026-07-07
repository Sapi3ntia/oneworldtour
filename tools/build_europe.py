#!/usr/bin/env python3
"""
build_europe.py — generator for data/europe.json

One World Tour stores each *destination* as a map marker. A destination now
also carries a list of `highlights` (the individual landmarks you explore once
you arrive). Encoding the whole continent as compact Python rows keeps the data
reviewable and lets us regenerate the JSON deterministically.

Row format (tuple):
    (id, name, country, sub_region, type, tag, emoji, lat, lng, wiki_slug,
     [ (highlight_name, highlight_wiki_slug), ... ])

`tag`  -> "famous" or "hidden" (drives marker colour + filter)
`type` -> picks the ambient sound bed

Authored blurbs / fun-facts / local tips live in BLURBS keyed by id. Anything
left out is filled live from Wikipedia by the front-end, so every destination
still renders text + photos.

Run:  python3 tools/build_europe.py
"""

import json
import os

# ---------------------------------------------------------------------------
# country -> flag emoji
# ---------------------------------------------------------------------------
FLAG = {
    "Austria": "🇦🇹", "Denmark": "🇩🇰", "Faroe Islands": "🇫🇴", "Spain": "🇪🇸",
    "England": "🇬🇧", "United Kingdom": "🇬🇧", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Germany": "🇩🇪", "Belgium": "🇧🇪", "Netherlands": "🇳🇱", "Italy": "🇮🇹",
    "France": "🇫🇷", "Malta": "🇲🇹", "Iceland": "🇮🇸", "Turkey": "🇹🇷",
    "Portugal": "🇵🇹", "Sweden": "🇸🇪", "Switzerland": "🇨🇭", "Finland": "🇫🇮",
    "Poland": "🇵🇱", "Croatia": "🇭🇷", "Ireland": "🇮🇪", "Czech Republic": "🇨🇿",
    "Greece": "🇬🇷", "Hungary": "🇭🇺", "Romania": "🇷🇴", "Bulgaria": "🇧🇬",
    "Norway": "🇳🇴", "Bosnia and Herzegovina": "🇧🇦", "Estonia": "🇪🇪",
    "Cyprus": "🇨🇾", "Montenegro": "🇲🇪", "Albania": "🇦🇱",
}

# type -> ambient sound file (files optional; player fails silently if absent)
SOUND = {
    "city":       "city-hum.mp3",
    "history":    "european-plaza.mp3",
    "coastal":    "ocean-waves.mp3",
    "island":     "ocean-waves.mp3",
    "mountain":   "mountain-wind.mp3",
    "nature":     "mountain-wind.mp3",
    "village":    "european-plaza.mp3",
}


def H(*pairs):
    """Build a highlights list from (name, slug) pairs."""
    return [{"name": n, "wikipedia_slug": s} for (n, s) in pairs]


# ---------------------------------------------------------------------------
# THE CONTINENT  (numbers track the user's source list, 2..100)
# ---------------------------------------------------------------------------
DEST = [
 ("vienna","Vienna","Austria","","city","famous","🎻",48.2082,16.3738,"Vienna", H(
    ("Schönbrunn Palace","Schönbrunn_Palace"),("Belvedere","Belvedere,_Vienna"),
    ("Vienna State Opera","Vienna_State_Opera"),("St. Stephen's Cathedral","St._Stephen's_Cathedral,_Vienna"),
    ("Hofburg","Hofburg"),("Kunsthistorisches Museum","Kunsthistorisches_Museum"),
    ("Natural History Museum","Natural_History_Museum,_Vienna"))),

 ("faroe-islands","Faroe Islands","Faroe Islands","","island","hidden","🌫️",62.0,-6.79,"Faroe_Islands", H(
    ("Tórshavn","Tórshavn"),("Sørvágsvatn","Sørvágsvatn"),
    ("Gásadalur","Gásadalur"),("Saksun","Saksun"))),

 ("canary-islands","Canary Islands","Spain","Canary Islands","island","famous","🌋",28.2916,-16.6291,"Canary_Islands", H(
    ("Mount Teide","Teide"),("Maspalomas Dunes","Maspalomas"),("Las Palmas","Las_Palmas_de_Gran_Canaria"),
    ("Lanzarote / César Manrique","César_Manrique"),("Fuerteventura","Fuerteventura"))),

 ("liverpool","Liverpool","England","","city","famous","🎸",53.4084,-2.9916,"Liverpool", H(
    ("Royal Albert Dock","Royal_Albert_Dock,_Liverpool"),("The Cavern Club","The_Cavern_Club"),
    ("The Beatles Story","The_Beatles_Story"),("Tate Liverpool","Tate_Liverpool"))),

 ("andalusia","Andalusia","Spain","Andalusia","history","famous","💃",37.3886,-5.9823,"Andalusia", H(
    ("Real Alcázar of Seville","Alcázar_of_Seville"),("The Alhambra","Alhambra"),
    ("Mezquita of Córdoba","Mosque–Cathedral_of_Córdoba"),("Cádiz","Cádiz"),
    ("Jerez de la Frontera","Jerez_de_la_Frontera"),("Sierra Nevada","Sierra_Nevada_(Spain)"))),

 ("black-forest","Black Forest","Germany","Baden-Württemberg","nature","hidden","🌲",48.0,8.2,"Black_Forest", H(
    ("Freiburg im Breisgau","Freiburg_im_Breisgau"),("Freiburg Minster","Freiburg_Minster"))),

 ("ghent","Ghent","Belgium","","history","famous","🏰",51.0543,3.7174,"Ghent", H(
    ("Gravensteen","Gravensteen"),("St. Bavo's Cathedral","Saint_Bavo's_Cathedral,_Ghent"))),

 ("zaanse-schans","Zaanse Schans","Netherlands","","village","hidden","🌬️",52.4742,4.8170,"Zaanse_Schans", H(
    ("Historic Windmills","Windmills_of_Zaanse_Schans"),("Wooden Houses","Zaanse_Schans"))),

 ("innsbruck","Innsbruck","Austria","Tyrol","mountain","famous","🏔️",47.2692,11.4041,"Innsbruck", H(
    ("The Golden Roof","Golden_Roof"),("Imperial Palace","Hofburg,_Innsbruck"),("Nordkette / Austrian Alps","Nordkette"))),

 ("rothenburg","Rothenburg ob der Tauber","Germany","Bavaria","village","famous","🧱",49.3755,10.1869,"Rothenburg_ob_der_Tauber", H(
    ("The Romantic Road","Romantic_Road"),("Medieval Town Walls","Rothenburg_ob_der_Tauber"))),

 ("italian-lakes","Italian Lake District","Italy","Lombardy","nature","famous","🚤",45.98,9.26,"Italian_Lakes", H(
    ("Lake Como","Lake_Como"),("Lake Garda","Lake_Garda"),("Lake Maggiore","Lake_Maggiore"),
    ("Borromean Islands","Borromean_Islands"))),

 ("bordeaux","Bordeaux","France","Nouvelle-Aquitaine","city","famous","🍷",44.8378,-0.5792,"Bordeaux", H(
    ("Cité du Vin","Cité_du_Vin"),("Place de la Bourse","Place_de_la_Bourse"),("Banks of the Garonne","Garonne"))),

 ("malta","Malta","Malta","","island","famous","🛡️",35.8989,14.5146,"Valletta", H(
    ("St. John's Co-Cathedral","St_John's_Co-Cathedral"),("Grand Master's Palace","Grandmaster's_Palace,_Valletta"),
    ("Gozo","Gozo"),("Comino / Blue Lagoon","Comino"))),

 ("iceland","Iceland","Iceland","","nature","famous","🌋",64.1466,-21.9426,"Iceland", H(
    ("Thingvellir National Park","Þingvellir"),("Reykjavík","Reykjavík"),
    ("Golden Circle","Golden_Circle_(Iceland)"))),

 ("cappadocia","Cappadocia","Turkey","","nature","famous","🎈",38.6431,34.8289,"Cappadocia", H(
    ("Fairy Chimneys","Fairy_chimney"),("Göreme","Göreme"),("Derinkuyu Underground City","Derinkuyu_underground_city"))),

 ("azores","Azores","Portugal","Azores","island","hidden","♨️",37.7412,-25.6756,"Azores", H(
    ("São Miguel Island","São_Miguel_Island"),("Furnas Hot Springs","Furnas"),("Angra do Heroísmo","Angra_do_Heroísmo"))),

 ("costa-del-sol","Costa del Sol","Spain","Andalusia","coastal","famous","🏖️",36.7213,-4.4214,"Costa_del_Sol", H(
    ("Marbella","Marbella"),("Torremolinos","Torremolinos"),("Fuengirola","Fuengirola"),
    ("Málaga","Málaga"),("Picasso Museum","Museo_Picasso_Málaga"),("Gibralfaro Castle","Castle_of_Gibralfaro"))),

 ("neuschwanstein","Neuschwanstein Castle","Germany","Bavaria","history","famous","🏰",47.5576,10.7498,"Neuschwanstein_Castle", H(
    ("Bavarian Alps","Bavarian_Alps"),("Füssen","Füssen"),("Hohenschwangau","Hohenschwangau_Castle"))),

 ("stockholm","Stockholm","Sweden","","city","famous","👑",59.3293,18.0686,"Stockholm", H(
    ("Gamla Stan (Old Town)","Gamla_stan"),("The Royal Palace","Stockholm_Palace"),
    ("Storkyrkan Cathedral","Storkyrkan"),("Djurgården","Djurgården"))),

 ("strasbourg","Strasbourg","France","Grand Est","history","famous","⛪",48.5734,7.7521,"Strasbourg", H(
    ("La Petite France","Petite_France,_Strasbourg"),("Strasbourg Cathedral","Strasbourg_Cathedral"))),

 ("swiss-alps","Swiss Alps","Switzerland","","mountain","famous","🏔️",46.0207,7.7491,"Swiss_Alps", H(
    ("The Matterhorn","Matterhorn"),("Zermatt","Zermatt"),("Interlaken","Interlaken"),
    ("Lake Thun","Lake_Thun"),("Lake Brienz","Lake_Brienz"))),

 ("lapland","Lapland","Finland","Lapland","nature","hidden","🦌",68.0,24.0,"Lapland_(Finland)", H(
    ("Northern Lights","Aurora"),("Sámi Culture","Sámi_people"))),

 ("hamburg","Hamburg","Germany","","city","famous","⚓",53.5511,9.9937,"Hamburg", H(
    ("Speicherstadt","Speicherstadt"),("Elbphilharmonie","Elbphilharmonie"),
    ("Reeperbahn","Reeperbahn"),("The Elbe","Elbe"))),

 ("copenhagen","Copenhagen","Denmark","","city","famous","🧜",55.6761,12.5683,"Copenhagen", H(
    ("Rosenborg Castle","Rosenborg_Castle"),("The Little Mermaid","The_Little_Mermaid_(statue)"),
    ("Nyhavn","Nyhavn"))),

 ("tirana","Albania & Tirana","Albania","","city","hidden","🇦🇱",41.3275,19.8187,"Tirana", H(
    ("Skanderbeg Square","Skanderbeg_Square"),("Butrint","Butrint"),("Albanian Riviera","Albanian_Riviera"))),

 ("krakow","Kraków","Poland","","history","famous","🐉",50.0647,19.9450,"Kraków", H(
    ("Wawel Castle","Wawel_Castle"),("Main Market Square","Main_Square,_Kraków"),
    ("St. Mary's Basilica","St._Mary's_Basilica,_Kraków"))),

 ("edinburgh","Edinburgh","United Kingdom","Scotland","history","famous","🏰",55.9533,-3.1883,"Edinburgh", H(
    ("Edinburgh Castle","Edinburgh_Castle"),("Arthur's Seat","Arthur's_Seat"),
    ("The Royal Mile","Royal_Mile"),("Palace of Holyroodhouse","Holyrood_Palace"))),

 ("dolomites","Dolomites","Italy","South Tyrol","mountain","famous","⛰️",46.4102,11.8440,"Dolomites", H(
    ("Tre Cime di Lavaredo","Tre_Cime_di_Lavaredo"),("Alpe di Siusi","Alpe_di_Siusi"))),

 ("madeira","Madeira","Portugal","Madeira","island","hidden","🌺",32.7607,-16.9595,"Madeira", H(
    ("Funchal","Funchal"),("Laurisilva Forest","Laurisilva_of_Madeira"),("The Levadas","Levada"))),

 ("rome","Rome","Italy","Lazio","history","famous","🏛️",41.9028,12.4964,"Rome", H(
    ("The Colosseum","Colosseum"),("Roman Forum","Roman_Forum"),("Piazza Navona","Piazza_Navona"),
    ("Trevi Fountain","Trevi_Fountain"),("St. Peter's Basilica","St._Peter's_Basilica"),
    ("Sistine Chapel","Sistine_Chapel"),("Vatican Museums","Vatican_Museums"))),

 ("amsterdam","Amsterdam","Netherlands","","city","famous","🚲",52.3676,4.9041,"Amsterdam", H(
    ("Historic Canals","Canals_of_Amsterdam"),("Van Gogh Museum","Van_Gogh_Museum"),
    ("Rijksmuseum","Rijksmuseum"),("Anne Frank House","Anne_Frank_House"),
    ("Bloemenmarkt","Bloemenmarkt"))),

 ("french-riviera","French Riviera","France","Provence-Alpes-Côte d'Azur","coastal","famous","🛥️",43.7102,7.2620,"French_Riviera", H(
    ("Nice","Nice"),("Cannes","Cannes"),("Saint-Tropez","Saint-Tropez"),
    ("Monaco","Monaco"),("Menton","Menton"))),

 ("salzburg","Salzburg","Austria","","history","famous","🎼",47.8095,13.0550,"Salzburg", H(
    ("Hohensalzburg Fortress","Hohensalzburg_Fortress"),("Getreidegasse","Getreidegasse"),
    ("Mirabell Gardens","Mirabell_Palace"),("Mozart's Birthplace","Mozart's_Birthplace"))),

 ("sintra","Sintra","Portugal","Lisbon Region","history","famous","🏰",38.7979,-9.3907,"Sintra", H(
    ("Pena National Palace","Pena_Palace"),("Moorish Castle","Castle_of_the_Moors"),
    ("Quinta da Regaleira","Quinta_da_Regaleira"))),

 ("toledo","Toledo","Spain","Castile-La Mancha","history","famous","⚔️",39.8628,-4.0273,"Toledo,_Spain", H(
    ("Toledo Cathedral","Toledo_Cathedral"),("El Greco Museum","El_Greco_Museum"),("Tagus River","Tagus"))),

 ("oxford","Oxford","England","","city","famous","📚",51.7520,-1.2577,"Oxford", H(
    ("Bodleian Library","Bodleian_Library"),("Radcliffe Camera","Radcliffe_Camera"),
    ("Christ Church College","Christ_Church,_Oxford"))),

 ("plitvice","Plitvice Lakes National Park","Croatia","","nature","famous","💧",44.8654,15.5820,"Plitvice_Lakes_National_Park", H(
    ("The Terraced Lakes","Plitvice_Lakes_National_Park"),("Veliki Slap Waterfall","Plitvice_Lakes_National_Park"))),

 ("wild-atlantic-way","Wild Atlantic Way","Ireland","","coastal","famous","🌊",53.0,-9.5,"Wild_Atlantic_Way", H(
    ("Cliffs of Moher","Cliffs_of_Moher"),("Connemara","Connemara"))),

 ("bern","Bern","Switzerland","","city","famous","🐻",46.9480,7.4474,"Bern", H(
    ("Medieval Arcades","Old_City_(Bern)"),("Zytglogge","Zytglogge"),("Aare River","Aare"))),

 ("leipzig","Leipzig","Germany","Saxony","city","hidden","🎶",51.3397,12.3731,"Leipzig", H(
    ("Old Town","Leipzig"),("Monument to the Battle of the Nations","Monument_to_the_Battle_of_the_Nations"))),

 ("dubrovnik","Dubrovnik","Croatia","Dalmatia","coastal","famous","🛡️",42.6507,18.0944,"Dubrovnik", H(
    ("Medieval City Walls","Walls_of_Dubrovnik"),("Rector's Palace","Rector's_Palace,_Dubrovnik"),
    ("St. Blaise Church","Church_of_St._Blaise,_Dubrovnik"),("Stradun","Stradun"))),

 ("cyprus","Cyprus","Cyprus","Paphos","island","famous","🏺",34.7768,32.4245,"Paphos", H(
    ("Paphos Archaeological Park","Paphos_Archaeological_Park"),("Roman Mosaics","House_of_Dionysus"))),

 ("sicily","Sicily","Italy","Sicily","island","famous","🌋",37.5990,14.0154,"Sicily", H(
    ("Palermo","Palermo"),("Teatro Massimo","Teatro_Massimo"),("Taormina","Taormina"),
    ("Mount Etna","Mount_Etna"),("Cefalù","Cefalù"),("Erice","Erice"))),

 ("hallstatt","Hallstatt","Austria","Upper Austria","village","hidden","🏞️",47.5622,13.6493,"Hallstatt", H(
    ("Lake Hallstatt","Hallstätter_See"),("Salzwelten Salt Mine","Salt_mine"))),

 ("munich","Munich","Germany","Bavaria","city","famous","🍺",48.1351,11.5820,"Munich", H(
    ("Marienplatz & Glockenspiel","Marienplatz"),("The Residenz","Munich_Residenz"),
    ("Englischer Garten","Englischer_Garten"),("BMW Museum","BMW_Museum"),
    ("Pinakothek der Moderne","Pinakothek_der_Moderne"))),

 ("manchester","Manchester","England","","city","hidden","⚽",53.4808,-2.2426,"Manchester", H(
    ("Old Trafford","Old_Trafford"),("Etihad Stadium","City_of_Manchester_Stadium"),
    ("The Northern Quarter","Northern_Quarter"),("Science and Industry Museum","Science_and_Industry_Museum"))),

 ("provence","Provence","France","Provence-Alpes-Côte d'Azur","nature","famous","💜",43.9,5.4,"Provence", H(
    ("Lavender Fields","Lavandula"),("Gordes","Gordes"),("Sault","Sault,_Vaucluse"))),

 ("sighisoara","Sighișoara","Romania","Transylvania","history","hidden","🧛",46.2197,24.7964,"Sighișoara", H(
    ("The Old Town","Sighișoara"),("The Clock Tower","Clock_Tower,_Sighișoara"),
    ("Birthplace of Vlad the Impaler","Vlad_the_Impaler"))),

 ("geneva","Geneva","Switzerland","","city","famous","⛲",46.2044,6.1432,"Geneva", H(
    ("Lake Geneva","Lake_Geneva"),("Jet d'Eau","Jet_d'Eau"),("Jura Mountains","Jura_Mountains"))),

 ("athens","Athens","Greece","","history","famous","🏛️",37.9838,23.7275,"Athens", H(
    ("The Acropolis","Acropolis_of_Athens"),("The Parthenon","Parthenon"),
    ("Plaka","Plaka"),("Monastiraki","Monastiraki"))),

 ("budapest","Budapest","Hungary","","city","famous","♨️",47.4979,19.0402,"Budapest", H(
    ("Hungarian Parliament","Hungarian_Parliament_Building"),("Buda Castle","Buda_Castle"),
    ("Széchenyi Thermal Bath","Széchenyi_thermal_bath"),("Chain Bridge","Széchenyi_Chain_Bridge"),
    ("The Ruin Pubs","Ruin_pub"))),

 ("mont-saint-michel","Mont Saint-Michel","France","Normandy","history","famous","⛪",48.6361,-1.5115,"Mont-Saint-Michel", H(
    ("The Island Abbey","Mont_Saint-Michel_Abbey"),("Tidal Flats","Mont_Saint-Michel"))),

 ("matera","Matera","Italy","Basilicata","history","famous","🪨",40.6664,16.6043,"Matera", H(
    ("The Sassi","Sassi_di_Matera"),("Rock Churches","Rupestrian_Churches_of_Matera"))),

 ("helsinki","Helsinki","Finland","","city","famous","🎨",60.1699,24.9384,"Helsinki", H(
    ("Kiasma","Kiasma"),("Finlandia Hall","Finlandia_Hall"),
    ("Helsinki Cathedral","Helsinki_Cathedral"),("Central Market","Market_Square,_Helsinki"))),

 ("bruges","Bruges","Belgium","","history","famous","🦢",51.2093,3.2247,"Bruges", H(
    ("Historic Canals","Bruges"),("Markt Square","Markt_(Bruges)"),("Belfry of Bruges","Belfry_of_Bruges"))),

 ("catalonia","Catalonia","Spain","Catalonia","nature","famous","⛰️",41.6,1.8,"Catalonia", H(
    ("Barcelona","Barcelona"),("Girona","Girona"),("Costa Brava","Costa_Brava"),
    ("Montserrat","Montserrat_(mountain)"))),

 ("london","London","United Kingdom","England","city","famous","🇬🇧",51.5074,-0.1278,"London", H(
    ("Tower Bridge","Tower_Bridge"),("Palace of Westminster","Palace_of_Westminster"),
    ("The Shard","The_Shard"),("British Museum","British_Museum"),
    ("National Gallery","National_Gallery"),("Hyde Park","Hyde_Park,_London"),
    ("Borough Market","Borough_Market"))),

 ("bavarian-alps","Bavarian Alps","Germany","Bavaria","mountain","famous","🏔️",47.4920,11.0950,"Bavarian_Alps", H(
    ("Zugspitze","Zugspitze"),("Garmisch-Partenkirchen","Garmisch-Partenkirchen"))),

 ("sardinia","Sardinia","Italy","Sardinia","island","famous","🏝️",40.1209,9.0129,"Sardinia", H(
    ("Costa Smeralda","Costa_Smeralda"),("Cala Luna","Cala_Luna"),("La Pelosa","Stintino"))),

 ("sofia","Sofia","Bulgaria","","city","hidden","⛪",42.6977,23.3219,"Sofia", H(
    ("Alexander Nevsky Cathedral","Alexander_Nevsky_Cathedral,_Sofia"),("Mount Vitosha","Vitosha"),
    ("Rotunda of St. George","Church_of_St_George,_Sofia"),("Central Mineral Baths","Central_Mineral_Baths"))),

 ("frankfurt","Frankfurt","Germany","Hesse","city","hidden","🏙️",50.1109,8.6821,"Frankfurt", H(
    ("Römerberg","Römerberg"),("Städel Museum","Städel"),("Goethe House","Goethe_House"),("Main River","Main_(river)"))),

 ("cambridge","Cambridge","England","","city","famous","🚣",52.2053,0.1218,"Cambridge", H(
    ("King's College","King's_College,_Cambridge"),("King's College Chapel","King's_College_Chapel,_Cambridge"),
    ("The Backs","The_Backs"),("Cavendish Laboratory","Cavendish_Laboratory"))),

 ("lofoten","Lofoten Islands","Norway","Nordland","island","hidden","🎣",68.2,13.6,"Lofoten", H(
    ("Arctic Fjords","Lofoten"),("Fishermen's Cabins (Rorbu)","Rorbu"))),

 ("portugal-coast","Portugal's Coast","Portugal","","coastal","famous","🏄",39.5,-9.2,"Portugal", H(
    ("Porto","Porto"),("Lisbon","Lisbon"),("Aveiro","Aveiro"),
    ("Cascais","Cascais"),("Arrábida National Park","Arrábida_Natural_Park"))),

 ("berlin","Berlin","Germany","","city","famous","🐻",52.5200,13.4050,"Berlin", H(
    ("Brandenburg Gate","Brandenburg_Gate"),("The Reichstag","Reichstag_building"),
    ("Museum Island","Museum_Island"))),

 ("alberobello","Alberobello","Italy","Apulia","village","hidden","🏠",40.7826,17.2369,"Alberobello", H(
    ("The Trulli","Trullo"),("Monti District","Alberobello"),("Church of St. Anthony","Alberobello"))),

 ("giethoorn","Giethoorn","Netherlands","Overijssel","village","hidden","🛶",52.7386,6.0780,"Giethoorn", H(
    ("The Canals","Giethoorn"),("Wooden Bridges","Giethoorn"))),

 ("valencia","Valencia","Spain","Valencian Community","city","famous","🐬",39.4699,-0.3763,"Valencia", H(
    ("City of Arts and Sciences","City_of_Arts_and_Sciences"),("Oceanogràfic","Oceanogràfic"))),

 ("paris","Paris","France","Île-de-France","city","famous","🗼",48.8566,2.3522,"Paris", H(
    ("Eiffel Tower","Eiffel_Tower"),("The Louvre","Louvre"),("Notre-Dame Cathedral","Notre-Dame_de_Paris"),
    ("Champs-Élysées","Champs-Élysées"),("Arc de Triomphe","Arc_de_Triomphe"),
    ("Tuileries Garden","Tuileries_Garden"),("Luxembourg Gardens","Luxembourg_Gardens"))),

 ("venice","Venice","Italy","Veneto","city","famous","🚤",45.4408,12.3155,"Venice", H(
    ("St. Mark's Square","Piazza_San_Marco"),("St. Mark's Basilica","St_Mark's_Basilica"),
    ("The Grand Canal","Grand_Canal_(Venice)"),("St. Mark's Campanile","St_Mark's_Campanile"))),

 ("istanbul","Istanbul","Turkey","","city","famous","🕌",41.0082,28.9784,"Istanbul", H(
    ("Hagia Sophia","Hagia_Sophia"),("The Blue Mosque","Sultan_Ahmed_Mosque"),
    ("Grand Bazaar","Grand_Bazaar,_Istanbul"),("Spice Bazaar","Spice_Bazaar"))),

 ("cyclades","Cyclades","Greece","South Aegean","island","famous","🏛️",37.0,25.2,"Cyclades", H(
    ("Santorini","Santorini"),("Mykonos","Mykonos"),("Paros","Paros"),("Delos","Delos"))),

 ("montenegro","Montenegro","Montenegro","","mountain","famous","🏔️",42.7087,19.3744,"Montenegro", H(
    ("Kotor","Kotor"),("Budva","Budva"),("Durmitor National Park","Durmitor"),("Lake Skadar","Lake_Skadar"))),

 ("obidos","Óbidos","Portugal","Oeste","village","hidden","🏯",39.3606,-9.1572,"Óbidos,_Portugal", H(
    ("Óbidos Castle","Óbidos_Castle"),("Medieval Walls","Óbidos,_Portugal"))),

 ("madrid","Madrid","Spain","","city","famous","🖼️",40.4168,-3.7038,"Madrid", H(
    ("Gran Vía","Gran_Vía"),("Almudena Cathedral","Almudena_Cathedral"),
    ("The Royal Palace","Royal_Palace_of_Madrid"),("Mercado de San Miguel","Mercado_de_San_Miguel"),
    ("Prado Museum","Museo_del_Prado"))),

 ("tuscany-florence","Tuscany & Florence","Italy","Tuscany","history","famous","🎨",43.7696,11.2558,"Florence", H(
    ("Uffizi Gallery","Uffizi"),("Florence Cathedral","Florence_Cathedral"),
    ("Piazza della Signoria","Piazza_della_Signoria"),("Siena","Siena"),
    ("Pisa","Pisa"),("Lucca","Lucca"),("Chianti","Chianti"))),

 ("jurassic-coast","Jurassic Coast","England","","coastal","hidden","🦕",50.62,-2.4,"Jurassic_Coast", H(
    ("Durdle Door","Durdle_Door"),("Lulworth Cove","Lulworth_Cove"))),

 ("norwegian-fjords","Norwegian Fjords","Norway","","nature","famous","⛰️",62.10,7.00,"Fjords_of_Norway", H(
    ("Geirangerfjord","Geirangerfjord"),("Nærøyfjord","Nærøyfjord"))),

 ("mostar","Mostar","Bosnia and Herzegovina","","history","famous","🌉",43.3438,17.8078,"Mostar", H(
    ("Stari Most","Stari_Most"),("Neretva River","Neretva"))),

 ("pyrenees","Pyrenees","Spain","","mountain","hidden","🏔️",42.6,1.0,"Pyrenees", H(
    ("Mountain Trails","Pyrenees"),("Romanesque Churches","Catalan_Romanesque"))),

 ("cesky-krumlov","Český Krumlov","Czech Republic","South Bohemia","village","hidden","🏰",48.8127,14.3175,"Český_Krumlov", H(
    ("Český Krumlov Castle","Český_Krumlov_Castle"),("Vltava River","Vltava"))),

 ("verdon-gorge","Verdon Gorge","France","Provence-Alpes-Côte d'Azur","nature","hidden","🏞️",43.75,6.33,"Verdon_Gorge", H(
    ("The Verdon River","Verdon_(river)"),("Lac de Sainte-Croix","Lac_de_Sainte-Croix"))),

 ("oslo","Oslo","Norway","","city","famous","🛶",59.9139,10.7522,"Oslo", H(
    ("Oslo Opera House","Oslo_Opera_House"),("Vigeland Sculpture Park","Vigeland_installation"),
    ("Viking Ship Museum","Viking_Ship_Museum_(Oslo)"),("Oslofjord","Oslofjord"))),

 ("corsica","Corsica","France","Corsica","island","famous","🏝️",41.9192,8.7386,"Corsica", H(
    ("Ajaccio","Ajaccio"),("Bonifacio","Bonifacio"))),

 ("balearic-islands","Balearic Islands","Spain","Balearic Islands","island","famous","🏖️",39.5696,2.6502,"Balearic_Islands", H(
    ("Mallorca","Mallorca"),("Ibiza","Ibiza"),("Menorca","Menorca"),("Formentera","Formentera"))),

 ("milan","Milan","Italy","Lombardy","city","famous","👗",45.4642,9.1900,"Milan", H(
    ("The Duomo","Milan_Cathedral"),("Galleria Vittorio Emanuele II","Galleria_Vittorio_Emanuele_II"),
    ("La Scala","La_Scala"),("Navigli","Navigli"),("Brera","Brera"))),

 ("porto","Porto","Portugal","","city","famous","🍷",41.1579,-8.6291,"Porto", H(
    ("Ribeira District","Ribeira_(Porto)"),("Dom Luís I Bridge","Dom_Luís_I_Bridge"),
    ("São Bento Station","São_Bento_railway_station"),("Porto Cathedral","Porto_Cathedral"),
    ("Douro River","Douro"),("Vila Nova de Gaia","Vila_Nova_de_Gaia"))),

 ("kotor","Kotor","Montenegro","","coastal","famous","🏰",42.4247,18.7712,"Kotor", H(
    ("The Old Town","Kotor"),("Fortifications of Kotor","Fortifications_of_Kotor"))),

 ("tallinn","Tallinn","Estonia","","history","famous","🏰",59.4370,24.7536,"Tallinn", H(
    ("The Old Town","Tallinn_Old_Town"),("Town Hall Square","Tallinn_Town_Hall"),("Toompea Hill","Toompea"))),

 ("prague","Prague","Czech Republic","","history","famous","🌉",50.0755,14.4378,"Prague", H(
    ("Astronomical Clock","Prague_astronomical_clock"),("Charles Bridge","Charles_Bridge"),
    ("Prague Castle","Prague_Castle"),("St. Vitus Cathedral","St._Vitus_Cathedral"),
    ("Old Town Square","Old_Town_Square"))),

 ("cinque-terre","Cinque Terre","Italy","Liguria","coastal","famous","🌅",44.1280,9.7095,"Cinque_Terre", H(
    ("Riomaggiore","Riomaggiore"),("Manarola","Manarola"),("Corniglia","Corniglia"),
    ("Vernazza","Vernazza"),("Monterosso al Mare","Monterosso_al_Mare"))),

 ("lisbon","Lisbon","Portugal","","city","famous","🚋",38.7223,-9.1393,"Lisbon", H(
    ("Belém Tower","Belém_Tower"),("Jerónimos Monastery","Jerónimos_Monastery"),
    ("Alfama District","Alfama"),("Bairro Alto","Bairro_Alto"),("Tagus River","Tagus"))),

 ("normandy","Normandy","France","Normandy","coastal","famous","🪖",49.18,-0.37,"Normandy", H(
    ("D-Day Beaches","Normandy_landings"),("Étretat Cliffs","Étretat"))),

 ("delft","Delft","Netherlands","South Holland","city","hidden","🏺",52.0116,4.3571,"Delft", H(
    ("Historic Canals","Delft"),("The New Church","Nieuwe_Kerk_(Delft)"))),

 ("transylvania","Transylvania","Romania","Transylvania","history","famous","🧛",45.7489,24.5,"Transylvania", H(
    ("Bran Castle","Bran_Castle"),("Brașov","Brașov"),("Sibiu","Sibiu"),("Cluj-Napoca","Cluj-Napoca"))),

 ("barcelona","Barcelona","Spain","Catalonia","city","famous","🏛️",41.3851,2.1734,"Barcelona", H(
    ("Sagrada Família","Sagrada_Família"),("Casa Batlló","Casa_Batlló"),("Park Güell","Park_Güell"),
    ("Passeig de Gràcia","Passeig_de_Gràcia"),("The Gothic Quarter","Gothic_Quarter,_Barcelona"),
    ("Barceloneta Beach","Barceloneta_Beach"))),

 ("aveiro","Aveiro","Portugal","Centro","coastal","hidden","🛶",40.6405,-8.6538,"Aveiro", H(
    ("The Canals","Aveiro"),("Costa Nova","Costa_Nova_do_Prado"),("Praia da Barra","Praia_da_Barra"))),

 ("amalfi-coast","Amalfi Coast","Italy","Campania","coastal","famous","🍋",40.6340,14.6027,"Amalfi_Coast", H(
    ("Positano","Positano"),("Amalfi","Amalfi"),("Ravello","Ravello"))),

 ("meteora","Meteora","Greece","Thessaly","nature","hidden","🧗",39.7217,21.6306,"Meteora", H(
    ("Great Meteoron Monastery","Monastery_of_Great_Meteoron"),("Clifftop Monasteries","Meteora"))),
]

# ---------------------------------------------------------------------------
# Authored copy for marquee destinations. Everything else falls back to the
# live Wikipedia summary in the front-end.
# ---------------------------------------------------------------------------
BLURBS = {
 "vienna": {
   "blurb": "Once the seat of the Habsburg empire, Vienna pairs imperial palaces and gilded concert halls with a café culture that turns sitting still into an art form. The historic centre is a UNESCO World Heritage Site, and the city has topped global liveability rankings year after year.",
   "fun_fact": "Vienna's coffee-house culture is recognised by UNESCO as 'intangible cultural heritage' — and the croissant was reputedly invented here, not in France, to celebrate breaking an Ottoman siege."},
 "rome": {
   "blurb": "The Eternal City layers nearly three thousand years of history in a single skyline — emperors, popes, and Vespas all sharing the same cobblestones. From the Colosseum to the Vatican, no other capital wears its past so casually.",
   "fun_fact": "Romans still throw an estimated €1.5 million in coins into the Trevi Fountain every year — all of it collected and donated to charity."},
 "paris": {
   "blurb": "The City of Light has set the global standard for art, fashion, and romance for centuries. Beyond the Eiffel Tower and the Louvre, Paris is a city of boulevards, riverside booksellers, and neighbourhood cafés best discovered on foot.",
   "fun_fact": "The Eiffel Tower was meant to be torn down after 20 years — it was saved only because it made a perfect radio antenna."},
 "london": {
   "blurb": "Two thousand years of history meet relentless reinvention along the Thames. Royal palaces, world-class museums (most of them free), and a theatre district that never sleeps make London one of the planet's great cities.",
   "fun_fact": "The London Underground is the world's oldest underground railway, opened in 1863 — and 'Mind the Gap' has been echoing through it since 1968."},
 "amsterdam": {
   "blurb": "Built on a web of 17th-century canals, Amsterdam is a city of gabled merchant houses, world-class art, and more bicycles than people. The compact centre is a UNESCO World Heritage Site you can cross entirely on two wheels.",
   "fun_fact": "Amsterdam has roughly 165 canals spanning over 100 kilometres — and an estimated 900,000 bicycles, far outnumbering its residents."},
 "barcelona": {
   "blurb": "Gaudí's surreal architecture, a medieval Gothic core, and Mediterranean beaches all converge in Catalonia's vibrant capital. The unfinished Sagrada Família has been under construction since 1882 and still draws the world.",
   "fun_fact": "The Sagrada Família is expected to be completed more than 140 years after it began — Gaudí himself said, 'My client is not in a hurry.'"},
 "prague": {
   "blurb": "The 'City of a Hundred Spires' came through the 20th century almost untouched, leaving a fairy-tale tangle of Gothic, Baroque, and Art Nouveau. Charles Bridge and the hilltop castle anchor one of Europe's best-preserved old towns.",
   "fun_fact": "Prague Castle is the largest ancient castle complex in the world, covering nearly 70,000 square metres."},
 "venice": {
   "blurb": "A city built on 118 islands laced by canals instead of streets, Venice has no cars — only boats and footbridges. For a thousand years it was a maritime superpower, and today it remains utterly unlike anywhere else on Earth.",
   "fun_fact": "Venice rests on millions of wooden pilings driven into the lagoon mud — submerged and starved of oxygen, the wood has petrified rather than rotted."},
 "istanbul": {
   "blurb": "The only city that straddles two continents, Istanbul has been the capital of Roman, Byzantine, and Ottoman empires in turn. Minarets, domes, and bazaars crowd the shores of the Bosphorus where Europe meets Asia.",
   "fun_fact": "Hagia Sophia has served as a cathedral, a mosque, a museum, and a mosque again across nearly 1,500 years of continuous use."},
 "athens": {
   "blurb": "The birthplace of democracy and Western philosophy, Athens has been continuously inhabited for over 3,400 years. The Parthenon still crowns the Acropolis above a sprawling, sun-bleached modern capital.",
   "fun_fact": "The Parthenon was built without mortar and uses subtle curves — its columns lean slightly inward — to correct optical illusions and appear perfectly straight."},
 "budapest": {
   "blurb": "Two cities — hilly Buda and flat Pest — face each other across the Danube, stitched together by grand bridges. Thermal springs feed ornate bathhouses, and crumbling courtyards have become legendary 'ruin pubs'.",
   "fun_fact": "Budapest sits on over 100 thermal springs and is the only capital city in the world classified as a spa town."},
 "edinburgh": {
   "blurb": "Scotland's dramatic capital rises in tiers from a medieval Old Town to an elegant Georgian New Town, all watched over by a castle on an extinct volcano. In August it becomes the largest arts festival on Earth.",
   "fun_fact": "Edinburgh was the first city in the world to have its own fire brigade — and its Old and New Towns are jointly a UNESCO World Heritage Site."},
 "dubrovnik": {
   "blurb": "Ringed by mighty stone walls dropping straight into the Adriatic, Dubrovnik was a wealthy independent republic for centuries. Its marble Stradun and terracotta rooftops have made it one of the Mediterranean's most photographed cities.",
   "fun_fact": "The Republic of Ragusa, as Dubrovnik was known, abolished slavery in 1416 — centuries ahead of most of Europe."},
 "hallstatt": {
   "blurb": "Wedged between a glassy lake and steep alpine slopes, this tiny Austrian village looks almost too perfect to be real. Its salt mine is among the oldest in the world, worked continuously for some 7,000 years.",
   "fun_fact": "Hallstatt is so iconic that a full-scale replica of the village was built in Guangdong, China."},
 "neuschwanstein": {
   "blurb": "The dream castle of 'Mad' King Ludwig II rises from a forested Bavarian crag like something from a storybook. Built in the 19th century in homage to Wagner's operas, it inspired Disney's Sleeping Beauty Castle.",
   "fun_fact": "Ludwig II spent only 11 nights in Neuschwanstein before his mysterious death — and the castle was opened to paying visitors just weeks later."},
 "cinque-terre": {
   "blurb": "Five centuries-old fishing villages cling to the cliffs of the Italian Riviera, linked by footpaths, terraced vineyards, and a single railway line. Cars can't reach the heart of them — you arrive by train, boat, or on foot.",
   "fun_fact": "The dry-stone walls that terrace the Cinque Terre hillsides stretch an estimated 7,000 km — comparable in length to the Great Wall of China."},
 "iceland": {
   "blurb": "A young island straddling two tectonic plates, Iceland is a landscape of volcanoes, glaciers, geysers, and black-sand coasts. Nearly all its energy comes from the geothermal forces simmering beneath it.",
   "fun_fact": "At Þingvellir you can walk — or dive — directly between the North American and Eurasian tectonic plates as they pull apart."},
 "faroe-islands": {
   "blurb": "Eighteen wind-scoured islands rising sheer from the North Atlantic, the Faroes are all green cliffs, hidden fjords, and turf-roofed villages. There are said to be more sheep here than people.",
   "fun_fact": "The Faroese once 'hired sheep' fitted with cameras to map the islands on Google Street View — they called it 'Sheep View'."},
 "lisbon": {
   "blurb": "Spread across seven hills above the Tagus, Lisbon is a city of pastel façades, rattling yellow trams, and melancholic fado music. Its golden light and tiled streets have earned it a devoted following.",
   "fun_fact": "Lisbon is one of the oldest cities in Western Europe — predating London, Paris, and Rome by centuries."},
 "sintra": {
   "blurb": "A misty hilltown of palaces, gardens, and fog-wrapped forests just outside Lisbon, Sintra was the summer retreat of Portuguese royalty. The candy-coloured Pena Palace is its crown jewel.",
   "fun_fact": "Quinta da Regaleira's 'Initiation Well' is an inverted underground tower with a spiral staircase descending 27 metres into the earth."},
 "cappadocia": {
   "blurb": "Soft volcanic rock eroded into a surreal landscape of 'fairy chimneys', honeycombed by cave dwellings and entire underground cities. At dawn the sky fills with hundreds of hot-air balloons.",
   "fun_fact": "The underground city of Derinkuyu could shelter up to 20,000 people, with stables, churches, and wineries dug as deep as 85 metres."},
 "mont-saint-michel": {
   "blurb": "A medieval abbey crowns this rocky tidal island off the Normandy coast, encircled by some of the fastest-moving tides in Europe. For centuries it was both a pilgrimage site and an impregnable fortress.",
   "fun_fact": "The tide here can move as fast as a galloping horse, and once a day it surrounds the island completely."},
 "meteora": {
   "blurb": "Six Eastern Orthodox monasteries perch impossibly atop sheer rock pillars rising hundreds of metres above the plains of Thessaly. For centuries monks reached them only by rope ladders and nets.",
   "fun_fact": "The name Meteora means 'suspended in the air' — and until the 1920s the only way up to some monasteries was being hauled in a net."},
 "plitvice": {
   "blurb": "Sixteen terraced lakes spill into one another through a cascade of waterfalls, their water shifting from turquoise to emerald with the light. Wooden walkways thread directly across the water.",
   "fun_fact": "The travertine barriers that create Plitvice's waterfalls are still growing about a centimetre each year, built by mosses and bacteria."},
 "santorini-note": {},  # placeholder (unused)
 "kotor": {
   "blurb": "Tucked at the end of a fjord-like bay, the walled town of Kotor hides a labyrinth of medieval squares beneath a mountain fortress. The climb up its 1,350 steps rewards you with one of the Adriatic's great views.",
   "fun_fact": "Kotor's defensive walls climb more than 260 metres up the mountainside to the fortress of San Giovanni."},
}


def build():
    out = []
    seen = set()
    for (id_, name, country, sub, type_, tag, emoji, lat, lng, slug, highlights) in DEST:
        assert id_ not in seen, f"duplicate id: {id_}"
        seen.add(id_)
        flag = FLAG.get(country, "🇪🇺")
        rec = {
            "id": id_,
            "name": name,
            "country": country,
            "country_flag": flag,
            "region": sub,
            "type": type_,
            "tag": tag,
            "emoji": emoji,
            "coordinates": {"lat": lat, "lng": lng},
            "street_view": {"lat": lat, "lng": lng, "heading": 0, "pitch": 0, "fov": 90},
            "wikipedia_slug": slug,
            "sounds": [SOUND.get(type_, "european-plaza.mp3")],
            "highlights": highlights,
            "blurb": BLURBS.get(id_, {}).get("blurb", ""),
            "fun_fact": BLURBS.get(id_, {}).get("fun_fact", ""),
            "hidden_gem_tip": BLURBS.get(id_, {}).get("hidden_gem_tip"),
        }
        out.append(rec)

    doc = {
        "country": None,
        "continent": "Europe",
        "code": "EU",
        "locations": out,
    }

    here = os.path.dirname(os.path.abspath(__file__))
    dest = os.path.join(here, "..", "data", "europe.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    hl = sum(len(r["highlights"]) for r in out)
    authored = sum(1 for r in out if r["blurb"])
    print(f"✓ wrote {len(out)} destinations, {hl} highlights "
          f"({authored} with authored copy) -> {os.path.normpath(dest)}")


if __name__ == "__main__":
    build()
