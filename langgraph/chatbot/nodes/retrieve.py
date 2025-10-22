from typing import List, Dict, Any
from datetime import datetime

from chromadb import PersistentClient

from embeddings import CustomSentenceTransformerEmbedding
from states import ChatState
from config import PROCESSING_STAGES, CHROMA_CONFIG, RETRIEVE_CONFIG
from utils.logger import logger


_client = None
_collection = None


def _get_collection():
    """ChromaDB 컬렉션 싱글톤"""
    global _client, _collection
    if _collection is None:
        _client = PersistentClient(path=CHROMA_CONFIG["persist_dir"])
        _collection = _client.get_collection(
            name=CHROMA_CONFIG["collection_name"],
            embedding_function=CustomSentenceTransformerEmbedding(model_name="BAAI/bge-m3")
        )
        logger.info(f"[Retrieve] ✅ ChromaDB 연결 완료: {CHROMA_CONFIG['collection_name']}")
    return _collection


# TODO: hybrid 검색 노드
def retrieve(state: ChatState) -> ChatState:
    """검색 노드 - ChromaDB 유사도 검색"""
    rewritten_query = state.get("rewritten_query", state["user_query"])
    logger.info(f"[Retrieve] 검색 시작: {rewritten_query}")

    start_time = datetime.now()

    try:
        col = _get_collection()

        # ChromaDB 쿼리 (자동 임베딩 + 코사인 유사도)
        raw = col.query(
            query_texts=[rewritten_query],
            n_results=RETRIEVE_CONFIG["top_k"],
            include=["documents", "metadatas", "distances"]
        )

        # 결과 포맷팅: retrieve_results는 List[Dict]
        results: List[Dict[str, Any]] = []
        if raw["documents"] and len(raw["documents"][0]) > 0:
            for i in range(len(raw["documents"][0])):
                results.append({
                    "text": raw["documents"][0][i],
                    "metadata": raw["metadatas"][0][i] if raw["metadatas"] else {},
                    "distance": raw["distances"][0][i] if raw["distances"] else 0.0,
                    "rank": i + 1
                })

        retrieval_time = (datetime.now() - start_time).total_seconds()

        logger.info(f"[Retrieve] ✅ 검색 완료: {len(results)}개 문서 검색됨 ({retrieval_time:.3f}초)")
        for i, doc in enumerate(results[:3]):  # 상위 3개만 로깅
            preview = doc["text"][:80] + "..." if len(doc["text"]) > 80 else doc["text"]
            logger.debug(f"[Retrieve] Doc {i+1}: {preview} | distance={doc['distance']:.4f}")

        return {
            "retrieve_results": results,
            "retrieval_time": retrieval_time,
            "processing_stage": PROCESSING_STAGES["RETRIEVED"]
        }

    except Exception as e:
        logger.error(f"[Retrieve] ❌ 검색 실패: {e}", exc_info=True)
        # 폴백: 빈 결과로 진행
        return {
            "retrieve_results": [],
            "retrieval_time": 0.0,
            "processing_stage": PROCESSING_STAGES["RETRIEVED"],
            "error": str(e)
        }
