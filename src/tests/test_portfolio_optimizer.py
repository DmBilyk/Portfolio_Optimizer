import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
from PySide6.QtWidgets import QApplication
import sys


from src.ui.widgets.portfolio_optimizer import MarkowitzOptimizer, PortfolioOptimizerWidget, MetricCard, StockCard


class TestMarkowitzOptimizer(unittest.TestCase):
    def setUp(self):

        self.stock_symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'META']


        np.random.seed(42)
        dates = pd.date_range(start='2022-01-01', periods=100)
        self.returns_data = pd.DataFrame(
            np.random.normal(0.001, 0.02, (100, len(self.stock_symbols))),
            columns=self.stock_symbols,
            index=dates
        )


        self.optimizer = MarkowitzOptimizer(
            self.stock_symbols,
            self.returns_data,
            risk_level='Medium',
            investment_period=12
        )

    def test_optimizer_initialization(self):

        self.assertEqual(self.optimizer.stock_symbols, self.stock_symbols)
        self.assertTrue(self.optimizer.returns_data.equals(self.returns_data))
        self.assertEqual(self.optimizer.risk_level, 'Medium')
        self.assertEqual(self.optimizer.investment_period, 12)

        self.assertIn('max_weight', self.optimizer.risk_params['Medium'])
        self.assertIn('min_stocks', self.optimizer.risk_params['Medium'])
        self.assertIn('risk_aversion', self.optimizer.risk_params['Medium'])
        self.assertIn('volatility_penalty', self.optimizer.risk_params['Medium'])

    def test_risk_level_adjustment(self):

        low_risk = MarkowitzOptimizer(
            self.stock_symbols, self.returns_data, risk_level='Low', investment_period=12
        )

        high_risk = MarkowitzOptimizer(
            self.stock_symbols, self.returns_data, risk_level='High', investment_period=12
        )


        self.assertLess(low_risk.risk_params['Low']['max_weight'],
                        high_risk.risk_params['High']['max_weight'])
        self.assertGreater(low_risk.risk_params['Low']['min_stocks'],
                           high_risk.risk_params['High']['min_stocks'])


        self.assertGreater(low_risk.risk_params['Low']['risk_aversion'],
                           high_risk.risk_params['High']['risk_aversion'])

    def test_investment_period_adjustment(self):

        short_term = MarkowitzOptimizer(
            self.stock_symbols, self.returns_data, risk_level='Medium', investment_period=3
        )

        long_term = MarkowitzOptimizer(
            self.stock_symbols, self.returns_data, risk_level='Medium', investment_period=48
        )


        self.assertGreater(short_term.risk_params['Medium']['risk_aversion'],
                           self.optimizer.risk_params['Medium']['risk_aversion'])


        self.assertLess(long_term.risk_params['Medium']['risk_aversion'],
                        self.optimizer.risk_params['Medium']['risk_aversion'])

    def test_portfolio_performance_calculation(self):

        weights = np.ones(len(self.stock_symbols)) / len(self.stock_symbols)

        portfolio_return, portfolio_volatility = self.optimizer.calculate_portfolio_performance(weights)


        self.assertIsInstance(portfolio_return, float)
        self.assertIsInstance(portfolio_volatility, float)
        self.assertGreater(portfolio_volatility, 0)

    def test_portfolio_optimization(self):

        result = self.optimizer.optimize_portfolio()


        self.assertIn('weights', result)
        self.assertIn('expected_return', result)
        self.assertIn('volatility', result)
        self.assertIn('sharpe_ratio', result)


        weights_sum = sum(result['weights'].values())
        self.assertAlmostEqual(weights_sum, 1.0, places=2)


        self.assertGreaterEqual(
            len(result['weights']),
            self.optimizer.risk_params['Medium']['min_stocks']
        )


        max_weight = max(result['weights'].values())
        self.assertLessEqual(
            max_weight,
            self.optimizer.risk_params['Medium']['max_weight']
        )


class TestPortfolioOptimizerWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):

        self.portfolio_manager_mock = MagicMock()
        self.stock_manager_mock = MagicMock()
        self.market_data_mock = MagicMock()


        self.market_data_mock.get_all_stock_symbols.return_value = ['AAPL', 'MSFT', 'GOOG']


        dates = pd.date_range(start='2022-01-01', periods=100)
        returns_data = pd.DataFrame(
            np.random.normal(0.001, 0.02, (100, 3)),
            columns=['AAPL', 'MSFT', 'GOOG'],
            index=dates
        )
        self.market_data_mock.get_historical_returns.return_value = returns_data


        self.market_data_mock.get_current_prices.return_value = {
            'AAPL': 150.0,
            'MSFT': 250.0,
            'GOOG': 2000.0
        }


        self.widget = PortfolioOptimizerWidget(
            self.portfolio_manager_mock,
            self.stock_manager_mock,
            self.market_data_mock
        )

    def test_widget_initialization(self):

        self.assertIsNotNone(self.widget.investment_amount)
        self.assertIsNotNone(self.widget.investment_period)
        self.assertIsNotNone(self.widget.risk_level)
        self.assertIsNotNone(self.widget.portfolio_selector)
        self.assertIsNotNone(self.widget.optimize_button)
        self.assertIsNotNone(self.widget.add_to_portfolio_button)


        self.assertEqual(self.widget.investment_amount.value(), 10000)
        self.assertEqual(self.widget.investment_period.value(), 12)
        self.assertEqual(self.widget.risk_level.currentText(), 'Low')


        self.assertFalse(self.widget.add_to_portfolio_button.isEnabled())

    @patch('src.ui.widgets.portfolio_optimizer.MarkowitzOptimizer')
    def test_optimize_portfolio_success(self, mock_optimizer_class):

        mock_optimizer = MagicMock()
        mock_optimizer_class.return_value = mock_optimizer


        mock_optimizer.optimize_portfolio.return_value = {
            'weights': {'AAPL': 0.5, 'MSFT': 0.3, 'GOOG': 0.2},
            'expected_return': 0.12,
            'volatility': 0.18,
            'sharpe_ratio': 0.66,
            'risk_level': 'Medium',
            'investment_period': 12
        }


        self.widget.optimize_portfolio()


        mock_optimizer_class.assert_called_once()


        mock_optimizer.optimize_portfolio.assert_called_once()


        self.assertTrue(self.widget.add_to_portfolio_button.isEnabled())


        self.assertIsNotNone(self.widget.optimized_stocks)
        self.assertGreater(len(self.widget.optimized_stocks), 0)

    def test_add_optimized_stocks(self):

        self.widget.optimized_stocks = [
            {'symbol': 'AAPL', 'shares': 10, 'price': 150.0, 'amount': 1500.0, 'weight': 0.5},
            {'symbol': 'MSFT', 'shares': 3, 'price': 250.0, 'amount': 750.0, 'weight': 0.25}
        ]


        self.widget.portfolio_selector.addItem("Test Portfolio", 1)
        self.widget.portfolio_selector.setCurrentIndex(1)

        with patch('PySide6.QtWidgets.QMessageBox.information') as mock_info_box:
            self.widget.add_optimized_stocks()


        self.assertEqual(self.widget.stock_manager.add_stock.call_count, 2)


        first_call_args = self.widget.stock_manager.add_stock.call_args_list[0][0]
        self.assertEqual(first_call_args[0], 1)

        self.assertFalse(self.widget.add_to_portfolio_button.isEnabled())
        self.assertIsNone(self.widget.optimized_stocks)