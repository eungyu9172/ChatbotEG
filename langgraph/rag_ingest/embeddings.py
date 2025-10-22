from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer


class CustomSentenceTransformerEmbedding(EmbeddingFunction):
    def __init__(
        self,
        model_name: str,
        batch_size: int = 64,
        normalize_embeddings: bool = True,
        device: str = "cpu"
    ):
        self.model = SentenceTransformer(model_name, device=device)
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings

    def __call__(self, input: Documents) -> Embeddings:
        """ChromaDB가 호출하는 메서드 - Documents를 받아 Embeddings 반환"""
        embeddings = self.model.encode(
            input,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embeddings.tolist()
