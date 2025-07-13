"""Configuration management for environment variables and paths."""
import os
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for Email CLI app supporting multiple providers."""
    
    # Email credentials
    EMAIL_USER: str = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "gmail").lower()
    
    # IMAP settings (configurable via environment or defaults based on provider)
    IMAP_HOST: str = os.getenv("IMAP_HOST", "")
    IMAP_PORT: int = int(os.getenv("IMAP_PORT", "993"))
    IMAP_USE_SSL: bool = os.getenv("IMAP_USE_SSL", "true").lower() == "true"
    
    # Predefined provider configurations
    PROVIDER_CONFIGS: Dict[str, Dict] = {
        "gmail": {
            "imap_host": "imap.gmail.com",
            "imap_port": 993,
            "use_ssl": True,
            "requires_app_password": True,
            "folder_name": "INBOX"
        },
        "outlook": {
            "imap_host": "outlook.office365.com",
            "imap_port": 993,
            "use_ssl": True,
            "requires_app_password": False,
            "folder_name": "INBOX"
        },
        "yahoo": {
            "imap_host": "imap.mail.yahoo.com",
            "imap_port": 993,
            "use_ssl": True,
            "requires_app_password": True,
            "folder_name": "INBOX"
        },
        "tuta": {
            "imap_host": "mail.tutanota.com",
            "imap_port": 993,
            "use_ssl": True,
            "requires_app_password": False,
            "folder_name": "INBOX"
        },
        "protonmail": {
            "imap_host": "127.0.0.1",  # ProtonMail Bridge
            "imap_port": 1143,
            "use_ssl": False,
            "requires_app_password": False,
            "folder_name": "INBOX"
        },
        "icloud": {
            "imap_host": "imap.mail.me.com",
            "imap_port": 993,
            "use_ssl": True,
            "requires_app_password": True,
            "folder_name": "INBOX"
        },
        "fastmail": {
            "imap_host": "imap.fastmail.com",
            "imap_port": 993,
            "use_ssl": True,
            "requires_app_password": False,
            "folder_name": "INBOX"
        },
        "custom": {
            "imap_host": os.getenv("IMAP_HOST", "localhost"),
            "imap_port": int(os.getenv("IMAP_PORT", "993")),
            "use_ssl": os.getenv("IMAP_USE_SSL", "true").lower() == "true",
            "requires_app_password": False,
            "folder_name": os.getenv("IMAP_FOLDER", "INBOX")
        }
    }
    
    # Database paths
    BASE_DIR: Path = Path(__file__).parent
    DB_PATH: Path = BASE_DIR / "emails.db"
    FAISS_INDEX_PATH: Path = BASE_DIR / "faiss_index.bin"
    FAISS_MAPPING_PATH: Path = BASE_DIR / "faiss_mapping.json"
    
    # Embedding settings
    EMBEDDING_MODEL: str = "multi-qa-mpnet-base-cos-v1"
    EMBEDDING_BATCH_SIZE: int = 64
    FAISS_INDEX_TYPE: str = "IndexHNSWFlat"
    
    # Performance settings
    MAX_EMAILS_PER_BATCH: int = 100
    
    @classmethod
    def validate_credentials(cls) -> bool:
        """Validate that required credentials are present."""
        return bool(cls.EMAIL_USER and cls.EMAIL_PASSWORD)
    
    @classmethod
    def get_provider_config(cls) -> Dict:
        """Get configuration for the current email provider."""
        provider = cls.EMAIL_PROVIDER
        if provider not in cls.PROVIDER_CONFIGS:
            raise ValueError(f"Unsupported email provider: {provider}. Supported providers: {list(cls.PROVIDER_CONFIGS.keys())}")
        
        config = cls.PROVIDER_CONFIGS[provider].copy()
        
        # Override with environment variables if set
        if cls.IMAP_HOST:
            config['imap_host'] = cls.IMAP_HOST
        if cls.IMAP_PORT != 993:  # Only override if explicitly set
            config['imap_port'] = cls.IMAP_PORT
        
        return config
    
    @classmethod
    def get_imap_host(cls) -> str:
        """Get IMAP host for the current provider."""
        return cls.get_provider_config()['imap_host']
    
    @classmethod
    def get_imap_port(cls) -> int:
        """Get IMAP port for the current provider."""
        return cls.get_provider_config()['imap_port']
    
    @classmethod
    def get_use_ssl(cls) -> bool:
        """Get SSL setting for the current provider."""
        return cls.get_provider_config()['use_ssl']
    
    @classmethod
    def get_folder_name(cls) -> str:
        """Get folder name for the current provider."""
        return cls.get_provider_config()['folder_name']
    
    @classmethod
    def requires_app_password(cls) -> bool:
        """Check if the current provider requires an app password."""
        return cls.get_provider_config()['requires_app_password']
    
    @classmethod
    def get_provider_display_name(cls) -> str:
        """Get display name for the current provider."""
        provider_names = {
            'gmail': 'Gmail',
            'outlook': 'Outlook/Office 365',
            'yahoo': 'Yahoo Mail',
            'tuta': 'Tutanota',
            'protonmail': 'ProtonMail',
            'icloud': 'iCloud Mail',
            'fastmail': 'Fastmail',
            'custom': 'Custom IMAP'
        }
        return provider_names.get(cls.EMAIL_PROVIDER, cls.EMAIL_PROVIDER.title())
    
    @classmethod
    def get_data_dir(cls) -> Path:
        """Get or create data directory."""
        data_dir = cls.BASE_DIR / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported email providers."""
        return list(cls.PROVIDER_CONFIGS.keys())
