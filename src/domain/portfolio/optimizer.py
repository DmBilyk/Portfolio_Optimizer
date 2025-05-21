import numpy as np
from scipy.optimize import minimize
import cvxpy as cp
from abc import ABC, abstractmethod


class OptimizationStrategy(ABC):
    """
    Abstract base class for optimization strategies.
    """

    @abstractmethod
    def optimize(self, stock_symbols, returns_data, risk_params, calculate_performance):
        """
        Abstract method to optimize a portfolio.

        Args:
            stock_symbols (list): List of stock symbols.
            returns_data (pd.DataFrame): Historical returns data for the stocks.
            risk_params (dict): Risk parameters for the optimization.
            calculate_performance (callable): Function to calculate portfolio performance.

        Returns:
            dict: Optimization results.
        """
        pass


class CVXPYOptimizationStrategy(OptimizationStrategy):
    """
    Concrete implementation of the OptimizationStrategy using CVXPY.
    """

    def optimize(self, stock_symbols, returns_data, risk_params, calculate_performance):
        """
        Optimize the portfolio using CVXPY.

        Args:
            stock_symbols (list): List of stock symbols.
            returns_data (pd.DataFrame): Historical returns data for the stocks.
            risk_params (dict): Risk parameters for the optimization.
            calculate_performance (callable): Function to calculate portfolio performance.

        Returns:
            dict: Optimization results including weights, expected return, volatility, and Sharpe ratio.
        """
        num_stocks = len(stock_symbols)

        # Calculate exponentially weighted mean returns and covariance matrix
        ewm_returns = returns_data.ewm(alpha=0.3).mean().iloc[-1].values
        sample_cov = returns_data.cov().values
        shrinkage = 0.2
        target = np.diag(np.diag(sample_cov))
        cov_matrix = (1 - shrinkage) * sample_cov + shrinkage * target

        # Define optimization variables and constraints
        w = cp.Variable(num_stocks)
        risk_free_rate = 0.02
        constraints = [
            cp.sum(w) == 1,  # Weights must sum to 1
            w >= 0,  # No short selling
            w <= risk_params['max_weight']  # Maximum weight constraint
        ]

        # Define the objective function
        risk = cp.quad_form(w, cov_matrix)
        annualized_return = 12 * (ewm_returns @ w)
        objective = cp.Maximize(annualized_return - risk_params['risk_aversion'] * risk)

        # Solve the optimization problem
        prob = cp.Problem(objective, constraints)
        try:
            prob.solve(solver=cp.ECOS)

            if prob.status == "optimal" or prob.status == "optimal_inaccurate":
                optimal_weights = w.value

                # Calculate performance metrics
                exp_return, exp_volatility = calculate_performance(optimal_weights)
                sharpe_ratio = (exp_return - risk_free_rate) / exp_volatility if exp_volatility > 0 else 0

                # Filter and normalize weights
                filtered_weights = {s: round(w, 4) for s, w in zip(stock_symbols, optimal_weights) if w > 0.005}
                total_weight = sum(filtered_weights.values())
                if total_weight < 0.999:
                    filtered_weights = {s: round(w / total_weight, 4) for s, w in filtered_weights.items()}

                return {
                    'weights': filtered_weights,
                    'expected_return': round(exp_return, 2),
                    'volatility': round(exp_volatility, 2),
                    'sharpe_ratio': round(sharpe_ratio, 2),
                    'success': True
                }
            else:
                return {'success': False}

        except Exception as e:
            return {'success': False, 'error': str(e)}


class SciPyOptimizationStrategy(OptimizationStrategy):
    """
    Concrete implementation of the OptimizationStrategy using SciPy.
    """

    def optimize(self, stock_symbols, returns_data, risk_params, calculate_performance):
        """
        Optimize the portfolio using SciPy.

        Args:
            stock_symbols (list): List of stock symbols.
            returns_data (pd.DataFrame): Historical returns data for the stocks.
            risk_params (dict): Risk parameters for the optimization.
            calculate_performance (callable): Function to calculate portfolio performance.

        Returns:
            dict: Optimization results including weights, expected return, volatility, and Sharpe ratio.
        """
        num_stocks = len(stock_symbols)
        initial_weights = np.ones(num_stocks) / num_stocks
        bounds = [(0.0, risk_params['max_weight']) for _ in range(num_stocks)]
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]

        def objective_function(weights):
            """
            Objective function for the optimization.

            Args:
                weights (np.ndarray): Portfolio weights.

            Returns:
                float: Negative utility value to minimize.
            """
            risk_free_rate = 0.02
            exp_return, exp_volatility = calculate_performance(weights)

            # Calculate diversity and Sortino penalties
            active_stocks = np.sum(weights > 0.01)
            diversity_penalty = max(0, risk_params['min_stocks'] - active_stocks) * 0.1
            downside_returns = np.minimum(0, returns_data - risk_free_rate / 12)
            downside_risk = np.sqrt(
                np.dot(weights.T, np.dot(downside_returns.T @ downside_returns / len(downside_returns), weights)))
            downside_risk = downside_risk * np.sqrt(12)
            sortino_penalty = 0 if downside_risk == 0 else 0.2 / (exp_return / downside_risk)

            # Calculate utility
            utility = exp_return - risk_params['risk_aversion'] * (exp_volatility ** 2) - diversity_penalty - sortino_penalty
            return -utility

        # Perform optimization with multiple initializations
        best_result = None
        best_utility = -np.inf
        for _ in range(3):
            if _ > 0:
                random_weights = np.random.random(num_stocks)
                initial_weights = random_weights / np.sum(random_weights)

            optimized = minimize(objective_function, initial_weights, method='SLSQP',
                                 bounds=bounds, constraints=constraints, options={'maxiter': 1000})

            if optimized.success:
                utility = -objective_function(optimized.x)
                if utility > best_utility:
                    best_utility = utility
                    best_result = optimized

        if best_result is not None and best_result.success:
            optimal_weights = best_result.x
            exp_return, exp_volatility = calculate_performance(optimal_weights)

            # Calculate Sharpe ratio
            risk_free_rate = 0.02
            sharpe_ratio = (exp_return - risk_free_rate) / exp_volatility if exp_volatility > 0 else 0

            # Filter and normalize weights
            filtered_weights = {s: round(w, 4) for s, w in zip(stock_symbols, optimal_weights) if w > 0.005}
            total_weight = sum(filtered_weights.values())
            if total_weight < 0.999:
                filtered_weights = {s: round(w / total_weight, 4) for s, w in filtered_weights.items()}

            return {
                'weights': filtered_weights,
                'expected_return': round(exp_return, 2),
                'volatility': round(exp_volatility, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'success': True
            }

        return {'success': False, 'error': "Optimization failed."}


class OptimizationStrategyFactory:
    """
    Factory class to create instances of optimization strategies.
    """

    @staticmethod
    def get_strategy(strategy_type):
        """
        Get an optimization strategy instance based on the strategy type.

        Args:
            strategy_type (str): Type of the strategy ('cvxpy' or 'scipy').

        Returns:
            OptimizationStrategy: Instance of the requested strategy.
        """
        strategies = {
            'cvxpy': CVXPYOptimizationStrategy(),
            'scipy': SciPyOptimizationStrategy()
        }
        return strategies.get(strategy_type.lower(), SciPyOptimizationStrategy())


class MarkowitzOptimizer:
    """
    Class to perform portfolio optimization using the Markowitz model.
    """

    def __init__(self, stock_symbols, returns_data, risk_level='Medium', investment_period=12):
        """
        Initialize the MarkowitzOptimizer.

        Args:
            stock_symbols (list): List of stock symbols.
            returns_data (pd.DataFrame): Historical returns data for the stocks.
            risk_level (str): Risk level ('Low', 'Medium', 'High').
            investment_period (int): Investment period in months.
        """
        self.stock_symbols = stock_symbols
        self.returns_data = self.clean_returns_data(returns_data)
        self.risk_level = risk_level
        self.investment_period = investment_period
        self.risk_params = self.initialize_risk_params()
        self.adjust_for_investment_period()

        self.cvxpy_strategy = CVXPYOptimizationStrategy()
        self.scipy_strategy = SciPyOptimizationStrategy()

    def clean_returns_data(self, returns_data):
        """
        Clean the returns data by handling NaN, infinite values, and outliers.

        Args:
            returns_data (pd.DataFrame): Historical returns data.

        Returns:
            pd.DataFrame: Cleaned returns data.
        """
        cleaned_data = returns_data.replace([np.inf, -np.inf], np.nan)

        for col in cleaned_data.columns:
            col_mean = cleaned_data[col].mean()
            cleaned_data[col] = cleaned_data[col].fillna(col_mean)

        for col in cleaned_data.columns:
            q_low = cleaned_data[col].quantile(0.01)
            q_high = cleaned_data[col].quantile(0.99)
            cleaned_data[col] = cleaned_data[col].clip(q_low, q_high)

        return cleaned_data

    def initialize_risk_params(self):
        """
        Initialize risk parameters based on the risk level.

        Returns:
            dict: Risk parameters for each risk level.
        """
        return {
            'Low': {'max_weight': 0.15, 'min_stocks': 8, 'risk_aversion': 1.5, 'volatility_penalty': 1.5},
            'Medium': {'max_weight': 0.25, 'min_stocks': 5, 'risk_aversion': 1.0, 'volatility_penalty': 1.0},
            'High': {'max_weight': 0.35, 'min_stocks': 3, 'risk_aversion': 0.5, 'volatility_penalty': 0.5}
        }

    def adjust_for_investment_period(self):
        """
        Adjust risk parameters based on the investment period.
        """
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
        """
        Calculate the performance of the portfolio.

        Args:
            weights (np.ndarray): Portfolio weights.

        Returns:
            tuple: Annualized return and volatility.
        """
        ewm_returns = self.returns_data.ewm(alpha=0.3).mean().iloc[-1]
        mean_monthly_return = np.dot(weights, ewm_returns)
        annual_return = (1 + mean_monthly_return) ** 12 - 1

        sample_cov = self.returns_data.cov()
        target = np.diag(np.diag(sample_cov))
        shrinkage = 0.2
        cov_matrix = (1 - shrinkage) * sample_cov + shrinkage * target

        monthly_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        annual_volatility = monthly_volatility * np.sqrt(12)

        return annual_return, annual_volatility

    def optimize_portfolio(self):
        """
        Optimize the portfolio using the appropriate strategy.

        Returns:
            dict: Optimization results including weights, expected return, volatility, and Sharpe ratio.

        Raises:
            ValueError: If optimization fails.
        """
        num_stocks = len(self.stock_symbols)
        params = self.risk_params[self.risk_level]

        if num_stocks <= 20:
            result = self.cvxpy_strategy.optimize(
                self.stock_symbols,
                self.returns_data,
                self.risk_params[self.risk_level],
                self.calculate_performance
            )

            if not result.get('success', False):
                result = self.scipy_strategy.optimize(
                    self.stock_symbols,
                    self.returns_data,
                    self.risk_params[self.risk_level],
                    self.calculate_performance
                )
        else:
            result = self.scipy_strategy.optimize(
                self.stock_symbols,
                self.returns_data,
                self.risk_params[self.risk_level],
                self.calculate_performance
            )

        if not result.get('success', False):
            raise ValueError(result.get('error', "Optimization failed."))

        result['risk_level'] = self.risk_level
        result['investment_period'] = self.investment_period

        if 'success' in result:
            del result['success']
        if 'error' in result:
            del result['error']

        return result