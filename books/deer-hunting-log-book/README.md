# Deer Hunting Log Book – 6 × 9" (KDP paperback)

Nisza z raportu agenta (23.11.2026): **„hunting journal”**. Prawdziwe dzienniki myśliwskie mają BSR
100–280 tys. (około 0,4–1 szt./dzień), a książki z 1–4 opiniami też się sprzedają (BSR 206–278 tys.).
Wysoki wynik „2000+ kupionych/mies.” pochodził od notesu „Kpop Demon Hunters” i był błędny. Od teraz
agent liczy odznaki tylko dla produktów pasujących do frazy.
Termin: sezon na jelenie trwa do stycznia, prezenty świąteczne. Celem jest sprzedaż do około 5.12.

## Generowanie

```bash
pip install reportlab numpy matplotlib
python make_interior.py --author "Robert Tomecki"   # output/deer-hunting-log-book_6x9_interior.pdf (110 stron)
python cover/make_cover.py --pages 110              # output/deer-hunting-log-book_6x9_cover.pdf (12,498 × 9,25")
python cover/make_cover.py --pages 110 --variant orange   # wariant pomarańczowy: …_cover_orange.pdf
```

**Wnętrze (110 stron):** strona tytułowa, prawa autorskie i uwaga o przepisach łowieckich, instrukcja
z kluczem faz księżyca, dane myśliwego i licencji z datami sezonów (łuk, kusza, muzzleloader, broń palna,
młodzież), lista sprzętu z polami wyboru (24 pozycje plus puste), 2 strony stanowisk (6 stanowisk:
typ, GPS, wiatr, dojście), 4 strony szkiców terenu (siatka kropek, strzałka północy),
**80 stron polowań** (data, stanowisko, z kim, godziny, broń, róża wiatrów do zakreślenia, temperatura,
prędkość wiatru, niebo z ikonami pogody, ciśnienie, faza księżyca, tabela zaobserwowanych jeleni: byki, łanie, młode,
oddany strzał, odległość, trafienie, wabienie i zapachy, notatki), **8 kart pozyskania** (strzał, lista miejsc trafienia i rysunek jelenia do zaznaczenia trafienia, tropienie,
numer znacznika, poroże L/P, waga, wiek, miejsce na zdjęcie, opis), 4 strony fotopułapek,
2 podsumowania sezonu, notatki.

Ilustracja jelenia (`art/deer.png`, dostarczona przez Roberta, tło wybielone) jest na stronie tytułowej i na kartach pozyskania.

Format bez spadu: marginesy 0,5" od grzbietu, 0,45" na zewnątrz, 0,5" góra i dół. Fonty osadzone.
Sprawdzone skryptem: 0 elementów poza marginesami KDP.

**Okładka:** projekt „Contour Vigil” (`cover/PHILOSOPHY.md`). Na całej okładce mapa poziomic,
na przodzie łańcuch tropów jelenia idący pod górę ku jedynemu pomarańczowemu punktowi, czyli
stanowisku „STAND 3, 06:48, WIND NW 4”, oraz ramka mapy z podziałką. Barwy: ciemna zieleń lasu, kość,
pomarańcz sygnałowy. Kroje (OFL, w `cover/fonts`): National Park (litery z tablic parków narodowych USA),
Jura i DM Mono. Grafika w pełni wektorowa. Grzbiet 0,248" bez tekstu. Prawy dolny róg tyłu jest wolny
na kod kreskowy KDP.

## Ustawienia w KDP

- **Language:** English. **Low-content book:** TAK. **Large-print book:** NIE
- **ISBN:** Publish without an ISBN
- **Ink and paper:** Black & white interior, white paper
- **Trim size:** 6 x 9 in. **Bleed:** **No Bleed**. **Cover finish:** **Matte**
- **AI-generated content:** Yes – teksty i grafika (Claude); jeśli ilustracja jelenia też jest z generatora AI, zaznacz ją w pytaniu o obrazy (Images)
- **Cena:** **9,99 $**. Druk około 2,32 $ (1,00 $ + 110 × 0,012 $), tantiemy około **3,67 $**
- Po wgraniu sprawdź całość w Previewerze

## Opis

**Title:** Deer Hunting Log Book
**Subtitle:** Hunter's Journal to Record Hunts, Weather, Wind, Moon Phase, Deer Sightings, Stands and Harvests, 6 x 9

**Description:**
```
The deer you saw, the wind you sat in, the stand that finally paid off. Write it down while it is fresh, and next season the pattern is yours.

Inside:
- 80 hunt pages: date, stand, time in and out, weapon, a wind compass to circle, temperature, sky, barometer and moon phase
- Deer-seen tables for every sit: time, bucks, does, fawns and where they moved
- Shot records: distance, hit or miss, calls, scent and decoys used
- 8 harvest records with antler measurements, weight, age, tag number and space for a photo
- Stand and blind locations with GPS, best wind and access route
- Trail camera log, 4 dot-grid pages for property maps, and a gear checklist
- Hunter and license information with season dates
- 2 season summaries to compare your results year after year

6 x 9 inches, 110 pages, paperback. Sized to fit in a pack or a truck console.

A practical gift for whitetail hunters, bowhunters and anyone who hunts deer.
```

**Słowa kluczowe (7 pól, bez słów z tytułu):**
1. whitetail season journal notebook
2. bowhunter archery record keeper
3. gifts for hunters men dad husband
4. tree stand trail camera tracker
5. buck antler harvest diary
6. rifle season hunt planner
7. outdoorsman christmas stocking stuffer

**Kategorie (propozycja):** Sports & Outdoors → Hunting & Fishing → Hunting;
Sports & Outdoors → Hunting & Fishing → Hunting → Big Game (jeśli dostępna);
Self-Help → Journal Writing (albo Reference → Personal & Practical Guides).
