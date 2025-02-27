from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QSpinBox, QComboBox, QPushButton, QMessageBox, QFrame,
    QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt
import numpy as np
from scipy.optimize import minimize


class MetricCard(QFrame):
    def __init__(self, title, value, suffix="", parent=None):
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
    def __init__(self, stock_data, parent=None):
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
    def __init__(self, portfolio_manager, stock_manager, market_data):
        super().__init__()
        self.portfolio_manager = portfolio_manager
        self.stock_manager = stock_manager
        self.market_data = market_data



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
        self.current_prices = {}

        self.load_portfolios()





    def setup_input_field(self, layout, label_text, widget, row):
        label = QLabel(label_text)
        layout.addWidget(label, row, 0)
        layout.addWidget(widget, row, 1)

    def clear_results(self):

        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def display_results(self, stock_data, optimal_portfolio, total_invested, investment, remaining):
        self.clear_results()


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


        stocks_label = QLabel("Portfolio Allocation")
        stocks_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333333; padding-top: 20px;")
        self.results_layout.addWidget(stocks_label)

        stocks_grid = QGridLayout()
        stocks_grid.setSpacing(10)

        for i, stock in enumerate(stock_data):
            stock_card = StockCard(stock)
            stocks_grid.addWidget(stock_card, i // 2, i % 2)

        self.results_layout.addLayout(stocks_grid)


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
        portfolios = self.portfolio_manager.get_all_portfolios()
        self.portfolio_selector.clear()
        self.portfolio_selector.addItem("Select Portfolio")
        for port_id, name in portfolios:
            self.portfolio_selector.addItem(name, port_id)

    def optimize_portfolio(self):
        investment = self.investment_amount.value()
        risk = self.risk_level.currentText()
        period = self.investment_period.value()


        stock_symbols = self.market_data.get_all_stock_symbols()
        returns_data = self.market_data.get_historical_returns(stock_symbols)
        self.current_prices = self.market_data.get_current_prices(stock_symbols)

        optimizer = MarkowitzOptimizer(stock_symbols, returns_data, risk_level=risk, investment_period=period)

        try:
            optimal_portfolio = optimizer.optimize_portfolio()


            min_investment_usage = 0.90
            max_investment_usage = 1.02

            stock_data = []
            total_invested = 0


            for symbol, weight in optimal_portfolio['weights'].items():
                target_amount = weight * investment
                price = self.current_prices[symbol]


                shares = int(target_amount / price)
                actual_amount = shares * price

                if shares > 0:
                    stock_data.append({
                        'symbol': symbol,
                        'shares': shares,
                        'price': price,
                        'amount': actual_amount,
                        'weight': weight
                    })
                    total_invested += actual_amount


            while total_invested < investment * min_investment_usage:
                stock_data.sort(key=lambda x: x['weight'], reverse=True)
                added_shares = False

                for stock in stock_data:
                    potential_addition = total_invested + stock['price']


                    if potential_addition <= investment * max_investment_usage:
                        stock['shares'] += 1
                        stock['amount'] = stock['shares'] * stock['price']
                        total_invested = sum(s['amount'] for s in stock_data)
                        added_shares = True
                        break

                if not added_shares or total_invested >= investment * max_investment_usage:
                    break


            if total_invested > investment * max_investment_usage:

                stock_data.sort(key=lambda x: x['weight'])
                for stock in stock_data:
                    while (total_invested > investment * max_investment_usage and
                           stock['shares'] > 0):
                        stock['shares'] -= 1
                        stock['amount'] = stock['shares'] * stock['price']
                        total_invested = sum(s['amount'] for s in stock_data)
                    if total_invested <= investment * max_investment_usage:
                        break


            for stock in stock_data:
                stock['weight'] = stock['amount'] / total_invested


            result = f"Оптимізований портфель (Сума інвестицій: ${total_invested:.2f}):\n"
            result += f"Використання коштів: {(total_invested / investment) * 100:.1f}%\n"
            result += f"Очікувана доходність: {optimal_portfolio['expected_return']:.2%}\n"
            result += f"Волатильність: {optimal_portfolio['volatility']:.2%}\n"
            result += f"Коефіцієнт Шарпа: {optimal_portfolio['sharpe_ratio']:.2f}\n\n"

            for stock in stock_data:
                result += f"{stock['symbol']}:\n"
                result += f"  Кількість акцій: {stock['shares']}\n"
                result += f"  Поточна ціна: ${stock['price']:.2f}\n"
                result += f"  Сума інвестицій: ${stock['amount']:.2f}\n"
                result += f"  Вага в портфелі: {stock['weight']:.2%}\n\n"

            remaining = investment - total_invested
            if remaining > 0:
                result += f"\nЗалишок коштів: ${remaining:.2f}"
            elif remaining < 0:
                result += f"\nПеревищення бюджету: ${-remaining:.2f}"

            self.display_results(stock_data, optimal_portfolio, total_invested, investment, remaining)
            self.optimized_stocks = stock_data
            self.add_to_portfolio_button.setEnabled(True)

        except Exception as e:
            self.results.setText(f"Error optimization: {str(e)}")

    def add_optimized_stocks(self):
        if not self.optimized_stocks:
            QMessageBox.warning(self, "Error", "Please optimize portfolio first.")
            return

        portfolio_index = self.portfolio_selector.currentIndex()
        if portfolio_index <= 0:
            QMessageBox.warning(self, "Error", "Please select a portfolio.")
            return

        portfolio_id = self.portfolio_selector.currentData()

        added_count = 0
        for stock in self.optimized_stocks:
            try:

                self.stock_manager.add_stock(
                    portfolio_id,
                    stock['symbol'],
                    stock['shares'],
                    stock['price']
                )
                added_count += 1
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to add {stock['symbol']}: {str(e)}"
                )

        if added_count > 0:
            QMessageBox.information(self, "Success", f"{added_count} stocks added to portfolio.")
        else:
            QMessageBox.warning(self, "Warning", "No stocks could be added.")

        self.add_to_portfolio_button.setEnabled(False)
        self.optimized_stocks = None


class MarkowitzOptimizer:
    def __init__(self, stock_symbols, returns_data, risk_level='Medium', investment_period=12):
        self.stock_symbols = stock_symbols
        self.returns_data = returns_data
        self.risk_level = risk_level
        self.investment_period = investment_period


        self.risk_params = {
            'Low': {
                'max_weight': 0.15,
                'min_stocks': 8,
                'risk_aversion': 1.5,
                'volatility_penalty': 1.5
            },
            'Medium': {
                'max_weight': 0.25,
                'min_stocks': 5,
                'risk_aversion': 1.0,
                'volatility_penalty': 1.0
            },
            'High': {
                'max_weight': 0.35,
                'min_stocks': 3,
                'risk_aversion': 0.5,
                'volatility_penalty': 0.5
            }
        }


        self.adjust_for_investment_period()

    def adjust_for_investment_period(self):

        if self.investment_period > 36:
            self.risk_params[self.risk_level]['risk_aversion'] *= 0.8
            self.risk_params[self.risk_level]['volatility_penalty'] *= 0.8
        elif self.investment_period < 6:
            self.risk_params[self.risk_level]['risk_aversion'] *= 1.5
            self.risk_params[self.risk_level]['volatility_penalty'] *= 1.5
            self.risk_params[self.risk_level]['max_weight'] *= 0.8
            self.risk_params[self.risk_level]['min_stocks'] += 2

    def calculate_portfolio_performance(self, weights):

        if self.investment_period > 24:
            returns = self.returns_data.rolling(window=24).mean()
        else:
            returns = self.returns_data.rolling(window=12).mean()

        mean_returns = returns.mean()
        cov_matrix = self.returns_data.cov()

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
            exp_return, exp_volatility = self.calculate_portfolio_performance(weights)


            risk_adjustment = params['risk_aversion']
            volatility_penalty = exp_volatility * params['volatility_penalty']
            concentration_penalty = np.sum(weights ** 2) * 0.5


            if self.investment_period > 24:
                return -(exp_return - risk_free_rate -
                         volatility_penalty * risk_adjustment * 0.8 -
                         concentration_penalty)
            else:
                return -(exp_return - risk_free_rate -
                         volatility_penalty * risk_adjustment -
                         concentration_penalty)

        optimized = minimize(
            objective_function,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if optimized.success:
            optimal_weights = optimized.x
            exp_return, exp_volatility = self.calculate_portfolio_performance(optimal_weights)
            sharpe_ratio = (exp_return - 0.02) / exp_volatility


            filtered_weights = {
                symbol: weight
                for symbol, weight in zip(self.stock_symbols, optimal_weights)
                if weight > 0.01
            }

            return {
                'weights': filtered_weights,
                'expected_return': exp_return,
                'volatility': exp_volatility,
                'sharpe_ratio': sharpe_ratio,
                'risk_level': self.risk_level,
                'investment_period': self.investment_period
            }
        else:
            raise ValueError("Optimization failed.")