from parsing.kolesakz import KolesaKz
from parsing.md999 import MD999

SITES = {
    "999.md": {
        "url": "https://999.md",
        "class": MD999,
        "structure": {
            "category": True, "subcategory": True, "subsubcategory": True
        }
    },
    "kolesa.kz": {
        "url": "https://kolesa.kz",
        "class": KolesaKz,
        "structure": {
            "category": True, "subcategory": True
        }
    }
}
