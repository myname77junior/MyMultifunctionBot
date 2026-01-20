from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Создаем кнопки (объекты)
# Текст = То, что видит юзер
# callback_data = Команда, которая прилетит боту скрытно

btn1 = InlineKeyboardButton(text="ℹ️ О боте", callback_data="about_btn")
btn2 = InlineKeyboardButton(text="💵 Курсы валют", callback_data="rates_btn")
btn3 = InlineKeyboardButton(text="🎲 Кинуть кубик", callback_data="dice_btn")

# Собираем клавиатуру (список списков = ряды кнопок)
main_menu = InlineKeyboardMarkup(
	inline_keyboard=[
		[btn1, btn2], # Первый ряд (две кнопки)
		[btn3]	      # Второй ряд (одна кнопка)
	]
)
