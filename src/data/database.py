"""
SQLite数据库管理模块
用于存储查询记录、API缓存和技术分析结果
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import os


class DatabaseManager:
    """SQLite数据库管理器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，默认为项目根目录下的trading_data.db
        """
        if db_path is None:
            # 默认数据库路径：项目根目录下
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "trading_data.db"
        
        self.db_path = str(db_path)
        self._ensure_database_exists()
        self._init_tables()
    
    def _ensure_database_exists(self):
        """确保数据库文件存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 允许通过列名访问
        return conn
    
    def _init_tables(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            # 查询记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    tickers TEXT NOT NULL,
                    start_date DATE,
                    end_date DATE,
                    analysis_params TEXT,  -- JSON格式存储分析参数
                    user_ip TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 技术分析结果表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_record_id INTEGER,
                    ticker TEXT NOT NULL,
                    current_price REAL,
                    signal TEXT,  -- 看涨/看跌/中性
                    confidence INTEGER,
                    reason TEXT,
                    macd_signal TEXT,
                    rsi_signal TEXT,
                    bollinger_signal TEXT,
                    volume_signal TEXT,
                    recommendation TEXT,
                    recommendation_action TEXT,
                    data_days INTEGER,
                    pe_ratio REAL,
                    pb_ratio REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_record_id) REFERENCES query_records (id)
                )
            """)
            
            # API缓存表 - 价格数据
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    date DATE NOT NULL,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    close_price REAL,
                    volume INTEGER,
                    api_source TEXT DEFAULT 'itick',
                    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    UNIQUE(ticker, date, api_source)
                )
            """)
            
            # API缓存表 - 财务指标
            conn.execute("""
                CREATE TABLE IF NOT EXISTS financial_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    report_period DATE,
                    period TEXT,  -- ttm, annual, quarterly
                    currency TEXT,
                    market_cap REAL,
                    pe_ratio REAL,
                    pb_ratio REAL,
                    ps_ratio REAL,
                    ev_ebitda REAL,
                    peg_ratio REAL,
                    roe REAL,
                    roa REAL,
                    debt_to_equity REAL,
                    current_ratio REAL,
                    quick_ratio REAL,
                    gross_margin REAL,
                    operating_margin REAL,
                    net_margin REAL,
                    api_source TEXT DEFAULT 'itick',
                    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    raw_data TEXT,  -- JSON格式存储原始数据
                    UNIQUE(ticker, report_period, period, api_source)
                )
            """)
            
            # 创建索引提高查询性能
            conn.execute("CREATE INDEX IF NOT EXISTS idx_query_records_timestamp ON query_records(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_query_records_tickers ON query_records(tickers)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_results_ticker ON analysis_results(ticker)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_cache_ticker_date ON price_cache(ticker, date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_cache_ticker ON financial_cache(ticker)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_cache_expires ON price_cache(expires_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_cache_expires ON financial_cache(expires_at)")
            
            conn.commit()
    
    def save_query_record(
        self, 
        tickers: List[str], 
        start_date: str, 
        end_date: str, 
        analysis_params: Dict[str, Any] = None,
        session_id: str = None,
        user_ip: str = None
    ) -> int:
        """
        保存查询记录
        
        Args:
            tickers: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            analysis_params: 分析参数
            session_id: 会话ID
            user_ip: 用户IP
            
        Returns:
            查询记录ID
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO query_records 
                (session_id, tickers, start_date, end_date, analysis_params, user_ip)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                json.dumps(tickers),
                start_date,
                end_date,
                json.dumps(analysis_params) if analysis_params else None,
                user_ip
            ))
            return cursor.lastrowid
    
    def save_analysis_result(
        self, 
        query_record_id: int, 
        result: Dict[str, Any]
    ):
        """
        保存技术分析结果
        
        Args:
            query_record_id: 查询记录ID
            result: 分析结果字典
        """
        ticker = result.get('ticker', '')
        current_price = result.get('current_price', 0.0)
        analysis = result.get('analysis', {})
        financial_metrics = result.get('financial_metrics', {})
        data_days = result.get('data_days', 0)
        
        # 从分析结果中提取详细信息
        signal = analysis.get('signal', '中性')
        confidence = analysis.get('confidence', 0)
        reason = analysis.get('reason', '')
        
        details = analysis.get('details', {})
        macd_signal = details.get('macd', {}).get('signal', '中性')
        rsi_signal = details.get('rsi', {}).get('signal', '中性') 
        bollinger_signal = details.get('bollinger', {}).get('signal', '中性')
        volume_signal = details.get('volume', {}).get('signal', '中性')
        
        # 生成交易建议
        recommendation_data = generate_trading_recommendation(result)
        recommendation = recommendation_data.get('recommendation', '')
        recommendation_action = recommendation_data.get('action', '')
        
        pe_ratio = financial_metrics.get('pe_ratio')
        pb_ratio = financial_metrics.get('pb_ratio')
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO analysis_results 
                (query_record_id, ticker, current_price, signal, confidence, reason,
                 macd_signal, rsi_signal, bollinger_signal, volume_signal,
                 recommendation, recommendation_action, data_days, pe_ratio, pb_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_record_id, ticker, current_price, signal, confidence, reason,
                macd_signal, rsi_signal, bollinger_signal, volume_signal,
                recommendation, recommendation_action, data_days, pe_ratio, pb_ratio
            ))
    
    def cache_price_data(
        self, 
        ticker: str, 
        price_data: List[Dict[str, Any]], 
        cache_hours: int = 24
    ):
        """
        缓存价格数据到数据库
        
        Args:
            ticker: 股票代码
            price_data: 价格数据列表
            cache_hours: 缓存有效期（小时）
        """
        expires_at = datetime.now() + timedelta(hours=cache_hours)
        
        with self.get_connection() as conn:
            for price in price_data:
                # 使用 INSERT OR REPLACE 处理重复数据
                conn.execute("""
                    INSERT OR REPLACE INTO price_cache 
                    (ticker, date, open_price, high_price, low_price, close_price, 
                     volume, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ticker.upper(),
                    price.get('time', price.get('date')),
                    price.get('open'),
                    price.get('high'),
                    price.get('low'),
                    price.get('close'),
                    price.get('volume'),
                    expires_at
                ))
    
    def get_cached_price_data(
        self, 
        ticker: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        从缓存中获取价格数据
        
        Args:
            ticker: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            价格数据列表，如果缓存过期或不存在返回空列表
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT date, open_price, high_price, low_price, close_price, volume
                FROM price_cache 
                WHERE ticker = ? AND date >= ? AND date <= ? 
                AND expires_at > CURRENT_TIMESTAMP
                ORDER BY date
            """, (ticker.upper(), start_date, end_date))
            
            rows = cursor.fetchall()
            
            return [
                {
                    'time': row['date'],
                    'open': row['open_price'],
                    'high': row['high_price'],
                    'low': row['low_price'],
                    'close': row['close_price'],
                    'volume': row['volume']
                }
                for row in rows
            ]
    
    def get_cached_dates(self, ticker: str) -> List[str]:
        """
        获取特定股票已缓存的所有日期
        
        Args:
            ticker: 股票代码
            
        Returns:
            已缓存日期列表
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT date
                FROM price_cache 
                WHERE ticker = ? AND expires_at > CURRENT_TIMESTAMP
                ORDER BY date
            """, (ticker.upper(),))
            
            rows = cursor.fetchall()
            return [row['date'] for row in rows]
    
    def cache_financial_data(
        self, 
        ticker: str, 
        financial_data: List[Dict[str, Any]], 
        cache_hours: int = 24 * 7  # 财务数据缓存1周
    ):
        """
        缓存财务数据到数据库
        
        Args:
            ticker: 股票代码
            financial_data: 财务数据列表
            cache_hours: 缓存有效期（小时）
        """
        expires_at = datetime.now() + timedelta(hours=cache_hours)
        
        with self.get_connection() as conn:
            for data in financial_data:
                conn.execute("""
                    INSERT OR REPLACE INTO financial_cache 
                    (ticker, report_period, period, currency, market_cap, pe_ratio, 
                     pb_ratio, ps_ratio, ev_ebitda, peg_ratio, roe, roa, 
                     debt_to_equity, current_ratio, quick_ratio, gross_margin, 
                     operating_margin, net_margin, expires_at, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ticker.upper(),
                    data.get('report_period'),
                    data.get('period', 'ttm'),
                    data.get('currency', 'USD'),
                    data.get('market_cap'),
                    data.get('price_to_earnings_ratio'),
                    data.get('price_to_book_ratio'),
                    data.get('price_to_sales_ratio'),
                    data.get('enterprise_value_to_ebitda_ratio'),
                    data.get('peg_ratio'),
                    data.get('return_on_equity'),
                    data.get('return_on_assets'),
                    data.get('debt_to_equity_ratio'),
                    data.get('current_ratio'),
                    data.get('quick_ratio'),
                    data.get('gross_margin'),
                    data.get('operating_margin'),
                    data.get('net_margin'),
                    expires_at,
                    json.dumps(data)
                ))
    
    def get_cached_financial_data(
        self, 
        ticker: str, 
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        从缓存中获取财务数据
        
        Args:
            ticker: 股票代码
            end_date: 结束日期
            
        Returns:
            财务数据列表
        """
        with self.get_connection() as conn:
            if end_date:
                cursor = conn.execute("""
                    SELECT raw_data
                    FROM financial_cache 
                    WHERE ticker = ? AND report_period <= ? 
                    AND expires_at > CURRENT_TIMESTAMP
                    ORDER BY report_period DESC
                """, (ticker.upper(), end_date))
            else:
                cursor = conn.execute("""
                    SELECT raw_data
                    FROM financial_cache 
                    WHERE ticker = ? AND expires_at > CURRENT_TIMESTAMP
                    ORDER BY report_period DESC
                """, (ticker.upper(),))
            
            rows = cursor.fetchall()
            
            return [json.loads(row['raw_data']) for row in rows]
    
    def get_query_history(
        self, 
        limit: int = 50, 
        ticker: str = None
    ) -> pd.DataFrame:
        """
        获取查询历史记录
        
        Args:
            limit: 返回记录数限制
            ticker: 过滤特定股票代码
            
        Returns:
            查询历史DataFrame
        """
        with self.get_connection() as conn:
            if ticker:
                sql = """
                    SELECT qr.*, 
                           COUNT(ar.id) as result_count,
                           GROUP_CONCAT(ar.ticker) as analyzed_tickers,
                           AVG(ar.confidence) as avg_confidence
                    FROM query_records qr
                    LEFT JOIN analysis_results ar ON qr.id = ar.query_record_id
                    WHERE qr.tickers LIKE ?
                    GROUP BY qr.id
                    ORDER BY qr.timestamp DESC
                    LIMIT ?
                """
                df = pd.read_sql_query(sql, conn, params=[f'%{ticker.upper()}%', limit])
            else:
                sql = """
                    SELECT qr.*, 
                           COUNT(ar.id) as result_count,
                           GROUP_CONCAT(ar.ticker) as analyzed_tickers,
                           AVG(ar.confidence) as avg_confidence
                    FROM query_records qr
                    LEFT JOIN analysis_results ar ON qr.id = ar.query_record_id
                    GROUP BY qr.id
                    ORDER BY qr.timestamp DESC
                    LIMIT ?
                """
                df = pd.read_sql_query(sql, conn, params=[limit])
        
        # 处理JSON字段
        if not df.empty:
            df['tickers'] = df['tickers'].apply(lambda x: json.loads(x) if x else [])
            df['analysis_params'] = df['analysis_params'].apply(lambda x: json.loads(x) if x else {})
        
        return df
    
    def get_analysis_history(
        self, 
        ticker: str = None, 
        limit: int = 100
    ) -> pd.DataFrame:
        """
        获取技术分析历史记录
        
        Args:
            ticker: 过滤特定股票代码
            limit: 返回记录数限制
            
        Returns:
            分析历史DataFrame
        """
        with self.get_connection() as conn:
            if ticker:
                sql = """
                    SELECT ar.*, qr.timestamp as query_time, qr.start_date, qr.end_date
                    FROM analysis_results ar
                    JOIN query_records qr ON ar.query_record_id = qr.id
                    WHERE ar.ticker = ?
                    ORDER BY ar.created_at DESC
                    LIMIT ?
                """
                df = pd.read_sql_query(sql, conn, params=[ticker.upper(), limit])
            else:
                sql = """
                    SELECT ar.*, qr.timestamp as query_time, qr.start_date, qr.end_date
                    FROM analysis_results ar
                    JOIN query_records qr ON ar.query_record_id = qr.id
                    ORDER BY ar.created_at DESC
                    LIMIT ?
                """
                df = pd.read_sql_query(sql, conn, params=[limit])
        
        return df
    
    def cleanup_expired_cache(self):
        """清理过期的缓存数据"""
        with self.get_connection() as conn:
            # 清理过期的价格缓存
            cursor = conn.execute("""
                DELETE FROM price_cache 
                WHERE expires_at <= CURRENT_TIMESTAMP
            """)
            price_deleted = cursor.rowcount
            
            # 清理过期的财务数据缓存
            cursor = conn.execute("""
                DELETE FROM financial_cache 
                WHERE expires_at <= CURRENT_TIMESTAMP
            """)
            financial_deleted = cursor.rowcount
            
            conn.commit()
            
            if price_deleted > 0 or financial_deleted > 0:
                print(f"🧹 清理过期缓存: 价格数据 {price_deleted} 条, 财务数据 {financial_deleted} 条")
    
    def clear_ticker_cache(self, ticker: str):
        """清除特定股票的所有缓存数据"""
        with self.get_connection() as conn:
            # 清除价格缓存
            cursor = conn.execute("""
                DELETE FROM price_cache 
                WHERE ticker = ?
            """, (ticker.upper(),))
            price_deleted = cursor.rowcount
            
            # 清除财务数据缓存
            cursor = conn.execute("""
                DELETE FROM financial_cache 
                WHERE ticker = ?
            """, (ticker.upper(),))
            financial_deleted = cursor.rowcount
            
            conn.commit()
            
            if price_deleted > 0 or financial_deleted > 0:
                print(f"🧹 清除 {ticker} 缓存: 价格数据 {price_deleted} 条, 财务数据 {financial_deleted} 条")
            
            return price_deleted + financial_deleted
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.get_connection() as conn:
            # 价格缓存统计
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT ticker) as unique_tickers,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date,
                    COUNT(CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 1 END) as valid_records
                FROM price_cache
            """)
            price_stats = dict(cursor.fetchone())
            
            # 财务缓存统计
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT ticker) as unique_tickers,
                    COUNT(CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 1 END) as valid_records
                FROM financial_cache
            """)
            financial_stats = dict(cursor.fetchone())
            
            # 查询记录统计
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_queries,
                    COUNT(DISTINCT DATE(timestamp)) as query_days,
                    MIN(timestamp) as first_query,
                    MAX(timestamp) as last_query
                FROM query_records
            """)
            query_stats = dict(cursor.fetchone())
            
            return {
                'price_cache': price_stats,
                'financial_cache': financial_stats,
                'query_records': query_stats
            }


# 全局数据库实例
_db_manager = None


def get_database_manager() -> DatabaseManager:
    """获取全局数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def generate_trading_recommendation(analysis_result):
    """
    生成交易建议（兼容性函数）
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