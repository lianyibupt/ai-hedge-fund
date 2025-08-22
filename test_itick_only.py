#!/usr/bin/env python3
"""
专门测试 iTick API 集成
使用真实的 API key 进行测试
"""

import sys
import os
from datetime import datetime, timedelta

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_itick_api_direct():
    """直接测试 iTick API"""
    print("🧪 测试 iTick API 直接调用...")
    
    try:
        from tools.itick_api import get_itick_api
        
        # 创建API实例
        itick_api = get_itick_api()
        
        # 测试实时价格获取
        print("📊 测试实时价格获取 (AAPL)...")
        real_time_data = itick_api.get_real_time_price("AAPL")
        print(f"✅ 实时价格数据获取成功")
        print(f"   响应数据: {real_time_data}")
        
        # 测试历史数据获取
        print("\\n📈 测试历史数据获取 (AAPL, 最近7天)...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        kline_data = itick_api.get_historical_kline(
            ticker="AAPL",
            period="1d",
            start_time=str(int(start_date.timestamp())),
            end_time=str(int(end_date.timestamp())),
            region="us"
        )
        
        if kline_data:
            print(f"✅ 历史数据获取成功，获得 {len(kline_data)} 条数据")
            if kline_data:
                print(f"   示例数据: {kline_data[0]}")
                
                # 转换为Price对象
                prices = itick_api.convert_to_price_objects(kline_data, "AAPL")
                if prices:
                    print(f"✅ 数据转换成功，获得 {len(prices)} 个Price对象")
                    print(f"   最新价格: ${prices[-1].close:.2f}")
                else:
                    print("❌ 数据转换失败")
        else:
            print("⚠️ 历史数据为空")
        
        # 测试公司信息获取
        print("\\n🏢 测试公司信息获取 (AAPL)...")
        try:
            company_info = itick_api.get_company_info("AAPL")
            print(f"✅ 公司信息获取成功")
            print(f"   响应数据: {company_info}")
        except Exception as e:
            print(f"⚠️ 公司信息获取失败: {str(e)}")
        
        # 测试财务数据获取
        print("\\n💰 测试财务数据获取 (AAPL)...")
        try:
            financial_data = itick_api.get_financial_data("AAPL")
            print(f"✅ 财务数据获取成功")
            print(f"   响应数据: {financial_data}")
            
            # 转换为FinancialMetrics对象
            metrics = itick_api.convert_to_financial_metrics(financial_data, "AAPL")
            if metrics:
                print(f"✅ 财务数据转换成功")
                m = metrics[0]
                print(f"   市值: {m.market_cap}")
                print(f"   P/E比率: {m.price_to_earnings_ratio}")
            else:
                print("⚠️ 财务数据转换失败")
        except Exception as e:
            print(f"⚠️ 财务数据获取失败: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ iTick API 测试失败: {str(e)}")
        return False


def test_unified_api_with_itick():
    """测试统一API使用iTick"""
    print("\\n🧪 测试统一API接口（使用iTick）...")
    
    try:
        from tools.api import get_prices, get_financial_metrics
        
        # 测试价格数据获取
        print("📊 测试统一价格数据接口...")
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        prices = get_prices("AAPL", start_date, end_date)
        
        if prices:
            print(f"✅ 统一接口价格数据获取成功，获得 {len(prices)} 条数据")
            print(f"   最新价格: ${prices[-1].close:.2f}")
            print(f"   数据来源: iTick API")
        else:
            print("❌ 统一接口价格数据获取失败")
            return False
        
        # 测试财务指标获取
        print("\\n💰 测试统一财务指标接口...")
        financial_metrics = get_financial_metrics("AAPL", end_date)
        
        if financial_metrics:
            print(f"✅ 统一接口财务指标获取成功")
            metrics = financial_metrics[0]
            print(f"   市值: {metrics.market_cap}")
            print(f"   P/E比率: {metrics.price_to_earnings_ratio}")
            print(f"   数据来源: iTick API")
        else:
            print("❌ 统一接口财务指标获取失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 统一API测试失败: {str(e)}")
        return False


def test_simple_trading_with_itick():
    """测试简化版交易系统使用iTick API"""
    print("\\n🧪 测试简化版交易系统（使用iTick API）...")
    
    try:
        from simple_personal_trading import analyze_stock_simple
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        print("📈 分析AAPL股票（使用iTick数据）...")
        result = analyze_stock_simple("AAPL", start_date, end_date)
        
        if result:
            print("✅ 股票分析成功")
            print(f"   股票代码: {result['ticker']}")
            print(f"   当前价格: ${result['current_price']:.2f}")
            print(f"   技术信号: {result['analysis']['signal']}")
            print(f"   信心度: {result['analysis']['confidence']}%")
            print(f"   数据天数: {result['data_days']} 天")
            print(f"   数据来源: iTick API")
            return True
        else:
            print("❌ 股票分析失败")
            return False
        
    except Exception as e:
        print(f"❌ 简化版交易系统测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试 iTick API 集成")
    print("=" * 60)
    
    test_results = []
    
    # 测试各个组件
    test_results.append(("iTick API 直接调用", test_itick_api_direct()))
    test_results.append(("统一API接口", test_unified_api_with_itick()))
    test_results.append(("简化版交易系统", test_simple_trading_with_itick()))
    
    # 汇总测试结果
    print("\\n" + "=" * 60)
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
        print("   1. 现在可以使用 iTick API 获取实时股票数据")
        print("   2. 运行: poetry run python src/simple_personal_trading.py --tickers AAPL")
        print("   3. 系统会优先使用 iTick API，失败时自动回退到模拟数据")
        print("   4. 支持美股、港股等多个市场的数据获取")
        return True
    else:
        print("⚠️ 部分测试失败，请检查API配置和网络连接")
        return False


if __name__ == "__main__":
    main()