"""
iTick API 接口模块
提供基于 iTick API 的股票数据获取功能
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from data.models import Price, FinancialMetrics


class iTickAPI:
    """iTick API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 iTick API 客户端
        
        Args:
            api_key: iTick API 密钥，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv("ITICK_API_KEY", "YOUR_FREE_KEY")
        self.base_url = "https://api.itick.org"
        self.headers = {
            "accept": "application/json",
            "token": self.api_key
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[Any, Any]:
        """
        发起 API 请求
        
        Args:
            endpoint: API 端点
            params: 请求参数
            
        Returns:
            API 响应数据
            
        Raises:
            Exception: 请求失败时抛出异常
        """
        url = f"{self.base_url}/{endpoint}"
        
        # 验证API密钥
        if not self.api_key or self.api_key == "YOUR_FREE_KEY":
            raise Exception("iTick API 密钥未配置或无效。请设置环境变量 ITICK_API_KEY")
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查API响应状态
            if isinstance(data, dict):
                if data.get("code") != 0:
                    error_msg = data.get("msg", "Unknown error")
                    raise Exception(f"iTick API 返回错误: {error_msg} (错误代码: {data.get('code')})")
                
                # 检查数据是否为空
                if "data" in data and not data["data"]:
                    raise Exception("iTick API 返回空数据")
                    
            return data
            
        except requests.exceptions.Timeout:
            raise Exception("iTick API 请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            raise Exception("无法连接到 iTick API 服务器，请检查网络连接")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("iTick API 认证失败，请检查API密钥是否正确")
            elif e.response.status_code == 429:
                raise Exception("iTick API 请求频率过高，请稍后重试")
            elif e.response.status_code == 500:
                raise Exception("iTick API 服务器内部错误")
            else:
                raise Exception(f"iTick API HTTP 错误: {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"iTick API 请求失败: {str(e)}")
        except ValueError as e:
            raise Exception(f"iTick API 响应格式错误，无法解析JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"iTick API 调用异常: {str(e)}")
    
    def get_real_time_price(self, ticker: str, region: str = "us") -> Dict[str, Any]:
        """
        获取实时价格数据
        
        Args:
            ticker: 股票代码
            region: 市场区域 (us, hk, cn)
            
        Returns:
            实时价格数据
        """
        params = {
            "region": region,
            "code": ticker
        }
        
        return self._make_request("stock/tick", params)
    
    def get_historical_kline(
        self, 
        ticker: str, 
        period: str = "1d",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        region: str = "us",
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        获取历史K线数据
        
        Args:
            ticker: 股票代码
            period: 时间周期 (1m, 5m, 15m, 30m, 1h, 1d, 1w, 1M)
            start_time: 开始时间 (Unix时间戳)
            end_time: 结束时间 (Unix时间戳)
            region: 市场区域
            limit: 数据条数限制
            
        Returns:
            历史K线数据列表
            
        Raises:
            Exception: API调用失败或数据为空时抛出异常
        """
        # 验证股票代码
        if not ticker or not ticker.strip():
            raise Exception("股票代码不能为空")
            
        # 期间到kType的映射（根据文档完整映射）
        period_to_ktype = {
            "1m": "1",    # 1分钟
            "5m": "2",    # 5分钟
            "15m": "3",   # 15分钟
            "30m": "4",   # 30分钟
            "1h": "5",    # 1小时
            "2h": "6",    # 2小时
            "4h": "7",    # 4小时
            "1d": "8",    # 1天
            "1w": "9",    # 1周
            "1M": "10"    # 1月
        }
        
        if period not in period_to_ktype:
            raise Exception(f"不支持的时间周期: {period}。支持的周期: {list(period_to_ktype.keys())}")
        
        params = {
            "region": region,
            "code": ticker.strip().upper(),
            "kType": period_to_ktype[period],  # 添加必需的kType参数
            "limit": min(limit, 5000)  # 限制最大请求数量
        }
        
        if start_time:
            try:
                # 验证时间戳格式
                int(start_time)
                params["start_time"] = start_time
            except ValueError:
                raise Exception(f"无效的开始时间戳: {start_time}")
                
        if end_time:
            try:
                # 验证时间戳格式
                int(end_time)
                params["end_time"] = end_time
            except ValueError:
                raise Exception(f"无效的结束时间戳: {end_time}")
            
        response = self._make_request("stock/kline", params)
        
        # 返回数据列表，通常在 'data' 字段中
        if isinstance(response, dict):
            data = response.get("data", [])
            if not data:
                raise Exception(f"获取 {ticker} 的K线数据为空，请检查股票代码或时间参数")
            return data
        return []
    
    def get_company_info(self, ticker: str, region: str = "us") -> Dict[str, Any]:
        """
        获取公司基本信息
        
        Args:
            ticker: 股票代码
            region: 市场区域
            
        Returns:
            公司基本信息
        """
        params = {
            "region": region,
            "code": ticker
        }
        
        return self._make_request("stock/company", params)
    
    def get_financial_data(self, ticker: str, region: str = "us") -> Dict[str, Any]:
        """
        获取财务数据
        
        Args:
            ticker: 股票代码
            region: 市场区域
            
        Returns:
            财务数据
        """
        params = {
            "region": region,
            "code": ticker
        }
        
        return self._make_request("stock/financial", params)
    
    def convert_to_price_objects(
        self, 
        kline_data: List[Dict[str, Any]], 
        ticker: str
    ) -> List[Price]:
        """
        将K线数据转换为Price对象列表
        
        Args:
            kline_data: K线数据列表
            ticker: 股票代码
            
        Returns:
            Price对象列表
            
        Raises:
            Exception: 数据转换失败时抛出异常
        """
        if not kline_data:
            raise Exception(f"无法转换空的K线数据为 Price 对象，股票代码: {ticker}")
            
        if not isinstance(kline_data, list):
            raise Exception(f"K线数据必须是列表类型，当前类型: {type(kline_data)}")
        
        prices = []
        invalid_count = 0
        
        for i, item in enumerate(kline_data):
            try:
                # iTick API 返回格式：
                # {
                #   "t": timestamp,     // 时间戳
                #   "o": open_price,    // 该K线开盘价
                #   "h": high_price,    // 该K线最高价  
                #   "l": low_price,     // 该K线最低价
                #   "c": close_price,   // 该K线收盘价
                #   "v": volume,        // 成交数量
                #   "tu": turnover      // 成交金额
                # }
                if not isinstance(item, dict):
                    print(f"⚠️ 跳过非字典格式的数据: {item}")
                    invalid_count += 1
                    continue
                    
                timestamp = item.get("t")  # 时间戳
                open_price = item.get("o")  # 开盘价
                high = item.get("h")        # 最高价
                low = item.get("l")         # 最低价
                close = item.get("c")       # 收盘价
                volume = item.get("v", 0)   # 成交数量
                
                # 验证必要字段
                if timestamp is None:
                    print(f"⚠️ 跳过缺少时间戳的K线数据项: {item}")
                    invalid_count += 1
                    continue
                    
                if open_price is None or close is None:
                    print(f"⚠️ 跳过缺少价格数据的K线数据项: {item}")
                    invalid_count += 1
                    continue
                    
                # 转换和验证数据类型
                try:
                    timestamp = int(timestamp)
                    open_price = float(open_price)
                    close = float(close)
                    high = float(high or close)
                    low = float(low or close)
                    volume = int(volume) if volume is not None else 0
                    
                    # 验证价格的合理性
                    if open_price <= 0 or close <= 0 or high <= 0 or low <= 0:
                        print(f"⚠️ 跳过价格为非正数的K线数据项: {item}")
                        invalid_count += 1
                        continue
                        
                    if high < max(open_price, close) or low > min(open_price, close):
                        print(f"⚠️ 跳过价格逻辑不合理的K线数据项: {item}")
                        invalid_count += 1
                        continue
                        
                    # 将毫秒级时间戳转换为日期字符串
                    try:
                        if timestamp > 1e10:  # 毫秒级时间戳
                            date_str = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d")
                        else:  # 秒级时间戳
                            date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
                    except (ValueError, OSError) as e:
                        print(f"⚠️ 跳过无效时间戳的K线数据项: {item}, 错误: {str(e)}")
                        invalid_count += 1
                        continue
                    
                    prices.append(Price(
                        open=open_price,
                        close=close,
                        high=high,
                        low=low, 
                        volume=volume,
                        time=date_str
                    ))
                    
                except (ValueError, TypeError) as e:
                    print(f"⚠️ 跳过无效的数据类型转换: {item}, 错误: {str(e)}")
                    invalid_count += 1
                    continue
                
            except Exception as e:
                print(f"⚠️ 跳过无效的K线数据项 {i}: {item}, 错误: {str(e)}")
                invalid_count += 1
                continue
        
        # 检查转换结果
        if not prices:
            raise Exception(f"无法从 {len(kline_data)} 条K线数据中转换出任何有效的 Price 对象，股票代码: {ticker}")
            
        if invalid_count > 0:
            print(f"⚠️ 共跳过 {invalid_count} 条无效的K线数据项，成功转换 {len(prices)} 条数据")
            
        return prices
    
    def convert_to_financial_metrics(
        self, 
        financial_data: Dict[str, Any], 
        ticker: str
    ) -> List[FinancialMetrics]:
        """
        将财务数据转换为FinancialMetrics对象
        
        Args:
            financial_data: 财务数据
            ticker: 股票代码
            
        Returns:
            FinancialMetrics对象列表
        """
        try:
            # iTick财务数据格式适配
            data = financial_data.get("data", {})
            
            # 获取基本信息
            basic_info = data.get("basic", {})
            valuation = data.get("valuation", {})
            profitability = data.get("profitability", {})
            liquidity = data.get("liquidity", {})
            leverage = data.get("leverage", {})
            efficiency = data.get("efficiency", {})
            
            # 当前日期作为报告期
            report_date = datetime.now().strftime("%Y-%m-%d")
            
            metrics = FinancialMetrics(
                ticker=ticker,
                report_period=report_date,
                period="ttm",  # 默认使用TTM
                currency=basic_info.get("currency", "USD"),
                
                # 估值指标
                market_cap=valuation.get("market_cap"),
                enterprise_value=valuation.get("enterprise_value"),
                price_to_earnings_ratio=valuation.get("pe_ratio"),
                price_to_book_ratio=valuation.get("pb_ratio"),
                price_to_sales_ratio=valuation.get("ps_ratio"),
                enterprise_value_to_ebitda_ratio=valuation.get("ev_ebitda"),
                enterprise_value_to_revenue_ratio=valuation.get("ev_revenue"),
                peg_ratio=valuation.get("peg_ratio"),
                
                # 盈利能力指标
                gross_margin=profitability.get("gross_margin"),
                operating_margin=profitability.get("operating_margin"),
                net_margin=profitability.get("net_margin"),
                return_on_equity=profitability.get("roe"),
                return_on_assets=profitability.get("roa"),
                return_on_invested_capital=profitability.get("roic"),
                
                # 流动性指标
                current_ratio=liquidity.get("current_ratio"),
                quick_ratio=liquidity.get("quick_ratio"),
                cash_ratio=liquidity.get("cash_ratio"),
                operating_cash_flow_ratio=liquidity.get("ocf_ratio"),
                
                # 杠杆指标
                debt_to_equity=leverage.get("debt_to_equity"),
                debt_to_assets=leverage.get("debt_to_assets"),
                interest_coverage=leverage.get("interest_coverage"),
                
                # 效率指标
                asset_turnover=efficiency.get("asset_turnover"),
                inventory_turnover=efficiency.get("inventory_turnover"),
                receivables_turnover=efficiency.get("receivables_turnover"),
                
                # 其他指标设为None，待后续补充
                free_cash_flow_yield=None,
                days_sales_outstanding=None,
                operating_cycle=None,
                working_capital_turnover=None,
                revenue_growth=None,
                earnings_growth=None,
                book_value_growth=None,
                earnings_per_share_growth=None,
                free_cash_flow_growth=None,
                operating_income_growth=None,
                ebitda_growth=None,
                payout_ratio=None,
                earnings_per_share=basic_info.get("eps"),
                book_value_per_share=basic_info.get("book_value_per_share"),
                free_cash_flow_per_share=None
            )
            
            return [metrics]
            
        except Exception as e:
            print(f"⚠️ 转换财务数据失败: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            连接是否成功
            
        Raises:
            Exception: API连接测试失败时抛出异常
        """
        try:
            print("🔄 正在测试 iTick API 连接...")
            # 使用AAPL测试连接
            response = self.get_real_time_price("AAPL")
            
            # 验证响应数据
            if not response or not isinstance(response, dict):
                raise Exception("API返回无效响应")
                
            print("✅ iTick API 连接测试成功")
            return True
            
        except Exception as e:
            error_msg = f"iTick API 连接测试失败: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)


def date_to_timestamp(date_str: str) -> int:
    """
    将日期字符串转换为Unix时间戳
    
    Args:
        date_str: YYYY-MM-DD 格式的日期字符串
        
    Returns:
        Unix时间戳
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp())
    except ValueError:
        # 如果解析失败，返回当前时间戳
        return int(datetime.now().timestamp())


# 全局iTick API实例
_itick_api = None


def get_itick_api() -> iTickAPI:
    """获取全局iTick API实例"""
    global _itick_api
    if _itick_api is None:
        _itick_api = iTickAPI()
    return _itick_api