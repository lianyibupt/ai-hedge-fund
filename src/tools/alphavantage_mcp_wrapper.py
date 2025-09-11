"""
Alpha Vantage HTTP API 工具调用包装器
提供基于HTTP API的Alpha Vantage数据获取功能，集成到交易应用中
"""

from typing import List, Dict, Any, Optional
from data.models import Price, FinancialMetrics
from .alphavantage_api import get_alphavantage_api
from datetime import datetime, timedelta
import json


class AlphaVantageHTTPWrapper:
    """Alpha Vantage HTTP API 包装器"""
    
    def __init__(self):
        self.api = get_alphavantage_api()
        print(f"🔧 Alpha Vantage HTTP 包装器初始化成功")
    
    def get_daily_prices(self, ticker: str, start_date: str, end_date: str) -> List[Price]:
        """
        获取每日价格数据
        
        Args:
            ticker: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Price 对象列表
        """
        try:
            print(f"🔄 调用 Alpha Vantage HTTP API 获取 {ticker} 的每日价格数据...")
            
            # 直接使用HTTP API获取数据
            daily_data = self.api.get_historical_data(ticker, start_date, end_date, "daily")
            
            if daily_data:
                prices = self.api.convert_daily_to_prices(daily_data, ticker)
                # 按日期过滤到请求范围，保持倒序（最新在前）
                filtered_prices = [p for p in prices if start_date <= p.time <= end_date]
                # 确保按日期倒序排列
                filtered_prices.sort(key=lambda x: x.time, reverse=True)
                
                print(f"✅ 成功获取 {len(filtered_prices)} 条价格数据")
                return filtered_prices
            else:
                print(f"⚠️ Alpha Vantage API 返回空数据")
                return []
                
        except Exception as e:
            print(f"🚫 Alpha Vantage HTTP API调用失败: {str(e)}")
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
            print(f"🔄 调用 Alpha Vantage HTTP API 获取 {ticker} 的实时报价...")
            
            # 直接使用HTTP API获取实时报价
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
                print(f"⚠️ Alpha Vantage API 返回空报价数据")
                return None
                
        except Exception as e:
            print(f"🚫 Alpha Vantage HTTP API实时报价获取失败: {str(e)}")
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
            print(f"🔄 调用 Alpha Vantage HTTP API 获取 {ticker} 的公司概览...")
            
            # 直接使用HTTP API获取公司概览
            overview_data = self.api.get_company_overview(ticker)
            
            if overview_data:
                metrics = self.api.convert_overview_to_financial_metrics(overview_data, ticker)
                if metrics:
                    print(f"✅ 成功获取 {ticker} 的公司概览")
                    return metrics
                else:
                    print(f"⚠️ 公司概览数据转换失败")
                    return []
            else:
                print(f"⚠️ Alpha Vantage API 返回空公司数据")
                return []
                
        except Exception as e:
            print(f"🚫 Alpha Vantage HTTP API公司数据获取失败: {str(e)}")
            return []

# 全局实例
_alphavantage_wrapper = None


def get_alphavantage_wrapper() -> AlphaVantageHTTPWrapper:
    """获取 Alpha Vantage HTTP 包装器实例"""
    global _alphavantage_wrapper
    if _alphavantage_wrapper is None:
        _alphavantage_wrapper = AlphaVantageHTTPWrapper()
    return _alphavantage_wrapper
