from typing import List, Optional
from ..data.database import Database
from ..data.models import Portfolio


class PortfolioManager:
    """
    A class to manage portfolio operations in the database.

    Attributes:
    db (Database): The database connection object.
    """

    def __init__(self, db: Database):
        """
        Constructs all the necessary attributes for the PortfolioManager object.

        Parameters:
        db (Database): The database connection object.
        """
        self.db = db

    def create_portfolio(self, name: str) -> int:
        """
        Creates a new portfolio in the database.

        Parameters:
        name (str): The name of the portfolio.

        Returns:
        int: The ID of the created portfolio. If the portfolio already exists, returns the existing portfolio ID.
        """
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
        """
        Retrieves a portfolio from the database by its ID.

        Parameters:
        portfolio_id (int): The ID of the portfolio.

        Returns:
        Optional[Portfolio]: The Portfolio object if found, otherwise None.
        """
        self.db.cursor.execute(
            "SELECT name FROM portfolio WHERE id = ?",
            (portfolio_id,)
        )
        result = self.db.cursor.fetchone()
        return Portfolio(result[0]) if result else None

    def get_all_portfolios(self) -> List[tuple]:
        """
        Retrieves all portfolios from the database.

        Returns:
        List[tuple]: A list of tuples containing the ID and name of each portfolio.
        """
        self.db.cursor.execute("SELECT id, name FROM portfolio")
        return self.db.cursor.fetchall()

    def delete_portfolio(self, portfolio_id: int) -> bool:
        """
        Deletes a portfolio and its associated stocks from the database.

        Parameters:
        portfolio_id (int): The ID of the portfolio to delete.

        Returns:
        bool: True if the deletion was successful, False otherwise.
        """
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