from aiogram.fsm.state import StatesGroup, State

# Создаем класс-шаблон анкеты
class Form(StatesGroup):
	name = State()	# Шаг 1: Ждем имя
	age = State()	# Шаг 2: Ждем возраст
	bio = State()	# Шаг 3: Ждем описание о себе
	city_request = State() 
	# Добавляем новое состояние для чата
	chat_active = State()
