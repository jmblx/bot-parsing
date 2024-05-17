from parsing.kolesakz import KolesaKz
from parsing.md999 import MD999

SITES = {
    "999.md": {
        "url": "https://999.md",
        "search_url": "https://999.md/ru/search?query=",
        "class": MD999,
        "structure": {
            "category": True, "subcategory": True, "subsubcategory": True
        }
    },
    "kolesa.kz": {
        "url": "https://kolesa.kz",
        "search_url": "https://kolesa.kz/cars/?_txt_=",
        "class": KolesaKz,
        "structure": {
            "category": True, "subcategory": True
        }
    }
}
