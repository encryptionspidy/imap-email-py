"""Embedding management with GPU/CPU fallback and FAISS indexing."""
import torch
import faiss
import numpy as np
import json
from typing import List, Dict, Optional
from pathlib import Path
from sentence_transformers import SentenceTransformer
from config import Config
from rich import print

class EmbeddingManager:
    """Handles email embedding and FAISS index management."""
    
    def __init__(self):
        self.device = self._get_device()
        self.model = self._load_model()
        self.index = None
        self.uid_to_faiss_id = {}
        self.faiss_id_to_uid = {}
        self._load_or_create_index()
        
    def _get_device(self) -> str:
        """Determine best available device (GPU/CPU)."""
        if torch.cuda.is_available():
            device = "cuda"
            print(f"[green]Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = "cpu"
            print("[yellow]Using CPU for embeddings")
        return device
    
    def _load_model(self) -> SentenceTransformer:
        """Load sentence transformer model."""
        print(f"[blue]Loading model: {Config.EMBEDDING_MODEL}")
        model = SentenceTransformer(Config.EMBEDDING_MODEL, device=self.device)
        return model
    
    def _load_or_create_index(self) -> None:
        """Load existing FAISS index or create new one."""
        if Config.FAISS_INDEX_PATH.exists():
            print("[blue]Loading existing FAISS index...")
            self.index = faiss.read_index(str(Config.FAISS_INDEX_PATH))
            self._load_mapping()
        else:
            print("[blue]Creating new FAISS index...")
            # Get embedding dimension from model
            sample_embedding = self.model.encode(["test"])
            dimension = sample_embedding.shape[1]
            
            # Create HNSW index for efficient similarity search
            self.index = faiss.IndexHNSWFlat(dimension, 32)
            self.index.hnsw.efConstruction = 200
            self.index.hnsw.efSearch = 50
            self._save_index()
            
    def _load_mapping(self) -> None:
        """Load UID to FAISS ID mapping."""
        if Config.FAISS_MAPPING_PATH.exists():
            with open(Config.FAISS_MAPPING_PATH, 'r') as f:
                data = json.load(f)
                self.uid_to_faiss_id = data.get('uid_to_faiss_id', {})
                self.faiss_id_to_uid = data.get('faiss_id_to_uid', {})
        else:
            self.uid_to_faiss_id = {}
            self.faiss_id_to_uid = {}
    
    def _save_mapping(self) -> None:
        """Save UID to FAISS ID mapping."""
        data = {
            'uid_to_faiss_id': self.uid_to_faiss_id,
            'faiss_id_to_uid': self.faiss_id_to_uid
        }
        with open(Config.FAISS_MAPPING_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_index(self) -> None:
        """Save FAISS index to disk."""
        faiss.write_index(self.index, str(Config.FAISS_INDEX_PATH))
        self._save_mapping()
    
    def embed_emails(self, emails: List[Dict]) -> None:
        """Embed email bodies and add to FAISS index."""
        if not emails:
            print("[yellow]No emails to embed")
            return
        
        # Filter emails that aren't already indexed
        new_emails = [
            email for email in emails 
            if email['uid'] not in self.uid_to_faiss_id
        ]
        
        if not new_emails:
            print("[yellow]All emails already embedded")
            return
        
        print(f"[blue]Embedding {len(new_emails)} new emails...")
        
        # Process in batches for memory efficiency
        for i in range(0, len(new_emails), Config.EMBEDDING_BATCH_SIZE):
            batch = new_emails[i:i + Config.EMBEDDING_BATCH_SIZE]
            self._embed_batch(batch)
        
        self._save_index()
        print(f"[green]Successfully embedded {len(new_emails)} emails")
    
    def _embed_batch(self, batch: List[Dict]) -> None:
        """Embed a batch of emails."""
        # Extract email bodies for embedding
        bodies = []
        for email in batch:
            body = email.get('body', '')
            if isinstance(body, bytes):
                try:
                    body = body.decode('utf-8')
                except UnicodeDecodeError:
                    body = body.decode('utf-8', errors='ignore')
            bodies.append(str(body))
        
        # Generate embeddings with GPU acceleration and memory optimization
        with torch.no_grad():
            embeddings = self.model.encode(
                bodies, 
                show_progress_bar=False, 
                device=self.device, 
                normalize_embeddings=True
            )
        
        # Add to FAISS index
        start_id = self.index.ntotal
        self.index.add(embeddings.astype('float32'))
        
        # Update mappings
        for i, email in enumerate(batch):
            faiss_id = start_id + i
            uid = email['uid']
            self.uid_to_faiss_id[uid] = faiss_id
            self.faiss_id_to_uid[str(faiss_id)] = uid
    
    def search_similar_emails(self, query: str, k: int = 10) -> List[Dict]:
        """Search for similar emails using semantic similarity."""
        if self.index.ntotal == 0:
            return []
        
        # Encode query with GPU acceleration
        with torch.no_grad():
            query_embedding = self.model.encode(
                [query], 
                device=self.device, 
                normalize_embeddings=True
            )
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Convert results to UID list
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx != -1:  # Valid result
                uid = self.faiss_id_to_uid.get(str(idx))
                if uid:
                    results.append({
                        'uid': uid,
                        'similarity_score': 1 - distance,  # Convert distance to similarity
                        'distance': distance
                    })
        
        return results
    
    def clear_index(self) -> None:
        """Clear the FAISS index and mappings."""
        if Config.FAISS_INDEX_PATH.exists():
            Config.FAISS_INDEX_PATH.unlink()
        if Config.FAISS_MAPPING_PATH.exists():
            Config.FAISS_MAPPING_PATH.unlink()
        
        # Reset mappings
        self.uid_to_faiss_id = {}
        self.faiss_id_to_uid = {}
        
        # Recreate index
        self._load_or_create_index()
        print("[green]FAISS index cleared successfully")
