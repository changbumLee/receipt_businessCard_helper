# db/db_handler.py
import sqlite3

class DBHandler:
    def __init__(self, db_name='db/records.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # 영수증 테이블
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_name TEXT,
                total_amount TEXT,
                transaction_date TEXT,
                memo TEXT,
                image_path TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # 명함 테이블
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS business_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                company TEXT,
                title TEXT,
                phone TEXT,
                email TEXT,
                memo TEXT,
                image_path TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def save_receipt(self, data):
        self.cursor.execute('''
            INSERT INTO receipts (store_name, total_amount, transaction_date, memo, image_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['store_name'], data['total_amount'], data['transaction_date'], data['memo'], data['image_path']))
        self.conn.commit()

    def save_business_card(self, data):
        self.cursor.execute('''
            INSERT INTO business_cards (name, company, title, phone, email, memo, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['company'], data['title'], data['phone'], data['email'], data['memo'], data['image_path']))
        self.conn.commit()

    def get_all_receipts(self):
        self.cursor.execute("SELECT id, store_name, total_amount, transaction_date, memo, timestamp FROM receipts ORDER BY timestamp DESC")
        return self.cursor.fetchall()

    def get_all_business_cards(self):
        self.cursor.execute("SELECT id, name, company, title, phone, email, memo, timestamp FROM business_cards ORDER BY timestamp DESC")
        return self.cursor.fetchall()

    def __del__(self):
        self.conn.close()