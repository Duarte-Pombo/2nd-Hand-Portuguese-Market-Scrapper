from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Condition(Enum):
    NEW       = "Novo"
    LIKE_NEW  = "Como Novo"
    GOOD      = "Bom Estado"
    USED      = "Usado"
    FOR_PARTS = "Para Peças"
    UNKNOWN   = "Desconhecido"


CONDITION_SCORES: dict[Condition, float] = {
    Condition.NEW:       1.00,
    Condition.LIKE_NEW:  0.85,
    Condition.GOOD:      0.70,
    Condition.USED:      0.50,
    Condition.FOR_PARTS: 0.20,
    Condition.UNKNOWN:   0.40,
}

# Maps raw scraped strings → Condition enum
CONDITION_MAP: dict[str, Condition] = {
    # Portuguese
    "novo":        Condition.NEW,
    "como novo":   Condition.LIKE_NEW,
    "bom estado":  Condition.GOOD,
    "bom":         Condition.GOOD,
    "usado":       Condition.USED,
    "para peças":  Condition.FOR_PARTS,
    "para peças/não funciona": Condition.FOR_PARTS,
    # English (eBay)
    "new":              Condition.NEW,
    "like new":         Condition.LIKE_NEW,
    "very good":        Condition.LIKE_NEW,
    "good":             Condition.GOOD,
    "acceptable":       Condition.USED,
    "for parts":        Condition.FOR_PARTS,
    "for parts or not working": Condition.FOR_PARTS,
    # BackMarket grades
    "pristine":   Condition.NEW,
    "excellent":  Condition.LIKE_NEW,
    "excelente":  Condition.LIKE_NEW,
    "fair":       Condition.USED,
    "aceitável":  Condition.USED,
    "premium":    Condition.LIKE_NEW,
}

# Cities / districts near Porto and Aveiro
PORTO_AVEIRO_KEYWORDS = [
    "porto", "aveiro", "vila nova de gaia", "matosinhos", "braga",
    "maia", "gondomar", "espinho", "ovar", "ílhavo", "águeda",
    "santa maria da feira", "oliveira de azeméis", "valongo",
    "póvoa de varzim", "trofa", "paredes", "penafiel", "gaia",
    "porto district", "aveiro district",
]

CATEGORY_SEARCHES: dict[str, list[str]] = {
    "All PC & Laptops":         ["pc portátil laptop computador"],
    "Laptops & Notebooks":      ["laptop portátil notebook macbook"],
    "Whole PCs / Desktops":     ["computador desktop torre workstation"],
    "CPUs (Processors)":        ["processador cpu ryzen intel core"],
    "GPUs (Graphics Cards)":    ["placa gráfica gpu rtx gtx radeon"],
    "RAM Memory":               ["memória ram ddr4 ddr5"],
    "Motherboards":             ["motherboard placa mãe"],
    "Storage (SSD / HDD)":      ["ssd hdd nvme disco interno"],
    "Monitors & Displays":      ["monitor ecrã display"],
    "PSU / Power Supplies":     ["fonte alimentação psu"],
    "Cooling / Fans":           ["cooler dissipador ventoinha cpu"],
    "Custom Search":            [],
}


@dataclass
class Listing:
    title:       str
    price:       float
    condition:   Condition
    location:    str
    url:         str
    source:      str
    image_url:   Optional[str] = None
    description: Optional[str] = None
    deal_score:  float = 0.0
    raw_condition: str = ""

    @property
    def is_near_porto_aveiro(self) -> bool:
        loc_lower = self.location.lower()
        return any(kw in loc_lower for kw in PORTO_AVEIRO_KEYWORDS)

    @property
    def price_display(self) -> str:
        return "N/A" if self.price <= 0 else f"€{self.price:,.0f}"

    @property
    def score_pct(self) -> int:
        return int(self.deal_score * 100)

    @property
    def location_flag(self) -> str:
        return "📍" if self.is_near_porto_aveiro else "🌐"
