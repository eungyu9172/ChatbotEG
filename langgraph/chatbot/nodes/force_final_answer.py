from langchain_core.messages import SystemMessage, ToolMessage

from states import ChatState
from config import PROCESSING_STAGES
from prompts import SYSTEM_PROMPTS
from utils.llm_clients import gpt_4o
from utils.logger import logger


def force_final_answer(state: ChatState) -> ChatState:
    """Tool count 초과 시 강제로 최종 답변 생성"""
    messages = state.get("messages", [])
    user_query = state.get("user_query", "")

    logger.info(f"[Force Final Answer] Tool call count 초과로 강제 답변 생성: {user_query}")

    pending_tool_messages = []
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            # tool_calls가 있으면 각각에 대한 더미 ToolMessage 생성
            logger.warning(f"[Force Final Answer] {len(last_message.tool_calls)}개의 대기 중인 tool_calls 감지 - 더미 응답 생성")

            for tool_call in last_message.tool_calls:
                tool_call_id = tool_call.get('id', 'unknown')
                tool_name = tool_call.get('name', 'unknown')

                dummy_message = ToolMessage(
                    content=f"최대 도구 호출 횟수에 도달하여 '{tool_name}' 도구를 실행할 수 없습니다.",
                    tool_call_id=tool_call_id
                )
                pending_tool_messages.append(dummy_message)

    # Tool 결과들을 포함한 메시지로 최종 답변 생성
    system_prompt = SystemMessage(content=SYSTEM_PROMPTS["force_final_answer"])
    prompt = [system_prompt] + messages + pending_tool_messages
    response = gpt_4o.invoke(prompt)

    logger.info("[Force Final Answer] ✅ 강제 답변 생성 완료")

    return {
        "final_answer": response.content or "죄송합니다. 충분한 정보를 수집하지 못했습니다.",
        "messages": [response],
        "processing_stage": PROCESSING_STAGES["FORCE_ANSWERED"]
    }
