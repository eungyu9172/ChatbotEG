from fastmcp import FastMCP
import yfinance as yf

mcp = FastMCP("FinanceServer")


@mcp.tool()
async def get_stock_price(ticker: str) -> dict:
    """
    주식 가격을 조회합니다.

    Args:
        ticker: 주식 티커 심볼 (예: AAPL, TSLA)

    Returns:
        주식 가격 정보
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "success": True,
            "ticker": ticker,
            "price": info.get("currentPrice", "N/A"),
            "currency": info.get("currency", "USD"),
            "company_name": info.get("longName", ticker)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ticker": ticker
        }

if __name__ == "__main__":
    mcp.run(transport="stdio")
