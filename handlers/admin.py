from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
import database
import os
import html 
import csv # <--- ВАЖНЫЙ ИМПОРТ ДЛЯ ЗАЩИТЫ ТЕКСТА

router = Router()

# Твой ID
ADMIN_ID = 260124758 

kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📥 Скачать базу .db", callback_data="get_db"),types.InlineKeyboardButton(text="📥 Выгрузить базу .csv", callback_data="export_data")],
        [types.InlineKeyboardButton(text="📢 Рассылка (тест)", callback_data="broadcast")]
    ])

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен!")
        return

    count = database.get_users_count()
    
    text = (
        f"👨‍✈️ <b>👑 Привет, Создатель! Чем займемся?</b>\n\n"
        f"👥 <b>Всего пользователей:</b> {count}\n"
    )

    await message.answer(text, reply_markup=kb, parse_mode="HTML")

# --- ЭКСПОРТ ДАННЫХ (НОВАЯ ФУНКЦИЯ) ---
@router.callback_query(F.data == "export_data")
async def cb_export(callback: types.CallbackQuery):
    await callback.message.edit_text("⏳ Генерирую отчет...")

    # 1. Получаем данные из базы
    users = database.get_full_report()

    if not users:
        await callback.message.edit_text("📂 База пуста, выгружать нечего.")
        return
    
    # 2. Имя файла
    file_path = "users_base.csv"

    # 3. Создаем и записываем файл
    # encoding='utf-8-sig' нужен, чтобы Excel на Windows правильно показывал русские буквы
    with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, delimiter=';') # Точка с запятой - стандарт для Excel в РФ

        # Пишем заголовки
        writer.writerow(['User ID', 'Имя', 'Возраст', 'Город', 'О себе'])

        # Пишем данные
        writer.writerows(users)

    # 4. Отправляем файл
    try:
        # FSInputFile - специальный тип для отправки файлов с диска
        await callback.message.answer_document(FSInputFile(file_path), caption="📂 Вот полная база пользователей.")
    except Exception as e:
        await callback.message.answer(f"Ошибка отправки: {e}")
    finally:
        # 5. Убираем за собой (удаляем файл с сервера)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Возвращаем меню
        await callback.message.answer("<b>Админ меню</b>", reply_markup=kb, parse_mode="HTML")


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
