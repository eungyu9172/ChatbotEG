from langchain_core.messages import SystemMessage, HumanMessage

from states import ChatState
from config import PROCESSING_STAGES
from prompts import SYSTEM_PROMPTS
from utils.llm_clients import gpt_4o_mini
from utils.token_counter import count_tokens
from utils.logger import logger


def check_answerability(state: ChatState) -> ChatState:
    contexts = state.get("reranked_context", [])
    user_query = state["user_query"]
    messages = state.get("messages", [])
    recent_messages = messages[-10:] if len(messages) > 10 else messages

    logger.info(f"[Check Answerable] 답변 가능성 판별 시작: {user_query}")
    logger.debug(f"[Check Answerable] 컨텍스트: {len(contexts)}개")
    logger.debug(f"[Check Answerable] 최근 10개 대화 히스토리: {recent_messages}")

    context_text = "\n".join(contexts)

    system_prompt_with_context = SystemMessage(content=f"""
    {SYSTEM_PROMPTS["check_answerable"]}

    컨텍스트:
    {context_text}
    """)
    user_query_with_context = f"질문: {user_query}\n\n컨텍스트:\n{context_text}"
    new_user_message = HumanMessage(content=user_query_with_context)
    prompt = [system_prompt_with_context] + recent_messages + [new_user_message]

    # 토큰 수 계산 및 로깅
    context_tokens = count_tokens(context_text)
    total_prompt_tokens = sum(count_tokens(getattr(msg, 'content', str(msg))) for msg in prompt)

    logger.debug(f"[Check Answerable] 컨텍스트 토큰: {context_tokens}")
    logger.debug(f"[Check Answerable] 전체 프롬프트 토큰: {total_prompt_tokens}")

    result = gpt_4o_mini.invoke(prompt).content.strip()
    is_answerable = result.upper().startswith("YES")

    logger.info(f"[Check Answerable] LLM 판별 결과: '{result}' → 답변 가능: {is_answerable}")

    if is_answerable:
        logger.info("[Check Answerable] ✅ 컨텍스트로 답변 가능 - generate 단계로 진행")
    else:
        logger.info("[Check Answerable] ❌ 컨텍스트 불충분 - 추가 정보 요청")

    return {
        "is_answerable": is_answerable,
        "processing_stage": PROCESSING_STAGES["CHECKED_ANSWERABILITY"]
    }
