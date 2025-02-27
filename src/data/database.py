import sqlite3
from datetime import datetime
from src.data.models import StockMetrics, OptimizedPortfolio


class Database:
    def __init__(self, db_name="portfolio.db"):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self._create_tables()

    def _create_tables(self):
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

            # Нові таблиці для оптимізації
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
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO stock_metrics 
                (symbol, mean_return, volatility, calculation_date, window_size)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                metrics.symbol,
                metrics.mean_return,
                metrics.volatility,
                metrics.calculation_date,
                metrics.window_size
            ))
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error saving stock metrics: {e}")

    def get_stock_metrics(self, symbol, window_size, max_age_days=7):
        try:
            self.cursor.execute('''
                SELECT symbol, mean_return, volatility, calculation_date, window_size
                FROM stock_metrics
                WHERE symbol = ? 
                AND window_size = ?
                AND date(calculation_date) >= date('now', ?)
            ''', (symbol, window_size, f'-{max_age_days} days'))

            row = self.cursor.fetchone()
            if row:
                return StockMetrics(*row)
            return None
        except sqlite3.Error as e:
            print(f"Error getting stock metrics: {e}")
            return None

    def save_optimized_portfolio(self, portfolio, weights, stocks_hash):
        try:
            self.cursor.execute('''
                INSERT INTO optimized_portfolio 
                (risk_level, investment_period, expected_return, volatility, 
                 sharpe_ratio, calculation_date, stocks_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                portfolio.risk_level,
                portfolio.investment_period,
                portfolio.expected_return,
                portfolio.volatility,
                portfolio.sharpe_ratio,
                datetime.now().date(),
                stocks_hash
            ))

            portfolio_id = self.cursor.lastrowid

            # Зберігаємо ваги для кожної акції
            for symbol, weight in weights.items():
                self.cursor.execute('''
                    INSERT INTO optimized_weights (portfolio_id, symbol, weight)
                    VALUES (?, ?, ?)
                ''', (portfolio_id, symbol, weight))

            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error saving optimized portfolio: {e}")

    def get_optimized_portfolio(self, risk_level, investment_period, stocks_hash, max_age_days=7):
        try:
            self.cursor.execute('''
                SELECT op.id, op.risk_level, op.investment_period, 
                       op.expected_return, op.volatility, op.sharpe_ratio
                FROM optimized_portfolio op
                WHERE op.risk_level = ?
                AND op.investment_period = ?
                AND op.stocks_hash = ?
                AND date(op.calculation_date) >= date('now', ?)
            ''', (risk_level, investment_period, stocks_hash, f'-{max_age_days} days'))

            portfolio_row = self.cursor.fetchone()
            if not portfolio_row:
                return None, None

            portfolio = OptimizedPortfolio(
                portfolio_row[1], portfolio_row[2],
                portfolio_row[3], portfolio_row[4], portfolio_row[5]
            )


            self.cursor.execute('''
                SELECT symbol, weight
                FROM optimized_weights
                WHERE portfolio_id = ?
            ''', (portfolio_row[0],))

            weights = {row[0]: row[1] for row in self.cursor.fetchall()}

            return portfolio, weights
        except sqlite3.Error as e:
            print(f"Error getting optimized portfolio: {e}")
            return None, None

    def close(self):
        self.connection.close()