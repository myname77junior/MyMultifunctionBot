import asyncio
import logging
import requests
import os
import datetime
import database
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# Импортируем наши настройки
from handlers import common, finance, survey, admin, ai_chat
from middlewares import TrackUserMiddleware
from ai_assistant import get_chat_response

# Планировщик задач
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# ИМПОРТИРУЕМ НОВУЮ ФУНКЦИЮ ИЗ FINANCE
from handlers.finance import get_currency_rate

# Загружаем переменные окружения
load_dotenv()

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Создаем объекты бота и диспетчера
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


# --- ФУНКЦИЯ УТРЕННЕЙ РАССЫЛКИ ---
async def send_morning_news():
    print("⏰ Начало утренней рассылки...")

    # 1. Генерируем цитату (ОДНУ для всех, чтобы не ждать долго)
    try:
        quote = await get_chat_response(
            "Придумай короткую мотивирующую цитату на утро. Без банальностей."
        )
    except:
        qoute = "Сделай сегодня что-то великое! ✨"

    # 2. Получаем курс валют (из finance.py)
    currency_info = get_currency_rate()

    # 2. Получаем список пользователей с городами
    users_data = (
        database.get_all_profiles_data()
    )  # [(123, 'Москва'), (456, 'Ульяновск')...]

    if not users_data:
        print("⚠️ Нет пользователей с заполненными городами.")
        return

    api_key = os.getenv("WEATHER_API_KEY")

    # 3. Проходим по каждому пользователю
    for user_id, city in users_data:
        try:
            # Получаем погоду для КОНКРЕТНОГО города
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
            resp = requests.get(url)

            weather_text = ""
            if resp.status_code == 200:
                data = resp.json()
                temp = round(data["main"]["temp"])
                desc = data["weather"][0]["description"]
                weather_text = f"🌤 В твоем городе ({city}): <b>{temp}°C</b>, {desc}."
            else:
                weather_text = f"🌤 Погода в {city} пока недоступна."

            # Формируем сообщение
            msg = (
                f"👋 <b>Доброе утро!</b>\n\n"
                f"{weather_text}\n\n"
                f"{currency_info}\n\n"
                f"🧘 <b>Мысль дня:</b>\n<i>{quote}</i>"
            )

            # Отправляем
            await bot.send_message(chat_id=user_id, text=msg, parse_mode="HTML")
            await asyncio.sleep(
                0.5
            )  # Небольшая пауза, чтобы Телеграм не забанил за спам

        except Exception as e:
            print(f"Не удалось отправить юзеру {user_id}: {e}")

    print("✅ Рассылка завершена.")


# --- ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА ---
async def main():
    # 1. Создаем таблицы БД
    database.create_tables()
    # 2. Подключаем "вахтера" (Middleware)
    # Теперь каждое сообщение проходит через эту проверку и сохраняет юзера
    dp.message.middleware(TrackUserMiddleware())

    # 3. Подключаем роутеры (отделы логики)
    dp.include_router(admin.router)  # Админка (проверяется первой!)
    dp.include_router(ai_chat.router)  # ИИ
    dp.include_router(common.router)  # Обычные команды
    dp.include_router(survey.router)  # Анкета
    dp.include_router(finance.router)  # Финансы

    # Настраиваем Планировщик (Scheduler)
    scheduler = AsyncIOScheduler()

    # Ставим задачу: каждый день в 08:00 утра
    # (Можешь поменять время на ближайшее к тебе для теста, например через 2 минуты)
    scheduler.add_job(send_morning_news, "cron", hour=23, minute=6)

    # ЗАПУСК ПЛАНИРОВЩИКА
    scheduler.start()

    # 4. Сбрасываем старые обновления
    await bot.delete_webhook(drop_pending_updates=True)
    # 6. Запускаем бота
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
