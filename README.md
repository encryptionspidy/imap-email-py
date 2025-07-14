# Multi-Provider Email CLI

A highly efficient Python-based CLI application for managing and searching emails from multiple providers using IMAP with semantic search capabilities powered by FAISS and sentence transformers.

## Screenshots

### Search Loop in Action
![Search Loop Demo](eg%20images/250714_11h26m57s_screenshot.png)

### Semantic Search Results
![Semantic Search Results](eg%20images/250714_11h29m17s_screenshot.png)

### Email Fetching Process
![Email Fetching](eg%20images/250714_11h32m35s_screenshot.png)

## Features

- **Multi-Provider Support**: Connect to Gmail, Outlook, Yahoo, Tutanota, ProtonMail, iCloud, Fastmail, and custom IMAP servers
- **IMAP Email Fetching**: Securely connect to any IMAP server and fetch emails with batching
- **Semantic Search**: Search emails using natural language with sentence transformers
- **Verification Code Detection**: Automatically detect and flag emails with verification codes
- **UIDVALIDITY Handling**: Robust handling of IMAP UIDVALIDITY changes
- **GPU/CPU Fallback**: Automatic detection and usage of GPU if available
- **SQLite Storage**: Efficient local storage of email metadata
- **FAISS Indexing**: Fast similarity search with HNSW index
- **Configurable Providers**: Easy setup for different email providers via environment variables

## Setup Instructions

### Cloning the Repository
1. Clone the repository:
   ```bash
   git clone https://github.com/encryptionspidy/imap-email-py.git
   cd imap-email-py
   ```

### Installing Dependencies
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Setting Up Email Credentials
3. Set up email credentials based on your provider:
   - **Gmail**: Generate an app password from [Google Account App Passwords](https://myaccount.google.com/apppasswords)
   - **Outlook**: Use your Microsoft account password or app password
   - **Yahoo**: Generate an app password from Yahoo Account Security
   - **Tutanota**: Use your regular password
   - **ProtonMail**: Configure ProtonMail Bridge for IMAP access
   - **iCloud**: Generate an app password from Apple ID settings
   - **Fastmail**: Use your regular password or an app password
   - **Custom**: Use your IMAP server credentials

### Configuring Environment Variables
4. Configure environment variables:
   ```bash
   cp .env.template .env
   # Edit .env with your email credentials and provider settings
   ```

## Usage

### Execution

#### 1. Fetch Emails (Essential First Step)
```bash
# Fetch emails from your configured provider and update local database
python main.py fetch-emails
```
**What it does:**
- Connects to your email provider via IMAP
- Downloads email metadata and content
- Generates semantic embeddings for search
- Updates the local SQLite database and FAISS index

#### 2. Interactive Search Loop (Recommended)
```bash
# Enter interactive search mode
python main.py search-loop

# Or filter by date
python main.py search-loop --after-date 2024-01-01
```
**What it does:**
- Opens an interactive search interface
- Allows continuous searching without restarting
- Supports natural language queries
- Shows search results with similarity scores
- Type 'quit' or 'exit' to leave the loop

#### 3. Check Status
```bash
# Check database and index status
python main.py status
```

### Listing and Viewing Emails

```bash
# List all emails (default: 50 emails)
python main.py list-emails

# List more emails
python main.py list-emails --limit 100

# View specific email
python main.py get-email <uid>
```

### Other Search Options

```bash
# One-time semantic search
python main.py search "meeting tomorrow"

# Limit search results
python main.py search "verification code" --limit 5

# Advanced search with filters
python main.py search "project update" --limit 10
```

### Verification Code Search

```bash
# Search for 6-digit verification codes
python main.py search-codes

# Search for 4-digit codes
python main.py search-codes --pattern "\\d{4}"

# Search for alphanumeric codes
python main.py search-codes --pattern "[A-Z0-9]{8}"
```

## Configuration

The app uses the following configuration (in `config.py`):

- **Database**: SQLite database for email metadata
- **FAISS Index**: HNSW index for fast similarity search
- **Embedding Model**: `multi-qa-mpnet-base-cos-v1` from sentence-transformers
- **Batch Size**: 64 emails per embedding batch
- **GPU Support**: Automatic detection with CPU fallback

## Project Structure

```
semantic_email_cli/
├── main.py              # CLI entry point
├── config.py            # Configuration management
├── imap_client.py       # Gmail IMAP interface
├── metadata_store.py    # SQLite database handler
├── embedding.py         # Sentence transformers + FAISS
├── search.py            # Semantic search functionality
├── utils.py             # Utility functions
├── requirements.txt     # Dependencies
├── .env.template        # Environment template
└── README.md           # This file
```

## UIDVALIDITY Handling

The app automatically handles Gmail UIDVALIDITY changes:

1. **Check UIDVALIDITY**: On each run, compares current vs. stored UIDVALIDITY
2. **Detect Changes**: If UIDVALIDITY changes, all local data is cleared
3. **Re-fetch**: Automatically re-fetches all emails and rebuilds index
4. **Incremental Updates**: For unchanged UIDVALIDITY, only processes new emails

## Performance Optimization

- **Batched Processing**: Emails fetched and embedded in configurable batches
- **GPU Acceleration**: Automatic GPU detection for embedding generation
- **FAISS HNSW**: Efficient similarity search index
- **Persistent Storage**: Index and mappings saved to disk
- **Memory Management**: Streaming processing for large email volumes

## Error Handling

The application includes comprehensive error handling:

- **Connection Errors**: Graceful handling of IMAP connection issues
- **Authentication**: Clear error messages for credential problems
- **Data Corruption**: Automatic recovery from corrupted indexes
- **Memory Issues**: Batch processing to prevent memory exhaustion

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Ensure 2FA is enabled on Gmail
   - Use App Password, not regular password
   - Check .env file configuration

2. **No Emails Found**
   - Run `fetch-emails` first
   - Check Gmail connection
   - Verify IMAP is enabled in Gmail settings

3. **Search Returns No Results**
   - Ensure embeddings are generated (`fetch-emails`)
   - Try different search terms
   - Check FAISS index status with `status`

4. **Memory Issues**
   - Reduce `EMBEDDING_BATCH_SIZE` in config
   - Ensure sufficient RAM for embeddings
   - Consider CPU-only mode if GPU memory is limited

## Requirements

- Python 3.8+
- Gmail account with App Password
- 2GB+ RAM recommended
- Optional: CUDA-compatible GPU for faster embeddings

## Security

- Credentials stored in local `.env` file
- No data sent to external services
- All processing done locally
- SQLite database and FAISS index stored locally


