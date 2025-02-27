class Portfolio:
    def __init__(self, name):
        self.name = name


class Stock:
    def __init__(self, symbol, quantity, price):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price

class StockMetrics:
    def __init__(self, symbol, mean_return, volatility, calculation_date, window_size):
        self.symbol = symbol
        self.mean_return = mean_return
        self.volatility = volatility
        self.calculation_date = calculation_date
        self.window_size = window_size

class OptimizedPortfolio:
    def __init__(self, risk_level, investment_period, expected_return, volatility, sharpe_ratio):
        self.risk_level = risk_level
        self.investment_period = investment_period
        self.expected_return = expected_return
        self.volatility = volatility
        self.sharpe_ratio = sharpe_ratio