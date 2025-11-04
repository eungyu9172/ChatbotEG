from pathlib import Path
import json

from fastmcp import FastMCP
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from chromadb import Documents, EmbeddingFunction, Embeddings

mcp = FastMCP("RetrieveServer")


# ==================== Embedding Function ====================
class CustomSentenceTransformerEmbedding(EmbeddingFunction):
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu"):
        self.model = SentenceTransformer(model_name, device=device)
        self.batch_size = 64
        self.normalize_embeddings = True

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = self.model.encode(
            input,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embeddings.tolist()


# ==================== 글로벌 클라이언트 (싱글톤) ====================
_client = None
_embedding_function = None
_collections_cache = {}

SERVER_DIR = Path(__file__).resolve().parent  # mcp_servers/retrieve_rag_server/
PROJECT_ROOT = SERVER_DIR.parent.parent       # langgraph/

# ChromaDB 경로 (절대 경로)
CHROMA_DIR = PROJECT_ROOT / ".chroma"


def _get_client():
    """ChromaDB 클라이언트 초기화 (싱글톤)"""
    global _client, _embedding_function
    if _client is None:
        _client = PersistentClient(path=str(CHROMA_DIR))
        _embedding_function = CustomSentenceTransformerEmbedding(model_name="BAAI/bge-m3")
    return _client


def _get_collection(collection_name: str):
    """특정 컬렉션 가져오기 (캐싱)"""
    global _collections_cache

    if collection_name not in _collections_cache:
        client = _get_client()
        try:
            collection = client.get_collection(
                name=collection_name,
                embedding_function=_embedding_function
            )
            _collections_cache[collection_name] = collection
        except Exception as e:
            raise ValueError(f"Collection '{collection_name}' not found: {str(e)}")

    return _collections_cache[collection_name]


# ==================== Collection 메타데이터 정의 ====================
COLLECTION_METADATA = {
    "innorules": {
        "name": "innorules",
        "description": "이노룰즈 제품, 사내 규정 및 정책 문서 컬렉션. 인사, 복지, 휴가, 출장, 업무 프로세스 등에 관한 공식 문서",
        # "categories": ["policy", "hr", "internal"],
        "language": "ko"
    }
}


# ==================== Resource: 컬렉션 목록 ====================
@mcp.resource("collections://list")
def list_collections() -> str:
    """
    사용 가능한 ChromaDB 컬렉션 목록과 설명을 제공합니다.
    이 리소스를 참고하여 어느 컬렉션에서 검색할지 결정하세요.
    """
    collections_info = {
        "available_collections": COLLECTION_METADATA,
        "total_count": len(COLLECTION_METADATA),
        "usage_guide": {
            "description": "retrieve_documents 툴을 사용할 때 collection_name 파라미터에 위 컬렉션 이름을 지정하세요",
            "example": "innorules 관련 질문이면 collection_name='innorules'를 사용"
        }
    }
    return json.dumps(collections_info, ensure_ascii=False, indent=2)


@mcp.resource("collections://{collection_name}/info")
def get_collection_info(collection_name: str) -> str:
    """
    특정 컬렉션의 상세 정보를 제공합니다.

    Args:
        collection_name: 조회할 컬렉션 이름
    """
    if collection_name not in COLLECTION_METADATA:
        return json.dumps({
            "error": f"Collection '{collection_name}' not found",
            "available_collections": list(COLLECTION_METADATA.keys())
        }, ensure_ascii=False)

    try:
        collection = _get_collection(collection_name)
        metadata = COLLECTION_METADATA[collection_name]

        info = {
            "name": collection_name,
            "metadata": metadata,
            "document_count": collection.count(),
            "status": "available"
        }
        return json.dumps(info, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "name": collection_name
        }, ensure_ascii=False)


# ==================== Tool: 문서 검색 ====================
@mcp.tool()
def retrieve_documents(
    query: str,
    collection_name: str,
    top_k: int = 10
) -> dict:
    """
    지정된 ChromaDB 컬렉션에서 관련 문서를 검색합니다.

    먼저 'collections://list' 리소스를 참고하여 적절한 컬렉션을 선택하세요.

    Args:
        query: 검색할 쿼리 텍스트
        collection_name: 검색할 컬렉션 이름 (현재 innorules 하나만 존재)
        top_k: 반환할 최대 문서 수 (기본값: 10)

    Returns:
        검색 결과를 담은 딕셔너리
    """
    try:
        # 컬렉션 존재 여부 확인
        if collection_name not in COLLECTION_METADATA:
            return {
                "success": False,
                "error": f"Unknown collection: {collection_name}",
                "available_collections": list(COLLECTION_METADATA.keys()),
                "query": query,
                "results": [],
                "count": 0
            }

        # 컬렉션 가져오기
        collection = _get_collection(collection_name)

        # ChromaDB 쿼리 실행
        raw_results = collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        # 결과 포맷팅
        results = []
        if raw_results["documents"] and len(raw_results["documents"][0]) > 0:
            for i in range(len(raw_results["documents"][0])):
                results.append({
                    "text": raw_results["documents"][0][i],
                    "metadata": raw_results["metadatas"][0][i] if raw_results["metadatas"] else {},
                    "distance": raw_results["distances"][0][i] if raw_results["distances"] else 0.0,
                    "rank": i + 1,
                    "collection": collection_name
                })

        for i, doc in enumerate(results[:3]):  # 상위 3개만 로깅
            preview = doc["text"][:80] + "..." if len(doc["text"]) > 80 else doc["text"]
            print(preview)

        return {
            "success": True,
            "query": query,
            "collection": collection_name,
            "collection_description": COLLECTION_METADATA[collection_name]["description"],
            "retrieve_results": results,
            "count": len(results)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "collection": collection_name,
            "retrieve_results": [],
            "count": 0
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
