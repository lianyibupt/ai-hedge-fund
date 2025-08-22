"""
简化版的Yahoo Finance API模块
使用基础的yfinance功能，避免复杂的缓存和重试机制
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random


def get_stock_data_simple(ticker: str, period: str = "3mo") -> pd.DataFrame:
    """
    获取股票数据的简化版本
    
    Args:
        ticker: 股票代码
        period: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    
    Returns:
        包含OHLCV数据的DataFrame
    """
    try:
        print(f"📊 正在获取 {ticker} 的数据...")
        
        # 添加随机延迟避免频率限制
        delay = random.uniform(0.5, 1.5)
        time.sleep(delay)
        
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            print(f"⚠️ 未能获取到 {ticker} 的数据")
            return pd.DataFrame()
        
        # 重命名列为小写
        hist.columns = [col.lower() for col in hist.columns]
        
        print(f"✅ 成功获取 {ticker} 的 {len(hist)} 天数据")
        return hist
        
    except Exception as e:
        print(f"❌ 获取 {ticker} 数据失败: {str(e)}")
        return pd.DataFrame()


def get_stock_info_simple(ticker: str) -> dict:
    """
    获取股票基本信息
    
    Args:
        ticker: 股票代码
    
    Returns:
        股票信息字典
    """
    try:
        print(f"💰 正在获取 {ticker} 的财务信息...")
        
        # 添加延迟
        time.sleep(random.uniform(0.5, 1.0))
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info:
            print(f"⚠️ 未能获取到 {ticker} 的财务信息")
            return {}
        
        # 提取关键财务指标
        key_metrics = {
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'Unknown'),
            'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
            'pe_ratio': info.get('trailingPE'),
            'pb_ratio': info.get('priceToBook'),
            'market_cap': info.get('marketCap'),
            'revenue_growth': info.get('revenueGrowth'),
            'profit_margins': info.get('profitMargins'),
            'debt_to_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'roa': info.get('returnOnAssets'),
            'roe': info.get('returnOnEquity'),
            'gross_margins': info.get('grossMargins'),
            'operating_margins': info.get('operatingMargins')
        }
        
        print(f"✅ 成功获取 {ticker} 的财务信息")
        return key_metrics
        
    except Exception as e:
        print(f"❌ 获取 {ticker} 财务信息失败: {str(e)}")
        return {}


def calculate_technical_indicators_simple(df: pd.DataFrame) -> dict:
    """
    计算基础技术指标
    
    Args:
        df: 包含OHLCV数据的DataFrame
    
    Returns:
        技术指标字典
    """
    if df.empty or len(df) < 20:
        return {}
    
    try:
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        # MACD计算
        exp1 = close.ewm(span=12).mean()
        exp2 = close.ewm(span=26).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9).mean()
        macd_histogram = macd_line - signal_line
        
        # RSI计算
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # 布林带计算
        bb_period = 20
        bb_std = 2
        bb_middle = close.rolling(window=bb_period).mean()
        bb_std_dev = close.rolling(window=bb_period).std()
        bb_upper = bb_middle + (bb_std_dev * bb_std)
        bb_lower = bb_middle - (bb_std_dev * bb_std)
        
        # 成交量分析
        volume_ma = volume.rolling(window=5).mean()
        volume_ratio = volume / volume_ma
        
        # 当前值
        current_values = {
            'macd': {
                'line': float(macd_line.iloc[-1]),
                'signal': float(signal_line.iloc[-1]),
                'histogram': float(macd_histogram.iloc[-1]),
                'is_bullish': bool(macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-1] > macd_line.iloc[-2])
            },
            'rsi': {
                'value': float(rsi.iloc[-1]),
                'is_oversold': bool(rsi.iloc[-1] < 30),
                'is_overbought': bool(rsi.iloc[-1] > 70),
                'is_bullish': bool(rsi.iloc[-1] > 50 and rsi.iloc[-1] < 70)
            },
            'bollinger': {
                'upper': float(bb_upper.iloc[-1]),
                'middle': float(bb_middle.iloc[-1]),
                'lower': float(bb_lower.iloc[-1]),
                'current_price': float(close.iloc[-1]),
                'position': float((close.iloc[-1] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])),
                'touching_lower': bool(close.iloc[-1] <= bb_lower.iloc[-1] * 1.01),
                'touching_upper': bool(close.iloc[-1] >= bb_upper.iloc[-1] * 0.99)
            },
            'volume': {
                'current_ratio': float(volume_ratio.iloc[-1]),
                'is_high_volume': bool(volume_ratio.iloc[-1] > 1.5),
                'avg_volume': float(volume_ma.iloc[-1])
            }
        }
        
        return current_values
        
    except Exception as e:
        print(f"❌ 技术指标计算失败: {str(e)}")
        return {}


def generate_simple_trading_signal(df: pd.DataFrame, stock_info: dict = None) -> dict:
    """
    生成简单的交易信号
    
    Args:
        df: 价格数据DataFrame
        stock_info: 股票信息字典
    
    Returns:
        交易信号字典
    """
    if df.empty:
        return {
            'signal': 'neutral',
            'confidence': 0,
            'reason': '数据不足'
        }
    
    indicators = calculate_technical_indicators_simple(df)
    if not indicators:
        return {
            'signal': 'neutral',
            'confidence': 0,
            'reason': '技术指标计算失败'
        }
    
    macd = indicators.get('macd', {})
    rsi = indicators.get('rsi', {})
    bb = indicators.get('bollinger', {})
    volume = indicators.get('volume', {})
    
    # 信号评分
    bullish_score = 0
    bearish_score = 0
    
    signals = []
    
    # MACD分析
    if macd.get('is_bullish'):
        bullish_score += 1
        signals.append('MACD看多')
    elif macd.get('line', 0) < macd.get('signal', 0):
        bearish_score += 1
        signals.append('MACD看空')
    
    # RSI分析
    if rsi.get('is_bullish'):
        bullish_score += 1
        signals.append('RSI看多')
    elif rsi.get('is_overbought'):
        bearish_score += 1
        signals.append('RSI超买')
    elif rsi.get('is_oversold'):
        bullish_score += 0.5
        signals.append('RSI超卖')
    
    # 布林带分析
    if bb.get('touching_lower'):
        bullish_score += 1
        signals.append('触及布林下轨')
    elif bb.get('touching_upper'):
        bearish_score += 1
        signals.append('触及布林上轨')
    
    # 成交量分析
    if volume.get('is_high_volume'):
        if bullish_score > bearish_score:
            bullish_score += 0.5
            signals.append('放量确认')
        elif bearish_score > bullish_score:
            bearish_score += 0.5
            signals.append('放量下跌')
    
    # 生成最终信号
    total_signals = bullish_score + bearish_score
    
    if bullish_score > bearish_score and bullish_score >= 2:
        signal = 'bullish'
        confidence = min(int((bullish_score / max(total_signals, 1)) * 100), 95)
    elif bearish_score > bullish_score and bearish_score >= 2:
        signal = 'bearish'
        confidence = min(int((bearish_score / max(total_signals, 1)) * 100), 95)
    else:
        signal = 'neutral'
        confidence = 50
    
    return {
        'signal': signal,
        'confidence': confidence,
        'reason': '; '.join(signals) if signals else '信号不明确',
        'details': {
            'bullish_score': bullish_score,
            'bearish_score': bearish_score,
            'indicators': indicators
        }
    }


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试简化版 yfinance API...")
    
    # 测试获取数据
    data = get_stock_data_simple("AAPL", "1mo")
    if not data.empty:
        print(f"✅ 数据获取成功，共 {len(data)} 天")
        
        # 测试技术指标
        indicators = calculate_technical_indicators_simple(data)
        if indicators:
            print("✅ 技术指标计算成功")
            
            # 测试交易信号
            signal = generate_simple_trading_signal(data)
            print(f"✅ 交易信号生成成功: {signal['signal']} (信心度: {signal['confidence']}%)")
            print(f"原因: {signal['reason']}")
    else:
        print("❌ 测试失败")