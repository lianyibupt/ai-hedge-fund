"""
Yahoo Finance RapidAPI MCP 调用模块
提供基于 Yahoo Finance RapidAPI 的股票数据获取功能
这是一个独立的调用入口，专门用于 RapidAPI 数据源
"""

from typing import List, Dict, Any, Optional
from data.models import Price, FinancialMetrics
from .rapidapi_yahoo_finance_wrapper import (
    get_rapidapi_yahoo_wrapper,
    fetch_prices_from_rapidapi_yahoo_mcp,
    fetch_financial_metrics_from_rapidapi_yahoo_mcp,
    test_rapidapi_yahoo_mcp_connection
)
from datetime import datetime, timedelta
import json


def fetch_prices_from_rapidapi_yahoo(
    ticker: str, 
    start_date: str, 
    end_date: str, 
    region: str = 'us'
) -> List[Price]:
    """
    从 Yahoo Finance RapidAPI 获取价格数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        region: 市场区域 (所有区域都支持)
    
    Returns:
        Price 对象列表
    """
    try:
        print(f"🔄 从 Yahoo Finance RapidAPI 获取 {ticker} 价格数据 ({start_date} 到 {end_date})")
        
        # 直接调用 RapidAPI Yahoo Finance
        prices = fetch_prices_from_rapidapi_yahoo_mcp(ticker, start_date, end_date, region)
        
        if not prices:
            print(f"⚠️ Yahoo Finance RapidAPI 返回空数据，股票代码: {ticker}")
            return []
        
        print(f"✅ 成功从 Yahoo Finance RapidAPI 获取 {len(prices)} 条价格数据")
        return prices
        
    except Exception as e:
        print(f"❌ Yahoo Finance RapidAPI 价格数据获取失败: {str(e)}")
        raise Exception(f"无法从 Yahoo Finance RapidAPI 获取 {ticker} 的价格数据: {str(e)}")


def fetch_financial_metrics_from_rapidapi_yahoo(
    ticker: str, 
    end_date: str, 
    period: str = "ttm", 
    limit: int = 30, 
    region: str = 'us'
) -> List[FinancialMetrics]:
    """
    从 Yahoo Finance RapidAPI 获取财务指标
    
    Args:
        ticker: 股票代码
        end_date: 结束日期
        period: 报告期间
        limit: 数据限制
        region: 市场区域
    
    Returns:
        FinancialMetrics 对象列表
    """
    try:
        print(f"🔄 从 Yahoo Finance RapidAPI 获取 {ticker} 财务指标")
        
        # 直接调用 RapidAPI Yahoo Finance
        metrics = fetch_financial_metrics_from_rapidapi_yahoo_mcp(ticker, end_date, period, limit, region)
        
        if not metrics:
            print(f"⚠️ Yahoo Finance RapidAPI 返回空财务数据，股票代码: {ticker}")
            return []
        
        print(f"✅ 成功从 Yahoo Finance RapidAPI 获取财务指标")
        return metrics[:limit]
        
    except Exception as e:
        print(f"❌ Yahoo Finance RapidAPI 财务指标获取失败: {str(e)}")
        raise Exception(f"无法从 Yahoo Finance RapidAPI 获取 {ticker} 的财务指标: {str(e)}")


def test_rapidapi_yahoo_connection() -> bool:
    """
    测试 Yahoo Finance RapidAPI 连接
    
    Returns:
        连接是否成功
    """
    try:
        return test_rapidapi_yahoo_mcp_connection()
    except Exception as e:
        print(f"❌ Yahoo Finance RapidAPI 连接测试失败: {str(e)}")
        return False


# 高级功能函数

def get_real_time_quote_rapidapi(ticker: str) -> Optional[Price]:
    """
    获取实时报价
    
    Args:
        ticker: 股票代码
        
    Returns:
        Price 对象或 None
    """
    try:
        wrapper = get_rapidapi_yahoo_wrapper()
        return wrapper.get_real_time_quote(ticker)
    except Exception as e:
        print(f"❌ 获取 {ticker} 实时报价失败: {str(e)}")
        return None


def get_intraday_prices_rapidapi(
    ticker: str, 
    interval: str = "1h", 
    limit: int = 100
) -> List[Price]:
    """
    获取盘中价格数据
    
    Args:
        ticker: 股票代码
        interval: 时间间隔 (1m, 5m, 15m, 30m, 1h)
        limit: 数据条数限制
        
    Returns:
        Price 对象列表
    """
    try:
        wrapper = get_rapidapi_yahoo_wrapper()
        return wrapper.get_intraday_prices(ticker, interval, limit)
    except Exception as e:
        print(f"❌ 获取 {ticker} 盘中数据失败: {str(e)}")
        return []


def get_multiple_stocks_data_rapidapi(
    tickers: List[str], 
    start_date: str, 
    end_date: str
) -> Dict[str, List[Price]]:
    """
    批量获取多个股票的价格数据
    
    Args:
        tickers: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        股票代码到价格数据的映射
    """
    results = {}
    
    for ticker in tickers:
        try:
            print(f"🔄 批量获取 {ticker} 数据...")
            prices = fetch_prices_from_rapidapi_yahoo(ticker, start_date, end_date)
            if prices:
                results[ticker] = prices
                print(f"✅ {ticker}: {len(prices)} 条数据")
            else:
                print(f"⚠️ {ticker}: 无数据")
                results[ticker] = []
        except Exception as e:
            print(f"❌ {ticker} 获取失败: {str(e)}")
            results[ticker] = []
    
    return results


def get_market_overview_rapidapi(market_symbols: List[str]) -> Dict[str, Any]:
    """
    获取市场概览数据
    
    Args:
        market_symbols: 市场代表性股票代码列表
        
    Returns:
        市场概览数据
    """
    overview = {
        "timestamp": datetime.now().isoformat(),
        "stocks": {},
        "summary": {
            "total_stocks": len(market_symbols),
            "successful": 0,
            "failed": 0
        }
    }
    
    wrapper = get_rapidapi_yahoo_wrapper()
    
    for symbol in market_symbols:
        try:
            quote = wrapper.get_real_time_quote(symbol)
            if quote:
                overview["stocks"][symbol] = {
                    "price": quote.close,
                    "open": quote.open,
                    "high": quote.high,
                    "low": quote.low,
                    "volume": quote.volume,
                    "change": quote.close - quote.open,
                    "change_percent": ((quote.close - quote.open) / quote.open * 100) if quote.open > 0 else 0
                }
                overview["summary"]["successful"] += 1
            else:
                overview["stocks"][symbol] = None
                overview["summary"]["failed"] += 1
        except Exception as e:
            print(f"❌ {symbol} 市场数据获取失败: {str(e)}")
            overview["stocks"][symbol] = None
            overview["summary"]["failed"] += 1
    
    return overview


# 用于个人化交易系统的专用函数

def get_personal_trading_data_rapidapi(
    ticker: str, 
    start_date: str, 
    end_date: str
) -> Dict[str, Any]:
    """
    为个人化交易系统获取完整数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        包含价格数据和财务指标的完整数据包
    """
    try:
        print(f"🔄 为个人交易系统获取 {ticker} 完整数据...")
        
        # 获取价格数据
        prices = fetch_prices_from_rapidapi_yahoo(ticker, start_date, end_date)
        
        # 获取财务指标
        financial_metrics = fetch_financial_metrics_from_rapidapi_yahoo(ticker, end_date)
        
        # 获取实时报价
        real_time_quote = get_real_time_quote_rapidapi(ticker)
        
        # 获取盘中数据（最近1小时）
        intraday_data = get_intraday_prices_rapidapi(ticker, "1h", 24)  # 最近24小时数据
        
        result = {
            "ticker": ticker,
            "data_source": "Yahoo Finance RapidAPI",
            "timestamp": datetime.now().isoformat(),
            "date_range": {
                "start": start_date,
                "end": end_date
            },
            "historical_prices": [p.model_dump() for p in prices] if prices else [],
            "financial_metrics": [m.model_dump() for m in financial_metrics] if financial_metrics else [],
            "real_time_quote": real_time_quote.model_dump() if real_time_quote else None,
            "intraday_data": [p.model_dump() for p in intraday_data] if intraday_data else [],
            "data_quality": {
                "historical_count": len(prices) if prices else 0,
                "has_financial_data": bool(financial_metrics),
                "has_real_time_data": bool(real_time_quote),
                "has_intraday_data": bool(intraday_data)
            }
        }
        
        print(f"✅ 个人交易数据获取完成:")
        print(f"   - 历史价格: {result['data_quality']['historical_count']} 条")
        print(f"   - 财务指标: {'✓' if result['data_quality']['has_financial_data'] else '✗'}")
        print(f"   - 实时报价: {'✓' if result['data_quality']['has_real_time_data'] else '✗'}")
        print(f"   - 盘中数据: {'✓' if result['data_quality']['has_intraday_data'] else '✗'}")
        
        return result
        
    except Exception as e:
        print(f"❌ 个人交易数据获取失败: {str(e)}")
        raise Exception(f"无法为个人交易系统获取 {ticker} 的完整数据: {str(e)}")


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试 Yahoo Finance RapidAPI MCP 模块...")
    
    try:
        # 测试连接
        if test_rapidapi_yahoo_connection():
            print("✅ 连接测试成功")
            
            # 测试获取单个股票数据
            print("\n📊 测试获取 AAPL 历史数据...")
            prices = fetch_prices_from_rapidapi_yahoo("AAPL", "2024-08-01", "2024-08-10")
            if prices:
                print(f"✅ 成功获取 {len(prices)} 条价格数据")
                for i, price in enumerate(prices[:3]):
                    print(f"  {i+1}. {price.time}: ${price.close}")
            
            # 测试实时报价
            print("\n📱 测试获取实时报价...")
            quote = get_real_time_quote_rapidapi("AAPL")
            if quote:
                print(f"✅ 实时报价: ${quote.close}")
            
            # 测试个人交易数据
            print("\n💼 测试个人交易数据获取...")
            trading_data = get_personal_trading_data_rapidapi("AAPL", "2024-08-01", "2024-08-10")
            if trading_data:
                print(f"✅ 个人交易数据获取成功")
                print(f"   数据源: {trading_data['data_source']}")
                print(f"   数据质量: {trading_data['data_quality']}")
        else:
            print("❌ 连接测试失败")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")