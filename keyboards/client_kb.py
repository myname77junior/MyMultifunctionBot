from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Создаем кнопки (объекты)
# Текст = То, что видит юзер
# callback_data = Команда, которая прилетит боту скрытно

btn1 = InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile_btn")
btn2 = InlineKeyboardButton(text="🤖 Чат с ИИ", callback_data="ai_btn")
btn3 = InlineKeyboardButton(text="💵 Курсы валют", callback_data="rates_btn")
btn4 = InlineKeyboardButton(text="🌤 Погода", callback_data="weather_btn")
btn5 = InlineKeyboardButton(text="🧘 Цитата дня", callback_data="quote_btn")
btn6 = InlineKeyboardButton(text="ℹ️ О боте", callback_data="about_btn")

# Собираем клавиатуру (список списков = ряды кнопок)
main_menu = InlineKeyboardMarkup(
	inline_keyboard=[
		[btn1, btn2], 	# Первый ряд (две кнопки)
		[btn3, btn4],	# Второй ряд (две кнопки)
		[btn5],
		[btn6]		# Третий ряд (одна кнопка)
	]
)

back_kb = InlineKeyboardMarkup(
	inline_keyboard=[
		[InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_home")]
	]
)
