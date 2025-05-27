# catalog_manager.py  • v1.0
import json, pathlib
CAT_FILE = pathlib.Path("catalogs_data.json")

DEFAULTS = {
    "organizations": ["ООО «Рост Золото»", "ИП Смирнова", "ЗАО «Злато»"],
    "contragents" :  ["ООО «Алмаз»", "Zlato Ltd.", "ИП Королёв"],
    "cities"      :  ["Таганрог", "Ростов", "Краснодар", "Сочи"],
    "warehouses"  :  ["Материалы","Металлы производства","Металлы давальческие",
                      "Вставок","Готовой продукции"],
    "articles"    :  [],     # динамические артикула
}

def _load():
    if CAT_FILE.exists():
        try:
            return json.loads(CAT_FILE.read_text("utf-8"))
        except Exception:
            pass
    return DEFAULTS.copy()

_data = _load()

def save():
    CAT_FILE.write_text(json.dumps(_data, ensure_ascii=False, indent=2),
                        encoding="utf-8")

def get(category: str) -> list[str]:
    return _data.get(category, [])

def add(category: str, value: str) -> bool:
    lst = _data.setdefault(category, [])
    if value and value not in lst:
        lst.append(value)
        save()
        return True
    return False
