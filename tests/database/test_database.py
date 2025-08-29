#!/usr/bin/env python3
"""
测试SQLite数据库功能
验证查询记录、API缓存和技术分析结果存储
"""

import sys
import os
from datetime import datetime, timedelta

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

from data.database import get_database_manager
from tools.api import get_prices, get_financial_metrics, cleanup_cache, get_cache_stats

def test_database_initialization():
    """测试数据库初始化"""
    print("🔧 测试数据库初始化...")
    try:
        db_manager = get_database_manager()
        print("✅ 数据库初始化成功")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        return False

def test_query_record():
    """测试查询记录功能"""
    print("\n📝 测试查询记录功能...")
    try:
        db_manager = get_database_manager()
        
        # 保存测试查询记录
        tickers = ["AAPL", "MSFT"]
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        analysis_params = {"test": True, "detailed": False}
        
        record_id = db_manager.save_query_record(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            analysis_params=analysis_params,
            session_id="test_session_123",
            user_ip="127.0.0.1"
        )
        
        print(f"✅ 查询记录保存成功，ID: {record_id}")
        
        # 获取查询历史
        history_df = db_manager.get_query_history(limit=5)
        print(f"✅ 获取查询历史成功，共 {len(history_df)} 条记录")
        
        return True
    except Exception as e:
        print(f"❌ 查询记录测试失败: {str(e)}")
        return False

def test_analysis_result():
    """测试分析结果保存"""
    print("\n📊 测试分析结果保存...")
    try:
        db_manager = get_database_manager()
        
        # 创建模拟分析结果
        test_result = {
            'ticker': 'AAPL',
            'current_price': 150.25,
            'analysis': {
                'signal': '看涨',
                'confidence': 75,
                'reason': '技术指标显示多头趋势',
                'details': {
                    'macd': {'signal': '看涨', 'reason': 'MACD金叉'},
                    'rsi': {'signal': '中性', 'reason': 'RSI在正常范围'},
                    'bollinger': {'signal': '看涨', 'reason': '价格突破上轨'},
                    'volume': {'signal': '看涨', 'reason': '成交量放大'}
                }
            },
            'financial_metrics': {
                'pe_ratio': 25.5,
                'pb_ratio': 6.2
            },
            'data_days': 30
        }
        
        # 保存分析结果
        db_manager.save_analysis_result(1, test_result)  # 使用测试查询记录ID
        print("✅ 分析结果保存成功")
        
        # 获取分析历史
        analysis_df = db_manager.get_analysis_history(ticker='AAPL', limit=5)
        print(f"✅ 获取分析历史成功，共 {len(analysis_df)} 条记录")
        
        return True
    except Exception as e:
        print(f"❌ 分析结果测试失败: {str(e)}")
        return False

def test_price_cache():
    """测试价格数据缓存"""
    print("\n💾 测试价格数据缓存...")
    try:
        db_manager = get_database_manager()
        
        # 创建模拟价格数据
        test_price_data = [
            {
                'time': '2024-01-01',
                'open': 150.0,
                'high': 155.0,
                'low': 149.0,
                'close': 152.0,
                'volume': 1000000
            },
            {
                'time': '2024-01-02',
                'open': 152.0,
                'high': 158.0,
                'low': 151.0,
                'close': 156.0,
                'volume': 1200000
            }
        ]
        
        # 缓存价格数据
        db_manager.cache_price_data('AAPL', test_price_data, cache_hours=1)
        print("✅ 价格数据缓存成功")
        
        # 从缓存获取数据
        cached_data = db_manager.get_cached_price_data('AAPL', '2024-01-01', '2024-01-02')
        print(f"✅ 从缓存获取价格数据成功，共 {len(cached_data)} 条记录")
        
        return True
    except Exception as e:
        print(f"❌ 价格缓存测试失败: {str(e)}")
        return False

def test_financial_cache():
    """测试财务数据缓存"""
    print("\n💰 测试财务数据缓存...")
    try:
        db_manager = get_database_manager()
        
        # 创建模拟财务数据
        test_financial_data = [
            {
                'ticker': 'AAPL',
                'report_period': '2024-01-01',
                'period': 'ttm',
                'currency': 'USD',
                'price_to_earnings_ratio': 25.5,
                'price_to_book_ratio': 6.2,
                'market_cap': 3000000000000,
                'return_on_equity': 0.15
            }
        ]
        
        # 缓存财务数据
        db_manager.cache_financial_data('AAPL', test_financial_data, cache_hours=24)
        print("✅ 财务数据缓存成功")
        
        # 从缓存获取数据
        cached_data = db_manager.get_cached_financial_data('AAPL', '2024-01-01')
        print(f"✅ 从缓存获取财务数据成功，共 {len(cached_data)} 条记录")
        
        return True
    except Exception as e:
        print(f"❌ 财务缓存测试失败: {str(e)}")
        return False

def test_cache_stats():
    """测试缓存统计功能"""
    print("\n📈 测试缓存统计功能...")
    try:
        db_manager = get_database_manager()
        
        # 获取缓存统计
        stats = db_manager.get_cache_stats()
        print("✅ 缓存统计获取成功:")
        
        if 'price_cache' in stats:
            price_stats = stats['price_cache']
            print(f"   价格缓存: {price_stats.get('total_records', 0)} 条记录")
        
        if 'financial_cache' in stats:
            financial_stats = stats['financial_cache']
            print(f"   财务缓存: {financial_stats.get('total_records', 0)} 条记录")
        
        if 'query_records' in stats:
            query_stats = stats['query_records']
            print(f"   查询记录: {query_stats.get('total_queries', 0)} 条记录")
        
        return True
    except Exception as e:
        print(f"❌ 缓存统计测试失败: {str(e)}")
        return False

def test_cache_cleanup():
    """测试缓存清理功能"""
    print("\n🧹 测试缓存清理功能...")
    try:
        db_manager = get_database_manager()
        
        # 执行缓存清理
        db_manager.cleanup_expired_cache()
        print("✅ 缓存清理执行成功")
        
        return True
    except Exception as e:
        print(f"❌ 缓存清理测试失败: {str(e)}")
        return False

def test_api_integration():
    """测试API集成功能"""
    print("\n🔗 测试API集成功能...")
    try:
        # 测试是否能正确导入新的API函数
        from tools.api import cleanup_cache, get_cache_stats
        print("✅ API函数导入成功")
        
        # 获取缓存统计
        stats = get_cache_stats()
        print("✅ API缓存统计获取成功")
        
        # 执行缓存清理
        cleanup_cache()
        print("✅ API缓存清理执行成功")
        
        return True
    except Exception as e:
        print(f"❌ API集成测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始SQLite数据库功能测试\n")
    
    tests = [
        ("数据库初始化", test_database_initialization),
        ("查询记录功能", test_query_record),
        ("分析结果保存", test_analysis_result),
        ("价格数据缓存", test_price_cache),
        ("财务数据缓存", test_financial_cache),
        ("缓存统计功能", test_cache_stats),
        ("缓存清理功能", test_cache_cleanup),
        ("API集成功能", test_api_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 出现异常: {str(e)}")
    
    print(f"\n📊 测试总结:")
    print(f"   总测试数: {total}")
    print(f"   通过测试: {passed}")
    print(f"   失败测试: {total - passed}")
    print(f"   成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！数据库功能正常工作。")
        return True
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败，请检查相关功能。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)