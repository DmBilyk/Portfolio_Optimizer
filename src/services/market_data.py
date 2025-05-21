import yfinance as yf
import pandas as pd
import os
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


class MarketDataCache:
    """
    Class for handling caching of market data.
    """

    def __init__(self, cache_dir="market_data_cache", cache_expiry_hours=24, max_filename_length=200):
        """
        Initialize the cache.

        Parameters:
        cache_dir (str): Directory to store cache files
        cache_expiry_hours (int): Number of hours after which cache is considered expired
        max_filename_length (int): Maximum length for cache filenames
        """
        self.cache_dir = cache_dir
        self.cache_expiry_hours = cache_expiry_hours
        self.max_filename_length = max_filename_length


        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def _get_cache_path(self, key, data_type):
        """Get the file path for a cache item"""

        if len(str(key)) > self.max_filename_length - len(data_type) - 10:

            hash_obj = hashlib.md5(str(key).encode())
            safe_key = hash_obj.hexdigest()
        else:

            safe_key = str(key).replace('/', '_').replace('\\', '_').replace(':', '_')

        return os.path.join(self.cache_dir, f"{safe_key}_{data_type}.cache")

    def get(self, key, data_type):
        """
        Get data from cache if available and not expired.

        Parameters:
        key (str): Unique identifier for the cached data
        data_type (str): Type of data (e.g., 'price', 'info', 'historical')

        Returns:
        data or None: The cached data if available, otherwise None
        """
        cache_path = self._get_cache_path(key, data_type)

        if not os.path.exists(cache_path):
            return None


        modified_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if datetime.now() - modified_time > timedelta(hours=self.cache_expiry_hours):
            return None

        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error reading cache for {key}: {str(e)}")
            return None

    def set(self, key, data_type, data):
        """
        Store data in cache.

        Parameters:
        key (str): Unique identifier for the cached data
        data_type (str): Type of data (e.g., 'price', 'info', 'historical')
        data: The data to cache
        """
        cache_path = self._get_cache_path(key, data_type)

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Error writing cache for {key}: {str(e)}")


class MarketData:

    _cache = MarketDataCache()

    @staticmethod
    def get_current_prices(symbols, use_cache=True):
        """
        Fetches the current prices for a list of stock symbols.

        Parameters:
        symbols (list): A list of stock symbols.
        use_cache (bool): Whether to use cached data if available.

        Returns:
        dict: A dictionary with stock symbols as keys and their current prices as values.
        """
        prices = {}


        if use_cache:
            for symbol in symbols:
                cached_price = MarketData._cache.get(symbol, 'current_price')
                if cached_price is not None:
                    prices[symbol] = cached_price


        symbols_to_fetch = [s for s in symbols if s not in prices]

        if not symbols_to_fetch:
            return prices

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

                # Cache the result
                if current_price is not None and use_cache:
                    MarketData._cache.set(symbol, 'current_price', current_price)

                return symbol, current_price
            except Exception as e:
                print(f"Error fetching price for {symbol}: {str(e)}")
                return symbol, None

        with ThreadPoolExecutor(max_workers=min(len(symbols_to_fetch), 10)) as executor:
            future_to_symbol = {executor.submit(fetch_price, symbol): symbol for symbol in symbols_to_fetch}

            for future in as_completed(future_to_symbol):
                symbol, price = future.result()
                if price is not None:
                    prices[symbol] = price

        return prices

    @staticmethod
    def get_stock_info(ticker, use_cache=True):
        """
        Fetches detailed information for a given stock ticker.

        Parameters:
        ticker (str): The stock ticker symbol.
        use_cache (bool): Whether to use cached data if available.

        Returns:
        dict: A dictionary containing detailed information about the stock.
        """

        if use_cache:
            cached_info = MarketData._cache.get(ticker, 'stock_info')
            if cached_info is not None:
                return cached_info


        stock = yf.Ticker(ticker)
        info = stock.info
        stock_info = {
            "symbol": ticker,
            "name": info.get("longName"),
            "sector": info.get("sector"),
            "market_cap": info.get("marketCap"),
            "current_price": info.get("currentPrice"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "dividend_yield": info.get("dividendYield"),
        }


        if use_cache:
            MarketData._cache.set(ticker, 'stock_info', stock_info)

        return stock_info

    @staticmethod
    def get_historical_data(ticker, start_date, end_date, use_cache=True):
        """
        Fetches historical price data for a given stock ticker.

        Parameters:
        ticker (str): The stock ticker symbol.
        start_date (str): The start date for the historical data in YYYY-MM-DD format.
        end_date (str): The end date for the historical data in YYYY-MM-DD format.
        use_cache (bool): Whether to use cached data if available.

        Returns:
        DataFrame: A pandas DataFrame containing the historical price data.
        """

        cache_key = f"{ticker}_{start_date}_{end_date}"


        if use_cache:
            cached_data = MarketData._cache.get(cache_key, 'historical_data')
            if cached_data is not None:
                return cached_data


        stock = yf.Ticker(ticker)
        historical_data = stock.history(start=start_date, end=end_date)


        if use_cache:
            MarketData._cache.set(cache_key, 'historical_data', historical_data)

        return historical_data

    @staticmethod
    def get_market_summary(use_cache=True):
        """
        Fetches the market summary for major indices.

        Parameters:
        use_cache (bool): Whether to use cached data if available.

        Returns:
        dict: A dictionary containing the market summary for major indices.
        """

        if use_cache:
            cached_summary = MarketData._cache.get('market_summary', 'summary')
            if cached_summary is not None:
                return cached_summary

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


        if use_cache:
            MarketData._cache.set('market_summary', 'summary', summary)

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
    def get_historical_returns(tickers, start_date="2020-01-01", end_date="2023-01-01", use_cache=True):
        """
        Fetches historical returns for a list of stock tickers.

        Parameters:
        tickers (list): A list of stock ticker symbols.
        start_date (str): The start date for the historical data in YYYY-MM-DD format.
        end_date (str): The end date for the historical data in YYYY-MM-DD format.
        use_cache (bool): Whether to use cached data if available.

        Returns:
        DataFrame: A pandas DataFrame containing the historical returns.
        """

        if len(tickers) > 10:
            tickers_str = "_".join(sorted(tickers))
            tickers_hash = hashlib.md5(tickers_str.encode()).hexdigest()
            cache_key = f"returns_hash_{tickers_hash}_{start_date}_{end_date}"
        else:
            cache_key = f"returns_{'_'.join(sorted(tickers))}_{start_date}_{end_date}"


        if use_cache:
            cached_returns = MarketData._cache.get(cache_key, 'historical_returns')
            if cached_returns is not None:
                return cached_returns

        all_data = {}
        for ticker in tickers:
            data = MarketData.get_historical_data(ticker, start_date, end_date, use_cache)
            all_data[ticker] = data['Close'].pct_change().dropna()

        returns_df = pd.DataFrame(all_data)


        if use_cache:
            MarketData._cache.set(cache_key, 'historical_returns', returns_df)

        return returns_df

    @staticmethod
    def clear_cache():
        """
        Clears all cached data.
        """
        cache_dir = MarketData._cache.cache_dir
        for file in os.listdir(cache_dir):
            os.remove(os.path.join(cache_dir, file))
        print(f"Cache cleared from {cache_dir}")