import unittest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.widgets.portfolio_optimizer import PortfolioOptimizerWidget
import unittest
import numpy as np
import pandas as pd
from src.domain.portfolio.optimizer import MarkowitzOptimizer

class TestMarkowitzOptimizer(unittest.TestCase):
    def setUp(self):
        self.stock_symbols = ['AAPL', 'GOOGL', 'AMZN', 'MSFT', 'TSLA']
        np.random.seed(42)
        returns_data = np.random.randn(60, len(self.stock_symbols)) * 0.02
        self.returns_data = pd.DataFrame(returns_data, columns=self.stock_symbols)

    def test_initialization(self):
        optimizer = MarkowitzOptimizer(self.stock_symbols, self.returns_data, risk_level='High', investment_period=24)
        self.assertEqual(optimizer.risk_level, 'High')
        self.assertEqual(optimizer.investment_period, 24)
        self.assertIn('max_weight', optimizer.risk_params['High'])

    def test_calculate_portfolio_performance(self):
        optimizer = MarkowitzOptimizer(self.stock_symbols, self.returns_data)
        weights = np.ones(len(self.stock_symbols)) / len(self.stock_symbols)
        portfolio_return, portfolio_volatility = optimizer.calculate_performance(weights)
        self.assertIsInstance(portfolio_return, float)
        self.assertIsInstance(portfolio_volatility, float)
        self.assertGreaterEqual(portfolio_volatility, 0)

    def test_optimize_portfolio(self):
        optimizer = MarkowitzOptimizer(self.stock_symbols, self.returns_data, risk_level='Medium', investment_period=12)
        result = optimizer.optimize_portfolio()
        self.assertIsInstance(result, dict)
        self.assertIn('weights', result)
        self.assertIn('expected_return', result)
        self.assertIn('volatility', result)
        self.assertGreaterEqual(len(result['weights']), optimizer.risk_params['Medium']['min_stocks'])

    def test_optimization_fails(self):
        empty_returns = pd.DataFrame(columns=self.stock_symbols)  # No data
        optimizer = MarkowitzOptimizer(self.stock_symbols, empty_returns)
        with self.assertRaises(ValueError):
            optimizer.optimize_portfolio()



class TestPortfolioOptimizerWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

    def setUp(self):
        self.mock_portfolio_service = MagicMock()
        self.widget = PortfolioOptimizerWidget(self.mock_portfolio_service)

    def test_load_portfolios(self):
        self.mock_portfolio_service.get_all_portfolios.return_value = [(1, "Test Portfolio")]

        self.widget.load_portfolios()

        self.assertEqual(self.widget.portfolio_selector.count(), 2)  # "Select Portfolio" + 1 портфель
        self.assertEqual(self.widget.portfolio_selector.itemText(1), "Test Portfolio")

    def test_optimize_portfolio_success(self):
        self.mock_portfolio_service.create_optimized_portfolio.return_value = {
            'stock_data': [{'symbol': 'AAPL', 'shares': 5, 'price': 150, 'amount': 750, 'weight': 0.5}],
            'optimal_portfolio': {'expected_return': 0.08, 'volatility': 0.15, 'sharpe_ratio': 1.2},
            'total_invested': 750,
            'investment': 1000,
            'remaining': 250
        }

        self.widget.optimize_portfolio()

        self.mock_portfolio_service.create_optimized_portfolio.assert_called_once()
        self.assertIsNotNone(self.widget.optimized_stocks)
        self.assertTrue(self.widget.add_to_portfolio_button.isEnabled())

    def test_optimize_portfolio_failure(self):
        self.mock_portfolio_service.create_optimized_portfolio.side_effect = Exception("Optimization failed")

        self.widget.optimize_portfolio()

        self.mock_portfolio_service.create_optimized_portfolio.assert_called_once()
        self.assertIsNone(self.widget.optimized_stocks)
        self.assertFalse(self.widget.add_to_portfolio_button.isEnabled())

    def test_add_optimized_stocks_success(self):
        self.widget.optimized_stocks = [{'symbol': 'AAPL', 'shares': 5, 'price': 150, 'amount': 750, 'weight': 0.5}]
        self.mock_portfolio_service.add_stocks_to_portfolio.return_value = (1, [])

        self.widget.portfolio_selector.addItem("Test Portfolio", 1)
        self.widget.portfolio_selector.setCurrentIndex(1)

        self.widget.add_optimized_stocks()

        self.mock_portfolio_service.add_stocks_to_portfolio.assert_called_once()
        self.assertFalse(self.widget.add_to_portfolio_button.isEnabled())
        self.assertIsNone(self.widget.optimized_stocks)

    def test_add_optimized_stocks_no_optimization(self):
        self.widget.optimized_stocks = None

        self.widget.add_optimized_stocks()

        self.mock_portfolio_service.add_stocks_to_portfolio.assert_not_called()

    def test_add_optimized_stocks_no_portfolio_selected(self):
        self.widget.optimized_stocks = [{'symbol': 'AAPL', 'shares': 5, 'price': 150, 'amount': 750, 'weight': 0.5}]
        self.widget.portfolio_selector.setCurrentIndex(0)

        self.widget.add_optimized_stocks()

        self.mock_portfolio_service.add_stocks_to_portfolio.assert_not_called()


if __name__ == "__main__":
    unittest.main()