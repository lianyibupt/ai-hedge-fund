#!/usr/bin/env python3
"""
缓存机制测试脚本
验证新的按日期分类的缓存功能
"""

import sys
import os
from datetime import datetime, timedelta

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

def test_new_cache_mechanism():
    """测试新的缓存机制"""
    print("🧪 开始测试新缓存机制...")
    
    try:
        from data.cache import get_cache
        
        # 获取缓存实例
        cache = get_cache()
        print("✅ 成功获取缓存实例")
        
        # 测试数据
        test_ticker = "AAPL"
        test_dates = [
            "2024-08-26",
            "2024-08-27", 
            "2024-08-28"
        ]
        
        # 模拟价格数据
        test_price_data = []
        for i, date in enumerate(test_dates):
            price_data = {
                "time": date,
                "open": 100.0 + i,
                "high": 102.0 + i,
                "low": 99.0 + i,
                "close": 101.0 + i,
                "volume": 1000000 + i * 10000
            }
            test_price_data.append(price_data)
        
        print(f"📦 准备测试数据: {len(test_price_data)} 条价格记录")
        
        # 测试存储价格数据
        cache.set_prices(test_ticker, test_price_data)
        print(f"✅ 成功存储 {test_ticker} 的价格数据")
        
        # 测试按日期范围查询
        cached_data = cache.get_prices(test_ticker, "2024-08-26", "2024-08-28")
        if cached_data:
            print(f"✅ 成功获取缓存数据: {len(cached_data)} 条记录")
            for data in cached_data:
                print(f"   - {data['time']}: 收盘价 ${data['close']}")
        else:
            print("❌ 未能获取缓存数据")
            return False
        
        # 测试部分日期范围查询
        partial_data = cache.get_prices(test_ticker, "2024-08-27", "2024-08-28")
        if partial_data:
            print(f"✅ 部分日期范围查询成功: {len(partial_data)} 条记录")
        else:
            print("❌ 部分日期范围查询失败")
            return False
        
        # 测试缓存统计
        stats = cache.get_cache_stats()
        print(f"📊 缓存统计:")
        print(f"   - 总股票数: {stats['cache_summary']['total_tickers']}")
        print(f"   - 总缓存条目: {stats['cache_summary']['total_cache_entries']}")
        print(f"   - 新鲜条目: {stats['cache_summary']['fresh_entries']}")
        print(f"   - 价格缓存股票数: {stats['price_cache']['tickers_count']}")
        print(f"   - 价格缓存日期条目数: {stats['price_cache']['total_date_entries']}")
        
        # 测试财务数据缓存
        test_financial_data = [{
            "ticker": test_ticker,
            "report_period": "2024-06-30",
            "period": "ttm",
            "currency": "USD",
            "market_cap": 3000000000000,
            "price_to_earnings_ratio": 25.5,
            "price_to_book_ratio": 5.2
        }]
        
        cache.set_financial_metrics(test_ticker, test_financial_data)
        print(f"✅ 成功存储 {test_ticker} 的财务数据")
        
        financial_cached = cache.get_financial_metrics(test_ticker, "2024-08-28")
        if financial_cached:
            print(f"✅ 成功获取财务缓存数据: {len(financial_cached)} 条记录")
        else:
            print("❌ 未能获取财务缓存数据")
        
        # 测试清理特定股票缓存
        cache.clear_ticker_cache(test_ticker)
        print(f"🧹 清理了 {test_ticker} 的所有缓存")
        
        # 验证清理结果
        after_clear = cache.get_prices(test_ticker, "2024-08-26", "2024-08-28")
        if not after_clear:
            print("✅ 缓存清理验证成功")
        else:
            print("❌ 缓存清理验证失败")
            return False
        
        print("🎉 所有缓存机制测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_new_cache_mechanism()
    if success:
        print("\n✅ 新缓存机制工作正常")
    else:
        print("\n❌ 新缓存机制存在问题")
        sys.exit(1)