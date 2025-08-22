#!/usr/bin/env python3
"""
超级简化版个人交易分析工具
直接使用简化的yfinance API，避免所有复杂依赖
"""

import sys
import argparse
from datetime import datetime
from colorama import Fore, Style, init

# 添加工具路径
sys.path.append('/Users/bytedance/Documents/code/ai-hedge-fund/src/tools')

from simple_yfinance import (
    get_stock_data_simple, 
    get_stock_info_simple,
    generate_simple_trading_signal
)

init(autoreset=True)


def analyze_stock_ultra_simple(ticker: str, period: str = "3mo"):
    """
    超级简化版股票分析
    """
    print(f"\n{Fore.CYAN}📊 分析股票: {ticker}{Style.RESET_ALL}")
    print("-" * 40)
    
    # 获取股票数据
    price_data = get_stock_data_simple(ticker, period)
    if price_data.empty:
        print(f"❌ 无法获取 {ticker} 的价格数据")
        return None
    
    # 获取基本信息
    stock_info = get_stock_info_simple(ticker)
    
    # 生成交易信号
    signal_result = generate_simple_trading_signal(price_data, stock_info)
    
    return {
        'ticker': ticker,
        'price_data': price_data,
        'stock_info': stock_info,
        'signal': signal_result
    }


def print_analysis_result(result):
    """
    打印分析结果
    """
    if not result:
        print("❌ 分析失败")
        return
    
    ticker = result['ticker']
    price_data = result['price_data']
    stock_info = result['stock_info']
    signal = result['signal']
    
    # 基本信息
    print(f"\n{Fore.WHITE}{Style.BRIGHT}📈 {ticker} 分析报告{Style.RESET_ALL}")
    print("=" * 50)
    
    if stock_info:
        print(f"🏢 公司名称: {stock_info.get('name', 'N/A')}")
        print(f"🏭 行业板块: {stock_info.get('sector', 'N/A')}")
        if stock_info.get('current_price'):
            print(f"💰 当前价格: ${stock_info['current_price']:.2f}")
        if stock_info.get('pe_ratio'):
            print(f"📊 P/E比率: {stock_info['pe_ratio']:.2f}")
        if stock_info.get('pb_ratio'):
            print(f"📊 P/B比率: {stock_info['pb_ratio']:.2f}")
    
    # 价格信息
    if not price_data.empty:
        latest_price = price_data['close'].iloc[-1]
        price_change = price_data['close'].iloc[-1] - price_data['close'].iloc[-2]
        price_change_pct = (price_change / price_data['close'].iloc[-2]) * 100
        
        change_color = Fore.GREEN if price_change >= 0 else Fore.RED
        print(f"📈 最新价格: ${latest_price:.2f} ({change_color}{price_change:+.2f} / {price_change_pct:+.2f}%{Style.RESET_ALL})")
        print(f"📊 数据天数: {len(price_data)} 天")
    
    # 交易信号
    print(f"\n{Fore.WHITE}{Style.BRIGHT}🎯 交易信号分析{Style.RESET_ALL}")
    print("-" * 30)
    
    signal_type = signal['signal']
    confidence = signal['confidence']
    reason = signal['reason']
    
    # 信号颜色
    if signal_type == 'bullish':
        signal_color = Fore.GREEN
        signal_text = "看涨 📈"
        action_text = "建议考虑买入"
    elif signal_type == 'bearish':
        signal_color = Fore.RED
        signal_text = "看跌 📉"
        action_text = "建议考虑卖出"
    else:
        signal_color = Fore.YELLOW
        signal_text = "中性 ⚖️"
        action_text = "建议持有观望"
    
    print(f"🚦 交易信号: {signal_color}{signal_text}{Style.RESET_ALL}")
    print(f"🎯 信心度: {confidence}%")
    print(f"📝 原因: {reason}")
    print(f"💡 建议: {action_text}")
    
    # 详细技术指标
    if 'details' in signal and 'indicators' in signal['details']:
        indicators = signal['details']['indicators']
        print(f"\n{Fore.WHITE}{Style.BRIGHT}📋 技术指标详情{Style.RESET_ALL}")
        print("-" * 30)
        
        # MACD
        if 'macd' in indicators:
            macd = indicators['macd']
            macd_status = "看涨" if macd.get('is_bullish') else "看跌"
            print(f"📊 MACD: {macd_status} (DIF: {macd.get('line', 0):.4f})")
        
        # RSI
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            rsi_value = rsi.get('value', 50)
            if rsi.get('is_overbought'):
                rsi_status = "超买"
            elif rsi.get('is_oversold'):
                rsi_status = "超卖"
            else:
                rsi_status = "正常"
            print(f"📊 RSI: {rsi_value:.1f} ({rsi_status})")
        
        # 布林带
        if 'bollinger' in indicators:
            bb = indicators['bollinger']
            position = bb.get('position', 0.5) * 100
            print(f"📊 布林带位置: {position:.1f}% (0%=下轨, 100%=上轨)")
        
        # 成交量
        if 'volume' in indicators:
            vol = indicators['volume']
            vol_ratio = vol.get('current_ratio', 1.0)
            vol_status = "放量" if vol.get('is_high_volume') else "缩量"
            print(f"📊 成交量: {vol_ratio:.1f}倍平均值 ({vol_status})")
    
    # 风险提示
    print(f"\n{Fore.YELLOW}⚠️ 风险提示:{Style.RESET_ALL}")
    print("• 本分析仅供参考，不构成投资建议")
    print("• 投资有风险，入市需谨慎")
    print("• 请结合基本面和市场环境综合判断")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="超级简化版个人交易分析工具")
    parser.add_argument("--tickers", type=str, required=True, help="股票代码，用逗号分隔 (如: AAPL,MSFT)")
    parser.add_argument("--period", type=str, default="3mo", help="数据周期 (1mo, 3mo, 6mo, 1y)")
    
    args = parser.parse_args()
    
    # 解析股票代码
    tickers = [ticker.strip().upper() for ticker in args.tickers.split(",")]
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}🎯 个人交易分析系统{Style.RESET_ALL}")
    print(f"📊 分析标的: {', '.join(tickers)}")
    print(f"📅 数据周期: {args.period}")
    print(f"💡 基于: MACD + RSI + 布林带 + 成交量")
    
    # 分析每只股票
    for i, ticker in enumerate(tickers):
        try:
            result = analyze_stock_ultra_simple(ticker, args.period)
            print_analysis_result(result)
            
            # 多股票间添加分隔
            if i < len(tickers) - 1:
                print(f"\n{'='*60}")
                
        except Exception as e:
            print(f"❌ 分析 {ticker} 时出错: {str(e)}")
    
    print(f"\n{Fore.GREEN}✅ 分析完成！{Style.RESET_ALL}")


if __name__ == "__main__":
    main()