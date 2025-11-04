from states import ChatState
from config import PROCESSING_LIMITS, PROCESSING_STAGES
from utils.token_counter import count_tokens
from utils.logger import logger


def validate_input(state: ChatState) -> ChatState:
    """입력 검증 노드"""
    user_query = state.get("user_query", "")

    logger.info(f"[Validate] Input query: {user_query[:50]}..." if len(user_query) > 50 else f"[Validate] Input query: {user_query}")

    if not user_query:
        logger.error("[Validate] ❌ Empty query provided")
        return {
            "error": "입력 데이터가 비어있습니다",
            "processing_stage": PROCESSING_STAGES["VALIDATION_FAILED"]
        }

    token_count = count_tokens(user_query)
    max_tokens = PROCESSING_LIMITS["max_input_tokens"]

    logger.debug(f"[Validate] 토큰 수 계산: {token_count}/{max_tokens}")

    if token_count > max_tokens:
        logger.error(f"[Validate] ❌ Query too long: {len(user_query)} tokens")
        return {
            "error": f"입력 데이터가 너무 깁니다 (토큰: {token_count}/{max_tokens})",
            "processing_stage": PROCESSING_STAGES["VALIDATION_FAILED"]
        }

    logger.info(f"[Validate] ✅ Input validated: {user_query[:50]}...")

    return {
        "processing_stage": PROCESSING_STAGES["VALIDATED"]
    }
