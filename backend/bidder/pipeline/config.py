"""
Configuration for bidder pipeline using environment variables
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Embedding model configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# FAISS dimension (must match the embedding model output dimension)
FAISS_DIM = int(os.getenv("FAISS_DIM", "384"))

# Google Cloud Platform credentials path for OCR
GCP_KEY_PATH = os.getenv("GCP_KEY_PATH", "")

# Validate required environment variables
if not GCP_KEY_PATH:
    print("Warning: GCP_KEY_PATH not set in environment variables")
