import os
from dotenv import load_dotenv
from gigachat import GigaChat

load_dotenv()

GIGACHAT_KEY = os.getenv("GIGACHAT_KEY")

def get_chat_response(chat_history):
    """
    Отправляем историю переписки в GigaChat
    """
    try:
        # Подключаемся. verify_ssl_certs=False важно для серверов
        with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False) as giga:

            request_body = {
                "messages": chat_history
            }

            response = giga.chat(request_body)

            return response.choices[0].message.content

    except Exception as e:
        print(f"Ошибка GigaChat: {e}")
        return "Ой, ошибка подключения: {e}"

