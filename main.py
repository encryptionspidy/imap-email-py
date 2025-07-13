"""Main CLI application for multi-provider email management."""
from typing import List, Optional
import typer
from rich import print
from rich.console import Console
from rich.table import Table
from loguru import logger
import sys
import os
from pathlib import Path
from datetime import datetime
from imap_client import IMAPClient
from metadata_store import MetadataStore
from embedding import EmbeddingManager
from search import SearchManager
from utils import format_email_for_display
from config import Config
from email_cleaner import EmailCleaner

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}",
    level="INFO"
)
logger.add(
    "logs/email_cli.log",
    rotation="10 MB",
    retention="10 days",
    level="DEBUG"
)

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Global offline mode and verbosity settings
offline_mode = False
verbosity_level = "INFO"

app = typer.Typer(help="Multi-provider Email CLI for managing and searching emails with semantic search")
console = Console()

@app.command()
def fetch_emails():
    """Fetch emails from Gmail and update local database and embeddings."""
    print("[blue]Fetching emails and updating database...")

    try:
        # Validate credentials first
        if not Config.validate_credentials():
            print("[red]Error: Email credentials not found. Please create a .env file with EMAIL_USER and EMAIL_PASSWORD.")
            print("[blue]See .env.template for an example.")
            return

        imap_client = IMAPClient()
        metadata_store = MetadataStore()

        # Check UIDVALIDITY
        uid_validity_changed = imap_client.check_uid_validity()
        if uid_validity_changed:
            print("[red]UIDVALIDITY has changed. Clearing database and embeddings...")
            metadata_store.clear()
            embedding_manager = EmbeddingManager()
            embedding_manager.clear_index()

        # Fetch emails
        fetched_emails = imap_client.fetch_emails()

        if fetched_emails:
            metadata_store.update_emails(fetched_emails)

            # Generate embeddings
            embedding_manager = EmbeddingManager()
            embedding_manager.embed_emails(fetched_emails)
            
            # Update last fetch timestamp
            from datetime import datetime
            metadata_store.set_last_fetch_time(datetime.now().isoformat())

            print(f"[green]Successfully processed {len(fetched_emails)} emails")
        else:
            print("[yellow]No emails to process")

    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(1)

@app.command()
def list_emails(limit: Optional[int] = typer.Option(50, help="Maximum number of emails to display")):
    """List all email metadata."""
    print("[blue]Listing email metadata...")
    
    try:
        metadata_store = MetadataStore()
        emails = metadata_store.list_emails()
        
        if not emails:
            print("[yellow]No emails found. Run 'fetch-emails' first.")
            return
        
        # Create table for better display
        table = Table(title="Email Metadata")
        table.add_column("UID", style="cyan")
        table.add_column("Subject", style="magenta")
        table.add_column("Sender", style="green")
        table.add_column("Date", style="yellow")
        
        for email in emails[:limit]:
            uid, subject, sender, date = email
            table.add_row(
                uid,
                subject[:50] + '...' if len(subject) > 50 else subject,
                sender[:30] + '...' if len(sender) > 30 else sender,
                str(date)[:10] if date else 'N/A'
            )
        
        console.print(table)
        
        if len(emails) > limit:
            print(f"[blue]Showing {limit} of {len(emails)} emails. Use --limit to see more.")
            
    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(1)

@app.command()
def get_email(uid: str):
    """Get full email body for a specific UID."""
    print(f"[blue]Fetching full body for email UID: {uid}")
    
    try:
        metadata_store = MetadataStore()
        email = metadata_store.get_email(uid)
        
        if not email:
            print(f"[red]Email with UID {uid} not found")
            return
        
        # Format email for display
        email_data = {
            'uid': email[0],
            'subject': email[2],
            'sender': email[3],
            'date': email[4],
            'body': email[5]
        }
        
        formatted_email = format_email_for_display(email_data)
        print(formatted_email)
        
    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(1)

@app.command()
def search(query: str,
           date_after: Optional[str] = typer.Option(None, "--date-after", help="Filter emails after specific date (YYYY-MM-DD)"),
           date_before: Optional[str] = typer.Option(None, "--date-before", help="Filter emails before specific date (YYYY-MM-DD)"),
           sender: Optional[str] = typer.Option(None, "--sender", help="Filter emails by sender"),
           regex: Optional[str] = typer.Option(None, "--regex", help="Filter emails matching regex pattern"),
           limit: Optional[int] = typer.Option(10, help="Maximum number of results"),
           offline: bool = typer.Option(False, "--offline", help="Search only local database (no IMAP calls)"),
           full: bool = typer.Option(False, "--full", help="Show full email body in results")):
    """Advanced search combining semantic similarity and filtering."""
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Starting search with query: {query}")
        logger.info(f"Filters - date_after: {date_after}, date_before: {date_before}, sender: {sender}, regex: {regex}")
        
        if offline:
            logger.info("Running in offline mode")
            print("[yellow]Running in offline mode (no IMAP calls)")
        
        search_manager = SearchManager()
        
        # Enhanced search with more filters
        results = search_manager.search_emails_enhanced(
            query=query,
            date_after=date_after,
            date_before=date_before,
            sender=sender,
            regex=regex,
            limit=limit,
            show_full_body=full
        )
        
        if not results:
            print("[yellow]No similar emails found")
            # Fallback to keyword search if no semantic results
            logger.info("No semantic results found, trying keyword fallback")
            results = search_manager.keyword_fallback_search(query, date_after, regex, limit)
        
        if results:
            search_time = time.time() - start_time
            print(f"[green]Found {len(results)} similar emails in {search_time:.2f} seconds")
            logger.info(f"Search completed successfully with {len(results)} results in {search_time:.2f}s")
            
            # Display results with improved formatting
            search_manager.display_enhanced_results(results, full_body=full)
        else:
            print("[yellow]No emails found matching your criteria")
            logger.info("No results found for query")
            
    except Exception as e:
        logger.error(f"Error during search: {e}")
        print(f"[red]Error during search: {e}")
        raise typer.Exit(1)

@app.command()
def search_loop(after_date: Optional[str] = typer.Option(None, "--after-date", help="Filter emails after specific date (YYYY-MM-DD)")):
    """Interactive search loop mode."""
    try:
        # Use SearchManager for consistent behavior
        search_manager = SearchManager(use_core=False)
        
        print('Entering search loop. Type "q" or "exit" to quit.')
        if after_date:
            print(f'Filtering emails after: {after_date}')
        
        while True:
            try:
                query = input('Enter search query (or q to quit): ').strip()
                if query.lower() in ['q', 'exit']:
                    break
                
                if not query:
                    print("Please enter a search query.")
                    continue
                
                # Use the search manager for consistent behavior
                results = search_manager.search_emails(query, date_after=after_date, limit=5)
                
                if not results:
                    print("No results found.")
                
            except KeyboardInterrupt:
                print("\nExiting search loop.")
                break
            except Exception as e:
                print(f"Error: {e}")
                continue
            
            print('-'*40)
    
    except Exception as e:
        print(f"[red]Error in search loop: {e}")
        raise typer.Exit(1)

@app.command()
def search_codes(pattern: Optional[str] = typer.Option(r'\d{6}', help="Regex pattern for verification codes")):
    """Search for emails containing verification codes."""
    try:
        search_manager = SearchManager()
        results = search_manager.search_by_verification_code(pattern)
        
        if not results:
            print("[yellow]No emails with verification codes found")
        else:
            print(f"[green]Found {len(results)} emails with verification codes")
            
    except Exception as e:
        print(f"[red]Error during verification code search: {e}")
        raise typer.Exit(1)

@app.command()
def configure():
    """Securely configure email credentials."""
    print("[blue]Configuring email credentials...")
    
    try:
        # Create .env file if it doesn't exist
        env_file = Path(".env")
        if not env_file.exists():
            env_file.touch()
        
        # Get email credentials
        email_user = typer.prompt("Email address")
        email_password = typer.prompt("App password (not your regular password)", hide_input=True)
        email_provider = typer.prompt("Email provider", default="gmail")
        
        # Write to .env file
        with open(env_file, "w") as f:
            f.write(f"EMAIL_USER={email_user}\n")
            f.write(f"EMAIL_PASSWORD={email_password}\n")
            f.write(f"EMAIL_PROVIDER={email_provider}\n")
            f.write(f"EMBEDDING_BATCH_SIZE=64\n")
            f.write(f"FAISS_INDEX_PATH=faiss_index.bin\n")
            f.write(f"DATABASE_PATH=emails.db\n")
        
        print("[green]Configuration saved successfully!")
        print("[blue]You can now run 'fetch-emails' to sync your emails.")
        
    except Exception as e:
        logger.error(f"Error configuring credentials: {e}")
        print(f"[red]Error: {e}")
        raise typer.Exit(1)

@app.command()
def status():
    """Show comprehensive database and index status."""
    try:
        metadata_store = MetadataStore()
        cursor = metadata_store.connection.cursor()
        
        # Get email count
        cursor.execute('SELECT COUNT(*) FROM emails')
        email_count = cursor.fetchone()[0]
        
        # Get date range
        cursor.execute('SELECT MIN(date), MAX(date) FROM emails')
        date_range = cursor.fetchone()
        
        # Get last fetch timestamp if available
        last_fetch = metadata_store.get_last_fetch_time()
        
        embedding_manager = EmbeddingManager()
        index_count = embedding_manager.index.ntotal if embedding_manager.index else 0
        
        # Create status table
        table = Table(title="Email CLI Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        
        table.add_row("Database", f"{email_count} emails", f"Range: {date_range[0]} to {date_range[1]}" if date_range[0] else "No emails")
        table.add_row("FAISS Index", f"{index_count} embeddings", f"Device: {embedding_manager.device}")
        table.add_row("Last Sync", last_fetch, "Run 'fetch-emails' to update")
        
        # Check if index needs updating
        if email_count != index_count:
            table.add_row("Index Status", "⚠️ Out of sync", "Run 'fetch-emails' to rebuild index")
        else:
            table.add_row("Index Status", "✅ Up to date", "All emails are indexed")
        
        console.print(table)
        
        # Show file sizes
        db_size = Path("emails.db").stat().st_size / (1024 * 1024) if Path("emails.db").exists() else 0
        faiss_size = Path("faiss_index.bin").stat().st_size / (1024 * 1024) if Path("faiss_index.bin").exists() else 0
        
        print(f"\n[blue]Storage Usage:")
        print(f"  Database: {db_size:.2f} MB")
        print(f"  FAISS Index: {faiss_size:.2f} MB")
        
        # Check if offline mode is possible
        if email_count > 0 and index_count > 0:
            print(f"\n[green]✅ Offline mode available - you can search without internet connection")
        else:
            print(f"\n[yellow]⚠️ Run 'fetch-emails' first to enable offline search")
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        print(f"[red]Error: {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
