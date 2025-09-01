#!/usr/bin/env python3
"""
演示版个人交易分析工具
使用模拟数据展示功能，避免API频率限制
"""

import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from colorama import Fore, Style, init

init(autoreset=True)


def generate_mock_stock_data(ticker: str, days: int = 60) -> pd.DataFrame:
    """
    生成模拟股票数据用于演示
    """
    print(f"📊 生成 {ticker} 的模拟数据 ({days}天)...")
    
    # 设置种子确保可重复
    np.random.seed(hash(ticker) % 2**32)
    
    # 基础价格
    base_prices = {
        'AAPL': 180.0,
        'MSFT': 410.0,
        'GOOGL': 170.0,
        'NVDA': 880.0,
        'TSLA': 250.0
    }
    
    base_price = base_prices.get(ticker, 100.0)
    
    # 生成日期
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=days, freq='D')
    
    # 生成价格走势
    returns = np.random.normal(0.001, 0.025, days)  # 日收益率
    prices = [base_price]
    
    for i in range(1, days):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(new_price)
    
    # 生成OHLCV数据
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # 生成开盘、最高、最低价
        volatility = abs(np.random.normal(0, 0.02))
        high = close * (1 + volatility)
        low = close * (1 - volatility)
        open_price = close * (1 + np.random.normal(0, 0.01))
        
        # 确保价格逻辑正确
        high = max(high, close, open_price)
        low = min(low, close, open_price)
        
        # 生成成交量
        volume = int(np.random.normal(50000000, 15000000))
        volume = max(volume, 1000000)  # 最小100万
        
        data.append({
            'date': date,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('date', inplace=True)
    
    print(f"✅ 成功生成 {ticker} 的 {len(df)} 天模拟数据")
    return df


def calculate_technical_indicators(df: pd.DataFrame) -> dict:
    """
    计算技术指标
    """
    if df.empty or len(df) < 26:
        return {}
    
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    
    # MACD计算
    exp1 = close.ewm(span=12).mean()
    exp2 = close.ewm(span=26).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9).mean()
    
    # RSI计算
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # 布林带计算
    bb_middle = close.rolling(window=20).mean()
    bb_std = close.rolling(window=20).std()
    bb_upper = bb_middle + (bb_std * 2)
    bb_lower = bb_middle - (bb_std * 2)
    
    # 成交量分析
    volume_ma = volume.rolling(window=5).mean()
    volume_ratio = volume / volume_ma
    
    return {
        'macd': {
            'line': macd_line.iloc[-1],
            'signal': signal_line.iloc[-1],
            'is_bullish': macd_line.iloc[-1] > signal_line.iloc[-1]
        },
        'rsi': {
            'value': rsi.iloc[-1],
            'is_oversold': rsi.iloc[-1] < 30,
            'is_overbought': rsi.iloc[-1] > 70
        },
        'bollinger': {
            'upper': bb_upper.iloc[-1],
            'middle': bb_middle.iloc[-1],
            'lower': bb_lower.iloc[-1],
            'current_price': close.iloc[-1],
            'position': (close.iloc[-1] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
        },
        'volume': {
            'ratio': volume_ratio.iloc[-1],
            'is_high': volume_ratio.iloc[-1] > 1.5
        }
    }


def generate_trading_signal(df: pd.DataFrame, ticker: str) -> dict:
    """
    生成交易信号
    """
    indicators = calculate_technical_indicators(df)
    if not indicators:
        return {'signal': 'neutral', 'confidence': 0, 'reason': '数据不足'}
    
    signals = []
    bullish_score = 0
    bearish_score = 0
    
    # MACD分析
    macd = indicators['macd']
    if macd['is_bullish']:
        if macd['line'] > 0:
            bullish_score += 1
            signals.append('MACD在0轴上方金叉')
        else:
            bullish_score += 0.8
            signals.append('MACD在0轴下方金叉')
    else:
        bearish_score += 0.8
        signals.append('MACD死叉')
    
    # RSI分析
    rsi = indicators['rsi']
    if rsi['is_oversold']:
        bullish_score += 1
        signals.append('RSI超卖回升')
    elif rsi['is_overbought']:
        bearish_score += 1
        signals.append('RSI超买')
    elif 40 < rsi['value'] < 60:
        bullish_score += 0.5
        signals.append('RSI中性偏多')
    
    # 布林带分析
    bb = indicators['bollinger']
    if bb['position'] < 0.2:
        bullish_score += 1
        signals.append('接近布林下轨')
    elif bb['position'] > 0.8:
        bearish_score += 1
        signals.append('接近布林上轨')
    
    # 成交量分析
    volume = indicators['volume']
    if volume['is_high']:
        if bullish_score > bearish_score:
            bullish_score += 0.5
            signals.append('放量上涨')
        else:
            bearish_score += 0.5
            signals.append('放量下跌')
    
    # 计算最终信号
    total_score = bullish_score + bearish_score
    if bullish_score > bearish_score and bullish_score >= 2:
        signal = 'bullish'
        confidence = min(int((bullish_score / max(total_score, 1)) * 100), 95)
    elif bearish_score > bullish_score and bearish_score >= 1.5:
        signal = 'bearish'
        confidence = min(int((bearish_score / max(total_score, 1)) * 100), 95)
    else:
        signal = 'neutral'
        confidence = 50
    
    return {
        'signal': signal,
        'confidence': confidence,
        'reason': '; '.join(signals),
        'indicators': indicators,
        'scores': {'bullish': bullish_score, 'bearish': bearish_score}
    }


def print_analysis_report(ticker: str, df: pd.DataFrame, signal_result: dict):
    """
    打印分析报告
    """
    print(f"\n{Fore.CYAN}{Style.BRIGHT}📈 {ticker} 技术分析报告{Style.RESET_ALL}")
    print("=" * 60)
    
    # 基本价格信息
    latest_price = df['close'].iloc[-1]
    prev_price = df['close'].iloc[-2]
    change = latest_price - prev_price
    change_pct = (change / prev_price) * 100
    
    change_color = Fore.GREEN if change >= 0 else Fore.RED
    print(f"💰 当前价格: ${latest_price:.2f}")
    print(f"📊 日涨跌: {change_color}{change:+.2f} ({change_pct:+.2f}%){Style.RESET_ALL}")
    print(f"📅 分析周期: {len(df)} 天")
    
    # 交易信号
    signal = signal_result['signal']
    confidence = signal_result['confidence']
    reason = signal_result['reason']
    
    print(f"\n{Fore.WHITE}{Style.BRIGHT}🎯 交易信号{Style.RESET_ALL}")
    print("-" * 30)
    
    if signal == 'bullish':
        signal_color = Fore.GREEN
        signal_text = "看涨 📈"
        action = "建议买入"
    elif signal == 'bearish':
        signal_color = Fore.RED
        signal_text = "看跌 📉"
        action = "建议卖出"
    else:
        signal_color = Fore.YELLOW
        signal_text = "中性 ⚖️"
        action = "建议观望"
    
    print(f"🚦 信号: {signal_color}{signal_text}{Style.RESET_ALL}")
    print(f"🎯 信心度: {confidence}%")
    print(f"💡 建议: {action}")
    print(f"📝 依据: {reason}")
    
    # 技术指标详情
    indicators = signal_result['indicators']
    print(f"\n{Fore.WHITE}{Style.BRIGHT}📋 技术指标详情{Style.RESET_ALL}")
    print("-" * 30)
    
    # MACD
    macd = indicators['macd']
    macd_status = "多头" if macd['is_bullish'] else "空头"
    print(f"📊 MACD: {macd_status} (DIF: {macd['line']:.4f}, DEA: {macd['signal']:.4f})")
    
    # RSI
    rsi = indicators['rsi']
    rsi_value = rsi['value']
    if rsi['is_overbought']:
        rsi_status = "超买"
    elif rsi['is_oversold']:
        rsi_status = "超卖"
    else:
        rsi_status = "正常"
    print(f"📊 RSI: {rsi_value:.1f} ({rsi_status})")
    
    # 布林带
    bb = indicators['bollinger']
    bb_position = bb['position'] * 100
    print(f"📊 布林带: {bb_position:.1f}% (上轨: {bb['upper']:.2f}, 下轨: {bb['lower']:.2f})")
    
    # 成交量
    volume = indicators['volume']
    vol_status = "放量" if volume['is_high'] else "正常"
    print(f"📊 成交量: {volume['ratio']:.1f}倍均值 ({vol_status})")
    
    # 基于您的交易策略的具体建议
    print(f"\n{Fore.WHITE}{Style.BRIGHT}💡 基于您的交易策略{Style.RESET_ALL}")
    print("-" * 30)
    
    strategy_advice = []
    
    # 买入策略分析
    if signal == 'bullish':
        buy_conditions = 0
        if macd['is_bullish']:
            buy_conditions += 1
            strategy_advice.append("✓ MACD金叉确认")
        if rsi['is_oversold'] or (40 < rsi['value'] < 70):
            buy_conditions += 1
            strategy_advice.append("✓ RSI位置合适")
        if bb['position'] < 0.3:
            buy_conditions += 1
            strategy_advice.append("✓ 接近布林下轨")
        if volume['is_high']:
            buy_conditions += 1
            strategy_advice.append("✓ 成交量放大")
        
        print(f"🟢 满足买入条件: {buy_conditions}/4")
        
    # 卖出策略分析
    elif signal == 'bearish':
        sell_conditions = 0
        if not macd['is_bullish']:
            sell_conditions += 1
            strategy_advice.append("✓ MACD死叉")
        if rsi['is_overbought']:
            sell_conditions += 1
            strategy_advice.append("✓ RSI超买")
        if bb['position'] > 0.8:
            sell_conditions += 1
            strategy_advice.append("✓ 触及布林上轨")
        
        print(f"🔴 满足卖出条件: {sell_conditions}/3")
    
    for advice in strategy_advice:
        print(f"  {advice}")
    
    print(f"\n{Fore.YELLOW}⚠️ 风险提示:{Style.RESET_ALL}")
    print("• 本分析基于模拟数据，仅供学习参考")
    print("• 实际交易请使用真实数据和专业分析")
    print("• 投资有风险，决策需谨慎")
    print("• 建议持仓周期：2-3周")
    print("• 建议频率限制：2周内不超过10次交易")


def main():
    parser = argparse.ArgumentParser(description="演示版个人交易分析工具")
    parser.add_argument("--tickers", type=str, required=True, help="股票代码，用逗号分隔")
    parser.add_argument("--days", type=int, default=60, help="模拟数据天数")
    
    args = parser.parse_args()
    
    tickers = [ticker.strip().upper() for ticker in args.tickers.split(",")]
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}🎯 个人交易分析系统 (演示版){Style.RESET_ALL}")
    print(f"📊 分析标的: {', '.join(tickers)}")
    print(f"📅 数据周期: {args.days} 天 (模拟数据)")
    print(f"💡 策略: MACD + RSI + 布林带 + 成交量")
    print(f"⏰ 交易周期: 2-3周")
    print(f"🔄 频率限制: 2周内不超过10次")
    
    for i, ticker in enumerate(tickers):
        try:
            # 生成模拟数据
            df = generate_mock_stock_data(ticker, args.days)
            
            # 生成交易信号
            signal_result = generate_trading_signal(df, ticker)
            
            # 打印分析报告
            print_analysis_report(ticker, df, signal_result)
            
            if i < len(tickers) - 1:
                print(f"\n{'='*70}")
                
        except Exception as e:
            print(f"❌ 分析 {ticker} 时出错: {str(e)}")
    
    print(f"\n{Fore.GREEN}✅ 演示分析完成！{Style.RESET_ALL}")
    print(f"{Fore.CYAN}💡 这是使用模拟数据的演示版本，实际使用时会连接真实的Yahoo Finance API{Style.RESET_ALL}")


if __name__ == "__main__":
    main()