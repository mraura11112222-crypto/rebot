import os
import random
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import delete, select

from app.database import async_session, engine
from app.models.telegram_verification import TelegramVerificationCode

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

dp = Dispatcher()
bot: Optional[Bot] = None
table_ready = False


async def ensure_verification_table() -> None:
    global table_ready
    if table_ready:
        return
    async with engine.begin() as conn:
        await conn.run_sync(TelegramVerificationCode.__table__.create, checkfirst=True)
    table_ready = True


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await ensure_verification_table()

    async with async_session() as session:
        await session.execute(
            delete(TelegramVerificationCode).where(
                TelegramVerificationCode.expires_at < datetime.utcnow()
            )
        )

        code = str(random.randint(10000, 99999))
        existing = await session.execute(
            select(TelegramVerificationCode).where(TelegramVerificationCode.code == code)
        )
        while existing.scalar_one_or_none():
            code = str(random.randint(10000, 99999))
            existing = await session.execute(
                select(TelegramVerificationCode).where(TelegramVerificationCode.code == code)
            )

        session.add(
            TelegramVerificationCode(
                code=code,
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username,
                expires_at=datetime.utcnow() + timedelta(days=3650),
            )
        )
        await session.commit()

    response_text = (
        f"👋 Assalomu alaykum, {message.from_user.first_name}!\n\n"
        f"RestoPro tizimiga kirish uchun kodingiz:\n\n"
        f"🔐 <b>{code}</b>\n\n"
        f"<i>Ushbu kodni saytdagi maxsus oynaga kiriting.</i>"
    )

    await message.answer(response_text, parse_mode="HTML")


async def start_bot() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN .env faylida sozlanmagan")
    global bot
    bot = Bot(token=BOT_TOKEN)
    print("[OK] Telegram bot started.")
    await dp.start_polling(bot)
