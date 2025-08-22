"""
带有回退机制的API模块
当Futu API不可用时，使用模拟数据进行演示
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List
from data.models import Price, FinancialMetrics

# 模拟数据生成器
class MockDataGenerator:
    def __init__(self):
        self.base_prices = {
            "AAPL": 150.0,
            "MSFT": 300.0,
            "NVDA": 400.0,
            "GOOGL": 120.0,
            "TSLA": 200.0
        }
    
    def generate_mock_prices(self, ticker: str, start_date: str, end_date: str) -> List[Price]:
        """生成模拟价格数据"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # 确保至少有120天的数据用于技术分析
        if (end_dt - start_dt).days < 120:
            start_dt = end_dt - timedelta(days=120)
        
        base_price = self.base_prices.get(ticker, 100.0)
        
        prices = []
        current_dt = start_dt
        current_price = base_price
        
        np.random.seed(hash(ticker) % 2**32)  # 确保可重复
        
        while current_dt <= end_dt:
            # 模拟价格波动
            daily_return = np.random.normal(0.001, 0.02)  # 平均0.1%日收益，2%波动
            current_price *= (1 + daily_return)
            
            # 生成OHLC数据
            high = current_price * (1 + abs(np.random.normal(0, 0.01)))
            low = current_price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = current_price * (1 + np.random.normal(0, 0.005))
            volume = int(np.random.normal(50000000, 10000000))  # 平均5000万股交易量
            
            prices.append(Price(
                open=round(open_price, 2),
                close=round(current_price, 2),
                high=round(high, 2),
                low=round(low, 2),
                volume=max(volume, 1000000),  # 最少100万股
                time=current_dt.strftime("%Y-%m-%d")
            ))
            
            current_dt += timedelta(days=1)
        
        return prices
    
    def generate_mock_financial_metrics(self, ticker: str, end_date: str) -> List[FinancialMetrics]:
        """生成模拟财务指标数据"""
        np.random.seed(hash(ticker) % 2**32)
        
        # 基础财务数据
        base_metrics = {
            "AAPL": {
                "market_cap": 2800000000000,  # 2.8万亿
                "pe_ratio": 25.0,
                "pb_ratio": 8.0,
                "ps_ratio": 7.0,
                "roe": 0.26,
                "net_margin": 0.25,
                "operating_margin": 0.30,
                "current_ratio": 1.0,
                "debt_to_equity": 0.8,
            },
            "MSFT": {
                "market_cap": 2300000000000,  # 2.3万亿
                "pe_ratio": 28.0,
                "pb_ratio": 9.0,
                "ps_ratio": 10.0,
                "roe": 0.30,
                "net_margin": 0.27,
                "operating_margin": 0.32,
                "current_ratio": 1.2,
                "debt_to_equity": 0.5,
            }
        }
        
        default_metrics = {
            "market_cap": 1000000000000,  # 1万亿
            "pe_ratio": 22.0,
            "pb_ratio": 3.5,
            "ps_ratio": 5.0,
            "roe": 0.15,
            "net_margin": 0.12,
            "operating_margin": 0.18,
            "current_ratio": 1.5,
            "debt_to_equity": 0.6,
        }
        
        metrics_data = base_metrics.get(ticker, default_metrics)
        
        # 添加一些随机波动
        for key in metrics_data:
            if isinstance(metrics_data[key], (int, float)):
                noise = np.random.normal(0, 0.05)  # 5%噪声
                metrics_data[key] *= (1 + noise)
        
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        report_date = (end_dt - timedelta(days=90)).strftime("%Y-%m-%d")
        
        return [FinancialMetrics(
            ticker=ticker,
            report_period=report_date,
            period="ttm",
            currency="USD",
            market_cap=metrics_data["market_cap"],
            enterprise_value=metrics_data["market_cap"] * 1.1,
            price_to_earnings_ratio=metrics_data["pe_ratio"],
            price_to_book_ratio=metrics_data["pb_ratio"],
            price_to_sales_ratio=metrics_data["ps_ratio"],
            enterprise_value_to_ebitda_ratio=12.0,
            enterprise_value_to_revenue_ratio=6.0,
            free_cash_flow_yield=0.04,
            peg_ratio=1.5,
            gross_margin=0.40,
            operating_margin=metrics_data["operating_margin"],
            net_margin=metrics_data["net_margin"],
            return_on_equity=metrics_data["roe"],
            return_on_assets=0.12,
            return_on_invested_capital=0.18,
            asset_turnover=0.8,
            inventory_turnover=10.0,
            receivables_turnover=15.0,
            days_sales_outstanding=24.0,
            operating_cycle=60.0,
            working_capital_turnover=5.0,
            current_ratio=metrics_data["current_ratio"],
            quick_ratio=1.0,
            cash_ratio=0.3,
            operating_cash_flow_ratio=0.8,
            debt_to_equity=metrics_data["debt_to_equity"],
            debt_to_assets=0.3,
            interest_coverage=8.0,
            revenue_growth=0.10,
            earnings_growth=0.12,
            book_value_growth=0.08,
            earnings_per_share_growth=0.12,
            free_cash_flow_growth=0.15,
            operating_income_growth=0.11,
            ebitda_growth=0.09,
            payout_ratio=0.25,
            earnings_per_share=6.50,
            book_value_per_share=4.20,
            free_cash_flow_per_share=7.80
        )]


# 全局模拟数据生成器
_mock_generator = MockDataGenerator()


def get_prices_with_fallback(ticker: str, start_date: str, end_date: str) -> List[Price]:
    """
    获取价格数据，带有回退机制
    """
    try:
        # 首先尝试使用原始API
        from tools.api import get_prices as original_get_prices
        return original_get_prices(ticker, start_date, end_date)
    except Exception as e:
        print(f"⚠️ Futu API不可用，使用模拟数据: {str(e)}")
        return _mock_generator.generate_mock_prices(ticker, start_date, end_date)


def get_financial_metrics_with_fallback(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> List[FinancialMetrics]:
    """
    获取财务指标，带有回退机制
    """
    try:
        # 首先尝试使用原始API
        from tools.api import get_financial_metrics as original_get_financial_metrics
        return original_get_financial_metrics(ticker, end_date, period, limit)
    except Exception as e:
        print(f"⚠️ Futu API不可用，使用模拟数据: {str(e)}")
        return _mock_generator.generate_mock_financial_metrics(ticker, end_date)


def prices_to_df(prices: List[Price]) -> pd.DataFrame:
    """将价格数据转换为DataFrame"""
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