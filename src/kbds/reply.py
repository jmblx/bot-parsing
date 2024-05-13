from aiogram.types import (
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from config import ADMIN_LIST


def get_keyboard(
    *btns: str,
    placeholder: str = None,
    request_contact: int = None,
    request_location: int = None,
    sizes: tuple[int] = (2,),
):
    """
    Parameters request_contact and request_location must be as indexes of btns args for buttons you need.
    Example:
    get_keyboard(
            "Меню",
            "О магазине",
            "Варианты оплаты",
            "Варианты доставки",
            "Отправить номер телефона",
            placeholder="Что вас интересует?",
            request_contact=4,
            sizes=(2, 2, 1)
        )
    """
    keyboard = ReplyKeyboardBuilder()

    for index, text in enumerate(btns, start=0):

        if request_contact and request_contact == index:
            keyboard.add(KeyboardButton(text=text, request_contact=True))

        elif request_location == index:
            keyboard.add(KeyboardButton(text=text, request_location=True))
        else:
            keyboard.add(KeyboardButton(text=text))

    return keyboard.adjust(*sizes).as_markup(
        resize_keyboard=True, input_field_placeholder=placeholder
    )


def get_inline_keyboard(buttons: list, in_row: int = 2):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(*buttons)
    return keyboard.adjust(in_row).as_markup()


default_add_kb = get_keyboard(
    "назад", "отмена", placeholder="Меню добавления рецепта", sizes=(1, 2)
)

change_type_kb = get_keyboard("коктейль", "твёрдое блюдо", sizes=(1, 1))


async def admin_check(message):
    return str(message.from_user.id) in ADMIN_LIST


def get_main_kb():
    return get_keyboard(
        "💼 Парсинг по категориям",
        "🔎 Парсинг по запросу",
        placeholder="Выберите действие",
        sizes=(1, 2),
    )


def get_admin_keyboard(cocktail_id, user_id):
    is_admin = str(user_id) in ADMIN_LIST
    keyboard = InlineKeyboardBuilder()

    if is_admin:
        keyboard.add(
            InlineKeyboardButton(
                text="Название", callback_data=f"edit_name_{cocktail_id}"
            ),
            InlineKeyboardButton(
                text="Ингредиенты",
                callback_data=f"edit_ingredients_{cocktail_id}",
            ),
            InlineKeyboardButton(
                text="Описание",
                callback_data=f"edit_description_{cocktail_id}",
            ),
            InlineKeyboardButton(
                text="Тип", callback_data=f"edit_type_{cocktail_id}"
            ),
            InlineKeyboardButton(
                text="Картинка", callback_data=f"edit_image_{cocktail_id}"
            ),
            InlineKeyboardButton(
                text="Сохранить изменения", callback_data=f"save_{cocktail_id}"
            ),
            InlineKeyboardButton(
                text="Удалить рецепт", callback_data=f"delete_{cocktail_id}"
            ),
            InlineKeyboardButton(
                text="Отмена", callback_data="cancel_editing"
            ),
        )
    return keyboard.adjust(2).as_markup()  # Настройте макет под ваши нужды


def change_type_kb(cocktail_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="Коктейль", callback_data=f"change_type_{cocktail_id}_True"
        ),
        InlineKeyboardButton(
            text="Твёрдое блюдо",
            callback_data=f"change_type_{cocktail_id}_False",
        ),
    )
    return keyboard.adjust(2).as_markup()
