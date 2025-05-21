import sqlite3
import os
import sys
from datetime import datetime
from src.data.models import StockMetrics, OptimizedPortfolio


def singleton(cls):
    """Декоратор, що перетворює клас на Singleton."""
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class Database:
    """
    Database handler for portfolio management system.
    Provides methods for storing and retrieving portfolio data, stock metrics,
    and optimized portfolio calculations.

    Implemented using the Singleton pattern to ensure only one database connection
    is active throughout the application.
    """

    def __init__(self, db_name="portfolio.db"):
        """
        Initialize database connection and create necessary tables if not already initialized.

        """
        # Визначаємо шлях до бази даних з урахуванням упакованого додатку
        self.db_path = self._get_db_path(db_name)
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self._create_tables()

    def _get_db_path(self, db_name):
        """
        Get the correct database path based on whether the application
        is running as a script, frozen application, or macOS bundle.



        """

        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):

            if sys.platform == 'darwin':

                app_name = os.path.basename(sys.executable).split('.')[0]
                base_dir = os.path.expanduser(f'~/Library/Application Support/{app_name}')
            else:

                base_dir = os.path.dirname(sys.executable)
        else:

            base_dir = os.path.abspath(os.path.dirname(__file__))


        data_dir = os.path.join(base_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)


        return os.path.join(data_dir, db_name)

    def _create_tables(self):
        """
        Create database tables if they don't exist.
        Handles portfolio, stock, stock_metrics, optimized_portfolio, and optimized_weights tables.
        """
        try:

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                );
            ''')


            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER,
                    symbol TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolio(id),
                    UNIQUE (portfolio_id, symbol)
                );
            ''')


            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    mean_return REAL NOT NULL,
                    volatility REAL NOT NULL,
                    calculation_date DATE NOT NULL,
                    window_size INTEGER NOT NULL,
                    UNIQUE (symbol, calculation_date, window_size)
                );
            ''')


            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimized_portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    risk_level TEXT NOT NULL,
                    investment_period INTEGER NOT NULL,
                    expected_return REAL NOT NULL,
                    volatility REAL NOT NULL,
                    sharpe_ratio REAL NOT NULL,
                    calculation_date DATE NOT NULL,
                    stocks_hash TEXT NOT NULL,
                    UNIQUE (risk_level, investment_period, stocks_hash, calculation_date)
                );
            ''')


            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimized_weights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER,
                    symbol TEXT NOT NULL,
                    weight REAL NOT NULL,
                    FOREIGN KEY (portfolio_id) REFERENCES optimized_portfolio(id),
                    UNIQUE (portfolio_id, symbol)
                );
            ''')

            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def save_stock_metrics(self, metrics):
        """
        Save stock performance metrics to the database.


        """
        try:
            query = '''
                INSERT OR REPLACE INTO stock_metrics 
                (symbol, mean_return, volatility, calculation_date, window_size)
                VALUES (?, ?, ?, ?, ?)
            '''
            params = (
                metrics.symbol,
                metrics.mean_return,
                metrics.volatility,
                metrics.calculation_date,
                metrics.window_size
            )

            self.cursor.execute(query, params)
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error saving stock metrics: {e}")

    def get_stock_metrics(self, symbol, window_size, max_age_days=7):
        """
        Retrieve stock metrics from the database for a specific symbol and window size.


        """
        try:
            query = '''
                SELECT symbol, mean_return, volatility, calculation_date, window_size
                FROM stock_metrics
                WHERE symbol = ? 
                AND window_size = ?
                AND date(calculation_date) >= date('now', ?)
            '''
            params = (symbol, window_size, f'-{max_age_days} days')

            self.cursor.execute(query, params)
            row = self.cursor.fetchone()

            if row:
                return StockMetrics(*row)
            return None
        except sqlite3.Error as e:
            print(f"Error getting stock metrics: {e}")
            return None

    def save_optimized_portfolio(self, portfolio, weights, stocks_hash):
        """
        Save an optimized portfolio and its asset weights to the database.


        """
        try:
            # Insert the portfolio record
            portfolio_query = '''
                INSERT INTO optimized_portfolio 
                (risk_level, investment_period, expected_return, volatility, 
                 sharpe_ratio, calculation_date, stocks_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            portfolio_params = (
                portfolio.risk_level,
                portfolio.investment_period,
                portfolio.expected_return,
                portfolio.volatility,
                portfolio.sharpe_ratio,
                datetime.now().date(),
                stocks_hash
            )

            self.cursor.execute(portfolio_query, portfolio_params)
            portfolio_id = self.cursor.lastrowid


            weight_query = '''
                INSERT INTO optimized_weights (portfolio_id, symbol, weight)
                VALUES (?, ?, ?)
            '''

            for symbol, weight in weights.items():
                self.cursor.execute(weight_query, (portfolio_id, symbol, weight))

            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error saving optimized portfolio: {e}")

    def get_optimized_portfolio(self, risk_level, investment_period, stocks_hash, max_age_days=7):
        """
        Retrieve an optimized portfolio and its weights from the database.


        """
        try:

            portfolio_query = '''
                SELECT op.id, op.risk_level, op.investment_period, 
                       op.expected_return, op.volatility, op.sharpe_ratio
                FROM optimized_portfolio op
                WHERE op.risk_level = ?
                AND op.investment_period = ?
                AND op.stocks_hash = ?
                AND date(op.calculation_date) >= date('now', ?)
            '''
            portfolio_params = (risk_level, investment_period, stocks_hash, f'-{max_age_days} days')

            self.cursor.execute(portfolio_query, portfolio_params)
            portfolio_row = self.cursor.fetchone()

            if not portfolio_row:
                return None, None


            portfolio = OptimizedPortfolio(
                portfolio_row[1],  # risk_level
                portfolio_row[2],  # investment_period
                portfolio_row[3],  # expected_return
                portfolio_row[4],  # volatility
                portfolio_row[5]  # sharpe_ratio
            )


            weights_query = '''
                SELECT symbol, weight
                FROM optimized_weights
                WHERE portfolio_id = ?
            '''

            self.cursor.execute(weights_query, (portfolio_row[0],))
            weights = {row[0]: row[1] for row in self.cursor.fetchall()}

            return portfolio, weights
        except sqlite3.Error as e:
            print(f"Error getting optimized portfolio: {e}")
            return None, None

    def backup_database(self, backup_path=None):
        """
        Create a backup of the database.

        """
        try:
            if not backup_path:
                # Generate backup filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.dirname(self.db_path)
                backup_name = f"portfolio_backup_{timestamp}.db"
                backup_path = os.path.join(backup_dir, backup_name)


            backup_conn = sqlite3.connect(backup_path)
            self.connection.backup(backup_conn)
            backup_conn.close()

            return backup_path
        except sqlite3.Error as e:
            print(f"Error creating database backup: {e}")
            return None

    def close(self):
        """
        Close the database connection properly.
        Should be called when the database is no longer needed.
        """
        if self.connection:
            self.connection.close()

    @classmethod
    def get_instance(cls, db_name="portfolio.db"):

        return cls(db_name)