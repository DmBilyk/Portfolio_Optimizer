"""
Main window for the Enhanced Stock Portfolio Manager application.
This module implements the UI for managing stock portfolios.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QMessageBox, QInputDialog, QFrame, QListWidget, QListWidgetItem # pylint: disable=no-name-in-module
)
from PySide6.QtCore import Qt # pylint: disable=no-name-in-module
from src.ui.widgets.stock_chart import StockChartWidget # pylint: disable=no-name-in-module
from src.ui.widgets.portfolio_optimizer import PortfolioOptimizerWidget # pylint: disable=no-name-in-module
from src.services.portfolio_service import PortfolioService # pylint: disable=no-name-in-module




class MainWindow(QMainWindow):
    """
    Main application window for the Enhanced Stock Portfolio Manager.
    Provides interfaces for portfolio management, stock charts, and portfolio optimization.
    """

    def __init__(self, portfolio_manager, stock_manager, market_data):
        """
        Initialize the main window with managers and UI setup.

        Args:
            portfolio_manager: Manager for portfolio operations
            stock_manager: Manager for stock operations
            market_data: Provider for market data
        """
        super().__init__()
        self.portfolio_manager = portfolio_manager
        self.stock_manager = stock_manager
        self.market_data = market_data
        self.current_portfolio_id = None

        # UI components initialized here to avoid pylint warnings
        self.tabs = None
        self.portfolio_list = None
        self.stock_table = None
        self.add_stock_btn = None
        self.delete_stock_btn = None
        self.refresh_btn = None

        self.setWindowTitle("Enhanced Stock Portfolio Manager")
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        """Set up the main UI components and layout."""
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        portfolio_tab = QWidget()
        portfolio_layout = QHBoxLayout(portfolio_tab)

        left_panel = self.setup_portfolio_list_panel()
        right_panel = self.setup_stock_list_panel()

        portfolio_layout.addWidget(left_panel, 1)
        portfolio_layout.addWidget(right_panel, 2)

        charts_tab = StockChartWidget(self.portfolio_manager, self.stock_manager)

        portfolio_service = PortfolioService(
            self.portfolio_manager, self.stock_manager, self.market_data
        )
        optimizer_tab = PortfolioOptimizerWidget(
            portfolio_service
        )

        self.tabs.addTab(portfolio_tab, "Portfolio Management")
        self.tabs.addTab(charts_tab, "Stock Charts")
        self.tabs.addTab(optimizer_tab, "Portfolio Optimizer")

        self.tabs.currentChanged.connect(self.update_current_tab)

    def update_current_tab(self, index):
        """
        Update the current tab when switched.

        Args:
            index: The index of the tab that was selected
        """
        current_widget = self.tabs.widget(index)

        if hasattr(current_widget, 'load_portfolios'):
            current_widget.load_portfolios()

    def setup_portfolio_list_panel(self):
        """
        Set up the portfolio list panel on the left side.

        Returns:
            QFrame: The portfolio list panel
        """
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)

        header = QLabel("Portfolios")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")

        self.portfolio_list = QListWidget()
        self.portfolio_list.itemClicked.connect(self.on_portfolio_selected)

        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Portfolio")
        add_btn.clicked.connect(self.add_portfolio)

        delete_btn = QPushButton("Delete Portfolio")
        delete_btn.clicked.connect(self.delete_portfolio)

        button_layout.addWidget(add_btn)
        button_layout.addWidget(delete_btn)

        layout.addWidget(header)
        layout.addWidget(self.portfolio_list)
        layout.addLayout(button_layout)

        self.refresh_portfolios()
        return panel

    def setup_stock_list_panel(self):
        """
        Set up the stock list panel on the right side.

        Returns:
            QFrame: The stock list panel
        """
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)

        header = QLabel("Stocks")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")

        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(5)
        self.stock_table.setHorizontalHeaderLabels([
            "ID", "Symbol", "Quantity", "Purchase Price", "Current Price"
        ])
        self.stock_table.setColumnHidden(0, True)

        self.stock_table.setSelectionMode(QTableWidget.MultiSelection)
        self.stock_table.setSelectionBehavior(QTableWidget.SelectRows)

        controls_layout = QHBoxLayout()
        self.add_stock_btn = QPushButton("Add Stock")
        self.add_stock_btn.clicked.connect(self.add_stock)
        self.add_stock_btn.setEnabled(False)

        self.delete_stock_btn = QPushButton("Delete Stock")
        self.delete_stock_btn.clicked.connect(self.delete_stock)
        self.delete_stock_btn.setEnabled(False)

        self.refresh_btn = QPushButton("Refresh Prices")
        self.refresh_btn.clicked.connect(self.refresh_stocks)

        controls_layout.addWidget(self.add_stock_btn)
        controls_layout.addWidget(self.delete_stock_btn)
        controls_layout.addWidget(self.refresh_btn)

        layout.addWidget(header)
        layout.addWidget(self.stock_table)
        layout.addLayout(controls_layout)

        return panel

    def delete_stock(self):
        """Delete selected stocks from the current portfolio."""
        if self.current_portfolio_id is None:
            QMessageBox.warning(self, "Error", "Please select a portfolio first.")
            return

        selected_rows = self.stock_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Please select stock(s) to delete.")
            return

        msg = f"Are you sure you want to delete {len(selected_rows)} stock(s)?"
        reply = QMessageBox.question(
            self, 'Delete Stock', msg, QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                deleted_count = 0
                for row in selected_rows:
                    stock_id = int(self.stock_table.item(row.row(), 0).text())
                    if self.stock_manager.remove_stock(stock_id):
                        deleted_count += 1

                self.refresh_stocks()
                QMessageBox.information(
                    self, "Success", f"{deleted_count} stock(s) deleted successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not delete stock(s): {str(e)}"
                )

    def delete_portfolio(self):
        """Delete the currently selected portfolio."""
        if self.current_portfolio_id is None:
            QMessageBox.warning(self, "Error", "Please select a portfolio to delete.")
            return

        reply = QMessageBox.question(
            self, 'Delete Portfolio',
            "Are you sure you want to delete this portfolio?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.portfolio_manager.delete_portfolio(self.current_portfolio_id)
                self.refresh_portfolios()

                self.current_portfolio_id = None
                self.add_stock_btn.setEnabled(False)
                self.delete_stock_btn.setEnabled(False)

                self.stock_table.setRowCount(0)

                QMessageBox.information(self, "Success", "Portfolio deleted successfully.")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not delete portfolio: {str(e)}"
                )

    def refresh_portfolios(self):
        """Refresh the list of portfolios."""
        self.portfolio_list.clear()
        portfolios = self.portfolio_manager.get_all_portfolios()
        for port_id, name in portfolios:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, port_id)
            self.portfolio_list.addItem(item)

    def refresh_stocks(self):
        """Refresh the stocks in the current portfolio with updated market prices."""
        if self.current_portfolio_id is None:
            return

        stocks = self.stock_manager.get_portfolio_stocks(self.current_portfolio_id)
        self.stock_table.setRowCount(len(stocks))

        for row, (stock_id, symbol, quantity, price) in enumerate(stocks):
            try:
                market_info = self.market_data.get_stock_info(symbol)
                current_price = market_info.get("current_price", "N/A")
            except Exception:
                current_price = "N/A"

            self.stock_table.setItem(row, 0, QTableWidgetItem(str(stock_id)))
            self.stock_table.setItem(row, 1, QTableWidgetItem(symbol))
            self.stock_table.setItem(row, 2, QTableWidgetItem(str(quantity)))
            self.stock_table.setItem(row, 3, QTableWidgetItem(f"${price:.2f}"))

            price_text = (f"${current_price:.2f}"
                          if isinstance(current_price, (int, float))
                          else current_price)
            self.stock_table.setItem(row, 4, QTableWidgetItem(price_text))

    def add_portfolio(self):
        """Add a new portfolio."""
        name, ok = QInputDialog.getText(self, "New Portfolio", "Enter portfolio name:")
        if ok and name:
            self.portfolio_manager.create_portfolio(name)
            self.refresh_portfolios()

    def add_stock(self):
        """Add a new stock to the current portfolio."""
        if self.current_portfolio_id is None:
            return

        symbol, ok = QInputDialog.getText(self, "Add Stock", "Enter stock symbol:")
        if not ok or not symbol:
            return

        quantity, ok = QInputDialog.getInt(self, "Add Stock", "Enter quantity:", 1, 1)
        if not ok:
            return

        price, ok = QInputDialog.getDouble(self, "Add Stock", "Enter purchase price:", 0.01, 0.01)
        if not ok:
            return

        self.stock_manager.add_stock(self.current_portfolio_id, symbol.upper(), quantity, price)
        self.refresh_stocks()

    def on_portfolio_selected(self, item):
        """
        Handle selection of a portfolio.

        Args:
            item: The selected QListWidgetItem
        """
        self.current_portfolio_id = item.data(Qt.UserRole)
        self.add_stock_btn.setEnabled(True)
        self.delete_stock_btn.setEnabled(True)
        self.refresh_stocks()

    def apply_styles(self):
        """Apply CSS styles to the application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QFrame {
                background-color: #262626;
                border-radius: 4px;
            }
            QListWidget {
                background-color: #262626;
                border: 1px solid #333;
                color: #e0e0e0;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #2c3e50;  /* Match the button color */
                color: #ecf0f1;
                border-radius: 3px;
            }

            QListWidget::item:hover {
                background-color: #34495e;  /* Match the button hover color */
            }
            QTableWidget {
                background-color: #262626;
                alternate-background-color: #2d2d2d;
                border: 1px solid #333;
                font-size: 13px;
                gridline-color: #333;
            }
            QTableWidget QHeaderView::section {
                background-color: #333;
                color: #e0e0e0;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                color: #e0e0e0;
                border-bottom: 1px solid #333;
            }
            QTableWidget::item:selected {
                background-color: #00BCD4;
                color: white;
            }
            QPushButton {
                background-color: #2c3e50;  
                color: #ecf0f1;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
                min-width: 80px;
                font-size: 13px;
            }

            QPushButton:hover {
                background-color: #34495e;
            }

            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666;
            }

            QTabBar::tab:selected {
                background: #2c3e50;  /* Match the button color for consistency */
                color: #ecf0f1;
            }
            QLabel {
                color: #e0e0e0;
                font-weight: 500;
                font-size: 14px;
            }
            QTabWidget::pane {
                border: 1px solid #333;
                background: #262626;
            }
            QTabBar::tab {
                background: #333;
                padding: 8px 16px;
                color: #e0e0e0;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QScrollBar:vertical {
                width: 10px;
                background: #262626;
            }
            QScrollBar::handle:vertical {
                background: #666;
                min-height: 20px;
            }
        """)

        self.stock_table.verticalHeader().setVisible(False)
        self.stock_table.horizontalHeader().setStretchLastSection(True)
        self.stock_table.setSortingEnabled(True)
        self.stock_table.setAlternatingRowColors(True)
        self.stock_table.setColumnWidth(1, 100)
        self.stock_table.setColumnWidth(2, 80)
        self.stock_table.setColumnWidth(3, 120)

        self.portfolio_list.setSpacing(3)
        self.portfolio_list.setUniformItemSizes(True)