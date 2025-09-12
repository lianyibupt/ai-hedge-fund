"""
Alpha Vantage HTTP API 调用模块
提供基于 Alpha Vantage HTTP API 的股票数据获取功能
"""

from typing import List, Dict, Any, Optional
from data.models import Price, FinancialMetrics
from .alphavantage_api import get_alphavantage_api
from .alphavantage_mcp_wrapper import get_alphavantage_wrapper
from datetime import datetime, timedelta
import json





def fetch_prices_from_alphavantage(ticker: str, start_date: str, end_date: str, region: str = 'us') -> List[Price]:
    """
    从 Alpha Vantage HTTP API 获取价格数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        region: 市场区域 (Alpha Vantage 主要支持美股)
    
    Returns:
        Price 对象列表
    """
    try:
        # Alpha Vantage 主要支持美股
        if region != 'us':
            print(f"⚠️ Alpha Vantage 主要支持美股，{ticker} 市场区域 {region} 可能不支持")
        
        wrapper = get_alphavantage_wrapper()
        
        print(f"🔄 从 Alpha Vantage HTTP API 获取 {ticker} 价格数据 ({start_date} 到 {end_date})")
        
        # 使用包装器获取数据
        prices = wrapper.get_daily_prices(ticker, start_date, end_date)
        
        if not prices:
            print(f"⚠️ Alpha Vantage HTTP API 返回空数据，股票代码: {ticker}")
            return []
        
        print(f"✅ 成功从 Alpha Vantage HTTP API 获取 {len(prices)} 条价格数据")
        return prices
        
    except Exception as e:
        print(f"❌ Alpha Vantage HTTP API 价格数据获取失败: {str(e)}")
        raise Exception(f"无法从 Alpha Vantage HTTP API 获取 {ticker} 的价格数据: {str(e)}")


def fetch_financial_metrics_from_alphavantage(
    ticker: str, 
    end_date: str, 
    period: str = "ttm", 
    limit: int = 10, 
    region: str = 'us'
) -> List[FinancialMetrics]:
    """
    从 Alpha Vantage HTTP API 获取财务指标
    
    注意：此函数已弃用，建议使用 Finnhub API 获取财务数据
    
    Args:
        ticker: 股票代码
        end_date: 结束日期
        period: 报告期间
        limit: 数据限制
        region: 市场区域
    
    Returns:
        FinancialMetrics 对象列表
    """
    print(f"⚠️ Alpha Vantage 财务数据接口已弃用，建议使用 Finnhub API")
    print(f"🔄 尝试从 Alpha Vantage 获取基础财务数据...")
    
    try:
        if region != 'us':
            print(f"⚠️ Alpha Vantage 主要支持美股财务数据，{ticker} 市场区域 {region} 可能不支持")
        
        wrapper = get_alphavantage_wrapper()
        
        print(f"🔄 从 Alpha Vantage HTTP API 获取 {ticker} 财务指标")
        
        # 使用包装器获取数据
        metrics = wrapper.get_company_overview(ticker)
        
        if not metrics:
            print(f"⚠️ Alpha Vantage HTTP API 返回空财务数据，股票代码: {ticker}")
            return []
        
        print(f"✅ 成功从 Alpha Vantage HTTP API 获取财务指标（有限数据）")
        return metrics[:limit]
        
    except Exception as e:
        print(f"❌ Alpha Vantage HTTP API 财务指标获取失败: {str(e)}")
        print(f"💡 建议使用 Finnhub API 获取更完整的财务数据")
        raise Exception(f"无法从 Alpha Vantage HTTP API 获取 {ticker} 的财务指标: {str(e)}")


def test_alphavantage_mcp_connection() -> bool:
    """
    测试 Alpha Vantage HTTP API 连接
    
    Returns:
        连接是否成功
    """
    try:
        wrapper = get_alphavantage_wrapper()
        # 简单测试：获取一个知名股票的报价
        test_quote = wrapper.get_real_time_quote("AAPL")
        
        if test_quote:
            print(f"✅ Alpha Vantage HTTP API 连接测试成功")
            return True
        else:
            print(f"❌ Alpha Vantage HTTP API 连接测试失败：无法获取测试数据")
            return False
            
    except Exception as e:
        print(f"❌ Alpha Vantage HTTP API 连接测试失败: {str(e)}")
        return False


# 用于实际 MCP 工具调用的辅助函数