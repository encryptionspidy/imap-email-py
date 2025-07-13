"""Core module for loading and sharing the model, FAISS index, and DB connection."""

import os
import torch
import faiss
from sentence_transformers import SentenceTransformer
from config import Config
from metadata_store import MetadataStore

# Load environment
model_name = Config.EMBEDDING_MODEL
index_filename = str(Config.FAISS_INDEX_PATH)
device = "cuda" if torch.cuda.is_available() else "cpu"

# Check for GPU
if device == "cpu":
    print("[Warning] CUDA device not found. Running on CPU can be slow.")

# Load the SentenceTransformer model
model = SentenceTransformer(model_name, device=device)
model.eval()

# Load or create FAISS index
if os.path.exists(index_filename):
    index = faiss.read_index(index_filename)
else:
    index = faiss.IndexHNSWFlat(768, 32)

# Database connection
metadata_store = MetadataStore()
