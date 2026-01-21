import database
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

	database.save_profile(
		user_id=message.from_user.id,
		name=data['name'],
		age=data['age'],
		bio=data['bio']
	)

	text = (
		f"✅ <b>Анкета готова!</b>\n\n"
		f"👤 <b>Имя:</b> {data['name']}\n"
		f"🎂 <b>Возраст:</b> {data['age']}\n"
		f"📝 <b>О себе:</b> {data['bio']}"
		)

	await message.answer(text, parse_mode="HTML")
	await state.clear()

@router.message(Command("myprofile"))
async def cmd_my_profile(message: types.Message):
	# 1. Спрашиваем у базы: "Есть что-нибудь про этого парня?"
	profile = database.get_profile(message.from_user.id)

	# 2. Если profile пустотой (None) — значит, анкеты нет
	if not profile:
		await message.answer("Я тебя пока не знаю! Напиши /profile, чтобы познакомиться.")
		return

	# 3. Если анкета есть — распаковываем данные
	name, age, bio = profile

	text = (
		f"📂 <b>Твой профиль:</b>\n\n"
		f"👤 <b>Имя:</b>{name}\n"
		f"🎂 <b>Возраст:</b>{age}\n"
		f"📝 <b>О себе:</b>{bio}"
	)
	await message.answer(text, parse_mode="HTML")
