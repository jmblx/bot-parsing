import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from sqlalchemy import insert, update

# from config import ADMIN_LIST
from database.models import User, Button
from middlewares.redis_config import RedisSession
from parsing.const import SITES

from middlewares.db import DataBaseSession
from database.engine import session_maker, create_db, drop_db
from dotenv import find_dotenv, load_dotenv
from kbds.reply import get_main_kb, admin_check
from handlers.category_parsing import user_private_router as parsing_router
from handlers.request_parsing import user_private_router as request_parsing_router

load_dotenv(find_dotenv())

ALLOWED_UPDATES = ["message, edited_message"]

bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(default=bot_properties, token=os.getenv("TOKEN"))
bot.my_admins_list = []

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_router(parsing_router)
dp.include_router(request_parsing_router)


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(
        """
Приветствую! Для получения информации выберите сайт для парсинга и категорию товаров этого сайта.
        """,
        reply_markup=get_main_kb(),
    )


async def on_startup(bot):
    await drop_db()
    await create_db()
    async with session_maker() as session:
        for name, url in SITES.items():
            button_id = (
                await session.execute(insert(Button).values(name=name, url=url, type="site").returning(Button.id))
            ).scalar()
            await session.commit()
            await session.execute(update(Button).where(Button.id == button_id).values(callback_data=f"site_{button_id}"))
        await session.commit()


async def on_shutdown(bot):
    await drop_db()
    print("")


async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    dp.update.middleware(RedisSession(os.getenv("REDIS_PATH", "redis://localhost")))
    await bot.delete_webhook(drop_pending_updates=True)
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)


asyncio.run(main())
