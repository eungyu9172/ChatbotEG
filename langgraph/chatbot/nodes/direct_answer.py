from langchain_core.messages import SystemMessage, HumanMessage

from states import ChatState
from config import PROCESSING_STAGES
from prompts import SYSTEM_PROMPTS
from utils.llm_clients import gpt_4o_with_tools
from utils.token_counter import count_tokens
from utils.logger import logger


def direct_answer(state: ChatState) -> ChatState:
    """단순 쿼리에 대한 응답 생성"""
    messages = state.get("messages", [])
    logger.info(f"[Direct Answer] messages: {messages}")
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_message = msg
            break
    logger.info(f"[Direct Answer] 직접 답변 생성 시작: {user_message.content}")
    logger.debug(f"[Direct Answer] 메시지 히스토리: {len(messages)}개")

    if user_message:
        last_msg_type = type(user_message).__name__
        logger.debug(f"[Direct Answer] 유저 메시지: '{last_msg_type}', {user_message.content}")

    system_prompt = SystemMessage(content=SYSTEM_PROMPTS["direct_answer"])
    prompt = [system_prompt] + messages

    # 토큰 수 로깅
    total_prompt_tokens = sum(count_tokens(getattr(msg, 'content', str(msg))) for msg in prompt)
    logger.debug(f"[Direct Answer] 전체 프롬프트 토큰: {total_prompt_tokens}")

    response = gpt_4o_with_tools.invoke(prompt)

    # Tool 호출 정보 로깅
    tool_calls = getattr(response, 'tool_calls', None)
    if tool_calls:
        logger.info(f"[Direct Answer] 🔧 도구 호출 요청됨: {len(tool_calls)}개")
        for i, tool_call in enumerate(tool_calls):
            tool_name = tool_call.get('name', 'unknown')
            tool_args = tool_call.get('args', {})
            logger.debug(f"[Direct Answer] 도구 {i+1}: {tool_name}({tool_args})")
        logger.info(f"[Direct Answer] Response: {response}")
        return {
            "messages": [response],
            "tool_call_count": state.get("tool_call_count", 0) + 1,
            "processing_stage": PROCESSING_STAGES["TOOLS_NEEDED"]
        }
    else:
        response_tokens = count_tokens(response.content) if response.content else 0
        logger.info("✅ [Direct Answer] 직접 답변 생성됨 (도구 호출 없음)")
        logger.debug(f"[Direct Answer] 답변 길이: {len(response.content)}자 ({response_tokens} 토큰)")
        logger.info(f"[Direct Answer] Response: {response}")
        return {
            "final_answer": response.content or "",
            "messages": [response],
            "processing_stage": PROCESSING_STAGES["ANSWERED_DIRECT"]
        }
