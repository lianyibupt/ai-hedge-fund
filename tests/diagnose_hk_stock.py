#!/usr/bin/env python3
"""
港股00700数据获取问题诊断脚本
"""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_api_key():
    """测试API密钥配置"""
    print("🔑 检查API密钥配置...")
    
    api_key = os.getenv("ITICK_API_KEY")
    
    if not api_key:
        print("❌ 未找到 ITICK_API_KEY 环境变量")
        return False
    elif api_key == "YOUR_FREE_KEY":
        print("❌ API密钥未正确配置（仍为默认值）")
        return False
    else:
        print(f"✅ API密钥已配置: {api_key[:10]}...{api_key[-4:]}")
        return True

def test_itick_api_direct():
    """直接测试iTick API"""
    print("\n🧪 直接测试 iTick API...")
    
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
        
        # 测试港股00700实时价格
        print("📊 测试港股00700实时价格...")
        real_time_data = itick_api.get_real_time_price("00700", region="hk")
        print(f"✅ 实时价格数据: {real_time_data}")
        
        # 测试港股00700历史数据
        print("📈 测试港股00700历史数据...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        kline_data = itick_api.get_historical_kline(
            ticker="00700",
            period="1d",
            start_time=str(int(start_date.timestamp())),
            end_time=str(int(end_date.timestamp())),
            region="hk"  # 指定港股市场
        )
        
        if kline_data:
            print(f"✅ 历史数据获取成功，获得 {len(kline_data)} 条数据")
            if kline_data:
                print(f"   示例数据: {kline_data[0]}")
                
                # 转换为Price对象
                prices = itick_api.convert_to_price_objects(kline_data, "00700")
                if prices:
                    print(f"✅ 数据转换成功，获得 {len(prices)} 个Price对象")
                    print(f"   最新价格: ${prices[-1].close:.2f}")
                    
                    # 检查日期范围
                    dates = [p.time for p in prices]
                    print(f"   日期范围: {min(dates)} 到 {max(dates)}")
                    return True
                else:
                    print("❌ 数据转换失败")
                    return False
        else:
            print("❌ 历史数据为空")
            return False
        
    except Exception as e:
        print(f"❌ iTick API 测试失败: {str(e)}")
        return False

def test_unified_api():
    """测试统一API接口"""
    print("\n🧪 测试统一API接口...")
    
    try:
        from tools.api import get_prices, _detect_ticker_region
        
        # 测试市场检测
        ticker = "00700"
        region = _detect_ticker_region(ticker)
        print(f"📍 市场检测结果: {ticker} -> {region}")
        
        # 测试价格数据获取
        print("📊 测试价格数据获取...")
        end_date = "2025-08-29"
        start_date = "2025-04-30"  # 使用问题报告中的日期范围
        
        print(f"   请求日期范围: {start_date} 到 {end_date}")
        print(f"   市场区域: {region}")
        
        prices = get_prices(ticker, start_date, end_date, region)
        
        if prices:
            print(f"✅ 统一接口价格数据获取成功，获得 {len(prices)} 条数据")
            print(f"   最新价格: ${prices[-1].close:.2f}")
            
            # 检查日期覆盖
            dates = [p.time for p in prices]
            print(f"   实际日期范围: {min(dates)} 到 {max(dates)}")
            
            # 检查指定日期范围内的数据
            in_range_prices = [p for p in prices if start_date <= p.time <= end_date]
            print(f"   指定范围内数据: {len(in_range_prices)} 条")
            
            return True
        else:
            print("❌ 统一接口价格数据获取失败")
            return False
        
    except Exception as e:
        print(f"❌ 统一API测试失败: {str(e)}")
        print(f"   错误详情: {type(e).__name__}: {str(e)}")
        return False

def test_cache_status():
    """检查缓存状态"""
    print("\n🗄️ 检查缓存状态...")
    
    try:
        from tools.api import get_cache_stats, clear_ticker_cache
        from data.cache import get_cache
        
        # 检查数据库缓存
        db_stats = get_cache_stats()
        if db_stats:
            print("📊 数据库缓存统计:")
            for key, value in db_stats.items():
                print(f"   {key}: {value}")
        
        # 检查内存缓存
        cache_instance = get_cache()
        memory_stats = cache_instance.get_cache_stats()
        if memory_stats:
            print("📊 内存缓存统计:")
            for key, value in memory_stats.items():
                print(f"   {key}: {value}")
        
        # 清理00700的缓存
        print("🗑️ 清理00700缓存...")
        cleared_count = clear_ticker_cache("00700")
        print(f"✅ 已清理 {cleared_count} 条缓存记录")
        
        return True
        
    except Exception as e:
        print(f"❌ 缓存检查失败: {str(e)}")
        return False

def test_date_range_issue():
    """测试特定日期范围问题"""
    print("\n📅 测试问题日期范围...")
    
    try:
        from tools.itick_api import date_to_timestamp
        
        # 测试日期转换
        start_date = "2025-04-30"
        end_date = "2025-08-29"
        
        start_ts = date_to_timestamp(start_date)
        end_ts = date_to_timestamp(end_date)
        
        print(f"📅 日期转换:")
        print(f"   开始日期: {start_date} -> {start_ts}")
        print(f"   结束日期: {end_date} -> {end_ts}")
        
        # 检查日期是否在未来
        now = datetime.now()
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        print(f"📊 日期分析:")
        print(f"   当前日期: {now.strftime('%Y-%m-%d')}")
        print(f"   开始日期: {start_date} ({'未来' if start_dt > now else '过去'})")
        print(f"   结束日期: {end_date} ({'未来' if end_dt > now else '过去'})")
        
        if end_dt > now:
            print("⚠️ 警告: 结束日期在未来，可能导致数据不可用")
            
            # 使用当前日期作为结束日期重新测试
            current_date = now.strftime("%Y-%m-%d")
            print(f"🔄 使用当前日期重新测试: {start_date} 到 {current_date}")
            
            from tools.api import get_prices
            prices = get_prices("00700", start_date, current_date, "hk")
            
            if prices:
                print(f"✅ 使用当前日期成功，获得 {len(prices)} 条数据")
                return True
            else:
                print("❌ 使用当前日期仍然失败")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 日期范围测试失败: {str(e)}")
        return False

def main():
    """主诊断流程"""
    print("🩺 港股00700数据获取问题诊断")
    print("=" * 50)
    
    # 测试步骤
    tests = [
        ("API密钥检查", test_api_key),
        ("日期范围问题", test_date_range_issue),
        ("缓存状态检查", test_cache_status),
        ("iTick API直接测试", test_itick_api_direct),
        ("统一API测试", test_unified_api),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ 通过" if result else "❌ 失败"
            print(f"结果: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"❌ 测试异常: {str(e)}")
    
    # 总结报告
    print(f"\n{'='*20} 诊断总结 {'='*20}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"测试通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    # 给出建议
    print(f"\n💡 问题诊断建议:")
    
    if not results.get("API密钥检查", False):
        print("1. 请确保在 .env 文件中正确配置 ITICK_API_KEY")
        
    if not results.get("日期范围问题", False):
        print("2. 请检查查询的日期范围，避免查询未来日期")
        
    if not results.get("iTick API直接测试", False):
        print("3. iTick API 连接有问题，请检查网络连接和API密钥")
        
    if not results.get("统一API测试", False):
        print("4. 统一API接口有问题，可能是市场参数传递错误")
    
    if all(results.values()):
        print("🎉 所有测试通过！如果仍有问题，可能是间歇性网络问题。")

if __name__ == "__main__":
    main()