import json
import uuid

from aiogram import Router, types, F
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Button
from database.orm_query import get_sites_buttons
from handlers.utils import default_site_selection
from kbds.reply import get_inline_keyboard

from parsing.sites import SITES
from parsing.utils import normalize_url

user_private_router = Router()


class CategoryParsingStates(StatesGroup):
    subcategory = State()
    subsubcategory = State()
    parsing_in_progress = State()


@user_private_router.message(
    or_f(
        Command("parsing"),
        (F.text.lower().contains("💼 парсинг по категориям")),
    )
)
async def select_site(message: types.Message, session: AsyncSession, redis: Redis):
    await default_site_selection(message, session, redis, "category")


@user_private_router.callback_query(or_f(F.data.startswith("category_site_")))
async def select_category(
    callback_query: types.CallbackQuery, state: FSMContext, session: AsyncSession, redis: Redis
):
    button_id = callback_query.data.split("_")[2]
    button = (await session.get(Button, int(button_id)))
    button_url = button.url

    site = SITES[button.name]
    parser_class = site.get("class")
    parser = parser_class()
    structure = site.get("structure")
    if structure.get("subcategory"):
        await redis.setex(button_id, 60, button_url)

        categories = (
            json.loads(await redis.get(button_url))
            if await redis.exists(button_url)
            else await parser.parse_categories(button_url)
        )
        if not await redis.exists(button_url):
            await redis.setex(button_url, 60, json.dumps(categories))

        inline_buttons = []
        for cat_name, cat_url in categories.items():
            cat_id = uuid.uuid4()
            inline_buttons.append(
                InlineKeyboardButton(
                    text=cat_name, callback_data=f"category_{cat_id}"
                )
            )
            await redis.setex(str(cat_id), 60, cat_url)
        await state.set_data({"parser": parser, "structure": structure})

        await state.set_state(CategoryParsingStates.subcategory)
        inline_keyboard = get_inline_keyboard(inline_buttons, in_row=3)
        await callback_query.message.answer(
            "Выберите категорию для парсинга", reply_markup=inline_keyboard
        )
    else:
        await callback_query.message.answer(
            "обработано"
        )
    await callback_query.answer()


@user_private_router.callback_query(or_f(F.data.startswith("category_")))
async def select_subcategory(callback_query: types.CallbackQuery, state: FSMContext, redis: Redis):
    data = await state.get_data()
    structure = data.get("structure")
    parser = data.get("parser")
    category_id = callback_query.data.split("_")[1]
    category_url = f"{await redis.get(category_id)}"
    subcategories = (
        json.loads(await redis.get(category_url))
        if await redis.exists(category_url)
        else await parser.parse_subcategories(category_url)
    )
    if not await redis.exists(category_url):
        await redis.setex(category_url, 60, json.dumps(subcategories))

    inline_buttons = []
    for cat_name, cat_dict in subcategories.items():
        subcat_id = uuid.uuid4()
        callback_data = f"subcategory_{subcat_id}" if structure.get("subsubcategory") else f"parsing_{subcat_id}"
        inline_buttons.append(
            InlineKeyboardButton(
                text=cat_name, callback_data=callback_data
            )
        )
        await redis.setex(str(subcat_id), 60, json.dumps(cat_dict))
    await state.set_state(CategoryParsingStates.subsubcategory if structure.get("subsubcategory") else CategoryParsingStates.parsing_in_progress)
    inline_keyboard = get_inline_keyboard(inline_buttons, in_row=3)
    await callback_query.message.answer(
        "Выберите подкатегорию для парсинга", reply_markup=inline_keyboard
    )
    await callback_query.answer()



@user_private_router.callback_query(or_f(F.data.startswith("subcategory_")))
async def select_subsubcategory(
    callback_query: types.CallbackQuery, state: FSMContext, redis: Redis
):
    data = await state.get_data()
    parser = data.get("parser")
    subcategory_id = callback_query.data.split("_")[1]
    subcategory_data_json = await redis.get(subcategory_id)

    subcategory_data = json.loads(subcategory_data_json)

    await state.set_state(CategoryParsingStates.parsing_in_progress)
    inline_buttons = []
    for subcat_name, subcat_url in subcategory_data.items():
        subcat_uuid = uuid.uuid4()
        inline_buttons.append(
            InlineKeyboardButton(
                text=subcat_name, callback_data=f"parsing_{subcat_uuid}"
            )
        )
        await redis.setex(str(subcat_uuid), 60, subcat_url)

    inline_keyboard = get_inline_keyboard(inline_buttons, in_row=3)

    await callback_query.message.answer(
        "Выберите подкатегорию для дальнейшего действия:",
        reply_markup=inline_keyboard,
    )
    await callback_query.answer()


@user_private_router.callback_query(or_f(F.data.startswith("parsing_")))
async def parse_products(callback_query: types.CallbackQuery, state: FSMContext, redis: Redis):
    data = await state.get_data()
    parser = data.get("parser")
    last_category_id = callback_query.data.split("_")[1]
    last_category = await redis.get(last_category_id)
    last_category_url = normalize_url(last_category)

    await parser.parse_category_products(
        last_category_url, callback_query=callback_query
    )
    await state.clear()
    await callback_query.answer()
