"""
个性化技术指标计算模块
支持2-3周交易周期的技术分析指标计算
包含MACD、RSI、布林带、成交量、ROC、随机指标和威廉指标分析
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


def calculate_roc(prices_df: pd.DataFrame, period: int = 12) -> pd.Series:
    """
    计算ROC（变动率指标）
    
    Args:
        prices_df: 包含价格数据的DataFrame
        period: ROC周期，默认12
    
    Returns:
        ROC值的Series
    """
    close = prices_df['close']
    
    # 计算ROC = (当前收盘价 - N天前收盘价) / N天前收盘价 * 100
    roc = ((close - close.shift(period)) / close.shift(period)) * 100
    
    return roc


def calculate_stochastic(prices_df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
    """
    计算随机指标（KDJ指标）
    
    Args:
        prices_df: 包含价格数据的DataFrame
        k_period: K值周期，默认14
        d_period: D值周期，默认3
    
    Returns:
        包含K值和D值的字典
    """
    high = prices_df['high']
    low = prices_df['low']
    close = prices_df['close']
    
    # 计算最低价和最高价的N日最低和最高
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    # 计算%K值
    k_value = ((close - lowest_low) / (highest_high - lowest_low)) * 100
    
    # 计算%D值（%K的3日移动平均）
    d_value = k_value.rolling(window=d_period).mean()
    
    return {
        'k': k_value,
        'd': d_value
    }


def calculate_williams_r(prices_df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    计算威廉指标（W%R）
    
    Args:
        prices_df: 包含价格数据的DataFrame
        period: 威廉指标周期，默认14
    
    Returns:
        威廉指标值的Series
    """
    high = prices_df['high']
    low = prices_df['low']
    close = prices_df['close']
    
    # 计算N日最高价和最低价
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    
    # 计算威廉指标
    williams_r = ((highest_high - close) / (highest_high - lowest_low)) * -100
    
    return williams_r


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


def analyze_roc_signals(roc: pd.Series) -> Dict[str, Any]:
    """
    分析ROC交易信号
    
    Args:
        roc: ROC计算结果
    
    Returns:
        ROC信号分析结果
    """
    if len(roc) < 2:
        return {
            'signal': '中性',
            'reason': '数据不足',
            'current_roc': 0.0,
            'prev_roc': 0.0,
            'roc_trend': '平缓',
            'is_oversold': False,
            'is_overbought': False
        }
    
    current_roc = roc.iloc[-1]
    prev_roc = roc.iloc[-2]
    
    # 判断ROC趋势
    if current_roc > prev_roc:
        roc_trend = '上升'
    elif current_roc < prev_roc:
        roc_trend = '下降'
    else:
        roc_trend = '平缓'
    
    # 检测超买超卖
    is_oversold = current_roc < -10  # ROC低于-10%为超卖
    is_overbought = current_roc > 10  # ROC高于10%为超买
    
    # 生成信号
    signal = '中性'
    reason = ''
    
    if is_oversold and roc_trend == '上升':
        signal = '看涨'
        reason = f'ROC从超卖区({prev_roc:.1f}%)回升至{current_roc:.1f}%'
    elif is_overbought and roc_trend == '下降':
        signal = '看跌'
        reason = f'ROC从超买区({prev_roc:.1f}%)回落至{current_roc:.1f}%'
    elif current_roc > 0 and roc_trend == '上升':
        signal = '看涨'
        reason = f'ROC在零轴上方({current_roc:.1f}%)且上升'
    elif current_roc < 0 and roc_trend == '下降':
        signal = '看跌'
        reason = f'ROC在零轴下方({current_roc:.1f}%)且下降'
    elif is_oversold:
        signal = '看涨'
        reason = f'ROC处于超卖区({current_roc:.1f}%)'
    elif is_overbought:
        signal = '看跌'
        reason = f'ROC处于超买区({current_roc:.1f}%)'
    
    return {
        'signal': signal,
        'reason': reason,
        'current_roc': float(current_roc),
        'prev_roc': float(prev_roc),
        'roc_trend': roc_trend,
        'is_oversold': bool(is_oversold),
        'is_overbought': bool(is_overbought)
    }


def analyze_stochastic_signals(stoch_data: Dict[str, pd.Series]) -> Dict[str, Any]:
    """
    分析随机指标交易信号
    
    Args:
        stoch_data: 随机指标计算结果
    
    Returns:
        随机指标信号分析结果
    """
    k_value = stoch_data['k']
    d_value = stoch_data['d']
    
    if len(k_value) < 2 or len(d_value) < 2:
        return {
            'signal': '中性',
            'reason': '数据不足',
            'current_k': 50.0,
            'current_d': 50.0,
            'k_d_cross': '无交叉',
            'is_oversold': False,
            'is_overbought': False
        }
    
    current_k = k_value.iloc[-1]
    prev_k = k_value.iloc[-2]
    current_d = d_value.iloc[-1]
    prev_d = d_value.iloc[-2]
    
    # 检测金叉和死叉
    is_golden_cross = prev_k <= prev_d and current_k > current_d
    is_death_cross = prev_k >= prev_d and current_k < current_d
    
    # 判断交叉类型
    if is_golden_cross:
        k_d_cross = '金叉'
    elif is_death_cross:
        k_d_cross = '死叉'
    else:
        k_d_cross = '无交叉'
    
    # 检测超买超卖
    is_oversold = current_k < 20 and current_d < 20  # K和D都低于20为超卖
    is_overbought = current_k > 80 and current_d > 80  # K和D都高于80为超买
    
    # 生成信号
    signal = '中性'
    reason = ''
    
    if is_golden_cross and is_oversold:
        signal = '看涨'
        reason = 'KDJ在超卖区形成金叉'
    elif is_death_cross and is_overbought:
        signal = '看跌'
        reason = 'KDJ在超买区形成死叉'
    elif is_golden_cross and current_k < 50:
        signal = '看涨'
        reason = 'KDJ在低位形成金叉'
    elif is_death_cross and current_k > 50:
        signal = '看跌'
        reason = 'KDJ在高位形成死叉'
    elif is_oversold:
        signal = '看涨'
        reason = 'KDJ处于超卖区'
    elif is_overbought:
        signal = '看跌'
        reason = 'KDJ处于超买区'
    
    return {
        'signal': signal,
        'reason': reason,
        'current_k': float(current_k),
        'current_d': float(current_d),
        'k_d_cross': k_d_cross,
        'is_oversold': bool(is_oversold),
        'is_overbought': bool(is_overbought)
    }


def analyze_williams_r_signals(williams_r: pd.Series) -> Dict[str, Any]:
    """
    分析威廉指标交易信号
    
    Args:
        williams_r: 威廉指标计算结果
    
    Returns:
        威廉指标信号分析结果
    """
    if len(williams_r) < 2:
        return {
            'signal': '中性',
            'reason': '数据不足',
            'current_wr': -50.0,
            'prev_wr': -50.0,
            'wr_trend': '平缓',
            'is_oversold': False,
            'is_overbought': False
        }
    
    current_wr = williams_r.iloc[-1]
    prev_wr = williams_r.iloc[-2]
    
    # 判断威廉指标趋势
    if current_wr > prev_wr:
        wr_trend = '上升'
    elif current_wr < prev_wr:
        wr_trend = '下降'
    else:
        wr_trend = '平缓'
    
    # 检测超买超卖（威廉指标与RSI相反）
    is_oversold = current_wr < -80  # 低于-80为超卖
    is_overbought = current_wr > -20  # 高于-20为超买
    
    # 生成信号
    signal = '中性'
    reason = ''
    
    if is_oversold and wr_trend == '上升':
        signal = '看涨'
        reason = f'威廉指标从超卖区({prev_wr:.1f})回升至{current_wr:.1f}'
    elif is_overbought and wr_trend == '下降':
        signal = '看跌'
        reason = f'威廉指标从超买区({prev_wr:.1f})回落至{current_wr:.1f}'
    elif is_oversold:
        signal = '看涨'
        reason = f'威廉指标处于超卖区({current_wr:.1f})'
    elif is_overbought:
        signal = '看跌'
        reason = f'威廉指标处于超买区({current_wr:.1f})'
    elif current_wr < -50 and wr_trend == '上升':
        signal = '看涨'
        reason = f'威廉指标在中轴下方({current_wr:.1f})且上升'
    elif current_wr > -50 and wr_trend == '下降':
        signal = '看跌'
        reason = f'威廉指标在中轴上方({current_wr:.1f})且下降'
    
    return {
        'signal': signal,
        'reason': reason,
        'current_wr': float(current_wr),
        'prev_wr': float(prev_wr),
        'wr_trend': wr_trend,
        'is_oversold': bool(is_oversold),
        'is_overbought': bool(is_overbought)
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
    
    # 确保数据按日期正序排列（从旧到新），这是技术指标计算所必需的
    prices_df = prices_df.sort_index(ascending=True)
    
    # 计算各项技术指标
    macd_data = calculate_macd(prices_df)
    rsi = calculate_rsi(prices_df)
    boll_data = calculate_bollinger_bands(prices_df)
    volume_analysis = calculate_volume_analysis(prices_df)
    roc = calculate_roc(prices_df)
    stoch_data = calculate_stochastic(prices_df)
    williams_r = calculate_williams_r(prices_df)
    
    # 分析各项信号
    macd_signals = analyze_macd_signals(macd_data)
    rsi_signals = analyze_rsi_signals(rsi)
    boll_signals = analyze_bollinger_signals(prices_df, boll_data)
    volume_signals = analyze_volume_signals(volume_analysis)
    roc_signals = analyze_roc_signals(roc)
    stoch_signals = analyze_stochastic_signals(stoch_data)
    williams_r_signals = analyze_williams_r_signals(williams_r)
    
    # 信号权重（调整为7个指标，总权重为1.0）
    weights = {
        'macd': 0.20,      # MACD权重降低
        'rsi': 0.15,       # RSI权重降低
        'boll': 0.15,      # 布林带权重降低
        'volume': 0.10,    # 成交量权重降低
        'roc': 0.15,       # ROC指标权重
        'stoch': 0.15,     # 随机指标权重
        'williams_r': 0.10 # 威廉指标权重
    }
    
    # 计算综合信号
    signals = [macd_signals, rsi_signals, boll_signals, volume_signals, roc_signals, stoch_signals, williams_r_signals]
    signal_names = ['macd', 'rsi', 'boll', 'volume', 'roc', 'stoch', 'williams_r']
    
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
            'volume': volume_signals,
            'roc': roc_signals,
            'stochastic': stoch_signals,
            'williams_r': williams_r_signals
        },
        'scores': {
            'bullish_score': round(bullish_score, 2),
            'bearish_score': round(bearish_score, 2)
        },
        'raw_data': {
            'macd_data': {
                'dif': macd_data['dif'].tolist(),  # 返回完整的DIF数据
                'dea': macd_data['dea'].tolist(),  # 返回完整的DEA数据
                'macd': macd_data['macd'].tolist()  # 返回完整的MACD数据
            },
            'rsi_data': rsi.tolist(),  # 返回完整的RSI数据
            'bollinger_data': {
                'upper': boll_data['upper'].tolist(),  # 返回完整的布林带上轨数据
                'middle': boll_data['middle'].tolist(),  # 返回完整的布林带中轨数据
                'lower': boll_data['lower'].tolist()  # 返回完整的布林带下轨数据
            },
            'volume_data': {
                'volume_ratio': volume_analysis['volume_ratio'].tolist()  # 返回完整的成交量比率数据
            },
            'roc_data': roc.tolist(),  # 返回完整的ROC数据
            'stochastic_data': {
                'k': stoch_data['k'].tolist(),  # 返回完整的K值数据
                'd': stoch_data['d'].tolist()   # 返回完整的D值数据
            },
            'williams_r_data': williams_r.tolist(),  # 返回完整的威廉指标数据
            'price_data': {
                'close': prices_df['close'].tolist(),  # 返回完整收盘价数据
                'high': prices_df['high'].tolist(),  # 返回完整最高价数据
                'low': prices_df['low'].tolist()  # 返回完整最低价数据
            }
        }
    }