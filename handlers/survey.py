from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form # Импортируем наши состояния

router = Router()

# 1. СТАРТ: Ловим команду /profile
@router.message(Command("profile"))
async def start_survey(message: types.Message, state: FSMContext):
	await message.answer("Давай заполним твой профиль! Как тебя зовут?")
	# Переводим бота в состояние ожидания имени
	await state.set_state(Form.name)

# --- 2. ЛОВИМ ИМЯ ---
@router.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
	await state.update_data(name=message.text)
	await message.answer(f"Приятно познакомиться, {message.text}! Сколько тебе лет?")
	await state.set_state(Form.age)

# --- 3. ЛОВИМ ВОЗРАСТ ---
@router.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
	if not message.text.isdigit():
		await message.answer("Пожалуйста, пиши возраст цифрами (например: 25)!")
		return
	await state.update_data(age=message.text)

	await message.answer("Отлично! Напиши пару слов о себе.")

	await state.set_state(Form.bio)

# --- 4. ФИНАЛ ---
@router.message(Form.bio)
async def process_bio(message: types.Message, state: FSMContext):
	await state.update_data(bio=message.text)

	data = await state.get_data()

	text = (
		f"✅ <b>Анкета готова!</b>\n\n"
		f"👤 <b>Имя:</b> {data['name']}\n"
		f"🎂 <b>Возраст:</b> {data['age']}\n"
		f"📝 <b>О себе:</b> {data['bio']}"
		)

	await message.answer(text, parse_mode="HTML")
	await state.clear()
