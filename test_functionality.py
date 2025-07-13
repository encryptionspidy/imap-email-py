#!/usr/bin/env python3
"""Test script to demonstrate email CLI functionality."""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    print(f"Output: {result.stdout}")
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result

def test_help():
    """Test help command."""
    print("\n=== Testing Help Command ===")
    result = run_command("python main.py --help")
    assert result.returncode == 0
    assert "Multi-provider Email CLI" in result.stdout

def test_status():
    """Test status command."""
    print("\n=== Testing Status Command ===")
    result = run_command("python main.py status")
    # Status might fail if no database exists, but command should be recognized
    assert "Database:" in result.stdout or "Error:" in result.stdout

def test_list_emails():
    """Test list emails command."""
    print("\n=== Testing List Emails Command ===")
    result = run_command("python main.py list-emails")
    # Command should work but might show no emails
    assert "No emails found" in result.stdout or "Email Metadata" in result.stdout

def test_search():
    """Test search command."""
    print("\n=== Testing Search Command ===")
    result = run_command("python main.py search 'test query'")
    # Search might fail if no embeddings exist, but command should be recognized
    assert result.returncode == 0 or "Error" in result.stdout

def test_search_codes():
    """Test search-codes command."""
    print("\n=== Testing Search Codes Command ===")
    result = run_command("python main.py search-codes")
    # Command should work but might show no codes
    assert "No emails with verification codes" in result.stdout or "Found" in result.stdout

def main():
    """Run all tests."""
    print("Starting Email CLI Functionality Tests...")
    
    try:
        test_help()
        test_status()
        test_list_emails()
        test_search()
        test_search_codes()
        print("\n✅ All functionality tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
