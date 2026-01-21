import os
from gigachat import GigaChat

# Функция должна быть ASYNC, чтобы не тормозить бота
async def get_chat_response(user_text):
	"""
	Отправляем сообщение в GigaChat и ждем ответ асинхронно
	"""
	token = os.getenv("GIGACHAT_KEY")

	if not token:
		return "⚠️ Ошибка: Не найден ключ GIGACHAT_KEY в настройках."

	try:
		# Используем async with (асинхронный контекстный менеджер)
		with GigaChat(credentials=token, verify_ssl_certs=False) as giga:

			# 2. Формируем правильную структуру сообщения для нейросети
			# Ей нужен список, где указано, кто пишет (user) и что пишет (content)
			payload = {
				"messages": [
					{"role": "user", "content": user_text}
				]
			}

			# 3. Отправляем запрос
			response = giga.chat(payload)

			return response.choices[0].message.content

	except Exception as e:
		print(f"🔥 Ошибка GigaChat: {e}")
		return f"Не могу ответить сейчас. Ошибка подключения: {e}"

