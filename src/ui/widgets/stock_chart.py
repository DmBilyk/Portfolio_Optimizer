from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QMessageBox, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import yfinance as yf
from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates
import numpy as np



class StockChartWidget(QWidget):
    def __init__(self, portfolio_manager, stock_manager):
        super().__init__()
        self.portfolio_manager = portfolio_manager
        self.stock_manager = stock_manager
        self.annotation = None
        self.current_data = None

        self.layout = QVBoxLayout()


        self.portfolio_selector = QComboBox()
        self.portfolio_selector.addItem("Select Portfolio")
        self.load_portfolios()
        self.portfolio_selector.currentIndexChanged.connect(self.update_stock_selector)


        self.stock_selector = QComboBox()
        self.stock_selector.addItem("Select Stock")
        self.stock_selector.setEnabled(False)


        self.period_selector = QComboBox()
        self.period_selector.addItems(['1MO', '3MO', '6MO', '1Y', '2Y'])
        self.period_selector.currentTextChanged.connect(self.update_chart)


        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.update_chart)


        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Portfolio:"))
        controls_layout.addWidget(self.portfolio_selector)
        controls_layout.addWidget(QLabel("Stock:"))
        controls_layout.addWidget(self.stock_selector)
        controls_layout.addWidget(QLabel("Period:"))
        controls_layout.addWidget(self.period_selector)
        controls_layout.addWidget(self.refresh_button)


        plt.style.use('seaborn-v0_8-darkgrid')
        self.figure = plt.figure(figsize=(10, 6))
        self.ax = self.figure.add_subplot(111)


        self.ax.set_facecolor('#f0f0f0')
        self.figure.patch.set_facecolor('white')

        self.canvas = FigureCanvas(self.figure)


        self.canvas.mpl_connect('motion_notify_event', self.on_hover)


        self.layout.addLayout(controls_layout)
        self.layout.addWidget(self.canvas)

        self.setLayout(self.layout)


        self.portfolio_selector.currentIndexChanged.connect(self.update_stock_selector)
        self.stock_selector.currentIndexChanged.connect(self.update_chart)

    def load_portfolios(self):
        portfolios = self.portfolio_manager.get_all_portfolios()
        self.portfolio_selector.clear()
        self.portfolio_selector.addItem("Select Portfolio")
        for port_id, name in portfolios:
            self.portfolio_selector.addItem(name, port_id)

    def update_stock_selector(self):
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

    def on_hover(self, event):
        if event.inaxes != self.ax or self.current_data is None:
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

    def update_chart(self):
        if (self.portfolio_selector.currentIndex() <= 0 or
                self.stock_selector.currentIndex() <= 0):
            return

        stock = self.stock_selector.currentText()
        period = self.period_selector.currentText()

        try:
            ticker = yf.Ticker(stock)
            hist = ticker.history(period=period)

            # Check if we received valid data
            if hist.empty or len(hist) == 0:
                QMessageBox.warning(self, "Error", f"No data available for {stock} for the selected period.")
                return

            # Check if 'Close' column exists and has data
            if 'Close' not in hist.columns or hist['Close'].empty:
                QMessageBox.warning(self, "Error", f"Price data missing for {stock}.")
                return

            self.current_data = hist

            self.ax.clear()

            # Only plot if we have valid data with matching dimensions
            if len(hist.index) > 0 and len(hist['Close']) > 0 and len(hist.index) == len(hist['Close']):
                self.ax.plot(hist.index, hist['Close'],
                             label='Close Price',
                             color='#2196F3',
                             linewidth=2)

                self.ax.scatter(hist.index, hist['Close'],
                                color='#2196F3',
                                s=10,
                                alpha=0.0)

                # Change the title format to match the expected format in the test
                self.ax.set_title(f"{stock} - Price Dynamics",
                                  fontsize=16,
                                  fontweight='bold',
                                  pad=20)

                self.ax.set_xlabel('Date',
                                   fontsize=12,
                                   fontweight='bold',
                                   labelpad=10)

                self.ax.set_ylabel('Price (USD)',
                                   fontsize=12,
                                   fontweight='bold',
                                   labelpad=10)

                self.ax.grid(True,
                             linestyle='--',
                             alpha=0.7,
                             color='#757575')

                self.ax.legend(facecolor='white',
                               framealpha=1,
                               shadow=True)

                self.ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
                self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
                plt.xticks(rotation=45, ha='right')

                self.figure.tight_layout(pad=2.0)

                self.annotation = None

                self.canvas.draw()
            else:
                QMessageBox.warning(self, "Error", "Invalid data dimensions for plotting.")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not fetch stock data: {str(e)}")
