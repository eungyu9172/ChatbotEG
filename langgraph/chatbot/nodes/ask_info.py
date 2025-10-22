from langchain_core.messages import SystemMessage, HumanMessage

from states import ChatState
from config import PROCESSING_STAGES
from prompts import SYSTEM_PROMPTS
from utils.llm_clients import gpt_4o_mini
from utils.token_counter import count_tokens
from utils.logger import logger


def ask_for_more_info(state: ChatState) -> ChatState:
    messages = state.get("messages", [])
    logger.info(f"[Generate] messages: {messages}")
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_message = msg
            break
    contexts = state.get("reranked_context", [])

    logger.info(f"[Ask Info] 추가 정보 요청 생성: {user_message.content}")
    logger.debug(f"[Ask Info] 불충분한 컨텍스트: {len(contexts)}개")

    system_prompt = SystemMessage(content=SYSTEM_PROMPTS["ask_info"])
    prompt = [system_prompt] + messages

    # 토큰 수 로깅
    total_tokens = sum(count_tokens(getattr(msg, 'content', str(msg))) for msg in prompt)
    logger.debug(f"[Ask Info] 추가 정보 요청 프롬프트 토큰: {total_tokens}")

    response = gpt_4o_mini.invoke(prompt)

    response_tokens = count_tokens(response.content) if response.content else 0

    logger.info("[Ask Info] ✅ 추가 정보 요청 생성 완료")
    logger.debug(f"[Ask Info] 요청 길이: {len(response.content)}자 ({response_tokens} 토큰)")

    return {
        "final_answer": response.content,
        "messages": [response],
        "processing_stage": PROCESSING_STAGES["ASKED_FOR_MORE_INFO"]
    }
