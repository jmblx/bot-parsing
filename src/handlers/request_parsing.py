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
    waiting_for_query = State()
    parsing_in_progress = State()



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
async def start_parsing_query(
        callback_query: types.CallbackQuery, state: FSMContext, session: AsyncSession, redis: Redis
):
    button_id = callback_query.data.split("_")[2]
    button_url = await redis.get(button_id)
    if not button_url:
        button_url = (await session.get(Button, int(button_id))).url
        await redis.setex(button_id, 60, button_url)
    await state.set_data({'button_url': button_url})
    await state.set_state(ParsingStates.waiting_for_query)
    await callback_query.message.answer("Введите ваш запрос:")
    await callback_query.answer()


@user_private_router.message(ParsingStates.waiting_for_query, F.text)
async def process_user_query(message: types.Message, state: FSMContext):
    user_query = message.text
    data = await state.get_data()
    full_query_url = f"{data['button_url']}/ru/search"
    await state.set_state(ParsingStates.parsing_in_progress)
    await parse_category_products(full_query_url, message=message, text_query=user_query)
    await state.clear()
    await message.answer("Завершили обработку вашего запроса.")

