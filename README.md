# Berlin-Hotel-Management-software
Desktop app for hotel meetings &amp; events pricing. Auto-calculates mixed German VAT (7% food / 19% beverages) per line item, saves bookings locally, and exports branded Excel &amp; PDF sheets. PySide6 + SQLite.
# Adina · Meetings & Events — Desktop Price Calculator

A native desktop application (Windows & macOS) for composing hotel conference &
event bookings, computing **mixed German VAT per line item** (7% food / 19%
beverages & services), saving everything to a **permanent local database**, and
Exporting **brand-styled Excel and PDF** price sheets.

Built with Python + PySide6 (Qt). All data stays on the machine — nothing is
Sent anywhere, and bookings persist across restarts.

---

## Why this exists

Conference and event pricing in hospitality involves **multiple packages, optional
add-ons, and mixed VAT rates**. In Germany, food is taxed at 7% while beverages
and services (room hire, equipment, drinks) are taxed at 19%. Calculating this
by hand across many bookings is slow and error-prone, and a single mistake can
cause problems at audit time.

This app replaces a complex pricing spreadsheet with a clean, click-and-go tool
that applies the correct VAT split automatically and produces accounting-ready
exports.

---

## Features

- **Five itemized packages** — each package is defined line by line with its own
  accounting code and VAT rate, so mixed-rate packages split correctly.
- **Live cost breakdown** — see net, VAT 7%, VAT 19%, gross, and final total
  update in real time as you build a booking.
- **Optional add-on services** — parking, extra coffee, extra drinks (start at 0;
  staff enter a value only when needed).
- **Package variants** — e.g. add a Welcome Coffee (Begrüßungskaffee) with one tick.
- **Manual +/− adjustment** — with an optional note, to match paper documents.
- **Automatic booking IDs** — `DDMMYYYY` + sequence, or enter your own.
- **Permanent local storage** — every booking saved to a local SQLite database.
- **One-click exports** — branded **Excel** (Summary + Itemized sheets) and
  **PDF** price sheets, for single bookings or the whole list.
- **Runs offline** — no internet, no account, no server.

---

## Tech stack

| Layer | Tool |
|-------|------|
| UI | [PySide6](https://doc.qt.io/qtforpython/) (Qt) |
| Storage | SQLite (via Python's built-in `sqlite3`) |
| Excel export | [openpyxl](https://openpyxl.readthedocs.io/) |
| PDF export | [ReportLab](https://www.reportlab.com/) |
| Packaging | [PyInstaller](https://pyinstaller.org/) |

---

## Project structure

```
adina-app/
├── app.py            # GUI — the program you run
├── core.py           # Packages, services & VAT engine — edit prices here
├── database.py       # Local SQLite storage
├── exports.py        # Excel + PDF generation
├── requirements.txt  # Dependencies
└── README.md
```

---

## Getting started

### Requirements
- Python 3.10 or newer

### Run from source (quickest)

```bash
pip install -r requirements.txt
python app.py          # use python3 on macOS/Linux
```

The window opens immediately.

### Build a standalone app (no Python needed to run it)

> Build on the OS you're targeting — PyInstaller can't cross-build. Build on
> Windows for a `.exe`, on macOS for a `.app`.

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --windowed --onefile --name "Adina" app.py
```

The finished program appears in the **`dist/`** folder:
- Windows → `dist/Adina.exe`
- macOS → `dist/Adina.app`

**macOS note:** the first time you open the app, right-click → **Open** →
**Open** to get past the unsigned-app warning (only needed once).

---

## Configuration

All prices, packages, and services live at the top of **`core.py`**. Each
package line is:

```python
("Line item name", gross_price, vat_rate, "accounting_code")
```

- `gross_price` — the VAT-inclusive (Brutto) price
- `vat_rate` — `7` (food / lodging) or `19` (beverages / services)

VAT is computed per line from the gross price, so totals always foot to the sum
of gross prices. Edit and re-run (or re-build) to apply changes.

---

## Data storage

Bookings are saved to:

- **Windows:** `C:\Users\<you>\.adina_meetings\bookings.db`
- **macOS:** `/Users/<you>/.adina_meetings/bookings.db`

To back up or migrate, copy that `bookings.db` file.

---

## VAT logic

Follows German UStG rules effective **1 January 2026**: food and lodging at
**7%**, beverages and services at **19%**. Because every package is itemized,
mixed-rate packages are split accurately and remain audit-clean.

---

## Roadmap / ideas

- Optional Adina logo icon (`.ico` / `.icns`) for the built app
- Search and filter the booking list
- Batch "export each selected booking as its own file"
- Editable packages from within the UI (no code edit)

---

## License

Add a license of your choice (e.g. MIT) before publishing.

---

## Disclaimer

This is an independent tool. Package names, prices, and branding are used for
demonstration; confirm any real-world tax figures with a qualified accountant
before operational use.
