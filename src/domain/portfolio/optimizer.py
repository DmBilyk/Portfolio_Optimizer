import numpy as np
from scipy.optimize import minimize

class MarkowitzOptimizer:
    def __init__(self, stock_symbols, returns_data, risk_level='Medium', investment_period=12):
        self.stock_symbols = stock_symbols
        self.returns_data = self.clean_returns_data(returns_data)
        self.risk_level = risk_level
        self.investment_period = investment_period
        self.risk_params = self.initialize_risk_params()
        self.adjust_for_investment_period()

    def clean_returns_data(self, returns_data):
        return returns_data.replace([np.inf, -np.inf], np.nan).dropna()

    def initialize_risk_params(self):
        return {
            'Low': {'max_weight': 0.15, 'min_stocks': 8, 'risk_aversion': 1.5, 'volatility_penalty': 1.5},
            'Medium': {'max_weight': 0.25, 'min_stocks': 5, 'risk_aversion': 1.0, 'volatility_penalty': 1.0},
            'High': {'max_weight': 0.35, 'min_stocks': 3, 'risk_aversion': 0.5, 'volatility_penalty': 0.5}
        }

    def adjust_for_investment_period(self):
        params = self.risk_params[self.risk_level]
        if self.investment_period > 36:
            params['risk_aversion'] *= 0.8
            params['volatility_penalty'] *= 0.8
        elif self.investment_period < 6:
            params['risk_aversion'] *= 1.5
            params['volatility_penalty'] *= 1.5
            params['max_weight'] *= 0.8
            params['min_stocks'] += 2

    def calculate_performance(self, weights):
        window = 24 if self.investment_period > 24 else 12
        cleaned_data = self.returns_data.rolling(window=window).mean().dropna()

        if cleaned_data.empty:
            return 0.0, np.nan

        mean_returns = cleaned_data.mean()
        cov_matrix = cleaned_data.cov()

        portfolio_return = np.dot(weights, mean_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        return portfolio_return, portfolio_volatility

    def optimize_portfolio(self):
        num_stocks = len(self.stock_symbols)
        initial_weights = np.ones(num_stocks) / num_stocks
        params = self.risk_params[self.risk_level]
        bounds = [(0.0, params['max_weight']) for _ in range(num_stocks)]
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
            {'type': 'ineq', 'fun': lambda w: np.sum(w > 0.01) - params['min_stocks']}
        ]

        def objective_function(weights):
            risk_free_rate = 0.02
            exp_return, exp_volatility = self.calculate_performance(weights)
            risk_adjustment = params['risk_aversion']
            volatility_penalty = exp_volatility * params['volatility_penalty']
            concentration_penalty = np.sum(weights ** 2) * 0.5
            if self.investment_period > 24:
                return -(exp_return - risk_free_rate - volatility_penalty * risk_adjustment * 0.8 - concentration_penalty)
            return -(exp_return - risk_free_rate - volatility_penalty * risk_adjustment - concentration_penalty)

        optimized = minimize(objective_function, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints)

        if optimized.success:
            optimal_weights = optimized.x
            exp_return, exp_volatility = self.calculate_performance(optimal_weights)
            sharpe_ratio = (exp_return - 0.02) / exp_volatility
            filtered_weights = {s: w for s, w in zip(self.stock_symbols, optimal_weights) if w > 0.01}
            return {
                'weights': filtered_weights,
                'expected_return': exp_return,
                'volatility': exp_volatility,
                'sharpe_ratio': sharpe_ratio,
                'risk_level': self.risk_level,
                'investment_period': self.investment_period
            }
        raise ValueError("Optimization failed.")
