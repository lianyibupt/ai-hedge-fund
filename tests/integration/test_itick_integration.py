#!/usr/bin/env python3
"""
测试iTick API集成
验证数据获取功能是否正常工作
"""

import sys
import os
from datetime import datetime, timedelta

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_itick_api():
    """测试iTick API直接调用"""
    print("🧪 测试 iTick API 直接调用...")
    
    try:
        from tools.itick_api import get_itick_api
        
        # 创建API实例
        itick_api = get_itick_api()
        
        # 测试连接
        print("📡 测试API连接...")
        if itick_api.test_connection():
            print("✅ iTick API 连接成功")
        else:
            print("❌ iTick API 连接失败")
            return False
        
        # 测试实时价格获取
        print("📊 测试实时价格获取...")
        real_time_data = itick_api.get_real_time_price("AAPL")
        print(f"✅ 实时价格数据: {real_time_data}")
        
        # 测试历史数据获取
        print("📈 测试历史数据获取...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        kline_data = itick_api.get_historical_kline(
            ticker="AAPL",
            period="1d",
            start_time=str(int(start_date.timestamp())),
            end_time=str(int(end_date.timestamp())),
            region="us"
        )
        
        if kline_data:
            print(f"✅ 历史数据获取成功，获得 {len(kline_data)} 条数据")
            print(f"   示例数据: {kline_data[0] if kline_data else 'None'}")
        else:
            print("⚠️ 历史数据为空")
        
        return True
        
    except Exception as e:
        print(f"❌ iTick API 测试失败: {str(e)}")
        return False


def test_unified_api():
    """测试统一API接口"""
    print("\\n🧪 测试统一API接口...")
    
    try:
        from tools.api import get_prices, get_financial_metrics
        
        # 测试价格数据获取
        print("📊 测试价格数据获取...")
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        prices = get_prices("AAPL", start_date, end_date)
        
        if prices:
            print(f"✅ 价格数据获取成功，获得 {len(prices)} 条数据")
            print(f"   最新价格: {prices[-1].close if prices else 'N/A'}")
        else:
            print("⚠️ 价格数据为空")
        
        # 测试财务指标获取
        print("💰 测试财务指标获取...")
        financial_metrics = get_financial_metrics("AAPL", end_date)
        
        if financial_metrics:
            print(f"✅ 财务指标获取成功")
            metrics = financial_metrics[0]
            print(f"   市值: {metrics.market_cap}")
            print(f"   P/E比率: {metrics.price_to_earnings_ratio}")
        else:
            print("⚠️ 财务指标为空")
        
        return True
        
    except Exception as e:
        print(f"❌ 统一API测试失败: {str(e)}")
        return False


def test_personal_trading():
    """测试个人交易系统集成"""
    print("\\n🧪 测试个人交易系统集成...")
    
    try:
        # 测试简化版个人交易分析
        print("📈 测试简化版个人交易分析...")
        
        # 这里只做导入测试，避免实际运行分析
        from simple_personal_trading import analyze_stock_simple
        print("✅ 简化版个人交易系统导入成功")
        
        # 测试personal_trader代理
        print("🤖 测试个人交易代理...")
        from agents.personal_trader import personal_trader_agent
        print("✅ 个人交易代理导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 个人交易系统测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试 iTick API 集成")
    print("=" * 50)
    
    test_results = []
    
    # 测试各个组件
    test_results.append(("iTick API 直接调用", test_itick_api()))
    test_results.append(("统一API接口", test_unified_api()))
    test_results.append(("个人交易系统集成", test_personal_trading()))
    
    # 汇总测试结果
    print("\\n" + "=" * 50)
    print("📋 测试结果汇总:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\\n🎯 总体结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！iTick API 集成成功！")
        print("\\n💡 使用建议:")
        print("   1. 设置环境变量 ITICK_API_KEY 为您的 iTick API 密钥")
        print("   2. 运行: python src/simple_personal_trading.py --tickers AAPL")
        print("   3. 查看智能回退机制的工作情况")
        return True
    else:
        print("⚠️ 部分测试失败，请检查配置和API连接")
        return False


if __name__ == "__main__":
    main()