"""
基于AKShare的API模块
使用AKShare库获取免费的股票数据，保持与yfinance_api一致的接口模式
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
import sys
import os
import time
import random
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
        'limit exceeded',
        'connection error',
        'timeout'
    ]
    
    # 检查错误消息中是否包含速率限制关键词
    return any(indicator in error_msg for indicator in rate_limit_indicators)

RETRY_ATTEMPTS = 3
RETRY_WAIT_MIN = 2
RETRY_WAIT_MAX = 10

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
        # 根据市场类型选择不同的AKShare函数
        market = _detect_market(ticker)
        formatted_symbol = _format_symbol(ticker, market)
        
        if market == 'cn':
            # A股数据
            df = ak.stock_zh_a_hist(symbol=formatted_symbol, period="daily", 
                                   start_date=start_date.replace('-', ''), 
                                   end_date=end_date.replace('-', ''), adjust="qfq")
        elif market == 'hk':
            # 港股数据
            df = ak.stock_hk_hist(symbol=formatted_symbol, period="daily", 
                                 start_date=start_date, end_date=end_date, adjust="qfq")
        elif market == 'us':
            # 美股数据 - 优先使用akshare获取历史数据
            try:
                df = ak.stock_us_daily(symbol=formatted_symbol)
                
                # 过滤日期范围
                if df is not None and not df.empty:
                    df['date'] = pd.to_datetime(df['date'], format='mixed', errors='coerce')
                    start_dt = pd.to_datetime(start_date, format='mixed', errors='coerce')
                    end_dt = pd.to_datetime(end_date, format='mixed', errors='coerce')
                    mask = (df['date'] >= start_dt) & (df['date'] <= end_dt)
                    df = df.loc[mask]
                    
                    if df.empty:
                        logger.warning(f"akshare未返回{ticker}在指定日期范围内的历史数据")
                        return []
                        
                    # 检查并处理成交量为0的情况（可能是最新一天还未交易）
                    df = _handle_zero_volume(df)
                        
                    prices = []
                    for _, row in df.iterrows():
                        try:
                            # 处理日期格式，避免NaT错误
                            if hasattr(row['date'], 'strftime'):
                                time_str = row['date'].strftime("%Y-%m-%d")
                            else:
                                parsed_date = pd.to_datetime(row['date'], format='mixed', errors='coerce')
                                time_str = parsed_date.strftime("%Y-%m-%d") if not pd.isna(parsed_date) and hasattr(parsed_date, 'strftime') else None
                            
                            if time_str:
                                # 检查成交量是否为0，如果是则记录警告
                                volume = int(row['volume'])
                                if volume == 0:
                                    logger.warning(f"股票{ticker}在{time_str}的成交量为0，可能是非交易日或数据异常")
                                
                                prices.append(Price(
                                    open=round(float(row['open']), 2),
                                    close=round(float(row['close']), 2),
                                    high=round(float(row['high']), 2),
                                    low=round(float(row['low']), 2),
                                    volume=volume,
                                    time=time_str
                                ))
                        except (ValueError, KeyError) as e:
                            logger.warning(f"美股数据格式转换错误: {e}")
                            continue
                    
                    logger.info(f"使用akshare成功获取{ticker}的{len(prices)}条价格数据")
                    return prices
                else:
                    logger.warning(f"akshare未返回{ticker}的历史数据")
                    return []
                    
            except Exception as ak_error:
                logger.error(f"akshare获取{ticker}数据失败: {str(ak_error)}")
                # 如果akshare失败，可以尝试使用yfinance作为备用方案
                try:
                    import yfinance as yf
                    yf_ticker = yf.Ticker(formatted_symbol)
                    
                    # 获取历史数据
                    hist = yf_ticker.history(start=start_date, end=end_date)
                    
                    if hist is not None and not hist.empty:
                        # 检查并处理成交量为0的情况
                        hist = _handle_zero_volume_yf(hist)
                        
                        prices = []
                        for date, row in hist.iterrows():
                            # 检查成交量是否为0，如果是则记录警告
                            volume = int(row['Volume'])
                            if volume == 0:
                                logger.warning(f"股票{ticker}在{date.strftime('%Y-%m-%d')}的成交量为0，可能是非交易日或数据异常")
                            
                            prices.append(Price(
                                open=round(float(row['Open']), 2),
                                close=round(float(row['Close']), 2),
                                high=round(float(row['High']), 2),
                                low=round(float(row['Low']), 2),
                                volume=volume,
                                time=date.strftime("%Y-%m-%d")
                            ))
                        logger.info(f"使用yfinance备用方案成功获取{ticker}的{len(prices)}条价格数据")
                        return prices
                    else:
                        logger.warning(f"yfinance备用方案也未返回{ticker}的历史数据")
                        return []
                        
                except ImportError:
                    logger.error("yfinance未安装，无法使用备用方案获取美股数据")
                    return []
                except Exception as yf_error:
                    logger.error(f"yfinance备用方案获取{ticker}数据失败: {str(yf_error)}")
                    return []
        else:
            logger.warning(f"不支持的股票代码格式: {ticker}")
            return []
        
        if df is None or df.empty:
            logger.warning(f"未获取到{ticker}的价格数据")
            return []
        
        # 转换数据格式
        prices = []
        for _, row in df.iterrows():
            try:
                # 根据市场类型确定列名
                if market == 'us':
                    # 美股使用英文列名
                    open_col = 'open'
                    close_col = 'close' 
                    high_col = 'high'
                    low_col = 'low'
                    volume_col = 'volume'
                    date_col = 'date'
                    
                    # 处理日期格式，避免NaT错误
                    if hasattr(row[date_col], 'strftime'):
                        time_str = row[date_col].strftime("%Y-%m-%d")
                    else:
                        parsed_date = pd.to_datetime(row[date_col], format='mixed', errors='coerce')
                        time_str = parsed_date.strftime("%Y-%m-%d") if not pd.isna(parsed_date) and hasattr(parsed_date, 'strftime') else None
                else:
                    # A股和港股使用中文列名
                    open_col = '开盘'
                    close_col = '收盘'
                    high_col = '最高'
                    low_col = '最低'
                    volume_col = '成交量'
                    date_col = '日期'
                    
                    # 处理日期格式，避免NaT错误
                    parsed_date = pd.to_datetime(row[date_col], format='mixed', errors='coerce')
                    time_str = parsed_date.strftime("%Y-%m-%d") if not pd.isna(parsed_date) and hasattr(parsed_date, 'strftime') else None
                
                prices.append(Price(
                    open=round(float(row[open_col]), 2),
                    close=round(float(row[close_col]), 2),
                    high=round(float(row[high_col]), 2),
                    low=round(float(row[low_col]), 2),
                    volume=int(row[volume_col]),
                    time=time_str
                ))
            except (ValueError, KeyError) as e:
                logger.warning(f"数据格式转换错误: {e}")
                continue
        
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

def _format_symbol(symbol: str, market: str) -> str:
    """格式化股票代码为AKShare需要的格式"""
    if market == 'hk':
        if symbol.startswith('hk'):
            return symbol[2:]  # 去掉hk前缀
        else:
            return symbol
    elif market == 'us':
        if symbol.startswith('us'):
            return symbol[2:]  # 去掉us前缀
        else:
            return symbol
    return symbol

def _detect_market(symbol: str) -> str:
    """检测股票代码所属市场"""
    if symbol.startswith('hk'):
        return 'hk'  # 港股
    elif symbol.startswith('us'):
        return 'us'  # 美股
    elif symbol.isdigit() and len(symbol) == 6:
        return 'cn'  # A股数字代码
    elif symbol.isdigit() and len(symbol) == 5:
        return 'hk'  # 港股数字代码
    elif symbol.isalpha() and 1 <= len(symbol) <= 5:
        return 'us'  # 美股字母代码
    else:
        return 'cn'  # 默认A股

@retry_with_backoff(max_retries=3, initial_delay=1, backoff_factor=2)
def get_financial_metrics_akshare(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> List[FinancialMetrics]:
    """
    从AKShare获取财务指标
    
    Args:
        ticker: 股票代码
        end_date: 结束日期
        period: 期间（ttm表示过去12个月）
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
        formatted_symbol = _format_symbol(ticker, market)
        
        # 暂时返回空列表，后续可以根据需要实现具体的财务指标获取逻辑
        logger.warning(f"暂不支持 {market} 市场的财务指标获取")
        
        # 构建一个基本的财务指标对象作为示例
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        report_date = (end_dt - timedelta(days=90)).strftime("%Y-%m-%d")
        
        metrics = FinancialMetrics(
            ticker=ticker,
            report_period=report_date,
            period=period,
            currency='CNY' if market == 'cn' else 'HKD' if market == 'hk' else 'USD',
            market_cap=None,
            enterprise_value=None,
            price_to_earnings_ratio=None,
            price_to_book_ratio=None,
            price_to_sales_ratio=None,
            enterprise_value_to_ebitda_ratio=None,
            enterprise_value_to_revenue_ratio=None,
            free_cash_flow_yield=None,
            peg_ratio=None,
            gross_margin=None,
            operating_margin=None,
            net_margin=None,
            return_on_equity=None,
            return_on_assets=None,
            return_on_invested_capital=None,
            asset_turnover=None,
            inventory_turnover=None,
            receivables_turnover=None,
            days_sales_outstanding=None,
            operating_cycle=None,
            working_capital_turnover=None,
            current_ratio=None,
            quick_ratio=None,
            cash_ratio=None,
            operating_cash_flow_ratio=None,
            debt_to_equity=None,
            debt_to_assets=None,
            interest_coverage=None,
            revenue_growth=None,
            earnings_growth=None,
            book_value_growth=None,
            earnings_per_share_growth=None,
            free_cash_flow_growth=None,
            operating_income_growth=None,
            ebitda_growth=None,
            payout_ratio=None,
            earnings_per_share=None,
            book_value_per_share=None,
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
    df["Date"] = pd.to_datetime(df["time"], format='mixed', errors='coerce')
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
        formatted_symbol = _format_symbol(ticker, market)
        
        # 暂时返回基本信息，后续可以根据需要实现具体的公司信息获取逻辑
        logger.warning(f"暂不支持 {market} 市场的公司信息获取")
        
        return {
            "name": ticker,
            "sector": "Unknown",
            "industry": "Unknown",
            "country": "China" if market == 'cn' else "Hong Kong" if market == 'hk' else "USA",
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
        df = ak.stock_zh_a_spot_em()
        return df is not None and not df.empty
    except Exception as e:
        logger.error(f"测试连接失败: {e}")
        if _is_rate_limit_error(e):
            logger.warning("遇到API速率限制，将重试...")
            raise  # 重新抛出异常以便重试
        return False

def _handle_zero_volume(df: pd.DataFrame) -> pd.DataFrame:
    """
    处理成交量为0的情况，特别是最新一天可能还未交易的情况
    
    Args:
        df: 包含股票数据的DataFrame
        
    Returns:
        处理后的DataFrame
    """
    if df is None or df.empty:
        return df
    
    # 按日期排序，确保最新日期在最后
    df = df.sort_values('date')
    
    # 检查最新一天的成交量是否为0
    latest_row = df.iloc[-1]
    if latest_row['volume'] == 0:
        logger.warning(f"最新交易日{latest_row['date']}的成交量为0，可能是非交易日或数据异常")
        
        # 如果只有一天数据且成交量为0，则返回空DataFrame
        if len(df) == 1:
            logger.warning("只有一天数据且成交量为0，返回空数据")
            return pd.DataFrame()
        
        # 如果有前一天数据，可以考虑使用前一天的数据
        # 这里我们只是记录警告，不自动替换数据
        # 因为成交量为0可能是正常情况（如节假日）
    
    return df


def _handle_zero_volume_yf(hist: pd.DataFrame) -> pd.DataFrame:
    """
    处理yfinance返回数据中成交量为0的情况
    
    Args:
        hist: yfinance返回的历史数据DataFrame
        
    Returns:
        处理后的DataFrame
    """
    if hist is None or hist.empty:
        return hist
    
    # 检查最新一天的成交量是否为0
    latest_row = hist.iloc[-1]
    if latest_row['Volume'] == 0:
        logger.warning(f"最新交易日{latest_row.name}的成交量为0，可能是非交易日或数据异常")
        
        # 如果只有一天数据且成交量为0，则返回空DataFrame
        if len(hist) == 1:
            logger.warning("只有一天数据且成交量为0，返回空数据")
            return pd.DataFrame()
    
    return hist


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试AKShare API连接...")
    
    if test_akshare_connection():
        print("✅ AKShare API连接成功")
        
        # 测试获取A股价格数据
        print("\n📊 测试获取000001价格数据...")
        prices = get_prices_akshare("000001", "2024-01-01", "2024-01-10")
        if prices:
            print(f"✅ 成功获取{len(prices)}条价格数据")
            print(f"最新价格: ¥{prices[-1].close}")
        
        # 测试获取港股价格数据
        print("\n📊 测试获取hk00700价格数据...")
        prices = get_prices_akshare("hk00700", "2024-01-01", "2024-01-10")
        if prices:
            print(f"✅ 成功获取{len(prices)}条价格数据")
            print(f"最新价格: HK${prices[-1].close}")
        
        # 测试获取财务指标
        print("\n💰 测试获取000001财务指标...")
        metrics = get_financial_metrics_akshare("000001", "2024-01-10")
        if metrics:
            print(f"✅ 成功获取财务指标")
    else:
        print("❌ AKShare API连接失败")