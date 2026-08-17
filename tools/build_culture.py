#!/usr/bin/env python3
"""
build_culture.py — extend js/lib/culture.js's four lookup tables so the
location-page culture panel, the local-radio lookup and the live currency
converter work for every country in data/countries.json, not just the
original 39.

Patches js/lib/culture.js IN PLACE, inserting a clearly-marked block before each
table's closing brace. Idempotent: re-running replaces the marked block.

THE TRAP THIS SCRIPT USED TO SET (fixed 2026-08-17, read before editing):
  The marked block is REPLACED wholesale on every run, so any country that was
  hand-added to culture.js inside the markers — and never mirrored back into
  ROWS below — is silently DELETED the next time anyone runs this. That had
  already happened to four countries (DR Congo, Namibia, North Korea, Zimbabwe)
  before it was caught. They are now back in ROWS, and `check_no_orphans()`
  aborts the run rather than dropping anything it does not recognise. If that
  check fires, copy the named entries into ROWS — do not delete the guard.
  Corollary: hand-editing culture.js inside the markers is never the fix.
  Add the row here and re-run.

Confidence note (be honest): ISO 3166 codes, ISO 4217 currency codes, capitals
and driving side are factual. `dish` is editorial. `phrases` (greetings) are
best-effort — native scripts where confident, romanized where the script is
error-prone — and DESERVE A NATIVE-SPEAKER REVIEW PASS before being treated as
authoritative (logged in OVERHAUL.md §4). Populations are rounded ~2023 figures.

Run:  python3 tools/build_culture.py
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CULT = os.path.join(HERE, "..", "js", "lib", "culture.js")
BEGIN = "  /* === world-expansion countries (build_culture.py) — review phrases/dishes === */"
END = "  /* === end world-expansion === */"
TABLES = ("COUNTRY_PROFILES", "COUNTRY_CODES", "CURRENCY_CODES", "COUNTRY_FACTS")

# country: code, ccy, ccy_label, lang, dish, [phrases], capital, pop, drives, plug
ROWS = {
 # ---------- Asia ----------
 "Japan": ("JP","JPY","Japanese yen (¥)","Japanese","Sushi, ramen & tempura",
   [["Hello","こんにちは"],["Thank you","ありがとう"],["Cheers","乾杯 (Kanpai)"]],"Tokyo","124M","Left","Type A/B · 100V"),
 "China": ("CN","CNY","Chinese yuan (¥)","Mandarin Chinese","Peking duck & dim sum",
   [["Hello","你好 (Nǐ hǎo)"],["Thank you","谢谢 (Xièxie)"],["Cheers","干杯 (Gānbēi)"]],"Beijing","1.41B","Right","Type A/I · 220V"),
 "India": ("IN","INR","Indian rupee (₹)","Hindi / English","Curry, biryani & dosa",
   [["Hello","नमस्ते (Namaste)"],["Thank you","धन्यवाद (Dhanyavaad)"],["Cheers","Cheers"]],"New Delhi","1.43B","Left","Type C/D/M · 230V"),
 "South Korea": ("KR","KRW","South Korean won (₩)","Korean","Kimchi & Korean BBQ",
   [["Hello","안녕하세요 (Annyeong)"],["Thank you","감사합니다 (Gamsahamnida)"],["Cheers","건배 (Geonbae)"]],"Seoul","52M","Right","Type C/F · 220V"),
 "Thailand": ("TH","THB","Thai baht (฿)","Thai","Pad Thai & green curry",
   [["Hello","สวัสดี (Sawasdee)"],["Thank you","ขอบคุณ (Khop khun)"],["Cheers","ไชโย (Chai-yo)"]],"Bangkok","72M","Left","Type A/B/C · 230V"),
 "Malaysia": ("MY","MYR","Malaysian ringgit (RM)","Malay","Nasi lemak & laksa",
   [["Hello","Selamat"],["Thank you","Terima kasih"],["Cheers","Cheers"]],"Kuala Lumpur","34M","Left","Type G · 240V"),
 "Singapore": ("SG","SGD","Singapore dollar (S$)","English / Malay / Mandarin / Tamil","Chicken rice & chilli crab",
   [["Hello","Hello"],["Thank you","Thank you / Terima kasih"],["Cheers","Cheers / Yum seng"]],"Singapore","5.9M","Left","Type G · 230V"),
 "Philippines": ("PH","PHP","Philippine peso (₱)","Filipino / English","Adobo & lechon",
   [["Hello","Kumusta"],["Thank you","Salamat"],["Cheers","Tagay"]],"Manila","117M","Right","Type A/B/C · 220V"),
 "Vietnam": ("VN","VND","Vietnamese đồng (₫)","Vietnamese","Phở & bánh mì",
   [["Hello","Xin chào"],["Thank you","Cảm ơn"],["Cheers","Dô / Một hai ba dô"]],"Hanoi","99M","Right","Type A/C · 220V"),
 "Cambodia": ("KH","KHR","Cambodian riel (៛)","Khmer","Fish amok & lok lak",
   [["Hello","Suosdey"],["Thank you","Aw kun"],["Cheers","Chol mouy"]],"Phnom Penh","17M","Right","Type A/C/G · 230V"),
 "Laos": ("LA","LAK","Lao kip (₭)","Lao","Larb & sticky rice",
   [["Hello","Sabaidee"],["Thank you","Khob chai"],["Cheers","Sok dee"]],"Vientiane","7.6M","Right","Type A/B/C · 230V"),
 "Taiwan": ("TW","TWD","New Taiwan dollar (NT$)","Mandarin Chinese","Beef noodle soup & bubble tea",
   [["Hello","你好 (Nǐ hǎo)"],["Thank you","謝謝 (Xièxie)"],["Cheers","乾杯 (Gānbēi)"]],"Taipei","23M","Right","Type A/B · 110V"),
 "Mongolia": ("MN","MNT","Mongolian tögrög (₮)","Mongolian","Buuz dumplings & khorkhog",
   [["Hello","Sain baina uu"],["Thank you","Bayarlalaa"],["Cheers","Tuluunii toloo"]],"Ulaanbaatar","3.4M","Right","Type C/E · 220V"),
 "Sri Lanka": ("LK","LKR","Sri Lankan rupee (Rs)","Sinhala / Tamil","Rice & curry, hoppers",
   [["Hello","Ayubowan"],["Thank you","Sthuthi"],["Cheers","Cheers"]],"Colombo","22M","Left","Type D/G/M · 230V"),
 "Israel": ("IL","ILS","Israeli shekel (₪)","Hebrew","Hummus, falafel & shakshuka",
   [["Hello","שלום (Shalom)"],["Thank you","תודה (Toda)"],["Cheers","לחיים (L'chaim)"]],"Jerusalem","9.8M","Right","Type C/H · 230V"),
 "United Arab Emirates": ("AE","AED","UAE dirham (د.إ)","Arabic","Shawarma & machboos",
   [["Hello","مرحبا (Marhaba)"],["Thank you","شكرا (Shukran)"],["Cheers","بصحتك (Bisaha)"]],"Abu Dhabi","9.5M","Right","Type G · 230V"),
 "Saudi Arabia": ("SA","SAR","Saudi riyal (ر.س)","Arabic","Kabsa & shawarma",
   [["Hello","مرحبا (Marhaba)"],["Thank you","شكرا (Shukran)"],["Cheers","بصحتك (Bisaha)"]],"Riyadh","37M","Right","Type G · 230V"),
 "Qatar": ("QA","QAR","Qatari riyal (ر.ق)","Arabic","Machboos & balaleet",
   [["Hello","مرحبا (Marhaba)"],["Thank you","شكرا (Shukran)"],["Cheers","بصحتك (Bisaha)"]],"Doha","2.7M","Right","Type D/G · 240V"),
 "Jordan": ("JO","JOD","Jordanian dinar (د.ا)","Arabic","Mansaf & falafel",
   [["Hello","مرحبا (Marhaba)"],["Thank you","شكرا (Shukran)"],["Cheers","بصحتك (Bisaha)"]],"Amman","11M","Right","Type C/D/F/G · 230V"),
 "Iran": ("IR","IRR","Iranian rial (﷼)","Persian (Farsi)","Kebab & ghormeh sabzi",
   [["Hello","سلام (Salam)"],["Thank you","ممنون (Mamnoon)"],["Cheers","به سلامتی (Be salamati)"]],"Tehran","89M","Right","Type C/F · 230V"),
 "Armenia": ("AM","AMD","Armenian dram (֏)","Armenian","Khorovats & dolma",
   [["Hello","Բարև (Barev)"],["Thank you","Շնորհակալություն (Shnorhakalutyun)"],["Cheers","Կենաց (Kenats)"]],"Yerevan","3.0M","Right","Type C/F · 230V"),
 "Azerbaijan": ("AZ","AZN","Azerbaijani manat (₼)","Azerbaijani","Plov & dolma",
   [["Hello","Salam"],["Thank you","Təşəkkür"],["Cheers","Nuş olsun"]],"Baku","10M","Right","Type C/F · 220V"),
 "Georgia": ("GE","GEL","Georgian lari (₾)","Georgian","Khachapuri & khinkali",
   [["Hello","გამარჯობა (Gamarjoba)"],["Thank you","მადლობა (Madloba)"],["Cheers","გაუმარჯოს (Gaumarjos)"]],"Tbilisi","3.7M","Right","Type C/F · 220V"),
 "North Korea": ("KP","KPW","North Korean won (₩)","Korean","Pyongyang naengmyŏn (cold noodles)",
   [["Hello","안녕하십니까 (Annyŏng hasimnikka)"],["Thank you","감사합니다 (Kamsahamnida)"],["Cheers","축배 (Chukbae)"]],"Pyongyang","26M","Right","Type A/C/F · 220V"),
 # ---------- Africa ----------
 "Morocco": ("MA","MAD","Moroccan dirham (د.م.)","Arabic / Berber","Tagine & couscous",
   [["Hello","السلام (Salam)"],["Thank you","شكرا (Shukran)"],["Cheers","بصحتك (Bsaha)"]],"Rabat","37M","Right","Type C/E · 220V"),
 "Egypt": ("EG","EGP","Egyptian pound (£)","Arabic","Koshari & ful medames",
   [["Hello","السلام عليكم (Salam)"],["Thank you","شكرا (Shukran)"],["Cheers","في صحتك (Fi sahetak)"]],"Cairo","113M","Right","Type C/F · 220V"),
 "Kenya": ("KE","KES","Kenyan shilling (KSh)","Swahili / English","Nyama choma & ugali",
   [["Hello","Jambo"],["Thank you","Asante"],["Cheers","Maisha marefu"]],"Nairobi","55M","Left","Type G · 240V"),
 "Senegal": ("SN","XOF","West African CFA franc (CFA)","French / Wolof","Thieboudienne",
   [["Hello","Bonjour / Salaam"],["Thank you","Merci / Jërëjëf"],["Cheers","Santé"]],"Dakar","18M","Right","Type C/D/E/K · 230V"),
 "Ethiopia": ("ET","ETB","Ethiopian birr (Br)","Amharic","Injera & doro wat",
   [["Hello","ሰላም (Selam)"],["Thank you","አመሰግናለሁ (Ameseginalehu)"],["Cheers","Bechewanet"]],"Addis Ababa","127M","Right","Type C/F · 220V"),
 "Gambia": ("GM","GMD","Gambian dalasi (D)","English","Domoda & benachin",
   [["Hello","Hello / Salaam"],["Thank you","Thank you / Jërejëf"],["Cheers","Cheers"]],"Banjul","2.7M","Right","Type G · 230V"),
 "South Africa": ("ZA","ZAR","South African rand (R)","English / Zulu / Afrikaans","Braai & bobotie",
   [["Hello","Hello / Sawubona"],["Thank you","Thank you / Ngiyabonga"],["Cheers","Cheers"]],"Pretoria","60M","Left","Type M/N · 230V"),
 "Namibia": ("NA","NAD","Namibian dollar (N$)","English / Oshiwambo / Afrikaans","Kapana & game biltong",
   [["Hello","Hello / Wa lalapo"],["Thank you","Thank you / Tangi"],["Cheers","Cheers"]],"Windhoek","2.6M","Left","Type D/M · 220V"),
 "Zimbabwe": ("ZW","ZWL","Zimbabwe gold (ZiG) & US dollar","Shona / Ndebele / English","Sadza & nyama",
   [["Hello","Mhoro"],["Thank you","Ndatenda"],["Cheers","Cheers"]],"Harare","16M","Left","Type D/G · 220V"),
 "DR Congo": ("CD","CDF","Congolese franc (FC)","French / Lingala / Swahili","Fufu & pondu",
   [["Hello","Mbote"],["Thank you","Matondo"],["Cheers","Santé"]],"Kinshasa","102M","Right","Type C/D/E · 220V"),
 # ---------- Africa, 2026-08 batch (the other 44, so all 54 are covered) ----------
 "Tunisia": ("TN","TND","Tunisian dinar (د.ت)","Arabic / French","Couscous & brik",
   [["Hello","السلام (Salam)"],["Thank you","شكرا (Shukran)"],["Cheers","بصحتك (Bsahtek)"]],"Tunis","12M","Right","Type C/E · 230V"),
 "Algeria": ("DZ","DZD","Algerian dinar (د.ج)","Arabic / Berber / French","Couscous & chorba",
   [["Hello","السلام (Salam)"],["Thank you","شكرا (Shukran)"],["Cheers","بصحتك (Bsahtek)"]],"Algiers","46M","Right","Type C/F · 230V"),
 "Libya": ("LY","LYD","Libyan dinar (ل.د)","Arabic","Bazin & couscous",
   [["Hello","السلام (Salam)"],["Thank you","شكرا (Shukran)"],["Cheers","في صحتك (Fi sahetak)"]],"Tripoli","7.3M","Right","Type C/L · 230V"),
 "Sudan": ("SD","SDG","Sudanese pound (ج.س)","Arabic / English","Ful medames & kisra",
   [["Hello","السلام عليكم (Salam)"],["Thank you","شكرا (Shukran)"],["Cheers","في صحتك (Fi sahetak)"]],"Khartoum","48M","Right","Type C/D · 230V"),
 "South Sudan": ("SS","SSP","South Sudanese pound (£)","English / Arabic","Kisra & asida",
   [["Hello","Hello / Salam"],["Thank you","Thank you / Shukran"],["Cheers","Cheers"]],"Juba","11M","Right","Type C/D · 230V"),
 "Mauritania": ("MR","MRU","Mauritanian ouguiya (UM)","Arabic / French","Thieboudienne & mechoui",
   [["Hello","السلام (Salam)"],["Thank you","شكرا (Shukran)"],["Cheers","بصحتك (Bsaha)"]],"Nouakchott","4.9M","Right","Type C · 220V"),
 "Mali": ("ML","XOF","West African CFA franc (CFA)","French / Bambara","Tigadèguèna — peanut stew",
   [["Hello","Bonjour / I ni ce"],["Thank you","Merci / I ni ce"],["Cheers","Santé"]],"Bamako","23M","Right","Type C/E · 220V"),
 "Niger": ("NE","XOF","West African CFA franc (CFA)","French / Hausa","Dambou & brochettes",
   [["Hello","Bonjour / Sannu"],["Thank you","Merci / Na gode"],["Cheers","Santé"]],"Niamey","26M","Right","Type C/D/E/F · 220V"),
 "Chad": ("TD","XAF","Central African CFA franc (FCFA)","French / Arabic","Boule & daraba",
   [["Hello","Bonjour / Salam"],["Thank you","Merci / Shukran"],["Cheers","Santé"]],"N'Djamena","18M","Right","Type C/D/E/F · 220V"),
 "Burkina Faso": ("BF","XOF","West African CFA franc (CFA)","French / Mooré","Riz gras & tô",
   [["Hello","Bonjour / Ne y windga"],["Thank you","Merci / Barka"],["Cheers","Santé"]],"Ouagadougou","23M","Right","Type C/E · 220V"),
 "Nigeria": ("NG","NGN","Nigerian naira (₦)","English / Hausa / Yoruba / Igbo","Jollof rice & suya",
   [["Hello","Hello / Sannu"],["Thank you","Thank you / Na gode"],["Cheers","Cheers"]],"Abuja","224M","Right","Type D/G · 230V"),
 "Ghana": ("GH","GHS","Ghanaian cedi (₵)","English / Twi","Jollof, waakye & banku",
   [["Hello","Hello / Ɛte sɛn"],["Thank you","Medaase"],["Cheers","Cheers"]],"Accra","34M","Right","Type D/G · 230V"),
 "Togo": ("TG","XOF","West African CFA franc (CFA)","French / Ewé","Fufu & akpan",
   [["Hello","Bonjour / Woezon"],["Thank you","Merci / Akpé"],["Cheers","Santé"]],"Lomé","9.1M","Right","Type C · 220V"),
 "Benin": ("BJ","XOF","West African CFA franc (CFA)","French / Fon","Amiwo & akassa",
   [["Hello","Bonjour / Kudo"],["Thank you","Merci / Awanou"],["Cheers","Santé"]],"Porto-Novo","13M","Right","Type C/E · 220V"),
 "Côte d'Ivoire": ("CI","XOF","West African CFA franc (CFA)","French","Attiéké & kedjenou",
   [["Hello","Bonjour"],["Thank you","Merci"],["Cheers","Santé"]],"Yamoussoukro","29M","Right","Type C/E · 220V"),
 "Guinea": ("GN","GNF","Guinean franc (FG)","French / Susu / Fula","Riz gras & poulet yassa",
   [["Hello","Bonjour / Tana muxu"],["Thank you","Merci"],["Cheers","Santé"]],"Conakry","14M","Right","Type C/F/K · 220V"),
 "Guinea-Bissau": ("GW","XOF","West African CFA franc (CFA)","Portuguese / Creole","Caldo de mancarra",
   [["Hello","Olá / Kuma ku bai"],["Thank you","Obrigado"],["Cheers","Saúde"]],"Bissau","2.2M","Right","Type C · 220V"),
 "Sierra Leone": ("SL","SLE","Sierra Leonean leone (Le)","English / Krio","Cassava leaves & jollof",
   [["Hello","Hello / Kushɛ"],["Thank you","Tenki"],["Cheers","Cheers"]],"Freetown","8.6M","Right","Type D/G · 230V"),
 "Liberia": ("LR","LRD","Liberian dollar (L$)","English","Jollof rice & palm butter",
   [["Hello","Hello"],["Thank you","Thank you"],["Cheers","Cheers"]],"Monrovia","5.4M","Right","Type A/B/C/F · 120V"),
 "Cape Verde": ("CV","CVE","Cape Verdean escudo ($)","Portuguese / Creole","Cachupa",
   [["Hello","Olá / Oi"],["Thank you","Obrigado"],["Cheers","Saúde"]],"Praia","600K","Right","Type C/F · 220V"),
 "Cameroon": ("CM","XAF","Central African CFA franc (FCFA)","French / English","Ndolé & poulet DG",
   [["Hello","Bonjour / Hello"],["Thank you","Merci / Thank you"],["Cheers","Santé"]],"Yaoundé","28M","Right","Type C/E · 220V"),
 "Gabon": ("GA","XAF","Central African CFA franc (FCFA)","French","Poulet nyembwe",
   [["Hello","Bonjour"],["Thank you","Merci"],["Cheers","Santé"]],"Libreville","2.4M","Right","Type C · 220V"),
 "Republic of the Congo": ("CG","XAF","Central African CFA franc (FCFA)","French / Lingala / Kituba","Saka-saka & poulet moambé",
   [["Hello","Bonjour / Mbote"],["Thank you","Merci / Matondo"],["Cheers","Santé"]],"Brazzaville","6.1M","Right","Type C/E · 230V"),
 "Central African Republic": ("CF","XAF","Central African CFA franc (FCFA)","Sango / French","Kanda ti nyma & gozo",
   [["Hello","Bara ala"],["Thank you","Singila"],["Cheers","Santé"]],"Bangui","5.7M","Right","Type C/E · 220V"),
 "Equatorial Guinea": ("GQ","XAF","Central African CFA franc (FCFA)","Spanish / French / Portuguese","Succotash & pepesup",
   [["Hello","Hola"],["Thank you","Gracias"],["Cheers","Salud"]],"Malabo","1.7M","Right","Type C/E · 220V"),
 "São Tomé and Príncipe": ("ST","STN","São Tomé dobra (Db)","Portuguese","Calulu & banana bread",
   [["Hello","Olá"],["Thank you","Obrigado"],["Cheers","Saúde"]],"São Tomé","230K","Right","Type C/F · 220V"),
 "Angola": ("AO","AOA","Angolan kwanza (Kz)","Portuguese","Funge & muamba de galinha",
   [["Hello","Olá"],["Thank you","Obrigado"],["Cheers","Saúde"]],"Luanda","36M","Right","Type C · 220V"),
 "Uganda": ("UG","UGX","Ugandan shilling (USh)","English / Swahili / Luganda","Matoke & the rolex",
   [["Hello","Oli otya"],["Thank you","Webale"],["Cheers","Cheers"]],"Kampala","48M","Left","Type G · 240V"),
 "Rwanda": ("RW","RWF","Rwandan franc (FRw)","Kinyarwanda / English / French","Isombe & brochettes",
   [["Hello","Muraho"],["Thank you","Murakoze"],["Cheers","Cheers"]],"Kigali","14M","Right","Type C/J · 230V"),
 "Burundi": ("BI","BIF","Burundian franc (FBu)","Kirundi / French","Boko boko & red beans",
   [["Hello","Amahoro"],["Thank you","Urakoze"],["Cheers","Santé"]],"Gitega","13M","Right","Type C/E · 220V"),
 "Tanzania": ("TZ","TZS","Tanzanian shilling (TSh)","Swahili / English","Ugali & nyama choma",
   [["Hello","Jambo / Habari"],["Thank you","Asante"],["Cheers","Afya"]],"Dodoma","67M","Left","Type D/G · 230V"),
 "Eritrea": ("ER","ERN","Eritrean nakfa (Nfk)","Tigrinya / Arabic / English","Injera & zigni",
   [["Hello","ሰላም (Selam)"],["Thank you","የቐንየለይ (Yekenyeley)"],["Cheers","Cheers"]],"Asmara","3.7M","Right","Type C/L · 230V"),
 "Djibouti": ("DJ","DJF","Djiboutian franc (Fdj)","French / Arabic","Skoudehkaris",
   [["Hello","Bonjour / Salam"],["Thank you","Merci / Shukran"],["Cheers","Santé"]],"Djibouti City","1.1M","Right","Type C/E · 220V"),
 "Somalia": ("SO","SOS","Somali shilling (Sh)","Somali / Arabic","Bariis iskukaris & suqaar",
   [["Hello","Iska warran"],["Thank you","Mahadsanid"],["Cheers","Cheers"]],"Mogadishu","18M","Right","Type C · 220V"),
 "Madagascar": ("MG","MGA","Malagasy ariary (Ar)","Malagasy / French","Romazava & ravitoto",
   [["Hello","Salama"],["Thank you","Misaotra"],["Cheers","Santé"]],"Antananarivo","30M","Right","Type C/E · 220V"),
 "Mauritius": ("MU","MUR","Mauritian rupee (₨)","English / French / Creole","Dholl puri & rougaille",
   [["Hello","Bonzour"],["Thank you","Mersi"],["Cheers","Santé"]],"Port Louis","1.3M","Left","Type C/G · 230V"),
 "Seychelles": ("SC","SCR","Seychellois rupee (₨)","Creole / English / French","Grilled fish & octopus curry",
   [["Hello","Bonzour"],["Thank you","Mersi"],["Cheers","Santé"]],"Victoria","100K","Left","Type G · 240V"),
 "Comoros": ("KM","KMF","Comorian franc (CF)","Comorian / Arabic / French","Langouste à la vanille",
   [["Hello","Bariza"],["Thank you","Marahaba"],["Cheers","Santé"]],"Moroni","850K","Right","Type C/E · 220V"),
 "Malawi": ("MW","MWK","Malawian kwacha (MK)","Chichewa / English","Nsima & chambo",
   [["Hello","Moni"],["Thank you","Zikomo"],["Cheers","Cheers"]],"Lilongwe","21M","Left","Type G · 230V"),
 "Mozambique": ("MZ","MZN","Mozambican metical (MT)","Portuguese","Peri-peri prawns & matapa",
   [["Hello","Olá"],["Thank you","Obrigado"],["Cheers","Saúde"]],"Maputo","33M","Left","Type C/F/M · 220V"),
 "Zambia": ("ZM","ZMW","Zambian kwacha (K)","English / Bemba / Nyanja","Nshima & kapenta",
   [["Hello","Muli bwanji"],["Thank you","Zikomo"],["Cheers","Cheers"]],"Lusaka","20M","Left","Type C/D/G · 230V"),
 "Botswana": ("BW","BWP","Botswana pula (P)","Setswana / English","Seswaa & bogobe",
   [["Hello","Dumela"],["Thank you","Ke a leboga"],["Cheers","Cheers"]],"Gaborone","2.7M","Left","Type D/G/M · 230V"),
 "Lesotho": ("LS","LSL","Lesotho loti (L)","Sesotho / English","Papa & moroho",
   [["Hello","Lumela"],["Thank you","Kea leboha"],["Cheers","Cheers"]],"Maseru","2.3M","Left","Type M · 220V"),
 "Eswatini": ("SZ","SZL","Swazi lilangeni (L)","siSwati / English","Sishwala & emasi",
   [["Hello","Sawubona"],["Thank you","Ngiyabonga"],["Cheers","Cheers"]],"Mbabane","1.2M","Left","Type M · 230V"),
 # ---------- Oceania ----------
 "Australia": ("AU","AUD","Australian dollar (A$)","English","Meat pie, barramundi & Vegemite",
   [["Hello","G'day"],["Thank you","Thanks / Ta"],["Cheers","Cheers"]],"Canberra","26M","Left","Type I · 230V"),
 "New Zealand": ("NZ","NZD","New Zealand dollar (NZ$)","English / Māori","Hāngī & pavlova",
   [["Hello","Kia ora"],["Thank you","Ngā mihi"],["Cheers","Cheers"]],"Wellington","5.2M","Left","Type I · 230V"),
 # ---------- Latin America ----------
 "Argentina": ("AR","ARS","Argentine peso ($)","Spanish","Asado & empanadas",
   [["Hello","Hola"],["Thank you","Gracias"],["Cheers","Salud"]],"Buenos Aires","46M","Right","Type C/I · 220V"),
 "Bolivia": ("BO","BOB","Bolivian boliviano (Bs)","Spanish / Quechua / Aymara","Salteñas & silpancho",
   [["Hello","Hola"],["Thank you","Gracias"],["Cheers","Salud"]],"Sucre","12M","Right","Type A/C · 230V"),
 "Colombia": ("CO","COP","Colombian peso ($)","Spanish","Bandeja paisa & arepas",
   [["Hello","Hola"],["Thank you","Gracias"],["Cheers","Salud"]],"Bogotá","52M","Right","Type A/B · 110V"),
 "Uruguay": ("UY","UYU","Uruguayan peso ($U)","Spanish","Asado & chivito",
   [["Hello","Hola"],["Thank you","Gracias"],["Cheers","Salud"]],"Montevideo","3.4M","Right","Type C/F/L · 230V"),
 "Paraguay": ("PY","PYG","Paraguayan guaraní (₲)","Spanish / Guaraní","Sopa paraguaya & chipá",
   [["Hello","Mba'éichapa"],["Thank you","Aguyje"],["Cheers","Salud"]],"Asunción","6.9M","Right","Type C · 220V"),
 "Cuba": ("CU","CUP","Cuban peso ($)","Spanish","Ropa vieja & moros y cristianos",
   [["Hello","Hola"],["Thank you","Gracias"],["Cheers","Salud"]],"Havana","11M","Right","Type A/B/C · 110/220V"),
 "Costa Rica": ("CR","CRC","Costa Rican colón (₡)","Spanish","Gallo pinto & casado",
   [["Hello","Hola / Pura vida"],["Thank you","Gracias"],["Cheers","Salud"]],"San José","5.2M","Right","Type A/B · 120V"),
 "Belize": ("BZ","BZD","Belize dollar (BZ$)","English / Kriol","Rice & beans, stew chicken",
   [["Hello","Hello"],["Thank you","Thank you"],["Cheers","Cheers"]],"Belmopan","410K","Right","Type A/B/G · 110/220V"),
 # ---------- New Europe ----------
 "Ukraine": ("UA","UAH","Ukrainian hryvnia (₴)","Ukrainian","Borscht & varenyky",
   [["Hello","Привіт (Pryvit)"],["Thank you","Дякую (Diakuyu)"],["Cheers","Будьмо (Budmo)"]],"Kyiv","38M","Right","Type C/F · 230V"),
 "Serbia": ("RS","RSD","Serbian dinar (дин)","Serbian","Ćevapi & pljeskavica",
   [["Hello","Здраво (Zdravo)"],["Thank you","Хвала (Hvala)"],["Cheers","Живели (Živeli)"]],"Belgrade","6.6M","Right","Type C/F · 230V"),
 "Luxembourg": ("LU","EUR","Euro (€)","Luxembourgish / French / German","Judd mat Gaardebounen",
   [["Hello","Moien"],["Thank you","Merci"],["Cheers","Prost / Santé"]],"Luxembourg City","660K","Right","Type C/F · 230V"),
 "Lithuania": ("LT","EUR","Euro (€)","Lithuanian","Cepelinai & šaltibarščiai",
   [["Hello","Labas"],["Thank you","Ačiū"],["Cheers","Į sveikatą"]],"Vilnius","2.9M","Right","Type C/F · 230V"),
 "Latvia": ("LV","EUR","Euro (€)","Latvian","Grey peas & speck",
   [["Hello","Sveiki"],["Thank you","Paldies"],["Cheers","Priekā"]],"Riga","1.9M","Right","Type C/F · 230V"),
 "Moldova": ("MD","MDL","Moldovan leu (L)","Romanian","Mămăligă & sarmale",
   [["Hello","Bună"],["Thank you","Mulțumesc"],["Cheers","Noroc"]],"Chișinău","2.6M","Right","Type C/F · 230V"),
 "Slovakia": ("SK","EUR","Euro (€)","Slovak","Bryndzové halušky",
   [["Hello","Ahoj"],["Thank you","Ďakujem"],["Cheers","Na zdravie"]],"Bratislava","5.4M","Right","Type C/E · 230V"),
 "Slovenia": ("SI","EUR","Euro (€)","Slovene","Potica & štruklji",
   [["Hello","Živjo"],["Thank you","Hvala"],["Cheers","Na zdravje"]],"Ljubljana","2.1M","Right","Type C/F · 230V"),
 "Vatican City": ("VA","EUR","Euro (€)","Italian / Latin","Roman pasta — cacio e pepe",
   [["Hello","Buongiorno"],["Thank you","Grazie"],["Cheers","Salute"]],"Vatican City","800","Right","Type C/F/L · 230V"),
 "Russia": ("RU","RUB","Russian ruble (₽)","Russian","Borscht, pelmeni & blini",
   [["Hello","Привет (Privet)"],["Thank you","Спасибо (Spasibo)"],["Cheers","На здоровье (Na zdorovie)"]],"Moscow","144M","Right","Type C/F · 230V"),
 # ---------- Gaps left by the Eurasia / Latin America batches (found 2026-08-17) ----------
 # These 13 were in the country registry and had places on the map, but never got
 # culture rows — so 59 location pages rendered em-dashes, no radio and no currency
 # converter. Nothing to do with Africa; caught by auditing the registry against
 # all four tables, which is worth re-running after ANY region batch.
 "Belarus": ("BY","BYN","Belarusian ruble (Br)","Belarusian / Russian","Draniki & machanka",
   [["Hello","Прывітанне (Pryvitannie)"],["Thank you","Дзякуй (Dziakuj)"],["Cheers","Будзьма (Budzma)"]],"Minsk","9.2M","Right","Type C/F · 230V"),
 "Brunei": ("BN","BND","Brunei dollar (B$)","Malay","Ambuyat & nasi katok",
   [["Hello","Salam"],["Thank you","Terima kasih"],["Cheers","Cheers"]],"Bandar Seri Begawan","460K","Left","Type G · 240V"),
 "Myanmar": ("MM","MMK","Myanmar kyat (K)","Burmese","Mohinga & tea leaf salad",
   [["Hello","မင်္ဂလာပါ (Mingalaba)"],["Thank you","ကျေးဇူးတင်ပါတယ် (Kyay zu tin ba de)"],["Cheers","Aung myin par say"]],"Naypyidaw","54M","Right","Type C/D/G · 230V"),
 "Kazakhstan": ("KZ","KZT","Kazakhstani tenge (₸)","Kazakh / Russian","Beshbarmak & baursak",
   [["Hello","Сәлеметсіз бе (Sälemetsiz be)"],["Thank you","Рахмет (Rakhmet)"],["Cheers","Сау болыңыз (Sau bolyñyz)"]],"Astana","20M","Right","Type C/F · 220V"),
 "Uzbekistan": ("UZ","UZS","Uzbekistani so'm (so'm)","Uzbek / Russian","Plov & samsa",
   [["Hello","Salom"],["Thank you","Rahmat"],["Cheers","Olqishlar"]],"Tashkent","36M","Right","Type C/F · 220V"),
 "Kyrgyzstan": ("KG","KGS","Kyrgyzstani som (с)","Kyrgyz / Russian","Beshbarmak & laghman",
   [["Hello","Салам (Salam)"],["Thank you","Рахмат (Rakhmat)"],["Cheers","Den sooluk"]],"Bishkek","7.0M","Right","Type C/F · 220V"),
 "Tajikistan": ("TJ","TJS","Tajikistani somoni (SM)","Tajik / Russian","Qurutob & plov",
   [["Hello","Салом (Salom)"],["Thank you","Раҳмат (Rahmat)"],["Cheers","Ba salomati"]],"Dushanbe","10M","Right","Type C/F · 220V"),
 "Turkmenistan": ("TM","TMT","Turkmenistani manat (m)","Turkmen / Russian","Plov & shashlik",
   [["Hello","Salam"],["Thank you","Sag boluň"],["Cheers","Saglygyňyza"]],"Ashgabat","6.5M","Right","Type C/F · 220V"),
 "Timor-Leste": ("TL","USD","US dollar ($)","Tetum / Portuguese","Ikan sabuko & batar daan",
   [["Hello","Bondia"],["Thank you","Obrigadu"],["Cheers","Saúde"]],"Dili","1.4M","Left","Type C/E/F/I · 220V"),
 "Ecuador": ("EC","USD","US dollar ($)","Spanish / Quechua","Ceviche & llapingachos",
   [["Hello","Hola"],["Thank you","Gracias"],["Cheers","Salud"]],"Quito","18M","Right","Type A/B · 120V"),
 "Venezuela": ("VE","VES","Venezuelan bolívar (Bs)","Spanish","Arepas & pabellón criollo",
   [["Hello","Hola"],["Thank you","Gracias"],["Cheers","Salud"]],"Caracas","28M","Right","Type A/B · 120V"),
 "Guyana": ("GY","GYD","Guyanese dollar (G$)","English / Creole","Pepperpot & cook-up rice",
   [["Hello","Hello"],["Thank you","Thank you"],["Cheers","Cheers"]],"Georgetown","810K","Left","Type A/B/D/G · 240V"),
 "Suriname": ("SR","SRD","Surinamese dollar (SRD)","Dutch / Sranan Tongo","Roti & pom",
   [["Hello","Hallo / Fa waka"],["Thank you","Dank u / Grantangi"],["Cheers","Proost"]],"Paramaribo","620K","Left","Type C/F · 127V"),
}


def esc(s):
    """Everything we emit lands inside a single-quoted JS string, so an
    apostrophe in the DATA closes it early and breaks the whole file. There are
    real ones here — Côte d'Ivoire, N'Djamena — so escape every field, not just
    the ones that happen to need it today."""
    return str(s).replace("\\", "\\\\").replace("'", "\\'")


def _phr(phrases):
    return "[" + ",".join("['" + esc(a) + "','" + esc(b) + "']" for a, b in phrases) + "]"


def block_for(table):
    lines = [BEGIN]
    for c, (code, ccy, ccyl, lang, dish, phrases, cap, pop, drives, plug) in ROWS.items():
        k = "'" + esc(c) + "'"
        if table == "COUNTRY_PROFILES":
            lines.append(f"  {k}: {{ lang: '{esc(lang)}', currency: '{esc(ccyl)}', "
                         f"dish: '{esc(dish)}', phrases: {_phr(phrases)} }},")
        elif table == "COUNTRY_CODES":
            lines.append(f"  {k}:'{esc(code)}',")
        elif table == "CURRENCY_CODES":
            lines.append(f"  {k}:'{esc(ccy)}',")
        elif table == "COUNTRY_FACTS":
            lines.append(f"  {k}:{{capital:'{esc(cap)}',pop:'{esc(pop)}',"
                         f"drives:'{esc(drives)}',plug:'{esc(plug)}'}},")
    lines.append(END)
    return "\n".join(lines)


def check_no_orphans(src):
    """Refuse to run if the live marked block holds a country ROWS has never
    heard of. Without this, the wholesale replace below quietly deletes it —
    which is exactly how DR Congo, Namibia, North Korea and Zimbabwe went
    missing. Loud failure beats a silent regression in a data file nobody
    diffs closely."""
    orphans = set()
    for table in TABLES:
        m = re.search(r"const %s = \{(.*?)\n\};" % table, src, re.S)
        if not m:
            continue
        blk = re.search(re.escape(BEGIN) + r"(.*?)" + re.escape(END), m.group(1), re.S)
        if not blk:
            continue
        for key in re.findall(r"^\s*'((?:[^'\\]|\\.)*)'\s*:", blk.group(1), re.M):
            if key.replace("\\'", "'") not in ROWS:
                orphans.add(key)
    if orphans:
        print("✗ refusing to write — these countries are in culture.js but not in ROWS,\n"
              "  so this run would DELETE them. Copy them into ROWS first:", file=sys.stderr)
        for o in sorted(orphans):
            print(f"    - {o}", file=sys.stderr)
        sys.exit(1)


def patch_table(src, table):
    # remove any prior marked block inside this table first
    decl = f"const {table} = {{"
    start = src.index(decl)
    close = src.index("\n};", start)
    body = src[start:close]
    body = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", "", body, flags=re.S)
    # ensure the last real entry ends with a comma before we append our block
    trimmed = body.rstrip()
    if not trimmed.endswith(",") and not trimmed.endswith("{"):
        trimmed += ","
    new_body = trimmed + "\n" + block_for(table) + "\n"
    return src[:start] + new_body + src[close:]


def main():
    with open(CULT, encoding="utf-8") as f:
        src = f.read()
    check_no_orphans(src)
    for table in TABLES:
        src = patch_table(src, table)
    with open(CULT, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"✓ patched js/lib/culture.js — {len(ROWS)} countries across 4 tables "
          f"({', '.join(TABLES)})")


if __name__ == "__main__":
    main()
