"""Powiadomienia Telegram: wiadomość od Twojego bota.

Konfiguracja w .env:
  TELEGRAM_TOKEN=123456:ABC...   (od @BotFather)
  TELEGRAM_CHAT_ID=987654321     (ustawi go: kdp_agent.py telegram)
Wysyłane bezpośrednio z VPS (nie przez proxy Luckfoxa).
"""
import logging
import os
from pathlib import Path

import requests

log = logging.getLogger("kdp")
API = "https://api.telegram.org/bot{token}/{method}"


def configured() -> bool:
    return bool(os.getenv("TELEGRAM_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))


def send(text: str) -> bool:
    if not configured():
        return False
    try:
        r = requests.post(API.format(token=os.environ["TELEGRAM_TOKEN"], method="sendMessage"),
                          data={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": text,
                                "disable_web_page_preview": "true"}, timeout=20)
        if r.status_code != 200:
            log.warning("Telegram: błąd %s %s", r.status_code, r.text[:200])
        return r.status_code == 200
    except requests.RequestException as e:
        log.warning("Telegram: %s", e)
        return False


def find_chat_id(token: str) -> str | None:
    """Odczytaj chat_id z ostatniej wiadomości, którą wysłałeś do bota."""
    r = requests.get(API.format(token=token, method="getUpdates"), timeout=20)
    r.raise_for_status()
    for upd in reversed(r.json().get("result", [])):
        chat = (upd.get("message") or upd.get("edited_message") or {}).get("chat")
        if chat:
            return str(chat["id"])
    return None


def setup(env_path: Path) -> str:
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        return "Brak TELEGRAM_TOKEN w .env – dopisz go najpierw (token od @BotFather)."
    chat = os.getenv("TELEGRAM_CHAT_ID") or find_chat_id(token)
    if not chat:
        return "Nie widzę wiadomości do bota. Otwórz swojego bota w Telegramie, wyślij mu „start” i spróbuj ponownie."
    if not os.getenv("TELEGRAM_CHAT_ID"):
        with env_path.open("a", encoding="utf-8") as fh:
            fh.write(f"\nTELEGRAM_CHAT_ID={chat}\n")
        os.environ["TELEGRAM_CHAT_ID"] = chat
    ok = send("✅ Agent KDP połączony. Tu będę pisał o sprzedaży i opiniach Twoich książek.")
    return "Gotowe – sprawdź Telegram." if ok else "Nie udało się wysłać wiadomości – sprawdź token."


def book_events(label: str, asin: str, prev: tuple | None, now: dict) -> list[str]:
    """prev: (ts, bsr, reviews, price, bought, title) z poprzedniego wpisu albo None."""
    url = f"https://www.amazon.com/dp/{asin}"
    bsr, rev = now.get("bsr"), now.get("reviews")
    out = []
    pbsr, prev_rev = (prev[1], prev[2]) if prev else (None, None)
    if bsr and not pbsr:
        out.append(f"🎉 {label}: pojawił się BSR {bsr:,} – pierwsza sprzedaż!\n{url}")
    elif bsr and pbsr and bsr < pbsr * 0.5:
        out.append(f"📈 {label}: BSR {pbsr:,} → {bsr:,} – prawdopodobnie kolejna sprzedaż.\n{url}")
    if rev is not None and prev_rev is not None and rev > prev_rev:
        out.append(f"⭐ {label}: nowa opinia (razem {rev}).\n{url}")
    return [m.replace(",", " ") for m in out]
