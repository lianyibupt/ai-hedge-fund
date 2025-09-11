#!/usr/bin/env python3
"""
测试Alpha Vantage MCP工具集成
验证MCP工具能否成功调用并获取真实股价数据
"""

import sys
import os
sys.path.insert(0, 'src')

def test_mcp_tools_direct():
    """直接测试MCP工具调用"""
    print("🧪 测试Alpha Vantage MCP工具直接调用...")
    
    # 测试股票代码
    test_symbols = ['AAPL', 'MSFT', 'RXRX', 'CRWV', 'SBET']
    
    for symbol in test_symbols:
        print(f"\n📊 测试 {symbol}...")
        
        # 1. 测试每日价格数据
        print(f"🔄 获取 {symbol} 每日价格数据...")
        try:
            # 直接调用当前环境中的MCP工具
            daily_result = mcp_alphavantage_TIME_SERIES_DAILY(
                symbol=symbol,
                outputsize="compact"
            )
            
            if daily_result:
                print(f"✅ {symbol} 每日价格数据获取成功")
                
                # 检查数据结构
                if isinstance(daily_result, list) and len(daily_result) > 0:
                    data = daily_result[0] if isinstance(daily_result[0], dict) else daily_result
                elif isinstance(daily_result, dict):
                    data = daily_result
                else:
                    data = {}
                
                if 'Time Series (Daily)' in data:
                    time_series = data['Time Series (Daily)']
                    dates = list(time_series.keys())
                    if dates:
                        latest_date = dates[0]
                        latest_data = time_series[latest_date]
                        print(f"   📅 最新日期: {latest_date}")
                        print(f"   💰 收盘价: ${latest_data.get('4. close', 'N/A')}")
                        print(f"   📈 开盘价: ${latest_data.get('1. open', 'N/A')}")
                else:
                    print(f"   ⚠️ 数据格式异常: {list(data.keys())}")
            else:
                print(f"❌ {symbol} 每日价格数据获取失败：返回空数据")
                
        except Exception as e:
            print(f"❌ {symbol} 每日价格数据获取失败: {str(e)}")
        
        # 2. 测试实时报价
        print(f"💰 获取 {symbol} 实时报价...")
        try:
            quote_result = mcp_alphavantage_GLOBAL_QUOTE(
                symbol=symbol
            )
            
            if quote_result:
                print(f"✅ {symbol} 实时报价获取成功")
                
                # 检查数据结构
                if isinstance(quote_result, list) and len(quote_result) > 0:
                    data = quote_result[0] if isinstance(quote_result[0], dict) else quote_result
                elif isinstance(quote_result, dict):
                    data = quote_result
                else:
                    data = {}
                
                if 'Global Quote' in data:
                    quote_data = data['Global Quote']
                    print(f"   💰 当前价格: ${quote_data.get('05. price', 'N/A')}")
                    print(f"   📊 涨跌: {quote_data.get('09. change', 'N/A')} ({quote_data.get('10. change percent', 'N/A')})")
                else:
                    print(f"   ⚠️ 报价数据格式异常: {list(data.keys())}")
            else:
                print(f"❌ {symbol} 实时报价获取失败：返回空数据")
                
        except Exception as e:
            print(f"❌ {symbol} 实时报价获取失败: {str(e)}")
        
        # 3. 测试公司概览（仅对几个主要股票）
        if symbol in ['AAPL', 'MSFT']:
            print(f"🏢 获取 {symbol} 公司概览...")
            try:
                overview_result = mcp_alphavantage_COMPANY_OVERVIEW(
                    symbol=symbol
                )
                
                if overview_result:
                    print(f"✅ {symbol} 公司概览获取成功")
                    
                    # 检查数据结构
                    if isinstance(overview_result, list) and len(overview_result) > 0:
                        data = overview_result[0] if isinstance(overview_result[0], dict) else overview_result
                    elif isinstance(overview_result, dict):
                        data = overview_result
                    else:
                        data = {}
                    
                    # 显示关键信息
                    if 'Symbol' in data:
                        print(f"   🏷️ 公司名称: {data.get('Name', 'N/A')}")
                        print(f"   💰 市值: {data.get('MarketCapitalization', 'N/A')}")
                        print(f"   📊 P/E比率: {data.get('PERatio', 'N/A')}")
                    else:
                        print(f"   ⚠️ 公司数据格式异常: {list(data.keys())}")
                else:
                    print(f"❌ {symbol} 公司概览获取失败：返回空数据")
                    
            except Exception as e:
                print(f"❌ {symbol} 公司概览获取失败: {str(e)}")
        
        print("-" * 50)


def test_wrapper_integration():
    """测试包装器集成"""
    print("\n🔧 测试Alpha Vantage MCP包装器集成...")
    
    try:
        from tools.alphavantage_mcp_wrapper import get_alphavantage_wrapper
        
        wrapper = get_alphavantage_wrapper()
        
        # 测试AAPL数据获取
        print("📊 测试AAPL价格数据获取...")
        prices = wrapper.get_daily_prices('AAPL', '2025-09-09', '2025-09-11')
        
        if prices:
            print(f"✅ 成功获取 {len(prices)} 条价格数据")
            for price in prices[:3]:  # 显示前3条数据
                print(f"   📈 {price.time}: 收盘价 ${price.close}, 开盘价 ${price.open}")
        else:
            print("❌ 未获取到价格数据")
        
        # 测试实时报价
        print("\n💰 测试AAPL实时报价...")
        quote = wrapper.get_real_time_quote('AAPL')
        
        if quote:
            print(f"✅ 成功获取实时报价")
            print(f"   💰 当前价格: ${quote.close} (日期: {quote.time})")
        else:
            print("❌ 未获取到实时报价")
            
    except Exception as e:
        print(f"❌ 包装器集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


def test_trading_app_integration():
    """测试交易应用集成"""
    print("\n🎯 测试交易应用集成...")
    
    try:
        from tools.api import get_prices
        
        # 测试统一API接口
        print("📊 通过统一接口获取AAPL价格数据...")
        prices = get_prices('AAPL', '2025-09-09', '2025-09-11', 'us')
        
        if prices:
            print(f"✅ 通过统一接口成功获取 {len(prices)} 条数据")
            print(f"   💰 最新价格: ${prices[0].close}")
        else:
            print("❌ 统一接口未获取到数据")
            
    except Exception as e:
        print(f"❌ 交易应用集成测试失败: {str(e)}")


if __name__ == "__main__":
    print("🚀 开始Alpha Vantage MCP工具集成测试")
    print("=" * 70)
    
    # 首先测试MCP工具直接调用
    try:
        test_mcp_tools_direct()
    except Exception as e:
        print(f"❌ MCP工具直接调用测试失败: {str(e)}")
    
    # 测试包装器集成
    try:
        test_wrapper_integration()
    except Exception as e:
        print(f"❌ 包装器集成测试失败: {str(e)}")
    
    # 测试交易应用集成
    try:
        test_trading_app_integration()
    except Exception as e:
        print(f"❌ 交易应用集成测试失败: {str(e)}")
    
    print("\n🎯 测试完成！")
    print("💡 如果所有测试通过，Alpha Vantage MCP工具已成功集成")
    print("🔄 现在可以运行 python run_personal_trading_app.py 获取真实股价数据")