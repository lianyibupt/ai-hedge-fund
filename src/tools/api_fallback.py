"""
API fallback模块 - 已废弃

注意：此文件已被重构，不再提供mock数据回退机制。
系统现在严格依赖 iTick API，当API不可用时会直接报错，
而不是回退到模拟数据。

如需使用数据获取功能，请直接使用 tools.api 模块。
"""

import warnings
from typing import List
from data.models import Price, FinancialMetrics


def get_prices_with_fallback(ticker: str, start_date: str, end_date: str) -> List[Price]:
    """
    此函数已废弃。请使用 tools.api.get_prices 代替。
    
    Raises:
        DeprecationWarning: 提示使用新的API
    """
    warnings.warn(
        "get_prices_with_fallback 已废弃，请使用 tools.api.get_prices",
        DeprecationWarning,
        stacklevel=2
    )
    
    # 重定向到新的API
    from .api import get_prices
    return get_prices(ticker, start_date, end_date)


def get_financial_metrics_with_fallback(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> List[FinancialMetrics]:
    """
    此函数已废弃。请使用 tools.api.get_financial_metrics 代替。
    
    Raises:
        DeprecationWarning: 提示使用新的API
    """
    warnings.warn(
        "get_financial_metrics_with_fallback 已废弃，请使用 tools.api.get_financial_metrics",
        DeprecationWarning,
        stacklevel=2
    )
    
    # 重定向到新的API
    from .api import get_financial_metrics
    return get_financial_metrics(ticker, end_date, period, limit)


# 移除所有mock数据生成器和相关函数
# 以确保系统不会意外使用模拟数据


# 如果有代码尝试直接访问MockDataGenerator，将抛出异常
class MockDataGenerator:
    def __init__(self):
        raise RuntimeError(
            "MockDataGenerator 已被禁用。系统现在严格依赖 iTick API，"
            "不再提供mock数据回退功能。请确保 iTick API 配置正确。"
        )

    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df


def get_price_data_with_fallback(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取价格数据并转换为DataFrame，带有回退机制"""
    prices = get_prices_with_fallback(ticker, start_date, end_date)
    return prices_to_df(prices)