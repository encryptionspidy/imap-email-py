import unittest
from unittest.mock import patch, MagicMock
import os
from config import Config

class TestConfig(unittest.TestCase):
    
    @patch.object(Config, 'EMAIL_USER', 'test@example.com')
    @patch.object(Config, 'EMAIL_PASSWORD', 'password123')
    def test_validate_credentials_success(self):
        """Test successful credential validation."""
        self.assertTrue(Config.validate_credentials())
    
    @patch.object(Config, 'EMAIL_USER', '')
    @patch.object(Config, 'EMAIL_PASSWORD', '')
    def test_validate_credentials_failure(self):
        """Test credential validation failure."""
        self.assertFalse(Config.validate_credentials())
    
    @patch.object(Config, 'EMAIL_PROVIDER', 'gmail')
    def test_get_provider_config_gmail(self):
        """Test Gmail provider configuration."""
        config = Config.get_provider_config()
        self.assertEqual(config['imap_host'], 'imap.gmail.com')
        self.assertEqual(config['imap_port'], 993)
        self.assertTrue(config['use_ssl'])
        self.assertTrue(config['requires_app_password'])
    
    @patch.object(Config, 'EMAIL_PROVIDER', 'outlook')
    def test_get_provider_config_outlook(self):
        """Test Outlook provider configuration."""
        config = Config.get_provider_config()
        self.assertEqual(config['imap_host'], 'outlook.office365.com')
        self.assertEqual(config['imap_port'], 993)
        self.assertTrue(config['use_ssl'])
        self.assertFalse(config['requires_app_password'])
    
    @patch.object(Config, 'EMAIL_PROVIDER', 'unsupported')
    def test_get_provider_config_invalid(self):
        """Test invalid provider configuration."""
        with self.assertRaises(ValueError) as context:
            Config.get_provider_config()
        self.assertIn('Unsupported email provider', str(context.exception))
    
    @patch.object(Config, 'EMAIL_PROVIDER', 'custom')
    @patch.object(Config, 'IMAP_HOST', 'custom.example.com')
    @patch.object(Config, 'IMAP_PORT', 1234)
    def test_get_provider_config_custom(self):
        """Test custom provider configuration."""
        config = Config.get_provider_config()
        self.assertEqual(config['imap_host'], 'custom.example.com')
        self.assertEqual(config['imap_port'], 1234)
    
    def test_get_supported_providers(self):
        """Test getting list of supported providers."""
        providers = Config.get_supported_providers()
        expected_providers = ['gmail', 'outlook', 'yahoo', 'tuta', 'protonmail', 'icloud', 'fastmail', 'custom']
        self.assertEqual(set(providers), set(expected_providers))
    
    @patch.object(Config, 'EMAIL_PROVIDER', 'gmail')
    def test_provider_display_name(self):
        """Test provider display name."""
        display_name = Config.get_provider_display_name()
        self.assertEqual(display_name, 'Gmail')
    
    @patch.object(Config, 'EMAIL_PROVIDER', 'unknown')
    def test_provider_display_name_unknown(self):
        """Test provider display name for unknown provider."""
        display_name = Config.get_provider_display_name()
        self.assertEqual(display_name, 'Unknown')

if __name__ == '__main__':
    unittest.main()
