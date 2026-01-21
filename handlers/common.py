from aiogram import Router, types, F
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardRemove
# Импортируем нашу новую клавиатуру
from keyboards.client_kb import main_menu

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

# Используем "contains" - сработает, если в тексте есть это слово
@router.message(F.text.contains("Поздороваться"))
async def cmd_hello(message: types.Message):
    await message.answer("Привет-привет! Рад тебя видеть!")

@router.message(F.text.contains("О боте"))
async def cmd_info(message: types.Message):
    await message.answer("Я тестовый бот, написанный на Python! 🐍")

@router.message(F.text.contains("кубик"))
async def cmd_dice(message: types.Message):
    await message.answer_dice(emoji="🎲")

# --- ОБРАБОТКА ИНЛАЙН КНОПОК ---

# Ловим нажатие на кнопку "О боте"

@router.callback_query(F.data == "about_btn")
async def cb_about(callback: types.CallbackQuery):
	# 1. Отвечаем всплывашкой (чтобы часики на кнопке пропали)
	await callback.answer("Загружаю инфу...", show_alter=False)

	# 2. Отправляем сообщение
	await callback.message.answer("Я бот на Python! Могу считать валюту и болтать.")

# Ловим нажатие на кнопку "Кубик"

@router.callback_query(F.data == "dice_btn")
async def cb_dice(callback: types.CallbackQuery):
	await callback.answer() # Просто убираем часики
	await callback.message.answer_dice()
