"""
Alpha Vantage API 接口模块
提供基于 Alpha Vantage HTTP API 的股票数据获取功能
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from data.models import Price, FinancialMetrics
import json
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class AlphaVantageAPI:
    """Alpha Vantage API 客户端（基于 HTTP API）"""
    
    def __init__(self):
        """
        初始化 Alpha Vantage API 客户端
        """
        self.api_name = "Alpha Vantage HTTP API"
        self.base_url = "https://www.alphavantage.co/query"
        self.api_key = os.getenv('ALPHAVANTAGE_API_KEY')
        
        if not self.api_key:
            raise ValueError("未找到 Alpha Vantage API 密钥，请在 .env 文件中设置 ALPHAVANTAGE_API_KEY")
        
        print(f"🔧 Alpha Vantage API 初始化成功，使用 HTTP API")
        
    def get_real_time_quote(self, ticker: str) -> Dict[str, Any]:
        """
        获取实时报价数据
        
        Args:
            ticker: 股票代码
            
        Returns:
            实时报价数据
        """
        try:
            print(f"📱 正在获取 {ticker} 的实时报价...")
            
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': ticker,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查是否有错误消息
            if 'Error Message' in data:
                raise Exception(f"API 错误: {data['Error Message']}")
            if 'Note' in data:
                raise Exception(f"API 限制: {data['Note']}")
            
            print(f"✅ 成功获取 {ticker} 的实时报价")
            return data
            
        except Exception as e:
            print(f"❌ Alpha Vantage API 实时报价获取失败: {str(e)}")
            raise Exception(f"Alpha Vantage API 实时报价获取失败: {str(e)}")
    
    def get_historical_data(
        self, 
        ticker: str, 
        start_date: str,
        end_date: str,
        interval: str = "daily"
    ) -> Dict[str, Any]:
        """
        获取历史数据
        
        Args:
            ticker: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            interval: 时间间隔 (daily, weekly, monthly)
            
        Returns:
            历史数据
        """
        try:
            print(f"📊 正在获取 {ticker} 的历史数据 ({start_date} 到 {end_date})...")
            
            # 根据间隔类型选择API函数
            if interval == "daily":
                function = "TIME_SERIES_DAILY"
            elif interval == "weekly":
                function = "TIME_SERIES_WEEKLY"
            elif interval == "monthly":
                function = "TIME_SERIES_MONTHLY"
            else:
                function = "TIME_SERIES_DAILY"  # 默认使用日线
            
            params = {
                'function': function,
                'symbol': ticker,
                'outputsize': 'full',  # 获取完整历史数据
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查是否有错误消息
            if 'Error Message' in data:
                raise Exception(f"API 错误: {data['Error Message']}")
            if 'Note' in data:
                raise Exception(f"API 限制: {data['Note']}")
            
            print(f"✅ 成功获取 {ticker} 的历史数据")
            return data
            
        except Exception as e:
            print(f"❌ Alpha Vantage API 历史数据获取失败: {str(e)}")
            raise Exception(f"Alpha Vantage API 历史数据获取失败: {str(e)}")
    
    def get_company_overview(self, ticker: str) -> Dict[str, Any]:
        """
        获取公司基本信息
        
        Args:
            ticker: 股票代码
            
        Returns:
            公司基本信息
        """
        try:
            print(f"🏢 正在获取 {ticker} 的公司概览...")
            
            params = {
                'function': 'OVERVIEW',
                'symbol': ticker,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查是否有错误消息
            if 'Error Message' in data:
                raise Exception(f"API 错误: {data['Error Message']}")
            if 'Note' in data:
                raise Exception(f"API 限制: {data['Note']}")
            
            print(f"✅ 成功获取 {ticker} 的公司概览")
            return data
            
        except Exception as e:
            print(f"❌ Alpha Vantage API 公司信息获取失败: {str(e)}")
            raise Exception(f"Alpha Vantage API 公司信息获取失败: {str(e)}")
    
    def convert_time_series_to_prices(
        self, 
        time_series_data: Dict[str, Any], 
        ticker: str
    ) -> List[Price]:
        """
        将 Alpha Vantage 时间序列数据转换为 Price 对象列表
        
        Args:
            time_series_data: Alpha Vantage 时间序列数据
            ticker: 股票代码
            
        Returns:
            Price对象列表
        """
        try:
            prices = []
            
            # 处理 Alpha Vantage 的时间序列数据格式
            if 'Time Series (Daily)' in time_series_data:
                time_series = time_series_data['Time Series (Daily)']
                
                for date_str, data in time_series.items():
                    price = Price(
                        ticker=ticker,
                        time=date_str,
                        open=float(data.get('1. open', 0)),
                        high=float(data.get('2. high', 0)),
                        low=float(data.get('3. low', 0)),
                        close=float(data.get('4. close', 0)),
                        volume=int(data.get('5. volume', 0))
                    )
                    prices.append(price)
            
            # 按日期倒序排序，确保最新数据在前
            prices.sort(key=lambda x: x.time, reverse=True)
            return prices
            
        except Exception as e:
            print(f"⚠️ Alpha Vantage 数据转换失败: {str(e)}")
            return []
    
    def convert_daily_to_prices(
        self, 
        daily_data: Dict[str, Any], 
        ticker: str
    ) -> List[Price]:
        """
        将 Alpha Vantage 每日价格数据转换为 Price 对象列表
        
        Args:
            daily_data: Alpha Vantage 每日价格数据
            ticker: 股票代码
            
        Returns:
            Price对象列表
        """
        try:
            prices = []
            
            if 'Time Series (Daily)' in daily_data:
                time_series = daily_data['Time Series (Daily)']
                
                for date_str, price_data in time_series.items():
                    price = Price(
                        ticker=ticker,
                        time=date_str,
                        open=float(price_data.get('1. open', 0)),
                        high=float(price_data.get('2. high', 0)),
                        low=float(price_data.get('3. low', 0)),
                        close=float(price_data.get('4. close', 0)),
                        volume=int(price_data.get('5. volume', 0))
                    )
                    prices.append(price)
                
                # 按日期倒序排序，确保最新数据在前
                prices.sort(key=lambda x: x.time, reverse=True)
                
            return prices
            
        except Exception as e:
            print(f"⚠️ Alpha Vantage 每日价格数据转换失败: {str(e)}")
            return []
    
    def convert_quote_to_price(
        self, 
        quote_data: Dict[str, Any], 
        ticker: str
    ) -> Optional[Price]:
        """
        将 Alpha Vantage 报价数据转换为 Price 对象
        
        Args:
            quote_data: Alpha Vantage 报价数据
            ticker: 股票代码
            
        Returns:
            Price对象或None
        """
        try:
            if 'Global Quote' in quote_data:
                quote = quote_data['Global Quote']
                
                price = Price(
                    ticker=ticker,
                    time=quote.get('07. latest trading day', datetime.now().strftime('%Y-%m-%d')),
                    open=float(quote.get('02. open', 0)),
                    high=float(quote.get('03. high', 0)),
                    low=float(quote.get('04. low', 0)),
                    close=float(quote.get('05. price', 0)),
                    volume=int(quote.get('06. volume', 0))
                )
                return price
            
            return None
            
        except Exception as e:
            print(f"⚠️ Alpha Vantage 报价数据转换失败: {str(e)}")
            return None
    
    def convert_overview_to_financial_metrics(
        self, 
        overview_data: Dict[str, Any], 
        ticker: str
    ) -> List[FinancialMetrics]:
        """
        将 Alpha Vantage 公司概览数据转换为 FinancialMetrics 对象
        
        Args:
            overview_data: Alpha Vantage 公司概览数据
            ticker: 股票代码
            
        Returns:
            FinancialMetrics对象列表
        """
        try:
            if not overview_data:
                return []
            
            # 当前日期作为报告期
            report_date = datetime.now().strftime("%Y-%m-%d")
            
            # 处理数值，将 "None" 和无效值转换为 None
            def safe_float(value):
                if value in [None, "None", "-", ""]:
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            metrics = FinancialMetrics(
                ticker=ticker,
                report_period=report_date,
                period="ttm",  # 默认使用TTM
                currency="USD",  # Alpha Vantage 主要提供美股数据
                
                # 估值指标
                market_cap=safe_float(overview_data.get("MarketCapitalization")),
                enterprise_value=None,  # Alpha Vantage 可能不直接提供
                price_to_earnings_ratio=safe_float(overview_data.get("PERatio")),
                price_to_book_ratio=safe_float(overview_data.get("PriceToBookRatio")),
                price_to_sales_ratio=safe_float(overview_data.get("PriceToSalesRatioTTM")),
                enterprise_value_to_ebitda_ratio=safe_float(overview_data.get("EVToEBITDA")),
                enterprise_value_to_revenue_ratio=safe_float(overview_data.get("EVToRevenue")),
                peg_ratio=safe_float(overview_data.get("PEGRatio")),
                
                # 盈利能力指标
                return_on_equity=safe_float(overview_data.get("ReturnOnEquityTTM")),
                return_on_assets=safe_float(overview_data.get("ReturnOnAssetsTTM")),
                gross_margin=safe_float(overview_data.get("GrossProfitTTM")),
                operating_margin=safe_float(overview_data.get("OperatingMarginTTM")),
                net_margin=safe_float(overview_data.get("ProfitMargin")),
                
                # 流动性指标
                current_ratio=safe_float(overview_data.get("CurrentRatio")),
                quick_ratio=safe_float(overview_data.get("QuickRatio")),
                
                # 杠杆指标
                debt_to_equity_ratio=safe_float(overview_data.get("DebtToEquity")),
                
                # 每股指标
                earnings_per_share=safe_float(overview_data.get("EPS")),
                book_value_per_share=safe_float(overview_data.get("BookValue")),
                
                # 增长指标
                revenue_growth=safe_float(overview_data.get("RevenuePerShareTTM")),
                earnings_growth=safe_float(overview_data.get("QuarterlyEarningsGrowthYOY")),
                
                # 股息指标
                dividend_yield=safe_float(overview_data.get("DividendYield")),
                payout_ratio=safe_float(overview_data.get("PayoutRatio")),
                
                # 其他指标暂时设为None
                enterprise_value_to_free_cash_flow_ratio=None,
                price_to_free_cash_flow_ratio=None,
                free_cash_flow_yield=None,
                days_sales_outstanding=None,
                operating_cycle=None,
                working_capital_turnover=None,
                book_value_growth=None,
                earnings_per_share_growth=None,
                free_cash_flow_growth=None,
                operating_income_growth=None,
                ebitda_growth=None,
                free_cash_flow_per_share=None
            )
            
            return [metrics]
            
        except Exception as e:
            print(f"⚠️ Alpha Vantage 财务数据转换失败: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        Returns:
            连接是否成功
        """
        try:
            print(f"🔄 正在测试 Alpha Vantage HTTP API 连接...")
            
            # 使用简单的API调用测试连接
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'AAPL',  # 使用AAPL作为测试
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查是否有有效数据
            if 'Global Quote' in data and data['Global Quote']:
                print(f"✅ Alpha Vantage HTTP API 连接成功")
                return True
            elif 'Error Message' in data:
                print(f"❌ Alpha Vantage API 错误: {data['Error Message']}")
                return False
            elif 'Note' in data:
                print(f"⚠️ Alpha Vantage API 限制: {data['Note']}")
                return False
            else:
                print(f"⚠️ Alpha Vantage API 返回意外格式: {data}")
                return False
            
        except Exception as e:
            print(f"❌ Alpha Vantage HTTP API 连接测试失败: {str(e)}")
            return False


# 全局实例
_alphavantage_api = None


def get_alphavantage_api() -> AlphaVantageAPI:
    """获取 Alpha Vantage API 实例"""
    global _alphavantage_api
    if _alphavantage_api is None:
        _alphavantage_api = AlphaVantageAPI()
    return _alphavantage_api