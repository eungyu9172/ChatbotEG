from typing import List, Dict, Any

from states import ChatState
from config import PROCESSING_STAGES, RERANK_CONFIG
from utils.logger import logger
from FlagEmbedding import FlagReranker


_reranker = None


def _get_reranker():
    """Reranker 싱글톤 로드"""
    global _reranker
    if _reranker is None:
        _reranker = FlagReranker(
            RERANK_CONFIG["model_name"],
            use_fp16=RERANK_CONFIG["use_fp16"]
        )
        logger.info(f"[Rerank] ✅ BGE Reranker 로드: {RERANK_CONFIG['model_name']}")
    return _reranker


def rerank(state: ChatState) -> ChatState:
    """문서 재순위 노드 - BGE 기반 reranking"""
    retrieve_results = state.get("retrieve_results", [])
    user_query = state.get("rewritten_query", state["user_query"])

    logger.info(f"[Rerank] 재순위 시작: {len(retrieve_results)}개 문서")

    if not retrieve_results:
        logger.warning("[Rerank] ⚠️ 검색 결과 없음")
        return {
            "reranked_context": [],
            "processing_stage": PROCESSING_STAGES["RERANKED"]
        }

    try:
        model = _get_reranker()
        pairs = [(user_query, doc["text"]) for doc in retrieve_results]

        scores = model.compute_score(pairs, normalize=True)

        if not isinstance(scores, list):
            scores = [scores]

        # 점수 결합 및 정렬
        scored_docs: List[Dict[str, Any]] = []
        for i, doc in enumerate(retrieve_results):
            scored_docs.append({
                "text": doc["text"],
                "metadata": doc.get("metadata", {}),
                "original_rank": doc.get("rank", i + 1),
                "rerank_score": float(scores[i])
            })

        scored_docs.sort(key=lambda x: x["rerank_score"], reverse=True)
        top_docs = scored_docs[:RERANK_CONFIG["top_k"]]
        reranked_context = [doc["text"] for doc in top_docs]

        logger.info(f"[Rerank] ✅ 재순위 완료: 상위 {len(reranked_context)}개 선택")
        for i, doc in enumerate(top_docs):
            preview = doc["text"][:60] + "..."
            logger.debug(
                f"[Rerank] #{i+1} (원래 #{doc['original_rank']}): "
                f"score={doc['rerank_score']:.4f} | {preview}"
            )

        return {
            "reranked_context": reranked_context,
            "processing_stage": PROCESSING_STAGES["RERANKED"]
        }

    except Exception as e:
        logger.error(f"[Rerank] ❌ 재순위 실패: {e}", exc_info=True)
        fallback = [doc["text"] for doc in retrieve_results[:RERANK_CONFIG["top_k"]]]
        logger.warning(f"[Rerank] 폴백: 원본 상위 {len(fallback)}개 사용")
        return {
            "reranked_context": fallback,
            "processing_stage": PROCESSING_STAGES["RERANKED"]
        }
