"""
Unit tests for the StockChartWidget, ChartRenderer, StockDataProvider, and StockChartWidgetIntegration classes.
"""

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
from src.ui.widgets.stock_chart import (
    StockChartWidget,
    ChartRenderer,
    StockDataProvider,
    StockDataException,
    ChartConfig
)
from matplotlib import pyplot as plt

# Initialize the QApplication instance
app = QApplication.instance() or QApplication(sys.argv)

class TestStockChartWidget(unittest.TestCase):
    """
    Unit tests for the StockChartWidget class.
    """

    def setUp(self):
        """
        Set up the test case with mock portfolio and stock managers and the widget instance.
        """
        self.mock_portfolio_manager = Mock()
        self.mock_stock_manager = Mock()
        self.mock_portfolio_manager.get_all_portfolios.return_value = [
            (1, "Test Portfolio 1"), (2, "Test Portfolio 2")
        ]
        self.mock_stock_manager.get_portfolio_stocks.return_value = [
            (1, "AAPL", 100, 150.0), (2, "MSFT", 50, 300.0)
        ]
        self.widget = StockChartWidget(self.mock_portfolio_manager, self.mock_stock_manager)
        self.mock_portfolio_manager.reset_mock()
        self.mock_stock_manager.reset_mock()

    def tearDown(self):
        """
        Tear down the widget instance.
        """
        self.widget = None

    def test_initialization(self):
        """
        Test the initialization of the StockChartWidget.
        """
        self.assertIsNotNone(self.widget.portfolio_selector)
        self.assertIsNotNone(self.widget.stock_selector)
        self.assertIsNotNone(self.widget.period_selector)
        self.assertIsNotNone(self.widget.refresh_button)
        self.assertIsNotNone(self.widget.figure)
        self.assertIsNotNone(self.widget.ax)
        self.assertIsNotNone(self.widget.canvas)
        self.assertIsNotNone(self.widget.chart_renderer)
        self.assertEqual(self.widget.portfolio_selector.count(), 3)
        self.assertEqual(self.widget.portfolio_selector.itemText(0), "Select Portfolio")
        self.assertEqual(self.widget.stock_selector.count(), 1)
        self.assertFalse(self.widget.stock_selector.isEnabled())
        self.assertEqual(self.widget.period_selector.count(), 5)

    def test_load_portfolios(self):
        """
        Test loading portfolios into the widget.
        """
        self.mock_portfolio_manager.reset_mock()
        self.widget.load_portfolios()
        self.mock_portfolio_manager.get_all_portfolios.assert_called_once()
        self.assertEqual(self.widget.portfolio_selector.count(), 3)
        self.assertEqual(self.widget.portfolio_selector.itemText(1), "Test Portfolio 1")
        self.assertEqual(self.widget.portfolio_selector.itemData(1), 1)
        self.assertEqual(self.widget.portfolio_selector.itemText(2), "Test Portfolio 2")
        self.assertEqual(self.widget.portfolio_selector.itemData(2), 2)

    def test_update_stock_selector_no_portfolio_selected(self):
        """
        Test updating the stock selector when no portfolio is selected.
        """
        self.widget.portfolio_selector.setCurrentIndex(0)
        self.widget.update_stock_selector()
        self.assertFalse(self.widget.stock_selector.isEnabled())
        self.assertEqual(self.widget.stock_selector.count(), 1)
        self.assertEqual(self.widget.stock_selector.itemText(0), "Select Stock")

    def test_update_stock_selector_with_portfolio(self):
        """
        Test updating the stock selector with a selected portfolio.
        """
        self.widget.portfolio_selector.setCurrentIndex(1)
        self.widget.update_stock_selector()
        self.mock_stock_manager.get_portfolio_stocks.assert_called_with(1)
        self.assertTrue(self.widget.stock_selector.isEnabled())
        self.assertEqual(self.widget.stock_selector.count(), 3)
        self.assertEqual(self.widget.stock_selector.itemText(1), "AAPL")
        self.assertEqual(self.widget.stock_selector.itemText(2), "MSFT")

class TestChartRenderer(unittest.TestCase):
    """
    Unit tests for the ChartRenderer class.
    """

    def setUp(self):
        """
        Set up the test case with a figure, axes, canvas, and chart configuration.
        """
        self.figure = plt.figure()
        self.ax = self.figure.add_subplot(111)
        self.canvas = MagicMock()
        self.config = ChartConfig()
        self.renderer = ChartRenderer(self.figure, self.ax, self.canvas, self.config)
        self.dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        self.data = pd.DataFrame({
            'Open': np.random.randn(10) + 100,
            'High': np.random.randn(10) + 102,
            'Low': np.random.randn(10) + 98,
            'Close': np.random.randn(10) + 101,
            'Volume': np.random.randint(1000000, 10000000, 10)
        }, index=self.dates)

    def tearDown(self):
        """
        Tear down the figure and renderer instance.
        """
        plt.close(self.figure)
        self.renderer = None

    def test_render(self):
        """
        Test rendering the chart with given data.
        """
        with patch.object(self.renderer, '_plot_price_data') as mock_plot, \
             patch.object(self.renderer, '_configure_chart_appearance') as mock_config, \
             patch.object(self.renderer, '_configure_axes') as mock_axes:
            self.renderer.render(self.data, "AAPL")
            mock_plot.assert_called_once_with(self.data)
            mock_config.assert_called_once_with("AAPL")
            mock_axes.assert_called_once()
            self.canvas.draw.assert_called_once()
            self.assertTrue(self.renderer.current_data.equals(self.data))
            self.assertIsNone(self.renderer.annotation)

    def test_handle_hover(self):
        """
        Test handling hover events on the chart.
        """
        self.renderer.current_data = self.data
        mock_event = Mock()
        mock_event.inaxes = self.ax
        mock_event.xdata = mdates.date2num(self.dates[5])
        mock_event.ydata = self.data['Close'][5]
        with patch.object(self.ax, 'annotate') as mock_annotate:
            mock_annotation = Mock()
            mock_annotate.return_value = mock_annotation
            self.renderer.handle_hover(mock_event)
            mock_annotate.assert_called_once()
            annotation_text = mock_annotate.call_args[0][0]
            self.assertIn(self.dates[5].strftime("%Y-%m-%d"), annotation_text)
            self.assertIn(f"${self.data['Close'][5]:.2f}", annotation_text)

class TestStockDataProvider(unittest.TestCase):
    """
    Unit tests for the StockDataProvider class.
    """

    @patch('yfinance.Ticker')
    def test_fetch_stock_data_valid(self, mock_ticker):
        """
        Test fetching valid stock data.
        """
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
        result = StockDataProvider.fetch_stock_data("AAPL", "1MO")
        mock_ticker.assert_called_with("AAPL")
        mock_ticker_instance.history.assert_called_with(period="1MO")
        pd.testing.assert_frame_equal(result, mock_data)

    @patch('yfinance.Ticker')
    def test_fetch_stock_data_empty(self, mock_ticker):
        """
        Test fetching stock data when the result is empty.
        """
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance
        result = StockDataProvider.fetch_stock_data("AAPL", "1MO")
        self.assertIsNone(result)

    @patch('yfinance.Ticker')
    def test_fetch_stock_data_missing_close(self, mock_ticker):
        """
        Test fetching stock data when the 'Close' column is missing.
        """
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
        result = StockDataProvider.fetch_stock_data("AAPL", "1MO")
        self.assertIsNone(result)

    @patch('yfinance.Ticker')
    def test_fetch_stock_data_exception(self, mock_ticker):
        """
        Test fetching stock data when an exception occurs.
        """
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.side_effect = Exception("Test error")
        mock_ticker.return_value = mock_ticker_instance
        with self.assertRaises(StockDataException) as context:
            StockDataProvider.fetch_stock_data("AAPL", "1MO")
        self.assertIn("Could not fetch stock data", str(context.exception))
        self.assertIn("Test error", str(context.exception))

class TestStockChartWidgetIntegration(unittest.TestCase):
    """
    Integration tests for the StockChartWidget class.
    """

    def setUp(self):
        """
        Set up the test case with mock portfolio and stock managers and the widget instance.
        """
        self.mock_portfolio_manager = Mock()
        self.mock_stock_manager = Mock()
        self.mock_portfolio_manager.get_all_portfolios.return_value = [
            (1, "Test Portfolio 1"), (2, "Test Portfolio 2")
        ]
        self.mock_stock_manager.get_portfolio_stocks.return_value = [
            (1, "AAPL", 100, 150.0), (2, "MSFT", 50, 300.0)
        ]
        self.widget = StockChartWidget(self.mock_portfolio_manager, self.mock_stock_manager)

    def tearDown(self):
        """
        Tear down the widget instance.
        """
        self.widget = None

    @patch('src.ui.widgets.stock_chart.StockDataProvider.fetch_stock_data')
    def test_update_chart_valid_data(self, mock_fetch_data):
        """
        Test updating the chart with valid data.
        """
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        mock_data = pd.DataFrame({
            'Open': np.random.randn(10) + 100,
            'High': np.random.randn(10) + 102,
            'Low': np.random.randn(10) + 98,
            'Close': np.random.randn(10) + 101,
            'Volume': np.random.randint(1000000, 10000000, 10)
        }, index=dates)
        mock_fetch_data.return_value = mock_data
        self.widget.portfolio_selector.setCurrentIndex(1)
        self.widget.update_stock_selector()
        self.widget.stock_selector.setCurrentIndex(1)
        self.widget.period_selector.setCurrentIndex(0)
        with patch.object(self.widget.chart_renderer, 'render') as mock_render:
            self.widget.update_chart()
            mock_fetch_data.assert_called_with("AAPL", "1MO")
            mock_render.assert_called_with(mock_data, "AAPL")

    @patch('src.ui.widgets.stock_chart.StockDataProvider.fetch_stock_data')
    def test_update_chart_empty_data(self, mock_fetch_data):
        """
        Test updating the chart when the fetched data is empty.
        """
        mock_fetch_data.return_value = None
        self.widget.portfolio_selector.setCurrentIndex(1)
        self.widget.update_stock_selector()
        self.widget.stock_selector.setCurrentIndex(1)
        with patch.object(QMessageBox, 'warning') as mock_warning:
            self.widget.update_chart()
            mock_warning.assert_called_once()
            self.assertEqual(mock_warning.call_args[0][0], self.widget)
            self.assertEqual(mock_warning.call_args[0][1], "Error")
            self.assertIn("No data available", mock_warning.call_args[0][2])

    @patch('src.ui.widgets.stock_chart.StockDataProvider.fetch_stock_data')
    def test_update_chart_exception(self, mock_fetch_data):
        """
        Test updating the chart when an exception occurs during data fetching.
        """
        mock_fetch_data.side_effect = StockDataException("Test error")
        self.widget.portfolio_selector.setCurrentIndex(1)
        self.widget.update_stock_selector()
        self.widget.stock_selector.setCurrentIndex(1)
        with patch.object(QMessageBox, 'warning') as mock_warning:
            self.widget.update_chart()
            mock_warning.assert_called_once()
            self.assertEqual(mock_warning.call_args[0][0], self.widget)
            self.assertEqual(mock_warning.call_args[0][1], "Error")
            self.assertEqual(mock_warning.call_args[0][2], "Test error")

if __name__ == '__main__':
    unittest.main()