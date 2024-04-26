import json
import uuid

from aiogram import Router, types, F
from aiogram.filters import Command, or_f
from aiogram.types import InlineKeyboardButton
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Button
from database.orm_query import get_sites_buttons
from handlers.utils import default_site_selection
from kbds.reply import get_inline_keyboard
from parsing.parsing import parse_subcategories, parse_categories, parse_category_products

user_private_router = Router()


@user_private_router.message(
    or_f(
        Command("parsing"),
        (F.text.lower().contains("💼 парсинг по категориям"))
    )
)
async def parsing(message: types.Message, session: AsyncSession, redis: Redis):
    await default_site_selection(message, session, redis, "category")


@user_private_router.callback_query(or_f(
    F.data.startswith("category_site_")
))
async def select_site(callback_query: types.CallbackQuery, session: AsyncSession, redis: Redis):
    button_id = callback_query.data.split("_")[2]
    button_url = await redis.get(button_id)
    if not button_url:
        button_url = (await session.get(Button, int(button_id))).url
        await redis.setex(button_id, 60, button_url)

    categories = json.loads(await redis.get(button_url)) if await redis.exists(button_url) else await parse_categories(
        button_url)
    if not await redis.exists(button_url):
        await redis.setex(button_url, 60, json.dumps(categories))

    inline_buttons = []
    for cat_name, cat_url in categories.items():
        cat_id = uuid.uuid4()
        inline_buttons.append(InlineKeyboardButton(text=cat_name, callback_data=f"category_{cat_id}"))
        await redis.setex(str(cat_id), 60, cat_url)
    inline_keyboard = get_inline_keyboard(inline_buttons, in_row=3)
    await callback_query.message.answer("Выберите категорию для парсинга", reply_markup=inline_keyboard)
    await callback_query.answer()


@user_private_router.callback_query(or_f(
    F.data.startswith("category_")
))
async def select_category(callback_query: types.CallbackQuery, redis: Redis):
    category_id = callback_query.data.split("_")[1]
    category_url = f"{await redis.get(category_id)}"
    categories = json.loads(await redis.get(category_url)) if await redis.exists(
        category_url) else await parse_subcategories(category_url)
    if not await redis.exists(category_url):
        await redis.setex(category_url, 60, json.dumps(categories))

    inline_buttons = []
    for cat_name, cat_dict in categories.items():
        subcat_id = uuid.uuid4()
        inline_buttons.append(InlineKeyboardButton(text=cat_name, callback_data=f"subcategory_{subcat_id}"))
        await redis.setex(str(subcat_id), 60, json.dumps(cat_dict))
    inline_keyboard = get_inline_keyboard(inline_buttons, in_row=3)
    await callback_query.message.answer("Выберите подкатегорию для парсинга", reply_markup=inline_keyboard)
    await callback_query.answer()


@user_private_router.callback_query(or_f(
    F.data.startswith("subcategory_")
))
async def select_subcategory(callback_query: types.CallbackQuery, redis: Redis):
    subcategory_id = callback_query.data.split("_")[1]
    subcategory_data_json = await redis.get(subcategory_id)

    # Проверка, есть ли данные в кэше
    if subcategory_data_json:
        subcategory_data = json.loads(subcategory_data_json)
    else:
        subcategory_data = await parse_subcategories("some_url")
        await redis.setex(subcategory_id, 60, json.dumps(subcategory_data))

    inline_buttons = []
    for subcat_name, subcat_url in subcategory_data.items():
        subcat_uuid = uuid.uuid4()
        inline_buttons.append(InlineKeyboardButton(text=subcat_name, callback_data=f"finalСhoice_{subcat_uuid}"))
        await redis.setex(str(subcat_uuid), 60, subcat_url)

    inline_keyboard = get_inline_keyboard(inline_buttons, in_row=3)

    await callback_query.message.answer(
        "Выберите подкатегорию для дальнейшего действия:",
        reply_markup=inline_keyboard
    )
    await callback_query.answer()


@user_private_router.callback_query(or_f(
    F.data.startswith("finalСhoice_")
))
async def parse_products(callback_query: types.CallbackQuery, redis: Redis):
    subsubcategory_id = callback_query.data.split("_")[1]
    subsubcategory_url = f"https://999.md{await redis.get(subsubcategory_id)}"
    await parse_category_products(subsubcategory_url, callback_query=callback_query)
    await callback_query.answer()
