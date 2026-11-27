# Mileage Log Book for Taxes – 6 × 9" (KDP paperback)

Nisza wybrana przez agenta (listopad 2026): **„vehicle mileage log book for taxes”** – 4 słabe książki
sprzedają się regularnie, mediana opinii 5,5, 100% wydawców niezależnych. Nowe książki z 0–4 opiniami
sprzedają się przy 9,99–10,99 $; starsze konkurują ceną 5,99–6,99 $ (z tym się nie ścigamy).
Szczyt popytu: sezon podatkowy w USA (styczeń–kwiecień).

## Generowanie

```bash
pip install reportlab playwright
python make_interior.py --author "Imię Nazwisko"   # output/mileage-log-book_6x9_interior.pdf (116 stron)
python make_cover.py --pages 116                   # output/mileage-log-book_6x9_cover.pdf + podgląd PNG
```

**Wnętrze (116 stron):** strona tytułowa (imię, telefon, rok, pojazd), prawa autorskie z zastrzeżeniem
„to nie porada podatkowa”, instrukcja, dane pojazdu (do dwóch aut, licznik 1 stycznia / 31 grudnia),
**100 stron przejazdów × 20 wierszy = 2000 przejazdów** (data, cel/adres, licznik start i koniec, mile,
służbowy/prywatny, sumy strony), 6 stron wydatków (parking, opłaty drogowe, inne koszty), podsumowanie
roczne po miesiącach z udziałem mil służbowych, 4 strony notatek.

Format bez spadu (nic nie dochodzi do krawędzi): marginesy 0,5" od grzbietu, 0,45" na zewnątrz,
0,5" góra/dół. Fonty osadzone. Sprawdzone skryptem: 0 znaków poza marginesami KDP.

**Okładka:** 12,51 × 9,25" (grzbiet ≈ 0,26" bez tekstu), granat drogowskazu z bursztynem, licznik
przebiegu z obracającą się ostatnią cyfrą, ten sam krój co w pierwszej książce. Tekst co najmniej 0,5"
od linii cięcia i grzbietu. Prawy dolny róg tyłu pusty na kod kreskowy KDP.

## Ustawienia w KDP

- **Low-content book:** tak. **Large-print book:** NIE (tabela ma mniejszą czcionkę, żeby zmieścić 20 przejazdów na stronie)
- **ISBN:** Publish without an ISBN
- **Ink and paper:** Black & white, white paper
- **Trim size:** 6 x 9 in
- **Bleed:** **No Bleed**
- **Cover finish:** Matte
- **AI-generated content:** Yes (teksty i grafika – Claude)
- **Cena:** 9,99 $ (próg 60% tantiem)

## Propozycja opisu

**Title:** Mileage Log Book for Taxes
**Subtitle:** Vehicle Mileage Tracker for Business and Personal Driving, with Expense Log and Annual Summary, 6 x 9

**Description:**
```
Keep a simple, complete record of your driving in one book that fits in your glove box.

Inside:
- Room for 2,000 trips: date, destination and purpose, odometer start and end, miles, business or personal
- Page totals for business and personal miles
- An annual summary by month, with your share of business miles
- Pages for parking, tolls and other vehicle costs
- Vehicle details for up to two cars, with odometer readings for January 1 and December 31

6 x 9 inches, 116 pages, paperback.

For self-employed workers, rideshare and delivery drivers, sales reps and anyone who drives for work.
This logbook is a place to record your driving. It is not tax advice.
```

**Słowa kluczowe (7 pól, bez słów z tytułu):**
1. self employed auto expense tracker
2. uber lyft rideshare driver notebook
3. doordash delivery driver record book
4. odometer journal for car
5. irs gas trip record keeping
6. small business vehicle expense ledger
7. realtor sales rep travel diary

**Kategorie (propozycja):** Business & Money → Small Business & Entrepreneurship → Bookkeeping;
Business & Money → Taxation → Small Business; Reference → General.

## A+ Content (27.11.2026)

`python aplus/make_aplus.py` → `output/aplus/` (styl okładki: granat, bursztyn, licznik, droga):
1. `1_header_1940x1200.jpg` – moduł **Standard Image Header With Text**
2. `2a_square_trips`, `2b_square_expenses`, `2c_square_summary` (1200) – moduł **Standard Three Images & Text**
   - *2,000 trips* – Date, destination and purpose, odometer start and end, miles, business or personal.
   - *Expenses* – Six pages for parking, tolls, fuel and repairs, kept next to your mileage.
   - *Annual summary* – Month-by-month business and personal miles on a single page.
3. `3_banner_1940x600.jpg` – moduł **Standard Image & Dark Text Overlay** (bez dodatkowego tekstu)

Alt-teksty: „Mileage log book trip page”, „vehicle expenses page”, „annual mileage summary page”.
Wspólne narzędzia: `tools/aplus_kit.py`, krój Atkinson Hyperlegible Next (`tools/fonts`, OFL).
