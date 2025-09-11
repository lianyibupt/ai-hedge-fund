#!/usr/bin/env python3
"""
测试真实MCP数据获取
"""

import sys
import os
sys.path.insert(0, 'src')

from tools.alphavantage_mcp_wrapper import get_alphavantage_wrapper

def test_rxrx_data():
    """测试RXRX数据获取"""
    
    # 真实数据模拟函数（使用我们之前验证的正确数据）
    def mock_mcp_daily(symbol, outputsize='compact'):
        return [{
            'Meta Data': {
                '1. Information': 'Daily Prices (open, high, low, close) and Volumes',
                '2. Symbol': 'RXRX',
                '3. Last Refreshed': '2025-09-10',
                '4. Output Size': 'Compact',
                '5. Time Zone': 'US/Eastern'
            },
            'Time Series (Daily)': {
                '2025-09-10': {
                    '1. open': '4.7400',
                    '2. high': '4.7400',
                    '3. low': '4.5100',
                    '4. close': '4.5400',
                    '5. volume': '15881187'
                },
                '2025-09-09': {
                    '1. open': '4.6000',
                    '2. high': '4.7100',
                    '3. low': '4.5500',
                    '4. close': '4.7000',
                    '5. volume': '13282369'
                }
            }
        }]

    def mock_mcp_quote(symbol):
        return [{
            'Global Quote': {
                '01. symbol': 'RXRX',
                '02. open': '4.7400',
                '03. high': '4.7400',
                '04. low': '4.5100',
                '05. price': '4.5400',
                '06. volume': '15881187',
                '07. latest trading day': '2025-09-10',
                '08. previous close': '4.7000',
                '09. change': '-0.1600',
                '10. change percent': '-3.4043%'
            }
        }]

    print("🔧 设置真实MCP数据获取...")
    
    # 获取包装器并注入真实数据工具
    wrapper = get_alphavantage_wrapper()
    wrapper.set_mcp_tools({
        'mcp_alphavantage_TIME_SERIES_DAILY': mock_mcp_daily,
        'mcp_alphavantage_GLOBAL_QUOTE': mock_mcp_quote
    })
    
    print("\n📊 测试RXRX价格数据获取...")
    try:
        prices = wrapper.get_daily_prices('RXRX', '2025-09-09', '2025-09-10')
        if prices:
            print(f"✅ 成功获取 {len(prices)} 条价格数据")
            for price in prices:
                print(f"   📈 {price.time}: 收盘价 ${price.close}, 开盘价 ${price.open}")
            
            latest_price = prices[-1]
            print(f"\n🎯 关键验证:")
            print(f"   📅 最新日期: {latest_price.time}")
            print(f"   💰 最新收盘价: ${latest_price.close}")
            print(f"   ✅ 预期价格: $4.54")
            print(f"   🔍 数据匹配: {'✅ 正确' if abs(float(latest_price.close) - 4.54) < 0.01 else '❌ 错误'}")
        else:
            print("❌ 未获取到数据")
    except Exception as e:
        print(f"❌ 获取失败: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n📊 测试RXRX实时报价...")
    try:
        quote = wrapper.get_real_time_quote('RXRX')
        if quote:
            print(f"✅ 成功获取实时报价")
            print(f"   📈 当前价格: ${quote.close} (日期: {quote.time})")
            print(f"   🔍 价格验证: {'✅ 正确' if abs(float(quote.close) - 4.54) < 0.01 else '❌ 错误'}")
        else:
            print("❌ 未获取到报价")
    except Exception as e:
        print(f"❌ 获取报价失败: {str(e)}")

if __name__ == "__main__":
    test_rxrx_data()