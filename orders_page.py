# orders_page.py  • v1.0
import uuid, json, pathlib
from datetime import datetime
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont, QColor, QBrush
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QFormLayout, QComboBox, QDateEdit,
    QSpinBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem, QPushButton,
    QMessageBox, QHeaderView, QCheckBox, QTabWidget, QHBoxLayout,
    QLineEdit, QCompleter, QTreeWidget, QTreeWidgetItem
)

from catalogs import metals, hallmarks, colors, INSERTS, NOMENCLATURE
from catalog_manager import get as cat_get, add as cat_add
from production_docs import process_new_order


STATUS_COLORS = {
    "Новый":        "#3b82f6",
    "В работе":     "#fbbf24",
    "Не пролилось": "#ef4444",
    "Дозаказ":      "#8b5cf6",
    "Готов":        "#10b981",
}

TREE_CSS = """
QTreeWidget{background:#ffffff;border:1px solid #d1d5db;font-size:14px;}
QTreeWidget::item{padding:4px 8px;border-bottom:1px solid #e5e7eb;}
QTreeWidget::item:selected{background:#2563eb;color:#ffffff;}
QTreeWidget::item:hover:!selected{background:rgba(37,99,235,0.30);}
"""

class OrdersPage(QWidget):
    COLS = ["Артикул","Наим.","Металл","Проба","Цвет","Вставки",
            "Размер","Кол-во","Вес, г","Комментарий"]

    def __init__(self):
        super().__init__()
        self._ui()

    # ───────────── UI ─────────────
    def _ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        self.tabs = QTabWidget(); outer.addWidget(self.tabs)

        # ---------- «Новый заказ» ----------
        self.frm_new = QWidget()
        v = QVBoxLayout(self.frm_new); v.setContentsMargins(40,30,40,30)

        hdr = QLabel("Заказ клиента"); hdr.setFont(QFont("Arial",22,QFont.Bold))
        v.addWidget(hdr)

        form = QFormLayout(); v.addLayout(form)

        self.ed_num = QLabel(datetime.now().strftime("%Y%m%d-")+uuid.uuid4().hex[:4])
        self.d_date = QDateEdit(datetime.now()); self.d_date.setCalendarPopup(True)

        self.c_org   = QComboBox(); self._setup_combo(self.c_org, "organizations")
        self.c_contr = QComboBox(); self._setup_combo(self.c_contr, "contragents")
        self.c_city  = QComboBox(); self._setup_combo(self.c_city, "cities")
        self.c_wh    = QComboBox(); self._setup_combo(self.c_wh, "warehouses")

        self.chk_ok  = QCheckBox("Согласовано")
        self.chk_res = QCheckBox("Резервировать товары")

        for lab,w in [("Номер",self.ed_num),("Дата",self.d_date),
                      ("Организация",self.c_org),("Контрагент",self.c_contr),
                      ("Город",self.c_city),("Склад",self.c_wh)]:
            form.addRow(lab,w)
        form.addRow(self.chk_ok); form.addRow(self.chk_res)

        # ---------- таблица товаров ----------
        self.tbl = QTableWidget(0,len(self.COLS))
        self.tbl.setHorizontalHeaderLabels(self.COLS)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        v.addWidget(self.tbl)
        self._add_row()

        # ---------- кнопки ----------
        btns = QHBoxLayout()
        for (txt,slot) in [
            ("+ строка", self._add_row), ("- строка", self._remove_row),
            ("Новый заказ", self._new_order), ("Провести", self._post),
            ("Провести и закрыть", self._post_close),
        ]:
            b = QPushButton(txt); b.clicked.connect(slot); btns.addWidget(b)
        v.addLayout(btns)

        self.tabs.addTab(self.frm_new,"Новый заказ")

        # ---------- «Заказы» ----------
        self.tree_orders = QTreeWidget()
        self.tree_orders.setHeaderLabels(
            ["№ заказа","Дата","Контрагент","Позиций","Вес, г","Статус"]
        )
        self.tree_orders.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree_orders.setStyleSheet(TREE_CSS)
        self.tabs.addTab(self.tree_orders,"Заказы")

    # ───────────── справочники в ComboBox ─────────────
    def _setup_combo(self, combo: QComboBox, category: str):
        combo.addItems(cat_get(category))
        combo.setEditable(True); combo.setInsertPolicy(QComboBox.NoInsert)
        combo.setCompleter(QCompleter(combo.model(), self))

        def maybe_add():
            val = combo.currentText().strip()
            if val and val not in cat_get(category):
                if QMessageBox.question(self,"Добавить?",
                    f'"{val}" не найдено в справочнике.\nДобавить?')==QMessageBox.Yes:
                    cat_add(category,val)
                    combo.addItem(val); combo.setCurrentText(val)
        combo.lineEdit().editingFinished.connect(maybe_add)

    # ───────────── строки таблицы ─────────────
    def _add_row(self):
        r = self.tbl.rowCount(); self.tbl.insertRow(r)

        art = QComboBox();  art.addItems(NOMENCLATURE.keys())
        art.setEditable(True); art.setInsertPolicy(QComboBox.NoInsert)
        art.setCompleter(QCompleter(art.model(), self))

        name  = QTableWidgetItem("")
        metal = QComboBox();  metal.addItems(metals())
        probe = QComboBox();  probe.addItems(hallmarks(metal.currentText()))
        color = QComboBox();  color.addItems(colors(metal.currentText()))
        ins   = QComboBox();  ins.addItems(INSERTS)

        size = QDoubleSpinBox(); size.setDecimals(1); size.setSingleStep(0.5)
        size.setRange(0.5,30.0); size.setValue(17.0)
        qty = QSpinBox(); qty.setRange(1,999); qty.setValue(1)
        wgt = QDoubleSpinBox(); wgt.setDecimals(3); wgt.setMaximum(9999)
        cmnt= QLineEdit()

        for c,w in enumerate([art,name,metal,probe,color,ins,size,qty,wgt,cmnt]):
            setter = self.tbl.setCellWidget if isinstance(
                     w,(QComboBox,QSpinBox,QDoubleSpinBox,QLineEdit)) else self.tbl.setItem
            setter(r,c,w)

        # авто-заполнение
        def fill():
            card = NOMENCLATURE.get(art.currentText(),{})
            name.setText(card.get("name",""))
            wgt.setValue(round(card.get("w",0)*qty.value(),3))
        def upd_probe_color():
            m = metal.currentText()
            probe.clear(); probe.addItems(hallmarks(m))
            color.clear(); color.addItems(colors(m))
        art.currentIndexChanged.connect(fill)
        metal.currentIndexChanged.connect(upd_probe_color)
        qty.valueChanged.connect(fill)
        fill()

    def _remove_row(self):
        r = self.tbl.currentRow()
        if r >= 0: self.tbl.removeRow(r)

    # ───────────── JSON заказа ─────────────
    def _collect(self)->dict:
        head = dict(
            num   = self.ed_num.text(),
            date  = self.d_date.date().toString("yyyy-MM-dd"),
            org   = self.c_org.currentText(),
            contr = self.c_contr.currentText(),
            city  = self.c_city.currentText(),
            wh    = self.c_wh.currentText(),
            stage = "Новый",
        )
        rows=[]
        for r in range(self.tbl.rowCount()):
            if self.tbl.cellWidget(r,7).value()<=0: continue
            rows.append(dict(
                article  = self.tbl.cellWidget(r,0).currentText(),
                name     = self.tbl.item(r,1).text(),
                metal    = self.tbl.cellWidget(r,2).currentText(),
                hallmark = self.tbl.cellWidget(r,3).currentText(),
                color    = self.tbl.cellWidget(r,4).currentText(),
                inserts  = self.tbl.cellWidget(r,5).currentText(),
                size     = self.tbl.cellWidget(r,6).value(),
                qty      = self.tbl.cellWidget(r,7).value(),
                weight   = float(self.tbl.cellWidget(r,8).value()),
                comment  = self.tbl.cellWidget(r,9).text(),
            ))
        return {"head":head,"rows":rows}

    # ───────────── проведение ─────────────
    def _post(self):
        order_json = self._collect()
        process_new_order(order_json)
        self._append_to_list(order_json)
        QMessageBox.information(self,"Готово",
            f"Заказ {order_json['head']['num']} проведён")

    def _post_close(self):
        self._post(); self.tabs.setCurrentIndex(1)

    # ───────────── вывод в дерево ─────────────
    def _append_to_list(self, order_json):
        head, rows = order_json["head"], order_json["rows"]
        qty = sum(r["qty"] for r in rows)
        wgt = sum(r["weight"] for r in rows)
        stage = head.get("stage","Новый")

        item = QTreeWidgetItem(self.tree_orders, [
            head["num"], head["date"], head["contr"],
            str(qty), f"{wgt:.3f}", stage
        ])

        bg = STATUS_COLORS.get(stage,"#e5e7eb")
        text = "#ffffff" if bg!= "#e5e7eb" else "#000000"
        for c in range(item.columnCount()):
            item.setBackground(c, QBrush(QColor(bg)))
            item.setForeground(c, QBrush(QColor(text)))
        item.setExpanded(True)

        for r in rows:
            QTreeWidgetItem(item, [
                f"{r['article']} (р-р {r['size']})",
                "", r["metal"], str(r["qty"]),
                f"{r['weight']:.3f}", ""
            ])

    # ───────────── вспомогательно ─────────────
    def _new_order(self):
        self.ed_num.setText(datetime.now().strftime("%Y%m%d-")+uuid.uuid4().hex[:4])
        self.tbl.setRowCount(0); self._add_row()
        self.tabs.setCurrentIndex(0)
