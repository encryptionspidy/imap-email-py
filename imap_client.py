"""Multi-provider IMAP client for fetching emails and handling UIDVALIDITY."""
import imaplib
from email import message_from_bytes
from email.utils import parsedate_to_datetime
from datetime import datetime
import re
from typing import List, Dict, Optional
from config import Config
from utils import extract_email_metadata, clean_email_body
from rich import print
from loguru import logger
from email_cleaner import EmailCleaner, clean_email_for_search, validate_email_content

class IMAPClient:
    """Multi-provider IMAP client with UIDVALIDITY handling."""
    
    def __init__(self):
        if not Config.validate_credentials():
            raise ValueError("Email credentials not found. Please check your .env file.")
        
        self.mail = None
        self.current_uidvalidity = None
        self.provider_config = Config.get_provider_config()
        self.email_cleaner = EmailCleaner()
        self._connect()
    
    def _connect(self) -> None:
        """Connect to the IMAP server."""
        try:
            # Use SSL or non-SSL connection based on provider config
            if self.provider_config['use_ssl']:
                self.mail = imaplib.IMAP4_SSL(self.provider_config['imap_host'], self.provider_config['imap_port'])
            else:
                self.mail = imaplib.IMAP4(self.provider_config['imap_host'], self.provider_config['imap_port'])
            
            self.mail.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)
            provider_name = Config.get_provider_display_name()
            print(f"[green]Successfully connected to {provider_name} IMAP ({self.provider_config['imap_host']})")
        except Exception as e:
            provider_name = Config.get_provider_display_name()
            print(f"[red]Failed to connect to {provider_name}: {e}")
            print(f"[blue]Host: {self.provider_config['imap_host']}:{self.provider_config['imap_port']}")
            print(f"[blue]SSL: {self.provider_config['use_ssl']}")
            if Config.requires_app_password():
                print(f"[yellow]Note: {provider_name} requires an app password, not your regular password")
            raise
    
    def fetch_emails(self) -> List[Dict]:
        """Fetch all emails from inbox."""
        try:
            folder_name = self.provider_config['folder_name']
            self.mail.select(folder_name)
            status, messages = self.mail.search(None, 'ALL')
            
            if status != 'OK':
                print(f"[red]Failed to search emails: {status}")
                return []
            
            email_uids = messages[0].split()
            fetched_emails = []
            
            print(f"[blue]Found {len(email_uids)} emails to process")
            
            # Process emails in batches
            batch_size = Config.MAX_EMAILS_PER_BATCH
            for i in range(0, len(email_uids), batch_size):
                batch = email_uids[i:i + batch_size]
                batch_emails = self._fetch_email_batch(batch)
                fetched_emails.extend(batch_emails)
                
                if i + batch_size < len(email_uids):
                    print(f"[blue]Processed {i + batch_size}/{len(email_uids)} emails")
            
            print(f"[green]Successfully fetched {len(fetched_emails)} emails")
            return fetched_emails
            
        except Exception as e:
            print(f"[red]Error fetching emails: {e}")
            return []
    
    def _fetch_email_batch(self, uids: List[bytes]) -> List[Dict]:
        """Fetch a batch of emails with improved cleaning."""
        emails = []
        
        for uid in uids:
            try:
                status, msg_data = self.mail.fetch(uid, '(RFC822)')
                
                if status == 'OK' and msg_data:
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            # Get raw email content
                            raw_email = response_part[1].decode('utf-8', errors='ignore')
                            
                            # Use EmailCleaner to clean and parse
                            subject, body = self.email_cleaner.clean_email_content(raw_email)
                            
                            # Extract additional metadata
                            metadata = self.email_cleaner.extract_metadata(raw_email)
                            
                            # Validate content before adding
                            if not validate_email_content(subject, body):
                                logger.warning(f"Skipping email {uid.decode('utf-8')} - insufficient content")
                                continue
                            
                            # Build email record
                            email_record = {
                                'uid': uid.decode('utf-8'),
                                'subject': subject,
                                'sender': metadata.get('sender', ''),
                                'body': body,
                                'date': metadata.get('date', ''),
                                'uidvalidity': self.current_uidvalidity,
                                'search_content': clean_email_for_search(subject, body)
                            }
                            
                            emails.append(email_record)
                            logger.debug(f"Processed email {uid.decode('utf-8')}: {subject[:50]}...")
                            break
                            
            except Exception as e:
                logger.error(f"Failed to fetch email {uid.decode('utf-8')}: {e}")
                print(f"[yellow]Warning: Failed to fetch email {uid.decode('utf-8')}: {e}")
                continue
        
        return emails
    
    def check_uid_validity(self) -> bool:
        """Check if UIDVALIDITY has changed."""
        try:
            folder_name = self.provider_config['folder_name']
            status, data = self.mail.status(folder_name, '(UIDVALIDITY)')
            
            if status != 'OK':
                print(f"[red]Failed to get UIDVALIDITY: {status}")
                return False
            
            # Parse UIDVALIDITY from response
            response = data[0].decode()
            match = re.search(r'UIDVALIDITY (\d+)', response)
            
            if not match:
                print(f"[red]Could not parse UIDVALIDITY from: {response}")
                return False
            
            self.current_uidvalidity = int(match.group(1))
            last_known_uidvalidity = self._load_last_uid_validity()
            
            if last_known_uidvalidity is None:
                # First run
                self._save_current_uid_validity(self.current_uidvalidity)
                return False
            
            if self.current_uidvalidity != last_known_uidvalidity:
                print(f"[yellow]UIDVALIDITY changed: {last_known_uidvalidity} -> {self.current_uidvalidity}")
                self._save_current_uid_validity(self.current_uidvalidity)
                return True
            
            return False
            
        except Exception as e:
            print(f"[red]Error checking UIDVALIDITY: {e}")
            return False
    
    def _load_last_uid_validity(self) -> Optional[int]:
        """Load last known UIDVALIDITY from file."""
        uidvalidity_file = Config.BASE_DIR / "uidvalidity.txt"
        
        if not uidvalidity_file.exists():
            return None
        
        try:
            with open(uidvalidity_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return None
    
    def _save_current_uid_validity(self, uid_validity: int) -> None:
        """Save current UIDVALIDITY to file."""
        uidvalidity_file = Config.BASE_DIR / "uidvalidity.txt"
        
        try:
            with open(uidvalidity_file, 'w') as f:
                f.write(str(uid_validity))
        except IOError as e:
            print(f"[red]Failed to save UIDVALIDITY: {e}")
    
    def close(self) -> None:
        """Close IMAP connection."""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
            except:
                pass
    
    def __del__(self):
        self.close()

