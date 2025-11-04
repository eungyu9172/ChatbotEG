from typing import TypedDict, Optional, Annotated, List, Dict, Any
from operator import add
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage


class ChatState(TypedDict):
    # 기본 처리 상태
    session_id: str
    error: Optional[str]
    processing_stage: str
    tool_call_count: int
    max_tool_calls: int

    # 쿼리 관련
    user_query: str
    is_simple_query: Optional[bool]
    rewritten_query: Optional[str]

    # 검색 관련
    retrieve_results: Optional[List[Dict[str, Any]]]
    reranked_context: Optional[List[str]]
    is_reranked: Optional[bool]
    is_answerable: Optional[bool]
    retrieval_time: Optional[float]

    # 응답 관련
    final_answer: Optional[str]
    confidence_score: Optional[float]

    # 대화 히스토리
    messages: Annotated[List[AIMessage | HumanMessage | SystemMessage | ToolMessage], add]
