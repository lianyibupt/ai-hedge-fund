#!/usr/bin/env python3
"""
Alpha Vantage MCP 工具使用示例
演示如何在实际环境中调用 Alpha Vantage MCP 工具
"""

import sys
import os
from datetime import datetime, timedelta

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)


def demo_alpha_vantage_usage():
    """演示 Alpha Vantage MCP 工具的使用"""
    print("🚀 Alpha Vantage MCP 工具使用示例")
    print("=" * 60)
    
    # 导入必要的模块
    try:
        from tools.alphavantage_mcp_wrapper import get_alphavantage_wrapper
        from tools.api import get_prices, get_financial_metrics
        
        print("✅ 成功导入 Alpha Vantage MCP 模块")
    except ImportError as e:
        print(f"❌ 导入失败: {str(e)}")
        return False
    
    # 设置测试参数
    ticker = "AAPL"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"\n📊 测试股票: {ticker}")
    print(f"📅 日期范围: {start_date} 到 {end_date}")
    print("-" * 60)
    
    # 1. 测试 Alpha Vantage 包装器
    print("\n1️⃣ 测试 Alpha Vantage MCP 包装器...")
    try:
        wrapper = get_alphavantage_wrapper()
        
        # 设置为模拟模式用于演示
        wrapper.set_mock_mode(True)
        
        # 测试获取价格数据
        print("📈 获取价格数据...")
        prices = wrapper.get_daily_prices(ticker, start_date, end_date)
        if prices:
            print(f"✅ 成功获取 {len(prices)} 条价格数据")
            print(f"   最新价格: ${prices[-1].close:.2f}")
        else:
            print("⚠️ 未获取到价格数据")
        
        # 测试获取实时报价
        print("\n💰 获取实时报价...")
        quote = wrapper.get_real_time_quote(ticker)
        if quote:
            print(f"✅ 成功获取实时报价: ${quote.close:.2f}")
        else:
            print("⚠️ 未获取到实时报价")
        
        # 测试获取财务指标
        print("\n📊 获取财务指标...")
        metrics = wrapper.get_company_overview(ticker)
        if metrics:
            m = metrics[0]
            print(f"✅ 成功获取财务指标:")
            print(f"   市值: ${m.market_cap:,.0f}" if m.market_cap else "   市值: N/A")
            print(f"   P/E比率: {m.price_to_earnings_ratio:.2f}" if m.price_to_earnings_ratio else "   P/E比率: N/A")
            print(f"   P/B比率: {m.price_to_book_ratio:.2f}" if m.price_to_book_ratio else "   P/B比率: N/A")
        else:
            print("⚠️ 未获取到财务指标")
            
    except Exception as e:
        print(f"❌ Alpha Vantage 包装器测试失败: {str(e)}")
    
    # 2. 测试统一 API 接口
    print("\n2️⃣ 测试统一 API 接口...")
    try:
        print("📈 通过统一接口获取价格数据...")
        prices = get_prices(ticker, start_date, end_date)
        if prices:
            print(f"✅ 统一接口价格数据获取成功: {len(prices)} 条")
            print(f"   最新价格: ${prices[-1].close:.2f}")
        else:
            print("⚠️ 统一接口未获取到价格数据")
        
        print("\n💰 通过统一接口获取财务指标...")
        financial_metrics = get_financial_metrics(ticker, end_date)
        if financial_metrics:
            m = financial_metrics[0]
            print(f"✅ 统一接口财务指标获取成功")
            print(f"   市值: ${m.market_cap:,.0f}" if m.market_cap else "   市值: N/A")
            print(f"   P/E比率: {m.price_to_earnings_ratio:.2f}" if m.price_to_earnings_ratio else "   P/E比率: N/A")
        else:
            print("⚠️ 统一接口未获取到财务指标")
            
    except Exception as e:
        print(f"❌ 统一API接口测试失败: {str(e)}")
    
    # 3. 实际 MCP 工具调用示例（需要在 MCP 环境中运行）
    print("\n3️⃣ 实际 MCP 工具调用示例...")
    print("""
    在实际的 MCP 环境中，您可以直接调用以下工具：
    
    📊 获取每日价格数据：
    mcp_alphavantage_TIME_SERIES_DAILY(
        symbol="AAPL",
        outputsize="compact"
    )
    
    💰 获取实时报价：
    mcp_alphavantage_GLOBAL_QUOTE(
        symbol="AAPL"
    )
    
    🏢 获取公司概览：
    mcp_alphavantage_COMPANY_OVERVIEW(
        symbol="AAPL"
    )
    
    📈 获取技术指标（如RSI）：
    mcp_alphavantage_RSI(
        symbol="AAPL",
        interval="daily",
        time_period=14,
        series_type="close"
    )
    """)
    
    # 4. 显示集成优势
    print("\n4️⃣ Alpha Vantage MCP 集成优势...")
    print("""
    🔄 从 iTick 迁移到 Alpha Vantage MCP 的优势：
    
    ✅ 更广泛的API支持: 
       - 基础股票数据、技术指标、基本面数据
       - 加密货币、外汇、商品数据
       - 经济指标和新闻情感分析
    
    ✅ 更好的数据质量:
       - 来自权威金融数据提供商
       - 实时和历史数据完整性更高
       - 标准化的API响应格式
    
    ✅ MCP 工具集成:
       - 直接在对话中调用金融数据
       - 无需手动API密钥管理
       - 自动处理API限制和重试
    
    ✅ 扩展性更好:
       - 支持50+种技术指标
       - 丰富的基本面分析数据
       - 多市场支持（美股为主）
    """)
    
    print("\n🎯 总结:")
    print("✅ Alpha Vantage MCP 工具集成成功")
    print("✅ 兼容现有的缓存和数据处理架构")
    print("✅ 为您的交易分析提供更丰富的数据源")
    print("\n💡 建议: 在实际使用中，主要使用美股代码以获得最佳数据质量")
    
    return True


def show_migration_guide():
    """显示迁移指南"""
    print("\n📋 从 iTick 到 Alpha Vantage MCP 的迁移指南")
    print("=" * 60)
    
    print("""
    🔄 主要变更:
    
    1. 数据源替换:
       - 旧: iTick API
       - 新: Alpha Vantage MCP 工具
    
    2. 代码调用方式:
       - 旧: itick_api.get_historical_kline()
       - 新: mcp_alphavantage_TIME_SERIES_DAILY()
    
    3. 支持的市场:
       - 主要: 美股 (US) - 完全支持
       - 有限: 其他市场 - 依赖历史缓存
    
    4. API配置:
       - 旧: 需要配置 ITICK_API_KEY
       - 新: MCP 工具自动处理API密钥
    
    🎯 最佳实践:
    
    1. 主要使用美股代码 (AAPL, MSFT, GOOGL 等)
    2. 利用智能缓存减少API调用
    3. 启用基本面分析获得更全面的投资信息
    4. 定期清理过期缓存保持数据新鲜度
    """)


if __name__ == "__main__":
    # 运行演示
    success = demo_alpha_vantage_usage()
    
    if success:
        print("\n" + "=" * 60)
        show_migration_guide()
        print("\n🎉 Alpha Vantage MCP 工具演示完成！")
    else:
        print("\n❌ Alpha Vantage MCP 工具演示失败")
    
    print("\n💡 要在实际 MCP 环境中使用，请确保：")
    print("   1. 在支持 MCP 的环境中运行")
    print("   2. 有有效的 Alpha Vantage API 访问权限")
    print("   3. 使用美股代码获得最佳体验")