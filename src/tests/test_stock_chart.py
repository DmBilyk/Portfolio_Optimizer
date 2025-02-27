import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
import datetime
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.dates as mdates


from PySide6.QtWidgets import QApplication, QMessageBox
import sys
from src.ui.widgets.stock_chart import StockChartWidget


app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestStockChartWidget(unittest.TestCase):
    def setUp(self):

        self.mock_portfolio_manager = Mock()
        self.mock_stock_manager = Mock()


        self.mock_portfolio_manager.get_all_portfolios.return_value = [
            (1, "Test Portfolio 1"),
            (2, "Test Portfolio 2")
        ]


        self.mock_stock_manager.get_portfolio_stocks.return_value = [
            (1, "AAPL", 100, 150.0),
            (2, "MSFT", 50, 300.0)
        ]


        self.widget = StockChartWidget(self.mock_portfolio_manager, self.mock_stock_manager)


        self.mock_portfolio_manager.reset_mock()
        self.mock_stock_manager.reset_mock()

    def tearDown(self):

        self.widget = None

    def test_initialization(self):

        self.assertIsNotNone(self.widget.portfolio_selector)
        self.assertIsNotNone(self.widget.stock_selector)
        self.assertIsNotNone(self.widget.period_selector)
        self.assertIsNotNone(self.widget.refresh_button)
        self.assertIsNotNone(self.widget.figure)
        self.assertIsNotNone(self.widget.ax)
        self.assertIsNotNone(self.widget.canvas)


        self.assertEqual(self.widget.portfolio_selector.count(), 3)
        self.assertEqual(self.widget.portfolio_selector.itemText(0), "Select Portfolio")
        self.assertEqual(self.widget.stock_selector.count(), 1)
        self.assertFalse(self.widget.stock_selector.isEnabled())
        self.assertEqual(self.widget.period_selector.count(), 5)

    def test_load_portfolios(self):

        self.mock_portfolio_manager.reset_mock()


        self.widget.load_portfolios()


        self.mock_portfolio_manager.get_all_portfolios.assert_called_once()


        self.assertEqual(self.widget.portfolio_selector.count(), 3)
        self.assertEqual(self.widget.portfolio_selector.itemText(1), "Test Portfolio 1")
        self.assertEqual(self.widget.portfolio_selector.itemData(1), 1)
        self.assertEqual(self.widget.portfolio_selector.itemText(2), "Test Portfolio 2")
        self.assertEqual(self.widget.portfolio_selector.itemData(2), 2)

    def test_update_stock_selector_no_portfolio_selected(self):

        self.widget.portfolio_selector.setCurrentIndex(0)


        self.widget.update_stock_selector()


        self.assertFalse(self.widget.stock_selector.isEnabled())
        self.assertEqual(self.widget.stock_selector.count(), 1)
        self.assertEqual(self.widget.stock_selector.itemText(0), "Select Stock")

    def test_update_stock_selector_with_portfolio(self):

        self.widget.portfolio_selector.setCurrentIndex(1)


        self.widget.update_stock_selector()


        self.mock_stock_manager.get_portfolio_stocks.assert_called_with(1)


        self.assertTrue(self.widget.stock_selector.isEnabled())
        self.assertEqual(self.widget.stock_selector.count(), 3)
        self.assertEqual(self.widget.stock_selector.itemText(1), "AAPL")
        self.assertEqual(self.widget.stock_selector.itemText(2), "MSFT")

    @patch('yfinance.Ticker')
    def test_update_chart_valid_data(self, mock_ticker):

        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        mock_data = pd.DataFrame({
            'Open': np.random.randn(10) + 100,
            'High': np.random.randn(10) + 102,
            'Low': np.random.randn(10) + 98,
            'Close': np.random.randn(10) + 101,
            'Volume': np.random.randint(1000000, 10000000, 10)
        }, index=dates)


        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance


        self.widget.portfolio_selector.setCurrentIndex(1)
        self.widget.update_stock_selector()
        self.widget.stock_selector.setCurrentIndex(1)
        self.widget.period_selector.setCurrentIndex(0)


        with patch.object(self.widget.canvas, 'draw'):

            self.widget.update_chart()


            mock_ticker.assert_called_with("AAPL")
            mock_ticker_instance.history.assert_called_with(period='1MO')


            self.assertIsNotNone(self.widget.current_data)
            pd.testing.assert_frame_equal(self.widget.current_data, mock_data)


            self.assertEqual(self.widget.ax.get_title(), "AAPL - Price Dynamics")
            self.assertEqual(self.widget.ax.get_xlabel(), "Date")
            self.assertEqual(self.widget.ax.get_ylabel(), "Price (USD)")

    @patch('yfinance.Ticker')
    def test_update_chart_empty_data(self, mock_ticker):

        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance


        self.widget.portfolio_selector.setCurrentIndex(1)
        self.widget.update_stock_selector()
        self.widget.stock_selector.setCurrentIndex(1)


        with patch.object(QMessageBox, 'warning') as mock_warning:

            self.widget.update_chart()


            mock_warning.assert_called_once()

            self.assertEqual(mock_warning.call_args[0][0], self.widget)
            self.assertEqual(mock_warning.call_args[0][1], "Error")

            self.assertIn("No data available", mock_warning.call_args[0][2])

    @patch('yfinance.Ticker')
    def test_update_chart_missing_close_column(self, mock_ticker):

        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        mock_data = pd.DataFrame({
            'Open': np.random.randn(10) + 100,
            'High': np.random.randn(10) + 102,
            'Low': np.random.randn(10) + 98,

            'Volume': np.random.randint(1000000, 10000000, 10)
        }, index=dates)


        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance


        self.widget.portfolio_selector.setCurrentIndex(1)
        self.widget.update_stock_selector()
        self.widget.stock_selector.setCurrentIndex(1)


        with patch.object(QMessageBox, 'warning') as mock_warning:
            # Call the method
            self.widget.update_chart()


            mock_warning.assert_called_once()

            self.assertEqual(mock_warning.call_args[0][0], self.widget)
            self.assertEqual(mock_warning.call_args[0][1], "Error")
            self.assertIn("Price data missing", mock_warning.call_args[0][2])

    @patch('yfinance.Ticker')
    def test_update_chart_exception(self, mock_ticker):

        mock_ticker_instance = Mock()
        mock_ticker_instance.history.side_effect = Exception("Test error")
        mock_ticker.return_value = mock_ticker_instance


        self.widget.portfolio_selector.setCurrentIndex(1)
        self.widget.update_stock_selector()
        self.widget.stock_selector.setCurrentIndex(1)


        with patch.object(QMessageBox, 'warning') as mock_warning:

            self.widget.update_chart()


            mock_warning.assert_called_once()

            self.assertEqual(mock_warning.call_args[0][0], self.widget)
            self.assertEqual(mock_warning.call_args[0][1], "Error")
            self.assertIn("Could not fetch stock data", mock_warning.call_args[0][2])
            self.assertIn("Test error", mock_warning.call_args[0][2])

    def test_on_hover_no_data(self):

        mock_event = Mock()
        mock_event.inaxes = None


        self.widget.on_hover(mock_event)


        self.assertIsNone(self.widget.annotation)

    @patch('matplotlib.axes.Axes.annotate')
    def test_on_hover_with_data(self, mock_annotate):

        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        mock_data = pd.DataFrame({
            'Close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        }, index=dates)
        self.widget.current_data = mock_data


        mock_event = Mock()
        mock_event.inaxes = self.widget.ax

        mock_event.xdata = mdates.date2num(dates[5])
        mock_event.ydata = 105


        mock_annotation = Mock()
        mock_annotate.return_value = mock_annotation


        with patch.object(self.widget.canvas, 'draw_idle'):
            self.widget.on_hover(mock_event)


            mock_annotate.assert_called_once()

            annotation_text = mock_annotate.call_args[0][0]
            self.assertIn("2023-01-06", annotation_text)
            self.assertIn("$105.00", annotation_text)


if __name__ == '__main__':
    unittest.main()