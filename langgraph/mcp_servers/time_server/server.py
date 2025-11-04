from fastmcp import FastMCP
from datetime import datetime
import pytz

mcp = FastMCP("TimeServer")


@mcp.tool()
def get_current_time(timezone: str = "Asia/Seoul") -> dict:
    """
    현재 시간을 조회합니다.

    Args:
        timezone: 시간대 (기본값: Asia/Seoul)

    Returns:
        현재 시간 정보
    """
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)

    return {
        "success": True,
        "timezone": timezone,
        "datetime": now.strftime("%Y년 %m월 %d일 %H시 %M분 %S초"),
        "timestamp": int(now.timestamp())
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
