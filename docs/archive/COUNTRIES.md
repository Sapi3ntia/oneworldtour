# 🗺️ Country Coverage & Expansion Backlog

> ### ✅ STATUS: PARITY SHIPPED (2026-06-29)
> The backlog below has been **executed**. One World Tour went **39 → 89 countries**
> and **191 → 345 locations** — all 50 "to be added" countries now have
> coordinate-verified destinations on the map, built on the new country-first data
> model. The country lists in §2–§4 are kept as the historical analysis + record of
> what was added. Per-country location counts and the live registry are in
> `data/countries.json`; see `OVERHAUL.md` for the architecture and what's still open
> (windows/walks/culture-review for the new countries).

> Working artifact created 2026-06-29. Purpose: a single source of truth for
> **which countries One World Tour covers today** vs. **which the reference
> competitor (virtualvacation.us) covers**, and a prioritized **"to be added"**
> backlog as the starting point for the world-coverage overhaul.
>
> Companion doc: [`OVERHAUL.md`](OVERHAUL.md) — the architecture proposal + issues log.
> The raw machine-readable extracts live in the session scratchpad
> (`extracted.json`, `country_diff.json`) — regenerate any time with the curl+node
> recipe in `OVERHAUL.md` §"How this was gathered".

---

## 1. What I actually visited (browser extension was offline → curl fallback)

The `claude-in-chrome` extension wasn't connected, so — per the HANDOFF §7 recipe — I
pulled raw HTML with `curl` and parsed the inline JS data arrays. Three requested pages
plus `/videarth` (the only page that names **countries**):

| Page | What it is | Data shape in source | Names countries? |
|---|---|---|---|
| `/` (home) | Landing + mode cards. Nav = the full feature set: `explore`, `videarth`, `window`, `livecam`, `walk`, `fly`, `driver`, `roadtrip`, `guess`, `monument`, `our-mission` | — | no |
| `/livecam` | Grid of live YouTube cams | `var location_lst = ['<ytid>', …]` — **30** cam IDs, **no place names in source** (titles resolved from YouTube at runtime) | no |
| `/window` | "Open a window" — single shared YT player, recorded clips seeked + looped | `var locations = [['City','<ytid>?start=ssssss'], …]` — **117** entries, **city-level only** | no (cities, not countries) |
| `/videarth` | Click-a-map-point → video. ~1,000 dots over Esri satellite | `var countriesAndCities = [['City','Country','Region'], …]` (**985** points, **496** cities) + parallel `vidids` | **YES — authoritative** |

**Key finding (confirms HANDOFF §7):** none of these are live. `/window` and `/videarth`
are recorded YouTube videos seeked to a `?start=` offset and looped. `/livecam` is the one
that's actually live-ish (real cam streams). Country naming only exists on `/videarth`.

---

## 2. The master list — every country named on virtualvacation.us (84)

Source: `/videarth`'s `countriesAndCities` (uses ISO-3166 official labels). Number = how
many of their ~985 video points sit in that country (a rough popularity/priority signal).

```
214 United States      18 Thailand           5 Iceland             3 Croatia
 62 United Kingdom      18 Malaysia           5 Norway              3 New Zealand
 42 France              15 Netherlands        5 Hungary             3 Chile
 42 Japan               14 Turkey             5 Israel              3 Bolivia*
 38 Canada              13 Ireland            5 UAE                  2 Slovakia
 37 Australia           11 Mexico             5 Cambodia            2 Latvia
 34 Germany             11 South Korea*        4 Serbia              2 Moldova*
 33 Russia*             10 Sweden             4 Cyprus              2 Uruguay
 32 China                9 Indonesia          4 Vietnam*            2 Iran*
 29 Brazil               9 Poland             4 Armenia             2 Mongolia
 29 India                9 Austria            3 Vatican*            2 Georgia
 24 Argentina            9 Switzerland        3 Estonia             2 Saudi Arabia
 22 Italy                8 Greece             3 Luxembourg          2 Kenya
 20 Spain                8 Ukraine            3 Cuba                2 Senegal
                         7 Belgium            3 Costa Rica          2 Ethiopia
                         7 Philippines        3 Colombia            2 Gambia
                         6 Peru               3 Portugal            2 Paraguay
                         6 Finland            3 Malta               1 Egypt, Belize, Denmark,
                         5 Singapore          3 Lithuania             Gibraltar*, Laos*, Taiwan*,
                         5 Bulgaria           3 Morocco               Qatar, Sri Lanka, Slovenia,
                                                                      Azerbaijan, Jordan, South Africa
```
`*` = label normalized from ISO form: Russia←Russian Federation, South Korea←Korea Republic of,
Vietnam←Viet Nam, Vatican←Holy See, Bolivia←…Plurinational State, Iran←…Islamic Republic,
Moldova←…Republic of, Laos←Lao PDR, Taiwan←…Province of China. **Gibraltar** is a UK territory
(we fold it into UK).

---

## 3. What WE cover today (39 countries, 191 locations)

Grouped by continent (raw label counts in `OVERHAUL.md` §issues — note the England/UK split):

| Continent | Countries (count = our locations) |
|---|---|
| **North America** (4) | USA(56*), Canada(17), Mexico(5), Bahamas(1) |
| **South America** (3) | Brazil(2), Peru(2), Chile(1) |
| **Europe** (29) | UK(7 — labeled England×5 + United Kingdom×2), France(9), Germany(9), Italy(12), Spain(10), Portugal(8), Netherlands(4), Belgium(2), Austria(4), Switzerland(3), Greece(3), Ireland(1), Sweden(1), Norway(3), Finland(2), Denmark(1), Iceland(1), Poland(1), Hungary(1), Czech Republic(2), Bulgaria(1), Cyprus(1), Estonia(1), Croatia(2), Romania(2), Montenegro(2), Bosnia & Herzegovina(1), Albania(1), **Faroe Islands(1)†** |
| **Asia** (2) | Turkey(6), Indonesia(1) |
| **Oceania** (1) | Micronesia(1) |

`*` USA 56 = 50 modern + 6 Ancient-Apocalypse US sites. †Faroe Islands is a Danish territory —
counted separately today (a data-hygiene call to make; see `OVERHAUL.md`).

**6 countries we have that virtualvacation does NOT** (our genuine edge — keep them):
`Albania, Bahamas, Bosnia and Herzegovina, Micronesia, Montenegro, Romania`.

---

## 4. ⭐ TO BE ADDED — the backlog (50 countries on virtualvacation, not in ours)

Ordered within each continent by their videarth weight `(N)` = rough priority. The big,
obvious gaps are at the top of each list.

### Tier 1 — high-impact, globally iconic (do first)
`Japan(42)`, `Australia(37)`, `Russia(33)`, `China(32)`, `India(29)`, `Argentina(24)`,
`Thailand(18)`, `Malaysia(18)`, `South Korea(11)`.
→ These 9 single-handedly close most of the "feels US/Euro-centric" gap.

### Full backlog by continent

| Continent | To add (N = their videarth points) |
|---|---|
| **Asia** (23) | Japan(42), China(32), India(29), Thailand(18), Malaysia(18), South Korea(11), Philippines(7), Singapore(5), Israel(5), UAE(5), Cambodia(5), Vietnam(4), Armenia(4), Georgia(2), Iran(2), Mongolia(2), Saudi Arabia(2), Azerbaijan(1), Jordan(1), Laos(1), Qatar(1), Sri Lanka(1), Taiwan(1) |
| **Europe** (9) | Ukraine(8), Serbia(4), Vatican(3), Lithuania(3), Luxembourg(3), Latvia(2), Moldova(2), Slovakia(2), Slovenia(1) |
| **Africa** (7) | Morocco(3), Ethiopia(2), Gambia(2), Kenya(2), Senegal(2), Egypt(1), South Africa(1) |
| **South America** (5) | Argentina(24), Bolivia(3), Colombia(3), Uruguay(2), Paraguay(2) |
| **North America** (3) | Cuba(3), Costa Rica(3), Belize(1) |
| **Oceania** (2) | Australia(37), New Zealand(3) |
| **Eurasia** (1) | Russia(33) |

**Net effect if fully closed:** 39 → ~89 countries; continents go from Euro/N-America-heavy
to genuinely global (adds real Asia/Africa/Oceania/S-America breadth).

### Beyond parity (where we can beat them)
virtualvacation tops out at 84 countries. Obvious missing-from-both countries worth adding so
we *exceed* them: Vietnam neighbors aside — e.g. **Nigeria, Tanzania, Ghana, Nepal, Pakistan,
Bangladesh, Kazakhstan, Greenland, Fiji, Vanuatu** — but parity first; this is a later pass.

---

## 5. Naming normalization (decisions baked into the diff above)

To compare the two sets cleanly I canonicalized labels. These same rules should drive the new
country registry so we never repeat the England/UK mess:

- `England / Scotland / Wales / Gibraltar` → **United Kingdom** (one country, regions as a sub-field)
- ISO long-forms → common name: Russian Federation→Russia, Korea Republic of→South Korea,
  Viet Nam→Vietnam, Holy See→Vatican, Lao PDR→Laos, Taiwan Province of China→Taiwan,
  …Plurinational/Islamic Republic/Republic of → Bolivia/Iran/Moldova, Czechia→Czech Republic.
- Territories: Faroe Islands (DK), Gibraltar (UK) — decide whether to surface as their own
  pin-country or fold into the sovereign state. Recommendation in `OVERHAUL.md`.
