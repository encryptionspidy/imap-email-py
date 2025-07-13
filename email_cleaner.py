"""Email content cleaning and normalization utilities."""

import re
import html
from typing import Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email
from bs4 import BeautifulSoup
import html2text
from email_reply_parser import EmailReplyParser
from loguru import logger


class EmailCleaner:
    """Comprehensive email content cleaning and normalization."""
    
    def __init__(self):
        self.html_parser = html2text.HTML2Text()
        self.html_parser.ignore_links = True
        self.html_parser.ignore_images = True
        self.html_parser.ignore_emphasis = True
        self.html_parser.body_width = 0  # Don't wrap lines
        
    def clean_email_content(self, raw_message: str) -> Tuple[str, str]:
        """
        Clean and normalize email content.
        
        Args:
            raw_message: Raw email message string
            
        Returns:
            Tuple of (cleaned_subject, cleaned_body)
        """
        try:
            # Parse email message
            msg = email.message_from_string(raw_message)
            
            # Extract subject
            subject = self._clean_subject(msg.get('Subject', ''))
            
            # Extract and clean body
            body = self._extract_and_clean_body(msg)
            
            return subject, body
            
        except Exception as e:
            logger.error(f"Error cleaning email content: {e}")
            return "", ""
    
    def _clean_subject(self, subject: str) -> str:
        """Clean and normalize email subject line."""
        if not subject:
            return ""
        
        # Decode HTML entities
        subject = html.unescape(subject)
        
        # Remove common prefixes (Re:, Fwd:, etc.)
        subject = re.sub(r'^(Re|RE|Fwd|FWD|Fw|FW):\s*', '', subject, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        subject = re.sub(r'\s+', ' ', subject).strip()
        
        return subject
    
    def _extract_and_clean_body(self, msg) -> str:
        """Extract and clean email body content."""
        # Try to get the best text representation
        plain_text = self._extract_plain_text(msg)
        html_text = self._extract_html_text(msg)
        
        # Prefer plain text if available and substantial
        if plain_text and len(plain_text.strip()) > 50:
            body = plain_text
        elif html_text:
            body = html_text
        else:
            body = plain_text or ""
        
        return self._clean_body_text(body)
    
    def _extract_plain_text(self, msg) -> str:
        """Extract plain text from email message."""
        plain_parts = []
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        content = part.get_payload(decode=True).decode(charset, errors='ignore')
                        plain_parts.append(content)
                    except (UnicodeDecodeError, AttributeError):
                        continue
        else:
            if msg.get_content_type() == 'text/plain':
                charset = msg.get_content_charset() or 'utf-8'
                try:
                    content = msg.get_payload(decode=True).decode(charset, errors='ignore')
                    plain_parts.append(content)
                except (UnicodeDecodeError, AttributeError):
                    pass
        
        return '\n'.join(plain_parts)
    
    def _extract_html_text(self, msg) -> str:
        """Extract and convert HTML to plain text."""
        html_parts = []
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        html_content = part.get_payload(decode=True).decode(charset, errors='ignore')
                        # Convert HTML to plain text
                        text_content = self._html_to_text(html_content)
                        html_parts.append(text_content)
                    except (UnicodeDecodeError, AttributeError):
                        continue
        else:
            if msg.get_content_type() == 'text/html':
                charset = msg.get_content_charset() or 'utf-8'
                try:
                    html_content = msg.get_payload(decode=True).decode(charset, errors='ignore')
                    text_content = self._html_to_text(html_content)
                    html_parts.append(text_content)
                except (UnicodeDecodeError, AttributeError):
                    pass
        
        return '\n'.join(html_parts)
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to clean plain text."""
        # First pass: BeautifulSoup for better HTML parsing
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and then use html2text for better formatting
        text = self.html_parser.handle(str(soup))
        
        return text
    
    def _clean_body_text(self, text: str) -> str:
        """Clean and normalize body text."""
        if not text:
            return ""
        
        # Remove quoted replies and signatures
        text = EmailReplyParser.parse_reply(text)
        
        # Normalize whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
        text = re.sub(r'[ \t]+', ' ', text)     # Normalize spaces and tabs
        
        # Remove common email artifacts
        text = re.sub(r'--\s*\n.*', '', text, flags=re.DOTALL)  # Remove signatures
        text = re.sub(r'On .* wrote:', '', text)  # Remove "On ... wrote:" lines
        text = re.sub(r'From:.*?\n', '', text, flags=re.MULTILINE)  # Remove "From:" lines
        text = re.sub(r'Sent:.*?\n', '', text, flags=re.MULTILINE)  # Remove "Sent:" lines
        text = re.sub(r'To:.*?\n', '', text, flags=re.MULTILINE)    # Remove "To:" lines
        text = re.sub(r'Subject:.*?\n', '', text, flags=re.MULTILINE)  # Remove "Subject:" lines
        
        # Remove URLs (optional - might want to keep for context)
        text = re.sub(r'https?://[^\s]+', '[URL]', text)
        
        # Remove email addresses in text
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL]', text)
        
        # Clean up extra whitespace
        text = text.strip()
        
        return text
    
    def extract_metadata(self, raw_message: str) -> dict:
        """Extract metadata from email message."""
        try:
            msg = email.message_from_string(raw_message)
            
            metadata = {
                'sender': msg.get('From', ''),
                'to': msg.get('To', ''),
                'cc': msg.get('Cc', ''),
                'bcc': msg.get('Bcc', ''),
                'date': msg.get('Date', ''),
                'message_id': msg.get('Message-ID', ''),
                'in_reply_to': msg.get('In-Reply-To', ''),
                'references': msg.get('References', ''),
                'content_type': msg.get_content_type(),
                'size': len(raw_message)
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}


def clean_email_for_search(subject: str, body: str) -> str:
    """
    Prepare email content for semantic search.
    
    Args:
        subject: Email subject line
        body: Email body text
        
    Returns:
        Combined and cleaned text for indexing
    """
    # Combine subject and body with appropriate weighting
    search_text = f"{subject}\n\n{body}"
    
    # Additional cleaning for search
    search_text = re.sub(r'\[URL\]', '', search_text)
    search_text = re.sub(r'\[EMAIL\]', '', search_text)
    search_text = re.sub(r'\n{2,}', '\n', search_text)
    search_text = search_text.strip()
    
    return search_text


def validate_email_content(subject: str, body: str) -> bool:
    """
    Validate that email content is substantial enough for indexing.
    
    Args:
        subject: Email subject line
        body: Email body text
        
    Returns:
        True if content is valid for indexing
    """
    # Check minimum content requirements
    if not subject and not body:
        return False
    
    # Check for minimum body length
    if len(body.strip()) < 20:
        return False
    
    # Check for spam-like patterns
    spam_indicators = [
        r'URGENT.*REPLY',
        r'CLICK HERE NOW',
        r'MAKE MONEY FAST',
        r'FREE MONEY',
        r'ACT NOW'
    ]
    
    combined_text = f"{subject} {body}".upper()
    for pattern in spam_indicators:
        if re.search(pattern, combined_text):
            logger.warning(f"Potential spam detected: {pattern}")
            return False
    
    return True
