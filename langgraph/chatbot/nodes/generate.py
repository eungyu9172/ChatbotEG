from langchain_core.messages import SystemMessage, HumanMessage

from states import ChatState
from config import PROCESSING_STAGES
from prompts import SYSTEM_PROMPTS
from utils.llm_clients import gpt_4o_with_tools
from utils.token_counter import count_tokens
from utils.logger import logger


def generate_answer(state: ChatState) -> ChatState:
    contexts = "\n".join(state["reranked_context"])
    messages = state.get("messages", [])
    logger.debug(f"[Generate] messages: {messages}")
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_message = msg
            break

    logger.info(f"[Generate] 최종 답변 생성 시작: {user_message.content}")
    logger.debug(f"[Generate] 컨텍스트: {len(contexts)}개, 메시지 히스토리: {len(messages)}개")

    context_text = "\n".join(contexts)

    # 컨텍스트를 포함한 시스템 프롬프트 생성
    system_prompt_with_context = SystemMessage(content=f"""
{SYSTEM_PROMPTS["generate_answer"]}

참고 컨텍스트:
{context_text}
""")
    prompt = [system_prompt_with_context] + messages

    # 토큰 수 로깅
    context_tokens = count_tokens(context_text)
    total_prompt_tokens = sum(count_tokens(getattr(msg, 'content', str(msg))) for msg in prompt)
    logger.debug(f"[Generate] 컨텍스트 토큰: {context_tokens}")
    logger.debug(f"[Generate] 전체 프롬프트 토큰: {total_prompt_tokens}")

    response = gpt_4o_with_tools.invoke(prompt)

    # Tool 호출 확인
    tool_calls = getattr(response, 'tool_calls', None)
    if tool_calls:
        logger.info(f"[Generate] 🔧 도구 호출 요청됨: {len(tool_calls)}개")
        for i, tool_call in enumerate(tool_calls):
            tool_name = tool_call.get('name', 'unknown')
            tool_args = tool_call.get('args', {})
            logger.debug(f"[Generate] 도구 {i+1}: {tool_name}({tool_args})")
        logger.info(f"[Generate] Response: {response}")
        return {
            "messages": [response],
            "tool_call_count": state.get("tool_call_count", 0) + 1,
            "processing_stage": PROCESSING_STAGES["TOOLS_NEEDED"]
        }
    else:
        response_tokens = count_tokens(response.content) if response.content else 0
        logger.info("[Generate] ✅ 최종 답변 생성 완료")
        logger.debug(f"[Generate] 답변 길이: {len(response.content)}자 ({response_tokens} 토큰)")
        logger.info(f"[Generate] Response: {response}")
        return {
            "final_answer": response.content or "",
            "messages": [response],
            "processing_stage": PROCESSING_STAGES["ANSWERED_WITH_CONTEXT"]
        }
