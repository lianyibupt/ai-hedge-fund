"""
Yahoo Finance RapidAPI 接口模块
提供基于 RapidAPI Yahoo Finance 的股票数据获取功能
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from data.models import Price, FinancialMetrics
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class RapidAPIYahooFinance:
    """Yahoo Finance RapidAPI 客户端"""
    
    def __init__(self):
        """
        初始化 Yahoo Finance RapidAPI 客户端
        """
        self.api_name = "Yahoo Finance RapidAPI"
        self.base_url = "https://yahoo-finance15.p.rapidapi.com/api/v2"
        self.api_key = os.getenv('RAPIDAPI_KEY')
        
        if not self.api_key:
            raise ValueError("未找到 RapidAPI 密钥，请在 .env 文件中设置 RAPIDAPI_KEY")
        
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "yahoo-finance15.p.rapidapi.com"
        }
        
        print(f"🔧 Yahoo Finance RapidAPI 初始化成功")
        
    def get_historical_data(
        self, 
        symbol: str, 
        interval: str = "1d",
        limit: int = 100,
        dividend: bool = False
    ) -> Dict[str, Any]:
        """
        获取历史股票数据
        
        Args:
            symbol: 股票代码
            interval: 时间间隔 (1m, 5m, 15m, 30m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            limit: 数据条数限制 (最大1000)
            dividend: 是否包含股息数据
            
        Returns:
            历史数据响应
        """
        try:
            print(f"📊 正在获取 {symbol} 的历史数据 (间隔: {interval}, 条数: {limit})...")
            
            url = f"{self.base_url}/markets/stock/history"
            
            querystring = {
                "symbol": symbol.upper(),
                "interval": interval,
                "limit": str(min(limit, 1000)),  # 限制最大请求数量
                "dividend": str(dividend).lower()
            }
            
            response = requests.get(url, headers=self.headers, params=querystring, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查响应状态
            if isinstance(data, dict) and data.get('meta', {}).get('status') != 200:
                raise Exception(f"API 错误: 状态码 {data.get('meta', {}).get('status')}")
            
            print(f"✅ 成功获取 {symbol} 的历史数据")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Yahoo Finance RapidAPI 网络请求失败: {str(e)}")
            raise Exception(f"Yahoo Finance RapidAPI 网络请求失败: {str(e)}")
        except Exception as e:
            print(f"❌ Yahoo Finance RapidAPI 历史数据获取失败: {str(e)}")
            raise Exception(f"Yahoo Finance RapidAPI 历史数据获取失败: {str(e)}")
    
    def get_real_time_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取实时报价数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            实时报价数据
        """
        try:
            print(f"📱 正在获取 {symbol} 的实时报价...")
            
            url = f"{self.base_url}/markets/stock/quotes"
            
            querystring = {
                "symbol": symbol.upper()
            }
            
            response = requests.get(url, headers=self.headers, params=querystring, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查响应状态
            if isinstance(data, dict) and data.get('meta', {}).get('status') != 200:
                raise Exception(f"API 错误: 状态码 {data.get('meta', {}).get('status')}")
            
            print(f"✅ 成功获取 {symbol} 的实时报价")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Yahoo Finance RapidAPI 实时报价网络请求失败: {str(e)}")
            raise Exception(f"Yahoo Finance RapidAPI 实时报价网络请求失败: {str(e)}")
        except Exception as e:
            print(f"❌ Yahoo Finance RapidAPI 实时报价获取失败: {str(e)}")
            raise Exception(f"Yahoo Finance RapidAPI 实时报价获取失败: {str(e)}")
    
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """
        获取公司基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            公司基本信息
        """
        try:
            print(f"🏢 正在获取 {symbol} 的公司概览...")
            
            url = f"{self.base_url}/markets/stock/profile"
            
            querystring = {
                "symbol": symbol.upper()
            }
            
            response = requests.get(url, headers=self.headers, params=querystring, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查响应状态
            if isinstance(data, dict) and data.get('meta', {}).get('status') != 200:
                raise Exception(f"API 错误: 状态码 {data.get('meta', {}).get('status')}")
            
            print(f"✅ 成功获取 {symbol} 的公司概览")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Yahoo Finance RapidAPI 公司信息网络请求失败: {str(e)}")
            raise Exception(f"Yahoo Finance RapidAPI 公司信息网络请求失败: {str(e)}")
        except Exception as e:
            print(f"❌ Yahoo Finance RapidAPI 公司信息获取失败: {str(e)}")
            raise Exception(f"Yahoo Finance RapidAPI 公司信息获取失败: {str(e)}")
    
    def convert_history_to_prices(
        self, 
        history_data: Dict[str, Any], 
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Price]:
        """
        将 Yahoo Finance RapidAPI 历史数据转换为 Price 对象列表
        
        Args:
            history_data: Yahoo Finance RapidAPI 历史数据响应
            symbol: 股票代码
            start_date: 开始日期过滤 (YYYY-MM-DD)
            end_date: 结束日期过滤 (YYYY-MM-DD)
            
        Returns:
            Price对象列表
        """
        try:
            prices = []
            
            # 处理 Yahoo Finance RapidAPI 的响应格式
            if 'body' in history_data and isinstance(history_data['body'], list):
                body_data = history_data['body']
                
                for item in body_data:
                    # 数据格式：
                    # {
                    #   "timestamp": "2025-08-28",
                    #   "timestamp_unix": 1756353600,
                    #   "open": 100.64,
                    #   "high": 105.5,
                    #   "low": 99.9,
                    #   "close": 102.79,
                    #   "volume": 45313100
                    # }
                    
                    timestamp = item.get('timestamp')  # 日期字符串
                    open_price = item.get('open')
                    high_price = item.get('high')
                    low_price = item.get('low')
                    close_price = item.get('close')
                    volume = item.get('volume', 0)
                    
                    # 验证必要字段
                    if not timestamp or open_price is None or close_price is None:
                        continue
                    
                    # 日期过滤
                    if start_date and timestamp < start_date:
                        continue
                    if end_date and timestamp > end_date:
                        continue
                    
                    price = Price(
                        ticker=symbol,
                        time=timestamp,
                        open=float(open_price),
                        high=float(high_price or close_price),
                        low=float(low_price or close_price),
                        close=float(close_price),
                        volume=int(volume)
                    )
                    prices.append(price)
            
            # 按日期倒序排序，确保最新数据在前
            prices.sort(key=lambda x: x.time, reverse=True)
            return prices
            
        except Exception as e:
            print(f"⚠️ Yahoo Finance RapidAPI 数据转换失败: {str(e)}")
            return []
    
    def convert_quote_to_price(
        self, 
        quote_data: Dict[str, Any], 
        symbol: str
    ) -> Optional[Price]:
        """
        将 Yahoo Finance RapidAPI 报价数据转换为 Price 对象
        
        Args:
            quote_data: Yahoo Finance RapidAPI 报价数据
            symbol: 股票代码
            
        Returns:
            Price对象或None
        """
        try:
            if 'body' in quote_data and isinstance(quote_data['body'], list) and quote_data['body']:
                quote = quote_data['body'][0]  # 取第一个报价
                
                current_price = quote.get('regularMarketPrice', quote.get('price'))
                open_price = quote.get('regularMarketOpen', current_price)
                high_price = quote.get('regularMarketDayHigh', current_price)
                low_price = quote.get('regularMarketDayLow', current_price)
                volume = quote.get('regularMarketVolume', 0)
                
                if current_price is not None:
                    price = Price(
                        ticker=symbol,
                        time=datetime.now().strftime('%Y-%m-%d'),
                        open=float(open_price or current_price),
                        high=float(high_price or current_price),
                        low=float(low_price or current_price),
                        close=float(current_price),
                        volume=int(volume)
                    )
                    return price
            
            return None
            
        except Exception as e:
            print(f"⚠️ Yahoo Finance RapidAPI 报价数据转换失败: {str(e)}")
            return None
    
    def convert_profile_to_financial_metrics(
        self, 
        profile_data: Dict[str, Any], 
        symbol: str
    ) -> List[FinancialMetrics]:
        """
        将 Yahoo Finance RapidAPI 公司概览数据转换为 FinancialMetrics 对象
        
        Args:
            profile_data: Yahoo Finance RapidAPI 公司概览数据
            symbol: 股票代码
            
        Returns:
            FinancialMetrics对象列表
        """
        try:
            if 'body' not in profile_data or not profile_data['body']:
                return []
            
            body = profile_data['body']
            
            # 当前日期作为报告期
            report_date = datetime.now().strftime("%Y-%m-%d")
            
            # 处理数值，将 None 和无效值转换为 None
            def safe_float(value):
                if value in [None, "None", "-", "", "N/A"]:
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            metrics = FinancialMetrics(
                ticker=symbol,
                report_period=report_date,
                period="ttm",  # 默认使用TTM
                currency=body.get("currency", "USD"),
                
                # 估值指标
                market_cap=safe_float(body.get("marketCap")),
                enterprise_value=safe_float(body.get("enterpriseValue")),
                price_to_earnings_ratio=safe_float(body.get("trailingPE")),
                price_to_book_ratio=safe_float(body.get("priceToBook")),
                price_to_sales_ratio=safe_float(body.get("priceToSalesTrailing12Months")),
                enterprise_value_to_ebitda_ratio=safe_float(body.get("enterpriseToEbitda")),
                enterprise_value_to_revenue_ratio=safe_float(body.get("enterpriseToRevenue")),
                peg_ratio=safe_float(body.get("pegRatio")),
                
                # 盈利能力指标
                return_on_equity=safe_float(body.get("returnOnEquity")),
                return_on_assets=safe_float(body.get("returnOnAssets")),
                gross_margin=safe_float(body.get("grossMargins")),
                operating_margin=safe_float(body.get("operatingMargins")),
                net_margin=safe_float(body.get("profitMargins")),
                
                # 流动性指标
                current_ratio=safe_float(body.get("currentRatio")),
                quick_ratio=safe_float(body.get("quickRatio")),
                
                # 杠杆指标
                debt_to_equity_ratio=safe_float(body.get("debtToEquity")),
                
                # 每股指标
                earnings_per_share=safe_float(body.get("trailingEps")),
                book_value_per_share=safe_float(body.get("bookValue")),
                
                # 增长指标
                revenue_growth=safe_float(body.get("revenueGrowth")),
                earnings_growth=safe_float(body.get("earningsGrowth")),
                
                # 股息指标
                dividend_yield=safe_float(body.get("dividendYield")),
                payout_ratio=safe_float(body.get("payoutRatio")),
                
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
            print(f"⚠️ Yahoo Finance RapidAPI 财务数据转换失败: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        Returns:
            连接是否成功
        """
        try:
            print(f"🔄 正在测试 Yahoo Finance RapidAPI 连接...")
            
            # 使用简单的API调用测试连接
            response = self.get_historical_data("AAPL", interval="1d", limit=1)
            
            # 检查是否有有效数据
            if response and 'body' in response and response['body']:
                print(f"✅ Yahoo Finance RapidAPI 连接成功")
                return True
            else:
                print(f"❌ Yahoo Finance RapidAPI 返回空数据")
                return False
            
        except Exception as e:
            print(f"❌ Yahoo Finance RapidAPI 连接测试失败: {str(e)}")
            return False


# 全局实例
_rapidapi_yahoo_finance = None


def get_rapidapi_yahoo_finance() -> RapidAPIYahooFinance:
    """获取 Yahoo Finance RapidAPI 实例"""
    global _rapidapi_yahoo_finance
    if _rapidapi_yahoo_finance is None:
        _rapidapi_yahoo_finance = RapidAPIYahooFinance()
    return _rapidapi_yahoo_finance


# 便捷函数
def fetch_prices_from_rapidapi_yahoo(
    symbol: str, 
    start_date: str, 
    end_date: str, 
    interval: str = "1d"
) -> List[Price]:
    """
    从 Yahoo Finance RapidAPI 获取价格数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        interval: 时间间隔
    
    Returns:
        Price 对象列表
    """
    try:
        api = get_rapidapi_yahoo_finance()
        
        # 计算需要的数据条数（粗略估算）
        from datetime import datetime
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        days_diff = (end_dt - start_dt).days
        
        # 根据间隔调整限制
        if interval == "1d":
            limit = min(days_diff + 10, 1000)  # 增加一些缓冲
        elif interval in ["1h", "30m", "15m", "5m", "1m"]:
            limit = 1000  # 小时级或分钟级数据使用最大限制
        else:
            limit = 100  # 其他情况默认100
        
        print(f"🔄 从 Yahoo Finance RapidAPI 获取 {symbol} 价格数据 ({start_date} 到 {end_date}, 间隔: {interval})")
        
        # 获取历史数据
        history_data = api.get_historical_data(symbol, interval=interval, limit=limit)
        
        if not history_data:
            print(f"⚠️ Yahoo Finance RapidAPI 返回空数据，股票代码: {symbol}")
            return []
        
        # 转换为 Price 对象
        prices = api.convert_history_to_prices(history_data, symbol, start_date, end_date)
        
        if not prices:
            print(f"⚠️ Yahoo Finance RapidAPI 数据转换失败，股票代码: {symbol}")
            return []
        
        print(f"✅ 成功从 Yahoo Finance RapidAPI 获取 {len(prices)} 条价格数据")
        return prices
        
    except Exception as e:
        print(f"❌ Yahoo Finance RapidAPI 价格数据获取失败: {str(e)}")
        raise Exception(f"无法从 Yahoo Finance RapidAPI 获取 {symbol} 的价格数据: {str(e)}")


def fetch_financial_metrics_from_rapidapi_yahoo(
    symbol: str, 
    end_date: str, 
    period: str = "ttm", 
    limit: int = 10
) -> List[FinancialMetrics]:
    """
    从 Yahoo Finance RapidAPI 获取财务指标
    
    Args:
        symbol: 股票代码
        end_date: 结束日期
        period: 报告期间
        limit: 数据限制
    
    Returns:
        FinancialMetrics 对象列表
    """
    try:
        api = get_rapidapi_yahoo_finance()
        
        print(f"🔄 从 Yahoo Finance RapidAPI 获取 {symbol} 财务指标")
        
        # 获取公司概览数据
        profile_data = api.get_company_profile(symbol)
        
        if not profile_data:
            print(f"⚠️ Yahoo Finance RapidAPI 返回空财务数据，股票代码: {symbol}")
            return []
        
        # 转换为 FinancialMetrics 对象
        metrics = api.convert_profile_to_financial_metrics(profile_data, symbol)
        
        if not metrics:
            print(f"⚠️ Yahoo Finance RapidAPI 财务数据转换失败，股票代码: {symbol}")
            return []
        
        print(f"✅ 成功从 Yahoo Finance RapidAPI 获取财务指标")
        return metrics[:limit]
        
    except Exception as e:
        print(f"❌ Yahoo Finance RapidAPI 财务指标获取失败: {str(e)}")
        raise Exception(f"无法从 Yahoo Finance RapidAPI 获取 {symbol} 的财务指标: {str(e)}")


def test_rapidapi_yahoo_connection() -> bool:
    """
    测试 Yahoo Finance RapidAPI 连接
    
    Returns:
        连接是否成功
    """
    try:
        api = get_rapidapi_yahoo_finance()
        return api.test_connection()
    except Exception as e:
        print(f"❌ Yahoo Finance RapidAPI 连接测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试 Yahoo Finance RapidAPI...")
    
    try:
        # 测试连接
        if test_rapidapi_yahoo_connection():
            print("✅ 连接测试成功")
            
            # 测试获取历史数据
            print("\n📊 测试获取 AAPL 历史数据...")
            prices = fetch_prices_from_rapidapi_yahoo("AAPL", "2024-01-01", "2024-01-10")
            if prices:
                print(f"✅ 成功获取 {len(prices)} 条价格数据")
                print(f"最新价格: ${prices[0].close}")
            
            # 测试获取财务指标
            print("\n💰 测试获取 AAPL 财务指标...")
            metrics = fetch_financial_metrics_from_rapidapi_yahoo("AAPL", "2024-01-10")
            if metrics:
                print(f"✅ 成功获取财务指标")
                print(f"P/E 比率: {metrics[0].price_to_earnings_ratio}")
        else:
            print("❌ 连接测试失败")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")