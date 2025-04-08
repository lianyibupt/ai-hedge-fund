import streamlit as st
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from main import run_hedge_fund, ANALYST_ORDER, LLM_ORDER, get_model_info
import json

# 页面标题
st.set_page_config(page_title="AI对冲基金交易系统", layout="wide")
st.title("🏦 AI对冲基金交易系统")

# 侧边栏参数设置
with st.sidebar:
    st.header("参数设置")
    
    # 股票代码输入
    tickers = st.text_input(
        "股票代码(逗号分隔)", 
        value="NBIS,SMCI,RXRX,CLSK",
        help="输入要分析的股票代码，多个代码用逗号分隔"
    )
    
    # 日期范围选择
    end_date = st.date_input(
        "结束日期", 
        datetime.now(),
        help="选择分析结束日期"
    )
    start_date = st.date_input(
        "开始日期", 
        end_date - relativedelta(months=3),
        help="选择分析开始日期"
    )
    
    # 初始资金设置
    initial_cash = st.number_input(
        "初始资金($)", 
        value=100000.0,
        min_value=1000.0,
        step=1000.0
    )
    
    # 保证金要求
    margin_requirement = st.number_input(
        "保证金要求(%)", 
        value=0.0,
        min_value=0.0,
        max_value=100.0,
        step=0.1
    )
    
    # 是否显示推理过程
    show_reasoning = st.checkbox("显示分析推理过程")

# 主界面
col1, col2 = st.columns(2)

with col1:
    # 分析师选择
    st.subheader("选择分析师")
    analyst_options = [display for display, value in ANALYST_ORDER]
    selected_analysts = st.multiselect(
        "选择AI分析师",
        options=analyst_options,
        default=[analyst_options[0], analyst_options[1]],
        help="选择要使用的AI分析师"
    )
    
    # 获取实际的值
    selected_analyst_values = [
        value for display, value in ANALYST_ORDER 
        if display in selected_analysts
    ]

with col2:
    # LLM模型选择
    st.subheader("选择LLM模型")
    model_options = [display for display, value, _ in LLM_ORDER]
    model_choice = st.selectbox(
        "选择LLM模型",
        options=model_options,
        index=0,
        help="选择要使用的LLM模型"
    )
    
    # 获取实际的值
    model_value = next(
        value for display, value, _ in LLM_ORDER 
        if display == model_choice
    )

# 运行按钮
if st.button("运行对冲基金", type="primary"):
    with st.spinner("正在运行分析..."):
        try:
            # 准备参数
            portfolio = {
                "cash": float(initial_cash),
                "margin_requirement": float(margin_requirement),
                "margin_used": 0.0,
                "positions": {
                    ticker.strip(): {
                        "long": 0,
                        "short": 0,
                        "long_cost_basis": 0.0,
                        "short_cost_basis": 0.0,
                        "short_margin_used": 0.0,
                    } for ticker in tickers.split(",") if ticker.strip()
                },
                "realized_gains": {
                    ticker.strip(): {
                        "long": 0.0,
                        "short": 0.0,
                    } for ticker in tickers.split(",") if ticker.strip()
                }
            }
            
            # 获取模型提供商
            model_info = get_model_info(model_value)
            model_provider = model_info.provider.value if model_info else "Unknown"
            
            # 运行对冲基金
            result = run_hedge_fund(
                tickers=[t.strip() for t in tickers.split(",") if t.strip()],
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                portfolio=portfolio,
                show_reasoning=show_reasoning,
                selected_analysts=selected_analyst_values,
                model_name=model_value,
                model_provider=model_provider,
            )
            
            # 显示结果
            st.success("分析完成!")
            
            st.subheader("交易决策")
            st.json(result["decisions"])
            
            st.subheader("分析师信号")
            st.json(result["analyst_signals"])
            
            # 显示详细财务数据和分析依据
            st.subheader("详细财务分析")
            for ticker in result["analysis_data"]:
                with st.expander(f"📊 {ticker} 详细分析", expanded=False):
                    tab1, tab2, tab3 = st.tabs(["财务指标", "估值分析", "分析师依据"])
                    
                    with tab1:
                        if result["analysis_data"][ticker]["fundamentals"]:
                            st.write("#### 基础财务指标")
                            fundamentals = result["analysis_data"][ticker]["fundamentals"]
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("ROE", f"{fundamentals.get('return_on_equity', 0)*100:.1f}%")
                            with col2:
                                st.metric("资产负债率", f"{fundamentals.get('debt_to_equity', 0)*100:.1f}%")
                            with col3:
                                st.metric("营业利润率", f"{fundamentals.get('operating_margin', 0)*100:.1f}%")
                            
                            st.write("#### 历史财务数据")
                            st.dataframe(fundamentals.get("historical_data", []))
                    
                    with tab2:
                        if result["analysis_data"][ticker]["valuation"]:
                            valuation = result["analysis_data"][ticker]["valuation"]
                            st.write("#### 估值指标")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("内在价值", f"${valuation.get('intrinsic_value', 0):,.2f}")
                            with col2:
                                st.metric("安全边际", f"{valuation.get('margin_of_safety', 0)*100:.1f}%")
                            
                            st.write("#### 估值假设")
                            st.json(valuation.get("assumptions", {}))
                    
                    with tab3:
                        if ticker in result["analyst_signals"]:
                            for analyst, signal in result["analyst_signals"][ticker].items():
                                with st.expander(f"{analyst.replace('_', ' ').title()} 分析"):
                                    st.write(f"**信号**: {signal['signal']}")
                                    st.write(f"**置信度**: {signal['confidence']}%")
                                    st.write("**分析依据**:")
                                    st.write(signal["reasoning"])
            
        except Exception as e:
            st.error(f"运行失败: {str(e)}")