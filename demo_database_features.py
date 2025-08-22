#!/usr/bin/env python3
"""
数据库功能演示脚本
展示SQLite数据库在个人交易分析中的应用
"""

import sys
import os
from datetime import datetime, timedelta

# 添加src目录到Python路径
sys.path.append('/Users/bytedance/Documents/code/ai-hedge-fund/src')

from data.database import get_database_manager
from tools.api import get_cache_stats, cleanup_cache
import pandas as pd

def demo_query_and_analysis_flow():
    """演示完整的查询和分析流程"""
    print("🎯 演示完整的查询和分析流程\n")
    
    db_manager = get_database_manager()
    
    # 1. 保存查询记录
    print("1️⃣ 保存查询记录...")
    tickers = ["AAPL", "MSFT", "GOOGL"]
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    analysis_params = {
        "show_detailed_indicators": True,
        "show_historical_data": False,
        "auto_refresh": False
    }
    
    query_record_id = db_manager.save_query_record(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        analysis_params=analysis_params,
        session_id="demo_session_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        user_ip="192.168.1.100"
    )
    print(f"   ✅ 查询记录已保存，ID: {query_record_id}")
    
    # 2. 保存分析结果
    print("\n2️⃣ 保存分析结果...")
    for i, ticker in enumerate(tickers):
        # 模拟不同的分析结果
        signals = ['看涨', '看跌', '中性']
        confidences = [85, 65, 45]
        
        analysis_result = {
            'ticker': ticker,
            'current_price': 150.0 + i * 50,
            'analysis': {
                'signal': signals[i % len(signals)],
                'confidence': confidences[i % len(confidences)],
                'reason': f'{ticker}的技术指标显示{signals[i % len(signals)]}趋势',
                'details': {
                    'macd': {'signal': signals[i % len(signals)], 'reason': 'MACD指标分析'},
                    'rsi': {'signal': '中性', 'reason': 'RSI在正常范围'},
                    'bollinger': {'signal': signals[i % len(signals)], 'reason': '布林带分析'},
                    'volume': {'signal': '看涨', 'reason': '成交量分析'}
                }
            },
            'financial_metrics': {
                'pe_ratio': 25.0 + i * 5,
                'pb_ratio': 6.0 + i * 2
            },
            'data_days': 30
        }
        
        db_manager.save_analysis_result(query_record_id, analysis_result)
        print(f"   ✅ {ticker} 分析结果已保存")
    
    # 3. 演示缓存功能
    print("\n3️⃣ 演示缓存功能...")
    
    # 缓存价格数据
    for ticker in tickers:
        price_data = []
        base_price = 150.0
        for j in range(5):
            price_data.append({
                'time': f'2024-01-{j+1:02d}',
                'open': base_price + j,
                'high': base_price + j + 5,
                'low': base_price + j - 2,
                'close': base_price + j + 3,
                'volume': 1000000 + j * 100000
            })
        
        db_manager.cache_price_data(ticker, price_data, cache_hours=24)
        print(f"   ✅ {ticker} 价格数据已缓存")
    
    # 缓存财务数据
    for ticker in tickers:
        financial_data = [{
            'ticker': ticker,
            'report_period': '2024-01-01',
            'period': 'ttm',
            'currency': 'USD',
            'price_to_earnings_ratio': 25.0,
            'price_to_book_ratio': 6.0,
            'market_cap': 3000000000000,
            'return_on_equity': 0.15
        }]
        
        db_manager.cache_financial_data(ticker, financial_data, cache_hours=24*7)
        print(f"   ✅ {ticker} 财务数据已缓存")
    
    return query_record_id

def demo_query_history():
    """演示查询历史功能"""
    print("\n📋 演示查询历史功能\n")
    
    db_manager = get_database_manager()
    
    # 获取查询历史
    history_df = db_manager.get_query_history(limit=10)
    print(f"📊 查询历史记录 (共 {len(history_df)} 条):")
    print("=" * 80)
    
    if not history_df.empty:
        for _, row in history_df.iterrows():
            tickers = ', '.join(row['tickers']) if isinstance(row['tickers'], list) else str(row['tickers'])
            print(f"🔍 查询ID: {row['id']}")
            print(f"   时间: {row['timestamp']}")
            print(f"   股票: {tickers}")
            print(f"   日期范围: {row['start_date']} ~ {row['end_date']}")
            print(f"   结果数量: {row['result_count']}")
            print(f"   平均信心度: {row['avg_confidence']:.1f}%" if row['avg_confidence'] else "   平均信心度: N/A")
            print("-" * 60)
    else:
        print("暂无查询历史记录")

def demo_analysis_history():
    """演示分析历史功能"""
    print("\n📈 演示分析历史功能\n")
    
    db_manager = get_database_manager()
    
    # 获取所有分析历史
    analysis_df = db_manager.get_analysis_history(limit=20)
    print(f"📊 分析历史记录 (共 {len(analysis_df)} 条):")
    print("=" * 100)
    
    if not analysis_df.empty:
        for _, row in analysis_df.iterrows():
            print(f"📊 {row['ticker']} | {row['signal']} | 信心度: {row['confidence']}% | 价格: ${row['current_price']:.2f}")
            print(f"   原因: {row['reason']}")
            print(f"   建议: {row['recommendation']}")
            print(f"   时间: {row['created_at']}")
            print("-" * 80)
    else:
        print("暂无分析历史记录")

def demo_cache_features():
    """演示缓存功能"""
    print("\n💾 演示缓存功能\n")
    
    db_manager = get_database_manager()
    
    # 1. 获取缓存统计
    print("1️⃣ 缓存统计:")
    stats = db_manager.get_cache_stats()
    
    if 'price_cache' in stats:
        price_stats = stats['price_cache']
        print(f"   📈 价格缓存:")
        print(f"      总记录数: {price_stats.get('total_records', 0)}")
        print(f"      股票数量: {price_stats.get('unique_tickers', 0)}")
        print(f"      有效记录: {price_stats.get('valid_records', 0)}")
        print(f"      日期范围: {price_stats.get('earliest_date', 'N/A')} ~ {price_stats.get('latest_date', 'N/A')}")
    
    if 'financial_cache' in stats:
        financial_stats = stats['financial_cache']
        print(f"   💰 财务缓存:")
        print(f"      总记录数: {financial_stats.get('total_records', 0)}")
        print(f"      股票数量: {financial_stats.get('unique_tickers', 0)}")
        print(f"      有效记录: {financial_stats.get('valid_records', 0)}")
    
    if 'query_records' in stats:
        query_stats = stats['query_records']
        print(f"   🔍 查询记录:")
        print(f"      总查询数: {query_stats.get('total_queries', 0)}")
        print(f"      查询天数: {query_stats.get('query_days', 0)}")
        print(f"      首次查询: {query_stats.get('first_query', 'N/A')}")
        print(f"      最近查询: {query_stats.get('last_query', 'N/A')}")
    
    # 2. 演示缓存数据获取
    print("\n2️⃣ 从缓存获取数据:")
    
    # 获取价格缓存数据
    cached_prices = db_manager.get_cached_price_data('AAPL', '2024-01-01', '2024-01-05')
    print(f"   📈 AAPL价格缓存: {len(cached_prices)} 条记录")
    
    # 获取财务缓存数据
    cached_financial = db_manager.get_cached_financial_data('AAPL')
    print(f"   💰 AAPL财务缓存: {len(cached_financial)} 条记录")
    
    # 3. 演示缓存清理
    print("\n3️⃣ 缓存清理:")
    print("   🧹 执行缓存清理...")
    db_manager.cleanup_expired_cache()
    print("   ✅ 缓存清理完成")

def demo_multi_level_cache():
    """演示多级缓存机制"""
    print("\n🔄 演示多级缓存机制\n")
    
    print("多级缓存架构:")
    print("┌─────────────┐    ┌─────────────┐    ┌─────────────┐")
    print("│   内存缓存    │ -> │  SQLite缓存  │ -> │  iTick API  │")
    print("│  (第一级)    │    │   (第二级)   │    │   (数据源)   │")
    print("└─────────────┘    └─────────────┘    └─────────────┘")
    print("")
    print("缓存策略说明:")
    print("• 内存缓存: 程序运行期间有效，访问速度最快")
    print("• SQLite缓存: 持久化存储，支持过期时间管理")
    print("• iTick API: 最终数据源，仅在缓存未命中时调用")
    print("")
    print("缓存优势:")
    print("• 🚀 显著减少API调用次数")
    print("• ⚡ 提高数据获取速度")
    print("• 💾 支持离线数据访问")
    print("• 📊 自动管理数据过期")

def main():
    """主演示函数"""
    print("🎯 个人交易分析系统 - SQLite数据库功能演示")
    print("=" * 60)
    print("本演示将展示以下功能:")
    print("• 查询记录存储与追溯")
    print("• 技术分析结果保存")
    print("• iTick API数据缓存")
    print("• 多级缓存机制")
    print("• 历史记录查询")
    print("=" * 60)
    
    try:
        # 1. 演示完整的查询和分析流程
        query_record_id = demo_query_and_analysis_flow()
        
        # 2. 演示查询历史
        demo_query_history()
        
        # 3. 演示分析历史
        demo_analysis_history()
        
        # 4. 演示缓存功能
        demo_cache_features()
        
        # 5. 演示多级缓存机制
        demo_multi_level_cache()
        
        print("\n🎉 演示完成！")
        print("\n📝 总结:")
        print("• ✅ SQLite数据库成功集成到个人交易分析系统")
        print("• ✅ 查询记录和分析结果可以完整追溯")
        print("• ✅ iTick API数据实现了高效的多级缓存")
        print("• ✅ 系统性能得到显著提升")
        
        print(f"\n📂 数据库文件位置: /Users/bytedance/Documents/code/ai-hedge-fund/trading_data.db")
        print("\n🚀 可以运行 Streamlit 应用来体验完整功能:")
        print("   streamlit run src/personal_trading_app.py")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)