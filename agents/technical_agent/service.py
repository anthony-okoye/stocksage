from typing import Dict, Any
import pandas_ta as ta
import sys
import os

# Add project root for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from libs.common.models import Task
from .client import OHLVC_Client

class TechnicalAnalysisService:
    """
    This service handles the business logic for calculating technical indicators.
    """
    def __init__(self, client: OHLVC_Client):
        self.client = client

    def calculate_indicators(self, task: Task) -> Dict[str, Any]:
        """
        Executes a technical analysis task.

        Args:
            task: A Task object containing the ticker and indicators to calculate.

        Returns:
            A dictionary containing the calculated indicator values.
        """
        if "ticker" not in task.params:
            return {"error": "Ticker not specified in the task parameters."}
        
        ticker = task.params["ticker"]
        requested_indicators = task.params.get("metrics", [])
        
        if not requested_indicators:
            return {"error": "No technical indicators were requested."}
            
        # Fetch historical data
        history_df = self.client.get_daily_history(ticker)
        if history_df.empty:
            return {"error": f"Could not retrieve historical data for {ticker}."}

        results = {}
        for indicator in requested_indicators:
            indicator_lower = indicator.lower()
            try:
                # Use pandas_ta to calculate the indicator
                # Example: history_df.ta.rsi()
                if hasattr(history_df.ta, indicator_lower):
                    # Call the indicator function (e.g., history_df.ta.rsi())
                    history_df.ta(kind=indicator_lower, append=True)
                    
                    # The result is a new column in the DataFrame, e.g., 'RSI_14'.
                    # We find the column name and get the last value.
                    result_col_name = next(col for col in history_df.columns if col.startswith(indicator.upper()))
                    last_value = history_df[result_col_name].iloc[-1]
                    results[indicator.upper()] = round(last_value, 2)
                else:
                    results[indicator.upper()] = "Indicator not supported"
            except Exception as e:
                results[indicator.upper()] = f"Calculation error: {e}"
        
        return results 