import sqlite3
from datetime import datetime

conn = sqlite3.connect('db.sqlite')
cursor = conn.cursor()

def create_users():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE,
            username VARCHAR(50) NOT NULL,
            first_name VARCHAR(50),
            last_name VARCHAR(50)
        )
    ''')

def create_users_birthdays():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users_birthdays (
            id INTEGER PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            birthday DATETIME NOT NULL,
            description TEXT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

def new_bot_users(user_id, user_name, first_name, last_name):
    try:
        cursor.execute(f'''
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES('{int(user_id)}', '{user_name}', '{first_name}', '{last_name}')
        ''')
        conn.commit()  # Сохранение изменений в базе данных
    except Exception as e:
        print(f"Произошла ошибка при вставке данных: {e}")


def insert_birthday(first_name: str, last_name: str, birthday: datetime, description: str):
    try:
        cursor.execute('''
            INSERT INTO users_birthdays (first_name, last_name, birthday, description)
            VALUES (?, ?, ?, ?)
        ''', (first_name, last_name, birthday.strftime('%Y-%m-%d %H:%M:%S'), description))
        conn.commit()  # Сохранение изменений в базе данных
    except Exception as e:
        print(f"Произошла ошибка при записи данных: {e}")

# Создание таблицы и вставка данных
create_users()
create_users_birthdays()
