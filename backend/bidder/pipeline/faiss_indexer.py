import numpy as np

# faiss is imported lazily when the class is first used so that server startup
# (uvicorn binding) is not blocked by PyTorch/faiss initialisation.
def _faiss():
    import faiss  # noqa: deferred
    return faiss

class BidderIndex:

    def __init__(self, dim):
        self.index = _faiss().IndexFlatIP(dim)
        self.meta = []
        self.embeddings = []

    def add(self, emb, meta):
        # Normalise for inner product to act as cosine similarity
        vec = np.array([emb]).astype("float32")
        _faiss().normalize_L2(vec)
        self.index.add(vec)
        self.meta.append(meta)
        self.embeddings.append(vec)

    def search(self, emb, k=5):
        vec = np.array([emb]).astype("float32")
        _faiss().normalize_L2(vec)
        D, I = self.index.search(vec, k)
        return [self.meta[i] for i in I[0]]

    def save(self, path: str):
        _faiss().write_index(self.index, path)