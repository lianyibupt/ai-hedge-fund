import streamlit as st
import sys
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加src目录到Python路径
sys.path.append('/Users/bytedance/Documents/code/ai-hedge-fund/src')

from tools.api import get_prices, prices_to_df, get_financial_metrics, cleanup_cache, get_cache_stats
from data.cache import get_cache
from data.database import get_database_manager
from utils.personal_indicators import generate_comprehensive_signal
import uuid

# 页面配置
st.set_page_config(
    page_title="个性化交易分析系统", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 获取数据库管理器和缓存实例
db_manager = get_database_manager()
cache_instance = get_cache()

# 生成会话ID
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# CSS样式
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}
.bullish { color: #00c851; font-weight: bold; }
.bearish { color: #ff4444; font-weight: bold; }
.neutral { color: #ffbb33; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 主标题
st.title("🎯 个性化交易分析系统")
st.markdown("基于MACD + RSI + 布林带 + 成交量的技术分析")

# 侧边栏参数设置
with st.sidebar:
    st.header("📊 分析参数")
    
    # 股票代码输入
    tickers_input = st.text_input(
        "股票代码 (逗号分隔)",
        value="ZETA,RXRX,TUYA,BEKE,SBET",
        help="输入要分析的股票代码，多个代码用逗号分隔。支持美股、港股等"
    )
    
    # 日期范围选择
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "开始日期", 
            datetime.now() - relativedelta(months=1),
            help="选择分析开始日期"
        )
    with col2:
        end_date = st.date_input(
            "结束日期", 
            datetime.now(),
            help="选择分析结束日期"
        )
    
    # 高级选项
    st.subheader("🔧 高级选项")
    show_detailed_indicators = st.checkbox("显示详细技术指标", value=False)
    show_historical_data = st.checkbox("显示历史数据", value=False)
    show_query_history = st.checkbox("显示查询历史", value=False)
    show_cache_stats = st.checkbox("显示缓存统计", value=False)
    auto_refresh = st.checkbox("自动刷新", value=False)
    
    if auto_refresh:
        refresh_interval = st.selectbox(
            "刷新间隔",
            options=[30, 60, 300, 600],
            format_func=lambda x: f"{x}秒",
            index=1
        )
    
    # 数据库管理
    st.subheader("🗄️ 数据管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("清理过期缓存", help="清除过期的API缓存数据"):
            # 清理内存缓存
            expired_count = cache_instance.clear_expired_cache()
            # 清理数据库缓存
            cleanup_cache()
            st.success(f"过期缓存已清理，清除了 {expired_count} 个过期条目")
    
    with col2:
        if st.button("刷新缓存统计", help="重新计算缓存统计数据"):
            st.rerun()
    
    # 缓存统计信息
    if show_cache_stats:
        st.subheader("📈 缓存统计")
        with st.expander("缓存详情", expanded=True):
            # 获取内存缓存统计
            memory_cache_stats = cache_instance.get_cache_stats()
            
            # 显示内存缓存统计
            if memory_cache_stats:
                st.markdown("**内存缓存统计:**")
                
                # 总体统计
                summary = memory_cache_stats.get('cache_summary', {})
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("缓存股票数量", summary.get('total_tickers', 0))
                with col2:
                    st.metric("总缓存条目", summary.get('total_cache_entries', 0))
                with col3:
                    st.metric("新鲜条目", summary.get('fresh_entries', 0))
                
                # 价格缓存详情
                price_cache = memory_cache_stats.get('price_cache', {})
                st.markdown("**价格缓存:**")
                pcol1, pcol2, pcol3 = st.columns(3)
                with pcol1:
                    st.write(f"- 股票数量: {price_cache.get('tickers_count', 0)}")
                with pcol2:
                    st.write(f"- 日期条目: {price_cache.get('total_date_entries', 0)}")
                with pcol3:
                    st.write(f"- 新鲜条目: {price_cache.get('fresh_entries', 0)}")
                
                # 财务缓存详情
                financial_cache = memory_cache_stats.get('financial_cache', {})
                st.markdown("**财务缓存:**")
                fcol1, fcol2, fcol3 = st.columns(3)
                with fcol1:
                    st.write(f"- 股票数量: {financial_cache.get('tickers_count', 0)}")
                with fcol2:
                    st.write(f"- 期间条目: {financial_cache.get('total_period_entries', 0)}")
                with fcol3:
                    st.write(f"- 新鲜条目: {financial_cache.get('fresh_entries', 0)}")
            
            # 获取数据库缓存统计
            st.markdown("---")
            st.markdown("**数据库缓存统计:**")
            db_cache_stats = get_cache_stats()
            if db_cache_stats:
                # 价格缓存统计
                if 'price_cache' in db_cache_stats:
                    price_cache = db_cache_stats['price_cache']
                    st.write("**数据库价格缓存:**")
                    st.write(f"- 总记录数: {price_cache.get('total_records', 0)}")
                    st.write(f"- 股票数量: {price_cache.get('unique_tickers', 0)}")
                    st.write(f"- 有效记录: {price_cache.get('valid_records', 0)}")
                
                # 财务缓存统计
                if 'financial_cache' in db_cache_stats:
                    financial_cache = db_cache_stats['financial_cache']
                    st.write("**数据库财务缓存:**")
                    st.write(f"- 总记录数: {financial_cache.get('total_records', 0)}")
                    st.write(f"- 股票数量: {financial_cache.get('unique_tickers', 0)}")
                    st.write(f"- 有效记录: {financial_cache.get('valid_records', 0)}")
                
                # 查询记录统计
                if 'query_records' in db_cache_stats:
                    query_records = db_cache_stats['query_records']
                    st.write("**查询记录:**")
                    st.write(f"- 总查询数: {query_records.get('total_queries', 0)}")
                    st.write(f"- 查询天数: {query_records.get('query_days', 0)}")
            else:
                st.info("暂无数据库缓存统计数据")


def analyze_stock_simple(ticker: str, start_date: str, end_date: str, query_record_id: int = None):
    """
    简化版股票分析 - 为Streamlit优化，支持数据库记录
    """
    # 获取扩展的历史数据用于技术分析
    extended_start = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=90)).strftime("%Y-%m-%d")
    
    # 创建进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text(f"⏳ 获取 {ticker} 价格数据...")
        progress_bar.progress(20)
        
        prices = get_prices(ticker, extended_start, end_date)
        
        if not prices:
            return None
        
        # 转换为DataFrame
        prices_df = prices_to_df(prices)
        
        if len(prices_df) < 30:
            st.error(f"❌ {ticker}数据不足（仅{len(prices_df)}天），需要至少30天数据")
            return None
        
        progress_bar.progress(50)
        status_text.text(f"🔍 开始技术分析...")
        
        # 生成技术分析信号
        analysis_result = generate_comprehensive_signal(prices_df)
        
        progress_bar.progress(80)
        status_text.text(f"💰 获取财务指标...")
        
        # 获取基本财务信息（可选，失败时不影响技术分析）
        pe_ratio = None
        pb_ratio = None
        try:
            financial_metrics = get_financial_metrics(ticker, end_date)
            if financial_metrics:
                pe_ratio = financial_metrics[0].price_to_earnings_ratio
                pb_ratio = financial_metrics[0].price_to_book_ratio
        except Exception as e:
            st.warning(f"⚠️ 财务指标获取失败: {str(e)}")
        
        progress_bar.progress(100)
        status_text.text("✅ 分析完成！")
        
        # 组装结果
        result = {
            'ticker': ticker,
            'current_price': prices_df['close'].iloc[-1],
            'analysis': analysis_result,
            'financial_metrics': {
                'pe_ratio': pe_ratio,
                'pb_ratio': pb_ratio
            },
            'data_days': len(prices_df),
            'prices_df': prices_df
        }
        
        # 保存分析结果到数据库（如果有查询记录ID）
        if query_record_id:
            try:
                db_manager.save_analysis_result(query_record_id, result)
            except Exception as e:
                st.warning(f"⚠️ 保存分析结果失败: {str(e)}")
        
        # 清理进度显示
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
        return result
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ 分析{ticker}时出错: {str(e)}")
        return None


def generate_trading_recommendation(analysis_result):
    """
    生成交易建议
    """
    if not analysis_result:
        return {"recommendation": "数据不足，无法生成建议", "action": "无操作", "reason": "", "confidence": 0}
    
    signal = analysis_result['analysis']['signal']
    confidence = analysis_result['analysis']['confidence']
    reason = analysis_result['analysis']['reason']
    
    # 生成建议
    if signal == '看涨' and confidence >= 60:
        recommendation = f"🟢 买入建议"
        action = "考虑买入"
    elif signal == '看跌' and confidence >= 60:
        recommendation = f"🔴 卖出建议"
        action = "考虑卖出"
    else:
        recommendation = f"🟡 持有建议"
        action = "继续观察"
    
    return {
        'recommendation': recommendation,
        'action': action,
        'reason': reason,
        'confidence': confidence
    }


def create_price_chart(prices_df, ticker, analysis):
    """
    创建价格图表
    """
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{ticker} 股价走势', 'MACD', 'RSI', '成交量'),
        row_heights=[0.5, 0.2, 0.15, 0.15]
    )
    
    # 主图：价格和布林带
    fig.add_trace(
        go.Candlestick(
            x=prices_df.index,
            open=prices_df['open'],
            high=prices_df['high'],
            low=prices_df['low'],
            close=prices_df['close'],
            name='价格'
        ),
        row=1, col=1
    )
    
    # 计算布林带
    if 'bollinger' in analysis['details']:
        boll_details = analysis['details']['bollinger']
        # 这里需要完整的布林带数据，简化处理
        fig.add_hline(
            y=boll_details['current_upper'],
            line_dash="dash",
            line_color="red",
            annotation_text="布林上轨",
            row=1, col=1
        )
        fig.add_hline(
            y=boll_details['current_middle'],
            line_dash="dash", 
            line_color="blue",
            annotation_text="布林中轨",
            row=1, col=1
        )
        fig.add_hline(
            y=boll_details['current_lower'],
            line_dash="dash",
            line_color="green", 
            annotation_text="布林下轨",
            row=1, col=1
        )
    
    # MACD图
    if 'raw_data' in analysis and 'macd_data' in analysis['raw_data']:
        macd_data = analysis['raw_data']['macd_data']
        recent_dates = prices_df.index[-len(macd_data['dif']):]
        
        fig.add_trace(
            go.Scatter(x=recent_dates, y=macd_data['dif'], name='DIF', line=dict(color='blue')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=recent_dates, y=macd_data['dea'], name='DEA', line=dict(color='red')),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(x=recent_dates, y=macd_data['macd'], name='MACD', marker_color='green'),
            row=2, col=1
        )
    
    # RSI图
    if 'raw_data' in analysis and 'rsi_data' in analysis['raw_data']:
        rsi_data = analysis['raw_data']['rsi_data']
        recent_dates = prices_df.index[-len(rsi_data):]
        
        fig.add_trace(
            go.Scatter(x=recent_dates, y=rsi_data, name='RSI', line=dict(color='purple')),
            row=3, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超买线", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超卖线", row=3, col=1)
    
    # 成交量图
    fig.add_trace(
        go.Bar(
            x=prices_df.index,
            y=prices_df['volume'],
            name='成交量',
            marker_color='lightblue'
        ),
        row=4, col=1
    )
    
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text=f"{ticker} 技术分析图表"
    )
    
    return fig


def display_detailed_indicators(analysis):
    """
    显示详细技术指标
    """
    st.subheader("📊 详细技术指标数据")
    
    # 创建四列布局
    col1, col2, col3, col4 = st.columns(4)
    
    # MACD详细数据
    with col1:
        st.markdown("### 📈 MACD指标")
        macd_details = analysis['details']['macd']
        
        st.metric("当前DIF", f"{macd_details['current_dif']:.4f}")
        st.metric("当前DEA", f"{macd_details['current_dea']:.4f}")
        st.metric("MACD柱状图", f"{macd_details['macd_histogram']:.4f}")
        
        st.write(f"**DIF趋势:** {macd_details['dif_trend']}")
        st.write(f"**DIF在0轴上方:** {'是' if macd_details['dif_above_zero'] else '否'}")
        st.write(f"**金叉:** {'是' if macd_details['is_golden_cross'] else '否'}")
        st.write(f"**死叉:** {'是' if macd_details['is_death_cross'] else '否'}")
    
    # RSI详细数据
    with col2:
        st.markdown("### 📊 RSI指标")
        rsi_details = analysis['details']['rsi']
        
        st.metric("当前RSI", f"{rsi_details['current_rsi']:.2f}")
        st.metric("前一期RSI", f"{rsi_details['prev_rsi']:.2f}")
        
        st.write(f"**RSI趋势:** {rsi_details['rsi_trend']}")
        st.write(f"**超买状态:** {'是' if rsi_details['is_overbought'] else '否'}")
        st.write(f"**超卖状态:** {'是' if rsi_details['is_oversold'] else '否'}")
        st.write(f"**超卖恢复:** {'是' if rsi_details['is_oversold_recovery'] else '否'}")
        st.write(f"**超买回落:** {'是' if rsi_details['is_overbought_decline'] else '否'}")
    
    # 布林带详细数据
    with col3:
        st.markdown("### 📉 布林带指标")
        boll_details = analysis['details']['bollinger']
        
        st.metric("当前价格", f"{boll_details['current_close']:.2f}")
        st.metric("上轨", f"{boll_details['current_upper']:.2f}")
        st.metric("中轨", f"{boll_details['current_middle']:.2f}")
        st.metric("下轨", f"{boll_details['current_lower']:.2f}")
        
        st.write(f"**带宽:** {boll_details['band_width']:.2f}%")
        st.write(f"**价格位置:** {boll_details['price_position']:.2%}")
        st.write(f"**中轨趋势:** {boll_details['middle_trend']}")
    
    # 成交量详细数据
    with col4:
        st.markdown("### 📊 成交量指标")
        volume_details = analysis['details']['volume']
        
        st.metric("当前成交量", f"{volume_details['current_volume']:,.0f}")
        st.metric("平均成交量", f"{volume_details['avg_volume']:,.0f}")
        st.metric("成交量比率", f"{volume_details['volume_ratio']:.2f}")
        
        st.write(f"**成交量趋势:** {volume_details['volume_trend']}")
        st.write(f"**放量:** {'是' if volume_details['is_surge'] else '否'}")


def display_historical_data(analysis):
    """
    显示历史数据
    """
    if 'raw_data' not in analysis:
        st.warning("历史数据不可用")
        return
    
    st.subheader("📈 历史数据（最近5期）")
    raw_data = analysis['raw_data']
    
    # 创建表格数据
    periods = list(range(1, 6))
    
    # 价格数据表格
    st.markdown("#### 价格数据")
    price_data = {
        '期数': periods,
        '收盘价': [f"{close:.2f}" for close in raw_data['price_data']['close']],
        '最高价': [f"{high:.2f}" for high in raw_data['price_data']['high']],
        '最低价': [f"{low:.2f}" for low in raw_data['price_data']['low']]
    }
    st.table(pd.DataFrame(price_data))
    
    # MACD数据表格
    st.markdown("#### MACD数据")
    macd_data = {
        '期数': periods,
        'DIF': [f"{dif:.4f}" for dif in raw_data['macd_data']['dif']],
        'DEA': [f"{dea:.4f}" for dea in raw_data['macd_data']['dea']],
        'MACD': [f"{macd:.4f}" for macd in raw_data['macd_data']['macd']]
    }
    st.table(pd.DataFrame(macd_data))
    
    # RSI数据表格
    st.markdown("#### RSI数据")
    rsi_data = {
        '期数': periods,
        'RSI': [f"{rsi:.2f}" for rsi in raw_data['rsi_data']]
    }
    st.table(pd.DataFrame(rsi_data))


def main():
    """
    主函数
    """
    # 解析股票代码
    if tickers_input:
        tickers = [ticker.strip().upper() for ticker in tickers_input.split(",")]
    else:
        st.error("请输入股票代码")
        return
    
    # 显示查询历史记录
    if show_query_history:
        st.subheader("📋 查询历史")
        with st.expander("历史查询记录", expanded=False):
            try:
                # 获取查询历史
                history_df = db_manager.get_query_history(limit=20)
                if not history_df.empty:
                    # 格式化显示
                    display_df = history_df[['timestamp', 'tickers', 'start_date', 'end_date', 'result_count', 'avg_confidence']].copy()
                    display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                    display_df['tickers'] = display_df['tickers'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
                    display_df.columns = ['查询时间', '股票代码', '开始日期', '结束日期', '结果数量', '平均信心度']
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.info("暂无查询历史")
            except Exception as e:
                st.error(f"获取查询历史失败: {str(e)}")
    
    # 运行分析按钮
    if st.button("🚀 开始分析", type="primary", use_container_width=True):
        st.markdown("---")
        
        # 保存查询记录到数据库
        query_record_id = None
        try:
            analysis_params = {
                'show_detailed_indicators': show_detailed_indicators,
                'show_historical_data': show_historical_data,
                'auto_refresh': auto_refresh
            }
            
            query_record_id = db_manager.save_query_record(
                tickers=tickers,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                analysis_params=analysis_params,
                session_id=st.session_state.session_id,
                user_ip=None  # Streamlit不容易获取用户IP
            )
            st.success(f"📝 查询记录已保存 (ID: {query_record_id})")
        except Exception as e:
            st.warning(f"⚠️ 保存查询记录失败: {str(e)}")
        
        # 分析每只股票
        for i, ticker in enumerate(tickers):
            with st.container():
                st.header(f"📊 {ticker} 分析结果")
                
                # 执行分析
                result = analyze_stock_simple(
                    ticker, 
                    start_date.strftime("%Y-%m-%d"), 
                    end_date.strftime("%Y-%m-%d"),
                    query_record_id
                )
                
                if result:
                    # 基本信息显示
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("当前价格", f"${result['current_price']:.2f}")
                    
                    with col2:
                        if result['financial_metrics']['pe_ratio']:
                            st.metric("P/E比率", f"{result['financial_metrics']['pe_ratio']:.2f}")
                        else:
                            st.metric("P/E比率", "N/A")
                    
                    with col3:
                        if result['financial_metrics']['pb_ratio']:
                            st.metric("P/B比率", f"{result['financial_metrics']['pb_ratio']:.2f}")
                        else:
                            st.metric("P/B比率", "N/A")
                    
                    with col4:
                        st.metric("数据天数", f"{result['data_days']}天")
                    
                    # 技术分析结果
                    analysis = result['analysis']
                    recommendation = generate_trading_recommendation(result)
                    
                    # 信号显示
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🎯 技术分析结果")
                        
                        # 总体信号
                        signal_class = "bullish" if analysis['signal'] == '看涨' else "bearish" if analysis['signal'] == '看跌' else "neutral"
                        st.markdown(f"**总体信号:** <span class='{signal_class}'>{analysis['signal']}</span>", unsafe_allow_html=True)
                        
                        st.metric("信心度", f"{analysis['confidence']}%")
                        st.write(f"**原因:** {analysis['reason']}")
                    
                    with col2:
                        st.subheader("💡 交易建议")
                        st.markdown(f"**建议:** {recommendation['recommendation']}")
                        st.write(f"**行动:** {recommendation['action']}")
                        st.write(f"**信心度:** {recommendation['confidence']}%")
                    
                    # 详细指标分析
                    st.subheader("📋 各指标信号")
                    details = analysis['details']
                    
                    indicator_cols = st.columns(4)
                    indicators = [
                        ('MACD', details['macd']),
                        ('RSI', details['rsi']),
                        ('布林带', details['bollinger']),
                        ('成交量', details['volume'])
                    ]
                    
                    for idx, (name, data) in enumerate(indicators):
                        with indicator_cols[idx]:
                            signal_class = "bullish" if data['signal'] == '看涨' else "bearish" if data['signal'] == '看跌' else "neutral"
                            st.markdown(f"**{name}**")
                            st.markdown(f"<span class='{signal_class}'>{data['signal']}</span>", unsafe_allow_html=True)
                            st.caption(data['reason'])
                    
                    # 图表显示
                    if 'prices_df' in result:
                        st.subheader("📈 技术分析图表")
                        chart = create_price_chart(result['prices_df'], ticker, analysis)
                        st.plotly_chart(chart, use_container_width=True)
                    
                    # 详细指标（可选）
                    if show_detailed_indicators:
                        display_detailed_indicators(analysis)
                    
                    # 历史数据（可选）
                    if show_historical_data:
                        display_historical_data(analysis)
                    
                    # 风险提示
                    with st.expander("⚠️ 风险提示"):
                        st.warning("""
                        • 本分析仅供参考，不构成投资建议
                        • 投资有风险，决策需谨慎  
                        • 建议结合基本面分析和市场环境
                        • 技术指标具有滞后性，不能预测未来
                        """)
                
                else:
                    st.error(f"❌ {ticker} 分析失败")
                
                # 分隔符
                if i < len(tickers) - 1:
                    st.markdown("---")
                
                # 添加延迟避免API频率限制
                if len(tickers) > 1 and i < len(tickers) - 1:
                    time.sleep(2)
    
    # 自动刷新功能
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    # 高级缓存管理功能（仅在调试模式下显示）
    if show_cache_stats:
        st.markdown("---")
        st.subheader("🔧 高级缓存管理")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("清空所有内存缓存", help="清空所有内存中的缓存数据"):
                cache_instance.clear_all_cache()
                st.success("所有内存缓存已清空")
        
        with col2:
            clear_ticker = st.text_input("清除特定股票缓存", placeholder="输入股票代码")
            if st.button("清除股票缓存") and clear_ticker:
                cache_instance.clear_ticker_cache(clear_ticker)
                st.success(f"已清除 {clear_ticker} 的所有缓存")
        
        with col3:
            st.write("缓存状态监控")
            # 实时显示缓存状态
            if st.button("刷新状态"):
                st.rerun()
    
    main()