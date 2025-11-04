from typing import List, Dict, Any

from fastmcp import FastMCP
from FlagEmbedding import FlagReranker

mcp = FastMCP("RerankServer")

# 글로벌 reranker 모델 (싱글톤)
_reranker = None


def _get_reranker():
    """Reranker 싱글톤 로드"""
    global _reranker
    if _reranker is None:
        _reranker = FlagReranker(
            "BAAI/bge-reranker-v2-m3",
            use_fp16=True
        )
    return _reranker


@mcp.tool()
def rerank_documents(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: int = 5
) -> dict:
    """
    state내에 is_rerank가 False이면서, retrieve_results에 검색된 문서가 존재하는 상태에서는 반드시 rerank 과정을 우선적으로 수행합니다.
    검색된 문서들을 쿼리와의 관련성에 따라 재정렬합니다.

    Args:
        query: 사용자 쿼리
        documents: 재정렬할 문서 리스트 (각 문서는 'text' 필드 필수)
        top_k: 반환할 상위 문서 수 (기본값: 5)

    Returns:
        재정렬된 문서 리스트
    """
    try:
        if not documents:
            return {
                "success": True,
                "query": query,
                "reranked_documents": [],
                "count": 0,
                "message": "No documents to rerank"
            }

        # 문서 텍스트 추출
        doc_texts = [doc.get("text", "") for doc in documents]

        # Query-document 쌍 생성
        pairs = [[query, text] for text in doc_texts]

        # Reranking 수행
        reranker = _get_reranker()
        scores = reranker.compute_score(pairs, normalize=True)

        # 점수와 문서를 결합하여 정렬
        scored_docs = []
        for idx, (doc, score) in enumerate(zip(documents, scores)):
            scored_docs.append({
                **doc,
                "rerank_score": float(score),
                "original_rank": doc.get("rank", idx + 1)
            })

        # 점수 기준 내림차순 정렬
        scored_docs.sort(key=lambda x: x["rerank_score"], reverse=True)

        # 상위 k개만 선택
        top_docs = scored_docs[:top_k]

        # 새로운 순위 부여
        for new_rank, doc in enumerate(top_docs, start=1):
            doc["rank"] = new_rank

        return {
            "success": True,
            "query": query,
            "reranked_documents": top_docs,
            "count": len(top_docs),
            "original_count": len(documents)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "reranked_documents": [],
            "count": 0
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
