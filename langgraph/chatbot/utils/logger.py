import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from config import LOGGING_CONFIG


class SessionLogger:
    """세션별 로그 파일 관리"""

    def __init__(self):
        self.log_dir = Path(LOGGING_CONFIG["log_directory"])
        self.log_dir.mkdir(exist_ok=True)
        self.session_id = None
        self.log_filepath = None
        self.file_handler = None
        self.logger = None

    def start_session(self):
        """새 세션 시작 - 로그 파일 생성"""
        if not LOGGING_CONFIG.get("log_to_file", False):
            return

        # 세션 ID 생성 (타임스탬프 기반)
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"chatbot_session_{self.session_id}.txt"
        self.log_filepath = self.log_dir / log_filename

        # 파일 핸들러 생성
        self.file_handler = logging.FileHandler(self.log_filepath, encoding='utf-8')
        self.file_handler.setLevel(logging.DEBUG)  # DEBUG 레벨까지 기록

        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.file_handler.setFormatter(formatter)

        # 로거에 핸들러 추가
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(self.file_handler)

        # 세션 시작 로그
        self.logger.info("=== 챗봇 세션 시작 ===")
        self.logger.info(f"세션 ID: {self.session_id}")
        self.logger.info(f"로그 파일: {self.log_filepath}")

    def end_session(self):
        """세션 종료 - 로그 파일 완료"""
        if self.file_handler and self.logger:
            self.logger.info("=== 챗봇 세션 종료 ===")
            self.logger.info(f"세션 ID: {self.session_id}")
            self.logger.info(f"로그 파일 완료: {self.log_filepath}")

            # 핸들러 제거 및 파일 닫기
            self.logger.removeHandler(self.file_handler)
            self.file_handler.close()

            print(f"📝 세션 로그 저장 완료: {self.log_filepath}")


# 전역 세션 로거 인스턴스
session_logger = SessionLogger()


def setup_logger():
    """로거 설정"""
    level = getattr(logging, LOGGING_CONFIG["log_level"])

    # 로거 생성
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    # 기존 핸들러 제거 (중복 방지)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 콘솔 핸들러 (항상 추가)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def format_value(value: Any, max_len: int = 30) -> str:
    """
    값을 간결하게 포맷팅 (길이만 제한)

    Args:
        value: 포맷팅할 값
        max_len: 최대 길이

    Returns:
        포맷팅된 문자열
    """
    if isinstance(value, str):
        if len(value) > max_len:
            return f'"{value[:max_len]}..."'
        return f'"{value}"'
    elif isinstance(value, list):
        return f"[{len(value)} items]"
    elif isinstance(value, dict):
        return f"{{{len(value)} keys}}"
    elif isinstance(value, bool):
        return str(value)
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        s = str(value)
        if len(s) > max_len:
            return s[:max_len] + "..."
        return s


def summarize_tool_result(result: Dict[str, Any]) -> str:
    """
    Tool 결과를 요약 (모든 필드 표시, 값만 짧게)

    Args:
        result: Tool 결과 딕셔너리

    Returns:
        요약 문자열
    """
    # success 필드 확인
    success = result.get("success")
    if success is True:
        status = "✅"
    elif success is False:
        status = "❌"
        error = result.get("error", "")
        if error:
            error_short = error[:70] + "..." if len(error) > 70 else error
            return f"{status} 실패: {error_short}"
        return f"{status} 실패"
    else:
        status = "📋"

    # 모든 결과 필드 표시 (success, error, tool_name 제외)
    result_keys = [k for k in result.keys()
                   if k not in ['success', 'error', 'tool_name'] and not k.startswith('_')]

    if not result_keys:
        return f"{status} 완료"

    # 모든 필드를 표시 (값만 짧게)
    parts = []
    for key in result_keys:
        value = result[key]
        formatted_value = format_value(value, max_len=40)
        parts.append(f"{key}={formatted_value}")

    summary = ", ".join(parts)
    return f"{status} {summary}"


def format_messages_for_log(messages: List) -> str:
    """
    메시지 리스트를 읽기 쉬운 형태로 포맷팅

    Args:
        messages: LangChain 메시지 리스트

    Returns:
        포맷팅된 문자열
    """
    if not messages:
        return "빈 메시지 리스트"

    lines = [f"\n{'='*80}"]
    lines.append(f"📨 메시지 ({len(messages)}개)")
    lines.append(f"{'='*80}")

    for idx, msg in enumerate(messages, 1):
        # HumanMessage
        if isinstance(msg, HumanMessage):
            content = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
            lines.append(f"[{idx}] 🧑 Human: {content}")

        # AIMessage
        elif isinstance(msg, AIMessage):
            # Tool calls가 있는 경우
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                lines.append(f"[{idx}] 🤖 AI: 🔧 {len(msg.tool_calls)}개 도구 호출")

                for i, tc in enumerate(msg.tool_calls, 1):
                    tool_name = tc.get('name', 'unknown')
                    tool_args = tc.get('args', {})

                    # ✅ 모든 인자 표시 (값만 짧게)
                    arg_parts = []
                    for k, v in tool_args.items():
                        arg_parts.append(f"{k}={format_value(v, 35)}")

                    args_str = ", ".join(arg_parts)
                    lines.append(f"    └─ [{i}] {tool_name}({args_str})")

            # 일반 응답
            else:
                if msg.content:
                    content = msg.content[:120] + "..." if len(msg.content) > 120 else msg.content
                    lines.append(f"[{idx}] 🤖 AI: {content}")
                else:
                    lines.append(f"[{idx}] 🤖 AI: (빈 응답)")

        # ToolMessage
        elif isinstance(msg, ToolMessage):
            tool_name = getattr(msg, 'name', 'unknown')

            # JSON 파싱 시도
            try:
                result = json.loads(msg.content)
                if isinstance(result, dict):
                    # ✅ 모든 필드 표시 (값만 짧게)
                    summary = summarize_tool_result(result)
                    lines.append(f"[{idx}] 🔨 Tool [{tool_name}]: {summary}")
                else:
                    content = str(result)[:100] + "..."
                    lines.append(f"[{idx}] 🔨 Tool [{tool_name}]: {content}")
            except (json.JSONDecodeError, Exception):
                # JSON이 아닌 경우
                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                lines.append(f"[{idx}] 🔨 Tool [{tool_name}]: {content}")

        # SystemMessage
        elif isinstance(msg, SystemMessage):
            first_line = msg.content.split('\n')[0]
            preview = first_line[:70] + "..." if len(first_line) > 70 else first_line
            lines.append(f"[{idx}] ⚙️ System: {preview}")

        # 기타
        else:
            lines.append(f"[{idx}] ❓ {type(msg).__name__}")

        # 구분선 (마지막 메시지 제외)
        if idx < len(messages):
            lines.append("    │")

    lines.append(f"{'='*80}\n")
    return "\n".join(lines)


logger = setup_logger()
