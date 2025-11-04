from langchain_core.messages import SystemMessage, HumanMessage

from states import ChatState
from config import PROCESSING_STAGES
from prompts import SYSTEM_PROMPTS
from utils.text_processing import extract_pronouns_and_references
from utils.llm_clients import gpt_4o_mini
from utils.token_counter import count_tokens
from utils.logger import logger


def rewrite_query(state: ChatState) -> ChatState:
    """쿼리 재작성 노드"""
    user_query = state.get("user_query", [])
    if not user_query:
        return {
            "error": "메시지가 없습니다",
            "processing_stage": PROCESSING_STAGES["VALIDATION_FAILED"]
        }
    logger.info(f"[Rewrite] 쿼리 재작성 시작: {user_query}")

    system_prompt = SystemMessage(content=SYSTEM_PROMPTS["rewrite_query"])
    user_message = HumanMessage(content=user_query)

    pronouns = extract_pronouns_and_references(user_query)
    if pronouns:
        # 대명사 있음 → 히스토리 포함
        existing_messages = state.get("messages", [])
        prompt = [system_prompt] + existing_messages
        logger.info(f"[Rewrite] 🔗 대명사 감지: {pronouns}")
        logger.debug(f"[Rewrite] 히스토리 포함 처리 ({len(existing_messages)} 메시지)")
    else:
        # 대명사 없음 → 현재 쿼리만
        prompt = [system_prompt, user_message]
        logger.info("[Rewrite] 📝 단순 쿼리 - 히스토리 제외 처리")

    # 토큰 수 로깅
    total_tokens = sum(count_tokens(getattr(msg, 'content', str(msg))) for msg in prompt)
    logger.debug(f"[Rewrite] 재작성 프롬프트 토큰 수: {total_tokens}")

    rewritten = gpt_4o_mini.invoke(prompt).content.strip()
    logger.info("[Rewrite] ✅ 쿼리 재작성 완료")
    logger.info(f"[Rewrite] 원본: {user_query}")
    logger.info(f"[Rewrite] 재작성: {rewritten}")

    rewritten_user_message = HumanMessage(content=rewritten)

    return {
        "messages": [rewritten_user_message],
        "processing_stage": PROCESSING_STAGES["REWRITTEN"]
    }
