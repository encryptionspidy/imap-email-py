import unittest
from unittest.mock import patch, MagicMock
from main import app
from typer.testing import CliRunner
from config import Config

class TestMainCLI(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch('main.Config.validate_credentials')
    @patch('main.IMAPClient')
    @patch('main.MetadataStore')
    @patch('main.EmbeddingManager')
    def test_fetch_emails_success(self, MockEmbeddingManager, MockMetadataStore, MockIMAPClient, mock_validate):
        mock_validate.return_value = True
        mock_imap_client_instance = MockIMAPClient.return_value
        mock_metadata_store_instance = MockMetadataStore.return_value
        mock_embedding_manager_instance = MockEmbeddingManager.return_value
        
        mock_imap_client_instance.check_uid_validity.return_value = False
        mock_imap_client_instance.fetch_emails.return_value = ['email1', 'email2']

        result = self.runner.invoke(app, ['fetch-emails'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Successfully processed 2 emails', result.output)

    @patch('main.Config.validate_credentials')
    def test_fetch_emails_invalid_credentials(self, mock_validate):
        mock_validate.return_value = False
        result = self.runner.invoke(app, ['fetch-emails'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Error: Email credentials not found', result.output)

    @patch('main.MetadataStore')
    def test_list_emails_no_emails(self, MockMetadataStore):
        mock_metadata_store_instance = MockMetadataStore.return_value
        mock_metadata_store_instance.list_emails.return_value = []
        
        result = self.runner.invoke(app, ['list-emails'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('No emails found. Run', result.output)

    @patch('main.MetadataStore')
    def test_list_emails_with_emails(self, MockMetadataStore):
        mock_metadata_store_instance = MockMetadataStore.return_value
        mock_metadata_store_instance.list_emails.return_value = [
            ('1', 'Test Email', 'test@example.com', '2025-07-13')
        ]

        result = self.runner.invoke(app, ['list-emails'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn('Email Metadata', result.output)
        self.assertIn('Test Email', result.output)

if __name__ == '__main__':
    unittest.main()
