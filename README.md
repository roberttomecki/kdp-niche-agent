# KDP Niche Agent (low-content)

Narzędzie na VPS do szukania nisz na Amazon KDP:

1. **discover** – zbiera frazy z podpowiedzi wyszukiwarki Amazona (dział Books) metodą
   „alphabet soup”: `seed a…z`, `seed 0…9`, `a…z seed` oraz modyfikatory typowe dla
   low-content (`for women`, `large print`, `log book`…). Liczba trafień frazy (`hits`)
   to przybliżenie popularności – Amazon nie udostępnia publicznie wolumenu wyszukiwań.
2. **analyze** – dla najlepszych fraz pobiera wyniki wyszukiwania (liczba wyników, reklamy,
   ceny, opinie) i strony top książek (BSR, liczba stron, data wydania, czy wydawca to
   „Independently published”). Z BSR szacuje sprzedaż/dzień.
3. **Ocena niszy 0–100** – popyt (sprzedaż topu), szerokość popytu (ile książek sprzedaje),
   **„słabi, a sprzedają”** (książki z <50 opiniami i ≥0,5 szt./dzień – główny sygnał, że da
   się wejść), udział indie, minus konkurencja (liczba wyników, mediana opinii).
4. **Warstwa agenta (opcjonalna)** – Claude grupuje frazy w nisze, ocenia je, proponuje tytuły
   i 7 pól słów kluczowych KDP oraz **nowe seedy**, które idą do kolejnej rundy (`--rounds`).
5. **report** – HTML (sortowana tabela, klik w wiersz pokazuje książki z topu), CSV, JSON.
   Historia ocen zostaje w SQLite, więc kolejne uruchomienia pokazują zmiany w czasie.

## Instalacja na VPS (Ubuntu/Debian)

```bash
sudo apt install -y python3-venv
cd ~ && unzip kdp-niche-agent.zip && cd kdp-niche-agent
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env          # klucz API, opcjonalnie proxy
cp seeds.example.txt seeds.txt && nano seeds.txt
./venv/bin/python -m pytest -q tests       # testy parserów (offline)
```

## Użycie

```bash
set -a; . ./.env; set +a
# szybki test na jednej frazie
./venv/bin/python kdp_agent.py run --seed "gratitude journal" --market us --top 10
# pełny przebieg: 2 rundy (druga na seedach zaproponowanych przez Claude)
./venv/bin/python kdp_agent.py run --seeds seeds.txt --market us de uk --top 30 --rounds 2
# kroki osobno
./venv/bin/python kdp_agent.py discover --seeds seeds.txt --market us --deep
./venv/bin/python kdp_agent.py analyze --market us --top 50 --per-keyword 10
./venv/bin/python kdp_agent.py report --market us --ai
```

Raporty lądują w `reports/`. Żeby obejrzeć HTML z VPS:
`scp vps:~/kdp-niche-agent/reports/*.html .` albo `python3 -m http.server -d reports 8080`
przez tunel SSH (`ssh -L 8080:localhost:8080 vps`).

Na rynkach DE/FR/IT/ES seedy wpisuj w języku rynku (`dankbarkeitstagebuch`, `carnet de gratitude`).

## Sygnały sprzedaży i historia

- **„Kupione/mies.”** – suma odznak Amazona „X+ bought in past month” z topu wyników. To twarda
  (choć zaniżona) informacja o sprzedaży; gdy jest, wzmacnia ocenę popytu.
- **Historia** – przy każdym przebiegu agent zapisuje BSR, opinie, cenę i odznakę każdej książki
  z topu (maks. raz na dobę). Po kilku cotygodniowych przebiegach widać, czy sprzedaż jest stała:
  ```bash
  ./venv/bin/python kdp_agent.py history --keyword "password log book large print"
  ./venv/bin/python kdp_agent.py history --asin B0XXXXXXXX
  ```

## Cron (np. co poniedziałek o 3:17)

```
17 3 * * 1  /home/USER/kdp-niche-agent/run.sh
```
`run.sh` czyta z `.env` także `MARKETS="us de"`, `TOP`, `ROUNDS`.

## Blokady Amazona – ważne

- **Autocomplete** to lekki endpoint JSON i zwykle działa z VPS bez problemu.
- **Strony wyszukiwania i produktów** Amazon często blokuje dla adresów IP centrów danych
  (CAPTCHA/503). Narzędzie wykrywa to, zapisuje stronę do `debug/` i po kilku blokadach
  przerywa. Rozwiązania (w `.env`): większe `KDP_DELAY`, `KDP_PROXY` (proxy rezydencjalne)
  albo `KDP_FETCH_TEMPLATE` (np. ScraperAPI, ScrapingBee – płatne, ale stabilne).
- Wszystko jest cache'owane (SERP 24 h, produkty i autocomplete 72 h), więc powtórki są tanie.
- Scrapowanie jest niezgodne z regulaminem Amazona – trzymaj niski wolumen.

Koszt jednej frazy: 1 strona wyszukiwania + do `--per-keyword` stron produktów (z cache'em
dużo mniej, bo te same książki wracają w wielu frazach). 30 fraz × 10 ≈ 300 stron ≈ 25–40 min
przy `KDP_DELAY=5`.

## Bramka domowa: Luckfox Pico Ultra (gdy Amazon blokuje IP VPS-a)

Amazon blokuje adresy serwerowe. Rozwiązanie: mała płytka w domu działa jako proxy,
a cała logika zostaje na VPS. Luckfox sam zestawia **odwrotny tunel SSH** do VPS-a, więc
na routerze nie otwierasz żadnych portów. Na VPS proxy jest dostępne tylko pod
`127.0.0.1:8888`, a konto `kdptunnel` nie ma powłoki i może wystawić wyłącznie ten jeden port.

```
VPS: kdp_agent.py --> 127.0.0.1:8888 ==tunel SSH==> Luckfox: tinyproxy --> Amazon (domowe IP)
```

1. **Luckfox** (obraz Ubuntu, kabel do routera), jako root:
   ```bash
   git clone https://github.com/roberttomecki/kdp-niche-agent.git && cd kdp-niche-agent
   sudo bash deploy/luckfox/setup_luckfox.sh ADRES_IP_VPS
   ```
   Na końcu wypisze komendę z kluczem publicznym – skopiuj ją.
2. **VPS**, jako root, w katalogu `/opt/kdp-niche-agent` (po `git pull`):
   ```bash
   sudo bash deploy/vps/setup_vps_tunnel.sh 'ssh-ed25519 AAAA... kdp-tunnel@luckfox'
   ```
3. **Luckfox**: `systemctl restart kdp-tunnel`
4. **VPS**, test – ma pokazać Twój domowy IP:
   ```bash
   curl -s -x http://127.0.0.1:8888 https://api.ipify.org ; echo
   ```
5. **VPS**: w `.env` ustaw `KDP_PROXY=http://127.0.0.1:8888` i uruchom agenta jak zwykle.

Dostęp do Luckfoxa z VPS (niezależnie od tego, w jakiej sieci stoi): `kdp luckfox`
(albo `ssh luckfox`) – tunel wystawia też jego SSH na VPS pod `127.0.0.1:2222`.

Diagnostyka na Luckfoxie: `systemctl status kdp-tunnel tinyproxy --no-pager`,
`journalctl -u kdp-tunnel -n 50`. Tunel sam się odnawia po zaniku sieci lub restarcie.
Proxy przepuszcza tylko HTTPS (port 443). Nie zmniejszaj `KDP_DELAY` – domowe IP też można
„spalić” zbyt szybkim scrapowaniem.

## Gdy parser przestanie działać

Amazon co jakiś czas zmienia HTML. Objaw: w logu „0 wyników sparsowanych” albo puste BSR.
Poprawki robi się tylko w `kdp/parse.py`; zapisany HTML jest w `debug/`. Dodaj go jako
fixture do `tests/fixtures/` i dopisz test.

## Jak czytać wyniki

- **Ocena** to porównanie nisz między sobą, nie prognoza zarobku. Krzywa BSR→sprzedaż
  (`kdp/score.py`) jest zgrubna; na rynkach poza USA skalowana mnożnikiem z `kdp/markets.py`.
- Najcenniejsza kolumna to **„Słabi, a sprzedają”**: ≥2–3 w top 10 oznacza, że nowa książka
  bez opinii ma realną szansę.
- **Popularność AC** wysoka + mało wyników = długi ogon wart sprawdzenia ręcznie.
- Gdy zaczniesz kampanie Amazon Ads, raport „Search term” daje prawdziwe frazy klientów –
  można je wrzucić jako seedy.

## Struktura

```
kdp_agent.py      CLI
kdp/markets.py    rynki (domena, marketplace id, mnożnik sprzedaży)
kdp/http.py       pobieranie: cache, opóźnienia, retry, CAPTCHA, proxy
kdp/discover.py   autocomplete / alphabet soup
kdp/parse.py      parsery SERP i stron produktów
kdp/score.py      BSR -> sprzedaż, ocena niszy
kdp/analyze.py    analiza jednej frazy
kdp/llm.py        warstwa Claude (wnioski + nowe seedy)
kdp/report.py     HTML/CSV/JSON
```
