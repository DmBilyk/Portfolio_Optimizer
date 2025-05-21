class PortfolioService:
    def __init__(self, portfolio_manager, stock_manager, market_data):
        self.portfolio_manager = portfolio_manager
        self.stock_manager = stock_manager
        self.market_data = market_data

    def get_all_portfolios(self):
        """Get all available portfolios"""
        return self.portfolio_manager.get_all_portfolios()

    def create_optimized_portfolio(self, investment, risk_level, investment_period):
        """
        Create an optimized portfolio based on input parameters

        Returns:
            dict: Dictionary containing optimized stocks and performance metrics
        """
        from src.domain.portfolio.optimizer import MarkowitzOptimizer


        stock_symbols = self.market_data.get_all_stock_symbols()
        returns_data = self.market_data.get_historical_returns(stock_symbols)
        current_prices = self.market_data.get_current_prices(stock_symbols)


        optimizer = MarkowitzOptimizer(
            stock_symbols,
            returns_data,
            risk_level=risk_level,
            investment_period=investment_period
        )

        optimal_portfolio = optimizer.optimize_portfolio()


        min_investment_usage = 0.90
        max_investment_usage = 1.02

        stock_data = []
        total_invested = 0


        for symbol, weight in optimal_portfolio['weights'].items():
            target_amount = weight * investment
            price = current_prices[symbol]


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


        stock_data = self._adjust_shares_for_target(
            stock_data,
            investment,
            total_invested,
            min_investment_usage,
            max_investment_usage
        )


        total_invested = sum(stock['amount'] for stock in stock_data)
        for stock in stock_data:
            stock['weight'] = stock['amount'] / total_invested

        remaining = investment - total_invested

        return {
            'stock_data': stock_data,
            'optimal_portfolio': optimal_portfolio,
            'total_invested': total_invested,
            'investment': investment,
            'remaining': remaining
        }

    def _adjust_shares_for_target(self, stock_data, investment, total_invested,
                                  min_investment_usage, max_investment_usage):
        """Adjust shares to meet target investment range"""

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

        return stock_data

    def add_stocks_to_portfolio(self, portfolio_id, stocks):
        """
        Add multiple stocks to a portfolio

        Returns:
            tuple: (success_count, errors)
        """
        added_count = 0
        errors = []

        for stock in stocks:
            try:
                self.stock_manager.add_stock(
                    portfolio_id,
                    stock['symbol'],
                    stock['shares'],
                    stock['price']
                )
                added_count += 1
            except Exception as e:
                errors.append(f"Failed to add {stock['symbol']}: {str(e)}")

        return added_count, errors