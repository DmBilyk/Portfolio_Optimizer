import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.data.database import Database
from src.domain.portfolio import PortfolioManager
from src.domain.stock import StockManager
from src.services.market_data import MarketData
from src.ui.main_window import MainWindow

def setup_demo_data(portfolio_manager, stock_manager):
    """
    Sets up demo data for the application.

    Args:
        portfolio_manager (PortfolioManager): The portfolio manager instance.
        stock_manager (StockManager): The stock manager instance.
    """
    tech_portfolio_id = portfolio_manager.create_portfolio("Tech Portfolio")
    dividend_portfolio_id = portfolio_manager.create_portfolio("Dividend Portfolio")

    tech_stocks = [
        ("AAPL", 10, 150.00),
        ("MSFT", 5, 280.00),
        ("GOOGL", 3, 2800.00)
    ]

    for symbol, quantity, price in tech_stocks:
        stock_manager.add_stock(tech_portfolio_id, symbol, quantity, price)

    dividend_stocks = [
        ("KO", 20, 54.00),
        ("JNJ", 8, 170.00),
        ("PG", 12, 140.00)
    ]

    for symbol, quantity, price in dividend_stocks:
        stock_manager.add_stock(dividend_portfolio_id, symbol, quantity, price)

def main():
    """
    The main entry point for the application.
    Sets up the application, initializes the database and managers,
    sets up demo data, and starts the main window.
    """
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)

    db = Database()
    portfolio_manager = PortfolioManager(db)
    stock_manager = StockManager(db)
    market_data = MarketData()

    setup_demo_data(portfolio_manager, stock_manager)

    app.setStyle("Fusion")

    window = MainWindow(portfolio_manager, stock_manager, market_data)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()