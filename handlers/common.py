from aiogram import Router, types, F
from aiogram.filters.command import Command

router = Router()

# --- ХЕНДЛЕРЫ ---

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот. Жми кнопки!")

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
