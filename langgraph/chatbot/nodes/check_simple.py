from langchain_core.messages import SystemMessage

from states import ChatState
from config import PROCESSING_STAGES
from prompts import SYSTEM_PROMPTS
from utils.llm_clients import gpt_4o_mini
from utils.logger import logger


def check_simple_query(state: ChatState) -> ChatState:
    """단순 쿼리 검사"""
    messages = state.get("messages", [])
    user_message = messages[-1]

    logger.info(f"[Check Simple] user_message(rewritten): {user_message.content}")
    system_prompt = SystemMessage(content=SYSTEM_PROMPTS["check_simple"])
    prompt = [system_prompt, user_message]

    result = gpt_4o_mini.invoke(prompt).content.strip()
    is_simple_query = result.upper().startswith("YES")

    logger.info(f"[Check Simple] LLM simple query check: {is_simple_query}")

    return {
        "is_simple_query": is_simple_query,
        "processing_stage": PROCESSING_STAGES["CHECKED_SIMPLE"]
    }
