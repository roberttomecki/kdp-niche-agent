# Large Print Password Log Book – wnętrze KDP

Nisza wybrana przez agenta (2 tygodnie obserwacji, listopad 2026): **„password log book large print”**.
Nowe książki z 0–3 opiniami sprzedają się tu regularnie, a wydawcy niezależni stanowią ok. 60–70% topu.

## Generowanie

```bash
pip install reportlab
python make_interior.py --all --author "Imię Nazwisko"
```

Wynik w `output/`:

| plik | format | stron | wpisów |
|---|---|---|---|
| `password-log-book_8.5x11_interior.pdf` | 8,5 × 11" (z bleed: 8,625 × 11,25") | 102 | 270 (3 na stronę) |
| `password-log-book_6x9_interior.pdf` | 6 × 9" (z bleed: 6,125 × 9,25") | 102 | 180 (2 na stronę) |

Zawartość: strona tytułowa z polem „This book belongs to”, strona z prawami autorskimi, instrukcja,
wskazówki bezpieczeństwa, strony „Email Accounts” i „Home Internet & Wi-Fi”, sekcje A–Z i „#”
(4 strony na częste litery, 2 na rzadkie), 6 stron „Notes”.
Pola wpisu: Website, Login / Email, Password, 2 × New password, Notes. Czarne zakładki z literą
drukowane na krawędzi tworzą indeks widoczny z boku zamkniętej książki.

Zmiany (liczba stron na literę, pola, wielkość czcionki) – na górze `make_interior.py`
(`SECTIONS`, `FIELDS`, `SPECS`).

## Ustawienia przy publikacji w KDP (Paperback)

- **Ink and paper:** Black & white interior, **white paper**
- **Trim size:** 8.5 x 11 in **albo** 6 x 9 in (każdy format to osobna książka)
- **Bleed:** **Bleed** (zakładki wychodzą do krawędzi)
- **Cover finish:** matte (lepiej wygląda przy prostych okładkach)
- **Manuscript:** odpowiedni plik `*_interior.pdf`
- Po wgraniu obejrzyj całość w **Previewer** – szczególnie zakładki przy krawędzi.

**Okładka:** grzbiet ≈ 102 × 0,002252" ≈ **0,23"** (biały papier). Przy mniej niż 80 stronach KDP
nie pozwala na tekst na grzbiecie, przy 102 stronach jest to dozwolone, ale grzbiet jest wąski –
bezpieczniej zostawić go bez tekstu. Dokładne wymiary okładki: kalkulator/szablon KDP
(Cover Calculator) dla wybranego formatu i 102 stron.

## Propozycja opisu (do dopracowania)

**Title:** Password Log Book Large Print
**Subtitle:** Easy-to-Read Internet Address and Password Organizer for Seniors with Alphabetical Tabs

**7 pól słów kluczowych (backend)** – bez słów, które już są w tytule i podtytule
(Amazon i tak je indeksuje):
1. keeper book for older adults
2. login username journal notebook
3. big font website tracker
4. gift for grandma grandpa elderly
5. online accounts record keeper diary
6. home computer pin code log
7. private address book for parents

**Cena:** 9,99–12,99 $ (mediana w niszy ok. 11,49 $).
