import yfinance as yf
import pandas as pd

class OHLVC_Client:
    """
    A client to fetch historical OHLCV data from Yahoo Finance.
    """
    def get_daily_history(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """
        Retrieves daily historical market data for a given stock ticker.

        Args:
            ticker: The stock ticker symbol (e.g., "TSLA").
            period: The time period for the data (e.g., "1d", "5d", "1mo", "1y", "5y").

        Returns:
            A pandas DataFrame with the historical data, indexed by date.
            Returns an empty DataFrame if the ticker is not found or data is unavailable.
        """
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period=period)
            if history.empty:
                raise ValueError(f"No historical data found for ticker '{ticker}' for the period '{period}'.")
            return history
        except Exception as e:
            print(f"Error fetching historical data for ticker '{ticker}': {e}")
            return pd.DataFrame() # Return empty DataFrame on error 