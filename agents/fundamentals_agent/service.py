from typing import Dict, Any, List
import sys
import os

# Make the shared library available for import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from libs.common.models import PlannerTask
from .client import YahooFinanceClient

# A mapping from natural language terms (from the LLM) to yfinance keys.
# This makes the system more robust to variations in the LLM's output.
METRIC_MAP = {
    "p/e ratio": "trailingPE",
    "pe ratio": "trailingPE",
    "price to earnings ratio": "trailingPE",
    "market cap": "marketCap",
    "market capitalization": "marketCap",
    "revenue": "totalRevenue",
    "total revenue": "totalRevenue",
    "revenue growth": "revenueGrowth",
    "eps": "trailingEps",
    "earnings per share": "trailingEps",
    "beta": "beta",
    "dividend yield": "dividendYield",
    "52 week high": "fiftyTwoWeekHigh",
    "52 week low": "fiftyTwoWeekLow",
}

class FundamentalsService:
    """
    This service handles the business logic for fetching fundamental stock data.
    """
    def __init__(self, client: YahooFinanceClient):
        self.client = client

    def _map_metrics(self, requested_metrics: list[str]) -> list[str]:
        """Translates natural language metric names to yfinance API keys."""
        mapped = []
        for metric in requested_metrics:
            mapped.append(METRIC_MAP.get(metric.lower(), metric))
        return mapped

    async def get_fundamental_data(self, task: PlannerTask) -> Dict[str, Any]:
        """
        Executes a fundamental data fetching task.

        Args:
            task: A Task object containing the instructions, including ticker and metrics.

        Returns:
            A dictionary containing the fetched financial data.
        """
        # A more robust solution would use an LLM or regex to extract entities
        # from the task.instructions. For now, we'll assume a simple structure.
        # Example: "Get P/E ratio and market cap for TSLA"
        words = task.instructions.replace(",", "").split()
        try:
            ticker = words[-1] # Assume last word is the ticker
        except IndexError:
            return {"error": "Could not parse ticker from instructions."}
        
        # This is a simplification. A real implementation would need more robust
        # parsing of the requested metrics from the instruction string.
        requested_metrics = [
            word for word in words 
            if word.lower() in METRIC_MAP or word in METRIC_MAP.values()
        ]

        if not requested_metrics:
            # If no specific metrics are asked for, return a default set.
            return await self.client.get_stock_info(ticker)
        
        # Translate natural language metrics to API-friendly keys
        yfinance_metrics = self._map_metrics(requested_metrics)
        
        return await self.client.get_specific_metrics(ticker, yfinance_metrics) 