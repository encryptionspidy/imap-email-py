"""Tests for metadata store functionality."""
import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import tempfile
import os

from metadata_store import MetadataStore


class TestMetadataStore(unittest.TestCase):
    """Test cases for MetadataStore class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_emails = [
            {
                'uid': '1',
                'subject': 'Test Email 1',
                'sender': 'sender1@example.com',
                'body': 'This is the first test email',
                'date': '2025-07-13',
                'uidvalidity': 123456,
                'verification_codes': ['123456']
            },
            {
                'uid': '2',
                'subject': 'Test Email 2',
                'sender': 'sender2@example.com',
                'body': 'This is the second test email',
                'date': '2025-07-14',
                'uidvalidity': 123456,
                'verification_codes': []
            }
        ]
    
    def test_init_creates_tables(self):
        """Test that MetadataStore initialization creates tables."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            with patch('metadata_store.Config.DB_PATH', temp_db_path):
                store = MetadataStore()
                
                # Check that table was created
                cursor = store.connection.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails'")
                result = cursor.fetchone()
                self.assertIsNotNone(result)
                
                store.close()
        finally:
            os.unlink(temp_db_path)
    
    def test_update_emails(self):
        """Test updating emails in the database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            with patch('metadata_store.Config.DB_PATH', temp_db_path):
                store = MetadataStore()
                
                # Update emails
                store.update_emails(self.test_emails)
                
                # Check that emails were inserted
                cursor = store.connection.cursor()
                cursor.execute('SELECT COUNT(*) FROM emails')
                count = cursor.fetchone()[0]
                self.assertEqual(count, 2)
                
                # Check specific email data
                cursor.execute('SELECT uid, subject, sender, verification_code FROM emails WHERE uid = ?', ('1',))
                result = cursor.fetchone()
                self.assertEqual(result[0], '1')
                self.assertEqual(result[1], 'Test Email 1')
                self.assertEqual(result[2], 'sender1@example.com')
                self.assertEqual(result[3], 1)  # Has verification code
                
                store.close()
        finally:
            os.unlink(temp_db_path)
    
    def test_update_emails_replace(self):
        """Test that updating emails replaces existing ones."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            with patch('metadata_store.Config.DB_PATH', temp_db_path):
                store = MetadataStore()
                
                # Insert initial emails
                store.update_emails(self.test_emails)
                
                # Update with modified data
                modified_emails = [
                    {
                        'uid': '1',
                        'subject': 'Modified Test Email 1',
                        'sender': 'modified@example.com',
                        'body': 'Modified body',
                        'date': '2025-07-15',
                        'uidvalidity': 123456,
                        'verification_codes': []
                    }
                ]
                
                store.update_emails(modified_emails)
                
                # Check that count is still 2 (one replaced, one unchanged)
                cursor = store.connection.cursor()
                cursor.execute('SELECT COUNT(*) FROM emails')
                count = cursor.fetchone()[0]
                self.assertEqual(count, 2)
                
                # Check that email was replaced
                cursor.execute('SELECT subject, sender FROM emails WHERE uid = ?', ('1',))
                result = cursor.fetchone()
                self.assertEqual(result[0], 'Modified Test Email 1')
                self.assertEqual(result[1], 'modified@example.com')
                
                store.close()
        finally:
            os.unlink(temp_db_path)
    
    def test_list_emails(self):
        """Test listing emails from the database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            with patch('metadata_store.Config.DB_PATH', temp_db_path):
                store = MetadataStore()
                
                # Insert test emails
                store.update_emails(self.test_emails)
                
                # List emails
                emails = store.list_emails()
                
                self.assertEqual(len(emails), 2)
                # Check that emails are ordered by date DESC
                self.assertEqual(emails[0][0], '2')  # UID of more recent email
                self.assertEqual(emails[1][0], '1')  # UID of older email
                
                store.close()
        finally:
            os.unlink(temp_db_path)
    
    def test_get_email(self):
        """Test getting a specific email from the database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            with patch('metadata_store.Config.DB_PATH', temp_db_path):
                store = MetadataStore()
                
                # Insert test emails
                store.update_emails(self.test_emails)
                
                # Get specific email
                email = store.get_email('1')
                
                self.assertIsNotNone(email)
                self.assertEqual(email[0], '1')  # UID
                self.assertEqual(email[2], 'Test Email 1')  # Subject
                
                # Test non-existent email
                email = store.get_email('999')
                self.assertIsNone(email)
                
                store.close()
        finally:
            os.unlink(temp_db_path)
    
    def test_clear(self):
        """Test clearing all emails from the database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            with patch('metadata_store.Config.DB_PATH', temp_db_path):
                store = MetadataStore()
                
                # Insert test emails
                store.update_emails(self.test_emails)
                
                # Verify emails exist
                cursor = store.connection.cursor()
                cursor.execute('SELECT COUNT(*) FROM emails')
                count = cursor.fetchone()[0]
                self.assertEqual(count, 2)
                
                # Clear emails
                store.clear()
                
                # Verify emails are cleared
                cursor.execute('SELECT COUNT(*) FROM emails')
                count = cursor.fetchone()[0]
                self.assertEqual(count, 0)
                
                store.close()
        finally:
            os.unlink(temp_db_path)
    
    def test_close_and_del(self):
        """Test closing the database connection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            with patch('metadata_store.Config.DB_PATH', temp_db_path):
                store = MetadataStore()
                connection = store.connection
                
                # Close manually
                store.close()
                
                # Connection should be closed
                with self.assertRaises(sqlite3.ProgrammingError):
                    connection.execute('SELECT 1')
                
                # Test __del__ method
                store2 = MetadataStore()
                connection2 = store2.connection
                del store2
                
                # Connection should be closed after __del__
                with self.assertRaises(sqlite3.ProgrammingError):
                    connection2.execute('SELECT 1')
                
        finally:
            try:
                os.unlink(temp_db_path)
            except FileNotFoundError:
                pass


if __name__ == '__main__':
    unittest.main()
