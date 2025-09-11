#!/usr/bin/env python3
"""
实时MCP数据注入器
通过当前AI对话环境获取真实的Alpha Vantage数据，并注入到交易应用中
"""

def get_live_stock_data():
    """获取实时股票数据"""
    
    # 要测试的股票列表
    test_symbols = ['RXRX', 'CRWV', 'SBET', 'CRCL', 'NBIS']
    
    live_data = {}
    
    for symbol in test_symbols:
        print(f"\n📊 获取 {symbol} 的实时数据...")
        
        try:
            # 获取每日价格数据
            daily_result = mcp_alphavantage_TIME_SERIES_DAILY(
                symbol=symbol,
                outputsize="compact"
            )
            
            # 获取实时报价
            quote_result = mcp_alphavantage_GLOBAL_QUOTE(
                symbol=symbol
            )
            
            if daily_result and quote_result:
                live_data[symbol] = {
                    'daily_data': daily_result,
                    'quote_data': quote_result,
                    'timestamp': '2025-09-11'
                }
                
                # 解析报价信息
                if isinstance(quote_result, list) and len(quote_result) > 0:
                    quote_info = quote_result[0].get('Global Quote', {})
                elif isinstance(quote_result, dict):
                    quote_info = quote_result.get('Global Quote', {})
                else:
                    quote_info = {}
                
                current_price = quote_info.get('05. price', 'N/A')
                change = quote_info.get('09. change', 'N/A')
                change_percent = quote_info.get('10. change percent', 'N/A')
                
                print(f"✅ {symbol} 数据获取成功")
                print(f"   💰 当前价格: ${current_price}")
                print(f"   📊 涨跌: {change} ({change_percent})")
                
        except Exception as e:
            print(f"❌ {symbol} 数据获取失败: {str(e)}")
    
    return live_data


def inject_live_data_to_app(live_data):
    """将实时数据注入到应用中"""
    
    print(f"\n🔧 开始注入实时数据到交易应用...")
    
    # 这里我们可以将数据保存到文件或数据库
    # 让交易应用能够读取这些最新数据
    
    import json
    import os
    
    # 保存到临时文件
    data_file = '/Users/bytedance/Documents/code/ai-hedge-fund/live_mcp_data.json'
    
    try:
        with open(data_file, 'w') as f:
            json.dump(live_data, f, indent=2)
        
        print(f"✅ 实时数据已保存到: {data_file}")
        print(f"📊 包含 {len(live_data)} 只股票的数据")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据保存失败: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 开始获取实时MCP数据并注入到交易应用...")
    print("=" * 70)
    
    # 获取实时股票数据
    live_data = get_live_stock_data()
    
    if live_data:
        # 注入数据到应用
        success = inject_live_data_to_app(live_data)
        
        if success:
            print(f"\n🎯 数据注入完成！")
            print(f"💡 现在运行交易应用将使用最新的真实股价数据")
            print(f"🔄 运行: python run_personal_trading_app.py")
        else:
            print(f"\n❌ 数据注入失败")
    else:
        print(f"\n❌ 未获取到任何实时数据")