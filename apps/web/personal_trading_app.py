import streamlit as st
import sys
import pandas as pd
import numpy as np
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
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

from tools.api import get_prices, prices_to_df, get_financial_metrics, cleanup_cache, get_cache_stats, clear_ticker_cache
from tools.alphavantage_mcp_wrapper import get_alphavantage_wrapper
from data.cache import get_cache
from data.database import get_database_manager
from utils.personal_indicators import generate_comprehensive_signal
from analyzers.fundamental_analyzer import FinnhubFundamentalAnalyzer, analyze_multiple_stocks, generate_analysis_report
import uuid
import re

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


def detect_market_region(ticker: str) -> str:
    """
    根据股票代码检测市场区域
    
    Args:
        ticker: 股票代码
        
    Returns:
        市场区域代码 (us, hk, sh, sz, sg, jp)
    """
    ticker = ticker.strip().upper()
    
    # 港股：HK.开头或者纯数字（4-5位）
    if ticker.startswith('HK.') or (ticker.isdigit() and len(ticker) in [4, 5]):
        return 'hk'
    
    # A股：以数字开头且6位数字
    if ticker.isdigit() and len(ticker) == 6:
        # 上证：000001-199999, 600000-699999, 900000-999999
        # 深证：000000-399999
        first_digit = ticker[0]
        if first_digit in ['6', '9']:
            return 'sh'  # 上证
        elif first_digit in ['0', '3']:
            return 'sz'  # 深证
    
    # A股：.SH 或 .SZ 后缀
    if ticker.endswith('.SH'):
        return 'sh'
    elif ticker.endswith('.SZ'):
        return 'sz'
    
    # 新加坡股票：暂时按代码模式识别（待完善）
    # 日本股票：暂时按代码模式识别（待完善）
    
    # 默认为美股
    return 'us'


def format_ticker_display(ticker: str, region: str) -> str:
    """
    格式化股票代码显示
    
    Args:
        ticker: 股票代码
        region: 市场区域
        
    Returns:
        格式化后的显示字符串
    """
    region_names = {
        'us': '🇺🇸 美股',
        'hk': '🇭🇰 港股', 
        'sh': '🇨🇳 上证',
        'sz': '🇨🇳 深证',
        'sg': '🇸🇬 新加坡',
        'jp': '🇯🇵 日本'
    }
    
    return f"{ticker} ({region_names.get(region, '🌍 其他')})"


def validate_ticker_format(ticker: str) -> tuple[bool, str]:
    """
    验证股票代码格式
    
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
    
    # 港股：HK.开头 + 5位数字
    if re.match(r'^HK\.[0-9]{5}$', ticker):
        return True, ""
    
    # 港股：纯4-5位数字
    if re.match(r'^[0-9]{4,5}$', ticker):
        return True, ""
    
    # A股：6位数字
    if re.match(r'^[0-9]{6}$', ticker):
        return True, ""
    
    # A股：6位数字.SH/SZ
    if re.match(r'^[0-9]{6}\.(SH|SZ)$', ticker):
        return True, ""
    
    return False, f"不支持的股票代码格式: {ticker}"

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
st.markdown("基于技术分析 + 基本面分析的综合投资决策系统")


# 智能缓存提示
with st.expander("💡 智能缓存策略说明", expanded=False):
    st.markdown("""
    本系统采用**智能增量缓存策略**，显著提升查询效率：
    
    🔹 **同日查询优化**: 相同股票在同一天的重复查询完全命中缓存，响应时间接近0
    
    🔹 **跨日智能更新**: 查询新日期范围时，系统会：
       - 分析已有缓存数据
       - 只请求缺失的日期范围
       - 将新旧数据智能合并
    
    🔹 **缓存命中率显示**: 查询结果会显示缓存命中率，帮助您了解系统效率
    
    🔹 **多级缓存架构**: 内存缓存 → SQLite缓存 → Alpha Vantage MCP，确保最佳性能
    
    🔹 **纯美股数据**: 现在使用 Alpha Vantage MCP 服务，主要支持美股市场实时数据
    """)

# 侧边栏参数设置
with st.sidebar:
    st.header("📊 分析参数")
    
    # 股票代码输入
    st.subheader("📊 股票选择")
    
    # 市场支持信息
    with st.expander("🌍 支持的市场和格式", expanded=False):
        st.markdown("""
        **主要支持的市场:**
        - 🇺🇸 **美股** (US): AAPL, MSFT, GOOGL, TSLA - **主要支持，数据最全**
        
        **有限支持的市场:**
        - 🇭🇰 **港股** (HK): 00700, 09988 - 部分支持，主要依赖缓存数据
        - 🇨🇳 **A股** (SH/SZ): 600519, 000001 - 部分支持，主要依赖缓存数据
        
        **格式示例:**
        - 美股: `AAPL,MSFT,NVDA,TSLA`
        - 港股: `00700,09988,03690` (可能需要缓存数据)
        - A股: `600519,000001` (可能需要缓存数据)
        - 混合: `AAPL,MSFT,NVDA` (建议主要使用美股)
        
        **重要说明:**
        - 🔄 **数据源已更新**: 从 iTick API 更换为 Alpha Vantage MCP 服务
        - 🇺🇸 **美股数据**: 实时、准确、全面，包括技术分析和基本面分析
        - 🌍 **其他市场**: 依赖历史缓存数据，可能不是最新数据
        - 📊 **基本面分析**: 仅支持美股市场
        """)
    
    tickers_input = st.text_input(
        "股票代码 (逗号分隔)",
        value="RXRX,CRWV,SBET,CRCL,NBIS",
        help="输入要分析的股票代码，多个代码用逗号分隔。建议使用美股代码获得最佳数据质量"
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
    st.subheader("🔧 分析选项")
    
    # 基本面分析选项
    enable_fundamental_analysis = st.checkbox("启用基本面分析", value=False, help="基于财务指标的五模块分析")
    
    # 技术分析显示选项
    show_detailed_indicators = st.checkbox("显示详细技术指标", value=True)
    show_historical_data = st.checkbox("显示历史数据", value=False)
    
    # 其他选项
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
    
    col1, col2, col3 = st.columns(3)
    
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
    
    with col3:
        if st.button("🔄 强制刷新数据", help="清除当前股票的所有缓存，强制从 API 获取最新数据"):
            # 获取当前输入的股票代码
            current_tickers = [ticker.strip().upper() for ticker in tickers_input.split(",") if ticker.strip()]
            if current_tickers:
                total_cleared = 0
                for ticker in current_tickers:
                    cleared_count = clear_ticker_cache(ticker)
                    total_cleared += cleared_count
                st.success(f"🔄 已清除 {', '.join(current_tickers)} 的所有缓存（{total_cleared} 条记录），下次分析将获取最新数据")
            else:
                st.warning("请先输入股票代码")
    
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


def analyze_stock_simple(ticker: str, start_date: str, end_date: str, query_record_id: int = None, enable_fundamental: bool = True):
    """
    综合版股票分析 - 支持技术分析 + 基本面分析，支持多市场
    """
    # 检测股票代码市场
    region = detect_market_region(ticker)
    ticker_display = format_ticker_display(ticker, region)
    
    # 验证股票代码格式
    is_valid, error_msg = validate_ticker_format(ticker)
    if not is_valid:
        st.error(f"⚠️ {error_msg}")
        return None
    
    # 获取扩展的历史数据用于技术分析
    extended_start = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=90)).strftime("%Y-%m-%d")
    
    # 创建进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text(f"⏳ 获取 {ticker_display} 价格数据...")
        progress_bar.progress(20)
        
        # 传递市场区域参数给API
        prices = get_prices_with_region(ticker, extended_start, end_date, region)
        
        if not prices:
            error_msg = f"⚠️ 无法获取 {ticker_display} 的价格数据。可能的原因：\n"
            error_msg += f"• 股票代码 {ticker} 可能不存在或已退市\n"
            error_msg += f"• 查询日期范围可能包含未来日期\n"
            error_msg += f"• 市场 {region.upper()} 可能不被 Alpha Vantage 支持（建议使用美股代码）\n"
            error_msg += f"• 网络连接或API服务问题"
            st.error(error_msg)
            return None
        
        # 转换为DataFrame
        prices_df = prices_to_df(prices)
        
        if len(prices_df) < 30:
            st.error(f"❌ {ticker_display}数据不足（仅{len(prices_df)}天），需要至少30天数据")
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
            financial_metrics = get_financial_metrics_with_region(ticker, end_date, region)
            if financial_metrics:
                pe_ratio = financial_metrics[0].price_to_earnings_ratio
                pb_ratio = financial_metrics[0].price_to_book_ratio
        except Exception as e:
            st.warning(f"⚠️ 财务指标获取失败: {str(e)}")
        
        # 基本面分析（可选）
        fundamental_result = None
        if enable_fundamental and region == 'us':  # 目前只支持美股基本面分析
            try:
                status_text.text(f"📊 基本面分析...")
                analyzer = FinnhubFundamentalAnalyzer()
                fundamental_result = analyzer.analyze_stock(ticker)
                progress_bar.progress(95)
            except Exception as e:
                st.warning(f"⚠️ 基本面分析失败: {str(e)}")
        elif enable_fundamental and region != 'us':
            st.info(f"📊 基本面分析目前只支持美股，{format_ticker_display(ticker, region)}将跳过基本面分析")
        
        progress_bar.progress(100)
        status_text.text("✅ 分析完成！")
        
        # 组装结果 - 修复当前价格获取逻辑
        # 尝试获取实时报价作为当前价格
        try:
            # 优先使用价格数据中的最新价格
            # 由于prices_df已经按日期正序排列，最新的价格在最后
            current_price = prices_df['close'].iloc[-1] if len(prices_df) > 0 else None
            print(f"💰 当前价格: {current_price} (来自历史数据最新记录)")
            
            # 如果需要更准确的实时数据，可以调用其他API
            # 注意：这里移除了AlphaVantage的实时报价获取
        except Exception as e:
            print(f"⚠️ 获取实时报价失败，使用历史数据: {str(e)}")
            # 由于prices_df已经按日期正序排列，最新的价格在最后
            current_price = prices_df['close'].iloc[-1] if len(prices_df) > 0 else None  # 使用iloc[-1]获取最新价格
        
        result = {
            'ticker': ticker,
            'ticker_display': ticker_display,
            'region': region,
            'current_price': current_price,
            'analysis': analysis_result,
            'financial_metrics': {
                'pe_ratio': pe_ratio,
                'pb_ratio': pb_ratio
            },
            'fundamental_analysis': fundamental_result,  # 新增基本面分析结果
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
        st.error(f"❌ 分析{ticker_display}时出错: {str(e)}")
        return None


def get_prices_with_region(ticker: str, start_date: str, end_date: str, region: str):
    """
    根据市场区域获取价格数据
    """
    return get_prices(ticker, start_date, end_date, region)


def get_financial_metrics_with_region(ticker: str, end_date: str, region: str):
    """
    根据市场区域获取财务指标
    """
    return get_financial_metrics(ticker, end_date, region=region)


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
    创建价格图表，显示所有技术指标
    """
    # 严格的过滤条件，确保只显示有效交易数据
    filtered_prices_df = prices_df[
        (prices_df['volume'] > 0) & 
        (prices_df['open'].notna()) & 
        (prices_df['high'].notna()) & 
        (prices_df['low'].notna()) & 
        (prices_df['close'].notna()) &
        (prices_df['open'] > 0) & 
        (prices_df['high'] > 0) & 
        (prices_df['low'] > 0) & 
        (prices_df['close'] > 0)
    ].copy()
    
    # 确保索引是日期类型并排序
    if not filtered_prices_df.empty:
        filtered_prices_df.index = pd.to_datetime(filtered_prices_df.index, format='mixed', errors='coerce')
        filtered_prices_df = filtered_prices_df.sort_index()
    
    # 创建更复杂的子图布局来显示所有7个指标
    fig = make_subplots(
        rows=7, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(
            f'{ticker} 股价走势', 
            'MACD', 
            'RSI', 
            '布林带',
            'ROC',
            '随机指标(KDJ)',
            '威廉指标'
        ),
        row_heights=[0.15, 0.25, 0.1, 0.1, 0.1, 0.15, 0.15]
    )
    
    # 主图：价格和布林带（只在有数据时添加）
    if not filtered_prices_df.empty:
        # 添加K线图，只显示有交易的数据点
        fig.add_trace(
            go.Candlestick(
                x=filtered_prices_df.index,
                open=filtered_prices_df['open'],
                high=filtered_prices_df['high'],
                low=filtered_prices_df['low'],
                close=filtered_prices_df['close'],
                name='价格'
            ),
            row=1, col=1
        )
        
        # 添加布林带（如果存在且有效）
        if 'bollinger' in analysis.get('details', {}) and not filtered_prices_df.empty:
            boll_details = analysis['details']['bollinger']
            # 只有当布林带值有效时才添加水平线
            if pd.notna(boll_details['current_upper']) and boll_details['current_upper'] > 0:
                fig.add_hline(
                    y=boll_details['current_upper'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text="布林上轨",
                    row=1, col=1
                )
            if pd.notna(boll_details['current_middle']) and boll_details['current_middle'] > 0:
                fig.add_hline(
                    y=boll_details['current_middle'],
                    line_dash="dash", 
                    line_color="blue",
                    annotation_text="布林中轨",
                    row=1, col=1
                )
            if pd.notna(boll_details['current_lower']) and boll_details['current_lower'] > 0:
                fig.add_hline(
                    y=boll_details['current_lower'],
                    line_dash="dash",
                    line_color="green", 
                    annotation_text="布林下轨",
                    row=1, col=1
                )
    
    # MACD图
    if 'raw_data' in analysis and 'macd_data' in analysis['raw_data'] and not filtered_prices_df.empty:
        macd_data = analysis['raw_data']['macd_data']
        macd_dates = filtered_prices_df.index
        
        if len(macd_data['dif']) > 0 and len(macd_data['dea']) > 0 and len(macd_data['macd']) > 0:
            min_length = min(len(macd_data['dif']), len(macd_dates))
            if min_length > 0:
                recent_dates = macd_dates[-min_length:]
                dif_data = macd_data['dif'][-min_length:]
                dea_data = macd_data['dea'][-min_length:]
                macd_bar_data = macd_data['macd'][-min_length:]
                
                # 过滤掉NaN值和无穷大值
                valid_mask = [
                    pd.notna(dif_data[i]) and pd.notna(dea_data[i]) and pd.notna(macd_bar_data[i]) and
                    np.isfinite(dif_data[i]) and np.isfinite(dea_data[i]) and np.isfinite(macd_bar_data[i])
                    for i in range(len(dif_data))
                ]
                
                valid_count = sum(valid_mask)
                if valid_count > 1:
                    valid_dates = [recent_dates[i] for i in range(len(recent_dates)) if valid_mask[i]]
                    valid_dif = [dif_data[i] for i in range(len(dif_data)) if valid_mask[i]]
                    valid_dea = [dea_data[i] for i in range(len(dea_data)) if valid_mask[i]]
                    valid_macd = [macd_bar_data[i] for i in range(len(macd_bar_data)) if valid_mask[i]]
                    
                    fig.add_trace(
                        go.Scatter(x=valid_dates, y=valid_dif, 
                                  name='DIF', line=dict(color='blue')),
                        row=2, col=1
                    )
                    fig.add_trace(
                        go.Scatter(x=valid_dates, y=valid_dea, 
                                  name='DEA', line=dict(color='red')),
                        row=2, col=1
                    )
                    fig.add_trace(
                        go.Bar(x=valid_dates, y=valid_macd, 
                              name='MACD', marker_color='green'),
                        row=2, col=1
                    )
    
    # RSI图
    if 'raw_data' in analysis and 'rsi_data' in analysis['raw_data'] and not filtered_prices_df.empty:
        rsi_data = analysis['raw_data']['rsi_data']
        rsi_dates = filtered_prices_df.index
        
        min_length = min(len(rsi_data), len(rsi_dates))
        if min_length > 0:
            recent_dates = rsi_dates[-min_length:]
            rsi_values = rsi_data[-min_length:]
            
            valid_mask = [
                pd.notna(x) and 0 <= x <= 100 and np.isfinite(x)
                for x in rsi_values
            ]
            
            valid_count = sum(valid_mask)
            if valid_count > 1:
                valid_dates = [recent_dates[i] for i in range(len(recent_dates)) if valid_mask[i]]
                valid_rsi = [rsi_values[i] for i in range(len(rsi_values)) if valid_mask[i]]
                
                fig.add_trace(
                    go.Scatter(x=valid_dates, y=valid_rsi, 
                              name='RSI', line=dict(color='purple')),
                    row=3, col=1
                )
                fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超买线", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超卖线", row=3, col=1)
    
    # 布林带图（单独显示）
    if 'raw_data' in analysis and 'bollinger_data' in analysis['raw_data'] and not filtered_prices_df.empty:
        boll_data = analysis['raw_data']['bollinger_data']
        boll_dates = filtered_prices_df.index
        
        if len(boll_data['upper']) > 0 and len(boll_data['middle']) > 0 and len(boll_data['lower']) > 0:
            min_length = min(len(boll_data['upper']), len(boll_dates))
            if min_length > 0:
                recent_dates = boll_dates[-min_length:]
                upper_data = boll_data['upper'][-min_length:]
                middle_data = boll_data['middle'][-min_length:]
                lower_data = boll_data['lower'][-min_length:]
                
                valid_mask = [
                    pd.notna(upper_data[i]) and pd.notna(middle_data[i]) and pd.notna(lower_data[i]) and
                    np.isfinite(upper_data[i]) and np.isfinite(middle_data[i]) and np.isfinite(lower_data[i])
                    for i in range(len(upper_data))
                ]
                
                valid_count = sum(valid_mask)
                if valid_count > 1:
                    valid_dates = [recent_dates[i] for i in range(len(recent_dates)) if valid_mask[i]]
                    valid_upper = [upper_data[i] for i in range(len(upper_data)) if valid_mask[i]]
                    valid_middle = [middle_data[i] for i in range(len(middle_data)) if valid_mask[i]]
                    valid_lower = [lower_data[i] for i in range(len(lower_data)) if valid_mask[i]]
                    
                    fig.add_trace(
                        go.Scatter(x=valid_dates, y=valid_upper, 
                                  name='上轨', line=dict(color='red', dash='dash')),
                        row=4, col=1
                    )
                    fig.add_trace(
                        go.Scatter(x=valid_dates, y=valid_middle, 
                                  name='中轨', line=dict(color='blue')),
                        row=4, col=1
                    )
                    fig.add_trace(
                        go.Scatter(x=valid_dates, y=valid_lower, 
                                  name='下轨', line=dict(color='green', dash='dash')),
                        row=4, col=1
                    )
    
    # ROC图
    if 'raw_data' in analysis and 'roc_data' in analysis['raw_data'] and not filtered_prices_df.empty:
        roc_data = analysis['raw_data']['roc_data']
        roc_dates = filtered_prices_df.index
        
        min_length = min(len(roc_data), len(roc_dates))
        if min_length > 0:
            recent_dates = roc_dates[-min_length:]
            roc_values = roc_data[-min_length:]
            
            valid_mask = [
                pd.notna(x) and np.isfinite(x)
                for x in roc_values
            ]
            
            valid_count = sum(valid_mask)
            if valid_count > 1:
                valid_dates = [recent_dates[i] for i in range(len(recent_dates)) if valid_mask[i]]
                valid_roc = [roc_values[i] for i in range(len(roc_values)) if valid_mask[i]]
                
                fig.add_trace(
                    go.Scatter(x=valid_dates, y=valid_roc, 
                              name='ROC', line=dict(color='orange')),
                    row=5, col=1
                )
                fig.add_hline(y=0, line_dash="dash", line_color="gray", row=5, col=1)
    
    # 随机指标图
    if 'raw_data' in analysis and 'stochastic_data' in analysis['raw_data'] and not filtered_prices_df.empty:
        stoch_data = analysis['raw_data']['stochastic_data']
        stoch_dates = filtered_prices_df.index
        
        if len(stoch_data['k']) > 0 and len(stoch_data['d']) > 0:
            min_length = min(len(stoch_data['k']), len(stoch_dates))
            if min_length > 0:
                recent_dates = stoch_dates[-min_length:]
                k_data = stoch_data['k'][-min_length:]
                d_data = stoch_data['d'][-min_length:]
                
                valid_mask = [
                    pd.notna(k_data[i]) and pd.notna(d_data[i]) and
                    np.isfinite(k_data[i]) and np.isfinite(d_data[i])
                    for i in range(len(k_data))
                ]
                
                valid_count = sum(valid_mask)
                if valid_count > 1:
                    valid_dates = [recent_dates[i] for i in range(len(recent_dates)) if valid_mask[i]]
                    valid_k = [k_data[i] for i in range(len(k_data)) if valid_mask[i]]
                    valid_d = [d_data[i] for i in range(len(d_data)) if valid_mask[i]]
                    
                    fig.add_trace(
                        go.Scatter(x=valid_dates, y=valid_k, 
                                  name='K值', line=dict(color='red')),
                        row=6, col=1
                    )
                    fig.add_trace(
                        go.Scatter(x=valid_dates, y=valid_d, 
                                  name='D值', line=dict(color='blue')),
                        row=6, col=1
                    )
                    fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="超买", row=6, col=1)
                    fig.add_hline(y=20, line_dash="dash", line_color="green", annotation_text="超卖", row=6, col=1)
    
    # 威廉指标图
    if 'raw_data' in analysis and 'williams_r_data' in analysis['raw_data'] and not filtered_prices_df.empty:
        williams_r_data = analysis['raw_data']['williams_r_data']
        wr_dates = filtered_prices_df.index
        
        min_length = min(len(williams_r_data), len(wr_dates))
        if min_length > 0:
            recent_dates = wr_dates[-min_length:]
            wr_values = williams_r_data[-min_length:]
            
            valid_mask = [
                pd.notna(x) and np.isfinite(x)
                for x in wr_values
            ]
            
            valid_count = sum(valid_mask)
            if valid_count > 1:
                valid_dates = [recent_dates[i] for i in range(len(recent_dates)) if valid_mask[i]]
                valid_wr = [wr_values[i] for i in range(len(wr_values)) if valid_mask[i]]
                
                fig.add_trace(
                    go.Scatter(x=valid_dates, y=valid_wr, 
                              name='W%R', line=dict(color='purple')),
                    row=7, col=1
                )
                fig.add_hline(y=-20, line_dash="dash", line_color="red", annotation_text="超买", row=7, col=1)
                fig.add_hline(y=-80, line_dash="dash", line_color="green", annotation_text="超卖", row=7, col=1)
    
    # 更新图表布局
    fig.update_layout(
        height=1200,
        showlegend=True,
        title_text=f"{ticker} 技术分析图表（7个指标）",
        xaxis_rangeslider_visible=False,
    )
    
    # 更新Y轴标题
    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)
    fig.update_yaxes(title_text="布林带", row=4, col=1)
    fig.update_yaxes(title_text="ROC", row=5, col=1)
    fig.update_yaxes(title_text="KDJ", row=6, col=1)
    fig.update_yaxes(title_text="W%R", row=7, col=1)
    
    # 确保X轴只显示有数据的日期
    if not filtered_prices_df.empty:
        fig.update_xaxes(
            type='date',
            tickformat='%Y-%m-%d',
            row=7, col=1
        )
    
    return fig


def display_detailed_indicators(analysis):
    """
    显示详细技术指标（7个指标）
    """
    st.subheader("📊 详细技术指标数据（7个指标）")
    
    # 检查details字典是否存在
    if 'details' not in analysis:
        st.warning("⚠️ 数据不足，无法显示详细指标数据")
        return
    
    details = analysis['details']
    
    # 创建两行布局，每行4列，共7个指标
    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
    row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)
    
    # MACD详细数据
    with row1_col1:
        st.markdown("### 📈 MACD指标")
        macd_details = details.get('macd', {})
        
        if macd_details:
            st.metric("当前DIF", f"{macd_details.get('current_dif', 0):.4f}")
            st.metric("当前DEA", f"{macd_details.get('current_dea', 0):.4f}")
            st.metric("MACD柱状图", f"{macd_details.get('macd_histogram', 0):.4f}")
            
            st.write(f"**DIF趋势:** {macd_details.get('dif_trend', '未知')}")
            st.write(f"**DIF在0轴上方:** {'是' if macd_details.get('dif_above_zero', False) else '否'}")
            st.write(f"**金叉:** {'是' if macd_details.get('is_golden_cross', False) else '否'}")
            st.write(f"**死叉:** {'是' if macd_details.get('is_death_cross', False) else '否'}")
        else:
            st.warning("MACD数据不可用")
    
    # RSI详细数据
    with row1_col2:
        st.markdown("### 📊 RSI指标")
        rsi_details = details.get('rsi', {})
        
        if rsi_details:
            st.metric("当前RSI", f"{rsi_details.get('current_rsi', 50):.2f}")
            st.metric("前一期RSI", f"{rsi_details.get('prev_rsi', 50):.2f}")
            
            st.write(f"**RSI趋势:** {rsi_details.get('rsi_trend', '未知')}")
            st.write(f"**超买状态:** {'是' if rsi_details.get('is_overbought', False) else '否'}")
            st.write(f"**超卖状态:** {'是' if rsi_details.get('is_oversold', False) else '否'}")
            st.write(f"**超卖恢复:** {'是' if rsi_details.get('is_oversold_recovery', False) else '否'}")
            st.write(f"**超买回落:** {'是' if rsi_details.get('is_overbought_decline', False) else '否'}")
        else:
            st.warning("RSI数据不可用")
    
    # 布林带详细数据
    with row1_col3:
        st.markdown("### 📉 布林带指标")
        boll_details = details.get('bollinger', {})
        
        if boll_details:
            st.metric("当前价格", f"{boll_details.get('current_close', 0):.2f}")
            st.metric("上轨", f"{boll_details.get('current_upper', 0):.2f}")
            st.metric("中轨", f"{boll_details.get('current_middle', 0):.2f}")
            st.metric("下轨", f"{boll_details.get('current_lower', 0):.2f}")
            
            st.write(f"**带宽:** {boll_details.get('band_width', 0):.2f}%")
            st.write(f"**价格位置:** {boll_details.get('price_position', 0.5):.2%}")
            st.write(f"**中轨趋势:** {boll_details.get('middle_trend', '未知')}")
        else:
            st.warning("布林带数据不可用")
    
    # 成交量详细数据
    with row1_col4:
        st.markdown("### 📊 成交量指标")
        volume_details = details.get('volume', {})
        
        if volume_details:
            st.metric("当前成交量", f"{volume_details.get('current_volume', 0):,.0f}")
            st.metric("平均成交量", f"{volume_details.get('avg_volume', 0):,.0f}")
            st.metric("成交量比率", f"{volume_details.get('volume_ratio', 1):.2f}")
            
            st.write(f"**成交量趋势:** {volume_details.get('volume_trend', '未知')}")
            st.write(f"**放量:** {'是' if volume_details.get('is_surge', False) else '否'}")
        else:
            st.warning("成交量数据不可用")
    
    # ROC详细数据
    with row2_col1:
        st.markdown("### 📈 ROC指标")
        roc_details = details.get('roc', {})
        
        if roc_details:
            st.metric("当前ROC", f"{roc_details.get('current_roc', 0):.2f}%")
            st.metric("前一期ROC", f"{roc_details.get('prev_roc', 0):.2f}%")
            
            st.write(f"**ROC趋势:** {roc_details.get('roc_trend', '未知')}")
            st.write(f"**超买状态:** {'是' if roc_details.get('is_overbought', False) else '否'}")
            st.write(f"**超卖状态:** {'是' if roc_details.get('is_oversold', False) else '否'}")
        else:
            st.warning("ROC数据不可用")
    
    # 随机指标详细数据
    with row2_col2:
        st.markdown("### 📊 随机指标(KDJ)")
        stoch_details = details.get('stochastic', {})
        
        if stoch_details:
            st.metric("当前K值", f"{stoch_details.get('current_k', 50):.2f}")
            st.metric("当前D值", f"{stoch_details.get('current_d', 50):.2f}")
            
            st.write(f"**K-D交叉:** {stoch_details.get('k_d_cross', '无交叉')}")
            st.write(f"**超买状态:** {'是' if stoch_details.get('is_overbought', False) else '否'}")
            st.write(f"**超卖状态:** {'是' if stoch_details.get('is_oversold', False) else '否'}")
        else:
            st.warning("随机指标数据不可用")
    
    # 威廉指标详细数据
    with row2_col3:
        st.markdown("### 📉 威廉指标")
        williams_r_details = details.get('williams_r', {})
        
        if williams_r_details:
            st.metric("当前W%R", f"{williams_r_details.get('current_wr', -50):.2f}")
            st.metric("前一期W%R", f"{williams_r_details.get('prev_wr', -50):.2f}")
            
            st.write(f"**威廉指标趋势:** {williams_r_details.get('wr_trend', '未知')}")
            st.write(f"**超买状态:** {'是' if williams_r_details.get('is_overbought', False) else '否'}")
            st.write(f"**超卖状态:** {'是' if williams_r_details.get('is_oversold', False) else '否'}")
        else:
            st.warning("威廉指标数据不可用")

    # 指标权重说明
    with row2_col4:
        st.markdown("### ⚖️ 指标权重")
        st.write("**综合信号权重分配:**")
        st.write("- MACD: 20%")
        st.write("- RSI: 15%")
        st.write("- 布林带: 15%")
        st.write("- 成交量: 10%")
        st.write("- ROC: 15%")
        st.write("- 随机指标: 15%")
        st.write("- 威廉指标: 10%")
        
        st.write("**信号生成规则:**")
        st.write("- 看涨信号: 权重总和 ≥ 50%")
        st.write("- 看跌信号: 权重总和 ≥ 50%")
        st.write("- 中性信号: 权重总和 < 50%")


def display_fundamental_analysis(fundamental_result):
    """
    显示基本面分析结果
    """
    if not fundamental_result:
        return
    
    st.subheader("📈 基本面分析结果")
    
    # 综合评分和投资建议
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("综合评分", f"{fundamental_result.total_score:.1f}/50.0")
        st.caption(f"综合百分比: {fundamental_result.overall_percentage:.1f}%")
    
    with col2:
        # 投资信号颜色显示
        signal_colors = {
            "强烈买入": "#00c851",
            "买入": "#00c851", 
            "持有": "#ffbb33",
            "卖出": "#ff4444",
            "强烈卖出": "#ff4444"
        }
        signal_value = fundamental_result.investment_signal.value
        color = signal_colors.get(signal_value, "#666666")
        st.markdown(f"**投资建议:** <span style='color: {color}; font-weight: bold;'>{signal_value}</span>", 
                   unsafe_allow_html=True)
    
    with col3:
        st.metric("信心度", f"{fundamental_result.confidence:.1f}%")
        st.caption(f"公司类型: {fundamental_result.company_type.value}")
    
    # 五大模块评分
    st.subheader("📊 五大模块评分")
    
    modules = [
        ("🏢 经营质量", fundamental_result.operating_quality),
        ("💰 盈利效率", fundamental_result.profitability_efficiency),
        ("🚀 成长地位", fundamental_result.growth_market_position),
        ("⚠️ 财务风险", fundamental_result.financial_risk),
        ("👥 管理治理", fundamental_result.management_governance)
    ]
    
    # 分两行显示
    for i in range(0, len(modules), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(modules):
                name, score_obj = modules[i + j]
                with cols[j]:
                    st.metric(name, f"{score_obj.score:.1f}/10.0")
                    st.caption(f"{score_obj.percentage:.1f}%")
                    
                    # 显示前3个详情
                    with st.expander("查看详情"):
                        for detail in score_obj.details[:3]:
                            st.write(f"• {detail}")
    
    # 详细分析报告
    with st.expander("📝 详细分析报告", expanded=False):
        report = generate_analysis_report(fundamental_result)
        st.text(report)


def display_historical_data(analysis):
    """
    显示历史数据（包含所有7个指标）
    """
    if 'raw_data' not in analysis:
        st.warning("历史数据不可用")
        return
    
    st.subheader("📈 历史数据（最近5期，7个指标）")
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
    
    # ROC数据表格
    st.markdown("#### ROC数据")
    roc_data = {
        '期数': periods,
        'ROC': [f"{roc:.2f}%" for roc in raw_data['roc_data']]
    }
    st.table(pd.DataFrame(roc_data))
    
    # 随机指标数据表格
    st.markdown("#### 随机指标(KDJ)数据")
    stoch_data = {
        '期数': periods,
        'K值': [f"{k:.2f}" for k in raw_data['stochastic_data']['k']],
        'D值': [f"{d:.2f}" for d in raw_data['stochastic_data']['d']]
    }
    st.table(pd.DataFrame(stoch_data))
    
    # 威廉指标数据表格
    st.markdown("#### 威廉指标数据")
    williams_r_data = {
        '期数': periods,
        'W%R': [f"{wr:.2f}" for wr in raw_data['williams_r_data']]
    }
    st.table(pd.DataFrame(williams_r_data))


def main():
    """
    主函数
    """
    # 解析股票代码
    if tickers_input:
        tickers = [ticker.strip().upper() for ticker in tickers_input.split(",")]
        
        # 验证所有股票代码
        invalid_tickers = []
        valid_tickers = []
        market_info = {}
        
        for ticker in tickers:
            is_valid, error_msg = validate_ticker_format(ticker)
            if is_valid:
                region = detect_market_region(ticker)
                valid_tickers.append(ticker)
                market_info[ticker] = {
                    'region': region,
                    'display': format_ticker_display(ticker, region)
                }
            else:
                invalid_tickers.append((ticker, error_msg))
        
        # 显示验证结果
        if valid_tickers:
            st.success(f"✅ 有效股票代码: {len(valid_tickers)} 个")
            
            # 按市场分组显示
            markets = {'us': [], 'hk': [], 'sh': [], 'sz': [], 'sg': [], 'jp': []}
            for ticker in valid_tickers:
                region = market_info[ticker]['region']
                markets[region].append(ticker)
            
            # 只显示有股票的市场
            active_markets = [(k, v) for k, v in markets.items() if v]
            market_names = {
                'us': '🇺🇸 美股', 
                'hk': '🇭🇰 港股', 
                'sh': '🇨🇳 上证',
                'sz': '🇨🇳 深证',
                'sg': '🇸🇬 新加坡',
                'jp': '🇯🇵 日本'
            }
            
            if len(active_markets) <= 3:
                cols = st.columns(len(active_markets))
                for i, (market, stocks) in enumerate(active_markets):
                    with cols[i]:
                        st.write(f"**{market_names[market]}**")
                        for stock in stocks:
                            st.write(f"• {stock}")
            else:
                # 如果超过3个市场，使用列表显示
                for market, stocks in active_markets:
                    st.write(f"**{market_names[market]}**: {', '.join(stocks)}")
        
        if invalid_tickers:
            st.error("❌ 无效的股票代码:")
            for ticker, error in invalid_tickers:
                st.write(f"• {ticker}: {error}")
            
        tickers = valid_tickers  # 只使用有效的股票代码
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
                    display_df['timestamp'] = pd.to_datetime(display_df['timestamp'], format='mixed', errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
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
                'enable_fundamental_analysis': enable_fundamental_analysis,
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
                # 使用市场信息显示标题
                ticker_display = market_info.get(ticker, {}).get('display', ticker)
                st.header(f"📊 {ticker_display} 分析结果")
                
                # 执行分析
                result = analyze_stock_simple(
                    ticker, 
                    start_date.strftime("%Y-%m-%d"), 
                    end_date.strftime("%Y-%m-%d"),
                    query_record_id,
                    enable_fundamental_analysis  # 传递基本面分析选项
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
                    
                    # 基本面分析结果（如果启用）
                    if result.get('fundamental_analysis'):
                        st.markdown("---")
                        display_fundamental_analysis(result['fundamental_analysis'])
                    
                    # 详细指标分析
                    st.subheader("📋 各指标信号（7个指标）")
                    details = analysis['details']
                    
                    # 创建两行布局，第一行4个指标，第二行3个指标
                    row1_cols = st.columns(4)
                    row2_cols = st.columns(3)
                    
                    # 第一行指标
                    indicators_row1 = [
                        ('MACD', details['macd']),
                        ('RSI', details['rsi']),
                        ('布林带', details['bollinger']),
                        ('成交量', details['volume'])
                    ]
                    
                    # 第二行指标
                    indicators_row2 = [
                        ('ROC', details['roc']),
                        ('随机指标', details['stochastic']),
                        ('威廉指标', details['williams_r'])
                    ]
                    
                    # 显示第一行指标
                    for idx, (name, data) in enumerate(indicators_row1):
                        with row1_cols[idx]:
                            signal_class = "bullish" if data['signal'] == '看涨' else "bearish" if data['signal'] == '看跌' else "neutral"
                            st.markdown(f"**{name}**")
                            st.markdown(f"<span class='{signal_class}'>{data['signal']}</span>", unsafe_allow_html=True)
                            st.caption(data['reason'])
                    
                    # 显示第二行指标
                    for idx, (name, data) in enumerate(indicators_row2):
                        with row2_cols[idx]:
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