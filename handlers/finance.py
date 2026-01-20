import os
import requests
import matplotlib.pyplot as plt
from aiogram import Router, types, F
from aiogram.types import FSInputFile
import database
from ai_assistant import get_chat_response
import datetime
import csv

router = Router()

# Переносим словарь истории сюда, так как он используется только здесь
users_history = {}

# Временная функция логирования (лучше потом вынести в utils.py, но пока пусть живет тут)
def log_message(user_id, username, text):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not username:
        username = "Anonim"
    data = [now, user_id, username, text]
    # Используем абсолютный путь, чтобы не потерять файл
    with open("logs.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(data)

# Ловим кнопку "Курсы валют"
@router.callback_query(F.data == "rates_btn")
async def cb_rates(callback: types.CallbackQuery):
	await callback.answer()
	await callback.message.answer("Чтобы узнать курс, просто напиши мне сумму числом (например: 1000).")

# --- ГЛАВНЫЙ ОБРАБОТЧИК (Валюты + ИИ) ---
# Мы ловим ВСЕ текстовые сообщения, которые не поймали предыдущие роутеры
@router.message(F.text)
async def convert_currency(message: types.Message):
    # Логируем
    log_message(message.from_user.id, message.from_user.username, message.text)
    
    user_id = message.from_user.id
    text = message.text
    clean_text = text.replace(" ", "")

    # 1. Если это ЧИСЛО -> Конвертация валют
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

            currencies = ['USD', 'EUR', 'CNY']
            values = [usd_res, eur_res, cny_res]

            # Рисуем график
            plt.figure(figsize=(6, 4))
            plt.bar(currencies, values, color=['green', 'blue', 'red'])
            plt.title(f'На {rubles} руб. можно купить:')
            plt.grid(True, alpha=0.3)

            file_name = f"chart_{user_id}.png" # Добавил ID, чтобы файлы не путались
            plt.savefig(file_name)
            plt.close()

            photo = FSInputFile(file_name)
            await message.answer_photo(photo, caption=f"Вот твой расчет на сегодня! 📉")
            os.remove(file_name)

        except Exception as e:
            await message.answer(f"Произошла ошибка: {e}")

    # 2. ИНАЧЕ -> Нейросеть (GigaChat)
    else:
        # Используем message.bot вместо bot
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        if user_id not in users_history:
            users_history[user_id] = []
        
        users_history[user_id].append({"role": "user", "content": text})
        
        # Передаем историю в функцию ИИ
        ai_answer = get_chat_response(users_history[user_id])
        
        users_history[user_id].append({"role": "assistant", "content": ai_answer})
        await message.answer(ai_answer)
