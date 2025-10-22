from langchain_core.tools import tool


@tool
def get_weather_info(location: str) -> str:
    """특정 장소의 날씨 정보를 가져옵니다."""
    mock_weather = {
        "서울": "맑음, 기온 22°C, 습도 45%",
        "부산": "구름 많음, 기온 25°C, 습도 60%"
    }
    weather = mock_weather.get(location, f"{location}의 날씨 정보를 찾을 수 없습니다.")
    return f"{location}의 현재 날씨: {weather}"
