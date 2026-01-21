from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
import database
import os
import html  # <--- ВАЖНЫЙ ИМПОРТ ДЛЯ ЗАЩИТЫ ТЕКСТА

router = Router()

# Твой ID
ADMIN_ID = 260124758 

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен!")
        return

    count = database.get_users_count()
    
    text = (
        f"👨‍✈️ <b>Панель Админа</b>\n\n"
        f"👥 <b>Всего пользователей:</b> {count}\n"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📥 Скачать базу", callback_data="get_db")],
        [types.InlineKeyboardButton(text="📢 Рассылка (тест)", callback_data="broadcast")]
    ])
    
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

# --- КНОПКА СКАЧИВАНИЯ БАЗЫ ---
@router.callback_query(lambda c: c.data == "get_db")
async def cb_get_db(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    # Отправляем файл
    if os.path.exists("bot_database.db"):
        db_file = FSInputFile("bot_database.db")
        await callback.message.answer_document(db_file, caption="📂 База данных")
    else:
        await callback.answer("База данных не найдена!", show_alert=True)
    
    await callback.answer()

# --- КОМАНДЫ ТОП И ЛИСТ (С ЗАЩИТОЙ HTML) ---

@router.message(Command("top"))
async def cmd_top(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    top_users = database.get_top_users()
    text = "🏆 <b>Топ активных пользователей:</b>\n\n"
    
    for index, user in enumerate(top_users):
        # user[0] = name, user[1] = count
        # Экранируем имя! Если там есть скобки < >, они не сломают бота
        safe_name = html.escape(user[0]) if user[0] else "Без ника"
        text += f"{index +1}. 👤 {safe_name} - {user[1]} сообщ. \n"

    await message.answer(text, parse_mode="HTML")

@router.message(Command("list"))
async def cmd_list(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    users = database.get_all_users()
    answer_text = "📋 <b>Список пользователей:</b>\n\n"
    
    for user in users:
        # user[1] = username
        safe_name = html.escape(user[1]) if user[1] else "Без ника"
        answer_text += f"👤 <b>{safe_name}</b> (ID: {user[0]}) - {user[2]} сообщ.\n"

    await message.answer(answer_text, parse_mode="HTML")

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    count = database.get_users_count()
    text = f"📊 <b>Статистика бота:</b>\n\n👥 В базе: {count} человек"
    await message.answer(text, parse_mode="HTML")

@router.message(Command("logs"))
async def cmd_send_logs(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    if os.path.exists("logs.csv"):
        log_file = FSInputFile("logs.csv")
        await message.answer_document(log_file, caption="📂 Логи")
    else:
        await message.answer("Файла с логами пока нет.")
