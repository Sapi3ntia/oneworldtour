#!/usr/bin/env python3
"""
build_culture.py — extend js/culture.js's four lookup tables to cover the 50
world-expansion countries (COUNTRIES.md), so the location-page culture panel +
the live currency converter work for every country, not just the original 39.

Patches js/culture.js IN PLACE, inserting a clearly-marked block before each
table's closing brace. Idempotent: re-running replaces the marked block.

Confidence note (be honest): ISO codes, currency codes, and capitals are
factual. Languages and capitals likewise. `dish` is editorial. `phrases`
(greetings) are best-effort — native scripts where confident, romanized where
the script is error-prone — and DESERVE A NATIVE-SPEAKER REVIEW PASS before being
treated as authoritative (logged in OVERHAUL.md §4).

Run:  python3 tools/build_culture.py
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CULT = os.path.join(HERE, "..", "js", "culture.js")
BEGIN = "  /* === world-expansion countries (build_culture.py) — review phrases/dishes === */"
END = "  /* === end world-expansion === */"

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
}


def _phr(phrases):
    return "[" + ",".join("['" + a.replace("'", "\\'") + "','" + b.replace("'", "\\'") + "']"
                          for a, b in phrases) + "]"


def block_for(table):
    lines = [BEGIN]
    for c, (code, ccy, ccyl, lang, dish, phrases, cap, pop, drives, plug) in ROWS.items():
        k = "'" + c + "'"
        if table == "COUNTRY_PROFILES":
            lines.append(f"  {k}: {{ lang: '{lang}', currency: '{ccyl}', dish: '{dish}', phrases: {_phr(phrases)} }},")
        elif table == "COUNTRY_CODES":
            lines.append(f"  {k}:'{code}',")
        elif table == "CURRENCY_CODES":
            lines.append(f"  {k}:'{ccy}',")
        elif table == "COUNTRY_FACTS":
            lines.append(f"  {k}:{{capital:'{cap}',pop:'{pop}',drives:'{drives}',plug:'{plug}'}},")
    lines.append(END)
    return "\n".join(lines)


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
    for table in ("COUNTRY_PROFILES", "COUNTRY_CODES", "CURRENCY_CODES", "COUNTRY_FACTS"):
        src = patch_table(src, table)
    with open(CULT, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"✓ patched js/culture.js — +{len(ROWS)} countries across 4 tables "
          f"(COUNTRY_PROFILES, COUNTRY_CODES, CURRENCY_CODES, COUNTRY_FACTS)")


if __name__ == "__main__":
    main()
