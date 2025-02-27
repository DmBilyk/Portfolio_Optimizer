from typing import List, Optional
from ..data.database import Database
from ..data.models import Portfolio

class PortfolioManager:
    def __init__(self, db: Database):
        self.db = db

    def create_portfolio(self, name: str) -> int:

        self.db.cursor.execute(
            "SELECT id FROM portfolio WHERE name = ?",
            (name,)
        )
        existing_portfolio = self.db.cursor.fetchone()
        if existing_portfolio:
            return existing_portfolio[0]


        self.db.cursor.execute(
            "INSERT INTO portfolio (name) VALUES (?)",
            (name,)
        )
        self.db.connection.commit()
        return self.db.cursor.lastrowid

    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        self.db.cursor.execute(
            "SELECT name FROM portfolio WHERE id = ?",
            (portfolio_id,)
        )
        result = self.db.cursor.fetchone()
        return Portfolio(result[0]) if result else None

    def get_all_portfolios(self) -> List[tuple]:
        self.db.cursor.execute("SELECT id, name FROM portfolio")
        return self.db.cursor.fetchall()

    def delete_portfolio(self, portfolio_id: int) -> bool:
        try:
            self.db.cursor.execute(
                "DELETE FROM stock WHERE portfolio_id = ?",
                (portfolio_id,)
            )
            self.db.cursor.execute(
                "DELETE FROM portfolio WHERE id = ?",
                (portfolio_id,)
            )
            self.db.connection.commit()
            return True
        except Exception:
            return False