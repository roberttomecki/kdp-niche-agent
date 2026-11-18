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
- **Cover:** „Upload a cover you already have” → odpowiedni `*_cover.pdf`
- **Manuscript:** odpowiedni plik `*_interior.pdf`
- Po wgraniu obejrzyj całość w **Previewer** – szczególnie zakładki przy krawędzi.

## Okładka

```bash
pip install playwright        # na serwerze/komputerze z Chromium
python cover/make_cover.py --all --pages 102
```

Wynik w `output/`: `password-log-book_<format>_cover.pdf` (pełna okładka: tył + grzbiet + przód,
ze spadem 0,125") i podgląd PNG. Grzbiet ≈ 102 × 0,002252" ≈ 0,23" – bez tekstu (wąski grzbiet).
Prawy dolny róg tyłu zostaje pusty na kod kreskowy, który dodaje KDP.

| format | wymiary PDF okładki |
|---|---|
| 8,5 × 11 | 17,48 × 11,25" |
| 6 × 9 | 12,48 × 9,25" |

Przed wysyłką porównaj wymiary z szablonem z KDP Cover Calculator; jeśli KDP poda inną szerokość
grzbietu, zmień stałą `PAPER` albo `--pages` i wygeneruj ponownie.

Projekt: zieleń jak płótno notesu adresowego, krój Atkinson Hyperlegible Next (tworzony z myślą
o osobach słabowidzących, licencja OFL), kolumna zakładek A–Z jak we wnętrzu z wysuniętą mosiężną
zakładką „P”, wyeksponowane „Large Print”, uczciwy podtytuł o nadrukowanym indeksie, a na przodzie podgląd prawdziwego wpisu z dużą czcionką.

## Propozycja opisu (do dopracowania)

**Title:** Password Log Book Large Print
**Subtitle:** Easy-to-Read Internet Address and Password Organizer for Seniors with a Printed A–Z Index

W opisie produktu napisz wprost, że indeks A–Z jest **nadrukowany na brzegu stron (bez wycinanych przekładek)** –
kupujący znają notesy z prawdziwymi przekładkami (Clever Fox, JUBTIC) i inaczej mogą się rozczarować.

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
