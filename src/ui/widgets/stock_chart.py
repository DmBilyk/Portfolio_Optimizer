from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QMessageBox, QPushButton # pylint: disable=no-name-in-module
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import yfinance as yf
from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple, Callable
import pandas as pd


@dataclass
class ChartConfig:
    """Configuration for chart appearance and behavior"""
    title_format: str = "{symbol} - Price Dynamics"
    title_fontsize: int = 16
    title_fontweight: str = 'bold'
    title_pad: int = 20

    xlabel: str = 'Date'
    xlabel_fontsize: int = 12
    xlabel_fontweight: str = 'bold'
    xlabel_pad: int = 10

    ylabel: str = 'Price (USD)'
    ylabel_fontsize: int = 12
    ylabel_fontweight: str = 'bold'
    ylabel_pad: int = 10

    line_color: str = '#2196F3'
    line_width: int = 2

    grid_style: str = '--'
    grid_alpha: float = 0.7
    grid_color: str = '#757575'

    hover_enabled: bool = True


class StockDataProvider:
    """Class responsible for fetching stock data"""

    @staticmethod
    def fetch_stock_data(symbol: str, period: str) -> Optional[pd.DataFrame]:
        """Fetch stock data from yfinance API"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if hist.empty or len(hist) == 0:
                return None

            if 'Close' not in hist.columns or hist['Close'].empty:
                return None

            return hist
        except Exception as e:
            raise StockDataException(f"Could not fetch stock data: {str(e)}")


class StockDataException(Exception):
    """Exception raised for errors in the stock data fetching process"""
    pass


class ChartRenderer:
    """Responsible for rendering the chart with stock data"""

    def __init__(self, figure, ax, canvas, config: ChartConfig = ChartConfig()):
        self.figure = figure
        self.ax = ax
        self.canvas = canvas
        self.config = config
        self.annotation = None
        self.current_data = None

    def render(self, data: pd.DataFrame, symbol: str) -> None:
        """Render the chart with the provided data"""
        if data is None or data.empty:
            return

        self.current_data = data
        self.ax.clear()


        self._plot_price_data(data)


        self._configure_chart_appearance(symbol)


        self._configure_axes()


        self.figure.tight_layout(pad=2.0)
        self.annotation = None
        self.canvas.draw()

    def _plot_price_data(self, data: pd.DataFrame) -> None:
        """Plot the price data on the chart"""
        self.ax.plot(
            data.index, data['Close'],
            label='Close Price',
            color=self.config.line_color,
            linewidth=self.config.line_width
        )


        self.ax.scatter(
            data.index, data['Close'],
            color=self.config.line_color,
            s=10,
            alpha=0.0
        )

    def _configure_chart_appearance(self, symbol: str) -> None:
        """Configure the appearance of the chart"""

        self.ax.set_title(
            self.config.title_format.format(symbol=symbol),
            fontsize=self.config.title_fontsize,
            fontweight=self.config.title_fontweight,
            pad=self.config.title_pad
        )


        self.ax.set_xlabel(
            self.config.xlabel,
            fontsize=self.config.xlabel_fontsize,
            fontweight=self.config.xlabel_fontweight,
            labelpad=self.config.xlabel_pad
        )


        self.ax.set_ylabel(
            self.config.ylabel,
            fontsize=self.config.ylabel_fontsize,
            fontweight=self.config.ylabel_fontweight,
            labelpad=self.config.ylabel_pad
        )


        self.ax.grid(
            True,
            linestyle=self.config.grid_style,
            alpha=self.config.grid_alpha,
            color=self.config.grid_color
        )


        self.ax.legend(
            facecolor='white',
            framealpha=1,
            shadow=True
        )

    def _configure_axes(self) -> None:
        """Configure the axes formatting"""
        self.ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha='right')

    def handle_hover(self, event) -> None:
        """Handle mouse hover events on the chart"""
        if not self.config.hover_enabled or event.inaxes != self.ax or self.current_data is None:
            if self.annotation:
                self.annotation.set_visible(False)
                self.canvas.draw_idle()
            return

        x_data = mdates.date2num(self.current_data.index)
        y_data = self.current_data['Close'].values


        x_dist = np.abs(x_data - event.xdata)
        closest_idx = np.argmin(x_dist)


        max_distance = (x_data[-1] - x_data[0]) / len(x_data) * 2
        if x_dist[closest_idx] > max_distance:
            if self.annotation:
                self.annotation.set_visible(False)
                self.canvas.draw_idle()
            return

        date = self.current_data.index[closest_idx]
        price = y_data[closest_idx]


        if self.annotation:
            self.annotation.set_visible(False)


        text = f'Date: {date.strftime("%Y-%m-%d")}\nPrice: ${price:.2f}'


        self.annotation = self.ax.annotate(
            text,
            xy=(mdates.date2num(date), price),
            xytext=(10, 10), textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='gray', alpha=0.8),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
        )

        self.canvas.draw_idle()


class StockChartWidget(QWidget):
    """Widget for displaying stock charts with portfolio integration"""

    def __init__(self, portfolio_manager, stock_manager):
        super().__init__()
        self.portfolio_manager = portfolio_manager
        self.stock_manager = stock_manager


        self._init_ui()


        self._init_chart()


        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize the UI components"""
        self.layout = QVBoxLayout()


        self.portfolio_selector = QComboBox()
        self.portfolio_selector.addItem("Select Portfolio")

        self.stock_selector = QComboBox()
        self.stock_selector.addItem("Select Stock")
        self.stock_selector.setEnabled(False)

        self.period_selector = QComboBox()
        self.period_selector.addItems(['1MO', '3MO', '6MO', '1Y', '2Y'])

        self.refresh_button = QPushButton("Refresh")


        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Portfolio:"))
        controls_layout.addWidget(self.portfolio_selector)
        controls_layout.addWidget(QLabel("Stock:"))
        controls_layout.addWidget(self.stock_selector)
        controls_layout.addWidget(QLabel("Period:"))
        controls_layout.addWidget(self.period_selector)
        controls_layout.addWidget(self.refresh_button)


        self.layout.addLayout(controls_layout)


        self.load_portfolios()

    def _init_chart(self) -> None:
        """Initialize the chart components"""

        plt.style.use('seaborn-v0_8-darkgrid')
        self.figure = plt.figure(figsize=(10, 6))
        self.ax = self.figure.add_subplot(111)


        self.ax.set_facecolor('#f0f0f0')
        self.figure.patch.set_facecolor('white')


        self.canvas = FigureCanvas(self.figure)


        self.chart_renderer = ChartRenderer(self.figure, self.ax, self.canvas)


        self.layout.addWidget(self.canvas)


        self.setLayout(self.layout)

    def _connect_signals(self) -> None:
        """Connect signals to slots"""
        self.portfolio_selector.currentIndexChanged.connect(self.update_stock_selector)
        self.stock_selector.currentIndexChanged.connect(self.update_chart)
        self.period_selector.currentTextChanged.connect(self.update_chart)
        self.refresh_button.clicked.connect(self.update_chart)
        self.canvas.mpl_connect('motion_notify_event', self._on_hover)

    def load_portfolios(self) -> None:
        """Load portfolios into the portfolio selector"""
        portfolios = self.portfolio_manager.get_all_portfolios()
        self.portfolio_selector.clear()
        self.portfolio_selector.addItem("Select Portfolio")
        for port_id, name in portfolios:
            self.portfolio_selector.addItem(name, port_id)

    def update_stock_selector(self) -> None:
        """Update the stock selector based on the selected portfolio"""
        self.stock_selector.clear()
        self.stock_selector.addItem("Select Stock")

        current_index = self.portfolio_selector.currentIndex()
        if current_index <= 0:
            self.stock_selector.setEnabled(False)
            return

        portfolio_id = self.portfolio_selector.currentData()
        stocks = self.stock_manager.get_portfolio_stocks(portfolio_id)

        for _, symbol, _, _ in stocks:
            self.stock_selector.addItem(symbol)

        self.stock_selector.setEnabled(True)

    def _on_hover(self, event) -> None:
        """Handle hover events on the chart"""
        self.chart_renderer.handle_hover(event)

    def update_chart(self) -> None:
        """Update the chart with data for the selected stock and period"""
        if (self.portfolio_selector.currentIndex() <= 0 or
                self.stock_selector.currentIndex() <= 0):
            return

        stock = self.stock_selector.currentText()
        period = self.period_selector.currentText()

        try:

            data = StockDataProvider.fetch_stock_data(stock, period)


            if data is None:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"No data available for {stock} for the selected period."
                )
                return


            self.chart_renderer.render(data, stock)

        except StockDataException as e:
            QMessageBox.warning(self, "Error", str(e))