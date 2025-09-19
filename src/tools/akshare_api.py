"""
基于AKShare的API模块
使用AKShare库获取A股、港股、美股的股票数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
import sys
import os
import time
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.models import Price, FinancialMetrics
from data.cache import get_cache

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局缓存实例
_cache = get_cache()

# 重试装饰器配置
def retry_with_backoff(max_retries=3, initial_delay=1, backoff_factor=2):
    """自定义重试装饰器，支持指数退避"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"函数 {func.__name__} 重试{max_retries}次后失败: {str(e)}")
                        raise
                    
                    delay = initial_delay * (backoff_factor ** (retries - 1))
                    logger.warning(f"函数 {func.__name__} 第{retries}次重试，等待{delay}秒后重试...")
                    time.sleep(delay)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 判断是否为速率限制错误
def _is_rate_limit_error(exception: Exception) -> bool:
    """判断异常是否为API速率限制错误"""
    error_msg = str(exception).lower()
    error_type = type(exception).__name__
    
    rate_limit_indicators = [
        'rate limit',
        'too many requests',
        '429',
        'exceeded',
        'quota',
        'limit exceeded'
    ]
    
    # 检查错误消息中是否包含速率限制关键词
    return any(indicator in error_msg for indicator in rate_limit_indicators)

RETRY_ATTEMPTS = 3
RETRY_WAIT_MIN = 2
RETRY_WAIT_MAX = 10


def _convert_to_akshare_symbol(ticker: str, market: str = None) -> str:
    """
    将标准股票代码转换为AKShare格式
    
    Args:
        ticker: 股票代码
        market: 市场类型 ('a', 'hk', 'us')
    
    Returns:
        AKShare格式的股票代码
    """
    ticker = ticker.upper().strip()
    
    # 如果已经包含市场前缀，直接返回
    if ticker.startswith(('sh', 'sz', 'hk', 'us')):
        return ticker
    
    # 根据市场类型添加前缀
    if market == 'a':
        # A股: 6开头是sh, 0/3开头是sz
        if ticker.startswith('6'):
            return f"sh{ticker}"
        elif ticker.startswith(('0', '3')):
            return f"sz{ticker}"
        else:
            # 默认尝试sh
            return f"sh{ticker}"
    elif market == 'hk':
        return f"hk{ticker}"
    elif market == 'us':
        return f"us{ticker}"
    else:
        # 自动检测市场
        if len(ticker) == 5 and ticker.isalpha():  # 美股代码通常是字母
            return f"us{ticker}"
        elif ticker.startswith('0') or ticker.startswith('3'):  # 深交所
            return f"sz{ticker}"
        elif ticker.startswith('6'):  # 上交所
            return f"sh{ticker}"
        elif len(ticker) == 5 and ticker.isdigit():  # 港股
            return f"hk{ticker}"
        else:
            # 默认尝试A股
            return f"sh{ticker}"


def _detect_market(ticker: str) -> str:
    """
    检测股票代码所属市场
    
    Returns:
        'a', 'hk', or 'us'
    """
    ticker = ticker.upper().strip()
    
    if ticker.startswith(('sh', 'sz')):
        return 'a'
    elif ticker.startswith('hk'):
        return 'hk'
    elif ticker.startswith('us'):
        return 'us'
    else:
        if len(ticker) == 5 and ticker.isalpha():
            return 'us'
        elif ticker.startswith(('0', '3', '6')):
            return 'a'
        elif len(ticker) == 5 and ticker.isdigit():
            return 'hk'
        else:
            return 'a'  # 默认A股


@retry(
    stop=stop_after_attempt(RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
    retry=retry_if_exception(_is_rate_limit_error)
)
def get_prices_akshare(ticker: str, start_date: str, end_date: str) -> List[Price]:
    """
    从AKShare获取价格数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
    
    Returns:
        Price对象列表
    """
    # 检查缓存
    if cached_data := _cache.get_prices(ticker, start_date, end_date):
        filtered_data = [Price(**price) for price in cached_data]
        if filtered_data:
            logger.info(f"从缓存获取{ticker}的{len(filtered_data)}条价格数据")
            return filtered_data

    try:
        market = _detect_market(ticker)
        akshare_symbol = _convert_to_akshare_symbol(ticker, market)
        
        df = None
        if market == 'a':
            # A股历史数据
            df = ak.stock_zh_a_hist(symbol=akshare_symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        elif market == 'hk':
            # 港股历史数据
            df = ak.stock_hk_daily(symbol=akshare_symbol[2:], start_date=start_date, end_date=end_date, adjust="")
        elif market == 'us':
            # 美股历史数据
            df = ak.stock_us_daily(symbol=akshare_symbol[2:], start_date=start_date, end_date=end_date, adjust="")
        
        if df is None or df.empty:
            logger.warning(f"未获取到{ticker}的价格数据")
            return []
        
        prices = []
        for _, row in df.iterrows():
            # 处理不同的列名格式
            date_str = row['日期'] if '日期' in row else row['date'] if 'date' in row else row['Date'] if 'Date' in row else row.name
            if hasattr(date_str, 'strftime'):
                date_str = date_str.strftime("%Y-%m-%d")
            
            prices.append(Price(
                open=round(float(row['开盘'] if '开盘' in row else row['open'] if 'open' in row else row['Open']), 2),
                close=round(float(row['收盘'] if '收盘' in row else row['close'] if 'close' in row else row['Close']), 2),
                high=round(float(row['最高'] if '最高' in row else row['high'] if 'high' in row else row['High']), 2),
                low=round(float(row['最低'] if '最低' in row else row['low'] if 'low' in row else row['Low']), 2),
                volume=int(row['成交量'] if '成交量' in row else row['volume'] if 'volume' in row else row['Volume']),
                time=date_str
            ))
        
        # 缓存结果
        _cache.set_prices(ticker, [p.model_dump() for p in prices])
        logger.info(f"成功获取{ticker}的{len(prices)}条价格数据")
        return prices
        
    except Exception as e:
        logger.error(f"获取{ticker}价格数据失败: {str(e)}")
        if _is_rate_limit_error(e):
            logger.warning("遇到API速率限制，将重试...")
            raise  # 重新抛出异常以便重试
        return []


@retry_with_backoff(max_retries=3, initial_delay=1, backoff_factor=2)
def get_financial_metrics_akshare(
    ticker: str,
    end_date: str,
    period: str = "annual",
    limit: int = 10,
) -> List[FinancialMetrics]:
    """
    从AKShare获取财务指标
    
    Args:
        ticker: 股票代码
        end_date: 结束日期
        period: 期间（annual表示年报）
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
        market = _detect_market(ticker)
        akshare_symbol = _convert_to_akshare_symbol(ticker, market)
        
        # 安全获取数据的辅助函数
        def safe_get(data, key, default=None):
            return data.get(key, default) if isinstance(data, dict) else default
        
        def safe_divide(a, b):
            if a is not None and b is not None and b != 0:
                return a / b
            return None
        
        # 获取财务数据
        financial_data = {}
        if market == 'a':
            # A股财务指标
            try:
                df = ak.stock_financial_analysis_indicator(symbol=akshare_symbol)
                if not df.empty:
                    latest_report = df.iloc[-1].to_dict()
                    financial_data.update(latest_report)
            except:
                pass
            
            # 获取资产负债表和利润表
            try:
                balance_sheet = ak.stock_balance_sheet_by_report_em(symbol=akshare_symbol)
                income_stmt = ak.stock_profit_em(symbol=akshare_symbol)
                
                if not balance_sheet.empty:
                    latest_balance = balance_sheet.iloc[-1].to_dict()
                    financial_data.update(latest_balance)
                
                if not income_stmt.empty:
                    latest_income = income_stmt.iloc[-1].to_dict()
                    financial_data.update(latest_income)
            except:
                pass
        
        # 构建财务指标对象
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        report_date = (end_dt - timedelta(days=365)).strftime("%Y-%m-%d")  # 年报
        
        metrics = FinancialMetrics(
            ticker=ticker,
            report_period=report_date,
            period=period,
            currency="CNY" if market == 'a' else "HKD" if market == 'hk' else "USD",
            market_cap=safe_get(financial_data, '总市值'),
            enterprise_value=None,  # AKShare不直接提供
            price_to_earnings_ratio=safe_get(financial_data, '市盈率'),
            price_to_book_ratio=safe_get(financial_data, '市净率'),
            price_to_sales_ratio=safe_get(financial_data, '市销率'),
            enterprise_value_to_ebitda_ratio=None,
            enterprise_value_to_revenue_ratio=None,
            free_cash_flow_yield=None,
            peg_ratio=None,
            gross_margin=safe_get(financial_data, '销售毛利率'),
            operating_margin=safe_get(financial_data, '营业利润率'),
            net_margin=safe_get(financial_data, '净利润率'),
            return_on_equity=safe_get(financial_data, '净资产收益率'),
            return_on_assets=safe_get(financial_data, '总资产报酬率'),
            return_on_invested_capital=None,
            asset_turnover=safe_get(financial_data, '总资产周转率'),
            inventory_turnover=safe_get(financial_data, '存货周转率'),
            receivables_turnover=safe_get(financial_data, '应收账款周转率'),
            days_sales_outstanding=None,
            operating_cycle=None,
            working_capital_turnover=None,
            current_ratio=safe_get(financial_data, '流动比率'),
            quick_ratio=safe_get(financial_data, '速动比率'),
            cash_ratio=None,
            operating_cash_flow_ratio=None,
            debt_to_equity=safe_get(financial_data, '资产负债率'),
            debt_to_assets=None,
            interest_coverage=None,
            revenue_growth=safe_get(financial_data, '营业收入同比增长率'),
            earnings_growth=safe_get(financial_data, '净利润同比增长率'),
            book_value_growth=None,
            earnings_per_share_growth=None,
            free_cash_flow_growth=None,
            operating_income_growth=None,
            ebitda_growth=None,
            payout_ratio=None,
            earnings_per_share=safe_get(financial_data, '基本每股收益'),
            book_value_per_share=safe_get(financial_data, '每股净资产'),
            free_cash_flow_per_share=None
        )
        
        # 缓存结果
        _cache.set_financial_metrics(ticker, [metrics.model_dump()])
        logger.info(f"成功获取{ticker}的财务指标数据")
        return [metrics]
        
    except Exception as e:
        logger.error(f"获取{ticker}财务指标失败: {str(e)}")
        return []


def prices_to_df_akshare(prices: List[Price]) -> pd.DataFrame:
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


def get_price_data_akshare(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取价格数据并转换为DataFrame"""
    prices = get_prices_akshare(ticker, start_date, end_date)
    return prices_to_df_akshare(prices)


@retry_with_backoff(max_retries=3, initial_delay=1, backoff_factor=2)
def get_company_info_akshare(ticker: str) -> dict:
    """获取公司基本信息"""
    try:
        market = _detect_market(ticker)
        akshare_symbol = _convert_to_akshare_symbol(ticker, market)
        
        info = {}
        if market == 'a':
            # A股公司信息
            try:
                df = ak.stock_individual_info_em(symbol=akshare_symbol)
                if not df.empty:
                    info = {row['item']: row['value'] for _, row in df.iterrows()}
            except:
                pass
            
            return {
                "name": info.get('公司名称', ticker),
                "sector": info.get('所属行业', 'Unknown'),
                "industry": info.get('细分行业', 'Unknown'),
                "country": "China",
                "website": info.get('公司网址', ''),
                "description": info.get('公司简介', '')
            }
        else:
            # 港股和美股信息有限
            return {
                "name": ticker,
                "sector": "Unknown",
                "industry": "Unknown",
                "country": "Hong Kong" if market == 'hk' else "USA",
                "website": "",
                "description": ""
            }
            
    except Exception as e:
        logger.error(f"获取{ticker}公司信息失败: {str(e)}")
        return {}


@retry_with_backoff(max_retries=3, initial_delay=1, backoff_factor=2)
def test_akshare_connection() -> bool:
    """测试AKShare连接"""
    try:
        # 测试获取A股数据
        df = ak.stock_zh_a_spot()
        return bool(df is not None and not df.empty)
    except Exception as e:
        logger.error(f"测试连接失败: {e}")
        if _is_rate_limit_error(e):
            logger.warning("遇到API速率限制，将重试...")
            raise  # 重新抛出异常以便重试
        return False


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试AKShare API连接...")
    
    if test_akshare_connection():
        print("✅ AKShare API连接成功")
        
        # 测试获取价格数据
        print("\n📊 测试获取A股价格数据...")
        prices = get_prices_akshare("600519", "2024-01-01", "2024-01-10")
        if prices:
            print(f"✅ 成功获取{len(prices)}条价格数据")
            print(f"最新价格: ¥{prices[-1].close}")
        
        # 测试获取财务指标
        print("\n💰 测试获取A股财务指标...")
        metrics = get_financial_metrics_akshare("600519", "2024-01-10")
        if metrics:
            print(f"✅ 成功获取财务指标")
            print(f"P/E比率: {metrics[0].price_to_earnings_ratio}")
    else:
        print("❌ AKShare API连接失败")