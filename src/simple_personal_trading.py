#!/usr/bin/env python3
"""
简化版个性化交易系统
直接调用个人交易策略，避免复杂的多代理工作流
"""

import sys
import argparse
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from colorama import Fore, Style, init

# 添加src目录到Python路径
sys.path.append('/Users/bytedance/Documents/code/ai-hedge-fund/src')

from tools.api import get_prices, prices_to_df, get_financial_metrics
from utils.personal_indicators import generate_comprehensive_signal

init(autoreset=True)


def analyze_stock_simple(ticker: str, start_date: str, end_date: str):
    """
    简化版股票分析
    """
    print(f"\n📊 分析股票: {ticker}")
    
    # 获取扩展的历史数据用于技术分析
    extended_start = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=90)).strftime("%Y-%m-%d")
    
    print(f"⏳ 获取价格数据 ({extended_start} 到 {end_date})...")
    prices = get_prices(ticker, extended_start, end_date)
    
    if not prices:
        print(f"❌ 无法获取{ticker}的价格数据")
        return None
    
    # 转换为DataFrame
    prices_df = prices_to_df(prices)
    
    if len(prices_df) < 30:
        print(f"❌ {ticker}数据不足（仅{len(prices_df)}天），需要至少30天数据")
        return None
    
    print(f"✅ 成功获取{len(prices_df)}天的价格数据")
    print(f"📈 当前价格: ${prices_df['close'].iloc[-1]:.2f}")
    
    # 生成技术分析信号
    print(f"🔍 开始技术分析...")
    analysis_result = generate_comprehensive_signal(prices_df)
    
    # 获取基本财务信息
    print(f"💰 获取财务指标...")
    financial_metrics = get_financial_metrics(ticker, end_date)
    
    pe_ratio = None
    pb_ratio = None
    if financial_metrics:
        pe_ratio = financial_metrics[0].price_to_earnings_ratio
        pb_ratio = financial_metrics[0].price_to_book_ratio
    
    return {
        'ticker': ticker,
        'current_price': prices_df['close'].iloc[-1],
        'analysis': analysis_result,
        'financial_metrics': {
            'pe_ratio': pe_ratio,
            'pb_ratio': pb_ratio
        },
        'data_days': len(prices_df)
    }


def generate_trading_recommendation(analysis_result):
    """
    生成交易建议
    """
    if not analysis_result:
        return "数据不足，无法生成建议"
    
    signal = analysis_result['analysis']['signal']
    confidence = analysis_result['analysis']['confidence']
    reason = analysis_result['analysis']['reason']
    
    # 生成建议
    if signal == 'bullish' and confidence >= 60:
        recommendation = f"🟢 买入建议 (信心度: {confidence}%)"
        action = "考虑买入"
    elif signal == 'bearish' and confidence >= 60:
        recommendation = f"🔴 卖出建议 (信心度: {confidence}%)"
        action = "考虑卖出"
    else:
        recommendation = f"🟡 持有建议 (信心度: {confidence}%)"
        action = "继续观察"
    
    return {
        'recommendation': recommendation,
        'action': action,
        'reason': reason,
        'confidence': confidence
    }


def print_analysis_report(result):
    """
    打印分析报告
    """
    if not result:
        print("❌ 分析失败")
        return
    
    ticker = result['ticker']
    current_price = result['current_price']
    analysis = result['analysis']
    financial = result['financial_metrics']
    
    print(f"\n" + "="*60)
    print(f"📈 {ticker} 股票分析报告")
    print(f"="*60)
    
    print(f"💰 当前价格: ${current_price:.2f}")
    
    if financial['pe_ratio']:
        print(f"📊 P/E比率: {financial['pe_ratio']:.2f}")
    if financial['pb_ratio']:
        print(f"📊 P/B比率: {financial['pb_ratio']:.2f}")
    
    print(f"\n🎯 技术分析结果:")
    print(f"   总体信号: {analysis['signal'].upper()}")
    print(f"   信心度: {analysis['confidence']}%")
    print(f"   原因: {analysis['reason']}")
    
    # 详细指标分析
    details = analysis['details']
    print(f"\n📋 详细指标分析:")
    
    indicators = [
        ('MACD', details['macd']),
        ('RSI', details['rsi']),
        ('布林带', details['bollinger']),
        ('成交量', details['volume'])
    ]
    
    for name, data in indicators:
        signal_color = Fore.GREEN if data['signal'] == 'bullish' else Fore.RED if data['signal'] == 'bearish' else Fore.YELLOW
        print(f"   {name}: {signal_color}{data['signal']}{Style.RESET_ALL} - {data['reason']}")
    
    # 生成交易建议
    recommendation = generate_trading_recommendation(result)
    print(f"\n🎯 交易建议:")
    print(f"   {recommendation['recommendation']}")
    print(f"   行动: {recommendation['action']}")
    
    print(f"\n⚠️  风险提示:")
    print(f"   • 本分析仅供参考，不构成投资建议")
    print(f"   • 投资有风险，决策需谨慎")
    print(f"   • 建议结合基本面分析和市场环境")
    print(f"="*60)


def main():
    parser = argparse.ArgumentParser(description="简化版个性化交易分析系统")
    parser.add_argument("--tickers", type=str, required=True, help="股票代码，用逗号分隔")
    parser.add_argument("--start-date", type=str, help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="结束日期 (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    # 解析股票代码
    tickers = [ticker.strip().upper() for ticker in args.tickers.split(",")]
    
    # 设置日期范围
    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    start_date = args.start_date or (datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(months=1)).strftime("%Y-%m-%d")
    
    print(f"\n{Fore.CYAN}🎯 个性化交易分析系统 (简化版){Style.RESET_ALL}")
    print(f"📅 分析时间范围: {start_date} 到 {end_date}")
    print(f"📊 分析标的: {', '.join(tickers)}")
    print(f"💡 策略: MACD + RSI + 布林带 + 成交量")
    
    # 分析每只股票
    for ticker in tickers:
        try:
            result = analyze_stock_simple(ticker, start_date, end_date)
            print_analysis_report(result)
        except Exception as e:
            print(f"❌ 分析{ticker}时出错: {str(e)}")
        
        # 添加延迟避免API频率限制
        if len(tickers) > 1:
            import time
            time.sleep(2)
    
    print(f"\n✅ 分析完成！")


if __name__ == "__main__":
    main()