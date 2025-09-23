"""
Yahoo Finance RapidAPI 包装器模块
提供集成到主API系统的接口
"""

from typing import List, Dict, Any, Optional
from data.models import Price, FinancialMetrics
from .rapidapi_yahoo_finance import (
    get_rapidapi_yahoo_finance,
    fetch_prices_from_rapidapi_yahoo,
    fetch_financial_metrics_from_rapidapi_yahoo,
    test_rapidapi_yahoo_connection
)
from datetime import datetime, timedelta
import json


class RapidAPIYahooWrapper:
    """Yahoo Finance RapidAPI 包装器"""
    
    def __init__(self):
        self.api = get_rapidapi_yahoo_finance()
        print(f"🔧 Yahoo Finance RapidAPI 包装器初始化成功")
    
    def get_daily_prices(
        self, 
        ticker: str, 
        start_date: str, 
        end_date: str,
        interval: str = "1d"
    ) -> List[Price]:
        """
        获取每日价格数据
        
        Args:
            ticker: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            interval: 时间间隔 (1d, 1h, 30m, 15m, 5m, 1m)
            
        Returns:
            Price 对象列表
        """
        try:
            print(f"🔄 调用 Yahoo Finance RapidAPI 获取 {ticker} 的价格数据...")
            
            # 使用新的 RapidAPI 获取数据
            prices = fetch_prices_from_rapidapi_yahoo(ticker, start_date, end_date, interval)
            
            if prices:
                # 按日期过滤到请求范围，保持倒序（最新在前）
                filtered_prices = [p for p in prices if start_date <= p.time <= end_date]
                # 确保按日期倒序排列
                filtered_prices.sort(key=lambda x: x.time, reverse=True)
                
                print(f"✅ 成功获取 {len(filtered_prices)} 条价格数据")
                return filtered_prices
            else:
                print(f"⚠️ Yahoo Finance RapidAPI 返回空数据")
                return []
                
        except Exception as e:
            print(f"🚫 Yahoo Finance RapidAPI 调用失败: {str(e)}")
            return []
    
    def get_real_time_quote(self, ticker: str) -> Optional[Price]:
        """
        获取实时报价
        
        Args:
            ticker: 股票代码
            
        Returns:
            Price 对象或 None
        """
        try:
            print(f"🔄 调用 Yahoo Finance RapidAPI 获取 {ticker} 的实时报价...")
            
            # 使用 RapidAPI 获取实时报价
            quote_data = self.api.get_real_time_quote(ticker)
            
            if quote_data:
                price = self.api.convert_quote_to_price(quote_data, ticker)
                if price:
                    print(f"✅ 成功获取 {ticker} 的实时报价: ${price.close}")
                    return price
                else:
                    print(f"⚠️ 实时报价数据转换失败")
                    return None
            else:
                print(f"⚠️ Yahoo Finance RapidAPI 返回空报价数据")
                return None
                
        except Exception as e:
            print(f"🚫 Yahoo Finance RapidAPI 实时报价获取失败: {str(e)}")
            return None
    
    def get_company_overview(self, ticker: str) -> List[FinancialMetrics]:
        """
        获取公司概览和财务指标
        
        Args:
            ticker: 股票代码
            
        Returns:
            FinancialMetrics 对象列表
        """
        try:
            print(f"🔄 调用 Yahoo Finance RapidAPI 获取 {ticker} 的公司概览...")
            
            # 使用新的 RapidAPI 获取财务指标
            metrics = fetch_financial_metrics_from_rapidapi_yahoo(ticker, datetime.now().strftime("%Y-%m-%d"))
            
            if metrics:
                print(f"✅ 成功获取 {ticker} 的公司概览")
                return metrics
            else:
                print(f"⚠️ 公司概览数据转换失败")
                return []
                
        except Exception as e:
            print(f"🚫 Yahoo Finance RapidAPI 公司数据获取失败: {str(e)}")
            return []
    
    def get_intraday_prices(
        self, 
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
            print(f"🔄 调用 Yahoo Finance RapidAPI 获取 {ticker} 的盘中数据 (间隔: {interval})...")
            
            # 使用当前日期作为结束日期
            end_date = datetime.now().strftime("%Y-%m-%d")
            # 开始日期设为一周前
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
            # 直接调用 API 获取盘中数据
            history_data = self.api.get_historical_data(ticker, interval=interval, limit=limit)
            
            if history_data:
                prices = self.api.convert_history_to_prices(history_data, ticker, start_date, end_date)
                if prices:
                    print(f"✅ 成功获取 {len(prices)} 条盘中数据")
                    return prices[:limit]  # 限制返回数量
                else:
                    print(f"⚠️ 盘中数据转换失败")
                    return []
            else:
                print(f"⚠️ Yahoo Finance RapidAPI 返回空盘中数据")
                return []
                
        except Exception as e:
            print(f"🚫 Yahoo Finance RapidAPI 盘中数据获取失败: {str(e)}")
            return []


# 全局实例
_rapidapi_yahoo_wrapper = None


def get_rapidapi_yahoo_wrapper() -> RapidAPIYahooWrapper:
    """获取 Yahoo Finance RapidAPI 包装器实例"""
    global _rapidapi_yahoo_wrapper
    if _rapidapi_yahoo_wrapper is None:
        _rapidapi_yahoo_wrapper = RapidAPIYahooWrapper()
    return _rapidapi_yahoo_wrapper


# 便捷调用函数，可直接在主API模块中使用
def fetch_prices_from_rapidapi_yahoo_mcp(
    ticker: str, 
    start_date: str, 
    end_date: str, 
    region: str = 'us'
) -> List[Price]:
    """
    从 Yahoo Finance RapidAPI 获取价格数据 (MCP兼容接口)
    
    Args:
        ticker: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        region: 市场区域 (所有区域都支持，主要是美股)
    
    Returns:
        Price 对象列表
    """
    try:
        wrapper = get_rapidapi_yahoo_wrapper()
        
        print(f"🔄 从 Yahoo Finance RapidAPI 获取 {ticker} 价格数据 ({start_date} 到 {end_date})")
        
        # 使用包装器获取数据
        prices = wrapper.get_daily_prices(ticker, start_date, end_date)
        
        if not prices:
            print(f"⚠️ Yahoo Finance RapidAPI 返回空数据，股票代码: {ticker}")
            return []
        
        print(f"✅ 成功从 Yahoo Finance RapidAPI 获取 {len(prices)} 条价格数据")
        return prices
        
    except Exception as e:
        print(f"❌ Yahoo Finance RapidAPI 价格数据获取失败: {str(e)}")
        raise Exception(f"无法从 Yahoo Finance RapidAPI 获取 {ticker} 的价格数据: {str(e)}")


def fetch_financial_metrics_from_rapidapi_yahoo_mcp(
    ticker: str, 
    end_date: str, 
    period: str = "ttm", 
    limit: int = 10, 
    region: str = 'us'
) -> List[FinancialMetrics]:
    """
    从 Yahoo Finance RapidAPI 获取财务指标 (MCP兼容接口)
    
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
        wrapper = get_rapidapi_yahoo_wrapper()
        
        print(f"🔄 从 Yahoo Finance RapidAPI 获取 {ticker} 财务指标")
        
        # 使用包装器获取数据
        metrics = wrapper.get_company_overview(ticker)
        
        if not metrics:
            print(f"⚠️ Yahoo Finance RapidAPI 返回空财务数据，股票代码: {ticker}")
            return []
        
        print(f"✅ 成功从 Yahoo Finance RapidAPI 获取财务指标")
        return metrics[:limit]
        
    except Exception as e:
        print(f"❌ Yahoo Finance RapidAPI 财务指标获取失败: {str(e)}")
        raise Exception(f"无法从 Yahoo Finance RapidAPI 获取 {ticker} 的财务指标: {str(e)}")


def test_rapidapi_yahoo_mcp_connection() -> bool:
    """
    测试 Yahoo Finance RapidAPI 连接 (MCP兼容接口)
    
    Returns:
        连接是否成功
    """
    try:
        return test_rapidapi_yahoo_connection()
    except Exception as e:
        print(f"❌ Yahoo Finance RapidAPI 连接测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试 Yahoo Finance RapidAPI 包装器...")
    
    try:
        # 测试连接
        if test_rapidapi_yahoo_mcp_connection():
            print("✅ 连接测试成功")
            
            # 测试获取历史数据
            print("\n📊 测试获取 AAPL 历史数据...")
            prices = fetch_prices_from_rapidapi_yahoo_mcp("AAPL", "2024-08-01", "2024-08-10")
            if prices:
                print(f"✅ 成功获取 {len(prices)} 条价格数据")
                for i, price in enumerate(prices[:3]):  # 显示前3条
                    print(f"  {i+1}. {price.time}: 开盘=${price.open}, 收盘=${price.close}, 成交量={price.volume}")
            
            # 测试获取财务指标
            print("\n💰 测试获取 AAPL 财务指标...")
            metrics = fetch_financial_metrics_from_rapidapi_yahoo_mcp("AAPL", "2024-08-10")
            if metrics:
                print(f"✅ 成功获取财务指标")
                metric = metrics[0]
                print(f"  市值: {metric.market_cap}")
                print(f"  P/E 比率: {metric.price_to_earnings_ratio}")
                print(f"  P/B 比率: {metric.price_to_book_ratio}")
        else:
            print("❌ 连接测试失败")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")