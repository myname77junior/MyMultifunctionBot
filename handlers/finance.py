import os
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from aiogram import Router, types, F
from aiogram.types import FSInputFile
import database
from ai_assistant import get_chat_response
import datetime
import csv
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.client_kb import back_kb


router = Router()

# Переносим словарь истории сюда, так как он используется только здесь
#users_history = {}

# Временная функция логирования (лучше потом вынести в utils.py, но пока пусть живет тут)
#def log_message(user_id, username, text):
#	now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#	if not username:
#	username = "Anonim"
#	data = [now, user_id, username, text]
#	#Используем абсолютный путь, чтобы не потерять файл
#	with open("logs.csv", "a", newline="", encoding="utf-8") as file:
#		writer = csv.writer(file)
#		writer.writerow(data)

# Ловим кнопку "Курсы валют"

class FinanceState(StatesGroup):
	waiting_for_amount = State()

@router.callback_query(F.data == "rates_btn")
async def cb_rates(callback: types.CallbackQuery, state: FSMContext):
	# Просим ввести рубли
	await callback.message.edit_text(
		"💰 <b>Конвертер валют</b>\n\n"
		"Напиши сумму в <b>рублях (RUB)</b>, которую ты хочешь обменять.\n",
		parse_mode="HTML",
		reply_markup=back_kb # Кнопка "Назад" всегда под рукой
	)
	# Включаем режим "Жду число"
	await state.set_state(FinanceState.waiting_for_amount)

# --- 2. Юзер прислал число (обрабатываем ввод) ---


@router.message(FinanceState.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
	user_id = message.from_user.id

	try:
		raw_text = message.text.replace(',', '.').replace(' ', '')
		rub_amount = float(raw_text)

	except ValueError:
		# Если юзер написал "пять тыщ", ругаемся
		await message.answer("❌ Введи числом! (например: 1000)", reply_markup=back_kb)
		return

	wait_msg = await message.answer("⏳ Считаю курс валют...")

	try:
		url = "https://www.cbr-xml-daily.ru/daily_json.js"
		response = requests.get(url)
		data = response.json()

		usd_rate = data['Valute']['USD']['Value']
		eur_rate = data['Valute']['EUR']['Value']
		cny_rate = data['Valute']["CNY"]['Value']

		usd_res = round(rub_amount / usd_rate, 2)
		eur_res = round(rub_amount / eur_rate, 2)
		cny_res = round(rub_amount / cny_rate, 2)

		currencies = ['USD', 'EUR', 'CNY']
		values = [usd_res, eur_res, cny_res]

		#Рисуем график
		# Используем plt.subplots - это более безопасно для бота
		fig, ax = plt.subplots(figsize=(6, 4))

		# Столбцы: зеленый, синий, красный
		bars = ax.bar(currencies, values, color=['#2ecc71', '#3498db', '#e74c3c'])

		ax.set_title(f'На {rub_amount:,.0f} руб. можно купить:'.replace(',', ' '))
		ax.grid(True, axis='y', alpha=0.3)

		# Добавляем подписи значений над столбцами
		ax.bar_label(bars, fmt='{:,.0f}')


		file_name = f"chart_{user_id}.png" # Добавил ID, чтобы файлы не путались
		plt.savefig(file_name)
		plt.close()

		photo = FSInputFile(file_name)

		caption_text = (
			f"💱 <b>Обмен {rub_amount:,.2f} ₽:</b>\n\n" # :, добавляет разделитель тысяч (5,000.00)
			f"🇺🇸 <b>USD:</b> {usd_res:,.2f} $ (Курс: {usd_rate:.2f})\n"
			f"🇪🇺 <b>EUR:</b> {eur_res:,.2f} € (Курс: {eur_rate:.2f})\n"
			f"🇨🇳 <b>CNY:</b> {cny_res:,.2f} ¥ (Курс: {cny_rate:.2f})"
		)

		# Удаляем сообщение "Считаю..."
		await wait_msg.delete()


		await message.answer_photo(
			photo,
			caption=caption_text,
			parse_mode="HTML",
			reply_markup=back_kb
		)

		# Удаляем файл с диска
		os.remove(file_name)

		# Сбрасываем состояние
		await state.clear()

		# Выключаем состояние (машину), чтобы бот снова ждал команды, а не числа

	except Exception as e:
		print(f"Ошибка Finance: {e}") # Пишем в консоль для отладки
		await message.answer(f"Ошибка получения данных: {e}", reply_markup=back_kb)
		await state.clear()



