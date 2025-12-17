import asyncio
from aiogram import Bot, Dispatcher
import os
import django
from decouple import config


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from bot.handlers.start import router


async def main():
    bot = config(Bot(token='TOKEN'))
    dp = Dispatcher()
    dp.include_router(router)

    print('bot ishga tushdi...')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())