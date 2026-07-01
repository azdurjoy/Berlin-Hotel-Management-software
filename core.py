"""
core.py — Adina Meetings & Events price engine.

Pure logic, no UI. Packages are itemised line by line; VAT is computed per line
from the gross price so every total foots exactly to the sum of gross prices.

To change prices, rates, codes, or add packages/services, edit PACKAGES and
SERVICES below. Each line is: (name, gross_price, vat_rate, accounting_code).
"""

from dataclasses import dataclass, field
from datetime import datetime

VAT_FOOD = 7
VAT_BEV = 19

# ---------------------------------------------------------------------------
# CONFIG — edit packages and services here
# ---------------------------------------------------------------------------
PACKAGES = {
    "Full-Day Meeting (Ganztagspauschale)": {
        "unit": "pax",
        "lines": [
            ("Coffeebreak – Morning (food)", 15, 7, "493032"),
            ("Coffeebreak – Afternoon (food)", 15, 7, "493033"),
            ("Lunch (food)", 39, 7, "493009"),
            ("Lunch Drinks", 4, 19, "494007"),
            ("Room Hire", 5, 19, "498005"),
            ("Equipment", 5, 19, "498004"),
            ("Conference Drinks", 12, 19, "494003"),
        ],
        "variants": [
            {"label": "Add Welcome Coffee (Begrüßungskaffee)",
             "line": ("Welcome Coffee", 8, 19, "3011")},
        ],
    },
    "Half-Day Meeting (Halbtagspauschale)": {
        "unit": "pax",
        "lines": [
            ("Coffeebreak Drinks", 4, 19, "493003"),
            ("Coffeebreak (food)", 15, 7, "493033"),
            ("Lunch (food)", 40, 7, "493009"),
            ("Lunch Drinks", 6, 19, "494007"),
            ("Room Hire", 6, 19, "498005"),
            ("Equipment", 6, 19, "498004"),
            ("Conference Drinks", 12, 19, "494003"),
        ],
    },
    "Day & Night All-Inclusive (with Dinner)": {
        "unit": "pax",
        "lines": [
            ("Coffeebreak (food)", 15, 7, "3002"),
            ("Lunch Drinks", 6, 19, "3007"),
            ("Lunch (food)", 38, 7, "3004"),
            ("Dinner (food)", 40, 7, "3005"),
            ("Dinner Drinks", 12, 19, "3008"),
            ("Room Hire", 5, 19, "3019"),
            ("Equipment", 5, 19, "3018"),
            ("General Drinks", 12, 19, "3009"),
            ("Coffee/Tea Arrangement", 5, 19, "3000"),
        ],
    },
    "Lunchbox Package (mobile / no sit-down)": {
        "unit": "pax",
        "lines": [
            ("Coffeebreak Drinks", 6, 19, "493003"),
            ("Lunchbox (food)", 35, 7, "493009"),
            ("Lunch Drinks", 6, 19, "494007"),
            ("Room Hire", 5, 19, "498005"),
            ("Equipment", 5, 19, "498004"),
            ("Conference Drinks", 12, 19, "494003"),
        ],
    },
    "Overnight Stay + Breakfast (per room/night)": {
        "unit": "room",
        "lines": [
            ("Room / Lodging", 135, 7, "ACC"),
            ("Breakfast Food", 11.32, 7, "BF FOOD"),
            ("Breakfast Drinks", 5.40, 19, "BF BEV"),
        ],
    },
}

# Additional services — all start at 0; staff enter a value when needed.
SERVICES = [
    ("Parking (per night)", 0.0, 19),
    ("Extra Coffee", 0.0, 7),
    ("Extra Drinks", 0.0, 19),
]


# ---------------------------------------------------------------------------
# Calculation
# ---------------------------------------------------------------------------
def net_from_gross(gross: float, rate: int) -> float:
    """Net price given a VAT-inclusive gross and a rate in percent."""
    return gross / (1 + rate / 100)


@dataclass
class Booking:
    booking_id: str
    customer: str
    qty: int
    unit: str
    package: str
    event_date: str
    lines: list           # list of (name, gross_unit, rate, code)
    services: list        # list of (name, gross_unit, rate)  (price > 0 only)
    adjust: float = 0.0
    adjust_note: str = ""

    # computed
    net: float = field(default=0.0)
    vat7: float = field(default=0.0)
    vat19: float = field(default=0.0)
    gross: float = field(default=0.0)
    total: float = field(default=0.0)

    def compute(self):
        vat7 = vat19 = gross = 0.0
        for _name, unit_gross, rate, _code in self.lines:
            g = unit_gross * self.qty
            v = g - net_from_gross(g, rate)
            gross += g
            if rate == 7:
                vat7 += v
            else:
                vat19 += v
        for _name, unit_gross, rate in self.services:
            g = unit_gross * self.qty
            v = g - net_from_gross(g, rate)
            gross += g
            if rate == 7:
                vat7 += v
            else:
                vat19 += v
        self.vat7 = round(vat7, 2)
        self.vat19 = round(vat19, 2)
        self.gross = round(gross, 2)
        self.net = round(gross - vat7 - vat19, 2)
        self.total = round(gross + self.adjust, 2)
        return self


def make_booking(package_name, qty, customer, event_date,
                 booking_id="", variant_flags=None,
                 service_prices=None, adjust=0.0, adjust_note=""):
    """Build and compute a Booking from form-style inputs.

    variant_flags: list of bools matching the package's variants.
    service_prices: dict {service_name: price} for any non-zero services.
    """
    pkg = PACKAGES[package_name]
    qty = max(1, int(qty or 1))

    lines = list(pkg["lines"])
    if variant_flags and pkg.get("variants"):
        for flag, var in zip(variant_flags, pkg["variants"]):
            if flag:
                lines.append(var["line"])

    services = []
    if service_prices:
        for name, price, rate in SERVICES:
            p = float(service_prices.get(name, 0) or 0)
            if p > 0:
                services.append((name, p, rate))

    if not booking_id.strip():
        booking_id = auto_id(event_date)

    b = Booking(
        booking_id=booking_id.strip(),
        customer=(customer.strip() or "—"),
        qty=qty, unit=pkg["unit"], package=package_name,
        event_date=event_date or "",
        lines=lines, services=services,
        adjust=float(adjust or 0), adjust_note=adjust_note.strip(),
    )
    return b.compute()


def auto_id(event_date: str, seq: int = 1) -> str:
    """DDMMYYYY + 3-digit sequence, e.g. 28062026001."""
    try:
        d = datetime.fromisoformat(event_date) if event_date else datetime.now()
    except ValueError:
        d = datetime.now()
    return f"{d.day:02d}{d.month:02d}{d.year}{seq:03d}"


def fmt_eur(n: float) -> str:
    """German-style euro formatting: €1.234,56"""
    s = f"{n:,.2f}"                      # 1,234.56
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return "€" + s


def short_name(pkg: str) -> str:
    return pkg.split(" (")[0]
