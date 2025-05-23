import unittest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import pytest

# Import modules to test
from src.domain.portfolio.optimizer import (
    OptimizationStrategy,
    CVXPYOptimizationStrategy,
    SciPyOptimizationStrategy,
    OptimizationStrategyFactory,
    MarkowitzOptimizer
)


class TestOptimizationStrategy(unittest.TestCase):
    """Tests for the base OptimizationStrategy class."""

    def test_optimization_strategy_is_abstract(self):
        """Test that OptimizationStrategy cannot be instantiated."""
        with self.assertRaises(TypeError):
            OptimizationStrategy()


class TestOptimizationStrategyFactory(unittest.TestCase):
    """Tests for the OptimizationStrategyFactory class."""

    def test_get_strategy_cvxpy(self):
        """Test that factory returns CVXPYOptimizationStrategy for 'cvxpy'."""
        strategy = OptimizationStrategyFactory.get_strategy('cvxpy')
        self.assertIsInstance(strategy, CVXPYOptimizationStrategy)

    def test_get_strategy_scipy(self):
        """Test that factory returns SciPyOptimizationStrategy for 'scipy'."""
        strategy = OptimizationStrategyFactory.get_strategy('scipy')
        self.assertIsInstance(strategy, SciPyOptimizationStrategy)

    def test_get_strategy_unknown(self):
        """Test that factory returns SciPyOptimizationStrategy for unknown strategy."""
        strategy = OptimizationStrategyFactory.get_strategy('unknown')
        self.assertIsInstance(strategy, SciPyOptimizationStrategy)


class TestCVXPYOptimizationStrategy(unittest.TestCase):
    """Tests for the CVXPYOptimizationStrategy class."""

    def setUp(self):
        self.strategy = CVXPYOptimizationStrategy()
        self.stock_symbols = ['AAPL', 'MSFT', 'GOOG']

        # Create sample returns data
        data = np.array([
            [0.01, 0.02, 0.01],
            [0.02, 0.01, 0.02],
            [0.03, 0.02, 0.01],
            [0.02, 0.01, 0.03],
            [0.01, 0.03, 0.02]
        ])
        self.returns_data = pd.DataFrame(data, columns=self.stock_symbols)

        self.risk_params = {
            'max_weight': 0.5,
            'risk_aversion': 1.0
        }

        def mock_calculate_performance(weights):
            return 0.1, 0.2

        self.calculate_performance = mock_calculate_performance

    @patch('cvxpy.Problem.solve')
    @patch('cvxpy.Maximize')
    def test_optimize_success(self, mock_maximize, mock_solve):
        """Test successful optimization using CVXPY."""

        mock_problem = MagicMock()
        mock_problem.status = "optimal"
        mock_solve.return_value = mock_problem


        mock_variable = MagicMock()
        mock_variable.value = np.array([0.33, 0.33, 0.34])

        with patch('cvxpy.Variable', return_value=mock_variable):
            with patch('cvxpy.Problem', return_value=mock_problem):
                result = self.strategy.optimize(
                    self.stock_symbols,
                    self.returns_data,
                    self.risk_params,
                    self.calculate_performance
                )

                self.assertTrue(result['success'])
                self.assertEqual(result['expected_return'], 0.1)
                self.assertEqual(result['volatility'], 0.2)
                self.assertIn('sharpe_ratio', result)
                self.assertIn('weights', result)

    @patch('cvxpy.Problem.solve')
    def test_optimize_failure(self, mock_solve):
        """Test optimization failure with CVXPY."""
        # Setup mock to simulate failure
        mock_problem = MagicMock()
        mock_problem.status = "infeasible"
        mock_solve.return_value = mock_problem

        with patch('cvxpy.Problem', return_value=mock_problem):
            result = self.strategy.optimize(
                self.stock_symbols,
                self.returns_data,
                self.risk_params,
                self.calculate_performance
            )

            self.assertFalse(result['success'])

    @patch('cvxpy.Problem.solve')
    def test_optimize_exception(self, mock_solve):
        """Test exception handling during optimization."""
        # Setup mock to raise exception
        mock_solve.side_effect = Exception("Test exception")

        result = self.strategy.optimize(
            self.stock_symbols,
            self.returns_data,
            self.risk_params,
            self.calculate_performance
        )

        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestSciPyOptimizationStrategy(unittest.TestCase):
    """Tests for the SciPyOptimizationStrategy class."""

    def setUp(self):
        self.strategy = SciPyOptimizationStrategy()
        self.stock_symbols = ['AAPL', 'MSFT', 'GOOG']

        # Create sample returns data
        data = np.array([
            [0.01, 0.02, 0.01],
            [0.02, 0.01, 0.02],
            [0.03, 0.02, 0.01],
            [0.02, 0.01, 0.03],
            [0.01, 0.03, 0.02]
        ])
        self.returns_data = pd.DataFrame(data, columns=self.stock_symbols)

        self.risk_params = {
            'max_weight': 0.5,
            'risk_aversion': 1.0,
            'min_stocks': 2
        }

        def mock_calculate_performance(weights):
            return 0.1, 0.2  # Mock expected return and volatility

        self.calculate_performance = mock_calculate_performance

    @patch('scipy.optimize.minimize')
    def test_optimize_success(self, mock_minimize):
        """Test successful optimization using SciPy."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.x = np.array([0.33, 0.33, 0.34])
        mock_minimize.return_value = mock_result

        result = self.strategy.optimize(
            self.stock_symbols,
            self.returns_data,
            self.risk_params,
            self.calculate_performance
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['expected_return'], 0.1)
        self.assertEqual(result['volatility'], 0.2)
        self.assertIn('sharpe_ratio', result)
        self.assertIn('weights', result)

    @patch('scipy.optimize.minimize')
    def test_optimize_failure(self, mock_minimize):
        """Test optimization failure with SciPy."""
        # Setup mock to simulate failure
        mock_result = MagicMock()
        mock_result.success = False
        mock_minimize.return_value = mock_result

        result = self.strategy.optimize(
            self.stock_symbols,
            self.returns_data,
            self.risk_params,
            self.calculate_performance
        )

        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestMarkowitzOptimizer(unittest.TestCase):
    """Tests for the MarkowitzOptimizer class."""

    def setUp(self):
        self.stock_symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN']

        # Create sample returns data with some NaN and inf values
        np.random.seed(42)  # For reproducibility
        data = np.random.normal(0.01, 0.03, (20, 4))
        data[0, 0] = np.nan  # Add a NaN value
        data[1, 1] = np.inf  # Add an inf value
        data[2, 2] = -np.inf  # Add a -inf value

        self.returns_data = pd.DataFrame(data, columns=self.stock_symbols)

        # Create instance of optimizer
        self.optimizer = MarkowitzOptimizer(
            self.stock_symbols,
            self.returns_data,
            risk_level='Medium',
            investment_period=12
        )

    def test_initialization(self):
        """Test proper initialization of MarkowitzOptimizer."""
        self.assertEqual(self.optimizer.stock_symbols, self.stock_symbols)
        self.assertEqual(self.optimizer.risk_level, 'Medium')
        self.assertEqual(self.optimizer.investment_period, 12)

        # Check that risk params were initialized
        self.assertIn('Medium', self.optimizer.risk_params)
        self.assertIn('max_weight', self.optimizer.risk_params['Medium'])

    def test_clean_returns_data(self):
        """Test data cleaning functionality."""
        cleaned_data = self.optimizer.clean_returns_data(self.returns_data)

        # Check that NaN and inf values were handled
        self.assertFalse(cleaned_data.isnull().any().any())
        self.assertFalse(np.isinf(cleaned_data.values).any())

    def test_adjust_for_investment_period(self):
        """Test adjustment of risk parameters based on investment period."""
        # Save initial values
        initial_risk_aversion = self.optimizer.risk_params['Medium']['risk_aversion']

        # Test short-term adjustment
        short_term_optimizer = MarkowitzOptimizer(
            self.stock_symbols,
            self.returns_data,
            risk_level='Medium',
            investment_period=3
        )

        self.assertGreater(
            short_term_optimizer.risk_params['Medium']['risk_aversion'],
            initial_risk_aversion
        )

        # Test long-term adjustment
        long_term_optimizer = MarkowitzOptimizer(
            self.stock_symbols,
            self.returns_data,
            risk_level='Medium',
            investment_period=48
        )

        self.assertLess(
            long_term_optimizer.risk_params['Medium']['risk_aversion'],
            initial_risk_aversion
        )

    def test_calculate_performance(self):
        """Test calculation of portfolio performance metrics."""
        # Test with equal weights
        equal_weights = np.ones(len(self.stock_symbols)) / len(self.stock_symbols)
        annual_return, annual_volatility = self.optimizer.calculate_performance(equal_weights)

        self.assertIsInstance(annual_return, float)
        self.assertIsInstance(annual_volatility, float)
        self.assertGreaterEqual(annual_volatility, 0)  # Volatility should be non-negative

    @patch.object(CVXPYOptimizationStrategy, 'optimize')
    @patch.object(SciPyOptimizationStrategy, 'optimize')
    def test_optimize_portfolio_cvxpy_success(self, mock_scipy, mock_cvxpy):
        """Test portfolio optimization with CVXPY success."""
        # Mock successful CVXPY optimization
        mock_cvxpy.return_value = {
            'success': True,
            'weights': {'AAPL': 0.25, 'MSFT': 0.25, 'GOOG': 0.25, 'AMZN': 0.25},
            'expected_return': 0.1,
            'volatility': 0.2,
            'sharpe_ratio': 0.4
        }

        result = self.optimizer.optimize_portfolio()

        # Check that CVXPY was used for small number of stocks
        mock_cvxpy.assert_called_once()
        mock_scipy.assert_not_called()

        # Check result
        self.assertEqual(result['expected_return'], 0.1)
        self.assertEqual(result['volatility'], 0.2)
        self.assertEqual(result['sharpe_ratio'], 0.4)
        self.assertEqual(result['risk_level'], 'Medium')
        self.assertEqual(result['investment_period'], 12)

    @patch.object(CVXPYOptimizationStrategy, 'optimize')
    @patch.object(SciPyOptimizationStrategy, 'optimize')
    def test_optimize_portfolio_cvxpy_fallback(self, mock_scipy, mock_cvxpy):
        """Test fallback to SciPy when CVXPY fails."""
        # Mock CVXPY failure and SciPy success
        mock_cvxpy.return_value = {'success': False, 'error': 'CVXPY failed'}
        mock_scipy.return_value = {
            'success': True,
            'weights': {'AAPL': 0.25, 'MSFT': 0.25, 'GOOG': 0.25, 'AMZN': 0.25},
            'expected_return': 0.1,
            'volatility': 0.2,
            'sharpe_ratio': 0.4
        }

        result = self.optimizer.optimize_portfolio()

        # Check that both strategies were called
        mock_cvxpy.assert_called_once()
        mock_scipy.assert_called_once()

        # Check result
        self.assertEqual(result['expected_return'], 0.1)
        self.assertEqual(result['volatility'], 0.2)

    @patch.object(CVXPYOptimizationStrategy, 'optimize')
    @patch.object(SciPyOptimizationStrategy, 'optimize')
    def test_optimize_portfolio_large_universe(self, mock_scipy, mock_cvxpy):
        """Test direct use of SciPy for large stock universe."""
        # Create optimizer with many stocks
        many_symbols = ['STOCK_' + str(i) for i in range(30)]
        many_returns = pd.DataFrame(
            np.random.normal(0.01, 0.03, (20, 30)),
            columns=many_symbols
        )

        large_optimizer = MarkowitzOptimizer(
            many_symbols,
            many_returns,
            risk_level='Medium',
            investment_period=12
        )

        mock_scipy.return_value = {
            'success': True,
            'weights': {many_symbols[0]: 0.1, many_symbols[1]: 0.9},
            'expected_return': 0.1,
            'volatility': 0.2,
            'sharpe_ratio': 0.4
        }

        result = large_optimizer.optimize_portfolio()

        # Check that only SciPy was called for large universe
        mock_cvxpy.assert_not_called()
        mock_scipy.assert_called_once()

        # Check result
        self.assertEqual(result['expected_return'], 0.1)
        self.assertEqual(result['volatility'], 0.2)

    @patch.object(CVXPYOptimizationStrategy, 'optimize')
    @patch.object(SciPyOptimizationStrategy, 'optimize')
    def test_optimize_portfolio_all_failures(self, mock_scipy, mock_cvxpy):
        """Test handling of optimization failures."""

        mock_cvxpy.return_value = {'success': False, 'error': 'CVXPY failed'}
        mock_scipy.return_value = {'success': False, 'error': 'SciPy failed'}

        with self.assertRaises(ValueError):
            self.optimizer.optimize_portfolio()


if __name__ == '__main__':
    pytest.main(['-xvs', __file__])