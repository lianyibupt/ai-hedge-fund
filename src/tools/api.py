import os
import pandas as pd
from typing import Optional
from .itick_api import get_itick_api, date_to_timestamp
import re

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


def _detect_ticker_region(ticker: str) -> str:
    """
    根据股票代码检测市场区域
    
    Args:
        ticker: 股票代码
        
    Returns:
        市场区域代码 (us, hk, sh, sz, sg, jp)
    """
    ticker = ticker.strip().upper()
    
    # 港股：HK.开头或者纯数字（4-5位）
    if ticker.startswith('HK.') or (ticker.isdigit() and len(ticker) in [4, 5]):
        return 'hk'
    
    # A股：以数字开头且6位数字
    if ticker.isdigit() and len(ticker) == 6:
        # 上证：000001-199999, 600000-699999, 900000-999999
        # 深证：000000-399999
        first_digit = ticker[0]
        if first_digit in ['6', '9']:
            return 'sh'  # 上证
        elif first_digit in ['0', '3']:
            return 'sz'  # 深证
    
    # A股：.SH 或 .SZ 后缀
    if ticker.endswith('.SH'):
        return 'sh'
    elif ticker.endswith('.SZ'):
        return 'sz'
    
    # 新加坡股票：暂时按代码模式识别（待完善）
    # 日本股票：暂时按代码模式识别（待完善）
    
    # 默认为美股
    return 'us'


def get_prices(ticker: str, start_date: str, end_date: str, region: str = None) -> list[Price]:
    """Fetch price data with intelligent cache: analyze existing cache and request only missing dates.
    
    Args:
        ticker: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        region: 市场区域 (us, hk, sh, sz, sg, jp)，如果不提供则自动检测
    """
    return _get_prices_intelligent_cache(ticker, start_date, end_date, region)


def _get_prices_intelligent_cache(ticker: str, start_date: str, end_date: str, region: str = None) -> list[Price]:
    """
    智能缓存策略：分析已有缓存数据，只请求缺失的日期范围
    
    缓存策略说明：
    1. 首先检查内存和数据库缓存，找出已有的日期
    2. 计算缺失的日期范围
    3. 只对缺失的日期范围请求API
    4. 将新获取的数据与缓存数据合并
    
    Args:
        ticker: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        region: 市场区域 (us, hk, sh, sz, sg, jp)，如果不提供则自动检测
    """
    from datetime import datetime, timedelta
    import pandas as pd
    
    # 如果没有提供region，则自动检测
    if region is None:
        region = _detect_ticker_region(ticker)
    
    # 日期验证：检查是否查询未来日期
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        now = datetime.now()
        
        if end_dt > now:
            # 如果结束日期在未来，调整为当前日期
            adjusted_end_date = now.strftime("%Y-%m-%d")
            print(f"⚠️ 结束日期 {end_date} 在未来，调整为 {adjusted_end_date}")
            end_date = adjusted_end_date
        
        if start_dt > now:
            print(f"⚠️ 警告：开始日期 {start_date} 在未来，无法获取数据")
            raise Exception(f"无法获取未来日期的数据: {start_date}")
            
    except ValueError as e:
        print(f"⚠️ 日期格式错误: {str(e)}")
        raise Exception(f"日期格式必须为 YYYY-MM-DD: {start_date}, {end_date}")
    
    # 1. 收集所有已有的缓存数据
    all_cached_prices = []
    cached_dates = set()
    
    # 检查内存缓存
    if cached_data := _cache.get_prices(ticker, start_date, end_date):
        cached_prices = [Price(**price) for price in cached_data]
        for price in cached_prices:
            if start_date <= price.time <= end_date:
                all_cached_prices.append(price)
                cached_dates.add(price.time)
        if cached_prices:
            print(f"📋 内存缓存命中 {ticker}: {len(cached_prices)} 条数据")
    
    # 检查SQLite缓存
    try:
        db_cached_data = _db_manager.get_cached_price_data(ticker, start_date, end_date)
        if db_cached_data:
            db_prices = [Price(**price_data) for price_data in db_cached_data]
            for price in db_prices:
                if price.time not in cached_dates and start_date <= price.time <= end_date:
                    all_cached_prices.append(price)
                    cached_dates.add(price.time)
            if db_prices:
                print(f"💾 SQLite缓存命中 {ticker}: {len(db_prices)} 条数据")
    except Exception as e:
        print(f"⚠️ SQLite缓存读取失败: {str(e)}")
    
    # 2. 分析缺失的日期范围
    missing_ranges = _calculate_missing_date_ranges(start_date, end_date, cached_dates)
    
    if not missing_ranges:
        # 所有数据都已缓存
        all_cached_prices.sort(key=lambda x: x.time)
        print(f"✅ {ticker} 数据完全命中缓存: {len(all_cached_prices)} 条")
        return all_cached_prices
    
    # 3. 对缺失的日期范围请求API
    new_prices = []
    for missing_start, missing_end in missing_ranges:
        print(f"🔄 从 iTick API 获取 {ticker} 缺失数据: {missing_start} 到 {missing_end} (市场: {region})")
        try:
            range_prices = _fetch_prices_from_itick(ticker, missing_start, missing_end, region)
            if range_prices:
                new_prices.extend(range_prices)
                print(f"✅ 成功获取 {len(range_prices)} 条新数据")
        except Exception as e:
            print(f"❌ 获取 {missing_start} 到 {missing_end} 数据失败: {str(e)}")
            print(f"❌ 详细错误: {type(e).__name__}: {str(e)}")
            # 继续处理其他日期范围
            continue
    
    # 4. 缓存新获取的数据
    if new_prices:
        try:
            price_dicts = [p.model_dump() for p in new_prices]
            _cache.set_prices(ticker, price_dicts)  # 内存缓存
            _db_manager.cache_price_data(ticker, price_dicts, cache_hours=24)  # SQLite缓存
            print(f"💾 新数据已缓存: {len(new_prices)} 条")
        except Exception as cache_error:
            print(f"⚠️ 缓存新数据失败: {str(cache_error)}")
    
    # 5. 合并所有数据
    all_prices = all_cached_prices + new_prices
    all_prices.sort(key=lambda x: x.time)
    
    # 过滤到请求的日期范围
    filtered_prices = [p for p in all_prices if start_date <= p.time <= end_date]
    
    if not filtered_prices:
        # 提供更详细的错误信息
        error_details = []
        error_details.append(f"股票代码: {ticker}")
        error_details.append(f"市场区域: {region}")
        error_details.append(f"查询日期范围: {start_date} 到 {end_date}")
        error_details.append(f"缓存数据: {len(all_cached_prices)} 条")
        error_details.append(f"新获取数据: {len(new_prices)} 条")
        error_details.append(f"缺失日期范围: {len(missing_ranges)} 个")
        
        error_msg = f"无法获取 {ticker} 在 {start_date} 到 {end_date} 期间的价格数据\n" + "\n".join([f"  - {detail}" for detail in error_details])
        raise Exception(error_msg)
    
    cache_ratio = len(all_cached_prices) / len(filtered_prices) * 100 if filtered_prices else 0
    print(f"📊 {ticker} 数据获取完成: 总计 {len(filtered_prices)} 条 (缓存命中率: {cache_ratio:.1f}%)")
    
    return filtered_prices


def _calculate_missing_date_ranges(start_date: str, end_date: str, cached_dates: set) -> list[tuple[str, str]]:
    """
    计算缺失的日期范围
    
    Args:
        start_date: 请求的开始日期
        end_date: 请求的结束日期  
        cached_dates: 已缓存的日期集合
        
    Returns:
        缺失日期范围的列表 [(start1, end1), (start2, end2), ...]
    """
    from datetime import datetime, timedelta
    
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    # 生成请求范围内的所有日期（只包括工作日）
    all_dates = []
    current_dt = start_dt
    while current_dt <= end_dt:
        # 只包括工作日（0-6代表周一到周日，0-4是工作日）
        if current_dt.weekday() < 5:  # 周一到周五
            all_dates.append(current_dt.strftime("%Y-%m-%d"))
        current_dt += timedelta(days=1)
    
    # 找出缺失的日期
    missing_dates = [date for date in all_dates if date not in cached_dates]
    
    if not missing_dates:
        return []
    
    # 将连续的缺失日期合并为范围
    ranges = []
    range_start = missing_dates[0]
    range_end = missing_dates[0]
    
    for i in range(1, len(missing_dates)):
        current_date = missing_dates[i]
        prev_date = missing_dates[i-1]
        
        # 检查是否连续（考虑工作日）
        prev_dt = datetime.strptime(prev_date, "%Y-%m-%d")
        current_dt = datetime.strptime(current_date, "%Y-%m-%d")
        
        # 计算中间的工作日数量
        next_workday = prev_dt + timedelta(days=1)
        while next_workday.weekday() >= 5:  # 跳过周末
            next_workday += timedelta(days=1)
        
        if next_workday.strftime("%Y-%m-%d") == current_date:
            # 连续的工作日
            range_end = current_date
        else:
            # 不连续，结束当前范围，开始新范围
            ranges.append((range_start, range_end))
            range_start = current_date
            range_end = current_date
    
    # 添加最后一个范围
    ranges.append((range_start, range_end))
    
    return ranges


def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    region: str = None,
) -> list[FinancialMetrics]:
    """Fetch financial metrics with multi-level cache: memory -> SQLite -> iTick API.
    
    Args:
        ticker: 股票代码
        end_date: 结束日期
        period: 报告期间
        limit: 数据限制
        region: 市场区域 (us, hk, sh, sz, sg, jp)，如果不提供则自动检测
    """
    # 如果没有提供region，则自动检测
    if region is None:
        region = _detect_ticker_region(ticker)
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
        metrics = _fetch_financial_metrics_from_itick(ticker, end_date, period, limit, region)
        
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


def clear_ticker_cache(ticker: str):
    """清除特定股票的所有缓存数据"""
    try:
        # 清除内存缓存
        _cache.clear_ticker_cache(ticker)
        # 清除数据库缓存
        return _db_manager.clear_ticker_cache(ticker)
    except Exception as e:
        print(f"⚠️ 清除 {ticker} 缓存失败: {str(e)}")
        return 0


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

def _fetch_prices_from_itick(ticker: str, start_date: str, end_date: str, region: str = 'us') -> list[Price]:
    """从iTick API获取价格数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        region: 市场区域 (us, hk, sh, sz, sg, jp)
    """
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
        region=region
    )
    
    # 转换为Price对象
    return itick_api.convert_to_price_objects(kline_data, ticker)








def _fetch_financial_metrics_from_itick(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    region: str = 'us',
) -> list[FinancialMetrics]:
    """从iTick API获取财务指标
    
    Args:
        ticker: 股票代码
        end_date: 结束日期
        period: 报告期间
        limit: 数据限制
        region: 市场区域 (us, hk, sh, sz, sg, jp)
    """
    itick_api = get_itick_api()
    
    # 获取财务数据
    financial_data = itick_api.get_financial_data(ticker, region=region)
    
    # 转换为FinancialMetrics对象
    return itick_api.convert_to_financial_metrics(financial_data, ticker)



