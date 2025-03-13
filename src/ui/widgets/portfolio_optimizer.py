from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QSpinBox, QComboBox, QPushButton, QMessageBox, QFrame,
    QScrollArea, QGridLayout
) # pylint: disable=no-name-in-module
from PySide6.QtCore import Qt # pylint: disable=no-name-in-module


class MetricCard(QFrame):
    """
    A class to represent a metric card in the UI.

    Attributes:
    title (str): The title of the metric.
    value (str): The value of the metric.
    suffix (str): The suffix to append to the value.
    parent (QWidget): The parent widget.
    """

    def __init__(self, title, value, suffix="", parent=None):
        """
        Constructs all the necessary attributes for the MetricCard object.

        Parameters:
        title (str): The title of the metric.
        value (str): The value of the metric.
        suffix (str): The suffix to append to the value.
        parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-radius: 8px;
                border: 1px solid #333333;
            }
            QLabel {
                color: #E0E0E0;
            }
        """)

        layout = QVBoxLayout(self)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #9E9E9E; font-size: 12px;")

        value_label = QLabel(f"{value}{suffix}")
        value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #E0E0E0; padding: 5px 0;")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.setContentsMargins(15, 10, 15, 10)


class StockCard(QFrame):
    """
    A class to represent a stock card in the UI.

    Attributes:
    stock_data (dict): The data of the stock.
    parent (QWidget): The parent widget.
    """

    def __init__(self, stock_data, parent=None):
        """
        Constructs all the necessary attributes for the StockCard object.

        Parameters:
        stock_data (dict): The data of the stock.
        parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-radius: 8px;
                border: 1px solid #333333;
                margin: 5px;
            }
            QLabel {
                color: #E0E0E0;
            }
        """)

        layout = QGridLayout(self)

        symbol_label = QLabel(stock_data['symbol'])
        symbol_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #64B5F6;")
        layout.addWidget(symbol_label, 0, 0, 1, 2)

        details = [
            ("Shares:", str(stock_data['shares'])),
            ("Price:", f"${stock_data['price']:.2f}"),
            ("Investment:", f"${stock_data['amount']:.2f}"),
            ("Weight:", f"{(stock_data['weight'] * 100):.2f}%")
        ]

        for i, (label, value) in enumerate(details):
            label_widget = QLabel(label)
            label_widget.setStyleSheet("color: #9E9E9E; font-size: 12px;")
            value_widget = QLabel(value)
            value_widget.setStyleSheet("color: #E0E0E0; font-weight: bold;")
            layout.addWidget(label_widget, i + 1, 0)
            layout.addWidget(value_widget, i + 1, 1)

        layout.setContentsMargins(15, 10, 15, 10)


class PortfolioOptimizerWidget(QWidget):
    """
    A class to represent the portfolio optimizer widget in the UI.

    Attributes:
    portfolio_service (object): The service to manage portfolio operations.
    """

    def __init__(self, portfolio_service):
        """
        Constructs all the necessary attributes for the PortfolioOptimizerWidget object.

        Parameters:
        portfolio_service (object): The service to manage portfolio operations.
        """
        super().__init__()
        self.portfolio_service = portfolio_service

        self.setStyleSheet("background-color: #121212;")

        self.layout = QVBoxLayout()
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # Input Section
        input_section = QFrame()
        input_section.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-radius: 8px;
                border: 1px solid #333333;
            }
            QLabel {
                font-size: 13px;
                color: #E0E0E0;
            }
            QPushButton {
                background-color: #2c3e50;;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666;
            }
            QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #424242;
                border-radius: 4px;
                padding: 4px;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background-color: #424242;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #424242;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #E0E0E0;
            }
        """)

        input_layout = QVBoxLayout(input_section)

        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(10)

        self.investment_amount = QDoubleSpinBox()
        self.investment_amount.setRange(1000, 1000000)
        self.investment_amount.setValue(10000)
        self.investment_amount.setPrefix("$ ")
        self.setup_input_field(form_layout, "Investment Amount:", self.investment_amount, 0)

        self.investment_period = QSpinBox()
        self.investment_period.setRange(1, 120)
        self.investment_period.setValue(12)
        self.setup_input_field(form_layout, "Investment Period (months):", self.investment_period, 1)

        self.risk_level = QComboBox()
        self.risk_level.addItems(['Low', 'Medium', 'High'])
        self.setup_input_field(form_layout, "Risk Level:", self.risk_level, 2)

        self.portfolio_selector = QComboBox()
        self.portfolio_selector.addItem("Select Portfolio")
        self.setup_input_field(form_layout, "Add to Portfolio:", self.portfolio_selector, 3)

        input_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.optimize_button = QPushButton("Optimize Portfolio")
        self.optimize_button.clicked.connect(self.optimize_portfolio)
        self.add_to_portfolio_button = QPushButton("Add Optimized Stocks")
        self.add_to_portfolio_button.clicked.connect(self.add_optimized_stocks)
        self.add_to_portfolio_button.setEnabled(False)

        button_layout.addWidget(self.optimize_button)
        button_layout.addWidget(self.add_to_portfolio_button)
        button_layout.setContentsMargins(0, 10, 0, 0)

        input_layout.addLayout(button_layout)

        # Results Scroll Area
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.results_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1E1E1E;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #424242;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                background: none;
            }
        """)

        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setSpacing(20)
        self.results_scroll.setWidget(self.results_widget)

        self.layout.addWidget(input_section)
        self.layout.addWidget(self.results_scroll)

        self.setLayout(self.layout)
        self.optimized_stocks = None

        self.load_portfolios()

    def setup_input_field(self, layout, label_text, widget, row):
        """
        Sets up an input field in the form layout.

        Parameters:
        layout (QGridLayout): The layout to add the input field to.
        label_text (str): The text for the label.
        widget (QWidget): The input widget.
        row (int): The row in the layout to place the input field.
        """
        label = QLabel(label_text)
        layout.addWidget(label, row, 0)
        layout.addWidget(widget, row, 1)

    def clear_results(self):
        """
        Clears the previous results from the results layout.
        """
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def display_results(self, results):
        """
        Displays the optimization results in the results layout.

        Parameters:
        results (dict): The results of the portfolio optimization.
        """
        self.clear_results()

        stock_data = results['stock_data']
        optimal_portfolio = results['optimal_portfolio']
        total_invested = results['total_invested']
        investment = results['investment']
        remaining = results['remaining']

        # Metrics Cards
        metrics_layout = QHBoxLayout()

        metrics = [
            ("Total Investment", f"${total_invested:.2f}", ""),
            ("Investment Usage", f"{(total_invested / investment * 100):.1f}", "%"),
            ("Expected Return", f"{(optimal_portfolio['expected_return'] * 100):.2f}", "%"),
            ("Volatility", f"{(optimal_portfolio['volatility'] * 100):.2f}", "%"),
            ("Sharpe Ratio", f"{optimal_portfolio['sharpe_ratio']:.2f}", "")
        ]

        for title, value, suffix in metrics:
            metrics_layout.addWidget(MetricCard(title, value, suffix))

        self.results_layout.addLayout(metrics_layout)

        # Stocks Grid
        stocks_label = QLabel("Portfolio Allocation")
        stocks_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #E0E0E0; padding-top: 20px;")
        self.results_layout.addWidget(stocks_label)

        stocks_grid = QGridLayout()
        stocks_grid.setSpacing(10)

        for i, stock in enumerate(stock_data):
            stock_card = StockCard(stock)
            stocks_grid.addWidget(stock_card, i // 2, i % 2)

        self.results_layout.addLayout(stocks_grid)

        # Remaining funds
        if remaining != 0:
            remaining_label = QLabel()
            if remaining > 0:
                remaining_label.setText(f"Remaining funds: ${remaining:.2f}")
                remaining_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                remaining_label.setText(f"Budget exceeded by: ${-remaining:.2f}")
                remaining_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.results_layout.addWidget(remaining_label)

        self.results_layout.addStretch()

    def load_portfolios(self):
        """
        Loads the portfolios from the portfolio service and populates the portfolio selector.
        """
        portfolios = self.portfolio_service.get_all_portfolios()
        self.portfolio_selector.clear()
        self.portfolio_selector.addItem("Select Portfolio")
        for port_id, name in portfolios:
            self.portfolio_selector.addItem(name, port_id)

    def optimize_portfolio(self):
        """
        Optimizes the portfolio based on the input parameters and displays the results.
        """
        try:
            investment = self.investment_amount.value()
            risk = self.risk_level.currentText()
            period = self.investment_period.value()

            # Call the service to create optimized portfolio
            results = self.portfolio_service.create_optimized_portfolio(
                investment, risk, period
            )

            self.display_results(results)
            self.optimized_stocks = results['stock_data']
            self.add_to_portfolio_button.setEnabled(True)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Optimization error: {str(e)}")

    def add_optimized_stocks(self):
        """
        Adds the optimized stocks to the selected portfolio.
        """
        if not self.optimized_stocks:
            QMessageBox.warning(self, "Error", "Please optimize portfolio first.")
            return

        portfolio_index = self.portfolio_selector.currentIndex()
        if portfolio_index <= 0:
            QMessageBox.warning(self, "Error", "Please select a portfolio.")
            return

        portfolio_id = self.portfolio_selector.currentData()

        # Call service to add the stocks
        added_count, errors = self.portfolio_service.add_stocks_to_portfolio(
            portfolio_id, self.optimized_stocks
        )

        if added_count > 0:
            QMessageBox.information(self, "Success", f"{added_count} stocks added to portfolio.")
        else:
            QMessageBox.warning(self, "Warning", "No stocks could be added.")

        if errors:
            error_message = "\n".join(errors)
            QMessageBox.warning(self, "Errors", f"Some stocks couldn't be added:\n{error_message}")

        self.add_to_portfolio_button.setEnabled(False)
        self.optimized_stocks = None

        self.load_portfolios()

    def setup_input_field(self, layout, label_text, widget, row):
        label = QLabel(label_text)
        layout.addWidget(label, row, 0)
        layout.addWidget(widget, row, 1)

    def clear_results(self):
        # Clear previous results
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def display_results(self, results):
        self.clear_results()

        stock_data = results['stock_data']
        optimal_portfolio = results['optimal_portfolio']
        total_invested = results['total_invested']
        investment = results['investment']
        remaining = results['remaining']

        # Metrics Cards
        metrics_layout = QHBoxLayout()

        metrics = [
            ("Total Investment", f"${total_invested:.2f}", ""),
            ("Investment Usage", f"{(total_invested / investment * 100):.1f}", "%"),
            ("Expected Return", f"{(optimal_portfolio['expected_return'] * 100):.2f}", "%"),
            ("Volatility", f"{(optimal_portfolio['volatility'] * 100):.2f}", "%"),
            ("Sharpe Ratio", f"{optimal_portfolio['sharpe_ratio']:.2f}", "")
        ]

        for title, value, suffix in metrics:
            metrics_layout.addWidget(MetricCard(title, value, suffix))

        self.results_layout.addLayout(metrics_layout)

        # Stocks Grid
        stocks_label = QLabel("Portfolio Allocation")
        stocks_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #E0E0E0; padding-top: 20px;")
        self.results_layout.addWidget(stocks_label)

        stocks_grid = QGridLayout()
        stocks_grid.setSpacing(10)

        for i, stock in enumerate(stock_data):
            stock_card = StockCard(stock)
            stocks_grid.addWidget(stock_card, i // 2, i % 2)

        self.results_layout.addLayout(stocks_grid)

        # Remaining funds
        if remaining != 0:
            remaining_label = QLabel()
            if remaining > 0:
                remaining_label.setText(f"Remaining funds: ${remaining:.2f}")
                remaining_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                remaining_label.setText(f"Budget exceeded by: ${-remaining:.2f}")
                remaining_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.results_layout.addWidget(remaining_label)

        self.results_layout.addStretch()

    def load_portfolios(self):
        portfolios = self.portfolio_service.get_all_portfolios()
        self.portfolio_selector.clear()
        self.portfolio_selector.addItem("Select Portfolio")
        for port_id, name in portfolios:
            self.portfolio_selector.addItem(name, port_id)

    def optimize_portfolio(self):
        try:
            investment = self.investment_amount.value()
            risk = self.risk_level.currentText()
            period = self.investment_period.value()

            # Call the service to create optimized portfolio
            results = self.portfolio_service.create_optimized_portfolio(
                investment, risk, period
            )

            self.display_results(results)
            self.optimized_stocks = results['stock_data']
            self.add_to_portfolio_button.setEnabled(True)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Optimization error: {str(e)}")

    def add_optimized_stocks(self):
        if not self.optimized_stocks:
            QMessageBox.warning(self, "Error", "Please optimize portfolio first.")
            return

        portfolio_index = self.portfolio_selector.currentIndex()
        if portfolio_index <= 0:
            QMessageBox.warning(self, "Error", "Please select a portfolio.")
            return

        portfolio_id = self.portfolio_selector.currentData()

        # Call service to add the stocks
        added_count, errors = self.portfolio_service.add_stocks_to_portfolio(
            portfolio_id, self.optimized_stocks
        )

        if added_count > 0:
            QMessageBox.information(self, "Success", f"{added_count} stocks added to portfolio.")
        else:
            QMessageBox.warning(self, "Warning", "No stocks could be added.")

        if errors:
            error_message = "\n".join(errors)
            QMessageBox.warning(self, "Errors", f"Some stocks couldn't be added:\n{error_message}")

        self.add_to_portfolio_button.setEnabled(False)
        self.optimized_stocks = None