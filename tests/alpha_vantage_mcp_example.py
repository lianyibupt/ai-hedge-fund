#!/usr/bin/env python3
"""
实际使用 Alpha Vantage MCP 工具的示例
演示如何在真实环境中调用 MCP 工具获取股票数据
"""

def example_alpha_vantage_mcp_calls():
    """
    演示实际的 Alpha Vantage MCP 工具调用
    
    注意：这些示例需要在支持 MCP 的环境中运行
    """
    
    print("📡 Alpha Vantage MCP 工具调用示例")
    print("=" * 60)
    
    # 1. 获取股票每日价格数据
    print("\n1️⃣ 获取 AAPL 每日价格数据:")
    daily_prices_call = """
# 调用 Alpha Vantage 每日价格数据 MCP 工具
response = mcp_alphavantage_TIME_SERIES_DAILY(
    symbol="AAPL",
    outputsize="compact"
)

# 响应数据结构示例:
{
    "Meta Data": {
        "1. Information": "Daily Prices (open, high, low, close) and Volumes",
        "2. Symbol": "AAPL",
        "3. Last Refreshed": "2025-09-10",
        "4. Output Size": "Compact",
        "5. Time Zone": "US/Eastern"
    },
    "Time Series (Daily)": {
        "2025-09-10": {
            "1. open": "232.1850",
            "2. high": "232.4200", 
            "3. low": "225.9500",
            "4. close": "226.7900",
            "5. volume": "83440810"
        },
        ...
    }
}
"""
    print(daily_prices_call)
    
    # 2. 获取实时股票报价
    print("\n2️⃣ 获取 AAPL 实时报价:")
    global_quote_call = """
# 调用 Alpha Vantage 全球报价 MCP 工具
response = mcp_alphavantage_GLOBAL_QUOTE(
    symbol="AAPL"
)

# 响应数据结构示例:
{
    "Global Quote": {
        "01. symbol": "AAPL",
        "02. open": "232.1850",
        "03. high": "232.4200",
        "04. low": "225.9500", 
        "05. price": "226.7900",
        "06. volume": "83440810",
        "07. latest trading day": "2025-09-10",
        "08. previous close": "234.3500",
        "09. change": "-7.5600",
        "10. change percent": "-3.2259%"
    }
}
"""
    print(global_quote_call)
    
    # 3. 获取公司基本面数据
    print("\n3️⃣ 获取 AAPL 公司概览:")
    company_overview_call = """
# 调用 Alpha Vantage 公司概览 MCP 工具
response = mcp_alphavantage_COMPANY_OVERVIEW(
    symbol="AAPL"
)

# 响应数据包含关键财务指标:
{
    "Symbol": "AAPL",
    "Name": "Apple Inc",
    "MarketCapitalization": "3500000000000",
    "PERatio": "28.5",
    "PriceToBookRatio": "8.2",
    "DividendYield": "0.0044",
    "EPS": "6.43",
    "RevenuePerShareTTM": "24.32",
    "ProfitMargin": "0.274",
    "OperatingMarginTTM": "0.308",
    "ReturnOnAssetsTTM": "0.221",
    "ReturnOnEquityTTM": "1.479",
    "GrossProfitTTM": "169148000000",
    ...
}
"""
    print(company_overview_call)
    
    # 4. 获取技术指标数据
    print("\n4️⃣ 获取 AAPL 的 RSI 技术指标:")
    rsi_call = """
# 调用 Alpha Vantage RSI 技术指标 MCP 工具
response = mcp_alphavantage_RSI(
    symbol="AAPL",
    interval="daily",
    time_period=14,
    series_type="close"
)

# 响应数据结构示例:
{
    "Meta Data": {
        "1: Symbol": "AAPL",
        "2: Indicator": "Relative Strength Index (RSI)",
        "3: Last Refreshed": "2025-09-10",
        "4: Interval": "daily",
        "5: Time Period": 14,
        "6: Series Type": "close"
    },
    "Technical Analysis: RSI": {
        "2025-09-10": {"RSI": "45.2341"},
        "2025-09-09": {"RSI": "48.7654"},
        ...
    }
}
"""
    print(rsi_call)
    
    # 5. 获取 MACD 技术指标
    print("\n5️⃣ 获取 AAPL 的 MACD 技术指标:")
    macd_call = """
# 调用 Alpha Vantage MACD 技术指标 MCP 工具
response = mcp_alphavantage_MACD(
    symbol="AAPL",
    interval="daily",
    series_type="close",
    fastperiod=12,
    slowperiod=26,
    signalperiod=9
)

# 响应数据结构示例:
{
    "Meta Data": {
        "1: Symbol": "AAPL",
        "2: Indicator": "Moving Average Convergence/Divergence (MACD)",
        "3: Last Refreshed": "2025-09-10",
        "4: Interval": "daily",
        "5: Fast Period": 12,
        "6: Slow Period": 26,
        "7: Signal Period": 9,
        "8: Series Type": "close"
    },
    "Technical Analysis: MACD": {
        "2025-09-10": {
            "MACD_Hist": "-0.8234",
            "MACD": "1.2345",
            "MACD_Signal": "2.0579"
        },
        ...
    }
}
"""
    print(macd_call)
    
    # 6. 批量获取股票报价
    print("\n6️⃣ 批量获取多只股票实时报价:")
    bulk_quotes_call = """
# 调用 Alpha Vantage 批量报价 MCP 工具 (最多100只股票)
response = mcp_alphavantage_REALTIME_BULK_QUOTES(
    symbol="AAPL,MSFT,GOOGL,TSLA,NVDA"
)

# 响应数据结构示例:
{
    "quotes": [
        {
            "symbol": "AAPL",
            "price": "226.79",
            "change": "-7.56",
            "change_percent": "-3.23%",
            "volume": "83440810"
        },
        {
            "symbol": "MSFT", 
            "price": "415.75",
            "change": "2.30",
            "change_percent": "0.56%",
            "volume": "25430192"
        },
        ...
    ]
}
"""
    print(bulk_quotes_call)
    
    # 7. 数据处理和集成示例
    print("\n7️⃣ 在 personal_trading_app.py 中集成 MCP 工具:")
    integration_example = """
# 在 alphavantage_mcp.py 中实际调用 MCP 工具
def fetch_prices_from_alphavantage(ticker: str, start_date: str, end_date: str, region: str = 'us') -> List[Price]:
    try:
        # 🔄 实际调用 Alpha Vantage MCP 工具
        time_series_data = mcp_alphavantage_TIME_SERIES_DAILY(
            symbol=ticker,
            outputsize="full"
        )
        
        # 转换数据格式
        alphavantage_api = get_alphavantage_api()
        prices = alphavantage_api.convert_time_series_to_prices(time_series_data, ticker)
        
        # 过滤日期范围
        filtered_prices = [p for p in prices if start_date <= p.time <= end_date]
        
        return filtered_prices
        
    except Exception as e:
        print(f"❌ Alpha Vantage MCP 调用失败: {str(e)}")
        return []

# 在 alphavantage_mcp.py 中获取财务数据
def fetch_financial_metrics_from_alphavantage(ticker: str, end_date: str, period: str = "ttm", limit: int = 10, region: str = 'us') -> List[FinancialMetrics]:
    try:
        # 🔄 实际调用 Alpha Vantage MCP 工具
        overview_data = mcp_alphavantage_COMPANY_OVERVIEW(symbol=ticker)
        
        # 转换数据格式
        alphavantage_api = get_alphavantage_api()
        metrics = alphavantage_api.convert_overview_to_financial_metrics(overview_data, ticker)
        
        return metrics[:limit]
        
    except Exception as e:
        print(f"❌ Alpha Vantage MCP 财务数据调用失败: {str(e)}")
        return []
"""
    print(integration_example)
    
    print("\n📋 使用指南:")
    print("=" * 60)
    
    usage_guide = """
🎯 在实际环境中使用 Alpha Vantage MCP 工具的步骤:

1. 确保环境支持:
   ✅ 在支持 MCP 的环境中运行 (如支持 MCP 的 AI 助手环境)
   ✅ 确保有有效的 Alpha Vantage API 访问权限
   ✅ 使用正确的 MCP 工具函数名和参数

2. 修改现有代码:
   📝 更新 alphavantage_mcp.py 中的实际调用部分
   📝 将示例中的 MCP 工具调用替换到实际函数中
   📝 在 alphavantage_mcp_wrapper.py 中设置 mock_mode=False

3. 测试验证:
   🧪 测试单只股票数据获取
   🧪 测试批量股票数据获取  
   🧪 验证技术指标计算准确性
   🧪 确认财务数据完整性

4. 优化性能:
   ⚡ 利用现有的智能缓存机制
   ⚡ 合理控制 API 调用频率
   ⚡ 使用批量接口减少调用次数

🎉 完成后，您的交易分析系统将享受到:
   • 更丰富的金融数据源
   • 更准确的技术指标
   • 更全面的基本面分析
   • 更便捷的 MCP 工具集成
"""
    print(usage_guide)


def show_mcp_tool_list():
    """显示可用的 Alpha Vantage MCP 工具列表"""
    print("\n🛠️ 可用的 Alpha Vantage MCP 工具:")
    print("=" * 60)
    
    tools = {
        "📊 股票数据": [
            "mcp_alphavantage_TIME_SERIES_DAILY - 每日股价数据",
            "mcp_alphavantage_TIME_SERIES_WEEKLY - 每周股价数据", 
            "mcp_alphavantage_TIME_SERIES_MONTHLY - 每月股价数据",
            "mcp_alphavantage_GLOBAL_QUOTE - 实时股票报价",
            "mcp_alphavantage_REALTIME_BULK_QUOTES - 批量实时报价"
        ],
        "🏢 基本面数据": [
            "mcp_alphavantage_COMPANY_OVERVIEW - 公司概览",
            "mcp_alphavantage_INCOME_STATEMENT - 利润表",
            "mcp_alphavantage_BALANCE_SHEET - 资产负债表",
            "mcp_alphavantage_CASH_FLOW - 现金流量表",
            "mcp_alphavantage_EARNINGS - 盈利数据"
        ],
        "📈 技术指标": [
            "mcp_alphavantage_RSI - 相对强弱指数",
            "mcp_alphavantage_MACD - 移动平均收敛发散",
            "mcp_alphavantage_BBANDS - 布林带",
            "mcp_alphavantage_SMA - 简单移动平均",
            "mcp_alphavantage_EMA - 指数移动平均"
        ],
        "🌍 其他市场": [
            "mcp_alphavantage_CURRENCY_EXCHANGE_RATE - 外汇汇率",
            "mcp_alphavantage_CRYPTO_INTRADAY - 加密货币数据",
            "mcp_alphavantage_WTI - 原油价格",
            "mcp_alphavantage_NATURAL_GAS - 天然气价格"
        ]
    }
    
    for category, tool_list in tools.items():
        print(f"\n{category}:")
        for tool in tool_list:
            print(f"  • {tool}")


if __name__ == "__main__":
    example_alpha_vantage_mcp_calls()
    show_mcp_tool_list()
    
    print("\n" + "=" * 60)
    print("💡 提示:")
    print("这些示例展示了如何在实际 MCP 环境中调用 Alpha Vantage 工具")
    print("要实际使用，请将示例代码集成到 alphavantage_mcp.py 文件中")
    print("并确保在支持 MCP 的环境中运行")