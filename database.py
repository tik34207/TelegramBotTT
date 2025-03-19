import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            country TEXT,
            account TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            format TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS log (
            id INTEGER PRIMARY KEY,
            action TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            account_id INTEGER,
            FOREIGN KEY(account_id) REFERENCES accounts(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY,
            country TEXT,
            account TEXT,
            retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            format TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS formats (
            id INTEGER PRIMARY KEY,
            format TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_country(country):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('INSERT INTO countries (name) VALUES (?)', (country,))
    conn.commit()
    conn.close()

def get_countries():
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('SELECT * FROM countries')
    countries = c.fetchall()
    conn.close()
    return countries

def add_account(country, account, format):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('INSERT INTO accounts (country, account, format) VALUES (?, ?, ?)', (country, account, format))
    conn.commit()
    conn.close()

def get_accounts(country, number):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('SELECT id, account FROM accounts WHERE country = ? ORDER BY added_at ASC LIMIT ?', (country, number))
    accounts = c.fetchall()
    # Log the retrieval action and add to history
    for account in accounts:
        c.execute('INSERT INTO log (action, account_id) VALUES ("retrieve", ?)', (account[0],))
        c.execute('INSERT INTO history (country, account, format) SELECT country, account, format FROM accounts WHERE id = ?', (account[0],))
        c.execute('DELETE FROM accounts WHERE id = ?', (account[0],))
    conn.commit()
    conn.close()
    return [account[1] for account in accounts]

def view_accounts():
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('SELECT country, account FROM accounts')
    accounts = c.fetchall()
    conn.close()
    return accounts

def delete_country(country):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('DELETE FROM countries WHERE name = ?', (country,))
    c.execute('DELETE FROM accounts WHERE country = ?', (country,))
    conn.commit()
    conn.close()

def get_total_accounts():
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM accounts')
    total = c.fetchone()[0]
    conn.close()
    return total

def delete_all_accounts():
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('DELETE FROM accounts')
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    now = datetime.now()
    start_day = now - timedelta(days=1)
    start_week = now - timedelta(weeks=1)
    start_month = now - timedelta(days=30)

    c.execute('SELECT COUNT(*) FROM accounts WHERE added_at >= ?', (start_day,))
    added_day = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM accounts WHERE added_at >= ?', (start_week,))
    added_week = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM accounts WHERE added_at >= ?', (start_month,))
    added_month = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM history WHERE retrieved_at >= ?', (start_day,))
    retrieved_day = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM history WHERE retrieved_at >= ?', (start_week,))
    retrieved_week = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM history WHERE retrieved_at >= ?', (start_month,))
    retrieved_month = c.fetchone()[0]

    conn.close()
    return f"Добавлено аккаунтов: День: {added_day}, Неделя: {added_week}, Месяц: {added_month}\nПолучено аккаунтов: День: {retrieved_day}, Неделя: {retrieved_week}, Месяц: {retrieved_month}"

def get_account_dates(country):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('SELECT MIN(added_at), MAX(added_at) FROM accounts WHERE country = ?', (country,))
    first_added, last_added = c.fetchone()
    conn.close()

    if first_added and last_added:
        now = datetime.now()
        first_added_dt = datetime.strptime(first_added, "%Y-%m-%d %H:%M:%S")
        last_added_dt = datetime.strptime(last_added, "%Y-%m-%d %H:%M:%S")
        days_since_first = (now - first_added_dt).days
        hours_since_first = (now - first_added_dt).seconds // 3600
        days_since_last = (now - last_added_dt).days
        hours_since_last = (now - last_added_dt).seconds // 3600
        return {
            "first_added": first_added,
            "last_added": last_added,
            "days_since_first": days_since_first,
            "hours_since_first": hours_since_first,
            "days_since_last": days_since_last,
            "hours_since_last": hours_since_last
        }
    return None

def get_history(country, page, per_page=10):
    offset = (page - 1) * per_page
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('SELECT account FROM history WHERE country = ? ORDER BY retrieved_at DESC LIMIT ? OFFSET ?', (country, per_page, offset))
    accounts = [row[0] for row in c.fetchall()]
    conn.close()
    return accounts

def clean_old_history():
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    three_days_ago = datetime.now() - timedelta(days=3)
    c.execute('DELETE FROM history WHERE retrieved_at < ?', (three_days_ago,))
    conn.commit()
    conn.close()

def add_format(format):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('INSERT INTO formats (format) VALUES (?)', (format,))
    conn.commit()
    conn.close()

def delete_format(format):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('DELETE FROM formats WHERE format = ?', (format,))
    conn.commit()
    conn.close()

def get_formats():
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('SELECT format FROM formats')
    formats = [row[0] for row in c.fetchall()]
    conn.close()
    return formats
