"""Advanced semantic search functionality with filtering and performance optimization."""
import re
import time
import psutil
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from embedding import EmbeddingManager
from metadata_store import MetadataStore
from rich import print
from rich.table import Table
from rich.console import Console
from rich.progress import Progress, TimeElapsedColumn, SpinnerColumn
from loguru import logger
import sqlite3

@dataclass
class SearchStats:
    """Performance statistics for search operations."""
    query: str
    search_time: float
    faiss_time: float
    filter_time: float
    memory_usage: float
    results_count: int
    total_emails: int

class SearchManager:
    """Handles advanced semantic search operations with filtering and performance optimization."""
    
    def __init__(self, use_core=False):
        # Always use individual instances for now to ensure proper mapping loading
        self.embedding_manager = EmbeddingManager()
        self.metadata_store = MetadataStore()
        self.model = self.embedding_manager.model
        self.index = self.embedding_manager.index
        self.device = self.embedding_manager.device
            
        self.console = Console()
        self.search_stats = []
    
    def search_emails_enhanced(self, query: str, date_after: Optional[str] = None, date_before: Optional[str] = None,
                               sender: Optional[str] = None, regex: Optional[str] = None, limit: int = 10,
                               show_full_body: bool = False) -> List[Dict]:
        """Enhanced search with additional filters before semantic search."""
        start_time = time.time()
        print(f"[blue]Processing query: [italic]'{query}'[/italic]")
        
        # Embed the search query with GPU acceleration
        import torch
        with torch.no_grad():
            query_embedding = self.embedding_manager.model.encode(
                [query], 
                device=self.embedding_manager.device, 
                normalize_embeddings=True
            )
        
        # Search FAISS index
        distances, indices = self.embedding_manager.index.search(query_embedding.astype('float32'), limit)
        
        # Convert results to list of UID mappings
        uids = []
        # Handle both numpy arrays (real usage) and lists (test mocking)
        if hasattr(indices, 'size'):  # numpy array
            has_results = indices.size > 0 and indices.shape[1] > 0
        else:  # list (from mocks)
            has_results = len(indices) > 0 and len(indices[0]) > 0
            
        if has_results:
            for i, idx in enumerate(indices[0]):
                if idx == -1:
                    continue
                uid = self.embedding_manager.faiss_id_to_uid.get(str(idx))
                if uid:  # Only add if UID exists
                    uids.append(uid)
        
        if not uids:
            print("[yellow]No similar emails found")
            return []
        
        # Fetch metadata for top FAISS hits and add similarity scores
        results = self._fetch_metadata_for_uids(uids, distances[0])
        
        # Apply date filters if provided
        if date_after:
            after_date = datetime.strptime(date_after, "%Y-%m-%d")
            results = [email for email in results if self._parse_date(email['date']) >= after_date]
            print(f"[blue]Filtered by date after {date_after}, remaining {len(results)} emails")
        
        if date_before:
            before_date = datetime.strptime(date_before, "%Y-%m-%d")
            results = [email for email in results if self._parse_date(email['date']) <= before_date]
            print(f"[blue]Filtered by date before {date_before}, remaining {len(results)} emails")

        # Apply sender filter if provided
        if sender:
            results = [email for email in results if sender.lower() in email['sender'].lower()]
            print(f"[blue]Filtered by sender '{sender}', remaining {len(results)} emails")

        # Apply regex filter if provided
        if regex:
            pattern = re.compile(regex)
            results = [email for email in results if pattern.search(email['body_preview'])]
            print(f"[blue]Filtered by regex '{regex}', remaining {len(results)} emails")
        
        # Sort by similarity score
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Return top results
        top_results = results[:limit]
        
        # Performance logging
        search_time = time.time() - start_time
        print(f"[green]Search completed in {search_time:.2f} seconds, found {len(top_results)} results")
        
        return top_results

    def display_enhanced_results(self, results: List[Dict], full_body: bool = False) -> None:
        """Display search results with optional full email body display."""
        if not results:
            return
        
        print("\n=== Email Search Results ===")
        for i, result in enumerate(results, 1):
            print(f"{i}. UID: {result['uid']}")
            print(f"   Subject: {result['subject']}")
            print(f"   Sender: {result['sender']}")
            print(f"   Date: {str(result['date'])[:10]}")
            print(f"   Similarity: {result['similarity_score']:.3f}")
            
            if full_body:
                print(f"   Full Body:\n{result['full_body']}")
            else:
                print(f"   Preview: {result['body_preview']}")
            print("   " + "=" * 80)
    
    def search_emails(self, query: str, date_after: Optional[str] = None, regex: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Original search method for backward compatibility."""
        results = self.search_emails_enhanced(query, date_after, None, None, regex, limit, False)
        if results:
            self._display_search_results(results)
        return results
    
    def _display_search_results(self, results: List[Dict]) -> None:
        """Display search results with full email body."""
        if not results:
            return
        
        print("\n=== Email Search Results ===")
        for i, result in enumerate(results, 1):
            print(f"{i}. UID: {result['uid']}")
            print(f"   Subject: {result['subject']}")
            print(f"   Sender: {result['sender']}")
            print(f"   Date: {str(result['date'])[:10]}")
            print(f"   Similarity: {result['similarity_score']:.3f}")
            print(f"   Body:\n{result['full_body']}")
            print("   " + "=" * 80)
    
    def _fetch_metadata_for_uids(self, uids: List[str], distances=None) -> List[Dict]:
        """Retrieve metadata from SQLite for a list of UIDs with similarity scores."""
        cursor = self.metadata_store.connection.cursor()
        query = 'SELECT uid, subject, sender, date, body FROM emails WHERE uid IN ({})'.format(
            ','.join(['?'] * len(uids))
        )
        cursor.execute(query, tuple(uids))
        emails = cursor.fetchall()

        # Create mapping from UID to email data
        uid_to_email = {email[0]: email for email in emails}
        
        results = []
        for i, uid in enumerate(uids):
            if uid in uid_to_email:
                email = uid_to_email[uid]
                uid, subject, sender, date, body = email
                
                # Convert distance to similarity score (1 - distance for cosine)
                if distances is not None and i < len(distances):
                    similarity_score = 1.0 - float(distances[i])
                else:
                    similarity_score = 0.0
                
                results.append({
                    'uid': uid,
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'body_preview': body[:200] + '...' if len(body) > 200 else body,
                    'full_body': body,
                    'similarity_score': similarity_score
                })
        
        return results
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        if isinstance(date_str, datetime):
            return date_str.replace(tzinfo=None) if date_str.tzinfo else date_str
        try:
            # Try parsing various date formats
            parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return parsed.replace(tzinfo=None)  # Remove timezone info for comparison
        except (ValueError, TypeError):
            try:
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                try:
                    return datetime.strptime(date_str[:10], "%Y-%m-%d")
                except (ValueError, TypeError):
                    return datetime.min
    
    def search_by_verification_code(self, pattern: str = r'\d{6}') -> List[Dict]:
        """Search emails containing verification codes."""
        print(f"[blue]Searching for verification codes with pattern: {pattern}")
        
        # Get all emails from database
        cursor = self.metadata_store.connection.cursor()
        cursor.execute('SELECT uid, subject, sender, date, body FROM emails ORDER BY date DESC')
        emails = cursor.fetchall()
        
        matching_emails = []
        for email in emails:
            uid, subject, sender, date, body = email
            if re.search(pattern, body):
                matching_emails.append({
                    'uid': uid,
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'body_preview': body[:200] + '...' if len(body) > 200 else body,
                    'full_body': body,
                    'similarity_score': 1.0  # Default similarity score for verification code search
                })
        
        self._display_search_results(matching_emails)
        return matching_emails
    
    def keyword_fallback_search(self, query: str, date_after: Optional[str] = None, regex: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Fallback to keyword search when semantic search fails."""
        logger.info(f"Performing keyword fallback search for: {query}")
        print(f"[yellow]Falling back to keyword search for: {query}")
        
        # Split query into keywords
        keywords = query.lower().split()
        
        # Build SQL query with WHERE conditions
        where_conditions = []
        params = []
        
        # Add keyword conditions
        for keyword in keywords:
            where_conditions.append("(LOWER(subject) LIKE ? OR LOWER(body) LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        # Add date filter
        if date_after:
            where_conditions.append("date >= ?")
            params.append(date_after)
        
        # Combine conditions
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Execute query
        cursor = self.metadata_store.connection.cursor()
        query_sql = f"SELECT uid, subject, sender, date, body FROM emails WHERE {where_clause} ORDER BY date DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query_sql, params)
        emails = cursor.fetchall()
        
        # Format results
        results = []
        for email in emails:
            uid, subject, sender, date, body = email
            
            # Apply regex filter if provided
            if regex and not re.search(regex, body):
                continue
            
            # Calculate simple relevance score based on keyword matches
            relevance_score = self._calculate_keyword_relevance(query, subject, body)
            
            results.append({
                'uid': uid,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body_preview': body[:200] + '...' if len(body) > 200 else body,
                'full_body': body,
                'similarity_score': relevance_score
            })
        
        # Sort by relevance score
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        if results:
            print(f"[green]Found {len(results)} emails using keyword search")
            self._display_search_results(results)
        
        return results
    
    def _calculate_keyword_relevance(self, query: str, subject: str, body: str) -> float:
        """Calculate relevance score for keyword search."""
        keywords = query.lower().split()
        subject_lower = subject.lower()
        body_lower = body.lower()
        
        score = 0.0
        
        for keyword in keywords:
            # Higher weight for subject matches
            if keyword in subject_lower:
                score += 2.0
            # Lower weight for body matches
            if keyword in body_lower:
                score += 1.0
        
        # Normalize by query length
        return score / len(keywords) if keywords else 0.0
