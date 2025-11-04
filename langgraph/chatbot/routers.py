from langchain_core.messages import AIMessage
from langgraph.graph import END

from states import ChatState
from config import PROCESSING_STAGES
from utils.logger import logger


def input_valid_router(state: ChatState) -> str:
    """입력 유효성 검사 결과에 따른 라우팅"""
    return "error" if state.get("error") else "rewrite"


def check_simple_router(state: ChatState) -> str:
    """단순 쿼리 여부에 따른 라우팅"""
    return "direct_answer" if state.get("is_simple_query") else "generate"


# def check_answerable_router(state: ChatState) -> str:
#     """답변 가능성에 따른 라우팅"""
#     return "generate" if state.get("is_answerable") else "ask_info"


def should_continue(state: ChatState) -> str:
    """도구 호출 필요성을 판단하여 라우팅"""
    messages = state.get("messages", [])
    tool_call_count = state.get("tool_call_count", 0)
    max_tool_calls = state.get("max_tool_calls", 3)

    if not messages:
        return END

    if tool_call_count > max_tool_calls:
        logger.info(f"[Router] 최대 도구 호출 횟수({max_tool_calls}) 도달, 종료")
        return "force_final_answer"

    last_message = messages[-1]
    logger.info(f"[Router - should_continue] Last message type: {type(last_message).__name__}")

    # AIMessage 객체이고 tool_calls가 있는지 확인
    if isinstance(last_message, AIMessage):
        tool_calls = getattr(last_message, 'tool_calls', None)
        if tool_calls and len(tool_calls) > 0:
            logger.info(f"[Router - should_continue]  🔧 Tool calls detected: {len(tool_calls)} tools")
            for i, tool_call in enumerate(tool_calls):
                name = tool_call.get('name', 'unknown')
                logger.info(f"  → Tool {i+1}: {name}")
            return "tools"

    logger.info("[Router - should_continue] No tool calls, ending")
    return END


def tools_router(state: ChatState) -> str:
    """도구 실행 후 다음 노드 결정"""
    stage = state.get("processing_stage", "")

    if stage == PROCESSING_STAGES["TOOL_ASSISTED_DIRECT_ANSWER"]:
        return "direct_answer"
    elif stage in [PROCESSING_STAGES["TOOL_ASSISTED_GENERATE"]]:
        return "generate"
    else:
        return "direct_answer"
