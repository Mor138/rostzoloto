# orders_page.py • v0.8.1  (контрагент = орг-ия, клиент = город)
# ─────────────────────────────────────────────────────────────────────────
import uuid, json
from datetime import datetime

from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QFormLayout, QComboBox, QDateEdit,
    QSpinBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem, QPushButton,
    QMessageBox, QHeaderView, QCheckBox, QTabWidget, QHBoxLayout, QLineEdit
)

from catalogs import (
    ORGANIZATIONS,
    metals, hallmarks, colors,
    INSERTS, NOMENCLATURE
)
from production_docs import process_new_order

CONTRACTS    = ["Купля-продажа"]
WAREHOUSES   = ["Основной склад"]
CLIENT_ORGS  = ["ООО «Алмаз»", "Zlato Ltd.", "ИП Королёв"]
CLIENT_CITIES= ["Таганрог", "Ростов", "Краснодар", "Сочи"]

class OrdersPage(QWidget):
    COLS = ["Артикул","Наим.","Металл","Проба","Цвет","Вставки",
            "Размер","Кол-во","Вес, г","Комментарий"]

    def __init__(self): super().__init__(); self._ui()

    # ------------------------------------------------------------------
    def _ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        self.tabs = QTabWidget(); outer.addWidget(self.tabs)

        # ===== вкладка «Новый заказ» ==================================
        self.frm_new = QWidget()
        v = QVBoxLayout(self.frm_new); v.setContentsMargins(40,30,40,30)

        hdr = QLabel("Заказ клиента"); hdr.setFont(QFont("Arial",22,QFont.Bold))
        v.addWidget(hdr)

        form = QFormLayout(); v.addLayout(form)
        self.ed_num = QLabel(datetime.now().strftime("%Y%m%d-")+uuid.uuid4().hex[:4])
        self.d_date = QDateEdit(datetime.now()); self.d_date.setCalendarPopup(True)

        self.c_org   = QComboBox(); self.c_org.addItems(ORGANIZATIONS)
        self.c_contr = QComboBox(); self.c_contr.addItems(CLIENT_ORGS)
        self.c_city  = QComboBox(); self.c_city.addItems(CLIENT_CITIES)
        self.c_ctr   = QComboBox(); self.c_ctr .addItems(CONTRACTS);  self.c_ctr.setEnabled(False)
        self.c_wh    = QComboBox(); self.c_wh  .addItems(WAREHOUSES); self.c_wh.setEnabled(False)

        self.chk_ok  = QCheckBox("Согласовано")
        self.chk_res = QCheckBox("Резервировать товары")

        for lab,w in [
            ("Номер",self.ed_num),("Дата",self.d_date),
            ("Организация",self.c_org),
            ("Контрагент",self.c_contr),
            ("Клиент",self.c_city),
            ("Договор",self.c_ctr),("Склад",self.c_wh)]:
            form.addRow(lab,w)
        form.addRow(self.chk_ok); form.addRow(self.chk_res)

        # ========== таблица товаров ===================================
        self.tbl = QTableWidget(0,len(self.COLS))
        self.tbl.setHorizontalHeaderLabels(self.COLS)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        v.addWidget(self.tbl)
        self._add_row()

        # ========== кнопки ============================================
        btns = QHBoxLayout()
        for (txt,slot) in [
            ("+ строка",self._add_row),
            ("Новый заказ",self._new_order),
            ("Провести",self._post),
            ("Провести и закрыть",self._post_close)]:
            b=QPushButton(txt); b.clicked.connect(slot); btns.addWidget(b)
        v.addLayout(btns)

        self.tabs.addTab(self.frm_new,"Новый заказ")

        # ===== вкладка «Заказы» ======================================
        self.tbl_orders = QTableWidget(0,3)
        self.tbl_orders.setHorizontalHeaderLabels(["№","Дата","Контрагент"])
        self.tbl_orders.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabs.addTab(self.tbl_orders,"Заказы")

    # ------------------------------------------------------------------
    def _new_order(self):
        self.ed_num.setText(datetime.now().strftime("%Y%m%d-")+uuid.uuid4().hex[:4])
        self.tbl.setRowCount(0); self._add_row(); self.tabs.setCurrentIndex(0)

    # ------------------------------------------------------------------
    def _add_row(self):
        r=self.tbl.rowCount(); self.tbl.insertRow(r)

        art=QComboBox(); art.addItems(NOMENCLATURE.keys())
        name=QTableWidgetItem("")
        metal=QComboBox(); metal.addItems(metals())
        probe=QComboBox(); probe.addItems(hallmarks(metal.currentText()))
        color=QComboBox(); color.addItems(colors(metal.currentText()))
        ins=QComboBox(); ins.addItems(INSERTS)

        size=QDoubleSpinBox(); size.setDecimals(1); size.setSingleStep(0.5)
        size.setRange(0.5,30.0); size.setValue(17.0)

        qty=QSpinBox(); qty.setRange(1,999); qty.setValue(1)
        wgt=QDoubleSpinBox(); wgt.setDecimals(3); wgt.setMaximum(9999)
        cmnt=QLineEdit()

        for c,w in enumerate([art,name,metal,probe,color,ins,size,qty,wgt,cmnt]):
            (self.tbl.setCellWidget if isinstance(w,(QComboBox,QSpinBox,
                                                     QDoubleSpinBox,QLineEdit))
             else self.tbl.setItem)(r,c,w)

        # авто-заполнение из каталога
        def fill():
            card=NOMENCLATURE.get(art.currentText(),{})
            name.setText(card.get("name",""))
            wgt.setValue(round(card.get("w",0)*qty.value(),3))
        def upd_probe_color():
            m=metal.currentText()
            probe.clear(); probe.addItems(hallmarks(m))
            color.clear(); color.addItems(colors(m))
        art.currentIndexChanged.connect(fill)
        metal.currentIndexChanged.connect(upd_probe_color)
        qty.valueChanged.connect(fill)
        fill()

    # ------------------------------------------------------------------
    def _collect(self)->dict:
        head=dict(num=self.ed_num.text(),
                  date=self.d_date.date().toString("yyyy-MM-dd"),
                  org=self.c_org.currentText(),
                  contragent=self.c_contr.currentText(),
                  client_city=self.c_city.currentText(),
                  contract=self.c_ctr.currentText(),
                  warehouse=self.c_wh.currentText(),
                  approved=self.chk_ok.isChecked(),
                  reserve=self.chk_res.isChecked())
        rows=[]
        for r in range(self.tbl.rowCount()):
            if self.tbl.cellWidget(r,7).value()<=0: continue
            rows.append(dict(
                article = self.tbl.cellWidget(r,0).currentText(),
                name    = self.tbl.item(r,1).text(),
                metal   = self.tbl.cellWidget(r,2).currentText(),
                hallmark= self.tbl.cellWidget(r,3).currentText(),
                color   = self.tbl.cellWidget(r,4).currentText(),
                inserts = self.tbl.cellWidget(r,5).currentText(),
                size    = self.tbl.cellWidget(r,6).value(),
                qty     = self.tbl.cellWidget(r,7).value(),
                weight  = float(self.tbl.cellWidget(r,8).value()),
                comment = self.tbl.cellWidget(r,9).text()))
        return {"head":head,"rows":rows}

    # ------------------------------------------------------------------
    def _post(self):
        order_json=self._collect()
        process_new_order(order_json)
        self._append_to_list(order_json)
        QMessageBox.information(self,"Готово",
            f"Заказ {order_json['head']['num']} проведён")

    def _post_close(self):
        self._post(); self.tabs.setCurrentIndex(1)

    def _append_to_list(self,order_json):
        r=self.tbl_orders.rowCount(); self.tbl_orders.insertRow(r)
        self.tbl_orders.setItem(r,0,QTableWidgetItem(order_json["head"]["num"]))
        self.tbl_orders.setItem(r,1,QTableWidgetItem(order_json["head"]["date"]))
        self.tbl_orders.setItem(r,2,QTableWidgetItem(order_json["head"]["contragent"]))
