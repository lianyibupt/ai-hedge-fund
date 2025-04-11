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
        value="HK.00700,HK.03690,HK.09988,HK.02020,HK.00941",
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
            
            # 交易决策表格
            st.subheader("交易决策")
            decisions_md = "| 股票代码 | 操作 | 数量 | 价格 | 理由 |\n|---------|------|------|------|------|\n"
            for ticker, decision in result["decisions"].items():
                price = decision.get('price', 'N/A')
                price_str = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)
                decisions_md += f"| {ticker} | {decision['action']} | {decision.get('quantity', 'N/A')} | {price_str} | {decision['reason']} |\n"
            st.markdown(decisions_md)
            
            # 分析师信号表格
            st.subheader("分析师信号")
            for ticker in result["analyst_signals"]:
                signals_md = f"### {ticker}\n| 分析师 | 信号 | 置信度 | 关键依据 |\n|--------|------|--------|----------|\n"
                for analyst, signal in result["analyst_signals"][ticker].items():
                    confidence = signal['confidence']
                    confidence_str = f"{confidence}%" if isinstance(confidence, (int, float)) else str(confidence)
                    signals_md += f"| {analyst.replace('_', ' ').title()} | {signal['signal']} | {confidence_str} | {signal['reasoning'].split('.')[0]}... |\n"
                st.markdown(signals_md)
            
        except Exception as e:
            st.error(f"运行失败: {str(e)}")