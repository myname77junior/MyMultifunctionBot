import requests
def get_smart_quote():
    url = "http://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=ru"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            try:
                data = response.json()

                quote = data.get('quoteText', '')
                author = data.get('quoteAuthor', '')

                if not author:
                    author = "Неизвестный мудрец"

                return f"💡 <b>Мудрость дня:</b>\n\n<i>«{quote}»</i>\n\n© <b>{author}</b>"
            except:
                return f"💡 <b>Мудрость дня:</b>\n\n<i>«Делай что должен, и будь что будет.»</i>\n\n© <b>Марк Аврелий</b> (резервная цитата)"
        else:
            return f"Сайт с цитатами устал (Ошибка {response.status_code})"
        
    except Exception as e:
        return f"Ошибка соединения: {e}"
    
if __name__ == "__main__":
    print(get_smart_quote())
