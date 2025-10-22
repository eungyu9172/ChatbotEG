from datetime import datetime

from langchain_core.tools import tool


@tool
def get_current_time():
    """현재 시간을 가져옵니다."""
    now = datetime.now()
    return f"현재 시간은 {now.strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}입니다."
