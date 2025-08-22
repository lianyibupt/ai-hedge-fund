#!/usr/bin/env python3
"""
测试模拟数据功能
验证当API不可用时的回退机制
"""

import sys
import os
from datetime import datetime, timedelta

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_mock_data():
    """测试模拟数据生成"""
    print("🧪 测试模拟数据生成...")
    
    try:
        from tools.api_fallback import MockDataGenerator
        
        mock_generator = MockDataGenerator()
        
        # 测试模拟价格数据
        print("📊 测试模拟价格数据生成...")
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        mock_prices = mock_generator.generate_mock_prices("AAPL", start_date, end_date)
        
        if mock_prices:
            print(f"✅ 模拟价格数据生成成功，获得 {len(mock_prices)} 条数据")
            print(f"   最新价格: ${mock_prices[-1].close:.2f}")
            print(f"   价格范围: ${min(p.close for p in mock_prices):.2f} - ${max(p.close for p in mock_prices):.2f}")
        else:
            print("❌ 模拟价格数据生成失败")
            return False
        
        # 测试模拟财务指标
        print("💰 测试模拟财务指标生成...")
        mock_financial = mock_generator.generate_mock_financial_metrics("AAPL", end_date)
        
        if mock_financial:
            print(f"✅ 模拟财务指标生成成功")
            metrics = mock_financial[0]
            print(f"   市值: ${metrics.market_cap:,.0f}")
            print(f"   P/E比率: {metrics.price_to_earnings_ratio:.2f}")
            print(f"   净利率: {metrics.net_margin:.2%}")
        else:
            print("❌ 模拟财务指标生成失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 模拟数据测试失败: {str(e)}")
        return False


def test_fallback_mechanism():
    """测试回退机制"""
    print("\\n🧪 测试API回退机制...")
    
    try:
        from tools.api import get_prices, get_financial_metrics
        
        # 设置无效的API密钥，强制使用回退机制
        os.environ["ITICK_API_KEY"] = "invalid_key"
        
        print("📊 测试价格数据回退...")
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        prices = get_prices("AAPL", start_date, end_date)
        
        if prices:
            print(f"✅ 回退机制成功，获得 {len(prices)} 条价格数据")
            print(f"   数据来源: 模拟数据")
        else:
            print("❌ 回退机制失败")
            return False
        
        print("💰 测试财务指标回退...")
        financial_metrics = get_financial_metrics("AAPL", end_date)
        
        if financial_metrics:
            print(f"✅ 回退机制成功，获得财务指标数据")
            print(f"   数据来源: 模拟数据")
        else:
            print("❌ 回退机制失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 回退机制测试失败: {str(e)}")
        return False


def test_simple_trading_with_mock():
    """测试简化版交易系统使用模拟数据"""
    print("\\n🧪 测试简化版交易系统（模拟数据）...")
    
    try:
        from simple_personal_trading import analyze_stock_simple
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        print("📈 分析AAPL股票...")
        result = analyze_stock_simple("AAPL", start_date, end_date)
        
        if result:
            print("✅ 股票分析成功")
            print(f"   股票代码: {result['ticker']}")
            print(f"   当前价格: ${result['current_price']:.2f}")
            print(f"   技术信号: {result['analysis']['signal']}")
            print(f"   信心度: {result['analysis']['confidence']}%")
            print(f"   数据天数: {result['data_days']} 天")
            return True
        else:
            print("❌ 股票分析失败")
            return False
        
    except Exception as e:
        print(f"❌ 简化版交易系统测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试模拟数据和回退机制")
    print("=" * 50)
    
    test_results = []
    
    # 测试各个组件
    test_results.append(("模拟数据生成", test_mock_data()))
    test_results.append(("API回退机制", test_fallback_mechanism()))
    test_results.append(("简化版交易系统", test_simple_trading_with_mock()))
    
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
        print("🎉 所有测试通过！模拟数据和回退机制工作正常！")
        print("\\n💡 使用建议:")
        print("   1. 当无法访问真实API时，系统会自动使用模拟数据")
        print("   2. 模拟数据包含合理的价格走势和财务指标")
        print("   3. 可以用于演示和测试交易策略")
        return True
    else:
        print("⚠️ 部分测试失败，请检查代码和依赖")
        return False


if __name__ == "__main__":
    main()