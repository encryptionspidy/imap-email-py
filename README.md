# Multi-Provider Email CLI

A highly efficient Python-based CLI application for managing and searching emails from multiple providers using IMAP with semantic search capabilities powered by FAISS and sentence transformers.

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

### Running the Project Locally
5. Use the following commands to interact with the CLI:
   - Fetch emails (first run):
     ```bash
     python main.py fetch-emails
     ```
   - Check status:
     ```bash
     python main.py status
     ```

   - List all emails (default: 50 emails):
     ```bash
     python main.py list-emails
     ```

   - Semantic search:
     ```bash
     python main.py search "your query"
     ```
   - Search for verification codes:
     ```bash
     python main.py search-codes
     ```

## Usage

### Initial Setup and Email Fetching

```bash
# Fetch emails from Gmail (first run)
python main.py fetch-emails

# Check status
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

### Semantic Search

```bash
# Search for emails about meetings
python main.py search "meeting tomorrow"

# Search for emails about payments
python main.py search "payment invoice receipt"

# Limit search results
python main.py search "verification code" --limit 5
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

## CLI Commands

| Command | Description |
|---------|-------------|
| `fetch-emails` | Sync emails from Gmail to local database and FAISS index |
| `list-emails` | Show email metadata in a table format |
| `get-email <uid>` | Display full email body for specific UID |
| `search <query>` | Semantic search using natural language |
| `search-codes` | Find emails containing verification codes |
| `status` | Show database and index statistics |

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

## License

MIT License - See LICENSE file for details
