# Adina · Meetings & Events — Desktop Price Calculator

A native desktop application (Windows & macOS) for composing conference-package
bookings, computing per-line German VAT, saving them to a permanent local
database, and exporting brand-styled Excel and PDF price sheets.

Built with Python + PySide6 (Qt). Data is stored locally in SQLite — nothing
leaves the computer, and bookings persist across restarts.

---

## Files

| File | What it does |
|------|--------------|
| `app.py` | The GUI (the program you run). |
| `core.py` | Packages, services, and the VAT calculation engine. **Edit prices here.** |
| `database.py` | Local SQLite storage. |
| `exports.py` | Excel + PDF generation. |
| `requirements.txt` | The three libraries needed. |

---

## A. Run it directly (quickest — needs Python)

1. Install Python 3.10+ from https://python.org (on Windows, tick
   **"Add Python to PATH"** during install).
2. Open a terminal (Windows: **Command Prompt** or **PowerShell**; Mac: **Terminal**)
   in this folder and run:

   ```
   pip install -r requirements.txt
   python app.py
   ```

The window opens. That's it.

---

## B. Build a standalone app (no Python needed to run it)

This produces a single file you can copy to any Windows or Mac machine and
double-click — the end user does **not** need Python installed.

> Important: you must build **on the same OS you're targeting**. Build on
> Windows to get a `.exe`; build on a Mac to get a `.app`. PyInstaller cannot
> cross-build.

### Step 1 — install the tools (one time)

```
pip install -r requirements.txt
pip install pyinstaller
```

### Step 2 — build

**Windows** (produces `dist\Adina.exe`):

```
pyinstaller --noconfirm --windowed --onefile --name "Adina" app.py
```

**macOS** (produces `dist/Adina.app`):

```
pyinstaller --noconfirm --windowed --onefile --name "Adina" app.py
```

When it finishes, your program is in the **`dist`** folder. Copy that one
file (`Adina.exe` or `Adina.app`) to wherever you want to use it.

Notes:
- `--windowed` hides the black console window.
- First launch may take a few seconds while it unpacks.
- On macOS, the first time you open it you may need to right-click →
  **Open** (because it isn't code-signed by Apple). This is normal for
  self-built apps.

---

## Where your data is stored

A folder named **`.adina_meetings`** in your user home directory:

- Windows: `C:\Users\<you>\.adina_meetings\bookings.db`
- macOS: `/Users/<you>/.adina_meetings/bookings.db`

To **back up** your bookings, copy that `bookings.db` file. To move to a new
computer, copy it into the same folder there.

---

## Changing packages, prices, or services

Open **`core.py`** and edit the `PACKAGES` and `SERVICES` sections at the top.
Each package line is:

```python
("Line item name", gross_price, vat_rate, "accounting_code")
```

- `gross_price` is the VAT-inclusive (Brutto) price.
- `vat_rate` is `7` (food / lodging) or `19` (beverages / services).
- VAT is computed automatically per line, so totals always foot to the sum of
  gross prices.

Add the Welcome Coffee–style options under a package's `"variants"` list.
After editing, re-run (method A) or re-build (method B).

---

## VAT logic (German law, 2026)

Food and lodging are taxed at **7%**; beverages and services (room hire,
equipment, drinks) at **19%**, following the German UStG rules effective
1 January 2026. Each package is itemized, so mixed-rate packages split their
VAT correctly and audit-cleanly.

---

## Notes / open items

- **Overnight package room rate:** the supplied line items (135.00 + 11.32 +
  5.40) total **€151.72**, while the original header said €146.32. The app uses
  the itemized lines. If the room line should differ, change it in `core.py`.
- The app is not code-signed. For wide internal distribution on managed
  machines, you may want a signing certificate (Windows) or Apple Developer ID
  (Mac), but it runs fine without one.
