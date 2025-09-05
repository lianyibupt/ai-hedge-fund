#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
专门的基本面分析应用
独立的基本面分析页面，不依赖iTick数据，专注于基本面分析
"""

import streamlit as st
import sys
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加src目录到Python路径
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

from analyzers.fundamental_analyzer import (
    FinnhubFundamentalAnalyzer, 
    analyze_multiple_stocks,
    generate_analysis_report,
    InvestmentSignal,
    CompanyType
)
import uuid
import re

# 页面配置
st.set_page_config(
    page_title="基本面分析系统", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 生成会话ID
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

def validate_us_stock_ticker(ticker: str) -> tuple[bool, str]:
    """
    验证美股代码格式（基本面分析仅支持美股）
    
    Args:
        ticker: 股票代码
        
    Returns:
        (是否有效, 错误信息)
    """
    ticker = ticker.strip().upper()
    
    if not ticker:
        return False, "股票代码不能为空"
    
    # 美股：字母组合，1-5位
    if re.match(r'^[A-Z]{1,5}$', ticker):
        return True, ""
    
    return False, f"基本面分析仅支持美股代码格式（如AAPL, MSFT）: {ticker}"

def create_score_chart(result):
    """
    创建基本面评分图表
    """
    # 五大模块数据
    modules = ['经营质量', '盈利效率', '成长地位', '财务风险', '管理治理']
    scores = [
        result.operating_quality.score,
        result.profitability_efficiency.score,
        result.growth_market_position.score,
        result.financial_risk.score,
        result.management_governance.score
    ]
    
    # 创建雷达图
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=modules,
        fill='toself',
        name=result.ticker,
        line_color='rgb(34, 139, 34)',
        fillcolor='rgba(34, 139, 34, 0.25)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=False,
        title=f"{result.ticker} 基本面分析雷达图",
        height=400
    )
    
    return fig

def create_comparison_chart(results):
    """
    创建多股票对比图表
    """
    if len(results) < 2:
        return None
    
    tickers = list(results.keys())
    modules = ['经营质量', '盈利效率', '成长地位', '财务风险', '管理治理']
    
    fig = go.Figure()
    
    # 为每只股票添加一条线
    for ticker in tickers:
        result = results[ticker]
        scores = [
            result.operating_quality.score,
            result.profitability_efficiency.score,
            result.growth_market_position.score,
            result.financial_risk.score,
            result.management_governance.score
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=modules,
            fill='toself',
            name=ticker,
            line_width=2
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=True,
        title="多股票基本面对比",
        height=500
    )
    
    return fig

def display_fundamental_summary(result):
    """
    显示基本面分析摘要
    """
    # 综合评分和建议
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("综合评分", f"{result.total_score:.1f}/50.0")
        st.caption(f"百分比: {result.overall_percentage:.1f}%")
    
    with col2:
        # 投资信号颜色显示
        signal_colors = {
            "强烈买入": "#00c851",
            "买入": "#00c851", 
            "持有": "#ffbb33",
            "卖出": "#ff4444",
            "强烈卖出": "#ff4444"
        }
        signal_value = result.investment_signal.value
        color = signal_colors.get(signal_value, "#666666")
        st.markdown(f"**投资建议**")
        st.markdown(f"<span style='color: {color}; font-weight: bold; font-size: 1.2em;'>{signal_value}</span>", 
                   unsafe_allow_html=True)
    
    with col3:
        st.metric("分析信心度", f"{result.confidence:.1f}%")
    
    with col4:
        st.metric("公司类型", result.company_type.value)
        st.caption(f"公司: {result.company_name}")

def display_detailed_modules(result):
    """
    显示详细模块分析
    """
    st.subheader("📊 五大模块详细分析")
    
    modules = [
        ("🏢 经营质量", result.operating_quality, "评估公司运营效率和市场地位"),
        ("💰 盈利效率", result.profitability_efficiency, "分析公司盈利能力和财务效率"),
        ("🚀 成长地位", result.growth_market_position, "评估成长潜力和行业地位"),
        ("⚠️ 财务风险", result.financial_risk, "评估财务稳定性和风险控制"),
        ("👥 管理治理", result.management_governance, "分析管理层和公司治理")
    ]
    
    # 分两行展示
    for i in range(0, len(modules), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(modules):
                name, score_obj, description = modules[i + j]
                with cols[j]:
                    # 评分显示
                    score_percentage = score_obj.percentage
                    if score_percentage >= 80:
                        score_color = "#00c851"  # 绿色
                    elif score_percentage >= 60:
                        score_color = "#ffbb33"  # 黄色
                    else:
                        score_color = "#ff4444"  # 红色
                    
                    st.markdown(f"### {name}")
                    st.markdown(f"<div style='font-size: 2em; color: {score_color}; font-weight: bold;'>{score_obj.score:.1f}/10</div>", 
                               unsafe_allow_html=True)
                    st.caption(f"{score_percentage:.1f}% | {description}")
                    
                    # 详细信息
                    with st.expander("查看详情"):
                        for detail in score_obj.details:
                            st.write(f"• {detail}")

def display_investment_recommendation(result):
    """
    显示投资建议和风险提示
    """
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 投资建议")
        
        # 根据投资信号显示不同颜色的建议
        signal_value = result.investment_signal.value
        if signal_value in ["强烈买入", "买入"]:
            st.success(f"💰 {signal_value}")
            st.write("基本面表现优秀，具有良好的投资价值。")
        elif signal_value == "持有":
            st.warning(f"⚠️ {signal_value}")
            st.write("基本面表现一般，建议谨慎观察。")
        else:
            st.error(f"🚫 {signal_value}")
            st.write("基本面存在较大风险，建议避免投资。")
        
        st.write(f"**分析信心度:** {result.confidence:.1f}%")
        
        # 投资要点
        st.subheader("📋 关键投资要点")
        
        # 找出最强和最弱的模块
        modules_scores = [
            ("经营质量", result.operating_quality.score),
            ("盈利效率", result.profitability_efficiency.score),
            ("成长地位", result.growth_market_position.score),
            ("财务风险", result.financial_risk.score),
            ("管理治理", result.management_governance.score)
        ]
        
        strongest = max(modules_scores, key=lambda x: x[1])
        weakest = min(modules_scores, key=lambda x: x[1])
        
        st.write(f"✅ **最强优势:** {strongest[0]} ({strongest[1]:.1f}/10)")
        st.write(f"⚠️ **需要关注:** {weakest[0]} ({weakest[1]:.1f}/10)")
    
    with col2:
        st.subheader("⚠️ 风险提示")
        st.warning("""
        **投资风险提示:**
        
        • 本分析仅供参考，不构成投资建议
        • 投资有风险，决策需谨慎  
        • 基本面分析具有滞后性
        • 建议结合技术分析和市场环境
        • 请根据个人风险承受能力投资
        """)
        
        if result.company_type == CompanyType.NON_PROFITABLE:
            st.error("""
            **未盈利公司特别提示:**
            
            • 公司尚未实现盈利
            • 投资风险较高
            • 关注现金流和烧钱速度
            • 谨慎评估成长前景
            """)

# CSS样式
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}
.strong-buy { color: #00c851; font-weight: bold; }
.buy { color: #00c851; font-weight: bold; }
.hold { color: #ffbb33; font-weight: bold; }
.sell { color: #ff4444; font-weight: bold; }
.strong-sell { color: #ff4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 主标题
st.title("📈 基本面分析系统")
st.markdown("专业的股票基本面分析平台 - 基于五大核心模块的投资决策支持")

# 侧边栏参数设置
with st.sidebar:
    st.header("📊 分析参数")
    
    # API密钥状态检查
    api_key = os.getenv("FINNHUB_API_KEY")
    if api_key and api_key != "YOUR_FREE_KEY":
        st.success(f"✅ Finnhub API 已配置")
        st.caption(f"密钥: {api_key[:8]}...")
    else:
        st.error("❌ 请配置 Finnhub API 密钥")
        st.info("在 .env 文件中设置 FINNHUB_API_KEY")
    
    st.subheader("🏢 股票选择")
    
    # 基本面分析说明
    with st.expander("📖 基本面分析说明", expanded=False):
        st.markdown("""
        **五大分析模块:**
        
        🏢 **经营质量** - 毛利率、营业利润率、股价表现、行业地位
        
        💰 **盈利效率** - ROE、ROA、净利率、P/E比率（盈利公司）或营收规模、毛利率、P/S比率（未盈利公司）
        
        🚀 **成长地位** - 营收规模、市值地位、行业属性、股价波动性
        
        ⚠️ **财务风险** - 流动比率、速动比率、市净率、盈利稳定性
        
        👥 **管理治理** - 分析师推荐、新闻情绪、信息透明度、治理结构
        
        **评分系统:**
        - 每模块满分10分，总分50分
        - 80%+: 强烈买入 | 70-80%: 买入 | 60-70%: 持有
        - 40-60%: 卖出 | <40%: 强烈卖出
        """)
    
    # 美股支持说明
    with st.expander("🇺🇸 支持的股票", expanded=False):
        st.markdown("""
        **当前仅支持美股:**
        - 🇺🇸 **美股**: AAPL, MSFT, GOOGL, TSLA, NVDA, META, AMZN 等
        
        **格式要求:**
        - 1-5位英文字母
        - 例如: `AAPL,MSFT,GOOGL`
        
        **数据来源:**
        - Finnhub API
        - 包含财务指标、分析师推荐、新闻数据
        """)
    
    # 股票代码输入
    tickers_input = st.text_input(
        "美股代码 (逗号分隔)",
        value="RXRX,CRCL,CRWV,SBET,NBIS,COIN",
        help="输入要分析的美股代码，多个代码用逗号分隔"
    )
    
    # 分析选项
    st.subheader("🔧 分析选项")
    analysis_mode = st.radio(
        "分析模式",
        ["单股详细分析", "多股对比分析"],
        help="选择分析模式"
    )
    
    show_detailed_report = st.checkbox("显示详细分析报告", value=False)
    show_score_chart = st.checkbox("显示评分图表", value=True)
    
    # 缓存管理（简化版，因为不依赖iTick）
    st.subheader("🗄️ 数据管理")
    if st.button("清除分析缓存", help="清除基本面分析的临时数据"):
        # 清除会话状态
        for key in list(st.session_state.keys()):
            if key.startswith('analysis_'):
                del st.session_state[key]
        st.success("✅ 分析缓存已清除")


def main():
    """
    主函数
    """
    # 解析股票代码
    if tickers_input:
        tickers = [ticker.strip().upper() for ticker in tickers_input.split(",") if ticker.strip()]
        
        # 验证所有股票代码
        invalid_tickers = []
        valid_tickers = []
        
        for ticker in tickers:
            is_valid, error_msg = validate_us_stock_ticker(ticker)
            if is_valid:
                valid_tickers.append(ticker)
            else:
                invalid_tickers.append((ticker, error_msg))
        
        # 显示验证结果
        if valid_tickers:
            st.success(f"✅ 有效美股代码: {', '.join(valid_tickers)}")
        
        if invalid_tickers:
            st.error("❌ 无效的股票代码:")
            for ticker, error in invalid_tickers:
                st.write(f"• {ticker}: {error}")
            
        tickers = valid_tickers  # 只使用有效的股票代码
    else:
        st.error("请输入美股代码")
        return
    
    # 检查API密钥
    if not api_key or api_key == "YOUR_FREE_KEY":
        st.error("❌ 未配置 Finnhub API 密钥，无法进行基本面分析")
        st.info("请在 .env 文件中设置 FINNHUB_API_KEY")
        return
    
    # 运行分析按钮
    if st.button("🚀 开始基本面分析", type="primary", use_container_width=True):
        st.markdown("---")
        
        if analysis_mode == "单股详细分析":
            # 单股分析模式
            for i, ticker in enumerate(tickers):
                with st.container():
                    st.header(f"📊 {ticker} 基本面分析")
                    
                    # 创建进度条
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        status_text.text(f"🔍 正在分析 {ticker} 的基本面...")
                        progress_bar.progress(20)
                        
                        # 执行基本面分析
                        analyzer = FinnhubFundamentalAnalyzer()
                        result = analyzer.analyze_stock(ticker)
                        
                        progress_bar.progress(100)
                        status_text.text("✅ 分析完成！")
                        
                        # 显示分析结果
                        display_fundamental_summary(result)
                        
                        # 评分图表
                        if show_score_chart:
                            st.subheader("📈 评分图表")
                            chart = create_score_chart(result)
                            st.plotly_chart(chart, use_container_width=True)
                        
                        # 详细模块分析
                        display_detailed_modules(result)
                        
                        # 投资建议
                        display_investment_recommendation(result)
                        
                        # 详细分析报告
                        if show_detailed_report:
                            st.subheader("📋 详细分析报告")
                            with st.expander("完整分析报告", expanded=False):
                                report = generate_analysis_report(result)
                                st.text(report)
                        
                        # 清理进度显示
                        time.sleep(1)
                        progress_bar.empty()
                        status_text.empty()
                        
                    except Exception as e:
                        progress_bar.empty()
                        status_text.empty()
                        st.error(f"❌ 分析 {ticker} 时出错: {str(e)}")
                        
                        # 错误详情
                        with st.expander("错误详情"):
                            st.write(f"错误类型: {type(e).__name__}")
                            st.write(f"错误信息: {str(e)}")
                            
                            # 常见问题解决方案
                            st.info("""
                            **可能的解决方案:**
                            • 检查股票代码是否正确
                            • 确认 Finnhub API 密钥有效
                            • 检查网络连接
                            • 稍后重试（可能是API限制）
                            """)
                    
                    # 分隔符
                    if i < len(tickers) - 1:
                        st.markdown("---")
                    
                    # 添加延迟避免API频率限制
                    if len(tickers) > 1 and i < len(tickers) - 1:
                        time.sleep(2)
        
        else:
            # 多股对比分析模式
            st.header("📊 多股基本面对比分析")
            
            # 创建进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔍 正在进行多股对比分析...")
                progress_bar.progress(10)
                
                # 批量分析
                results = analyze_multiple_stocks(tickers)
                
                if not results:
                    st.error("❌ 未能获取任何分析结果")
                    return
                
                progress_bar.progress(80)
                status_text.text("📊 生成对比结果...")
                
                # 按评分排序
                sorted_results = sorted(results.items(), key=lambda x: x[1].total_score, reverse=True)
                
                # 对比表格
                st.subheader("📋 综合评分排名")
                
                # 创建对比数据
                comparison_data = []
                for rank, (ticker, result) in enumerate(sorted_results, 1):
                    comparison_data.append({
                        '排名': rank,
                        '股票代码': ticker,
                        '公司名称': result.company_name,
                        '综合评分': f"{result.total_score:.1f}/50",
                        '百分比': f"{result.overall_percentage:.1f}%",
                        '投资建议': result.investment_signal.value,
                        '信心度': f"{result.confidence:.1f}%",
                        '公司类型': result.company_type.value
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True)
                
                # 对比图表
                if show_score_chart and len(results) > 1:
                    st.subheader("📈 多股对比雷达图")
                    comparison_chart = create_comparison_chart(results)
                    if comparison_chart:
                        st.plotly_chart(comparison_chart, use_container_width=True)
                
                # 投资组合建议
                st.subheader("💼 投资组合建议")
                
                strong_buys = [ticker for ticker, result in results.items() 
                              if result.investment_signal == InvestmentSignal.STRONG_BUY]
                buys = [ticker for ticker, result in results.items() 
                       if result.investment_signal == InvestmentSignal.BUY]
                holds = [ticker for ticker, result in results.items() 
                        if result.investment_signal == InvestmentSignal.HOLD]
                sells = [ticker for ticker, result in results.items() 
                        if result.investment_signal in [InvestmentSignal.SELL, InvestmentSignal.STRONG_SELL]]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if strong_buys:
                        st.success("🚀 核心持仓")
                        for ticker in strong_buys:
                            st.write(f"• {ticker}")
                    else:
                        st.info("无强烈买入推荐")
                
                with col2:
                    if buys:
                        st.success("🟢 配置建议")
                        for ticker in buys:
                            st.write(f"• {ticker}")
                    else:
                        st.info("无买入推荐")
                
                with col3:
                    if holds:
                        st.warning("🟡 观察标的")
                        for ticker in holds:
                            st.write(f"• {ticker}")
                    else:
                        st.info("无持有建议")
                
                with col4:
                    if sells:
                        st.error("🔴 规避风险")
                        for ticker in sells:
                            st.write(f"• {ticker}")
                    else:
                        st.info("无卖出建议")
                
                # 详细分析报告
                if show_detailed_report:
                    st.subheader("📋 各股详细分析")
                    
                    for ticker, result in sorted_results:
                        with st.expander(f"{ticker} - {result.company_name}"):
                            # 简化的详细信息
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**综合评分:** {result.total_score:.1f}/50")
                                st.write(f"**投资建议:** {result.investment_signal.value}")
                                st.write(f"**信心度:** {result.confidence:.1f}%")
                            
                            with col2:
                                st.write(f"**公司类型:** {result.company_type.value}")
                                # 显示最强模块
                                modules = [
                                    ("经营质量", result.operating_quality.score),
                                    ("盈利效率", result.profitability_efficiency.score),
                                    ("成长地位", result.growth_market_position.score),
                                    ("财务风险", result.financial_risk.score),
                                    ("管理治理", result.management_governance.score)
                                ]
                                best_module = max(modules, key=lambda x: x[1])
                                st.write(f"**最强模块:** {best_module[0]} ({best_module[1]:.1f}/10)")
                
                progress_bar.progress(100)
                status_text.text("✅ 对比分析完成！")
                
                # 清理进度显示
                time.sleep(1)
                progress_bar.empty()
                status_text.empty()
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ 多股对比分析出错: {str(e)}")
                
                with st.expander("错误详情"):
                    st.write(f"错误类型: {type(e).__name__}")
                    st.write(f"错误信息: {str(e)}")


if __name__ == "__main__":
    main()