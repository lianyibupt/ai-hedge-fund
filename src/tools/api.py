import os
import pandas as pd
import yfinance as yf

from data.cache import get_cache
from data.models import (
    CompanyNews,
    CompanyNewsResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    Price,
    PriceResponse,
    LineItem,
    LineItemResponse,
    InsiderTrade,
    InsiderTradeResponse,
)

# Global cache instance
_cache = get_cache()


def get_prices(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fetch price data from yfinance."""
    # Check cache first
    if cached_data := _cache.get_prices(ticker):
        # Filter cached data by date range
        filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
        if filtered_data:
            return filtered_data

    # Fetch from yfinance if not in cache
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date, interval="1d")
        
        if hist.empty:
            return []

        # Convert to Price objects
        prices = []
        for date, row in hist.iterrows():
            prices.append(Price(
                open=row["Open"],
                close=row["Close"],
                high=row["High"],
                low=row["Low"],
                volume=int(row["Volume"]),
                time=date.strftime("%Y-%m-%d")
            ))

        # Cache the results as dicts
        _cache.set_prices(ticker, [p.model_dump() for p in prices])
        return prices

    except Exception as e:
        raise Exception(f"Error fetching price data for {ticker}: {str(e)}")


def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[FinancialMetrics]:
    """Fetch financial metrics using yfinance."""
    # Check cache first
    if cached_data := _cache.get_financial_metrics(ticker):
        # Filter cached data by date and limit
        filtered_data = [FinancialMetrics(**metric) for metric in cached_data if metric["report_period"] <= end_date]
        filtered_data.sort(key=lambda x: x.report_period, reverse=True)
        if filtered_data:
            return filtered_data[:limit]

    # Fetch data using yfinance
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get financial data
        financials = stock.financials.transpose()
        balance_sheet = stock.balance_sheet.transpose()
        cashflow = stock.cashflow.transpose()
        
        # Combine data
        combined = pd.concat([financials, balance_sheet, cashflow], axis=1)
        combined = combined.sort_index(ascending=False)
        
        # Convert to FinancialMetrics objects
        financial_metrics = []
        for date, row in combined.iterrows():
            if str(date.date()) > end_date:
                continue
                
            # Safely get values with None checks
            revenue = row.get("Total Revenue")
            net_income = row.get("Net Income")
            total_assets = row.get("Total Assets")
            total_equity = row.get("Stockholders Equity")
            ebitda = row.get("EBITDA")
            total_liabilities = row.get("Total Liabilities")
            current_assets = row.get("Total Current Assets")
            current_liabilities = row.get("Total Current Liabilities")
            inventory = row.get("Inventory")
            cash = row.get("Cash And Cash Equivalents")
            op_cash_flow = row.get("Operating Cash Flow")
            interest_expense = row.get("Interest Expense")
            gross_profit = row.get("Gross Profit")
            op_income = row.get("Operating Income")
            
            # Calculate derived metrics with robust None checks
            def safe_divide(a, b):
                return a / b if a is not None and b is not None and b != 0 else None
                
            metrics = FinancialMetrics(
                ticker=ticker,
                report_period=str(date.date()),
                period=period,
                currency=info.get("currency", "USD"),
                market_cap=info.get("marketCap"),
                enterprise_value=info.get("enterpriseValue"),
                price_to_earnings_ratio=info.get("trailingPE"),
                price_to_book_ratio=info.get("priceToBook"),
                price_to_sales_ratio=info.get("priceToSalesTrailing12Months"),
                enterprise_value_to_ebitda_ratio=info.get("enterpriseToEbitda"),
                enterprise_value_to_revenue_ratio=info.get("enterpriseToRevenue"),
                free_cash_flow_yield=safe_divide(info.get("freeCashflow"), info.get("marketCap")),
                peg_ratio=info.get("pegRatio"),
                gross_margin=safe_divide(gross_profit, revenue),
                operating_margin=safe_divide(op_income, revenue),
                net_margin=safe_divide(net_income, revenue),
                return_on_equity=safe_divide(net_income, total_equity),
                return_on_assets=safe_divide(net_income, total_assets),
                return_on_invested_capital=None,
                asset_turnover=safe_divide(revenue, total_assets),
                inventory_turnover=None,
                receivables_turnover=None,
                days_sales_outstanding=None,
                operating_cycle=None,
                working_capital_turnover=None,
                current_ratio=safe_divide(current_assets, current_liabilities),
                quick_ratio=safe_divide((current_assets - inventory) if current_assets is not None and inventory is not None else None, current_liabilities),
                cash_ratio=safe_divide(cash, current_liabilities),
                operating_cash_flow_ratio=safe_divide(op_cash_flow, current_liabilities),
                debt_to_equity=safe_divide(total_liabilities, total_equity),
                debt_to_assets=safe_divide(total_liabilities, total_assets),
                interest_coverage=safe_divide(ebitda, interest_expense),
                revenue_growth=None,
                earnings_growth=None,
                book_value_growth=None,
                earnings_per_share_growth=None,
                free_cash_flow_growth=None,
                operating_income_growth=None,
                ebitda_growth=None,
                payout_ratio=info.get("payoutRatio"),
                earnings_per_share=info.get("trailingEps"),
                book_value_per_share=info.get("bookValue"),
                free_cash_flow_per_share=safe_divide(info.get("freeCashflow"), info.get("sharesOutstanding"))
            )
            financial_metrics.append(metrics)
            
            if len(financial_metrics) >= limit:
                break

        if not financial_metrics:
            return []

        # Cache the results as dicts
        _cache.set_financial_metrics(ticker, [m.model_dump() for m in financial_metrics])
        return financial_metrics
        
    except Exception as e:
        raise Exception(f"Error fetching data from yfinance: {ticker} - {str(e)}")


def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[LineItem]:
    """Fetch line items using yfinance."""
    try:
        stock = yf.Ticker(ticker)
        
        # Get financial data
        financials = stock.financials.transpose()
        balance_sheet = stock.balance_sheet.transpose()
        cashflow = stock.cashflow.transpose()
        
        # Combine data
        combined = pd.concat([financials, balance_sheet, cashflow], axis=1)
        combined = combined.sort_index(ascending=False)
        
        # Convert to LineItem objects
        line_items_result = []
        for date, row in combined.iterrows():
            if str(date.date()) > end_date:
                continue
                
            # Create LineItem with requested fields
            item_data = {
                "ticker": ticker,
                "report_period": str(date.date()),
                "period": period,
                "currency": stock.info.get("currency", "USD")
            }
            
            # Add requested line items
            for line_item in line_items:
                item_data[line_item] = row.get(line_item)
                
            line_items_result.append(LineItem(**item_data))
            
            if len(line_items_result) >= limit:
                break

        return line_items_result
        
    except Exception as e:
        raise Exception(f"Error fetching line items from yfinance: {ticker} - {str(e)}")


def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[InsiderTrade]:
    """Fetch insider trades (not available via yfinance, returns empty list)."""
    # Check cache first
    if cached_data := _cache.get_insider_trades(ticker):
        # Filter cached data by date range
        filtered_data = [InsiderTrade(**trade) for trade in cached_data
                        if (start_date is None or (trade.get("transaction_date") or trade["filing_date"]) >= start_date)
                        and (trade.get("transaction_date") or trade["filing_date"]) <= end_date]
        filtered_data.sort(key=lambda x: x.transaction_date or x.filing_date, reverse=True)
        if filtered_data:
            return filtered_data[:limit]

    # yfinance doesn't provide insider trade data
    return []


def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[CompanyNews]:
    """Fetch company news (not available via yfinance, returns empty list)."""
    # Check cache first
    if cached_data := _cache.get_company_news(ticker):
        # Filter cached data by date range
        filtered_data = [CompanyNews(**news) for news in cached_data
                        if (start_date is None or news["date"] >= start_date)
                        and news["date"] <= end_date]
        filtered_data.sort(key=lambda x: x.date, reverse=True)
        if filtered_data:
            return filtered_data[:limit]

    # yfinance doesn't provide company news data
    return []



def get_market_cap(
    ticker: str,
    end_date: str,
) -> float | None:
    """Fetch market cap from the API."""
    financial_metrics = get_financial_metrics(ticker, end_date)
    market_cap = financial_metrics[0].market_cap
    if not market_cap:
        return None

    return market_cap


def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df


# Update the get_price_data function to use the new functions
def get_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    prices = get_prices(ticker, start_date, end_date)
    return prices_to_df(prices)
