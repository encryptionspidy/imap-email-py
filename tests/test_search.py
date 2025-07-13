import unittest
from unittest.mock import patch, MagicMock
from search import SearchManager, SearchStats
from datetime import datetime

class TestSearchManager(unittest.TestCase):
    def setUp(self):
        self.patcher_embedding = patch('search.EmbeddingManager')
        self.patcher_metadata = patch('search.MetadataStore')
        self.patcher_console = patch('search.Console')
        
        self.MockEmbeddingManager = self.patcher_embedding.start()
        self.MockMetadataStore = self.patcher_metadata.start()
        self.MockConsole = self.patcher_console.start()
        
        # Mock instances
        self.mock_embedding_manager = self.MockEmbeddingManager.return_value
        self.mock_metadata_store = self.MockMetadataStore.return_value
        self.mock_console = self.MockConsole.return_value
        
        # Create SearchManager instance
        self.search_manager = SearchManager()

    def tearDown(self):
        self.patcher_embedding.stop()
        self.patcher_metadata.stop()
        self.patcher_console.stop()

    def test_search_emails_basic(self):
        """Test basic email search functionality."""
        # Mock search results
        mock_query_embedding = MagicMock()
        self.mock_embedding_manager.model.encode.return_value = mock_query_embedding
        
        # Mock FAISS search results
        distances = [[0.2, 0.4, 0.6]]
        indices = [[0, 1, 2]]
        self.mock_embedding_manager.index.search.return_value = (distances, indices)
        
        # Mock UID mapping
        self.mock_embedding_manager.faiss_id_to_uid = {'0': 'uid1', '1': 'uid2', '2': 'uid3'}
        
        # Mock database results
        mock_cursor = MagicMock()
        self.mock_metadata_store.connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ('uid1', 'Test Subject 1', 'sender1@example.com', '2025-07-13', 'Test body content 1'),
            ('uid2', 'Test Subject 2', 'sender2@example.com', '2025-07-12', 'Test body content 2'),
            ('uid3', 'Test Subject 3', 'sender3@example.com', '2025-07-11', 'Test body content 3')
        ]
        
        # Test search
        results = self.search_manager.search_emails("test query", limit=3)
        
        # Assertions
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['uid'], 'uid1')
        self.assertEqual(results[0]['subject'], 'Test Subject 1')
        self.assertAlmostEqual(results[0]['similarity_score'], 0.8, places=2)  # 1 - 0.2

    def test_search_emails_with_date_filter(self):
        """Test email search with date filtering."""
        # Mock search results
        mock_query_embedding = MagicMock()
        self.mock_embedding_manager.model.encode.return_value = mock_query_embedding
        
        # Mock FAISS search results
        distances = [[0.2, 0.4]]
        indices = [[0, 1]]
        self.mock_embedding_manager.index.search.return_value = (distances, indices)
        
        # Mock UID mapping
        self.mock_embedding_manager.faiss_id_to_uid = {'0': 'uid1', '1': 'uid2'}
        
        # Mock database results
        mock_cursor = MagicMock()
        self.mock_metadata_store.connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ('uid1', 'Test Subject 1', 'sender1@example.com', '2025-07-13', 'Test body content 1'),
            ('uid2', 'Test Subject 2', 'sender2@example.com', '2025-07-10', 'Test body content 2')
        ]
        
        # Test search with date filter
        results = self.search_manager.search_emails("test query", date_after="2025-07-12", limit=2)
        
        # Should filter out uid2 (2025-07-10) and keep uid1 (2025-07-13)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uid'], 'uid1')

    def test_search_emails_with_regex_filter(self):
        """Test email search with regex filtering."""
        # Mock search results
        mock_query_embedding = MagicMock()
        self.mock_embedding_manager.model.encode.return_value = mock_query_embedding
        
        # Mock FAISS search results
        distances = [[0.2, 0.4]]
        indices = [[0, 1]]
        self.mock_embedding_manager.index.search.return_value = (distances, indices)
        
        # Mock UID mapping
        self.mock_embedding_manager.faiss_id_to_uid = {'0': 'uid1', '1': 'uid2'}
        
        # Mock database results
        mock_cursor = MagicMock()
        self.mock_metadata_store.connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ('uid1', 'Test Subject 1', 'sender1@example.com', '2025-07-13', 'Test body content with code 123456'),
            ('uid2', 'Test Subject 2', 'sender2@example.com', '2025-07-12', 'Test body content without code')
        ]
        
        # Test search with regex filter
        results = self.search_manager.search_emails("test query", regex=r'\d{6}', limit=2)
        
        # Should filter out uid2 and keep uid1 (contains 6-digit code)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uid'], 'uid1')

    def test_search_by_verification_code(self):
        """Test verification code search functionality."""
        # Mock database results
        mock_cursor = MagicMock()
        self.mock_metadata_store.connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ('uid1', 'Verification Code', 'noreply@example.com', '2025-07-13', 'Your verification code is 123456'),
            ('uid2', 'Another Email', 'sender@example.com', '2025-07-12', 'No code here'),
            ('uid3', 'Login Code', 'security@example.com', '2025-07-11', 'Login code: 789012')
        ]
        
        # Test verification code search
        results = self.search_manager.search_by_verification_code(r'\d{6}')
        
        # Should return emails with 6-digit codes
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['uid'], 'uid1')
        self.assertEqual(results[1]['uid'], 'uid3')

    def test_parse_date_various_formats(self):
        """Test date parsing with various date formats."""
        # Test ISO format
        result = self.search_manager._parse_date('2025-07-13T15:30:00')
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 7)
        self.assertEqual(result.day, 13)
        
        # Test standard format
        result = self.search_manager._parse_date('2025-07-13 15:30:00')
        self.assertEqual(result.year, 2025)
        
        # Test invalid format
        result = self.search_manager._parse_date('invalid-date')
        self.assertEqual(result, datetime.min)

    def test_search_emails_no_results(self):
        """Test search when no emails match."""
        # Mock search results
        mock_query_embedding = MagicMock()
        self.mock_embedding_manager.model.encode.return_value = mock_query_embedding
        
        # Mock FAISS search results (no results)
        distances = [[]]
        indices = [[]]
        self.mock_embedding_manager.index.search.return_value = (distances, indices)
        
        # Test search
        results = self.search_manager.search_emails("nonexistent query")
        
        # Should return empty list
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()
