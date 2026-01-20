import asyncio
import logging
import requests
import matplotlib.pyplot as plt
import os
import csv
import datetime
import database
import parser
from aiogram.types import FSInputFile
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from ai_assistant import get_chat_response

# Включаем логирование, чтобы видеть сообщения в консоли
logging.basicConfig(level=logging.INFO)

# ---NASTROYKA--
bot = Bot(token="8345459205:AAFitLeMVFJIetASo0Xj_KZ7_wgiqdSCpNY")
dp = Dispatcher()

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




# --- ФУНКЦИЯ ДЛЯ ЗАПИСИ ДАННЫХ (LOGGING) ---
def log_message(user_id, username, text):
    # 1. Получаем текущее время
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2. Собираем данные в список
    # Если username нет (скрыт), напишем "Anonim"
    if not username:
        username = "Anonim"

    data = [now, user_id, username, text]

    # 3. Открываем файл logs.csv в режиме "дозаписи" (append - 'a')
    # newline='' нужен, чтобы не было пустых строк между записями
    # encoding='utf-8' нужен, чтобы русские буквы не превратились в кракозябры
    with open("logs.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(data)

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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # --- ЗАПИСЬ В ЖУРНАЛ ---
    log_message(message.from_user.id,message.from_user.username, "/start")
    # -----------------------
    name = message.from_user.username
    if not name:
        name = message.from_user.first_name

    database.add_user_to_db(message.from_user.id, name)


    await message.answer("Привет! Выбери действие ниже или введи сумму в рублях, и я покажу графики! 📊:", reply_markup=keyboard)

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


# Если нажали "Поздороваться"
@dp.message(F.text == "👋 Поздороваться")
async def cmd_hello(message: types.Message):
    await message.answer("Привет-привет! Рад тебя видеть!")

# Если нажали "Кинуть кубик" (Телеграм умеет кидать красивые 3D кубики)
@dp.message(F.text == "🎲 Кинуть кубик")
async def cmd_dice(message: types.Message):
    await message.answer_dice(emoji="🎲")

# Если нажали "О боте"
@dp.message(F.text == "ℹ️ О боте")
async def cmd_info(message: types.Message):
    await message.answer("Я тестовый бот, написанный на Python! 🐍")


# --- ГЛАВНЫЙ ОБРАБОТЧИК СООБЩЕНИЙ ---
@dp.message()
async def convert_currency(message: types.Message):
    # --- ЗАПИСЬ В ЖУРНАЛ ---
    log_message(message.from_user.id, message.from_user.username, message.text)
    # -----------------------

    # 1. Чистим текст
    user_id = message.from_user.id
    text = message.text
    clean_text = text.replace(" ", "")



    # 2. Проверка: А это вообще число?
    # .isdigit() спрашивает: "Состоит ли этот текст только из цифр?"

    if clean_text.isdigit():
        database.update_user_counter(message.from_user.id)
        rubles = int(clean_text)

        await message.answer("⏳ Считаю курс валют...")

        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        try:

            response = requests.get(url)
            data = response.json()

            usd_rate = data['Valute']['USD']['Value']
            eur_rate = data['Valute']['EUR']['Value']
            cny_rate = data['Valute']["CNY"]['Value']

            usd_res = round(rubles / usd_rate, 2)
            eur_res = round(rubles / eur_rate, 2)
            cny_res = round(rubles / cny_rate, 2)

            # 3. --- РИСУЕМ ГРАФИК (Data Science часть) ---

            # Данные для осей
            currencies = ['USD', 'EUR', 'CNY']
            values = [usd_res, eur_res, cny_res]

            # Создаем картинку
            plt.figure(figsize=(6, 4))
            plt.bar(currencies, values, color=['green', 'blue', 'red'])
            plt.title(f'На {rubles} руб. можно купить:')
            plt.grid(True, alpha=0.3)

            # Сохраняем картинку в файл
            file_name = "chart.png"
            plt.savefig(file_name)
            plt.close()

            # 4. Отправляем фото
            photo = FSInputFile(file_name)
            await message.answer_photo(photo, caption=f"Вот твой расчет на сегодня! 📉")

            # Удаляем файл после отправки (убираем за собой)
            os.remove(file_name)

        except Exception as e:
            await message.answer(f"Произошла ошибка курсов валют {e}")

    # 3. ИНАЧЕ: Это текст (Общаемся через GigaChat)
    else:
        # Показываем статус "печатает..."
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")

        # --- ШАГ А: Достаем историю этого пользователя ---
        # Если пользователя нет в словаре, создаем для него пустой список []
        if user_id not in users_history:
            users_history[user_id] = []

        # --- ШАГ Б: Добавляем сообщение пользователя в историю ---
        # Формат требует GigaChat: {"role": "user", "content": "Текст"}
        users_history[user_id].append({"role": "user", "content": text})

        # --- ШАГ В: Отправляем ВЕСЬ список сообщений в нейросеть ---
        # Мы берем историю users_history[user_id] и передаем в функцию
        ai_answer = get_chat_response(users_history[user_id])

        # --- ШАГ Г: Запоминаем ответ бота ---
        # Чтобы в следующий раз бот знал, что он сам ответил
        users_history[user_id].append({"role": "assistant", "content": ai_answer})

        # Отправляем ответ
        await message.answer(ai_answer)



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
    api_key = "30cc035c854726c52997b2703d50d222"
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
