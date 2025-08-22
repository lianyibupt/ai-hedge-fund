"""
个性化技术指标计算模块
支持2-3周交易周期的技术分析指标计算
包含MACD、RSI、布林带和成交量分析
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple


def calculate_macd(prices_df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, pd.Series]:
    """
    计算MACD指标
    
    Args:
        prices_df: 包含价格数据的DataFrame
        fast_period: 快线周期，默认12
        slow_period: 慢线周期，默认26
        signal_period: 信号线周期，默认9
    
    Returns:
        包含DIF、DEA、MACD柱状图的字典
    """
    close = prices_df['close']
    
    # 计算EMA
    ema_fast = close.ewm(span=fast_period).mean()
    ema_slow = close.ewm(span=slow_period).mean()
    
    # 计算DIF（快线）
    dif = ema_fast - ema_slow
    
    # 计算DEA（慢线/信号线）
    dea = dif.ewm(span=signal_period).mean()
    
    # 计算MACD柱状图
    macd_histogram = (dif - dea) * 2
    
    return {
        'dif': dif,
        'dea': dea,
        'macd': macd_histogram
    }


def calculate_rsi(prices_df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    计算RSI指标
    
    Args:
        prices_df: 包含价格数据的DataFrame
        period: RSI周期，默认14
    
    Returns:
        RSI值的Series
    """
    close = prices_df['close']
    delta = close.diff()
    
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_bollinger_bands(prices_df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
    """
    计算布林带指标
    
    Args:
        prices_df: 包含价格数据的DataFrame
        period: 移动平均周期，默认20
        std_dev: 标准差倍数，默认2.0
    
    Returns:
        包含上轨、中轨、下轨的字典
    """
    close = prices_df['close']
    
    # 计算中轨（移动平均线）
    middle_band = close.rolling(window=period).mean()
    
    # 计算标准差
    std = close.rolling(window=period).std()
    
    # 计算上轨和下轨
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    return {
        'upper': upper_band,
        'middle': middle_band,
        'lower': lower_band
    }


def calculate_volume_analysis(prices_df: pd.DataFrame, ma_period: int = 5) -> Dict[str, Any]:
    """
    计算成交量分析指标
    
    Args:
        prices_df: 包含价格和成交量数据的DataFrame
        ma_period: 成交量移动平均周期，默认5
    
    Returns:
        包含成交量分析结果的字典
    """
    volume = prices_df['volume']
    
    # 计算成交量移动平均
    volume_ma = volume.rolling(window=ma_period).mean()
    
    # 计算成交量比率
    volume_ratio = volume / volume_ma
    
    # 计算最新的成交量放大倍数
    latest_volume_ratio = volume_ratio.iloc[-1] if len(volume_ratio) > 0 else 1.0
    
    return {
        'volume_ma': volume_ma,
        'volume_ratio': volume_ratio,
        'latest_ratio': latest_volume_ratio,
        'is_volume_surge': latest_volume_ratio >= 1.5  # 1.5倍以上认为是放量
    }


def analyze_macd_signals(macd_data: Dict[str, pd.Series]) -> Dict[str, Any]:
    """
    分析MACD交易信号
    
    Args:
        macd_data: MACD计算结果
    
    Returns:
        MACD信号分析结果
    """
    dif = macd_data['dif']
    dea = macd_data['dea']
    
    if len(dif) < 2 or len(dea) < 2:
        return {
            'signal': '中性',
            'reason': '数据不足',
            'is_golden_cross': False,
            'is_death_cross': False,
            'dif_above_zero': False,
            'dif_trend': '中性',
            'current_dif': 0.0,
            'current_dea': 0.0,
            'macd_histogram': 0.0
        }
    
    # 获取最新和前一个值
    current_dif = dif.iloc[-1]
    prev_dif = dif.iloc[-2]
    current_dea = dea.iloc[-1]
    prev_dea = dea.iloc[-2]
    
    # 检测金叉和死叉
    is_golden_cross = prev_dif <= prev_dea and current_dif > current_dea
    is_death_cross = prev_dif >= prev_dea and current_dif < current_dea
    
    # 判断DIF是否在0轴上方
    dif_above_zero = current_dif > 0
    
    # 判断DIF趋势
    if current_dif > prev_dif:
        dif_trend = '上升'
    elif current_dif < prev_dif:
        dif_trend = '下降'
    else:
        dif_trend = '平缓'
    
    # 生成信号
    signal = '中性'
    reason = ''
    
    if is_golden_cross and not dif_above_zero and dif_trend == '上升':
        signal = '看涨'
        reason = 'DIF在0轴下方金叉DEA且向上发散'
    elif dif_above_zero and dif_trend == '上升' and current_dif > current_dea:
        signal = '看涨'
        reason = 'DIF在0轴上方向上，趋势延续'
    elif is_golden_cross and dif_above_zero:
        signal = '看涨'
        reason = 'DIF在0轴上方金叉DEA'
    elif is_death_cross and dif_above_zero:
        signal = '看跌'
        reason = 'DIF在0轴上方死叉DEA'
    elif dif_trend == '下降' and current_dif > 0:
        signal = '看跌'
        reason = 'DIF在高位拐头向下'
    elif not dif_above_zero and is_death_cross:
        signal = '看跌'
        reason = 'DIF在0轴下方死叉DEA'
    
    # 计算MACD柱状图
    current_macd = macd_data['macd'].iloc[-1] if len(macd_data['macd']) > 0 else 0.0
    
    return {
        'signal': signal,
        'reason': reason,
        'is_golden_cross': is_golden_cross,
        'is_death_cross': is_death_cross,
        'dif_above_zero': dif_above_zero,
        'dif_trend': dif_trend,
        'current_dif': float(current_dif),
        'current_dea': float(current_dea),
        'macd_histogram': float(current_macd),
        'dif_dea_diff': float(current_dif - current_dea)
    }


def analyze_rsi_signals(rsi: pd.Series) -> Dict[str, Any]:
    """
    分析RSI交易信号
    
    Args:
        rsi: RSI计算结果
    
    Returns:
        RSI信号分析结果
    """
    if len(rsi) < 2:
        return {
            'signal': '中性',
            'reason': '数据不足',
            'current_rsi': 50.0,
            'prev_rsi': 50.0,
            'is_oversold_recovery': False,
            'is_overbought_decline': False,
            'rsi_trend': '平缓'
        }
    
    current_rsi = rsi.iloc[-1]
    prev_rsi = rsi.iloc[-2]
    
    # 判断RSI趋势
    if current_rsi > prev_rsi:
        rsi_trend = '上升'
    elif current_rsi < prev_rsi:
        rsi_trend = '下降'
    else:
        rsi_trend = '平缓'
    
    # 检测超卖恢复
    is_oversold_recovery = prev_rsi <= 30 and current_rsi > 40 and current_rsi < 70
    
    # 检测超买下跌
    is_overbought_decline = prev_rsi >= 70 and current_rsi < 60
    
    # 生成信号
    signal = '中性'
    reason = ''
    
    if is_oversold_recovery:
        signal = '看涨'
        reason = f'RSI从{prev_rsi:.1f}回升至{current_rsi:.1f}，突破超卖区'
    elif is_overbought_decline:
        signal = '看跌'
        reason = f'RSI从{prev_rsi:.1f}回落至{current_rsi:.1f}，离开超买区'
    elif current_rsi > 70:
        signal = '看跌'
        reason = f'RSI高于70({current_rsi:.1f})，进入超买区'
    elif current_rsi < 30:
        signal = '看涨'
        reason = f'RSI低于30({current_rsi:.1f})，进入超卖区'
    elif current_rsi >= 50 and rsi_trend == '上升':
        signal = '看涨'
        reason = f'RSI在中性区上方({current_rsi:.1f})且上升'
    elif current_rsi <= 50 and rsi_trend == '下降':
        signal = '看跌'
        reason = f'RSI在中性区下方({current_rsi:.1f})且下降'
    
    return {
        'signal': signal,
        'reason': reason,
        'current_rsi': float(current_rsi),
        'prev_rsi': float(prev_rsi),
        'rsi_trend': rsi_trend,
        'is_oversold_recovery': bool(is_oversold_recovery),
        'is_overbought_decline': bool(is_overbought_decline),
        'is_oversold': current_rsi < 30,
        'is_overbought': current_rsi > 70
    }


def analyze_bollinger_signals(prices_df: pd.DataFrame, boll_data: Dict[str, pd.Series]) -> Dict[str, Any]:
    """
    分析布林带交易信号
    
    Args:
        prices_df: 价格数据
        boll_data: 布林带计算结果
    
    Returns:
        布林带信号分析结果
    """
    if len(prices_df) < 2:
        return {
            'signal': '中性',
            'reason': '数据不足',
            'price_position': 0.5,
            'is_touching_lower': False,
            'is_touching_upper': False,
            'middle_trend': '中性',
            'current_upper': 0.0,
            'current_middle': 0.0,
            'current_lower': 0.0,
            'current_close': 0.0
        }
    
    close = prices_df['close']
    high = prices_df['high']
    low = prices_df['low']
    
    upper = boll_data['upper']
    middle = boll_data['middle']
    lower = boll_data['lower']
    
    current_close = close.iloc[-1]
    current_high = high.iloc[-1]
    current_low = low.iloc[-1]
    current_upper = upper.iloc[-1]
    current_middle = middle.iloc[-1]
    current_lower = lower.iloc[-1]
    
    # 计算价格在布林带中的位置
    price_position = (current_close - current_lower) / (current_upper - current_lower)
    
    # 检测触及上轨或下轨
    is_touching_lower = current_low <= current_lower
    is_touching_upper = current_high >= current_upper
    
    # 判断中轨趋势
    if len(middle) >= 2:
        middle_trend = '上升' if middle.iloc[-1] > middle.iloc[-2] else '下降' if middle.iloc[-1] < middle.iloc[-2] else '平缓'
    else:
        middle_trend = '平缓'
    
    # 检测长下影线（企稳信号）
    has_long_lower_shadow = (current_close - current_low) > (current_high - current_close) * 2
    
    # 检测长上影线（见顶信号）
    has_long_upper_shadow = (current_high - current_close) > (current_close - current_low) * 2
    
    # 生成信号
    signal = '中性'
    reason = ''
    
    if is_touching_lower and has_long_lower_shadow and middle_trend == '上升':
        signal = '看涨'
        reason = '价格触及布林下轨并出现长下影线，中轨向上'
    elif is_touching_upper and has_long_upper_shadow:
        signal = '看跌'
        reason = '价格触及布林上轨并出现长上影线'
    elif price_position < 0.2 and middle_trend == '上升':
        signal = '看涨'
        reason = '价格接近布林下轨，中轨向上'
    elif price_position > 0.8:
        signal = '看跌'
        reason = '价格接近布林上轨，可能回调'
    elif is_touching_lower and not has_long_lower_shadow:
        signal = '看涨'
        reason = '价格触及布林下轨，支撑位'
    elif price_position < 0.3 and middle_trend != '下降':
        signal = '看涨'
        reason = '价格在布林下轨附近，中轨非下降趋势'
    
    return {
        'signal': signal,
        'reason': reason,
        'price_position': float(price_position),
        'is_touching_lower': bool(is_touching_lower),
        'is_touching_upper': bool(is_touching_upper),
        'middle_trend': middle_trend,
        'has_long_lower_shadow': bool(has_long_lower_shadow),
        'has_long_upper_shadow': bool(has_long_upper_shadow),
        'current_upper': float(current_upper),
        'current_middle': float(current_middle),
        'current_lower': float(current_lower),
        'current_close': float(current_close),
        'band_width': float((current_upper - current_lower) / current_middle * 100)
    }


def analyze_volume_signals(volume_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析成交量交易信号
    
    Args:
        volume_analysis: 成交量分析结果
    
    Returns:
        成交量信号分析结果
    """
    latest_ratio = volume_analysis['latest_ratio']
    is_volume_surge = volume_analysis['is_volume_surge']
    
    signal = '中性'
    reason = ''
    
    if is_volume_surge:
        signal = '看涨'
        reason = f'成交量放大{latest_ratio:.1f}倍，资金进场'
    elif latest_ratio < 0.7:
        signal = '看跌'
        reason = f'成交量萎缩({latest_ratio:.1f}倍)，缺乏资金支持'
    elif latest_ratio >= 1.2:
        signal = '看涨'
        reason = f'成交量温和放大({latest_ratio:.1f}倍)'
    elif latest_ratio < 0.8:
        signal = '看跌'
        reason = f'成交量偏低({latest_ratio:.1f}倍)'
    
    # 获取最新成交量数据
    volume_ma = volume_analysis['volume_ma']
    current_volume = volume_ma.iloc[-1] * latest_ratio if len(volume_ma) > 0 else 0
    avg_volume = volume_ma.iloc[-1] if len(volume_ma) > 0 else 0
    
    return {
        'signal': signal,
        'reason': reason,
        'volume_ratio': float(latest_ratio),
        'is_surge': bool(is_volume_surge),
        'current_volume': float(current_volume),
        'avg_volume': float(avg_volume),
        'volume_trend': '放量' if latest_ratio >= 1.2 else '缩量' if latest_ratio < 0.8 else '正常'
    }


def generate_comprehensive_signal(prices_df: pd.DataFrame) -> Dict[str, Any]:
    """
    基于个人交易策略生成综合交易信号
    
    Args:
        prices_df: 包含OHLCV数据的DataFrame
    
    Returns:
        综合交易信号分析结果
    """
    if len(prices_df) < 30:  # 需要足够的数据进行计算
        return {
            'signal': '中性',
            'confidence': 0,
            'reason': '数据不足，无法进行技术分析'
        }
    
    # 计算各项技术指标
    macd_data = calculate_macd(prices_df)
    rsi = calculate_rsi(prices_df)
    boll_data = calculate_bollinger_bands(prices_df)
    volume_analysis = calculate_volume_analysis(prices_df)
    
    # 分析各项信号
    macd_signals = analyze_macd_signals(macd_data)
    rsi_signals = analyze_rsi_signals(rsi)
    boll_signals = analyze_bollinger_signals(prices_df, boll_data)
    volume_signals = analyze_volume_signals(volume_analysis)
    
    # 信号权重
    weights = {
        'macd': 0.3,
        'rsi': 0.25,
        'boll': 0.25,
        'volume': 0.2
    }
    
    # 计算综合信号
    signals = [macd_signals, rsi_signals, boll_signals, volume_signals]
    signal_names = ['macd', 'rsi', 'boll', 'volume']
    
    bullish_score = 0
    bearish_score = 0
    
    reasons = []
    
    for i, signal_data in enumerate(signals):
        signal_name = signal_names[i]
        weight = weights[signal_name]
        
        if signal_data['signal'] == '看涨':
            bullish_score += weight
            reasons.append(f"{signal_name.upper()}: {signal_data['reason']}")
        elif signal_data['signal'] == '看跌':
            bearish_score += weight
            reasons.append(f"{signal_name.upper()}: {signal_data['reason']}")
    
    # 生成最终信号
    if bullish_score > bearish_score and bullish_score >= 0.5:
        final_signal = '看涨'
        confidence = int(bullish_score * 100)
    elif bearish_score > bullish_score and bearish_score >= 0.5:
        final_signal = '看跌'
        confidence = int(bearish_score * 100)
    else:
        final_signal = '中性'
        confidence = 50
    
    return {
        'signal': final_signal,
        'confidence': confidence,
        'reason': '; '.join(reasons) if reasons else '各项指标信号不明确',
        'details': {
            'macd': macd_signals,
            'rsi': rsi_signals,
            'bollinger': boll_signals,
            'volume': volume_signals
        },
        'scores': {
            'bullish_score': round(bullish_score, 2),
            'bearish_score': round(bearish_score, 2)
        },
        'raw_data': {
            'macd_data': {
                'dif': macd_data['dif'].iloc[-5:].tolist() if len(macd_data['dif']) >= 5 else macd_data['dif'].tolist(),
                'dea': macd_data['dea'].iloc[-5:].tolist() if len(macd_data['dea']) >= 5 else macd_data['dea'].tolist(),
                'macd': macd_data['macd'].iloc[-5:].tolist() if len(macd_data['macd']) >= 5 else macd_data['macd'].tolist()
            },
            'rsi_data': rsi.iloc[-5:].tolist() if len(rsi) >= 5 else rsi.tolist(),
            'bollinger_data': {
                'upper': boll_data['upper'].iloc[-5:].tolist() if len(boll_data['upper']) >= 5 else boll_data['upper'].tolist(),
                'middle': boll_data['middle'].iloc[-5:].tolist() if len(boll_data['middle']) >= 5 else boll_data['middle'].tolist(),
                'lower': boll_data['lower'].iloc[-5:].tolist() if len(boll_data['lower']) >= 5 else boll_data['lower'].tolist()
            },
            'volume_data': {
                'volume_ratio': volume_analysis['volume_ratio'].iloc[-5:].tolist() if len(volume_analysis['volume_ratio']) >= 5 else volume_analysis['volume_ratio'].tolist()
            },
            'price_data': {
                'close': prices_df['close'].iloc[-5:].tolist() if len(prices_df) >= 5 else prices_df['close'].tolist(),
                'high': prices_df['high'].iloc[-5:].tolist() if len(prices_df) >= 5 else prices_df['high'].tolist(),
                'low': prices_df['low'].iloc[-5:].tolist() if len(prices_df) >= 5 else prices_df['low'].tolist()
            }
        }
    }