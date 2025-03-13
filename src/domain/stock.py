from typing import List, Optional
from ..data.database import Database
from ..data.models import Stock


class StockManager:
    """
    A class to manage stock operations in the database.

    Attributes:
    db (Database): The database connection object.
    """

    def __init__(self, db: Database):
        """
        Constructs all the necessary attributes for the StockManager object.

        Parameters:
        db (Database): The database connection object.
        """
        self.db = db

    def add_stock(self, portfolio_id: int, symbol: str, quantity: int, price: float) -> int:
        """
        Adds a stock to the portfolio. If the stock already exists, updates the quantity.

        Parameters:
        portfolio_id (int): The ID of the portfolio.
        symbol (str): The stock symbol.
        quantity (int): The quantity of the stock.
        price (float): The price of the stock.

        Returns:
        int: The ID of the added or updated stock.
        """
        existing_stock = self.db.cursor.execute(
            "SELECT id, quantity FROM stock WHERE portfolio_id = ? AND symbol = ?",
            (portfolio_id, symbol)
        ).fetchone()

        if existing_stock:
            stock_id, existing_quantity = existing_stock
            new_quantity = existing_quantity + quantity
            self.update_stock_quantity(stock_id, new_quantity)
            return stock_id
        else:
            self.db.cursor.execute(
                "INSERT INTO stock (portfolio_id, symbol, quantity, price) VALUES (?, ?, ?, ?)",
                (portfolio_id, symbol, quantity, price)
            )
            self.db.connection.commit()
            return self.db.cursor.lastrowid

    def remove_stock(self, stock_id: int) -> bool:
        """
        Removes a stock from the database.

        Parameters:
        stock_id (int): The ID of the stock to remove.

        Returns:
        bool: True if the removal was successful, False otherwise.
        """
        try:
            self.db.cursor.execute(
                "DELETE FROM stock WHERE id = ?",
                (stock_id,)
            )
            self.db.connection.commit()
            return True
        except Exception:
            return False

    def update_stock_quantity(self, stock_id: int, quantity: int) -> bool:
        """
        Updates the quantity of a stock in the database.

        Parameters:
        stock_id (int): The ID of the stock to update.
        quantity (int): The new quantity of the stock.

        Returns:
        bool: True if the update was successful, False otherwise.
        """
        try:
            self.db.cursor.execute(
                "UPDATE stock SET quantity = ? WHERE id = ?",
                (quantity, stock_id)
            )
            self.db.connection.commit()
            return True
        except Exception:
            return False

    def get_portfolio_stocks(self, portfolio_id: int) -> List[tuple]:
        """
        Retrieves all stocks in a portfolio.

        Parameters:
        portfolio_id (int): The ID of the portfolio.

        Returns:
        List[tuple]: A list of tuples containing the ID, symbol, quantity, and price of each stock.
        """
        self.db.cursor.execute(
            "SELECT id, symbol, quantity, price FROM stock WHERE portfolio_id = ?",
            (portfolio_id,)
        )
        return self.db.cursor.fetchall()

    def get_stock(self, stock_id: int) -> Optional[Stock]:
        """
        Retrieves a stock from the database by its ID.

        Parameters:
        stock_id (int): The ID of the stock.

        Returns:
        Optional[Stock]: The Stock object if found, otherwise None.
        """
        self.db.cursor.execute(
            "SELECT symbol, quantity, price FROM stock WHERE id = ?",
            (stock_id,)
        )
        result = self.db.cursor.fetchone()
        return Stock(result[0], result[1], result[2]) if result else None
