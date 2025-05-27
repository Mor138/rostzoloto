# stock_page.py  • v0.1
import json, pathlib
from collections import defaultdict
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QMessageBox
)

from catalogs import WAREHOUSES

DATA_FILE = pathlib.Path("stock.json")


class StockPage(QWidget):
    """Простейший складской учёт на JSON-файле (заменится БД 1С)."""
    def __init__(self):
        super().__init__()
        self._ui()

    # ───────── UI ─────────
    def _ui(self):
        v = QVBoxLayout(self); v.setContentsMargins(40,30,40,30)

        hdr = QLabel("Складские остатки")
        hdr.setFont(QFont("Arial",22,QFont.Bold))
        v.addWidget(hdr)

        btn_row = QVBoxLayout()
        btn_ref = QPushButton("Обновить"); btn_ref.clicked.connect(self.refresh)
        btn_row.addWidget(btn_ref, alignment=Qt.AlignLeft)
        v.addLayout(btn_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Наименование","Qty","Вес, г"])
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        v.addWidget(self.tree,1)

        self.refresh()

    # ───────── fill ─────────
    def refresh(self):
        self.tree.clear()
        data = self._load()

        for wh_name in WAREHOUSES:
            wh_root = QTreeWidgetItem(self.tree,[wh_name,"",""])
            wh_root.setExpanded(True)
            for art, recs in data.get(wh_name, {}).items():
                qty = sum(r["qty"] for r in recs)
                wgt = sum(r["weight"] for r in recs)
                QTreeWidgetItem(wh_root,[art,str(qty),f"{wgt:.3f}"])

    # ───────── data ─────────
    def _load(self)->dict:
        if DATA_FILE.exists():
            try:
                return json.loads(DATA_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                QMessageBox.warning(self,"Ошибка чтения",str(e))
        # пустое хранилище
        return {wh:{} for wh in WAREHOUSES}
