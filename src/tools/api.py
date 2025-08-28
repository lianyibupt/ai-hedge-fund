import os
import pandas as pd
from typing import Optional
from .itick_api import get_itick_api, date_to_timestamp

from data.cache import get_cache
from data.database import get_database_manager
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

# Global cache instance (内存缓存作为第一级)
_cache = get_cache()
# 数据库管理器实例（SQLite缓存作为第二级）
_db_manager = get_database_manager()


def get_prices(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fetch price data with multi-level cache: memory -> SQLite -> iTick API."""
    # 第一级：检查内存缓存（新的按日期缓存机制）
    if cached_data := _cache.get_prices(ticker, start_date, end_date):
        # 转换为Price对象并进一步过滤日期范围
        prices = [Price(**price) for price in cached_data]
        filtered_prices = [p for p in prices if start_date <= p.time <= end_date]
        if filtered_prices:
            print(f"📋 从内存缓存获取 {ticker} 价格数据: {len(filtered_prices)} 条")
            return filtered_prices

    # 第二级：检查SQLite缓存
    try:
        cached_price_data = _db_manager.get_cached_price_data(ticker, start_date, end_date)
        if cached_price_data:
            print(f"💾 从SQLite缓存获取 {ticker} 价格数据: {len(cached_price_data)} 条")
            # 转换为Price对象
            prices = [Price(**price_data) for price_data in cached_price_data]
            # 同时更新内存缓存
            _cache.set_prices(ticker, [p.model_dump() for p in prices])
            return prices
    except Exception as e:
        print(f"⚠️ SQLite缓存读取失败: {str(e)}")

    # 第三级：从iTick API获取数据
    print(f"🔄 从 iTick API 获取 {ticker} 的价格数据...")
    try:
        prices = _fetch_prices_from_itick(ticker, start_date, end_date)
        
        if not prices:
            raise Exception(f"iTick API 返回空数据，股票代码: {ticker}")
            
        print(f"✅ 成功从 iTick API 获取到 {len(prices)} 条价格数据")
        
        # 存储到双级缓存
        price_dicts = [p.model_dump() for p in prices]
        _cache.set_prices(ticker, price_dicts)  # 内存缓存
        
        try:
            _db_manager.cache_price_data(ticker, price_dicts, cache_hours=24)  # SQLite缓存
            print(f"💾 价格数据已缓存到SQLite数据库")
        except Exception as cache_error:
            print(f"⚠️ SQLite缓存存储失败: {str(cache_error)}")
        
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
    """Fetch financial metrics with multi-level cache: memory -> SQLite -> iTick API."""
    # 第一级：检查内存缓存（新的按报告期缓存机制）
    if cached_data := _cache.get_financial_metrics(ticker, end_date):
        # 转换为FinancialMetrics对象并应用限制
        metrics = [FinancialMetrics(**metric) for metric in cached_data]
        limited_metrics = metrics[:limit]
        if limited_metrics:
            print(f"📋 从内存缓存获取 {ticker} 财务指标: {len(limited_metrics)} 条")
            return limited_metrics

    # 第二级：检查SQLite缓存
    try:
        cached_financial_data = _db_manager.get_cached_financial_data(ticker, end_date)
        if cached_financial_data:
            print(f"💾 从SQLite缓存获取 {ticker} 财务指标: {len(cached_financial_data)} 条")
            # 转换为FinancialMetrics对象
            metrics = [FinancialMetrics(**financial_data) for financial_data in cached_financial_data]
            metrics.sort(key=lambda x: x.report_period, reverse=True)
            limited_metrics = metrics[:limit]
            # 同时更新内存缓存
            _cache.set_financial_metrics(ticker, [m.model_dump() for m in limited_metrics])
            return limited_metrics
    except Exception as e:
        print(f"⚠️ SQLite财务缓存读取失败: {str(e)}")

    # 第三级：从iTick API获取数据
    print(f"🔄 从 iTick API 获取 {ticker} 的财务指标...")
    try:
        metrics = _fetch_financial_metrics_from_itick(ticker, end_date, period, limit)
        
        if not metrics:
            raise Exception(f"iTick API 返回空财务数据，股票代码: {ticker}")
            
        print(f"✅ 成功从 iTick API 获取到财务指标")
        
        # 存储到双级缓存
        metric_dicts = [m.model_dump() for m in metrics]
        _cache.set_financial_metrics(ticker, metric_dicts)  # 内存缓存
        
        try:
            _db_manager.cache_financial_data(ticker, metric_dicts, cache_hours=24*7)  # SQLite缓存
            print(f"💾 财务指标已缓存到SQLite数据库")
        except Exception as cache_error:
            print(f"⚠️ SQLite财务缓存存储失败: {str(cache_error)}")
        
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


def cleanup_cache():
    """清理过期的缓存数据"""
    try:
        _db_manager.cleanup_expired_cache()
    except Exception as e:
        print(f"⚠️ 缓存清理失败: {str(e)}")


def get_cache_stats() -> dict:
    """获取缓存统计信息"""
    try:
        return _db_manager.get_cache_stats()
    except Exception as e:
        print(f"⚠️ 获取缓存统计失败: {str(e)}")
        return {}


# Update the get_price_data function to use the new functions
def get_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取价格数据并转换为DataFrame"""
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



