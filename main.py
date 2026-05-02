import sys
import csv
import webbrowser
from datetime import datetime
from typing import List, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPushButton, QLineEdit, QLabel, QTableWidget,
    QTableWidgetItem, QProgressBar, QCheckBox, QComboBox,
    QDoubleSpinBox, QGroupBox, QScrollArea, QDialog, QFormLayout,
    QDialogButtonBox, QHeaderView, QFrame, QMessageBox, QFileDialog,
    QSlider, QSizePolicy, QAbstractItemView, QSpinBox, QStatusBar,
    QLineEdit,
)
from PyQt6.QtCore  import Qt, QSize, QUrl, QTimer
from PyQt6.QtGui   import (
    QColor, QFont, QIcon, QDesktopServices, QAction, QFontDatabase,
    QCursor,
)

from models  import Listing, Condition, CATEGORY_SEARCHES
from config  import load_config, save_config
from scorer  import filter_listings
from workers import ScraperWorker


# ─────────────────────────────────────────────────────────────
#  Palette
# ─────────────────────────────────────────────────────────────
BG        = "#0d0d1a"
SURFACE   = "#13132b"
SURFACE2  = "#1c1c3a"
ACCENT    = "#e94560"
ACCENT2   = "#4e9af1"
TEXT      = "#e8e8f0"
TEXT_MUTED= "#7878a0"
SUCCESS   = "#2ecc71"
WARNING   = "#f39c12"
DANGER    = "#e74c3c"
BORDER    = "#2a2a4a"

SCORE_COLORS = {
    80: SUCCESS,
    60: "#8bc34a",
    40: WARNING,
    0:  DANGER,
}

SOURCE_COLORS = {
    "OLX.pt":              "#6e45e2",
    "CustoJusto.pt":       "#00b4d8",
    "eBay.pt":             "#f5af02",
    "BackMarket.pt":       "#4caf50",
    "Facebook Marketplace":"#1877f2",
}

CONDITION_COLORS = {
    Condition.NEW:       SUCCESS,
    Condition.LIKE_NEW:  "#8bc34a",
    Condition.GOOD:      ACCENT2,
    Condition.USED:      WARNING,
    Condition.FOR_PARTS: DANGER,
    Condition.UNKNOWN:   TEXT_MUTED,
}


# ─────────────────────────────────────────────────────────────
#  Global stylesheet
# ─────────────────────────────────────────────────────────────
STYLE = f"""
QMainWindow, QDialog {{ background: {BG}; color: {TEXT}; }}
QWidget {{ background: {BG}; color: {TEXT}; font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; font-size: 13px; }}

/* Scrollbars */
QScrollBar:vertical {{ background: {SURFACE}; width: 8px; border-radius: 4px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 4px; min-height: 20px; }}
QScrollBar::handle:vertical:hover {{ background: {TEXT_MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: {SURFACE}; height: 8px; border-radius: 4px; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 4px; min-width: 20px; }}

/* Inputs */
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
    background: {SURFACE2}; color: {TEXT}; border: 1px solid {BORDER};
    border-radius: 6px; padding: 6px 10px;
}}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {ACCENT2};
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: {SURFACE2}; color: {TEXT}; border: 1px solid {BORDER};
    selection-background-color: {ACCENT2};
}}

/* Buttons */
QPushButton {{
    background: {SURFACE2}; color: {TEXT}; border: 1px solid {BORDER};
    border-radius: 6px; padding: 7px 16px; font-weight: 600;
}}
QPushButton:hover  {{ background: {BORDER}; border-color: {ACCENT2}; }}
QPushButton:pressed {{ background: {ACCENT2}; color: #fff; }}
QPushButton#btnScan {{
    background: {ACCENT}; color: #fff; border: none; font-size: 13px;
}}
QPushButton#btnScan:hover  {{ background: #c73652; }}
QPushButton#btnScan:pressed {{ background: #a32b42; }}
QPushButton#btnStop {{
    background: {SURFACE2}; color: {DANGER}; border: 1px solid {DANGER};
}}
QPushButton#btnStop:hover {{ background: {DANGER}; color: #fff; }}
QPushButton#btnOpen {{
    background: transparent; color: {ACCENT2}; border: none;
    padding: 4px 8px; font-size: 12px; text-decoration: underline;
}}
QPushButton#btnOpen:hover {{ color: #fff; }}

/* Checkboxes */
QCheckBox {{ spacing: 6px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid {BORDER}; background: {SURFACE2};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT2}; border-color: {ACCENT2};
    image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><polyline points='3,8 7,12 13,4' stroke='white' stroke-width='2' fill='none'/></svg>");
}}

/* Table */
QTableWidget {{
    background: {SURFACE}; color: {TEXT};
    border: none; gridline-color: {SURFACE2};
    selection-background-color: {SURFACE2};
}}
QTableWidget::item {{ padding: 4px 8px; border-bottom: 1px solid {SURFACE2}; }}
QTableWidget::item:selected {{ background: {SURFACE2}; color: {TEXT}; }}
QHeaderView::section {{
    background: {SURFACE2}; color: {TEXT_MUTED}; font-weight: 700;
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
    border: none; border-bottom: 1px solid {BORDER}; padding: 8px 10px;
}}
QHeaderView::section:hover {{ color: {TEXT}; background: {BORDER}; }}

/* Group boxes */
QGroupBox {{
    color: {TEXT_MUTED}; font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.5px;
    border: 1px solid {BORDER}; border-radius: 8px; margin-top: 14px;
    padding-top: 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    padding: 0 6px; background: {BG};
}}

/* Progress bar */
QProgressBar {{
    background: {SURFACE2}; border: none; border-radius: 3px;
    height: 6px; text-align: center; color: transparent;
}}
QProgressBar::chunk {{ background: {ACCENT2}; border-radius: 3px; }}

/* Splitter */
QSplitter::handle {{ background: {BORDER}; width: 1px; }}

/* Status bar */
QStatusBar {{ background: {SURFACE}; color: {TEXT_MUTED}; font-size: 12px; }}
"""


# ─────────────────────────────────────────────────────────────
#  Settings Dialog
# ─────────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Facebook credentials ──
        fb_box = QGroupBox("Facebook Marketplace Credentials")
        fb_form = QFormLayout(fb_box)
        fb_form.setSpacing(10)

        self.fb_email = QLineEdit(self.config.get("fb_email", ""))
        self.fb_email.setPlaceholderText("your@email.com")
        self.fb_pass  = QLineEdit(self.config.get("fb_password", ""))
        self.fb_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.fb_pass.setPlaceholderText("••••••••")

        fb_form.addRow("Email:",    self.fb_email)
        fb_form.addRow("Password:", self.fb_pass)

        warn = QLabel("⚠ Stored in plain text. Use a dedicated account if possible.")
        warn.setStyleSheet(f"color: {WARNING}; font-size: 11px;")
        warn.setWordWrap(True)
        fb_form.addRow(warn)
        layout.addWidget(fb_box)

        # ── Scraping options ──
        opt_box = QGroupBox("Scraping Options")
        opt_form = QFormLayout(opt_box)
        opt_form.setSpacing(10)

        self.max_results = QSpinBox()
        self.max_results.setRange(5, 100)
        self.max_results.setValue(self.config.get("max_results_per_site", 30))
        self.max_results.setSuffix(" results / site")

        self.headless = QCheckBox("Headless browser (faster, no visible window)")
        self.headless.setChecked(self.config.get("headless_browser", True))

        opt_form.addRow("Limit:",    self.max_results)
        opt_form.addRow(self.headless)
        layout.addWidget(opt_box)

        # ── Score weights ──
        wt_box = QGroupBox("Deal Score Weights  (must sum to 100)")
        wt_form = QFormLayout(wt_box)
        wt_form.setSpacing(10)

        w = self.config.get("weights", {})
        self.w_price = self._spin(int(w.get("price", 0.5) * 100))
        self.w_cond  = self._spin(int(w.get("condition", 0.3) * 100))
        self.w_loc   = self._spin(int(w.get("location", 0.2) * 100))

        wt_form.addRow("Price %:",     self.w_price)
        wt_form.addRow("Condition %:", self.w_cond)
        wt_form.addRow("Location %:",  self.w_loc)
        layout.addWidget(wt_box)

        # ── Buttons ──
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _spin(self, val: int) -> QSpinBox:
        s = QSpinBox()
        s.setRange(0, 100)
        s.setValue(val)
        s.setSuffix("%")
        return s

    def _save(self):
        total = self.w_price.value() + self.w_cond.value() + self.w_loc.value()
        if total != 100:
            QMessageBox.warning(self, "Invalid Weights",
                                f"Weights must sum to 100 (currently {total}).")
            return
        self.config["fb_email"]             = self.fb_email.text().strip()
        self.config["fb_password"]          = self.fb_pass.text()
        self.config["max_results_per_site"] = self.max_results.value()
        self.config["headless_browser"]     = self.headless.isChecked()
        self.config["weights"] = {
            "price":     self.w_price.value() / 100,
            "condition": self.w_cond.value()  / 100,
            "location":  self.w_loc.value()   / 100,
        }
        save_config(self.config)
        self.accept()


# ─────────────────────────────────────────────────────────────
#  Main Window
# ─────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    # Table column indices
    COL_SCORE  = 0
    COL_TITLE  = 1
    COL_PRICE  = 2
    COL_COND   = 3
    COL_LOC    = 4
    COL_SOURCE = 5
    COL_LINK   = 6

    def __init__(self):
        super().__init__()
        self.config   = load_config()
        self._listings: List[Listing] = []
        self._worker:   Optional[ScraperWorker] = None

        self.setWindowTitle("Break Point")
        self.setMinimumSize(1100, 680)
        self.resize(1280, 780)

        self._build_ui()
        self._connect_signals()

    # ── UI construction ───────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        root.addWidget(splitter)

        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_main_panel())
        splitter.setSizes([240, 1040])
        splitter.setStretchFactor(1, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.lbl_status = QLabel("Ready  ·  0 listings")
        self.lbl_status.setStyleSheet(f"color: {TEXT_MUTED};")
        self.status_bar.addWidget(self.lbl_status)

        self.lbl_last_scan = QLabel("")
        self.lbl_last_scan.setStyleSheet(f"color: {TEXT_MUTED};")
        self.status_bar.addPermanentWidget(self.lbl_last_scan)

    # ── Sidebar (filters) ──

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"background: {SURFACE}; border-right: 1px solid {BORDER};")

        scroll = QScrollArea()
        scroll.setWidget(sidebar)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {SURFACE}; }}")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(6)

        # Logo / title
        title = QLabel("Break Point\nScrapper")
        title.setStyleSheet(
            f"color: {TEXT}; font-size: 18px; font-weight: 800; line-height: 1.2;"
        )
        layout.addWidget(title)

        accent_bar = QFrame()
        accent_bar.setFixedHeight(3)
        accent_bar.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {ACCENT}, stop:1 {ACCENT2}); border-radius: 2px;"
        )
        layout.addWidget(accent_bar)
        layout.addSpacing(10)

        # ── Price filter ──
        price_box = QGroupBox("Price Range")
        price_layout = QVBoxLayout(price_box)
        price_layout.setSpacing(6)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Min €"))
        self.spin_min_price = QDoubleSpinBox()
        self.spin_min_price.setRange(0, 99999)
        self.spin_min_price.setDecimals(0)
        self.spin_min_price.setSpecialValueText("Any")
        row1.addWidget(self.spin_min_price)
        price_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Max €"))
        self.spin_max_price = QDoubleSpinBox()
        self.spin_max_price.setRange(0, 99999)
        self.spin_max_price.setDecimals(0)
        self.spin_max_price.setSpecialValueText("Any")
        row2.addWidget(self.spin_max_price)
        price_layout.addLayout(row2)
        layout.addWidget(price_box)

        # ── Condition filter ──
        cond_box = QGroupBox("Condition")
        cond_layout = QVBoxLayout(cond_box)
        cond_layout.setSpacing(4)

        self.cond_checks: dict[Condition, QCheckBox] = {}
        for cond in [
            Condition.NEW, Condition.LIKE_NEW, Condition.GOOD,
            Condition.USED, Condition.FOR_PARTS, Condition.UNKNOWN,
        ]:
            cb = QCheckBox(cond.value)
            cb.setChecked(True)
            color = CONDITION_COLORS.get(cond, TEXT_MUTED)
            cb.setStyleSheet(f"QCheckBox {{ color: {color}; }}")
            self.cond_checks[cond] = cb
            cond_layout.addWidget(cb)
        layout.addWidget(cond_box)

        # ── Sources ──
        src_box = QGroupBox("Sources")
        src_layout = QVBoxLayout(src_box)
        src_layout.setSpacing(4)

        self.source_checks: dict[str, QCheckBox] = {}
        for site, default in self.config.get("enabled_sites", {}).items():
            label = {
                "olx":        "OLX.pt",
                "custojusto": "CustoJusto.pt",
                "ebay":       "eBay.pt",
                "backmarket": "BackMarket.pt",
                "facebook":   "Facebook Marketplace",
            }.get(site, site)
            cb = QCheckBox(label)
            cb.setChecked(default)
            color = SOURCE_COLORS.get(label, TEXT)
            cb.setStyleSheet(f"QCheckBox {{ color: {color}; }}")
            self.source_checks[site] = cb
            src_layout.addWidget(cb)
        layout.addWidget(src_box)

        # ── Location preference ──
        loc_box = QGroupBox("Location")
        loc_layout = QVBoxLayout(loc_box)
        self.chk_prefer_local = QCheckBox("Prefer Porto / Aveiro")
        self.chk_prefer_local.setChecked(True)
        self.chk_prefer_local.setToolTip(
            "Items near Porto/Aveiro get a higher deal score.\n"
            "Others still appear but rank lower."
        )
        loc_layout.addWidget(self.chk_prefer_local)
        layout.addWidget(loc_box)

        layout.addStretch()

        # Settings button
        self.btn_settings = QPushButton("⚙  Settings")
        layout.addWidget(self.btn_settings)

        return scroll

    # ── Main panel (search bar + table) ──

    def _build_main_panel(self) -> QWidget:
        panel  = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        # ── Top toolbar ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.cmb_category = QComboBox()
        self.cmb_category.addItems(list(CATEGORY_SEARCHES.keys()))
        self.cmb_category.setCurrentText(
            self.config.get("last_category", "All PC & Laptops")
        )
        self.cmb_category.setFixedWidth(200)
        toolbar.addWidget(self.cmb_category)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(
            "Custom keyword override  (leave blank to use category)"
        )
        self.txt_search.setText(self.config.get("last_query", ""))
        toolbar.addWidget(self.txt_search, 1)

        self.btn_scan = QPushButton("▶  Scan")
        self.btn_scan.setObjectName("btnScan")
        self.btn_scan.setFixedWidth(100)
        toolbar.addWidget(self.btn_scan)

        self.btn_stop = QPushButton("■  Stop")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setFixedWidth(80)
        self.btn_stop.setEnabled(False)
        toolbar.addWidget(self.btn_stop)

        self.btn_export = QPushButton("⬇  Export CSV")
        self.btn_export.setFixedWidth(120)
        toolbar.addWidget(self.btn_export)

        layout.addLayout(toolbar)

        # ── Progress ──
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        # ── Results header row ──
        results_header = QHBoxLayout()
        self.lbl_results_count = QLabel("No results yet")
        self.lbl_results_count.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        results_header.addWidget(self.lbl_results_count)
        results_header.addStretch()

        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("🔍  Filter results…")
        self.txt_filter.setFixedWidth(200)
        results_header.addWidget(self.txt_filter)
        layout.addLayout(results_header)

        # ── Table ──
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Score", "Title", "Price", "Condition", "Location", "Source", ""
        ])
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(self.COL_SCORE,  QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(self.COL_TITLE,  QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(self.COL_PRICE,  QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(self.COL_COND,   QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(self.COL_LOC,    QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(self.COL_SOURCE, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(self.COL_LINK,   QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(self.COL_SCORE,  68)
        self.table.setColumnWidth(self.COL_PRICE,  80)
        self.table.setColumnWidth(self.COL_COND,  110)
        self.table.setColumnWidth(self.COL_LOC,   150)
        self.table.setColumnWidth(self.COL_SOURCE,120)
        self.table.setColumnWidth(self.COL_LINK,   70)
        self.table.verticalHeader().setDefaultSectionSize(42)

        layout.addWidget(self.table)
        return panel

    # ── Signal wiring ──────────────────────────────────────────

    def _connect_signals(self):
        self.btn_scan.clicked.connect(self._start_scan)
        self.btn_stop.clicked.connect(self._stop_scan)
        self.btn_export.clicked.connect(self._export_csv)
        self.btn_settings.clicked.connect(self._open_settings)
        self.txt_filter.textChanged.connect(self._apply_local_filter)
        self.txt_search.returnPressed.connect(self._start_scan)

    # ── Scan logic ─────────────────────────────────────────────

    def _start_scan(self):
        # Build query
        custom = self.txt_search.text().strip()
        if custom:
            query = custom
        else:
            cat    = self.cmb_category.currentText()
            terms  = CATEGORY_SEARCHES.get(cat, [])
            query  = terms[0] if terms else cat

        if not query:
            QMessageBox.information(self, "No Query",
                                    "Enter a search term or select a category.")
            return

        # Update config with enabled sites
        for key, cb in self.source_checks.items():
            self.config.setdefault("enabled_sites", {})[key] = cb.isChecked()

        # Location weight
        if not self.chk_prefer_local.isChecked():
            self.config.setdefault("weights", {})["location"] = 0.0

        # Filters
        selected_conds = [
            cond for cond, cb in self.cond_checks.items() if cb.isChecked()
        ]
        filters = {
            "max_price":  self.spin_max_price.value() or None,
            "min_price":  self.spin_min_price.value() or None,
            "conditions": selected_conds if selected_conds else None,
        }

        # Save last query
        self.config["last_query"]    = custom
        self.config["last_category"] = self.cmb_category.currentText()
        save_config(self.config)

        # UI state
        self.btn_scan.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress.setValue(0)
        self.table.setRowCount(0)
        self._listings.clear()
        self.lbl_results_count.setText("Scanning…")

        # Start worker
        self._worker = ScraperWorker(query, self.config, filters, parent=self)
        self._worker.site_done.connect(self._on_site_done)
        self._worker.status_msg.connect(self._on_status_msg)
        self._worker.all_done.connect(self._on_all_done)
        self._worker.start()

    def _stop_scan(self):
        if self._worker:
            self._worker.abort()
        self.btn_stop.setEnabled(False)
        self.btn_scan.setEnabled(True)
        self.lbl_status.setText("Stopped by user")

    # ── Worker callbacks ───────────────────────────────────────

    def _on_site_done(self, site: str, count: int, pct: int):
        self.progress.setValue(pct)
        color = SOURCE_COLORS.get(site, TEXT)
        self.lbl_status.setText(
            f"<span style='color:{color}'>{site}</span> → {count} listings  ({pct}%)"
        )

    def _on_status_msg(self, msg: str):
        self.lbl_status.setText(msg)

    def _on_all_done(self, listings: List[Listing]):
        self._listings = listings
        self.progress.setValue(100)
        self.btn_scan.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_last_scan.setText(
            f"Last scan: {datetime.now().strftime('%H:%M:%S')}"
        )
        self._populate_table(listings)

    # ── Table population ───────────────────────────────────────

    def _populate_table(self, listings: List[Listing]):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for row_idx, lst in enumerate(listings):
            self.table.insertRow(row_idx)
            self._set_row(row_idx, lst)

        self.table.setSortingEnabled(True)
        self.lbl_results_count.setText(
            f"{len(listings)} listing{'s' if len(listings) != 1 else ''} found"
        )

    def _set_row(self, row: int, lst: Listing):
        rh = self.table.verticalHeader()
        rh.setSectionResizeMode(row, QHeaderView.ResizeMode.Fixed)

        # ── Score ──
        score_item = QTableWidgetItem()
        score_item.setData(Qt.ItemDataRole.DisplayRole, lst.score_pct)
        score_item.setTextAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        color = self._score_color(lst.score_pct)
        score_item.setForeground(QColor(color))
        score_item.setFont(self._bold_font(14))
        self.table.setItem(row, self.COL_SCORE, score_item)

        # ── Title ──
        title_item = QTableWidgetItem(lst.title)
        title_item.setToolTip(lst.title)
        self.table.setItem(row, self.COL_TITLE, title_item)

        # ── Price ──
        price_item = QTableWidgetItem()
        price_item.setData(Qt.ItemDataRole.DisplayRole, lst.price if lst.price > 0 else 0)
        price_item.setText(lst.price_display)
        price_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        price_item.setFont(self._bold_font(13))
        price_item.setForeground(QColor(SUCCESS if lst.price > 0 else TEXT_MUTED))
        self.table.setItem(row, self.COL_PRICE, price_item)

        # ── Condition ──
        cond_item = QTableWidgetItem(lst.condition.value)
        cond_item.setForeground(QColor(CONDITION_COLORS.get(lst.condition, TEXT_MUTED)))
        self.table.setItem(row, self.COL_COND, cond_item)

        # ── Location ──
        loc_text  = f"{lst.location_flag}  {lst.location}" if lst.location else "—"
        loc_item  = QTableWidgetItem(loc_text)
        loc_item.setForeground(
            QColor(ACCENT2 if lst.is_near_porto_aveiro else TEXT_MUTED)
        )
        self.table.setItem(row, self.COL_LOC, loc_item)

        # ── Source ──
        src_item = QTableWidgetItem(lst.source)
        src_item.setForeground(QColor(SOURCE_COLORS.get(lst.source, TEXT)))
        src_item.setFont(self._bold_font(11))
        self.table.setItem(row, self.COL_SOURCE, src_item)

        # ── Open link button ──
        if lst.url:
            btn = QPushButton("Open ↗")
            btn.setObjectName("btnOpen")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda _, u=lst.url: QDesktopServices.openUrl(QUrl(u)))
            self.table.setCellWidget(row, self.COL_LINK, btn)

    # ── Local real-time filter ─────────────────────────────────

    def _apply_local_filter(self, text: str):
        if not self._listings:
            return
        kw = text.lower().strip()
        filtered = (
            [l for l in self._listings if kw in l.title.lower()]
            if kw else self._listings
        )
        self._populate_table(filtered)

    # ── Export ─────────────────────────────────────────────────

    def _export_csv(self):
        if not self._listings:
            QMessageBox.information(self, "No Data", "Run a scan first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "tech_deals.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Score", "Title", "Price (€)", "Condition",
                    "Location", "Source", "URL"
                ])
                for l in self._listings:
                    writer.writerow([
                        l.score_pct, l.title, l.price,
                        l.condition.value, l.location, l.source, l.url
                    ])
            QMessageBox.information(self, "Exported",
                                    f"Saved {len(self._listings)} listings to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))

    # ── Settings ───────────────────────────────────────────────

    def _open_settings(self):
        dlg = SettingsDialog(self.config, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Refresh source checkboxes in case FB was enabled
            for key, cb in self.source_checks.items():
                cb.setChecked(self.config.get("enabled_sites", {}).get(key, False))

    # ── Helpers ────────────────────────────────────────────────

    @staticmethod
    def _score_color(score: int) -> str:
        for threshold, color in sorted(SCORE_COLORS.items(), reverse=True):
            if score >= threshold:
                return color
        return DANGER

    @staticmethod
    def _bold_font(size: int = 13) -> QFont:
        f = QFont()
        f.setPointSize(size)
        f.setWeight(QFont.Weight.Bold)
        return f

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.abort()
            self._worker.wait(2000)
        save_config(self.config)
        event.accept()


# ─────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Break Point")
    app.setStyleSheet(STYLE)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
