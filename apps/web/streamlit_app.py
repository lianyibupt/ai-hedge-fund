import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# 添加必要的目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
src_dir = os.path.join(project_root, 'src')
cli_dir = os.path.join(project_root, 'apps', 'cli')
sys.path.insert(0, src_dir)
sys.path.insert(0, cli_dir)

from main import run_hedge_fund
from utils.analysts import ANALYST_ORDER, ANALYST_CONFIG
from llm.models import LLM_ORDER, get_model_info
import json

# 页面标题和样式
st.set_page_config(
    page_title="AI对冲基金交易系统",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("🏦 AI对冲基金交易系统")

# 添加一些CSS样式优化
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏参数设置
with st.sidebar:
    st.header("参数设置")
    
    # 股票代码输入
    tickers = st.text_input(
        "股票代码(逗号分隔)",
        value="RXRX,CRWV,SBET,CRCL",
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
    st.subheader("选择AI分析师")
    
    # 显示分析师详细信息 - 默认折叠，避免页面过长
    st.write("**分析师策略说明:**")
    with st.expander("📋 查看所有分析师策略详情", expanded=False):
        for display_name, analyst_key in ANALYST_ORDER:
            analyst_config = ANALYST_CONFIG[analyst_key]
            st.write(f"**{analyst_config['chinese_name']} - {display_name}**")
            st.write(f"策略描述: {analyst_config['strategy_description']}")
            st.markdown("---")
    
    # 分析师选择框
    analyst_options = [display for display, value in ANALYST_ORDER]
    selected_analysts = st.multiselect(
        "选择要使用的AI分析师:",
        options=analyst_options,
        default=[analyst_options[0], analyst_options[1]],
        help="勾选要使用的AI分析师，可以多选"
    )
    
    # 获取实际的值
    selected_analyst_values = [
        value for display, value in ANALYST_ORDER
        if display in selected_analysts
    ]
    
    # 显示已选分析师
    if selected_analysts:
        st.write("**已选择的分析师:**")
        for analyst in selected_analysts:
            analyst_key = next(value for display, value in ANALYST_ORDER if display == analyst)
            analyst_config = ANALYST_CONFIG[analyst_key]
            st.write(f"• {analyst_config['chinese_name']}")

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
            
            # 显示结果 - 使用更醒目的样式
            st.markdown('<div class="success-box">🎯 <strong>分析完成!</strong> 以下是本次分析的结果</div>', unsafe_allow_html=True)
            
            # 调试信息 - 显示返回的数据结构
            st.write("**调试信息:**")
            st.json(result)
            
            # 直接使用run_hedge_fund返回的解析后结果
            # (与gradio_app保持一致，run_hedge_fund已经返回解析后的JSON对象)
            
            # 显示缓存统计信息
            try:
                from data.cache import get_cache
                cache_stats = get_cache().get_cache_stats()
                st.write("**缓存统计信息:**")
                st.json(cache_stats)
            except Exception as e:
                st.write(f"**缓存统计获取失败:** {str(e)}")
            
            # 交易决策表格 - 使用DataFrame展示
            st.markdown('<div class="section-header">📈 交易决策汇总</div>', unsafe_allow_html=True)
            
            # 创建交易决策DataFrame
            decisions_data = []
            for ticker, decision in result["decisions"].items():
                price = decision.get('price', 'N/A')
                price_str = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)
                
                # 为操作添加颜色标识
                action = decision['action']
                if action == "buy":
                    action_display = "🟢 买入"
                elif action == "sell":
                    action_display = "🔴 卖出"
                elif action == "short":
                    action_display = "🔵 做空"
                elif action == "cover":
                    action_display = "🟡 平仓"
                else:
                    action_display = "⚪ 持有"
                
                decisions_data.append({
                    "股票代码": ticker,
                    "操作": action_display,
                    "数量": decision.get('quantity', 'N/A'),
                    "价格": price_str,
                    "理由": decision.get('reason', '暂无理由')[:100] + "..." if len(decision.get('reason', '暂无理由')) > 100 else decision.get('reason', '暂无理由')
                })
            
            if decisions_data:
                df_decisions = pd.DataFrame(decisions_data)
                st.dataframe(df_decisions, use_container_width=True, height=200)
            else:
                st.info("暂无交易决策")
            
            # 分析师信号表格 - 优化展示效果
            st.markdown('<div class="section-header">📊 分析师信号分析</div>', unsafe_allow_html=True)
            
            # 为每个股票创建分析师信号表格，使用折叠面板避免页面过长
            for ticker in result["analyst_signals"]:
                with st.expander(f"📋 {ticker} - 分析师信号详情", expanded=False):
                    signals_data = []
                    for analyst, signal in result["analyst_signals"][ticker].items():
                        confidence = signal.get('confidence', 0)
                        confidence_str = f"{confidence}%" if isinstance(confidence, (int, float)) else str(confidence)
                        
                        # 为信号添加颜色标识
                        signal_type = signal.get('signal', 'neutral')
                        if signal_type == "bullish":
                            signal_display = "🟢 看涨"
                        elif signal_type == "bearish":
                            signal_display = "🔴 看跌"
                        else:
                            signal_display = "⚪ 中性"
                        
                        # 获取分析师中文名称
                        analyst_display = analyst.replace('_agent', '')
                        analyst_config = ANALYST_CONFIG.get(analyst_display, {})
                        chinese_name = analyst_config.get('chinese_name', analyst_display.replace('_', ' ').title())
                        
                        signals_data.append({
                            "分析师": chinese_name,
                            "信号": signal_display,
                            "置信度": confidence_str,
                            "关键依据": signal.get('reasoning', '暂无分析依据')[:80] + "..." if len(signal.get('reasoning', '暂无分析依据')) > 80 else signal.get('reasoning', '暂无分析依据')
                        })
                    
                    if signals_data:
                        df_signals = pd.DataFrame(signals_data)
                        st.dataframe(df_signals, use_container_width=True, height=150)
                    else:
                        st.info(f"{ticker} 暂无分析师信号")
            
        except Exception as e:
            import traceback
            st.error(f"运行失败: {str(e)}")
            st.error(f"详细错误信息: {traceback.format_exc()}")