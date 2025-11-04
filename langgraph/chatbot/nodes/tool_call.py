import json

from langchain_core.messages import ToolMessage
from langgraph.prebuilt import ToolNode

from states import ChatState
from utils.logger import logger
# from mcp_client.client_manager import get_mcp_manager
from utils.llm_clients import AVAILABLE_TOOLS


async def tool_call(state: ChatState) -> ChatState:
    """
    도구 호출 노드 (MCP 전용)

    Args:
        state: 현재 그래프 상태

    Returns:
        업데이트된 상태
    """
    messages = state["messages"]

    # 도구 호출 횟수 체크
    tool_call_count = state.get("tool_call_count", 0)
    max_tool_calls = state.get("max_tool_calls", 3)
    if tool_call_count > max_tool_calls:
        logger.warning(f"최대 도구 호출 횟수({max_tool_calls}) 도달")

        # 마지막 메시지에서 tool_call_id 추출
        last_message = messages[-1]
        tool_call_id = "error"
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            tool_call_id = last_message.tool_calls[0].get("id", "error")

        error_message = ToolMessage(
            content="최대 도구 호출 횟수에 도달했습니다.",
            tool_call_id=tool_call_id
        )
        return {
            "messages": [error_message],
            "tool_call_count": tool_call_count + 1
        }

    try:
        # MCP 도구 가져오기
        if not AVAILABLE_TOOLS:
            logger.error("사용 가능한 MCP 도구가 없습니다.")

        logger.info(f"MCP 도구 실행: {len(AVAILABLE_TOOLS)}개 도구 사용 가능")

        # ToolNode로 도구 실행
        tool_node = ToolNode(AVAILABLE_TOOLS)
        result = await tool_node.ainvoke(state)

        logger.info("MCP 도구 실행 완료")

        state_updates = {
            "messages": result["messages"]
        }

        tool_messages = result.get("messages", [])
        for tool_message in tool_messages:
            if isinstance(tool_message, ToolMessage):
                try:
                    # ToolMessage content를 JSON으로 파싱
                    tool_result = json.loads(tool_message.content)

                    # retrieve_documents 결과인지 확인
                    if tool_result.get("success") and "retrieve_results" in tool_result:
                        # retrieve_results state 업데이트
                        state_updates["retrieve_results"] = tool_result["retrieve_results"]
                        state_updates["is_reranked"] = False

                        logger.info(
                            f"✅ [State Update] retrieve_results 업데이트: "
                            f"{len(tool_result['retrieve_results'])}개 문서, "
                            f"컬렉션: {tool_result.get('collection', 'unknown')}"
                        )
                        for i, doc in enumerate(tool_result['retrieve_results']):
                            preview = doc["text"][:60] + "..." if len(doc["text"]) > 80 else doc["text"]
                            logger.debug(f"[Retrieve] Doc {i+1}: {preview} | distance={doc['distance']:.4f}")

                    # rerank_documents 결과인지 확인
                    elif tool_result.get("success") and "reranked_documents" in tool_result:
                        # reranked_context state 업데이트
                        reranked_docs = tool_result["reranked_documents"]
                        state_updates["reranked_context"] = [
                            doc.get("text", "") for doc in reranked_docs
                        ]
                        state_updates["is_reranked"] = True

                        logger.info(
                            f"✅ [State Update] reranked_context 업데이트: "
                            f"{len(reranked_docs)}개 문서 (상위 순위)"
                        )
                        for i, doc in enumerate(reranked_docs):
                            preview = doc["text"][:60] + "..."
                            logger.debug(f"[Rerank] #{i+1} (원래 #{doc['original_rank']}): ")
                            logger.debug(f"score={doc['rerank_score']:.4f} | {preview}")

                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    # JSON 파싱 실패 시 로그만 남기고 계속 진행
                    logger.debug(f"ToolMessage 파싱 실패 (무시): {e}")
                    continue

        return state_updates

    except Exception as e:
        logger.error(f"MCP 도구 호출 중 오류: {e}", exc_info=True)

        # 에러 메시지 생성
        last_message = messages[-1]
        tool_call_id = "error"
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            tool_call_id = last_message.tool_calls[0].get("id", "error")

        error_message = ToolMessage(
            content=f"도구 실행 중 오류가 발생했습니다: {str(e)}",
            tool_call_id=tool_call_id
        )

        return {
            "messages": [error_message],
            "tool_call_count": tool_call_count + 1
        }
