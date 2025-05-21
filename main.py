import sys
import traceback
import os
import logging
from datetime import datetime

# Налаштування логування
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, "portfolio_app_log.txt")
logging.basicConfig(filename=log_file, level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    """
    The main entry point for the application.
    """
    try:
        logging.info("Application starting")

        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        logging.info("PySide6 modules imported")

        if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

        app = QApplication(sys.argv)
        logging.info("QApplication created")

        from src.data.database import Database
        from src.domain.portfolio_manager import PortfolioManager
        from src.domain.stock import StockManager
        from src.services.market_data import MarketData
        logging.info("Business logic modules imported")

        db = Database()
        logging.info("Database initialized")

        portfolio_manager = PortfolioManager(db)
        stock_manager = StockManager(db)
        market_data = MarketData()
        logging.info("Managers initialized")

        # Setup demo data
        tech_portfolio_id = portfolio_manager.create_portfolio("Tech Portfolio")
        dividend_portfolio_id = portfolio_manager.create_portfolio("Dividend Portfolio")
        logging.info("Portfolios created")

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
        logging.info("Demo data setup complete")

        app.setStyle("Fusion")
        logging.info("Style set to Fusion")

        from src.ui.main_window import MainWindow
        logging.info("MainWindow module imported")

        window = MainWindow(portfolio_manager, stock_manager, market_data)
        logging.info("MainWindow instance created")

        window.show()
        logging.info("Window show called")

        return app.exec()

    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        logging.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    try:
        logging.info("Script starting")
        sys.exit(main())
    except Exception as e:
        logging.error(f"Uncaught exception: {str(e)}")
        logging.error(traceback.format_exc())