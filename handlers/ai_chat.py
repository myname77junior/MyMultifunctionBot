from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states import Form
from keyboards.client_kb import back_kb
from ai_assistant import get_chat_response

router = Router()

# --- 1. ВХОД В ЧАТ (Нажатие кнопки "Чат с ИИ") ---
@router.callback_query(F.data == "ai_btn")
async def start_ai_chat(callback: types.CallbackQuery, state: FSMContext):
	await callback.message.edit_text(
		"🤖 <b>Gigachat на связи!</b>\n\n"
		"Я готов отвечать на твои вопросы. Спрашивай что угодно!\n"
		"<i>(Чтобы выйти, нажми кнопку 'Назад в меню')</i>",
		parse_mode="HTML",
		reply_markup=back_kb
	)
	# Включаем состояние "Чат активен"
	await state.set_state(Form.chat_active)


# --- 2. ОБРАБОТКА ВОПРОСОВ (Работает только в состоянии chat_active) ---
@router.message(Form.chat_active)
async def process_ai_message(message: types.Message):
	# Показываем статус "печатает..."
	await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

	# Просто берем текст пользователя
	user_text = message.text

	# Получаем ответ от ИИ
	ai_answer = await get_chat_response(user_text)

	# Отправляем ответ + кнопку Назад
	await message.answer(ai_answer, reply_markup=back_kb)
