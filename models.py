import sqlite3
from datetime import datetime, timedelta

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


def insert_event(first_name: str, last_name: str, birthday: datetime, description: str):
    try:
        cursor.execute('''
            INSERT INTO users_birthdays (first_name, last_name, birthday, description)
            VALUES (?, ?, ?, ?)
        ''', (first_name, last_name, birthday.strftime('%Y-%m-%d %H:%M:%S'), description))
        conn.commit()  # Сохранение изменений в базе данных
    except Exception as e:
        print(f"Произошла ошибка при записи данных: {e}")


def get_events():
    try:
        cursor.execute('SELECT * FROM `users_birthdays`')
        rows = cursor.fetchall()  # Извлекаем все строки из курсора

        # Преобразуем результат в список словарей (каждая строка - словарь)
        events = []
        for row in rows:
            event = {
                'id': row[0],
                'name': row[1],
                'last_name': row[2],
                'birthday': row[3],
                'description': row[4]
            }
            events.append(event)

        conn.commit()
        return events  # Возвращаем список событий
    except Exception as e:
        print(f"Произошла ошибка при сборе данных: {e}")
        return []  # Возвращаем пустой список в случае ошибки

def get_event_by_id(event_id):
    try:
        cursor.execute('SELECT * FROM `users_birthdays` WHERE `id` = ?', (event_id,))
        event = cursor.fetchone()
        return event
    except Exception as e:
        print(f"Произошла ошибка при получении события: {e}")
        return None

def update_event(event_id, event):
    event_dict = {
        'name': event[1],
        'last_name': event[2],
        'birthday': event[3],
        'description': event[4]
    }
    try:
        cursor.execute('UPDATE users_birthdays SET first_name = ?, last_name = ?, birthday = ?, description = ? WHERE id = ?', (
            event_dict['name'], event_dict['last_name'], event_dict['birthday'], event_dict['description'], event_id))
        conn.commit()
    except Exception as e:
        print(f"Произошла ошибка при обновлении события: {e}")


async def perform_delete_event(event_id):
    try:
        cursor.execute('DELETE FROM users_birthdays WHERE id = ?', (event_id,))
        conn.commit()
        return True  # Успешное удаление
    except Exception as e:
        print(f"Произошла ошибка при удалении события: {e}")
        return False  # Ошибка при удалении

async def get_event_for_tomorrow():
    try:
        current_datetime = datetime.now()
        next_day = current_datetime + timedelta(days=1)
        next_day_str = next_day.strftime('%m-%d')  # Форматируем дату как ММ-ДД
        cursor.execute('SELECT * FROM users_birthdays WHERE strftime("%m-%d", birthday) = ?', (next_day_str,))
        events = cursor.fetchall()
        conn.commit()
        return events
    except Exception as e:
        print(f"Произошла ошибка при сборе данных: {e}")
        return False
    
async def get_event_for_week():
    try:
        current_datetime = datetime.now()
        week = current_datetime + timedelta(days=7)
        week_str = week.strftime('%m-%d')  # Форматируем дату как ММ-ДД
        cursor.execute('SELECT * FROM users_birthdays WHERE strftime("%m-%d", birthday) = ?', (week_str,))
        events = cursor.fetchall()
        conn.commit()
        return events
    except Exception as e:
        print(f"Произошла ошибка при сборе данных: {e}")
        return False

### Попробовать выдавать одно красивое сообщения в телегу раз в день
### Дополнить базу событиями
async def get_event_for_today():
    try:
        current_datetime = datetime.now()
        today = current_datetime
        today_str = today.strftime('%m-%d')  # Форматируем дату как ММ-ДД
        cursor.execute('SELECT * FROM users_birthdays WHERE strftime("%m-%d", birthday) = ?', (today_str,))
        events = cursor.fetchall()
        conn.commit()
        return events
    except Exception as e:
        print(f"Произошла ошибка при сборе данных: {e}")
        return False



# Создание таблицы и вставка данных
create_users()
create_users_birthdays()
