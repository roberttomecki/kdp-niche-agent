# Crochet Pattern Notebook – 8,5 × 11" (KDP paperback) · seria **Golden Stitch** #1

Nisza z obserwacji agenta (`/nisze`, 27.11.2026): **crochet pattern notebook** – ✅ „sprzedaje się regularnie”,
5/10 książek z topu sprzedało w 3 dni, sprzedają też słabe pozycje z 1–2 opiniami (Crocheting Log Book,
The Crochet Pattern Notebook). Temat bez daty (cały rok) + prezenty świąteczne dla osób szydełkujących.
Ten sam temat wyszedł pośrednio w „quilting planner 2027” (sprzedają tam planery szydełkowe).

Pierwsza książka serii **Golden Stitch Notebooks** – okładka z algorytmu generatywnego (spirala Fibonacciego
z oczek łańcuszka), opis algorytmu: `series/golden-stitch/PHILOSOPHY.md`.

## Generowanie

```bash
pip install reportlab pillow playwright pdfplumber pypdf
python make_interior.py                          # output/…_interior.pdf (106 stron)
python cover/make_cover.py --pages 106 --seed 1  # output/…_cover.pdf (17,4887 × 11,25", grzbiet 0,2387")
python marketing/make_marketing.py               # output/marketing/ – A+, mockupy, piny
python ../../series/golden-stitch/check_pdf.py output/crochet-pattern-notebook_8.5x11_interior.pdf \
       --gutter 0.625 --outer 0.5 --top 0.5 --bottom 0.5    # 0 elementów poza marginesami, fonty osadzone
```
Okładka: `--seed N` daje inną spiralę tej samej rodziny. Do przeglądania seedów i palet:
`series/golden-stitch/viewer.html` (otwórz w przeglądarce).

**Wnętrze (106 stron):** strona tytułowa z emblematem spirali, jak korzystać, skróty US/UK (22 pozycje),
tabele rozmiarów szydełek i grubości włóczki, moje szydełka, zapas włóczki (2 str.), spis projektów (2 str.),
**40 rozkładówek projektów** (lewa: karta projektu – wzór, źródło, dla kogo, daty, poziom, 3 włóczki z partią
barwienia, szydełko, rozmiar, próbka i gęstość, ściegi, akcesoria, miejsce na zdjęcie/etykietę, notatki, ocena;
prawa: licznik rzędów 1–60 do odhaczania + 24 wiersze instrukcji + wykończenie), 10 stron papieru w kratkę
(0,2", co 5 pogrubione), wzory do zrobienia (2), dziennik prezentów (2), notatki (3).
Kroje: Fraunces + Jost (OFL, `series/golden-stitch/fonts`). Marginesy: grzbiet 0,625", reszta 0,5".

**Okładka:** śliwkowe tło (#2a1730) z jaskrawą spiralą przędzy (bursztyn, koral, krem, morski), kremowy pas
tytułu o wysokości 11"/φ² ≈ 4,2", łańcuszek na granicy. Środek spirali w złotym punkcie przodu.
Grzbiet bez tekstu (0,2387"). Prawy dolny róg tyłu wolny na kod kreskowy KDP.
Wyróżnik: konkurencja to głównie pastelowe okładki z kłębkami – ciemna okładka ze świecącą spiralą
jest widoczna na liście wyników; tytuł czytelny w miniaturze 160 px (`output/…_thumb160.png`).

## Ustawienia w KDP

- **Language:** English. **Low-content book:** TAK. **Large-print book:** NIE
- **Author:** Robert Tomecki. **Series:** BRAK – KDP nie dopuszcza książek low-content do serii (odrzucenie serii 27.11.2026). Marka „Golden Stitch Notebooks” zostaje tylko na okładce i w A+.
- **ISBN:** Publish without an ISBN
- **Ink and paper:** Black & white interior, white paper
- **Trim size:** 8.5 x 11 in. **Bleed:** **No Bleed** (wnętrze). **Cover finish:** **Matte**
- **AI-generated content:** Yes – tekst (Claude) i obrazy (okładka generowana kodem napisanym przez AI)
- **Cena:** **9,99 $**. Druk około 2,27 $ (1,00 $ + 106 × 0,012 $), tantiemy około **3,72 $**
- Po wgraniu sprawdź całość w Previewerze

## Listing

**Title:** Crochet Pattern Notebook
**Subtitle:** Crochet Journal and Project Log Book with Row Counter, Gauge, Yarn and Hook Tracker, US/UK Abbreviations and Graph Paper for 40 Projects

**Description:**
```
You finished the blanket. Six months later someone asks for one in blue, and you cannot remember the hook, the yarn or what you changed in round 14. This notebook keeps all of it, so every pattern you love can be made again.

Inside:
• 40 two-page project spreads: a project card on the left, a row and round tracker on the right
• Project card: pattern and source, made for, start and finish dates, skill level, up to 3 yarns with colour and dye lot, hook size, pattern gauge and your gauge, finished size, stitches used, notions, a box for a photo, yarn label or swatch, notes and a 5-star rating
• Tick-off row counter for rows 1–60 and 24 lines of instructions with stitch counts
• US and UK stitch abbreviations side by side, hook size chart and yarn weight chart
• My hooks, yarn stash inventory and a project index
• 10 pages of chart paper for tapestry, mosaic, C2C and filet crochet
• Patterns to try and a gift log to remember who received what you made

8.5 x 11 inches, 106 pages, matte paperback with plenty of room to write.

A thoughtful gift for crocheters, from beginners making their first granny square to amigurumi and blanket makers.
```

**Słowa kluczowe (7 pól, bez słów z tytułu):**
1. crochet journal project planner
2. gifts for crocheters women mom grandma
3. crochet log book row counter
4. yarn stash organizer tracker
5. crochet graph paper tapestry chart
6. amigurumi granny square blanket notes
7. knitting and crochet record keeper

**Kategorie (3):**
1. Crafts, Hobbies & Home → Crafts & Hobbies → Needlecrafts & Textile Crafts → Crocheting
2. Crafts, Hobbies & Home → Crafts & Hobbies → Needlecrafts & Textile Crafts → Knitting (albo Needlework)
3. Self-Help → Journal Writing

## Marketing (zasada: przy każdej książce)

Wszystko w `output/marketing/` (generuje `marketing/make_marketing.py`, ten sam algorytm co okładka).

| Plik | Gdzie użyć |
|---|---|
| `aplus_1_header_1940x1200.jpg` | A+ moduł **Standard Image Header With Text** (970 × 600) |
| `aplus_2a/2b/2c_square_1200.jpg` | A+ moduł **Standard Three Images & Text** (3 kwadraty) |
| `aplus_3_banner_1940x600.jpg` | A+ moduł **Standard Image & Dark Text Overlay** (970 × 300) |
| `mockup_cover_2000.jpg` | Author Central, social media, sklep |
| `mockup_spread_2400x1600.jpg` | „Look inside” w social media, A+ (opcjonalnie) |
| `pin_1/2/3_1000x1500.jpg` | Pinterest (2:3) |

**A+ Content** (KDP → Marketing → A+ Content Manager → Start creating): moduły w kolejności nagłówek,
trzy kwadraty, baner. Teksty do modułu z trzema obrazami (pod kwadratami):
- *Project card* – Pattern source, yarn and dye lot, hook, gauge, size and stitches, all in one place.
- *Row counter* – Tick off rows 1–60 as you go, with 24 lines of instructions per project.
- *Quick reference* – US/UK abbreviations, hook sizes, yarn weights and 10 pages of chart paper.
Alt-tekst: „Crochet Pattern Notebook project card page”, „row counter page”, „crochet abbreviations page”.
Przypisz A+ do ASIN-u po publikacji. Ten sam układ można dać kolejnym książkom serii.

**Pinterest** (konto firmowe, tablica „Crochet Journal & Pattern Keeping”, link do `amazon.com/dp/ASIN`):
1. *Never lose a crochet pattern again* – „Write down the hook, yarn, gauge and every row you changed. A crochet pattern notebook with 40 project spreads and a tick-off row counter. #crochet #crochetjournal #crochetgift”
2. *Look inside: 40 crochet project spreads* – „Project card on the left, row counter on the right. 8.5 × 11 crochet log book with yarn stash, hook chart and graph paper. #crochetersofinstagram #crochetpattern”
3. *US or UK crochet terms?* – „Both are inside, side by side – plus hook sizes and yarn weights. A handy reference for every crocheter. #crochettips #learntocrochet”
Publikuj po jednym pinie co 2–3 dni; najlepiej przed świętami (prezent).

**Amazon Ads (opcjonalnie, po publikacji):** kampania Sponsored Products **automatyczna**, 3–5 $/dzień,
14 dni, stawka domyślna. Po 2 tygodniach z raportu wyszukiwanych fraz przenieś frazy ze sprzedażą do
kampanii ręcznej, a frazy z kliknięciami bez sprzedaży dodaj jako negatywne.

**Po publikacji:** w Telegramie `/dodaj ASIN Crochet Pattern Notebook`; Author Central – dodaj książkę (bez serii).
