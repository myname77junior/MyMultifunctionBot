from aiogram import BaseMiddleware
from aiogram.types import Message
import database

class TrackUserMiddleware(BaseMiddleware):
	async def __call__(self, handler, event, data):
	# Если это сообщение и у него есть отправитель
		if isinstance(event, Message) and event.from_user:
			# Молча записываем его в базу (функция сама разберется, новый он или старый)
			database.add_user_to_db(event.from_user.id, event.from_user.username)

		# Передаем управление дальше (обработчикам команд)
		return await handler(event, data)
