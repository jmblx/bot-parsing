from aiogram import Router, F, types
from aiogram.filters import or_f, Command
from aiogram.types import InlineKeyboardButton
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import get_sites_buttons
from kbds.reply import get_inline_keyboard


async def default_site_selection(
    message: types.Message,
    session: AsyncSession,
    redis: Redis,
    callback_prefix: str,
):
    buttons = await get_sites_buttons(session)
    inline_buttons = []
    for button in buttons:
        print(button, button.callback_data)
        inline_buttons.append(
            InlineKeyboardButton(
                text=button.name,
                callback_data=f"{callback_prefix}_{button.callback_data}",
            )
        )
        # Сохранение URL с TTL
        await redis.setex(button.id, 60, button.url)
    inline_keyboard = get_inline_keyboard(inline_buttons, in_row=1)
    await message.answer(
        "Выберите сайт для парсинга", reply_markup=inline_keyboard
    )
