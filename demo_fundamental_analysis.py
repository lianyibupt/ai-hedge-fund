#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基本面分析框架演示脚本
展示如何使用基于Finnhub API的五模块基本面分析系统
"""

import os
import sys
import argparse
from typing import List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加src目录到路径，以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from analyzers.fundamental_analyzer import (
    FinnhubFundamentalAnalyzer, 
    analyze_multiple_stocks,
    generate_analysis_report,
    InvestmentSignal
)

def demo_single_stock_analysis(symbol: str = "AAPL"):
    """演示单个股票的基本面分析"""
    print(f"\n🔍 单股分析演示 - {symbol}")
    print("=" * 60)
    
    analyzer = FinnhubFundamentalAnalyzer()
    
    try:
        result = analyzer.analyze_stock(symbol)
        
        # 显示简要结果
        print(f"\n📊 {symbol} 分析结果:")
        print(f"• 公司名称: {result.company_name}")
        print(f"• 公司类型: {result.company_type.value}")
        print(f"• 综合评分: {result.total_score:.1f}/50.0 ({result.overall_percentage:.1f}%)")
        print(f"• 投资建议: {result.investment_signal.value}")
        print(f"• 信心度: {result.confidence:.1f}%")
        
        # 显示各模块评分
        print(f"\n📈 各模块评分:")
        print(f"• 经营质量: {result.operating_quality.score:.1f}/10.0")
        print(f"• 盈利效率: {result.profitability_efficiency.score:.1f}/10.0")  
        print(f"• 成长地位: {result.growth_market_position.score:.1f}/10.0")
        print(f"• 财务风险: {result.financial_risk.score:.1f}/10.0")
        print(f"• 管理治理: {result.management_governance.score:.1f}/10.0")
        
        # 显示详细报告
        print(f"\n{generate_analysis_report(result)}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

def demo_multiple_stocks_comparison():
    """演示多股票对比分析"""
    print(f"\n📊 多股对比演示")
    print("=" * 60)
    
    # 选择不同类型的股票进行对比
    tech_stocks = ['AAPL', 'MSFT', 'GOOGL']
    growth_stocks = ['TSLA', 'NVDA']
    traditional_stocks = ['JNJ', 'PG']
    
    all_symbols = tech_stocks + growth_stocks + traditional_stocks
    
    print(f"🎯 分析股票: {', '.join(all_symbols)}")
    print()
    
    results = analyze_multiple_stocks(all_symbols)
    
    if not results:
        print("❌ 未能获取任何分析结果")
        return
    
    # 按评分排序
    sorted_results = sorted(results.items(), key=lambda x: x[1].total_score, reverse=True)
    
    # 显示对比表格
    print(f"\n📋 对比结果:")
    print("-" * 100)
    print(f"{'排名':<4} {'股票':<8} {'公司类型':<12} {'综合评分':<12} {'投资建议':<12} {'信心度':<8} {'强项模块':<15}")
    print("-" * 100)
    
    for i, (symbol, result) in enumerate(sorted_results, 1):
        # 找出最强的模块
        scores = [
            ("经营", result.operating_quality.score),
            ("盈利", result.profitability_efficiency.score),
            ("成长", result.growth_market_position.score),
            ("风控", result.financial_risk.score),
            ("治理", result.management_governance.score)
        ]
        best_module = max(scores, key=lambda x: x[1])[0]
        
        print(f"{i:<4} {symbol:<8} {result.company_type.value:<12} "
              f"{result.total_score:.1f}/50.0   {result.investment_signal.value:<12} "
              f"{result.confidence:.1f}%   {best_module}({max(scores, key=lambda x: x[1])[1]:.1f})")
    
    # 投资组合建议
    print(f"\n💼 投资组合建议:")
    print("-" * 60)
    
    strong_buys = [s for s, r in results.items() if r.investment_signal == InvestmentSignal.STRONG_BUY]
    buys = [s for s, r in results.items() if r.investment_signal == InvestmentSignal.BUY]
    holds = [s for s, r in results.items() if r.investment_signal == InvestmentSignal.HOLD]
    
    if strong_buys:
        print(f"🚀 核心持仓 (强烈买入): {', '.join(strong_buys)}")
    if buys:
        print(f"🟢 配置建议 (买入): {', '.join(buys)}")
    if holds:
        print(f"🟡 观察标的 (持有): {', '.join(holds)}")

def demo_framework_explanation():
    """演示分析框架说明"""
    print(f"\n📚 基本面分析框架说明")
    print("=" * 60)
    
    print("""
🎯 五大分析模块:

1. 🏢 公司经营质量 (Operating Quality)
   • 毛利率、营业利润率
   • 52周股价表现  
   • 行业地位评估
   
2. 💰 盈利能力与财务效率 (Profitability & Efficiency)
   • 盈利公司: ROE、ROA、净利润率、市盈率
   • 未盈利公司: 营收规模、毛利率、市销率
   
3. 🚀 成长性与行业地位 (Growth & Market Position)
   • 营收规模与增长潜力
   • 市值地位分析
   • 行业属性评估 (高成长 vs 传统)
   • 股价波动性 (反映成长性)
   
4. ⚠️ 财务风险与可持续性 (Financial Risk & Sustainability)
   • 流动比率、速动比率
   • 市净率安全边际
   • 根据公司类型的风险评估
   
5. 👥 管理层与治理 (Management & Governance)
   • 分析师推荐趋势
   • 新闻情绪分析
   • 信息透明度
   • 市场关注度

📊 评分体系:
• 每个模块满分 10 分
• 总分满分 50 分
• 80%+ (40分+): 强烈买入
• 70-80% (35-40分): 买入
• 60-70% (30-35分): 持有
• 40-60% (20-30分): 卖出
• <40% (<20分): 强烈卖出

🔍 投资决策流程:
1. 判断公司类型 (盈利 vs 未盈利)
2. 五模块分析打分
3. 综合评分生成投资信号
4. 考虑公司类型调整风险建议
""")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='基本面分析框架演示')
    parser.add_argument('--stock', '-s', type=str, help='分析单个股票 (如: AAPL)')
    parser.add_argument('--compare', '-c', action='store_true', help='多股票对比分析')
    parser.add_argument('--explain', '-e', action='store_true', help='显示框架说明')
    parser.add_argument('--all', '-a', action='store_true', help='运行所有演示')
    
    args = parser.parse_args()
    
    print("🚀 基于基本面的股票分析框架演示")
    print("=" * 60)
    print("基于您提供的五大模块分析框架和Finnhub API实现")
    print("注意: 请确保设置 FINNHUB_API_KEY 环境变量")
    
    # 检查API密钥
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key or api_key == "YOUR_FREE_KEY":
        print("\n⚠️ 警告: 未设置有效的API密钥，将使用默认密钥 (功能可能受限)")
        print("请设置环境变量: export FINNHUB_API_KEY=your_finnhub_api_key")
    else:
        print(f"\n✅ API密钥已设置: {api_key[:8]}...")
    
    if args.all:
        # 运行所有演示
        demo_framework_explanation()
        demo_single_stock_analysis()
        demo_multiple_stocks_comparison()
    elif args.stock:
        # 单股分析
        demo_single_stock_analysis(args.stock.upper())
    elif args.compare:
        # 多股对比
        demo_multiple_stocks_comparison()
    elif args.explain:
        # 框架说明
        demo_framework_explanation()
    else:
        # 默认显示帮助和简单演示
        print(f"\n🎯 使用方法:")
        print("python demo_fundamental_analysis.py --explain    # 查看框架说明")
        print("python demo_fundamental_analysis.py -s AAPL     # 分析单个股票")
        print("python demo_fundamental_analysis.py --compare    # 多股票对比")
        print("python demo_fundamental_analysis.py --all        # 运行所有演示")
        
        # 运行一个简单的演示
        demo_framework_explanation()
        demo_single_stock_analysis()

if __name__ == "__main__":
    main()