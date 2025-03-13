import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed


class MarketData:
    @staticmethod
    def get_current_prices(symbols):
        """
        Fetches the current prices for a list of stock symbols.

        Parameters:
        symbols (list): A list of stock symbols.

        Returns:
        dict: A dictionary with stock symbols as keys and their current prices as values.
        """
        prices = {}

        def fetch_price(symbol):
            """
            Fetches the current price for a single stock symbol.

            Parameters:
            symbol (str): The stock symbol.

            Returns:
            tuple: A tuple containing the stock symbol and its current price.
            """
            try:
                stock = yf.Ticker(symbol)
                info = stock.info
                current_price = info.get('currentPrice')
                if current_price is None:
                    current_price = info.get('regularMarketPrice')
                return symbol, current_price
            except Exception as e:
                print(f"Error fetching price for {symbol}: {str(e)}")
                return symbol, None

        with ThreadPoolExecutor(max_workers=min(len(symbols), 10)) as executor:
            future_to_symbol = {executor.submit(fetch_price, symbol): symbol for symbol in symbols}

            for future in as_completed(future_to_symbol):
                symbol, price = future.result()
                if price is not None:
                    prices[symbol] = price

        return prices

    @staticmethod
    def get_stock_info(ticker):
        """
        Fetches detailed information for a given stock ticker.

        Parameters:
        ticker (str): The stock ticker symbol.

        Returns:
        dict: A dictionary containing detailed information about the stock.
        """
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "symbol": ticker,
            "name": info.get("longName"),
            "sector": info.get("sector"),
            "market_cap": info.get("marketCap"),
            "current_price": info.get("currentPrice"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "dividend_yield": info.get("dividendYield"),
        }

    @staticmethod
    def get_historical_data(ticker, start_date, end_date):
        """
        Fetches historical price data for a given stock ticker.

        Parameters:
        ticker (str): The stock ticker symbol.
        start_date (str): The start date for the historical data in YYYY-MM-DD format.
        end_date (str): The end date for the historical data in YYYY-MM-DD format.

        Returns:
        DataFrame: A pandas DataFrame containing the historical price data.
        """
        stock = yf.Ticker(ticker)
        historical_data = stock.history(start=start_date, end=end_date)
        return historical_data

    @staticmethod
    def get_market_summary():
        """
        Fetches the market summary for major indices.

        Returns:
        dict: A dictionary containing the market summary for major indices.
        """
        indices = ["^GSPC", "^DJI", "^IXIC"]
        summary = {}
        for index in indices:
            data = yf.Ticker(index)
            info = data.info
            summary[index] = {
                "name": info.get("shortName"),
                "current_price": info.get("regularMarketPrice"),
                "change": info.get("regularMarketChange"),
                "percent_change": info.get("regularMarketChangePercent"),
            }
        return summary

    @staticmethod
    def get_all_stock_symbols():
        """
        Returns a list of all stock symbols.

        Returns:
        list: A list of stock symbols.
        """
        return [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "KO", "JNJ",
            "META", "V", "PG", "UNH", "XOM", "CVX", "PFE",
            "HD", "DIS", "MA", "BAC", "MRK", "CSCO", "PEP", "LLY",
            "ABBV", "TMO", "NKE", "COST", "AVGO", "CRM", "ORCL",
            "ADBE", "INTC", "WMT", "QCOM", "VZ", "ABT", "TXN",
            "UPS", "NEE", "PM", "ACN", "DHR", "WFC", "MDT",
            "AMGN", "MS", "RTX", "IBM", "LIN", "HON", "BA",
            "SCHW", "AMAT", "LOW", "SPGI", "CAT", "COP", "NOW",
            "GS", "PLD", "BLK", "CCI", "LMT", "T", "MO", "BKNG"
        ]

    @staticmethod
    def get_historical_returns(tickers, start_date="2020-01-01", end_date="2023-01-01"):
        """
        Fetches historical returns for a list of stock tickers.

        Parameters:
        tickers (list): A list of stock ticker symbols.
        start_date (str): The start date for the historical data in YYYY-MM-DD format.
        end_date (str): The end date for the historical data in YYYY-MM-DD format.

        Returns:
        DataFrame: A pandas DataFrame containing the historical returns.
        """
        all_data = {}
        for ticker in tickers:
            data = MarketData.get_historical_data(ticker, start_date, end_date)
            all_data[ticker] = data['Close'].pct_change().dropna()

        return pd.DataFrame(all_data)