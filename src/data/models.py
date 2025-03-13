class Portfolio:
    """
    A class to represent a portfolio.

    Attributes:
    name (str): The name of the portfolio.
    """

    def __init__(self, name):
        """
        Constructs all the necessary attributes for the Portfolio object.

        Parameters:
        name (str): The name of the portfolio.
        """
        self.name = name


class Stock:
    """
    A class to represent a stock.

    Attributes:
    symbol (str): The stock symbol.
    quantity (int): The quantity of the stock.
    price (float): The price of the stock.
    """

    def __init__(self, symbol, quantity, price):
        """
        Constructs all the necessary attributes for the Stock object.

        Parameters:
        symbol (str): The stock symbol.
        quantity (int): The quantity of the stock.
        price (float): The price of the stock.
        """
        self.symbol = symbol
        self.quantity = quantity
        self.price = price


class StockMetrics:
    """
    A class to represent stock metrics.

    Attributes:
    symbol (str): The stock symbol.
    mean_return (float): The mean return of the stock.
    volatility (float): The volatility of the stock.
    calculation_date (str): The date of the calculation.
    window_size (int): The window size for the calculation.
    """

    def __init__(self, symbol, mean_return, volatility, calculation_date, window_size):
        """
        Constructs all the necessary attributes for the StockMetrics object.

        Parameters:
        symbol (str): The stock symbol.
        mean_return (float): The mean return of the stock.
        volatility (float): The volatility of the stock.
        calculation_date (str): The date of the calculation.
        window_size (int): The window size for the calculation.
        """
        self.symbol = symbol
        self.mean_return = mean_return
        self.volatility = volatility
        self.calculation_date = calculation_date
        self.window_size = window_size


class OptimizedPortfolio:
    """
    A class to represent an optimized portfolio.

    Attributes:
    risk_level (str): The risk level of the portfolio.
    investment_period (int): The investment period of the portfolio.
    expected_return (float): The expected return of the portfolio.
    volatility (float): The volatility of the portfolio.
    sharpe_ratio (float): The Sharpe ratio of the portfolio.
    """

    def __init__(self, risk_level, investment_period, expected_return, volatility, sharpe_ratio):
        """
        Constructs all the necessary attributes for the OptimizedPortfolio object.

        Parameters:
        risk_level (str): The risk level of the portfolio.
        investment_period (int): The investment period of the portfolio.
        expected_return (float): The expected return of the portfolio.
        volatility (float): The volatility of the portfolio.
        sharpe_ratio (float): The Sharpe ratio of the portfolio.
        """
        self.risk_level = risk_level
        self.investment_period = investment_period
        self.expected_return = expected_return
        self.volatility = volatility
        self.sharpe_ratio = sharpe_ratio