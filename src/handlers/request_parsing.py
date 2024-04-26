from aiogram import Router, F, types
from aiogram.filters import or_f, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Button
from handlers.utils import default_site_selection
from kbds.reply import get_main_kb
from parsing.const import SITES
from parsing.parsing import parse_category_products

user_private_router = Router()


class ParsingStates(StatesGroup):
    waiting_for_request = State()
    processing_request = State()


@user_private_router.message(
    or_f(
        Command("rq_parsing"),
        (F.text.lower().contains("🔎 парсинг по запросу"))
    )
)
async def parsing(message: types.Message, session: AsyncSession, redis: Redis):
    await default_site_selection(message, session, redis, "request")


@user_private_router.callback_query(or_f(
    F.data.startswith("request_")
))
async def start_parsing_by_query(callback_query: types.CallbackQuery, state: FSMContext, redis: Redis):
    await state.set_state(ParsingStates.waiting_for_request)
    await callback_query.message.answer("Введите текст запроса для парсинга или 'отмена' для завершения.")
    await callback_query.answer()


@user_private_router.message(ParsingStates.waiting_for_request, F.text)
async def process_query_text(message: types.Message, state: FSMContext, session: AsyncSession, redis: Redis):
    query_text = message.text
    if query_text.lower() == "отмена":
        await state.clear()
        await message.answer("Запрос отменен.", reply_markup=get_main_kb())
        return

    await state.set_state(ParsingStates.processing_request)
    button_id = "1"
    button_url = await redis.get(button_id)
    if not button_url:
        button_url = (await session.get(Button, int(button_id))).url
        await redis.setex(button_id, 60 * 60, button_url)  # Кэширование на час

    await parse_category_products(f"{button_url}{query_text}", callback_query=message)
    await state.clear()
    await message.answer("Парсинг завершен.", reply_markup=get_main_kb())
