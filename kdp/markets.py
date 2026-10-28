"""Konfiguracja rynków Amazon."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Market:
    code: str
    domain: str          # np. amazon.com
    mid: str             # marketplace id (dla autocomplete)
    lang: str
    # Mnożnik sprzedaży względem USA przy tym samym BSR (bardzo zgrubny).
    sales_factor: float

    @property
    def completion_url(self) -> str:
        return f"https://completion.{self.domain}/api/2017/suggestions"

    @property
    def base_url(self) -> str:
        return f"https://www.{self.domain}"


MARKETS = {
    "us": Market("us", "amazon.com", "ATVPDKIKX0DER", "en_US", 1.00),
    "uk": Market("uk", "amazon.co.uk", "A1F83G8C2ARO7P", "en_GB", 0.30),
    "de": Market("de", "amazon.de", "A1PA6795UKMFR9", "de_DE", 0.35),
    "fr": Market("fr", "amazon.fr", "A13V1IB3VIYZZH", "fr_FR", 0.20),
    "it": Market("it", "amazon.it", "APJ6JRA9NG5V4", "it_IT", 0.15),
    "es": Market("es", "amazon.es", "A1RKKUPIHCS9HS", "es_ES", 0.15),
    "ca": Market("ca", "amazon.ca", "A2EUQ1WTGCTBG2", "en_CA", 0.15),
    "au": Market("au", "amazon.com.au", "A39IBJ37TRP1C6", "en_AU", 0.08),
}


def get_market(code: str) -> Market:
    try:
        return MARKETS[code.lower()]
    except KeyError:
        raise SystemExit(f"Nieznany rynek '{code}'. Dostępne: {', '.join(MARKETS)}")
