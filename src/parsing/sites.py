from parsing.gumtreeza import GumtreeZa
from parsing.kolesakz import KolesaKz
from parsing.md999 import MD999

SITES = {
    "999.md": {
        "url": "https://999.md",
        "search_url": "https://999.md/ru/search?query=",
        "class": MD999,
        "structure": {
            "category": True, "subcategory": True, "subsubcategory": True
        },
        "modes": {
                "category": True,
                "query": True,
        }
    },
    "kolesa.kz": {
        "url": "https://kolesa.kz",
        "search_url": "https://kolesa.kz/cars/?_txt_=",
        "class": KolesaKz,
        "structure": {
            "category": True, "subcategory": True
        },
        "modes": {
                "category": True,
                "query": True,
        }
    },
    "gumtree.co.za": {
        "url": "https://www.gumtree.co.za/",
        "search_url": "https://www.gumtree.co.za/s-all-the-ads/v1b0p1?q=",
        "class": GumtreeZa,
        "structure": {
            "category": False, "subcategory": False
        },
        "modes": {
                "category": False,
                "query": True,
        }
    }
}
