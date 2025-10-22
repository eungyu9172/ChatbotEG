from langchain_core.messages import SystemMessage

from states import ChatState
from config import PROCESSING_STAGES
from prompts import SYSTEM_PROMPTS
from utils.llm_clients import gpt_4o
from utils.logger import logger


def force_final_answer(state: ChatState) -> ChatState:
    """Tool count 초과 시 강제로 최종 답변 생성"""
    messages = state.get("messages", [])
    user_query = state.get("user_query", "")

    logger.info(f"[Force Final Answer] Tool count 초과로 강제 답변 생성: {user_query}")

    # Tool 결과들을 포함한 메시지로 최종 답변 생성
    system_prompt = SystemMessage(content=SYSTEM_PROMPTS["force_final_answer"])
    prompt = [system_prompt] + messages
    response = gpt_4o.invoke(prompt)

    logger.info("[Force Final Answer] ✅ 강제 답변 생성 완료")

    return {
        "final_answer": response.content or "죄송합니다. 충분한 정보를 수집하지 못했습니다.",
        "messages": [response],
        "processing_stage": PROCESSING_STAGES["ANSWERED_WITH_CONTEXT"]
    }
