from typing import List, Dict, Any
from chromadb import PersistentClient

from .embeddings import CustomSentenceTransformerEmbedding


class ChromaStore:
    def __init__(
        self,
        path: str,
        collection: str,
        embedding_model: str,
        batch_size: int = 64,
        normalize_embeddings: bool = True
    ):
        self.client = PersistentClient(path=path)
        try:
            self.embedding_function = CustomSentenceTransformerEmbedding(
                model_name=embedding_model,
                batch_size=batch_size,
                normalize_embeddings=normalize_embeddings,
                device="cpu"
            )
        except Exception as e:
            print(f"Error: {e}")
            raise ValueError(f"지원하지 않는 임베딩 모델: {embedding_model}")
        self.col = self.client.get_or_create_collection(
            name=collection,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

    def get_latest_version(self, document_id: str) -> int:
        """document_id에 해당하는 최신 버전 번호 조회"""
        try:
            results = self.col.get(
                where={"document_id": document_id},
                limit=1,
                include=["metadatas"]
            )
            if results["metadatas"]:
                return results["metadatas"][0].get("version", 0)
            return 0
        except Exception:
            return 0

    def delete_document(self, document_id: str):
        """document_id에 해당하는 모든 청크 삭제"""
        try:
            self.col.delete(where={"document_id": document_id})
            print("  🗑️  기존 청크 삭제 완료")
        except Exception as e:
            print(f"  ⚠️  삭제 실패: {e}")

    def upsert(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]]
    ):
        # Chroma 0.5의 add는 동일 id 중복 시 에러 → delete 후 add 방식으로 upsert
        # TODO: 현재는 chunk별로 uuid를 부여해서 겹치지 않으나 파일 이름을 통해 생성 규칙을 정하고 버전 관리 필요
        try:
            self.col.delete(ids=ids)
        except Exception:
            pass
        self.col.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
