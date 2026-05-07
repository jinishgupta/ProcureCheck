from bidder.pipeline.config import EMBEDDING_MODEL

# Lazy-loaded — do NOT instantiate SentenceTransformer at module level.
# PyTorch initialization takes minutes and causes Render's port-scan to time
# out before uvicorn can bind to the port.
_model = None

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer  # noqa: deferred
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model

def embed(text):
    return _get_model().encode(text)