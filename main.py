import asyncio
import logging
import requests
import os
import datetime
import database
import parser
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
# Импортируем наши настройки
from handlers import common, finance, survey, admin, ai_chat
from middlewares import TrackUserMiddleware

# Загружаем переменные окружения
load_dotenv()

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Создаем объекты бота и диспетчера
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

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
    # Проверка на случай, если ключа нет
    if not api_key:
        return "🌤 Погода: ключ API не найден."
        
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = round(data['main']['temp'])
            desc = data['weather'][0]['description']
            return f"🌤 <b>Погода в Ульяновске:</b> {temp}°C, {desc}"
        else:
            return "🌤 Погода недоступна (ошибка сервиса)."
    except:
        return "🌤 Погода недоступна."

# --- ПЛАНИРОВЩИК (SCHEDULER) ---
async def scheduler():
    while True:
        try:
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")
            target_time = "05:00" # Время рассылки

            if current_time == target_time:
                users = database.get_all_users()
                
                # Собираем данные
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
                
                # Ждем 60 секунд, чтобы не отправить дважды в одну минуту
                await asyncio.sleep(60)

            # Проверяем время каждые 10 секунд
            await asyncio.sleep(10)

        except Exception as e:
            print(f"Ошибка в планировщике: {e}")
            await asyncio.sleep(10)

# --- ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА ---
async def main():
	#1. Создаем таблицы БД
	database.create_tables()

	# 2. Подключаем "вахтера" (Middleware)
	# Теперь каждое сообщение проходит через эту проверку и сохраняет юзера
	dp.message.middleware(TrackUserMiddleware())

	# 3. Подключаем роутеры (отделы логики)
	dp.include_router(admin.router)   # Админка (проверяется первой!)
	dp.include_router(ai_chat.router) # ИИ
	dp.include_router(common.router)  # Обычные команды
	dp.include_router(survey.router)  # Анкета
	dp.include_router(finance.router) # Финансы 

	#4. Сбрасываем старые обновления
	await bot.delete_webhook(drop_pending_updates=True)

	#5. Запускаем планировщик в фоне
	asyncio.create_task(scheduler())

	#6. Запускаем бота
	print("🚀 Бот запущен!")
	await dp.start_polling(bot)

if __name__ == "__main__":
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		print("Бот выключен")
