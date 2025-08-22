"""
基于Yahoo Finance的API模块
使用yfinance库获取免费的股票数据
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
import sys
import os
import time
import random

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.models import Price, FinancialMetrics
from data.cache import get_cache

# 全局缓存实例
_cache = get_cache()


def get_prices_yfinance(ticker: str, start_date: str, end_date: str) -> List[Price]:
    """
    从Yahoo Finance获取价格数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
    
    Returns:
        Price对象列表
    """
    # 检查缓存
    if cached_data := _cache.get_prices(ticker):
        # 过滤缓存数据
        filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
        if filtered_data:
            return filtered_data

    try:
        # 使用yfinance获取数据
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date, interval="1d")
        
        if hist.empty:
            print(f"⚠️ 未获取到{ticker}的价格数据")
            return []
        
        prices = []
        for date, row in hist.iterrows():
            prices.append(Price(
                open=round(float(row['Open']), 2),
                close=round(float(row['Close']), 2),
                high=round(float(row['High']), 2),
                low=round(float(row['Low']), 2),
                volume=int(row['Volume']),
                time=date.strftime("%Y-%m-%d")
            ))
        
        # 缓存结果
        _cache.set_prices(ticker, [p.model_dump() for p in prices])
        print(f"✅ 成功获取{ticker}的{len(prices)}条价格数据")
        return prices
        
    except Exception as e:
        print(f"❌ 获取{ticker}价格数据失败: {str(e)}")
        return []


def get_financial_metrics_yfinance(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> List[FinancialMetrics]:
    """
    从Yahoo Finance获取财务指标
    
    Args:
        ticker: 股票代码
        end_date: 结束日期
        period: 期间（ttm表示过去12个月）
        limit: 限制数量
    
    Returns:
        FinancialMetrics对象列表
    """
    # 检查缓存
    if cached_data := _cache.get_financial_metrics(ticker):
        filtered_data = [FinancialMetrics(**metric) for metric in cached_data if metric["report_period"] <= end_date]
        filtered_data.sort(key=lambda x: x.report_period, reverse=True)
        if filtered_data:
            return filtered_data[:limit]

    try:
        # 使用yfinance获取股票信息
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info:
            print(f"⚠️ 未获取到{ticker}的财务信息")
            return []
        
        # 获取财务报表数据
        try:
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
        except Exception:
            financials = pd.DataFrame()
            balance_sheet = pd.DataFrame()
            cash_flow = pd.DataFrame()
        
        # 安全获取数据的辅助函数
        def safe_get(data, key, default=None):
            return data.get(key, default)
        
        def safe_divide(a, b):
            if a is not None and b is not None and b != 0:
                return a / b
            return None
        
        # 从info中提取基本财务指标
        current_price = safe_get(info, 'currentPrice', safe_get(info, 'regularMarketPrice'))
        shares_outstanding = safe_get(info, 'sharesOutstanding')
        market_cap = safe_get(info, 'marketCap')
        
        # 计算市值（如果没有直接提供）
        if not market_cap and current_price and shares_outstanding:
            market_cap = current_price * shares_outstanding
        
        # 构建财务指标对象
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        report_date = (end_dt - timedelta(days=90)).strftime("%Y-%m-%d")
        
        metrics = FinancialMetrics(
            ticker=ticker,
            report_period=report_date,
            period=period,
            currency=safe_get(info, 'currency', 'USD'),
            market_cap=market_cap,
            enterprise_value=safe_get(info, 'enterpriseValue'),
            price_to_earnings_ratio=safe_get(info, 'trailingPE'),
            price_to_book_ratio=safe_get(info, 'priceToBook'),
            price_to_sales_ratio=safe_get(info, 'priceToSalesTrailing12Months'),
            enterprise_value_to_ebitda_ratio=safe_get(info, 'enterpriseToEbitda'),
            enterprise_value_to_revenue_ratio=safe_get(info, 'enterpriseToRevenue'),
            free_cash_flow_yield=safe_divide(safe_get(info, 'freeCashflow'), market_cap),
            peg_ratio=safe_get(info, 'pegRatio'),
            gross_margin=safe_get(info, 'grossMargins'),
            operating_margin=safe_get(info, 'operatingMargins'),
            net_margin=safe_get(info, 'profitMargins'),
            return_on_equity=safe_get(info, 'returnOnEquity'),
            return_on_assets=safe_get(info, 'returnOnAssets'),
            return_on_invested_capital=None,  # yfinance不提供
            asset_turnover=None,  # 需要计算
            inventory_turnover=None,  # 需要计算
            receivables_turnover=None,  # 需要计算
            days_sales_outstanding=None,  # 需要计算
            operating_cycle=None,  # 需要计算
            working_capital_turnover=None,  # 需要计算
            current_ratio=safe_get(info, 'currentRatio'),
            quick_ratio=safe_get(info, 'quickRatio'),
            cash_ratio=None,  # 需要计算
            operating_cash_flow_ratio=None,  # 需要计算
            debt_to_equity=safe_get(info, 'debtToEquity'),
            debt_to_assets=None,  # 需要计算
            interest_coverage=None,  # 需要计算
            revenue_growth=safe_get(info, 'revenueGrowth'),
            earnings_growth=safe_get(info, 'earningsGrowth'),
            book_value_growth=None,  # yfinance不直接提供
            earnings_per_share_growth=safe_get(info, 'earningsQuarterlyGrowth'),
            free_cash_flow_growth=None,  # 需要计算
            operating_income_growth=None,  # 需要计算
            ebitda_growth=None,  # 需要计算
            payout_ratio=safe_get(info, 'payoutRatio'),
            earnings_per_share=safe_get(info, 'trailingEps'),
            book_value_per_share=safe_get(info, 'bookValue'),
            free_cash_flow_per_share=safe_divide(safe_get(info, 'freeCashflow'), shares_outstanding)
        )
        
        # 缓存结果
        _cache.set_financial_metrics(ticker, [metrics.model_dump()])
        print(f"✅ 成功获取{ticker}的财务指标数据")
        return [metrics]
        
    except Exception as e:
        print(f"❌ 获取{ticker}财务指标失败: {str(e)}")
        return []


def prices_to_df_yfinance(prices: List[Price]) -> pd.DataFrame:
    """将价格数据转换为DataFrame"""
    if not prices:
        return pd.DataFrame()
        
    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    
    # 确保数值列是数值类型
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df.sort_index(inplace=True)
    return df


def get_price_data_yfinance(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取价格数据并转换为DataFrame"""
    prices = get_prices_yfinance(ticker, start_date, end_date)
    return prices_to_df_yfinance(prices)


def get_company_info_yfinance(ticker: str) -> dict:
    """获取公司基本信息"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "country": info.get("country", "Unknown"),
            "website": info.get("website", ""),
            "description": info.get("longBusinessSummary", "")
        }
    except Exception as e:
        print(f"❌ 获取{ticker}公司信息失败: {str(e)}")
        return {}


def test_yfinance_connection() -> bool:
    """测试yfinance连接"""
    try:
        # 测试获取AAPL的简单数据
        stock = yf.Ticker("AAPL")
        info = stock.info
        # 检查是否成功获取到数据
        return bool(info and len(info) > 10)  # 如果获取到足够的信息就认为成功
    except Exception as e:
        print(f"测试连接失败: {e}")
        return False


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试Yahoo Finance API连接...")
    
    if test_yfinance_connection():
        print("✅ Yahoo Finance API连接成功")
        
        # 测试获取价格数据
        print("\n📊 测试获取AAPL价格数据...")
        prices = get_prices_yfinance("AAPL", "2024-01-01", "2024-01-10")
        if prices:
            print(f"✅ 成功获取{len(prices)}条价格数据")
            print(f"最新价格: ${prices[-1].close}")
        
        # 测试获取财务指标
        print("\n💰 测试获取AAPL财务指标...")
        metrics = get_financial_metrics_yfinance("AAPL", "2024-01-10")
        if metrics:
            print(f"✅ 成功获取财务指标")
            print(f"P/E比率: {metrics[0].price_to_earnings_ratio}")
    else:
        print("❌ Yahoo Finance API连接失败")