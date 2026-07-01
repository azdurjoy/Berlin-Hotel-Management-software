"""
app.py — Adina Meetings & Events desktop application (PySide6).

Run:  python app.py
The window lets staff compose a booking, see a live VAT breakdown, save it to a
permanent local database, and export selected or all bookings to Excel / PDF.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox, QDateEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QFileDialog, QMessageBox, QAbstractItemView,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

import core
import database as db
import exports

TERRA = "#B65A33"
TERRA_D = "#9a4526"
INK = "#2B2622"
PAPER = "#FAF7F3"
CARD = "#FFFFFF"
LINE = "#E8DED3"
MUTED = "#8A7F74"
SOFT = "#F4E7DF"


STYLE = f"""
QMainWindow, QWidget {{ background: {PAPER}; color: {INK};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; font-size: 13px; }}
QFrame#card {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 4px; }}
QLabel#logo {{ font-family: 'Georgia', serif; font-size: 30px; font-weight: bold; color: {INK}; }}
QLabel#logodot {{ font-family: 'Georgia', serif; font-size: 30px; font-weight: bold; color: {TERRA}; }}
QLabel#brandsub {{ font-size: 10px; letter-spacing: 3px; color: {TERRA}; font-weight: 600; }}
QLabel#h2 {{ font-size: 11px; letter-spacing: 2px; color: {TERRA}; font-weight: 600; }}
QLabel#flabel {{ font-size: 10px; letter-spacing: 1px; color: {MUTED}; font-weight: 600; }}
QLabel#hint {{ font-size: 10px; color: {MUTED}; font-style: italic; }}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {{
    background: #fff; border: 1px solid {LINE}; border-radius: 3px; padding: 7px 9px; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QDateEdit:focus, QTextEdit:focus {{ border: 1px solid {TERRA}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QPushButton#primary {{ background: {TERRA}; color: #fff; border: none; border-radius: 3px;
    padding: 12px 18px; font-weight: 600; letter-spacing: 1px; }}
QPushButton#primary:hover {{ background: {TERRA_D}; }}
QPushButton#dark {{ background: {INK}; color: #fff; border: none; border-radius: 3px;
    padding: 10px 16px; font-weight: 600; letter-spacing: 1px; }}
QPushButton#ghost {{ background: transparent; color: {MUTED}; border: 1px solid {LINE};
    border-radius: 3px; padding: 10px 16px; }}
QPushButton#ghost:hover {{ border: 1px solid {INK}; color: {INK}; }}
QPushButton#rowbtn {{ background: transparent; color: {MUTED}; border: 1px solid {LINE};
    border-radius: 3px; padding: 4px 8px; font-size: 10px; }}
QPushButton#rowbtn:hover {{ border: 1px solid {TERRA}; color: {TERRA}; }}
QTableWidget {{ background: #fff; border: 1px solid {LINE}; gridline-color: {LINE}; }}
QHeaderView::section {{ background: {PAPER}; color: {MUTED}; padding: 8px;
    border: none; border-bottom: 2px solid {INK}; font-size: 10px; font-weight: 600; }}
QLabel#grand {{ font-family: 'Georgia', serif; font-size: 26px; font-weight: bold; color: {TERRA}; }}
QCheckBox {{ spacing: 8px; }}
"""


def flabel(text):
    lb = QLabel(text)
    lb.setObjectName("flabel")
    return lb


class AdinaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Adina · Meetings & Events — Price Calculator")
        self.resize(1180, 880)
        db.init_db()

        self.service_inputs = {}
        self.variant_checks = []

        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(22, 18, 22, 22)
        outer.setSpacing(18)

        outer.addLayout(self._build_header())

        # two-column area
        cols = QHBoxLayout()
        cols.setSpacing(18)
        cols.addWidget(self._build_form_card(), 5)
        cols.addWidget(self._build_breakdown_card(), 4)
        outer.addLayout(cols)

        outer.addWidget(self._build_list_card(), 1)

        self.setStyleSheet(STYLE)
        self._refresh_packages_combo()
        self._on_package_changed()
        self.refresh_list()

    # ---- header --------------------------------------------------------
    def _build_header(self):
        h = QHBoxLayout()
        brand = QHBoxLayout()
        logo = QLabel("Adina")
        logo.setObjectName("logo")
        dot = QLabel(".")
        dot.setObjectName("logodot")
        brand.addWidget(logo)
        brand.addWidget(dot)
        bar = QFrame()
        bar.setFrameShape(QFrame.VLine)
        bar.setStyleSheet(f"color:{LINE}")
        brand.addSpacing(10)
        brand.addWidget(bar)
        brand.addSpacing(10)
        sub = QLabel("MEETINGS & EVENTS")
        sub.setObjectName("brandsub")
        brand.addWidget(sub)
        brand.addStretch()
        h.addLayout(brand)
        return h

    # ---- form ----------------------------------------------------------
    def _build_form_card(self):
        card = QFrame()
        card.setObjectName("card")
        g = QVBoxLayout(card)
        g.setContentsMargins(22, 20, 22, 22)
        g.setSpacing(10)

        title = QLabel("NEW BOOKING")
        title.setObjectName("h2")
        g.addWidget(title)

        row1 = QGridLayout()
        row1.setHorizontalSpacing(12)
        self.bid = QLineEdit()
        self.bid.setPlaceholderText("auto if left empty")
        self.bid.textChanged.connect(self.update_breakdown)
        self.cust = QLineEdit()
        self.cust.setPlaceholderText("Company / guest")
        self.cust.textChanged.connect(self.update_breakdown)
        row1.addWidget(flabel("BOOKING ID"), 0, 0)
        row1.addWidget(flabel("CUSTOMER NAME"), 0, 1)
        row1.addWidget(self.bid, 1, 0)
        row1.addWidget(self.cust, 1, 1)
        self.id_hint = QLabel("")
        self.id_hint.setObjectName("hint")
        row1.addWidget(self.id_hint, 2, 0)
        g.addLayout(row1)

        row2 = QGridLayout()
        row2.setHorizontalSpacing(12)
        self.qty_label = flabel("NUMBER OF GUESTS")
        self.qty = QSpinBox()
        self.qty.setRange(1, 9999)
        self.qty.setValue(1)
        self.qty.valueChanged.connect(self.update_breakdown)
        self.pkg = QComboBox()
        self.pkg.currentIndexChanged.connect(self._on_package_changed)
        self.vdate = QDateEdit()
        self.vdate.setCalendarPopup(True)
        self.vdate.setDisplayFormat("yyyy-MM-dd")
        self.vdate.setDate(QDate.currentDate())
        self.vdate.dateChanged.connect(self.update_breakdown)
        row2.addWidget(self.qty_label, 0, 0)
        row2.addWidget(flabel("PACKAGE"), 0, 1)
        row2.addWidget(flabel("DATE OF EVENT"), 0, 2)
        row2.addWidget(self.qty, 1, 0)
        row2.addWidget(self.pkg, 1, 1)
        row2.addWidget(self.vdate, 1, 2)
        g.addLayout(row2)

        # variants area
        self.variant_box = QVBoxLayout()
        g.addLayout(self.variant_box)

        g.addWidget(flabel("ADDITIONAL SERVICES  (optional · per guest)"))
        self.services_box = QVBoxLayout()
        self.services_box.setSpacing(6)
        for name, price, rate in core.SERVICES:
            line = QHBoxLayout()
            nm = QLabel(name)
            rt = QLabel(f"{rate}%")
            rt.setStyleSheet(f"color:{MUTED}")
            inp = QDoubleSpinBox()
            inp.setRange(0, 100000)
            inp.setDecimals(2)
            inp.setValue(price)
            inp.setFixedWidth(110)
            inp.valueChanged.connect(self.update_breakdown)
            self.service_inputs[name] = (inp, rate)
            line.addWidget(nm)
            line.addStretch()
            line.addWidget(rt)
            line.addWidget(inp)
            self.services_box.addLayout(line)
        g.addLayout(self.services_box)

        row3 = QGridLayout()
        row3.setHorizontalSpacing(12)
        self.adjust = QDoubleSpinBox()
        self.adjust.setRange(-100000, 100000)
        self.adjust.setDecimals(2)
        self.adjust.valueChanged.connect(self.update_breakdown)
        self.adjnote = QLineEdit()
        self.adjnote.setPlaceholderText("e.g. agreed discount")
        self.adjnote.textChanged.connect(self.update_breakdown)
        row3.addWidget(flabel("MANUAL ADJUSTMENT (€, +/−)"), 0, 0)
        row3.addWidget(flabel("ADJUSTMENT NOTE (OPTIONAL)"), 0, 1)
        row3.addWidget(self.adjust, 1, 0)
        row3.addWidget(self.adjnote, 1, 1)
        g.addLayout(row3)
        hint = QLabel("Add or subtract to match your paper documents — applied to the gross total.")
        hint.setObjectName("hint")
        g.addWidget(hint)

        add = QPushButton("ADD TO BOOKING LIST")
        add.setObjectName("primary")
        add.clicked.connect(self.add_entry)
        g.addWidget(add)
        g.addStretch()
        return card

    # ---- breakdown -----------------------------------------------------
    def _build_breakdown_card(self):
        card = QFrame()
        card.setObjectName("card")
        v = QVBoxLayout(card)
        v.setContentsMargins(22, 20, 22, 22)
        title = QLabel("LIVE BREAKDOWN")
        title.setObjectName("h2")
        v.addWidget(title)
        self.breakdown = QTextEdit()
        self.breakdown.setReadOnly(True)
        self.breakdown.setFrameShape(QFrame.NoFrame)
        self.breakdown.setStyleSheet("background:transparent;")
        v.addWidget(self.breakdown)
        return card

    # ---- list ----------------------------------------------------------
    def _build_list_card(self):
        card = QFrame()
        card.setObjectName("card")
        v = QVBoxLayout(card)
        v.setContentsMargins(22, 20, 22, 22)
        title = QLabel("BOOKING LIST")
        title.setObjectName("h2")
        v.addWidget(title)

        self.table = QTableWidget(0, 12)
        self.table.setHorizontalHeaderLabels(
            ["", "ID", "Customer", "Qty", "Package", "Add-ons",
             "Net", "VAT 7%", "VAT 19%", "Adjust", "Total", "Export"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.Stretch)
        v.addWidget(self.table)

        foot = QHBoxLayout()
        gl = QVBoxLayout()
        cap = QLabel("GRAND TOTAL")
        cap.setObjectName("flabel")
        self.grand = QLabel("€0,00")
        self.grand.setObjectName("grand")
        gl.addWidget(cap)
        gl.addWidget(self.grand)
        foot.addLayout(gl)
        foot.addStretch()

        clear = QPushButton("Clear all")
        clear.setObjectName("ghost")
        clear.clicked.connect(self.clear_all)
        exp_pdf = QPushButton("Export PDF")
        exp_pdf.setObjectName("dark")
        exp_pdf.clicked.connect(lambda: self.export(kind="pdf"))
        exp_xls = QPushButton("Export Excel")
        exp_xls.setObjectName("primary")
        exp_xls.clicked.connect(lambda: self.export(kind="xlsx"))
        foot.addWidget(clear)
        foot.addWidget(exp_pdf)
        foot.addWidget(exp_xls)
        v.addLayout(foot)
        return card

    # ---- package / variant handling -----------------------------------
    def _refresh_packages_combo(self):
        self.pkg.blockSignals(True)
        self.pkg.clear()
        for name, pdata in core.PACKAGES.items():
            gross = sum(l[1] for l in pdata["lines"])
            self.pkg.addItem(f"{name} — €{gross:.2f}", name)
        self.pkg.blockSignals(False)

    def _current_package(self):
        return self.pkg.currentData()

    def _on_package_changed(self):
        # rebuild variant checkboxes
        while self.variant_box.count():
            item = self.variant_box.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.variant_checks = []
        pdata = core.PACKAGES[self._current_package()]
        self.qty_label.setText("ROOMS × NIGHTS" if pdata["unit"] == "room"
                               else "NUMBER OF GUESTS")
        for var in pdata.get("variants", []):
            cb = QCheckBox(f'{var["label"]}   +€{var["line"][1]:.2f} · {var["line"][2]}%')
            cb.stateChanged.connect(self.update_breakdown)
            self.variant_box.addWidget(cb)
            self.variant_checks.append(cb)
        self.update_breakdown()

    # ---- building a booking from the form ------------------------------
    def _form_booking(self):
        flags = [cb.isChecked() for cb in self.variant_checks]
        prices = {name: inp.value() for name, (inp, _) in self.service_inputs.items()}
        date = self.vdate.date().toString("yyyy-MM-dd")
        seq = db.next_seq_for_date(date)
        bid = self.bid.text().strip()
        if not bid:
            bid = core.auto_id(date, seq)
        return core.make_booking(
            self._current_package(), self.qty.value(), self.cust.text(), date,
            booking_id=bid, variant_flags=flags, service_prices=prices,
            adjust=self.adjust.value(), adjust_note=self.adjnote.text())

    def update_breakdown(self):
        b = self._form_booking()
        self.id_hint.setText("" if self.bid.text().strip() else f"will use: {b.booking_id}")
        unit_txt = (f"{b.qty} room/night(s)" if b.unit == "room"
                    else f"{b.qty} guest(s)")
        rows = []
        rows.append(f'<div style="font-family:Georgia,serif;font-size:19px;'
                    f'color:{INK};">{core.short_name(b.package)}</div>')
        rows.append(f'<div style="color:{MUTED};font-size:11px;margin-bottom:6px;">{unit_txt}</div>')
        for name, ug, rate, code in b.lines:
            rows.append(
                f'<div style="color:{MUTED};font-size:11px;">{name} '
                f'<span style="opacity:.6">[{code}] {rate}%</span> '
                f'&nbsp;—&nbsp; {core.fmt_eur(ug*b.qty)}</div>')
        for name, ug, rate in b.services:
            rows.append(
                f'<div style="font-size:12px;">+ {name} ({rate}%) × {b.qty} '
                f'&nbsp;—&nbsp; {core.fmt_eur(ug*b.qty)}</div>')
        rows.append("<hr>")
        rows.append(f'<b>Net (excl. VAT)</b> &nbsp;—&nbsp; {core.fmt_eur(b.net)}')
        rows.append(f'<div style="color:{MUTED}">VAT 7% · food/lodging &nbsp;—&nbsp; {core.fmt_eur(b.vat7)}</div>')
        rows.append(f'<div style="color:{MUTED}">VAT 19% · bev/services &nbsp;—&nbsp; {core.fmt_eur(b.vat19)}</div>')
        rows.append(f'<b>Gross</b> &nbsp;—&nbsp; {core.fmt_eur(b.gross)}')
        adj = ("+" if b.adjust >= 0 else "−") + core.fmt_eur(abs(b.adjust))[1:]
        note = f" · {b.adjust_note}" if b.adjust_note else ""
        rows.append(f'Manual adjustment{note} &nbsp;—&nbsp; {adj}')
        rows.append("<hr>")
        rows.append(f'<div style="font-size:15px;"><b>Final total</b> &nbsp;—&nbsp; '
                    f'<span style="font-family:Georgia,serif;font-size:24px;color:{TERRA};">'
                    f'{core.fmt_eur(b.total)}</span></div>')
        self.breakdown.setHtml("<br>".join(rows))

    # ---- actions -------------------------------------------------------
    def add_entry(self):
        b = self._form_booking()
        db.save_booking(b)
        self.bid.clear()
        self.adjust.setValue(0)
        self.adjnote.clear()
        self.refresh_list()
        self.update_breakdown()

    def refresh_list(self):
        self.records = db.load_all()
        self.table.setRowCount(0)
        for r in self.records:
            self._add_table_row(r)
        total = sum(r["total"] for r in self.records)
        self.grand.setText(core.fmt_eur(round(total, 2)))

    def _add_table_row(self, r):
        row = self.table.rowCount()
        self.table.insertRow(row)
        chk = QCheckBox()
        wrap = QWidget()
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(8, 0, 0, 0)
        lay.addWidget(chk)
        self.table.setCellWidget(row, 0, wrap)
        r["_chk"] = chk

        import json as _json
        svc_list = _json.loads(r["services_json"])
        addons = ", ".join(s[0] for s in svc_list) if svc_list else "—"
        qty_txt = f'{r["qty"]}{" rm" if r["unit"] == "room" else ""}'
        adj = "—" if r["adjust"] == 0 else (("+" if r["adjust"] > 0 else "−") +
                                            core.fmt_eur(abs(r["adjust"]))[1:])
        values = [r["booking_id"], r["customer"], qty_txt,
                  core.short_name(r["package"]), addons,
                  core.fmt_eur(r["net"]), core.fmt_eur(r["vat7"]),
                  core.fmt_eur(r["vat19"]), adj, core.fmt_eur(r["total"])]
        for col, val in enumerate(values, start=1):
            it = QTableWidgetItem(str(val))
            if col in (6, 7, 8, 9, 10):
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if col == 10:
                f = it.font(); f.setBold(True); it.setFont(f)
            self.table.setItem(row, col, it)

        # export buttons
        wrap2 = QWidget()
        lay2 = QHBoxLayout(wrap2)
        lay2.setContentsMargins(2, 2, 2, 2)
        lay2.setSpacing(4)
        for label, kind in (("XLS", "xlsx"), ("PDF", "pdf")):
            b = QPushButton(label)
            b.setObjectName("rowbtn")
            b.clicked.connect(lambda _=False, rid=r["row_id"], k=kind: self.export_one(rid, k))
            lay2.addWidget(b)
        dele = QPushButton("✕")
        dele.setObjectName("rowbtn")
        dele.clicked.connect(lambda _=False, rid=r["row_id"]: self.delete_one(rid))
        lay2.addWidget(dele)
        self.table.setCellWidget(row, 11, wrap2)

    def _selected_records(self):
        sel = [r for r in self.records if r.get("_chk") and r["_chk"].isChecked()]
        return sel if sel else self.records

    def export(self, kind):
        recs = self._selected_records()
        if not recs:
            return
        self._do_export(recs, kind, many=len(recs) > 1)

    def export_one(self, row_id, kind):
        rec = next((r for r in self.records if r["row_id"] == row_id), None)
        if rec:
            self._do_export([rec], kind, many=False)

    def _do_export(self, recs, kind, many):
        default = (f"adina-bookings.{kind}" if many
                   else f"adina-booking-{recs[0]['booking_id']}.{kind}")
        filt = "Excel (*.xlsx)" if kind == "xlsx" else "PDF (*.pdf)"
        path, _ = QFileDialog.getSaveFileName(self, "Save export", default, filt)
        if not path:
            return
        try:
            if kind == "xlsx":
                exports.export_excel(recs, path)
            else:
                exports.export_pdf(recs, path)
            QMessageBox.information(self, "Saved", f"Exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export failed", str(e))

    def delete_one(self, row_id):
        db.delete_booking(row_id)
        self.refresh_list()

    def clear_all(self):
        if not self.records:
            return
        if QMessageBox.question(self, "Clear all",
                                "Remove all saved bookings?") == QMessageBox.Yes:
            db.clear_all()
            self.refresh_list()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    w = AdinaApp()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
