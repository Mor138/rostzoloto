# catalogs_page.py  • v1.0
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QPushButton, QHBoxLayout, QMessageBox, QHeaderView
)
from catalogs         import NOMENCLATURE
from catalog_manager  import get as cat_get, add as cat_add

class CatalogsPage(QWidget):
    """Многоуровневая витрина всех справочников + поиск/добавление."""
    def __init__(self):
        super().__init__()
        self._ui()

    def _ui(self):
        v = QVBoxLayout(self); v.setContentsMargins(40,30,40,30)

        hdr = QLabel("Справочники"); hdr.setFont(QFont("Arial",22,QFont.Bold))
        v.addWidget(hdr)

        # --- поиск ---
        top = QHBoxLayout(); v.addLayout(top)
        self.ed_find = QLineEdit(); self.ed_find.setPlaceholderText("Поиск...")
        self.ed_find.textChanged.connect(self._filter)
        top.addWidget(self.ed_find,1)
        btn_add = QPushButton("Добавить"); btn_add.clicked.connect(self._add)
        top.addWidget(btn_add,0)

        # --- дерево ---
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Категория / Значение"])
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        v.addWidget(self.tree,1)
        self._fill()

    # ───────── заполнение ─────────
    def _fill(self):
        self.tree.clear()

        # корневые узлы
        roots = {}
        for cat in ["organizations", "contragents", "cities", "warehouses"]:
            roots[cat] = QTreeWidgetItem(self.tree, [cat.capitalize()])

        art_root = QTreeWidgetItem(self.tree, ["articles"])
        roots["articles"] = art_root

        # значения из JSON-справочников
        for cat in ["organizations", "contragents", "cities", "warehouses"]:
            for val in cat_get(cat):
                QTreeWidgetItem(roots[cat], [val])

        # номенклатура из catalogs.py
        for art, card in NOMENCLATURE.items():
            leaf = QTreeWidgetItem(art_root,
                                   [f"{art} — {card['name']}"])
            leaf.setToolTip(
                0, f"Вес: {card['w']} г   Метод: {card['method']}"
            )

        # раскрываем дерево
        for node in roots.values():
            node.setExpanded(True)

    # ───────── фильтр ─────────
    def _filter(self, text: str):
        text=text.lower()
        def recurse(item: QTreeWidgetItem)->bool:
            visible = False
            for i in range(item.childCount()):
                if recurse(item.child(i)): visible = True
            if not visible:
                visible = text in item.text(0).lower()
            item.setHidden(not visible)
            return visible
        for i in range(self.tree.topLevelItemCount()):
            recurse(self.tree.topLevelItem(i))

    # ───────── добавление значения ─────────
    def _add(self):
        path = self.tree.currentItem()
        if not path or path.parent():
            QMessageBox.warning(self,"Выбор категории",
                "Выберите категорию (верхний уровень) для добавления значения.")
            return
        category = path.text(0).lower()
        val = self.ed_find.text().strip()
        if not val:
            QMessageBox.warning(self,"Пустое значение","Введите текст в поле поиска.")
            return
        if cat_add(category,val):
            QTreeWidgetItem(path,[val])
            path.setExpanded(True)
            QMessageBox.information(self,"Добавлено",
                f'"{val}" добавлено в категорию «{category}».')
        else:
            QMessageBox.information(self,"Уже есть",
                f'"{val}" уже присутствует в этой категории.')
