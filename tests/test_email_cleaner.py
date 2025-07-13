"""Test for EmailCleaner, ensuring HTML parsing and cleaning fidelity."""
import pytest
from email_cleaner import EmailCleaner


@pytest.fixture
def email_cleaner():
    return EmailCleaner()


def test_clean_email_content_plain_text(email_cleaner):
    raw_email = """Subject: Test Email\n\nThis is a simple plain text email."""
    subject, body = email_cleaner.clean_email_content(raw_email)
    assert subject == "Test Email"
    assert body == "This is a simple plain text email."


def test_clean_email_content_html(email_cleaner):
    raw_email = """Subject: Test Email\nContent-Type: text/html; charset=utf-8\n\n<html><head></head><body><h1>Title</h1><p>This is a test email.</p></body></html>"""
    subject, body = email_cleaner.clean_email_content(raw_email)
    assert subject == "Test Email"
    assert "Title" in body
    assert "This is a test email." in body


@pytest.mark.parametrize("raw_email, expected_subject, expected_body", [
    ("Subject: HTML with Links\nContent-Type: text/html; charset=utf-8\n\n<p>Check <a href='http://example.com'>this</a> out!</p>",
     "HTML with Links", "Check this out!"),
    ("Subject: Re: Forwarded\nContent-Type: text/plain; charset=utf-8\n\nRe: Fwd: Test", "Forwarded", "Re: Fwd: Test"),
])
def test_clean_email_varied_cases(email_cleaner, raw_email, expected_subject, expected_body):
    subject, body = email_cleaner.clean_email_content(raw_email)
    assert subject == expected_subject
    assert body.strip() == expected_body


def test_email_metadata_extraction(email_cleaner):
    raw_email = """Subject: Test Email\nFrom: sender@example.com\nTo: recipient@example.com\nDate: Sat, 13 Jul 2025 14:32:00 +0530\nMessage-ID: <970f7c608f8e@example.com>\n\nThis is a test email."""
    metadata = email_cleaner.extract_metadata(raw_email)
    assert metadata['sender'] == "sender@example.com"
    assert metadata['to'] == "recipient@example.com"
    assert metadata['date'] == "Sat, 13 Jul 2025 14:32:00 +0530"
    assert metadata['message_id'] == "<970f7c608f8e@example.com>"
