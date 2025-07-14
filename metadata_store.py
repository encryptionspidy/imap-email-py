"""Handles all database interactions using SQLite."""
import sqlite3
from typing import List, Dict
from config import Config

class MetadataStore:
    """SQLite handler for email metadata storage."""
    def __init__(self):
        self.connection = sqlite3.connect(Config.DB_PATH)
        self._create_tables()

    def _create_tables(self):
        with self.connection:
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS emails (
                    uid TEXT PRIMARY KEY,
                    uidvalidity INTEGER,
                    subject TEXT,
                    sender TEXT,
                    date TIMESTAMP,
                    body TEXT
                )
            ''')
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            print("Tables are created or verified existing.")

    def update_emails(self, emails: List[Dict]):
        """Update or insert emails into the database."""
        with self.connection:
            for email in emails:
                self.connection.execute('''
                    INSERT OR REPLACE INTO emails (uid, uidvalidity, subject, sender, date, body)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    email['uid'], 
                    email.get('uidvalidity', 0), 
                    email.get('subject', ''), 
                    email.get('sender', ''), 
                    email.get('date', ''), 
                    email.get('body', '')
                ))
        print(f"[green]Updated {len(emails)} emails in database")

    def list_emails(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT uid, subject, sender, date FROM emails ORDER BY date DESC')
        return cursor.fetchall()

    def get_email(self, uid: str):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM emails WHERE uid = ?', (uid,))
        return cursor.fetchone()

    def clear(self):
        with self.connection:
            self.connection.execute('DELETE FROM emails')
    
    def set_last_fetch_time(self, timestamp: str):
        """Set the last fetch timestamp."""
        with self.connection:
            self.connection.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)', ('last_fetch', timestamp))
    
    def get_last_fetch_time(self) -> str:
        """Get the last fetch timestamp."""
        cursor = self.connection.cursor()
        cursor.execute('SELECT value FROM metadata WHERE key = ?', ('last_fetch',))
        result = cursor.fetchone()
        return result[0] if result else 'Never'

    def close(self):
        self.connection.close()

    def __del__(self):
        self.close()

