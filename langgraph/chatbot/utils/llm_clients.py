from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from config import GPT_4O_MINI_CONFIG, GPT_4O_CONFIG
from tools import AVAILABLE_TOOLS

# LLM 클라이언트 초기화
gpt_4o_mini = ChatOpenAI(**GPT_4O_MINI_CONFIG)

gpt_4o = ChatOpenAI(**GPT_4O_CONFIG)

gpt_4o_with_tools = ChatOpenAI(**GPT_4O_CONFIG).bind_tools(AVAILABLE_TOOLS)

# ToolNode 초기화
tool_node = ToolNode(AVAILABLE_TOOLS)
