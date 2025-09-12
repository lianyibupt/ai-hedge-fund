#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Finnhub 财务数据API模块
专门用于获取基本面财务指标数据，替代AlphaVantage的财务数据功能
"""

import os
import finnhub
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from data.models import FinancialMetrics
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class FinnhubFinancialAPI:
    """Finnhub 财务数据API客户端"""
    
    def __init__(self):
        """
        初始化 Finnhub 财务API客户端
        """
        self.api_name = "Finnhub Financial API"
        self.api_key = os.getenv('FINNHUB_API_KEY')
        
        if not self.api_key:
            raise ValueError("未找到 Finnhub API 密钥，请在 .env 文件中设置 FINNHUB_API_KEY")
        
        self.client = finnhub.Client(api_key=self.api_key)
        print(f"🔧 Finnhub 财务API 初始化成功")
        
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
            
            # 获取公司基本信息
            profile_data = self.client.company_profile2(symbol=ticker)
            
            if not profile_data:
                raise Exception(f"未找到股票 {ticker} 的公司信息")
            
            print(f"✅ 成功获取 {ticker} 的公司概览")
            return profile_data
            
        except Exception as e:
            print(f"❌ Finnhub 公司信息获取失败: {str(e)}")
            raise Exception(f"Finnhub 公司信息获取失败: {str(e)}")
    
    def get_financial_metrics(self, ticker: str) -> Dict[str, Any]:
        """
        获取财务指标
        
        Args:
            ticker: 股票代码
            
        Returns:
            财务指标数据
        """
        try:
            print(f"📊 正在获取 {ticker} 的财务指标...")
            
            # 获取基础财务指标
            financials_data = self.client.company_basic_financials(ticker, 'all')
            
            if not financials_data or 'metric' not in financials_data:
                raise Exception(f"未找到股票 {ticker} 的财务数据")
            
            print(f"✅ 成功获取 {ticker} 的财务指标")
            return financials_data
            
        except Exception as e:
            print(f"❌ Finnhub 财务指标获取失败: {str(e)}")
            raise Exception(f"Finnhub 财务指标获取失败: {str(e)}")
    
    def get_recommendation_trends(self, ticker: str) -> List[Dict[str, Any]]:
        """
        获取分析师推荐趋势
        
        Args:
            ticker: 股票代码
            
        Returns:
            分析师推荐数据
        """
        try:
            print(f"📈 正在获取 {ticker} 的分析师推荐...")
            
            recommendation_data = self.client.recommendation_trends(ticker)
            
            if not recommendation_data:
                print(f"⚠️ 未找到股票 {ticker} 的分析师推荐数据")
                return []
            
            print(f"✅ 成功获取 {ticker} 的分析师推荐")
            return recommendation_data
            
        except Exception as e:
            print(f"❌ Finnhub 分析师推荐获取失败: {str(e)}")
            return []
    
    def convert_to_financial_metrics(
        self, 
        financials_data: Dict[str, Any], 
        profile_data: Dict[str, Any],
        ticker: str
    ) -> List[FinancialMetrics]:
        """
        将 Finnhub 财务数据转换为 FinancialMetrics 对象
        
        Args:
            financials_data: Finnhub 财务数据
            profile_data: Finnhub 公司信息
            ticker: 股票代码
            
        Returns:
            FinancialMetrics对象列表
        """
        try:
            if not financials_data or 'metric' not in financials_data:
                return []
            
            metrics = financials_data['metric']
            
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
            
            financial_metrics = FinancialMetrics(
                ticker=ticker,
                report_period=report_date,
                period="ttm",  # 默认使用TTM
                currency="USD",  # Finnhub 主要提供美股数据
                
                # 估值指标
                market_cap=safe_float(profile_data.get("marketCapitalization")),
                enterprise_value=None,  # Finnhub 不直接提供
                price_to_earnings_ratio=safe_float(metrics.get("peBasicExclExtraTTM")),
                price_to_book_ratio=safe_float(metrics.get("pbQuarterly")),
                price_to_sales_ratio=safe_float(metrics.get("psTTM")),
                enterprise_value_to_ebitda_ratio=None,  # Finnhub 不直接提供
                enterprise_value_to_revenue_ratio=None,  # Finnhub 不直接提供
                peg_ratio=None,  # Finnhub 不直接提供
                
                # 盈利能力指标
                return_on_equity=safe_float(metrics.get("roeRfy")),
                return_on_assets=safe_float(metrics.get("roaRfy")),
                gross_margin=safe_float(metrics.get("grossMarginTTM")),
                operating_margin=safe_float(metrics.get("operatingMarginTTM")),
                net_margin=safe_float(metrics.get("netMarginTTM")),
                
                # 流动性指标
                current_ratio=safe_float(metrics.get("currentRatioQuarterly")),
                quick_ratio=safe_float(metrics.get("quickRatioQuarterly")),
                
                # 杠杆指标
                debt_to_equity=safe_float(metrics.get("totalDebt/totalEquityQuarterly")),
                
                # 每股指标
                earnings_per_share=safe_float(metrics.get("epsBasicExclExtraItemsTTM")),
                book_value_per_share=safe_float(metrics.get("bookValuePerShareQuarterly")),
                
                # 增长指标 - Finnhub 提供的增长数据
                revenue_growth=safe_float(metrics.get("revenueGrowthTTMYoy")),
                earnings_growth=safe_float(metrics.get("epsGrowthTTMYoy")),
                
                # 股息指标
                payout_ratio=safe_float(metrics.get("payoutRatioAnnual") or metrics.get("dividendYieldIndicatedAnnual")),
                
                # 其他指标暂时设为None（Finnhub不直接提供或需要计算）
            )
            
            return [financial_metrics]
            
        except Exception as e:
            print(f"⚠️ Finnhub 财务数据转换失败: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        Returns:
            连接是否成功
        """
        try:
            print(f"🔄 正在测试 Finnhub API 连接...")
            
            # 使用简单的API调用测试连接
            quote_data = self.client.quote('AAPL')
            
            # 检查是否有有效数据
            if quote_data and 'c' in quote_data:
                print(f"✅ Finnhub API 连接成功")
                return True
            else:
                print(f"⚠️ Finnhub API 返回意外格式: {quote_data}")
                return False
            
        except Exception as e:
            print(f"❌ Finnhub API 连接测试失败: {str(e)}")
            return False


# 全局实例
_finnhub_financial_api = None


def get_finnhub_financial_api() -> FinnhubFinancialAPI:
    """获取 Finnhub 财务API 实例"""
    global _finnhub_financial_api
    if _finnhub_financial_api is None:
        _finnhub_financial_api = FinnhubFinancialAPI()
    return _finnhub_financial_api


# 统一接口函数，替代AlphaVantage财务数据获取
def fetch_financial_metrics_from_finnhub(
    ticker: str, 
    end_date: str, 
    period: str = "ttm", 
    limit: int = 10, 
    region: str = 'us'
) -> List[FinancialMetrics]:
    """
    从 Finnhub API 获取财务指标
    
    Args:
        ticker: 股票代码
        end_date: 结束日期（Finnhub主要提供实时数据，此参数保持兼容性）
        period: 报告期间（保持兼容性）
        limit: 数据限制（保持兼容性）
        region: 市场区域（Finnhub主要支持美股）
    
    Returns:
        FinancialMetrics 对象列表
    """
    try:
        if region != 'us':
            print(f"⚠️ Finnhub 主要支持美股财务数据，{ticker} 市场区域 {region} 可能不支持")
        
        api = get_finnhub_financial_api()
        
        print(f"🔄 从 Finnhub API 获取 {ticker} 财务指标")
        
        # 获取财务数据和公司信息
        financials_data = api.get_financial_metrics(ticker)
        profile_data = api.get_company_overview(ticker)
        
        # 转换为标准格式
        metrics = api.convert_to_financial_metrics(financials_data, profile_data, ticker)
        
        if not metrics:
            print(f"⚠️ Finnhub API 返回空财务数据，股票代码: {ticker}")
            return []
        
        print(f"✅ 成功从 Finnhub API 获取财务指标")
        return metrics[:limit]
        
    except Exception as e:
        print(f"❌ Finnhub API 财务指标获取失败: {str(e)}")
        raise Exception(f"无法从 Finnhub API 获取 {ticker} 的财务指标: {str(e)}")


def test_finnhub_financial_connection() -> bool:
    """
    测试 Finnhub 财务API 连接
    
    Returns:
        连接是否成功
    """
    try:
        api = get_finnhub_financial_api()
        return api.test_connection()
    except Exception as e:
        print(f"❌ Finnhub 财务API 连接测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试 Finnhub 财务API...")
    
    if test_finnhub_financial_connection():
        print("✅ 连接测试成功")
        
        # 测试获取财务指标
        print("\n💰 测试获取 AAPL 财务指标...")
        try:
            metrics = fetch_financial_metrics_from_finnhub("AAPL", "2024-01-10")
            if metrics:
                print(f"✅ 成功获取财务指标")
                metric = metrics[0]
                print(f"P/E 比率: {metric.price_to_earnings_ratio}")
                print(f"市值: {metric.market_cap}")
                print(f"ROE: {metric.return_on_equity}")
        except Exception as e:
            print(f"❌ 获取财务指标失败: {e}")
    else:
        print("❌ 连接测试失败")