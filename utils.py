"""Utility functions for date parsing, regex filters, and email processing."""
import re
from datetime import datetime
from typing import Optional, List, Dict
from email.utils import parsedate_to_datetime
from dateutil import parser

def parse_email_date(date_string: str) -> Optional[datetime]:
    """Parse email date string to datetime object."""
    if not date_string:
        return None
    
    try:
        # First try email.utils parser
        return parsedate_to_datetime(date_string)
    except (ValueError, TypeError):
        try:
            # Fallback to dateutil parser
            return parser.parse(date_string)
        except (ValueError, TypeError):
            return None


def clean_email_body(body: str) -> str:
    """Clean email body text for better embedding."""
    if not body:
        return ""
    
    # Remove HTML tags
    body = re.sub(r'<[^>]+>', '', body)
    
    # Remove excessive whitespace
    body = re.sub(r'\s+', ' ', body)
    
    # Remove common email signatures
    body = re.sub(r'-+\s*Original Message\s*-+.*', '', body, flags=re.DOTALL)
    body = re.sub(r'On .* wrote:.*', '', body, flags=re.DOTALL)
    
    # Remove URLs
    body = re.sub(r'https?://[^\s]+', '[URL]', body)
    
    return body.strip()

def extract_email_metadata(raw_email: bytes) -> Dict:
    """Extract metadata from raw email bytes."""
    from email import message_from_bytes
    
    msg = message_from_bytes(raw_email)
    
    # Extract basic metadata
    metadata = {
        'subject': msg.get('Subject', ''),
        'sender': msg.get('From', ''),
        'recipient': msg.get('To', ''),
        'date': parse_email_date(msg.get('Date', '')),
        'message_id': msg.get('Message-ID', ''),
        'thread_id': msg.get('Thread-Index', ''),
    }
    
    # Extract body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                break
    else:
        body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
    
    metadata['body'] = clean_email_body(body)
    
    return metadata

def format_email_for_display(email_data: Dict) -> str:
    """Format email data for CLI display."""
    template = """
Subject: {subject}
From: {sender}
Date: {date}
UID: {uid}

{body}
    """
    
    return template.format(
        subject=email_data.get('subject', 'No Subject'),
        sender=email_data.get('sender', 'Unknown Sender'),
        date=email_data.get('date', 'Unknown Date'),
        uid=email_data.get('uid', 'Unknown UID'),
        body=email_data.get('body', 'No Body')[:1000] + '...' if len(email_data.get('body', '')) > 1000 else email_data.get('body', '')
    )

def validate_email_address(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
