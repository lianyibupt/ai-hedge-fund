#!/usr/bin/env python3
"""
测试Alpha Vantage HTTP API集成
验证HTTP API能否成功调用并获取真实股价数据
"""

import sys
import os
sys.path.insert(0, 'src')

def test_alphavantage_http_api():
    """测试Alpha Vantage HTTP API"""
    print("🚀 开始测试Alpha Vantage HTTP API...")
    print("=" * 70)
    
    try:
        from tools.alphavantage_api import get_alphavantage_api
        
        api = get_alphavantage_api()
        
        # 测试API连接
        print("\n🔄 测试API连接...")
        if api.test_connection():
            print("✅ API连接测试成功")
        else:
            print("❌ API连接测试失败")
            return False
        
        # 测试获取RXRX的实时报价
        print(f"\n💰 测试获取RXRX实时报价...")
        quote_data = api.get_real_time_quote('RXRX')
        if quote_data:
            print(f"✅ 成功获取RXRX实时报价")
            
            # 显示报价信息
            if 'Global Quote' in quote_data:
                quote = quote_data['Global Quote']
                print(f"   💰 当前价格: ${quote.get('05. price', 'N/A')}")
                print(f"   📊 涨跌: {quote.get('09. change', 'N/A')} ({quote.get('10. change percent', 'N/A')})")
                print(f"   📅 最新交易日: {quote.get('07. latest trading day', 'N/A')}")
        else:
            print("❌ 获取RXRX实时报价失败")
        
        # 测试获取RXRX的历史数据
        print(f"\n📊 测试获取RXRX历史数据...")
        historical_data = api.get_historical_data('RXRX', '2025-09-09', '2025-09-11', 'daily')
        if historical_data:
            print(f"✅ 成功获取RXRX历史数据")
            
            # 显示历史数据
            if 'Time Series (Daily)' in historical_data:
                time_series = historical_data['Time Series (Daily)']
                dates = list(time_series.keys())[:3]  # 显示前3天
                print(f"   📈 共获取 {len(time_series)} 天的数据")
                for date in dates:
                    data = time_series[date]
                    print(f"   📅 {date}: 收盘 ${data.get('4. close', 'N/A')}, 开盘 ${data.get('1. open', 'N/A')}")
        else:
            print("❌ 获取RXRX历史数据失败")
        
        # 测试获取RXRX的公司概览
        print(f"\n🏢 测试获取RXRX公司概览...")
        overview_data = api.get_company_overview('RXRX')
        if overview_data:
            print(f"✅ 成功获取RXRX公司概览")
            
            # 显示公司信息
            if 'Symbol' in overview_data:
                print(f"   🏷️ 公司名称: {overview_data.get('Name', 'N/A')}")
                print(f"   💰 市值: {overview_data.get('MarketCapitalization', 'N/A')}")
                print(f"   📊 P/E比率: {overview_data.get('PERatio', 'N/A')}")
                print(f"   📈 52周高点: ${overview_data.get('52WeekHigh', 'N/A')}")
                print(f"   📉 52周低点: ${overview_data.get('52WeekLow', 'N/A')}")
        else:
            print("❌ 获取RXRX公司概览失败")
        
        return True
        
    except Exception as e:
        print(f"❌ Alpha Vantage HTTP API测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_wrapper_integration():
    """测试包装器集成"""
    print("\n🔧 测试Alpha Vantage HTTP包装器集成...")
    
    try:
        from tools.alphavantage_mcp_wrapper import get_alphavantage_wrapper
        
        wrapper = get_alphavantage_wrapper()
        
        # 测试RXRX数据获取
        print("📊 测试RXRX价格数据获取...")
        prices = wrapper.get_daily_prices('RXRX', '2025-09-09', '2025-09-11')
        
        if prices:
            print(f"✅ 成功获取 {len(prices)} 条价格数据")
            for price in prices[:3]:  # 显示前3条数据
                print(f"   📈 {price.time}: 收盘价 ${price.close}, 开盘价 ${price.open}")
        else:
            print("❌ 未获取到价格数据")
        
        # 测试实时报价
        print("\n💰 测试RXRX实时报价...")
        quote = wrapper.get_real_time_quote('RXRX')
        
        if quote:
            print(f"✅ 成功获取实时报价")
            print(f"   💰 当前价格: ${quote.close} (日期: {quote.time})")
        else:
            print("❌ 未获取到实时报价")
        
        # 测试公司概览
        print("\n🏢 测试RXRX公司概览...")
        metrics = wrapper.get_company_overview('RXRX')
        
        if metrics:
            print(f"✅ 成功获取公司概览 ({len(metrics)} 项指标)")
            metric = metrics[0]
            print(f"   📊 P/E比率: {metric.price_to_earnings_ratio}")
            print(f"   💰 市值: {metric.market_cap}")
        else:
            print("❌ 未获取到公司概览")
            
        return True
        
    except Exception as e:
        print(f"❌ 包装器集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_api():
    """测试统一API接口"""
    print("\n🎯 测试统一API接口集成...")
    
    try:
        from tools.api import get_prices
        
        # 测试统一API接口
        print("📊 通过统一接口获取RXRX价格数据...")
        prices = get_prices('RXRX', '2025-09-09', '2025-09-11', 'us')
        
        if prices:
            print(f"✅ 通过统一接口成功获取 {len(prices)} 条数据")
            print(f"   💰 最新价格: ${prices[0].close}")
            print(f"   📅 数据日期: {prices[0].time}")
        else:
            print("❌ 统一接口未获取到数据")
            
        return True
            
    except Exception as e:
        print(f"❌ 统一API测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 开始Alpha Vantage HTTP API集成测试")
    print("=" * 70)
    
    success_count = 0
    total_tests = 3
    
    # 1. 测试基础HTTP API
    if test_alphavantage_http_api():
        success_count += 1
    
    # 2. 测试包装器集成
    if test_wrapper_integration():
        success_count += 1
    
    # 3. 测试统一API集成
    if test_unified_api():
        success_count += 1
    
    print(f"\n🎯 测试完成！成功 {success_count}/{total_tests} 项测试")
    
    if success_count == total_tests:
        print("💡 所有测试通过，Alpha Vantage HTTP API已成功集成")
        print("🔄 现在可以运行 python run_personal_trading_app.py 获取真实股价数据")
    else:
        print("⚠️ 部分测试失败，请检查API配置和网络连接")