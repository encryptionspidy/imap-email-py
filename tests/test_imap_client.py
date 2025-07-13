"""Tests for IMAP client functionality."""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
from pathlib import Path

# Set up environment for testing
os.environ['EMAIL_USER'] = 'test@example.com'
os.environ['EMAIL_PASSWORD'] = 'test_password'
os.environ['EMAIL_PROVIDER'] = 'gmail'

from imap_client import IMAPClient
from email_cleaner import EmailCleaner


class TestIMAPClient(unittest.TestCase):
    """Test cases for IMAPClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_email_data = b"""Subject: Test Email
From: sender@example.com
To: recipient@example.com
Date: Sat, 13 Jul 2025 14:32:00 +0530
Message-ID: <test@example.com>

This is a test email body.
"""
    
    @patch('imap_client.Config.validate_credentials')
    @patch('imap_client.imaplib.IMAP4_SSL')
    def test_imap_client_init_success(self, mock_imap4_ssl, mock_validate):
        """Test successful IMAP client initialization."""
        mock_validate.return_value = True
        mock_imap_instance = MagicMock()
        mock_imap4_ssl.return_value = mock_imap_instance
        
        client = IMAPClient()
        
        self.assertIsNotNone(client.mail)
        self.assertEqual(client.mail, mock_imap_instance)
        mock_imap_instance.login.assert_called_once()
    
    @patch('imap_client.Config.validate_credentials')
    def test_imap_client_init_invalid_credentials(self, mock_validate):
        """Test IMAP client initialization with invalid credentials."""
        mock_validate.return_value = False
        
        with self.assertRaises(ValueError):
            IMAPClient()
    
    @patch('imap_client.Config.validate_credentials')
    @patch('imap_client.imaplib.IMAP4_SSL')
    def test_fetch_email_batch(self, mock_imap4_ssl, mock_validate):
        """Test fetching a batch of emails."""
        mock_validate.return_value = True
        mock_imap_instance = MagicMock()
        mock_imap4_ssl.return_value = mock_imap_instance
        
        # Mock email fetch response
        mock_imap_instance.fetch.return_value = ('OK', [(b'1 (RFC822 {123}', self.test_email_data)])
        
        client = IMAPClient()
        client.current_uidvalidity = 123456
        
        # Test batch fetching
        emails = client._fetch_email_batch([b'1'])
        
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0]['uid'], '1')
        self.assertEqual(emails[0]['subject'], 'Test Email')
        self.assertEqual(emails[0]['uidvalidity'], 123456)
    
    @patch('imap_client.Config.validate_credentials')
    @patch('imap_client.imaplib.IMAP4_SSL')
    def test_check_uid_validity(self, mock_imap4_ssl, mock_validate):
        """Test UID validity checking."""
        mock_validate.return_value = True
        mock_imap_instance = MagicMock()
        mock_imap4_ssl.return_value = mock_imap_instance
        
        # Mock status response
        mock_imap_instance.status.return_value = ('OK', [b'INBOX (UIDVALIDITY 123456)'])
        
        client = IMAPClient()
        
        # Test with no existing UID validity file
        with patch('imap_client.Path.exists', return_value=False):
            with patch('builtins.open', mock_open()) as mock_file:
                result = client.check_uid_validity()
                self.assertFalse(result)  # First run, no change
                mock_file.assert_called()
        
        # Test with existing UID validity file (same value)
        with patch('imap_client.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='123456')):
                result = client.check_uid_validity()
                self.assertFalse(result)  # No change
        
        # Test with existing UID validity file (different value)
        with patch('imap_client.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='654321')):
                with patch('builtins.open', mock_open()) as mock_write:
                    result = client.check_uid_validity()
                    self.assertTrue(result)  # Change detected
    
    @patch('imap_client.Config.validate_credentials')
    @patch('imap_client.imaplib.IMAP4_SSL')
    def test_fetch_emails_success(self, mock_imap4_ssl, mock_validate):
        """Test successful email fetching."""
        mock_validate.return_value = True
        mock_imap_instance = MagicMock()
        mock_imap4_ssl.return_value = mock_imap_instance
        
        # Mock search and fetch responses
        mock_imap_instance.select.return_value = ('OK', [])
        mock_imap_instance.search.return_value = ('OK', [b'1 2 3'])
        mock_imap_instance.fetch.return_value = ('OK', [(b'1 (RFC822 {123}', self.test_email_data)])
        
        client = IMAPClient()
        client.current_uidvalidity = 123456
        
        emails = client.fetch_emails()
        
        self.assertEqual(len(emails), 3)  # 3 UIDs were returned
        mock_imap_instance.select.assert_called_once()
        mock_imap_instance.search.assert_called_once()
    
    @patch('imap_client.Config.validate_credentials')
    @patch('imap_client.imaplib.IMAP4_SSL')
    def test_fetch_emails_empty_result(self, mock_imap4_ssl, mock_validate):
        """Test email fetching with empty result."""
        mock_validate.return_value = True
        mock_imap_instance = MagicMock()
        mock_imap4_ssl.return_value = mock_imap_instance
        
        # Mock empty search result
        mock_imap_instance.select.return_value = ('OK', [])
        mock_imap_instance.search.return_value = ('OK', [b''])
        
        client = IMAPClient()
        
        emails = client.fetch_emails()
        
        self.assertEqual(len(emails), 0)
    
    @patch('imap_client.Config.validate_credentials')
    @patch('imap_client.imaplib.IMAP4_SSL')
    def test_fetch_emails_search_failure(self, mock_imap4_ssl, mock_validate):
        """Test email fetching with search failure."""
        mock_validate.return_value = True
        mock_imap_instance = MagicMock()
        mock_imap4_ssl.return_value = mock_imap_instance
        
        # Mock search failure
        mock_imap_instance.select.return_value = ('OK', [])
        mock_imap_instance.search.return_value = ('NO', [])
        
        client = IMAPClient()
        
        emails = client.fetch_emails()
        
        self.assertEqual(len(emails), 0)


if __name__ == '__main__':
    unittest.main()
