import yfinance as yf
from langchain_core.tools import tool


@tool
def get_stock_ticker_price(stockticker: str) -> str:
    """주식 가격을 조회합니다."""
    try:
        ticker = yf.Ticker(stockticker)
        todays_data = ticker.history(period="1d")
        if todays_data.empty:
            return f"{stockticker} 주식 정보를 찾을 수 없습니다."
        return f"{stockticker}: ${round(todays_data['Close'].iloc[0], 2)}"
    except Exception as e:
        return f"주식 정보 조회 중 오류가 발생했습니다: {str(e)}"
