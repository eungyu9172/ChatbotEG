from langchain_core.messages import SystemMessage, HumanMessage

from states import ChatState
from config import PROCESSING_STAGES
from prompts import SYSTEM_PROMPTS
from utils.llm_clients import gpt_4o_with_tools
from utils.token_counter import count_tokens
from utils.logger import logger, format_messages_for_log  


def generate_answer(state: ChatState) -> ChatState:
    reranked_context = state.get("reranked_context") or []
    if not isinstance(reranked_context, list):
        reranked_context = []
    contexts = "\n".join(reranked_context)

    messages = state.get("messages", [])

    logger.debug(f"[Generate] messages: {format_messages_for_log(messages)}")

    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_message = msg
            break

    logger.info(f"[Generate] 최종 답변 생성 시도: {user_message.content}")
    logger.debug(f"[Generate] 컨텍스트: {len(contexts)}개, 메시지 히스토리: {len(messages)}개")

    context_text = "\n".join(contexts)

    # ✅ State 정보를 포함한 동적 프롬프트 생성
    retrieve_results = state.get("retrieve_results") or []
    is_reranked = state.get("is_reranked", True)

    state_info = f"""
## 현재 상태 정보
- 검색 결과 존재: {"예 (" + str(len(retrieve_results)) + "개 문서)" if retrieve_results else "아니오"}
- Rerank 완료 여부: {"예" if is_reranked else "아니오"}

## 도구 사용 가이드
1. **retrieve_documents 사용 시점**:
   - 사용자 질문이 특정 컬렉션(innorules, technical_docs 등)의 정보를 요구할 때
   - 아직 검색을 수행하지 않았을 때

2. **rerank_documents 사용 시점 (우선순위)**:
   - 검색 결과가 존재하고 ({len(retrieve_results)}개 문서)
   - Rerank가 아직 수행되지 않았을 때 (현재: {"완료" if is_reranked else "미완료"})
   - ⚠️ 이 조건이 충족되면 **반드시 먼저 rerank_documents를 호출**하세요

3. **답변 생성 시점**:
   - Rerank가 완료되어 정제된 문서가 있을 때
   - 또는 도구 없이 답변 가능한 간단한 질문일 때
"""

    system_prompt_with_context = SystemMessage(content=f"""
{SYSTEM_PROMPTS["generate_answer"]}

{state_info}

참고 컨텍스트:
{context_text if context_text else "(검색된 컨텍스트 없음)"}
""")
    prompt = [system_prompt_with_context] + messages

    # 토큰 수 로깅
    context_tokens = count_tokens(context_text)
    total_prompt_tokens = sum(count_tokens(getattr(msg, 'content', str(msg))) for msg in prompt)
    logger.debug(f"[Generate] 컨텍스트 토큰: {context_tokens}")
    logger.debug(f"[Generate] 전체 프롬프트 토큰: {total_prompt_tokens}")

    response = gpt_4o_with_tools.invoke(prompt)

    # Tool 호출 확인
    tool_calls = getattr(response, 'tool_calls', None)
    if tool_calls:
        logger.info(f"[Generate] 🔧 도구 호출 요청됨: {len(tool_calls)}개")
        for i, tool_call in enumerate(tool_calls):
            tool_name = tool_call.get('name', 'unknown')
            tool_args = tool_call.get('args', {})
            logger.debug(f"[Generate] 도구 {i+1}: {tool_name}({tool_args})")
        logger.info(f"[Generate] Response: {format_messages_for_log([response])}")
        return {
            "messages": [response],
            "tool_call_count": state.get("tool_call_count", 0) + 1,
            "processing_stage": PROCESSING_STAGES["TOOL_ASSISTED_GENERATE"]
        }
    else:
        response_tokens = count_tokens(response.content) if response.content else 0
        logger.info("[Generate] ✅ 최종 답변 생성 완료")
        logger.debug(f"[Generate] 답변 길이: {len(response.content)}자 ({response_tokens} 토큰)")
        logger.info(f"[Generate] Response: {format_messages_for_log([response])}")
        return {
            "final_answer": response.content or "",
            "messages": [response],
            "processing_stage": PROCESSING_STAGES["ANSWERED"]
        }
