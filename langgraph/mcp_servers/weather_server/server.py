from fastmcp import FastMCP
import httpx


mcp = FastMCP("WeatherServer")

API_BASE = "https://api.open-meteo.com/v1"


@mcp.tool()
async def get_current_weather(
    city: str,
    country: str = "KR"
) -> dict:
    """
    도시의 현재 날씨를 조회합니다.

    Args:
        city: 도시 이름 (예: Seoul, Busan, Incheon)
        country: 국가 코드 (기본값: KR)

    Returns:
        현재 날씨 정보
    """
    try:
        # 1단계: 도시명으로 좌표 찾기 (Geocoding)
        geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        async with httpx.AsyncClient() as client:
            geo_response = await client.get(
                geocoding_url,
                params={
                    "name": city,
                    "count": 1,
                    "language": "ko",
                    "format": "json"
                },
                timeout=10.0
            )
            geo_response.raise_for_status()
            geo_data = geo_response.json()

        if not geo_data.get("results"):
            return {
                "success": False,
                "error": f"'{city}' 도시를 찾을 수 없습니다.",
                "city": city
            }

        # 좌표 추출
        location = geo_data["results"][0]
        latitude = location["latitude"]
        longitude = location["longitude"]
        city_name = location["name"]

        # 2단계: 좌표로 날씨 정보 가져오기
        weather_url = f"{API_BASE}/forecast"
        async with httpx.AsyncClient() as client:
            weather_response = await client.get(
                weather_url,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current_weather": "true",
                    "timezone": "Asia/Seoul"
                },
                timeout=10.0
            )
            weather_response.raise_for_status()
            weather_data = weather_response.json()

        current = weather_data["current_weather"]

        # 날씨 코드 해석
        weather_codes = {
            0: "맑음",
            1: "대체로 맑음",
            2: "부분적으로 흐림",
            3: "흐림",
            45: "안개",
            48: "서리 안개",
            51: "이슬비",
            61: "약한 비",
            63: "비",
            65: "강한 비",
            71: "약한 눈",
            73: "눈",
            75: "강한 눈",
            95: "뇌우"
        }

        weather_description = weather_codes.get(
            current["weathercode"],
            "알 수 없음"
        )

        return {
            "success": True,
            "city": city_name,
            "latitude": latitude,
            "longitude": longitude,
            "temperature": current["temperature"],
            "temperature_unit": "°C",
            "wind_speed": current["windspeed"],
            "wind_speed_unit": "km/h",
            "wind_direction": current["winddirection"],
            "weather": weather_description,
            "weather_code": current["weathercode"],
            "time": current["time"]
        }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "날씨 API 응답 시간 초과",
            "city": city
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "city": city
        }


@mcp.resource("weather://supported-cities")
def get_supported_cities() -> dict:
    """지원하는 주요 도시 목록을 제공합니다."""
    return {
        "korea": [
            "Seoul", "Busan", "Incheon", "Daegu", "Daejeon",
            "Gwangju", "Ulsan", "Suwon", "Changwon", "Seongnam"
        ],
        "international": [
            "Tokyo", "Beijing", "Shanghai", "New York",
            "London", "Paris", "Sydney", "Los Angeles"
        ]
    }


if __name__ == "__main__":
    # stdio 전송으로 서버 실행
    mcp.run(transport="stdio")
