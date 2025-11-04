import os
from dotenv import load_dotenv


# 환경 변수
load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# 모델 설정
GPT_4O_MINI_CONFIG = {
    "model": "gpt-4o-mini",
    "temperature": 0.1,
}

GPT_4O_CONFIG = {
    "model": "gpt-4o",
    "temperature": 0.1,
}

# 모델별 토큰 제한
MODEL_TOKEN_LIMITS = {
    "gpt-4o-mini": 128000,
    "gpt-4o": 128000,
}

# Processing Limits
PROCESSING_LIMITS = {
    "max_input_tokens": 2000,
    "max_context_docs": 5,
    "max_reranked_docs": 3,
    "max_conversation_history": 10,
}

# Processing Stages
PROCESSING_STAGES = {
    "VALIDATION_FAILED": "validation_failed",
    "VALIDATED": "validated",
    "CHECKED_SIMPLE": "checked_simple",
    "ANSWERED_DIRECT": "answered_direct",
    "REWRITTEN": "rewritten",
    "RETRIEVED": "retrieved",
    "RERANKED": "reranked",
    "CHECKED_ANSWERABILITY": "checked_answerability",
    "ANSWERED": "answered",
    "ASKED_FOR_MORE_INFO": "asked_for_more_info",
    "TOOL_ASSISTED_GENERATE": "tool_asisted_generate",
    "TOOL_ASSISTED_DIRECT_ANSWER": "tool_assisted_direct_answer",
    "FORCE_ANSWERED": "force_answered"
}

# 로깅 설정
LOGGING_CONFIG = {
    "debug_mode": DEBUG_MODE,
    "log_to_file": DEBUG_MODE,
    "log_directory": "logs",
    "log_level": "DEBUG" if DEBUG_MODE else "INFO"
}

# ==================== RAG 설정 ====================
# ChromaDB 설정
CHROMA_CONFIG = {
    "persist_dir": "../.chroma",
    "collection_name": "innorules",
}

# Retrieve 설정
RETRIEVE_CONFIG = {
    "top_k": 10,
}

# Rerank 설정
RERANK_CONFIG = {
    "model_name": "BAAI/bge-reranker-v2-m3",
    "device": "cpu",
    "top_k": 5,
    "use_fp16": True
}
