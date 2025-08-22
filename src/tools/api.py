import os
import pandas as pd
from typing import Optional
from .itick_api import get_itick_api, date_to_timestamp

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
    """Fetch price data from iTick API only. No fallback mechanism."""
    # Check cache first
    if cached_data := _cache.get_prices(ticker):
        # Filter cached data by date range
        filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
        if filtered_data:
            return filtered_data

    # Only use iTick API - no fallback mechanism
    print(f"🔄 从 iTick API 获取 {ticker} 的价格数据...")
    try:
        prices = _fetch_prices_from_itick(ticker, start_date, end_date)
        
        if not prices:
            raise Exception(f"iTick API 返回空数据，股票代码: {ticker}")
            
        print(f"✅ 成功从 iTick API 获取到 {len(prices)} 条价格数据")
        # Cache the results as dicts
        _cache.set_prices(ticker, [p.model_dump() for p in prices])
        return prices
        
    except Exception as e:
        print(f"❌ iTick API 获取价格数据失败: {str(e)}")
        raise Exception(f"无法从 iTick API 获取 {ticker} 的价格数据: {str(e)}")


def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[FinancialMetrics]:
    """Fetch financial metrics from iTick API only. No fallback mechanism."""
    # Check cache first
    if cached_data := _cache.get_financial_metrics(ticker):
        # Filter cached data by date and limit
        filtered_data = [FinancialMetrics(**metric) for metric in cached_data if metric["report_period"] <= end_date]
        filtered_data.sort(key=lambda x: x.report_period, reverse=True)
        if filtered_data:
            return filtered_data[:limit]

    # Only use iTick API - no fallback mechanism
    print(f"🔄 从 iTick API 获取 {ticker} 的财务指标...")
    try:
        metrics = _fetch_financial_metrics_from_itick(ticker, end_date, period, limit)
        
        if not metrics:
            raise Exception(f"iTick API 返回空财务数据，股票代码: {ticker}")
            
        print(f"✅ 成功从 iTick API 获取到财务指标")
        # Cache the results as dicts
        _cache.set_financial_metrics(ticker, [m.model_dump() for m in metrics])
        return metrics
        
    except Exception as e:
        print(f"❌ iTick API 获取财务指标失败: {str(e)}")
        raise Exception(f"无法从 iTick API 获取 {ticker} 的财务指标: {str(e)}")








def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[LineItem]:
    """Fetch line items using iTick API."""
    try:
        # Get financial metrics from iTick API
        metrics = get_financial_metrics(ticker, end_date, period, limit)
        
        if not metrics:
            return []
            
        # Convert FinancialMetrics to LineItem objects
        line_items_result = []
        for metric in metrics:
            # Create LineItem with requested fields
            item_data = {
                "ticker": ticker,
                "report_period": metric.report_period,
                "period": period,
                "currency": metric.currency or "USD"
            }
            
            # Add requested line items from financial metrics
            for line_item in line_items:
                if hasattr(metric, line_item):
                    item_data[line_item] = getattr(metric, line_item)
                else:
                    item_data[line_item] = None
                    
            line_items_result.append(LineItem(**item_data))
            
            if len(line_items_result) >= limit:
                break

        return line_items_result
        
    except Exception as e:
        raise Exception(f"Error fetching line items from iTick API: {ticker} - {str(e)}")


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


# =============================================================================
# Data Source Implementations
# =============================================================================

def _fetch_prices_from_itick(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """从iTick API获取价格数据"""
    itick_api = get_itick_api()
    
    # 转换日期为时间戳
    start_timestamp = date_to_timestamp(start_date)
    end_timestamp = date_to_timestamp(end_date)
    
    # 获取历史K线数据
    kline_data = itick_api.get_historical_kline(
        ticker=ticker,
        period="1d",
        start_time=str(start_timestamp),
        end_time=str(end_timestamp),
        region="us"
    )
    
    # 转换为Price对象
    return itick_api.convert_to_price_objects(kline_data, ticker)








def _fetch_financial_metrics_from_itick(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[FinancialMetrics]:
    """从iTick API获取财务指标"""
    itick_api = get_itick_api()
    
    # 获取财务数据
    financial_data = itick_api.get_financial_data(ticker, region="us")
    
    # 转换为FinancialMetrics对象
    return itick_api.convert_to_financial_metrics(financial_data, ticker)



