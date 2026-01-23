from aiogram import Router, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext #нужно для запуска анкеты
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from states import Form
# Импортируем нашу новую клавиатуру
from keyboards.client_kb import main_menu, back_kb
from ai_assistant import get_chat_response
import database
import requests
import os
import datetime


router = Router()

# --- ХЕНДЛЕРЫ ---

@router.message(Command("start"))
async def cmd_start(message: types.Message):
	# 1. Сначала отправляем сообщение "удалялку", чтобы стереть кнопки внизу
	await message.answer("Загружаю меню...", reply_markup=ReplyKeyboardRemove())
	# 2. Потом отправляем красивое меню
	await message.answer(
		"Привет! Я стал современнее. Жми кнопки под сообщением! 👇",
		reply_markup=main_menu # <--- Прикрепляем клавиатуру
	)

#--- ЛОГИКА КНОПКИ "НАЗАД" (УЛУЧШЕННАЯ) ---
@router.callback_query(F.data == "back_home")
async def cb_back(callback: types.CallbackQuery, state: FSMContext):
	# Сбрасываем любые состояния (ввод суммы, города и т.д.)
	await state.clear()

	try:
	# Попытка 1: Просто отредактировать текст (сработает, если было текстовое сообщение)
		await callback.message.edit_text(
			"Ты в главном меню. Выбирай! 👇",reply_markup=main_menu)
	except Exception:
		# Попытка 2: Если возникла ошибка (например, это была картинка),
		# мы удаляем старое сообщение и отправляем новое
		await callback.message.delete()
		await callback.message.answer("Ты в главном меню. Выбирай! 👇",reply_markup=main_menu)

# --- ЛОГИКА КНОПКИ "ПРОФИЛЬ" ---
@router.callback_query(F.data == "profile_btn")
async def cb_profile(callback: types.CallbackQuery, state: FSMContext):
	user_id = callback.from_user.id
	# 1. Проверяем базу
	profile = database.get_profile(user_id)

	# 2. Если профиля НЕТ -> Запускаем анкету
	if not profile:
		await callback.message.answer("Я тебя пока не знаю! Давай знакомиться.\nКак тебя зовут?")
		await state.set_state(Form.name) # <-- Запускаем машину состояний
		return

	# Распаковываем 4 значения (раньше было 3)
	name, age, city, bio = profile
	text = (
		f"📂 <b>Твой профиль:</b>\n\n"
		f"👤 <b>Имя:</b> {name}\n"
		f"🎂 <b>Возраст:</b> {age}\n"
		f"🏙 <b>Город:</b> {city}\n"
 		f"📝 <b>О себе:</b> {bio}"
	)

	# Кнопка редактирования прямо под профилем
	edit_kb = InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile")],
		[InlineKeyboardButton(text="🔙 Назад", callback_data="back_home")]
	])

	await callback.message.edit_text(text, reply_markup=edit_kb, parse_mode="HTML")

# --- ЛОГИКА РЕДАКТИРОВАНИЯ ---
@router.callback_query(F.data == "edit_profile")
async def cb_edit_profile(callback: types.CallbackQuery, state: FSMContext):
	await callback.message.edit_text("Давай обновим данные. Как тебя зовут?", reply_markup=back_kb)
	await state.set_state(Form.name) # Запускаем анкету заново

# --- ЦИТАТА (Используем ИИ) ---
@router.callback_query(F.data == "quote_btn")
async def cb_quote(callback: types.CallbackQuery):
	# Показываем, что думаем
	await callback.message.edit_text("🧘 Ищу мудрость для тебя...", reply_markup=back_kb)

	try:
		# Просим GigaChat придумать цитату
		prompt = "Придумай короткую, вдохновляющую, мудрую цитату или аффирмацию на сегодня. Не используй банальности."
		ai_answer = await get_chat_response(prompt)

		await callback.message.edit_text(
			f"✨ <b>Цитата дня:</b>\n\n<i>{ai_answer}</i>",
			reply_markup=back_kb,
			parse_mode="HTML"
		)
	except Exception as e:
		await callback.message.edit_text(f"Не удалось получить мудрость: {e}", reply_markup=back_kb)


# --- ЛОГИКА КНОПКИ "О БОТЕ" ---
@router.callback_query(F.data == "about_btn")
async def cb_about(callback: types.CallbackQuery):
	# 1. Отвечаем всплывашкой (чтобы часики на кнопке пропали)
	await callback.message.edit_text(
		"Я бот, написанный на Python + Aiogram 3. 🐍\n"
		"Умею хранить данные, считать валюту и болтать.",
		reply_markup=back_kb
	)

# ==========================================
# НОВАЯ ЛОГИКА: ПОГОДА + ПРОГНОЗ
# ==========================================

@router.callback_query(F.data == "weather_btn")
async def cb_weather(callback: types.CallbackQuery, state: FSMContext):
	await callback.message.edit_text(
		"Напиши название города (например: Москва):",
		reply_markup=back_kb
	)
	await state.set_state(Form.city_request)

@router.message(Form.city_request)
async def process_weather_city(message: types.Message, state: FSMContext):
	city = message.text
	api_key = os.getenv("WEATHER_API_KEY") # Берем ключ из .env

	# 1. URL для текущей погоды
	url_now = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
	# 2. URL для прогноза (forecast)
	url_forecast = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=ru"

	await message.answer(f"🔎 Смотрю погоду в: {city}...")

	try:
		# --- ПОЛУЧАЕМ ТЕКУЩУЮ ПОГОДУ ---
		resp_now = requests.get(url_now)

		if resp_now.status_code != 200:
			await message.answer("❌ Город не найден. Попробуй еще раз.", reply_markup=back_kb)
			return # Не выходим из состояния, даем шанс исправить

		data = resp_now.json()
		temp = round(data['main']['temp'])
		desc = data['weather'][0]['description']
		wind = data['wind']['speed']

		# --- ПОЛУЧАЕМ ПРОГНОЗ ---

		resp_forecast = requests.get(url_forecast)

		# --- ВАЖНАЯ ПРОВЕРКА ---
		if resp_forecast.status_code != 200:
			print(f"🔥 ОШИБКА ПРОГНОЗА: {resp_forecast.text}")
			await message.answer(f"Погоду нашел, а прогноз не смог (Ошибка API).", reply_markup=back_kb)
			return
		# -----------------------

		forecast_data = resp_forecast.json()

		# OpenWeatherMap дает прогноз каждые 3 часа. Список 'list' содержит 40 записей (5 дней * 8 отрезков).
		# Чтобы узнать погоду на завтра, берем 8-й элемент (через 24 часа), на послезавтра - 16-й и т.д.

		forecast_list = forecast_data['list']

		# Формируем текст прогноза
		forecast_text = ""

		# range(8, 33, 8) означает: берем индексы 8, 16, 24, 32...
		# То есть берем погоду с шагом в 24 часа (примерно)
		days_map = {0: "Завтра", 1: "Послезавтра", 2: "Через 3 дня"}

		for i, idx in enumerate(range(7, 30, 8)): # Берем 3 точки в будущем
			if idx < len(forecast_list):
				item = forecast_list[idx]
				f_temp = round(item['main']['temp'])
				f_desc = item['weather'][0]['description']
				# Получаем дату из текста "2024-01-21 15:00:00"
				f_date = item['dt_txt'].split(" ")[0]

				day_name = days_map.get(i, f_date)

				forecast_text += f"📅 <b>{day_name}:</b> {f_temp}°C, {f_desc}\n"

		# --- СОБИРАЕМ ВСЁ ВМЕСТЕ ---

		final_msg = (
			f"🌤 <b>Погода сейчас в {city}:</b>\n"
			f"🌡 <b>{temp}°C</b>, {desc}\n"
			f"💨 Ветер: {wind} м/с\n\n"
			f"🔮 <b>Прогноз на будущее:</b>\n"
			f"{forecast_text}"
		)

		await message.answer(final_msg, parse_mode="HTML", reply_markup=back_kb)
		await state.clear()

	except Exception as e:
		# Выводим саму ошибку пользователю, чтобы понять причину
		print(f"КРИТИЧЕСКАЯ ОШИБКА {e}")
		await message.answer(f"Ошибка: {e}", reply_markup=back_kb)
		await state.clear()
