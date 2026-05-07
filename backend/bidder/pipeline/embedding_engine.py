from sentence_transformers import SentenceTransformer
from bidder.pipeline.config import EMBEDDING_MODEL

model = SentenceTransformer(EMBEDDING_MODEL)

def embed(text):
    return model.encode(text)