"""Tests for embedding functionality."""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import json
from pathlib import Path

from embedding import EmbeddingManager


class TestEmbeddingManager(unittest.TestCase):
    """Test cases for EmbeddingManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_emails = [
            {
                'uid': '1',
                'subject': 'Test Email 1',
                'sender': 'sender1@example.com',
                'body': 'This is the first test email',
                'date': '2025-07-13'
            },
            {
                'uid': '2',
                'subject': 'Test Email 2',
                'sender': 'sender2@example.com',
                'body': 'This is the second test email',
                'date': '2025-07-14'
            }
        ]
    
    @patch('embedding.torch.cuda.is_available')
    @patch('embedding.SentenceTransformer')
    @patch('embedding.faiss.read_index')
    @patch('embedding.Path.exists')
    def test_init_with_existing_index(self, mock_exists, mock_read_index, mock_sentence_transformer, mock_cuda):
        """Test EmbeddingManager initialization with existing index."""
        mock_cuda.return_value = False
        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_sentence_transformer.return_value = mock_model
        mock_index = MagicMock()
        mock_read_index.return_value = mock_index
        
        with patch('builtins.open', mock_open(read_data='{"uid_to_faiss_id": {"1": 0}, "faiss_id_to_uid": {"0": "1"}}')):
            manager = EmbeddingManager()
        
        self.assertEqual(manager.device, 'cpu')
        self.assertEqual(manager.model, mock_model)
        self.assertEqual(manager.index, mock_index)
        self.assertEqual(manager.uid_to_faiss_id, {'1': 0})
        self.assertEqual(manager.faiss_id_to_uid, {'0': '1'})
    
    @patch('embedding.torch.cuda.is_available')
    @patch('embedding.torch.cuda.get_device_name')
    @patch('embedding.SentenceTransformer')
    @patch('embedding.faiss.IndexHNSWFlat')
    @patch('embedding.Path.exists')
    def test_init_with_new_index(self, mock_exists, mock_index_class, mock_sentence_transformer, mock_device_name, mock_cuda):
        """Test EmbeddingManager initialization with new index."""
        mock_cuda.return_value = True
        mock_device_name.return_value = 'NVIDIA GTX 1650'
        mock_exists.return_value = False
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_sentence_transformer.return_value = mock_model
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index
        
        with patch('builtins.open', mock_open()):
            with patch('embedding.faiss.write_index'):
                manager = EmbeddingManager()
        
        self.assertEqual(manager.device, 'cuda')
        self.assertEqual(manager.model, mock_model)
        self.assertEqual(manager.index, mock_index)
    
    @patch('embedding.torch.cuda.is_available')
    @patch('embedding.SentenceTransformer')
    @patch('embedding.faiss.IndexHNSWFlat')
    @patch('embedding.Path.exists')
    def test_embed_emails_new_emails(self, mock_exists, mock_index_class, mock_sentence_transformer, mock_cuda):
        """Test embedding new emails."""
        mock_cuda.return_value = False
        mock_exists.return_value = False
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_sentence_transformer.return_value = mock_model
        mock_index = MagicMock()
        mock_index.ntotal = 0
        mock_index_class.return_value = mock_index
        
        with patch('builtins.open', mock_open()):
            with patch('embedding.faiss.write_index'):
                manager = EmbeddingManager()
                manager.embed_emails(self.test_emails)
        
        # Check that model.encode was called with email bodies
        mock_model.encode.assert_called_once()
        args, kwargs = mock_model.encode.call_args
        self.assertEqual(len(args[0]), 2)  # 2 email bodies
        
        # Check that index.add was called
        mock_index.add.assert_called_once()
        
        # Check that mappings were updated
        self.assertEqual(manager.uid_to_faiss_id['1'], 0)
        self.assertEqual(manager.uid_to_faiss_id['2'], 1)
        self.assertEqual(manager.faiss_id_to_uid['0'], '1')
        self.assertEqual(manager.faiss_id_to_uid['1'], '2')
    
    @patch('embedding.torch.cuda.is_available')
    @patch('embedding.SentenceTransformer')
    @patch('embedding.faiss.IndexHNSWFlat')
    @patch('embedding.Path.exists')
    def test_embed_emails_already_embedded(self, mock_exists, mock_index_class, mock_sentence_transformer, mock_cuda):
        """Test embedding emails that are already embedded."""
        mock_cuda.return_value = False
        mock_exists.return_value = False
        mock_model = MagicMock()
        mock_sentence_transformer.return_value = mock_model
        mock_index = MagicMock()
        mock_index.ntotal = 0
        mock_index_class.return_value = mock_index
        
        with patch('builtins.open', mock_open()):
            with patch('embedding.faiss.write_index'):
                manager = EmbeddingManager()
                manager.uid_to_faiss_id = {'1': 0, '2': 1}  # Already embedded
                manager.embed_emails(self.test_emails)
        
        # Check that model.encode was not called
        mock_model.encode.assert_not_called()
        
        # Check that index.add was not called
        mock_index.add.assert_not_called()
    
    @patch('embedding.torch.cuda.is_available')
    @patch('embedding.SentenceTransformer')
    @patch('embedding.faiss.IndexHNSWFlat')
    @patch('embedding.Path.exists')
    def test_search_similar_emails(self, mock_exists, mock_index_class, mock_sentence_transformer, mock_cuda):
        """Test searching for similar emails."""
        mock_cuda.return_value = False
        mock_exists.return_value = False
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_sentence_transformer.return_value = mock_model
        mock_index = MagicMock()
        mock_index.ntotal = 2
        mock_index.search.return_value = (np.array([[0.1, 0.2]]), np.array([[0, 1]]))
        mock_index_class.return_value = mock_index
        
        with patch('builtins.open', mock_open()):
            with patch('embedding.faiss.write_index'):
                manager = EmbeddingManager()
                manager.faiss_id_to_uid = {'0': '1', '1': '2'}
                
                results = manager.search_similar_emails('test query', k=2)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['uid'], '1')
        self.assertEqual(results[1]['uid'], '2')
        self.assertAlmostEqual(results[0]['similarity_score'], 0.9, places=1)
        self.assertAlmostEqual(results[1]['similarity_score'], 0.8, places=1)
    
    @patch('embedding.torch.cuda.is_available')
    @patch('embedding.SentenceTransformer')
    @patch('embedding.faiss.IndexHNSWFlat')
    @patch('embedding.Path.exists')
    def test_search_similar_emails_empty_index(self, mock_exists, mock_index_class, mock_sentence_transformer, mock_cuda):
        """Test searching for similar emails with empty index."""
        mock_cuda.return_value = False
        mock_exists.return_value = False
        mock_model = MagicMock()
        mock_sentence_transformer.return_value = mock_model
        mock_index = MagicMock()
        mock_index.ntotal = 0
        mock_index_class.return_value = mock_index
        
        with patch('builtins.open', mock_open()):
            with patch('embedding.faiss.write_index'):
                manager = EmbeddingManager()
                
                results = manager.search_similar_emails('test query', k=2)
        
        self.assertEqual(len(results), 0)
    
    @patch('embedding.torch.cuda.is_available')
    @patch('embedding.SentenceTransformer')
    @patch('embedding.faiss.IndexHNSWFlat')
    @patch('embedding.Path.exists')
    def test_clear_index(self, mock_exists, mock_index_class, mock_sentence_transformer, mock_cuda):
        """Test clearing the index."""
        mock_cuda.return_value = False
        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_sentence_transformer.return_value = mock_model
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index
        
        with patch('builtins.open', mock_open()):
            with patch('embedding.faiss.write_index'):
                with patch('embedding.Path.unlink') as mock_unlink:
                    manager = EmbeddingManager()
                    manager.uid_to_faiss_id = {'1': 0}
                    manager.faiss_id_to_uid = {'0': '1'}
                    
                    manager.clear_index()
        
        # Check that mappings were cleared
        self.assertEqual(manager.uid_to_faiss_id, {})
        self.assertEqual(manager.faiss_id_to_uid, {})
        
        # Check that files were deleted
        self.assertEqual(mock_unlink.call_count, 2)


if __name__ == '__main__':
    unittest.main()
