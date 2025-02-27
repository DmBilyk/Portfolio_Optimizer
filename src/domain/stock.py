from typing import List, Optional
from ..data.database import Database
from ..data.models import  Stock


class StockManager:
    def __init__(self, db: Database):
        self.db = db

    def add_stock(self, portfolio_id: int, symbol: str, quantity: int, price: float) -> int:
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
        self.db.cursor.execute(
            "SELECT id, symbol, quantity, price FROM stock WHERE portfolio_id = ?",
            (portfolio_id,)
        )
        return self.db.cursor.fetchall()

    def get_stock(self, stock_id: int) -> Optional[Stock]:
        self.db.cursor.execute(
            "SELECT symbol, quantity, price FROM stock WHERE id = ?",
            (stock_id,)
        )
        result = self.db.cursor.fetchone()
        return Stock(result[0], result[1], result[2]) if result else None