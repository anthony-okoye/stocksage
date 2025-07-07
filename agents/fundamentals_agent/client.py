import yfinance as yf
from typing import Dict, Any, List
import asyncio

class YahooFinanceClient:
    """
    A client to fetch financial data from Yahoo Finance.
    Calls are wrapped in asyncio.to_thread to avoid blocking the event loop.
    """
    async def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """
        Retrieves comprehensive information for a given stock ticker.

        Args:
            ticker: The stock ticker symbol (e.g., "TSLA").

        Returns:
            A dictionary containing the stock's information.
            Returns an empty dictionary if the ticker is not found.
        """
        def _fetch():
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                if not info or info.get('regularMarketPrice') is None:
                    raise ValueError(f"Ticker '{ticker}' not found or has no data.")
                return info
            except Exception as e:
                print(f"Error fetching data for ticker '{ticker}' from yfinance: {e}")
                return {"error": str(e)}
        
        return await asyncio.to_thread(_fetch)

    async def get_specific_metrics(self, ticker: str, metrics: List[str]) -> Dict[str, Any]:
        """
        Retrieves only specific metrics for a stock. This is more efficient
        if only a few data points are needed.

        Args:
            ticker: The stock ticker symbol.
            metrics: A list of desired metrics in camelCase format (e.g., 'marketCap').

        Returns:
            A dictionary containing the requested metrics and their values.
        """
        info = await self.get_stock_info(ticker)
        if "error" in info:
            return info

        result = {}
        for metric in metrics:
            result[metric] = info.get(metric, "N/A")
        
        return result 