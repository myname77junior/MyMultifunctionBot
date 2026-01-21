import sqlite3
import datetime

# --- ИНИЦИАЛИЗАЦИЯ (Создание таблиц) ---
def create_tables():
	conn = sqlite3.connect('bot_database.db')
	cursor = conn.cursor()

	# 1. Таблица пользователей (Для счетчика сообщений)
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY,
			username TEXT,
			first_seen TEXT,
			messages_count INTEGER DEFAULT 0
		)
	""")

	# 2. Таблица анкет (НОВАЯ: Для имени, возраста и био)
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS profiles (
			user_id INTEGER PRIMARY KEY,
			name TEXT,
			age INTEGER,
			bio TEXT
		)
	''')

	conn.commit()
	conn.close()

# --- ФУНКЦИИ ДЛЯ АНКЕТЫ (НОВЫЕ) ---
def save_profile(user_id, name, age, bio):
	conn = sqlite3.connect("bot_database.db")
	cursor = conn.cursor()
	cursor.execute('''
		INSERT OR REPLACE INTO profiles (user_id, name, age, bio)
		VALUES (?, ?, ?, ?)
	''', (user_id, name, age, bio))
	conn.commit()
	conn.close()



def get_top_users():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, messages_count FROM users ORDER BY messages_count DESC LIMIT 3")
    users = cursor.fetchall()
    conn.close()
    return users

def update_user_counter(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    query = "UPDATE users SET messages_count = messages_count + 1 WHERE id = ?"
    cursor.execute(query, (user_id,))
    conn.commit()
    conn.close()

def get_users_count():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    # Мы просим: "Посчитай мне количество всех записей"
    cursor.execute("SELECT COUNT(*) FROM users")
    result = cursor.fetchone()
    count = result[0]
    conn.close()
    return count

def get_all_users():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, messages_count FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def add_user_to_db(user_id, username):
    # 1. Подключаемся (или создаем файл, если его нет)
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    # 2. Создаем таблицу (на всякий случай, вдруг файл удалили)

	# 2.1 UPD: Убрали создание таблицы от сюда, так как теперь она создаётся в create_tables

    # 3. Время регистрации
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 4. ХИТРЫЙ ЗАПРОС: Вставь, ИЛИ пропусти, если уже есть
    query = "INSERT OR IGNORE INTO users (id, username, first_seen) VALUES (?, ?, ?)"
    cursor.execute(query, (user_id, username, now))

    # 5. Сохраняем и уходим
    conn.commit()
    conn.close()

# --- ЧТЕНИЕ АНКЕТЫ ---
def get_profile(user_id):
	conn = sqlite3.connect("bot_database.db")
	cursor = conn.cursor()
	# Ищем пользователя по ID
	cursor.execute("SELECT name, age, bio FROM profiles WHERE user_id = ?", (user_id,))
	profile = cursor.fetchone()
	conn.close()
	return profile
