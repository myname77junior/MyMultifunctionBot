import asyncio
import logging
import requests
import os
import datetime
import database
import parser
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from handlers import common, finance, survey

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
	load_dotenv(dotenv_path)

# Загружаем секреты из файла .env прямо сейчас
load_dotenv()

# Включаем логирование, чтобы видеть сообщения в консоли
logging.basicConfig(level=logging.INFO)

# ---NASTROYKA--
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# !!! ПОДКЛЮЧАЕМ РОУТЕР (Это самое важное) !!!
# Мы говорим диспетчеру: "Если придет сообщение, проверь его в common.router"
dp.include_router(common.router) # 1. Сначала кнопки
dp.include_router(survey.router) # - переехватываем, если это анкета 
dp.include_router(finance.router) #2. Потом деньги и ИИ

# Sozdaem klaviaturu

kb = [
    [
        KeyboardButton(text="👋 Поздороваться"),
        KeyboardButton(text="🎲 Кинуть кубик")
    ],
    [
        KeyboardButton(text="ℹ️ О боте")
    ]
]

#Sozdaem ob'ekt klaviaturi
keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- ПАМЯТЬ БОТА (Словарь) ---
# Это как шкаф с ящиками. На каждом ящике написан ID пользователя (user_id).
# Внутри ящика лежит список сообщений.
# Структура: { 12345678: [список_сообщений], 98765432: [список_сообщений] }
users_history = {}

# ---OBRABOTCHIK---

# --- КОМАНДА СБРОСА ПАМЯТИ ---
@dp.message(F.text == "🗑 Сбросить диалог")
@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    user_id = message.from_user.id
    # Обращаемся к словарю users_history
    # Команда .pop(key) удаляет запись из словаря, если она есть
    users_history.pop(user_id, None)

    await message.answer("🧠 Я забыл всё, о чем мы говорили. Можем начать сначала!")

@dp.message(Command("news"))
async def cmd_news(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    news_text = parser.get_smart_quote()
    await message.answer(news_text, parse_mode="HTML", disable_web_page_preview=True)

@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    top_users = database.get_top_users()

    text = "🏆 <b>Топ активных пользователей:</b>\n\n"

    for index, user in enumerate(top_users):
        text += f"{index +1}. 👤 {user[0]} - {user[1]} сообщ. \n"

    await message.answer(text, parse_mode="HTML")


@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    users = database.get_all_users()
    answer_text = "📋 <b>Список пользователей:</b>\n\n"

    for user in users:
        answer_text += f"👤 <b>Имя:</b> {user[1]} (ID: {user[0]}) - Запросов: {user[2]}\n"

    await message.answer(answer_text, parse_mode="HTML")


# --- СЕКРЕТНАЯ КОМАНДА ДЛЯ АДМИНА ---
@dp.message(Command("logs"))
async def cmd_send_logs(message: types.Message):
    # Проверяем, существует ли файл (вдруг еще никто не писал?)
    if os.path.exists("logs.csv"):
        # Готовим файл к отправке
        # FSInputFile мы уже использовали для графиков, тут то же самое
        log_file = FSInputFile("logs.csv")

        await message.answer_document(log_file, caption="📂 Вот отчет о всех действиях!")
    else:
        await message.answer("Файла с логами пока нет. Напиши боту что-нибудь!")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    count = database.get_users_count()
    text = f"📊 <b>Статистика бота:</b>\n\n👥 В базе:{count} человек"
    await message.answer(text, parse_mode="HTML")


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАССЫЛКИ ---
def get_daily_currency():
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        response = requests.get(url)
        data = response.json()
        usd = data['Valute']['USD']['Value']
        eur = data['Valute']['EUR']['Value']
        cny = data['Valute']['CNY']['Value']
        return f"💰 <b>Курсы валют:</b>\n🇺🇸 USD: {usd:.2f} ₽\n🇪🇺 EUR: {eur:.2f} ₽\n🇨🇳 CNY: {cny:.2f} ₽"
    except:
        return "💰 Курсы валют временно недоступны."

def get_daily_weather():
    city = "Ульяновск"
    api_key = os.getenv("WEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = round(data['main']['temp'])
            desc = data['weather'][0]['description']
            return f"🌤 <b>Погода в Ульяновске:</b> {temp}°C, {desc}"
        else:
            return "🌤 Погода недоступна."
    except:
        return "🌤 Погода недоступна."

# --- ФУНКЦИЯ РАССЫЛКИ (SCHEDULER) ---
async def scheduler():
    while True:
        try:
            now = datetime.datetime.now()

            current_time = now.strftime("%H:%M")

            target_time = "05:00"

            if current_time == target_time:

                users = database.get_all_users()

                currency_text = get_daily_currency()
                weather_text = get_daily_weather()
                quote_text = parser.get_smart_quote()

                final_message = (
                    f"👋 Доброе утро! Вот твоя сводка:\n\n"
                    f"{weather_text}\n\n"
                    f"{currency_text}\n\n"
                    f"{quote_text}"
                )

                count = 0
                for user in users:
                    user_id = user[0]
                    try:
                        await bot.send_message(chat_id=user_id, text=final_message, parse_mode='HTML')
                        count += 1
                    except Exception as e:
                        print(f"Не смог отправить {user_id}: {e}")

                print(f"✅ Рассылка завершена! Отправлено: {count} людям.")

                await asyncio.sleep(60)

            await asyncio.sleep(10)

        except Exception as e:
            print(f"Ошибка в планировщике: {e}")
            await asyncio.sleep(10)


# --- ЗАПУСК ---
async def main():
    # Запускаем нашего "Повелителя времени" в фоне
    asyncio.create_task(scheduler())


    # Запускаем самого бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
