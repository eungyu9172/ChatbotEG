import asyncio

from langchain_openai import ChatOpenAI

from config import GPT_4O_MINI_CONFIG, GPT_4O_CONFIG
from utils.logger import logger
from mcp_client.client_manager import get_mcp_manager


def _load_mcp_tools():
    """MCP 도구를 동기적으로 로드합니다."""
    try:
        # 이벤트 루프 가져오기 (또는 새로 생성)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # MCP Manager 초기화 및 도구 로드
        mcp_manager_coro = get_mcp_manager()
        mcp_manager = loop.run_until_complete(mcp_manager_coro)
        tools = mcp_manager.get_tools()

        logger.info(f"✅ MCP 도구 {len(tools)}개 로드됨")
        return tools

    except Exception as e:
        logger.error(f"❌ MCP 도구 로드 실패: {e}")
        logger.info("도구 없이 LLM을 사용합니다.")
        return []


AVAILABLE_TOOLS = _load_mcp_tools()

# LLM 클라이언트 초기화
gpt_4o_mini = ChatOpenAI(**GPT_4O_MINI_CONFIG)

gpt_4o = ChatOpenAI(**GPT_4O_CONFIG)

# GPT-4o + MCP 도구 바인딩
if AVAILABLE_TOOLS:
    gpt_4o_mini_with_tools = gpt_4o_mini.bind_tools(AVAILABLE_TOOLS)
    gpt_4o_with_tools = gpt_4o.bind_tools(AVAILABLE_TOOLS)
    logger.info(f"✅ Bind Tools: {len(AVAILABLE_TOOLS)}개 도구 바인딩됨")
else:
    gpt_4o_mini_with_tools = gpt_4o_mini
    gpt_4o_with_tools = gpt_4o
    logger.warning("⚠️  Bind Tools: 도구 없음")
