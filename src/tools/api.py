import os
import pandas as pd
from futu import RET_OK
from typing import Optional
from .futu_api import FutuAPI

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
    """Fetch price data from Futu API."""
    # Check cache first
    if cached_data := _cache.get_prices(ticker):
        # Filter cached data by date range
        filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
        if filtered_data:
            return filtered_data

    # Fetch from Futu API if not in cache
    try:
        futu = FutuAPI()
        if not futu.connect():
            raise Exception("Failed to connect to Futu API")

        # Convert ticker to Futu format (e.g. AAPL -> US.AAPL)
        futu_code = f"US.{ticker}" if not ticker.startswith(("US.", "HK.", "SH.", "SZ.")) else ticker
        
        kline_data = futu.get_history_kline(futu_code, start_date, end_date)
        if not kline_data:
            return []

        # Convert to Price objects
        prices = []
        for item in kline_data:
            prices.append(Price(
                open=float(item["open"]),
                close=float(item["close"]),
                high=float(item["high"]),
                low=float(item["low"]),
                volume=int(item["volume"]),
                time=item["time_key"][:10]  # YYYY-MM-DD format
            ))

        # Cache the results as dicts
        _cache.set_prices(ticker, [p.model_dump() for p in prices])
        futu.close()
        return prices

    except Exception as e:
        raise Exception(f"Error fetching price data for {ticker}: {str(e)}")


def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[FinancialMetrics]:
    """Fetch financial metrics using Futu API."""
    # Check cache first
    if cached_data := _cache.get_financial_metrics(ticker):
        # Filter cached data by date and limit
        filtered_data = [FinancialMetrics(**metric) for metric in cached_data if metric["report_period"] <= end_date]
        filtered_data.sort(key=lambda x: x.report_period, reverse=True)
        if filtered_data:
            return filtered_data[:limit]

    # Fetch data using Futu API
    try:
        futu = FutuAPI()
        if not futu.connect():
            raise Exception("Failed to connect to Futu API")

        # Convert ticker to Futu format
        futu_code = f"US.{ticker}" if not ticker.startswith(("US.", "HK.", "SH.", "SZ.")) else ticker
        
        # Get market snapshot for basic info
        snapshot = futu.get_market_snapshot([futu_code])
        if not snapshot:
            return []
            
        snapshot = snapshot[0]
        
        # Get financial data
        financial_data = futu.get_financial_data(futu_code, "income") or []
        balance_data = futu.get_financial_data(futu_code, "balance") or []
        cashflow_data = futu.get_financial_data(futu_code, "cashflow") or []
        
        # Convert to FinancialMetrics objects
        financial_metrics = []
        for item in financial_data:
            if item["report_date"] > end_date:
                continue
                
            # Find matching balance sheet and cashflow data
            balance_item = next((b for b in balance_data if b["report_date"] == item["report_date"]), {})
            cashflow_item = next((c for c in cashflow_data if c["report_date"] == item["report_date"]), {})
            
            def safe_divide(a, b):
                return a / b if a is not None and b is not None and b != 0 else None
                
            metrics = FinancialMetrics(
                ticker=ticker,
                report_period=item["report_date"],
                period=period,
                currency=snapshot.get("currency", "USD"),
                market_cap=snapshot.get("market_val"),
                enterprise_value=snapshot.get("total_enterprise_value"),
                price_to_earnings_ratio=snapshot.get("pe_ratio"),
                price_to_book_ratio=snapshot.get("pb_ratio"),
                price_to_sales_ratio=snapshot.get("ps_ratio"),
                enterprise_value_to_ebitda_ratio=snapshot.get("ev_ebitda"),
                enterprise_value_to_revenue_ratio=snapshot.get("ev_revenue"),
                free_cash_flow_yield=safe_divide(cashflow_item.get("free_cash_flow"), snapshot.get("market_val")),
                peg_ratio=None,  # Not available in Futu
                gross_margin=safe_divide(item.get("gross_profit"), item.get("revenue")),
                operating_margin=safe_divide(item.get("operating_income"), item.get("revenue")),
                net_margin=safe_divide(item.get("net_income"), item.get("revenue")),
                return_on_equity=safe_divide(item.get("net_income"), balance_item.get("total_equity")),
                return_on_assets=safe_divide(item.get("net_income"), balance_item.get("total_assets")),
                return_on_invested_capital=None,
                asset_turnover=safe_divide(item.get("revenue"), balance_item.get("total_assets")),
                inventory_turnover=None,
                receivables_turnover=None,
                days_sales_outstanding=None,
                operating_cycle=None,
                working_capital_turnover=None,
                current_ratio=safe_divide(balance_item.get("current_assets"), balance_item.get("current_liabilities")),
                quick_ratio=safe_divide(
                    (balance_item.get("current_assets") - balance_item.get("inventory"))
                    if balance_item.get("current_assets") is not None and balance_item.get("inventory") is not None
                    else None,
                    balance_item.get("current_liabilities")
                ),
                cash_ratio=safe_divide(balance_item.get("cash"), balance_item.get("current_liabilities")),
                operating_cash_flow_ratio=safe_divide(cashflow_item.get("operating_cash_flow"), balance_item.get("current_liabilities")),
                debt_to_equity=safe_divide(balance_item.get("total_liabilities"), balance_item.get("total_equity")),
                debt_to_assets=safe_divide(balance_item.get("total_liabilities"), balance_item.get("total_assets")),
                interest_coverage=safe_divide(item.get("ebitda"), item.get("interest_expense")),
                revenue_growth=None,
                earnings_growth=None,
                book_value_growth=None,
                earnings_per_share_growth=None,
                free_cash_flow_growth=None,
                operating_income_growth=None,
                ebitda_growth=None,
                payout_ratio=snapshot.get("dividend_payout_ratio"),
                earnings_per_share=snapshot.get("eps"),
                book_value_per_share=snapshot.get("book_value_per_share"),
                free_cash_flow_per_share=safe_divide(cashflow_item.get("free_cash_flow"), snapshot.get("total_shares"))
            )
            financial_metrics.append(metrics)
            
            if len(financial_metrics) >= limit:
                break

        if not financial_metrics:
            return []

        # Cache the results as dicts
        _cache.set_financial_metrics(ticker, [m.model_dump() for m in financial_metrics])
        futu.close()
        return financial_metrics
        
    except Exception as e:
        raise Exception(f"Error fetching data from Futu API: {ticker} - {str(e)}")


def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[LineItem]:
    """Fetch line items using Futu API."""
    try:
        futu = FutuAPI()
        if not futu.connect():
            raise Exception("Failed to connect to Futu API")

        # Convert ticker to Futu format
        futu_code = f"US.{ticker}" if not ticker.startswith(("US.", "HK.", "SH.", "SZ.")) else ticker
        
        # Get financial data based on line items requested
        financial_types = set()
        for item in line_items:
            if item in ["revenue", "gross_profit", "operating_income", "net_income"]:
                financial_types.add("income")
            elif item in ["total_assets", "total_liabilities", "total_equity", "current_assets"]:
                financial_types.add("balance")
            elif item in ["operating_cash_flow", "free_cash_flow"]:
                financial_types.add("cashflow")
                
        # Fetch all required financial data
        all_data = {}
        for ftype in financial_types:
            data = futu.get_financial_data(futu_code, ftype) or []
            all_data[ftype] = data
            
        # Get market snapshot for currency info
        snapshot = futu.get_market_snapshot([futu_code])
        currency = snapshot[0].get("currency", "USD") if snapshot else "USD"
        
        # Convert to LineItem objects
        line_items_result = []
        for ftype, data in all_data.items():
            for item in data:
                if item["report_date"] > end_date:
                    continue
                    
                # Create LineItem with requested fields
                item_data = {
                    "ticker": ticker,
                    "report_period": item["report_date"],
                    "period": period,
                    "currency": currency
                }
                
                # Add requested line items
                for line_item in line_items:
                    item_data[line_item] = item.get(line_item)
                    
                line_items_result.append(LineItem(**item_data))
                
                if len(line_items_result) >= limit:
                    break
            if len(line_items_result) >= limit:
                break

        futu.close()
        return line_items_result
        
    except Exception as e:
        raise Exception(f"Error fetching line items from Futu API: {ticker} - {str(e)}")


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
