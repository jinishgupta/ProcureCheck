import faiss
import numpy as np

class BidderIndex:

    def __init__(self, dim):
        self.index = faiss.IndexFlatL2(dim)
        self.meta = []

    def add(self, emb, meta):
        self.index.add(np.array([emb]).astype("float32"))
        self.meta.append(meta)

    def search(self, emb, k=5):
        D, I = self.index.search(
            np.array([emb]).astype("float32"), k
        )

        return [self.meta[i] for i in I[0]]