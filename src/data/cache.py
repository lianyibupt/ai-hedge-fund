from datetime import datetime, date
from typing import Dict, List, Any, Optional

class Cache:
    """Enhanced in-memory cache with date-based keys for fresh data."""

    def __init__(self):
        # 使用 ticker + date 作为key的缓存结构
        self._prices_cache: Dict[str, Dict[str, dict]] = {}  # {ticker: {date: price_data}}
        self._financial_metrics_cache: Dict[str, Dict[str, dict]] = {}  # {ticker: {report_period: financial_data}}
        self._line_items_cache: Dict[str, Dict[str, dict]] = {}  # {ticker: {report_period: line_items_data}}
        self._insider_trades_cache: Dict[str, List[dict]] = {}  # 内部交易保持原有结构
        self._company_news_cache: Dict[str, List[dict]] = {}  # 新闻保持原有结构
        
        # 添加缓存时间戳跟踪
        self._cache_timestamps: Dict[str, datetime] = {}  # 记录缓存更新时间

    def _get_cache_key(self, ticker: str, date_str: str = None) -> str:
        """生成缓存键，结合股票代码和日期"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        return f"{ticker.upper()}_{date_str}"
    
    def _is_cache_fresh(self, cache_key: str, max_age_hours: int = 24) -> bool:
        """检查缓存是否在指定时间内是新鲜的"""
        if cache_key not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[cache_key]
        now = datetime.now()
        age_hours = (now - cache_time).total_seconds() / 3600
        return age_hours < max_age_hours
    
    def _update_cache_timestamp(self, cache_key: str):
        """更新缓存时间戳"""
        self._cache_timestamps[cache_key] = datetime.now()

    def get_prices(self, ticker: str, start_date: str = None, end_date: str = None) -> List[dict] | None:
        """获取缓存的价格数据，支持日期范围过滤"""
        ticker = ticker.upper()
        
        if ticker not in self._prices_cache:
            return None
        
        ticker_cache = self._prices_cache[ticker]
        
        # 如果没有指定日期范围，返回所有缓存数据
        if start_date is None and end_date is None:
            all_prices = []
            for date_key in sorted(ticker_cache.keys()):
                cache_key = f"{ticker}_{date_key}"
                # 检查缓存是否新鲜（价格数据保持24小时新鲜）
                if self._is_cache_fresh(cache_key, max_age_hours=24):
                    all_prices.append(ticker_cache[date_key])
            return all_prices if all_prices else None
        
        # 根据日期范围过滤
        filtered_prices = []
        for date_key, price_data in ticker_cache.items():
            if start_date and date_key < start_date:
                continue
            if end_date and date_key > end_date:
                continue
            
            cache_key = f"{ticker}_{date_key}"
            # 检查缓存是否新鲜
            if self._is_cache_fresh(cache_key, max_age_hours=24):
                filtered_prices.append(price_data)
        
        return filtered_prices if filtered_prices else None
    
    def get_cached_dates(self, ticker: str) -> List[str]:
        """获取特定股票已缓存的所有日期"""
        ticker = ticker.upper()
        
        if ticker not in self._prices_cache:
            return []
        
        cached_dates = []
        ticker_cache = self._prices_cache[ticker]
        
        for date_key in ticker_cache.keys():
            cache_key = f"{ticker}_{date_key}"
            # 只返回新鲜的缓存日期
            if self._is_cache_fresh(cache_key, max_age_hours=24):
                cached_dates.append(date_key)
        
        return sorted(cached_dates)

    def set_prices(self, ticker: str, data: List[dict]):
        """按日期存储价格数据，每个日期单独缓存"""
        ticker = ticker.upper()
        
        if ticker not in self._prices_cache:
            self._prices_cache[ticker] = {}
        
        for price_item in data:
            date_key = price_item.get('time', price_item.get('date'))
            if date_key:
                # 确保日期格式统一
                if isinstance(date_key, str) and len(date_key) > 10:
                    date_key = date_key[:10]  # 截取YYYY-MM-DD部分
                
                # 存储到对应日期的缓存中
                self._prices_cache[ticker][date_key] = price_item
                
                # 更新缓存时间戳
                cache_key = f"{ticker}_{date_key}"
                self._update_cache_timestamp(cache_key)

    def get_financial_metrics(self, ticker: str, end_date: str = None) -> List[dict] | None:
        """获取缓存的财务指标数据"""
        ticker = ticker.upper()
        
        if ticker not in self._financial_metrics_cache:
            return None
        
        ticker_cache = self._financial_metrics_cache[ticker]
        
        # 如果没有指定结束日期，返回所有新鲜的缓存数据
        if end_date is None:
            all_metrics = []
            for period_key in sorted(ticker_cache.keys(), reverse=True):
                cache_key = f"{ticker}_financial_{period_key}"
                # 财务数据保持7天新鲜
                if self._is_cache_fresh(cache_key, max_age_hours=24*7):
                    all_metrics.append(ticker_cache[period_key])
            return all_metrics if all_metrics else None
        
        # 根据结束日期过滤
        filtered_metrics = []
        for period_key, financial_data in ticker_cache.items():
            if period_key <= end_date:
                cache_key = f"{ticker}_financial_{period_key}"
                # 检查缓存是否新鲜
                if self._is_cache_fresh(cache_key, max_age_hours=24*7):
                    filtered_metrics.append(financial_data)
        
        # 按报告期倒序排列
        filtered_metrics.sort(key=lambda x: x.get('report_period', ''), reverse=True)
        return filtered_metrics if filtered_metrics else None

    def set_financial_metrics(self, ticker: str, data: List[dict]):
        """按报告期存储财务指标数据"""
        ticker = ticker.upper()
        
        if ticker not in self._financial_metrics_cache:
            self._financial_metrics_cache[ticker] = {}
        
        for metric_item in data:
            period_key = metric_item.get('report_period')
            if period_key:
                # 存储到对应报告期的缓存中
                self._financial_metrics_cache[ticker][period_key] = metric_item
                
                # 更新缓存时间戳
                cache_key = f"{ticker}_financial_{period_key}"
                self._update_cache_timestamp(cache_key)

    def get_line_items(self, ticker: str, end_date: str = None) -> List[dict] | None:
        """获取缓存的财务报表项目数据"""
        ticker = ticker.upper()
        
        if ticker not in self._line_items_cache:
            return None
        
        ticker_cache = self._line_items_cache[ticker]
        
        if end_date is None:
            all_items = []
            for period_key in sorted(ticker_cache.keys(), reverse=True):
                cache_key = f"{ticker}_lineitem_{period_key}"
                if self._is_cache_fresh(cache_key, max_age_hours=24*7):
                    all_items.append(ticker_cache[period_key])
            return all_items if all_items else None
        
        filtered_items = []
        for period_key, item_data in ticker_cache.items():
            if period_key <= end_date:
                cache_key = f"{ticker}_lineitem_{period_key}"
                if self._is_cache_fresh(cache_key, max_age_hours=24*7):
                    filtered_items.append(item_data)
        
        filtered_items.sort(key=lambda x: x.get('report_period', ''), reverse=True)
        return filtered_items if filtered_items else None

    def set_line_items(self, ticker: str, data: List[dict]):
        """按报告期存储财务报表项目数据"""
        ticker = ticker.upper()
        
        if ticker not in self._line_items_cache:
            self._line_items_cache[ticker] = {}
        
        for item_data in data:
            period_key = item_data.get('report_period')
            if period_key:
                self._line_items_cache[ticker][period_key] = item_data
                cache_key = f"{ticker}_lineitem_{period_key}"
                self._update_cache_timestamp(cache_key)

    def get_insider_trades(self, ticker: str) -> List[dict] | None:
        """获取缓存的内部交易数据（保持原有结构）"""
        ticker = ticker.upper()
        cache_key = f"{ticker}_insider"
        
        # 检查缓存是否新鲜（内部交易数据保持1天新鲜）
        if self._is_cache_fresh(cache_key, max_age_hours=24):
            return self._insider_trades_cache.get(ticker)
        return None

    def set_insider_trades(self, ticker: str, data: List[dict]):
        """存储内部交易数据"""
        ticker = ticker.upper()
        
        # 合并数据，避免重复
        existing_data = self._insider_trades_cache.get(ticker, [])
        if existing_data:
            existing_keys = {item.get('filing_date', item.get('transaction_date')) for item in existing_data}
            new_items = [item for item in data if item.get('filing_date', item.get('transaction_date')) not in existing_keys]
            self._insider_trades_cache[ticker] = existing_data + new_items
        else:
            self._insider_trades_cache[ticker] = data
        
        # 更新缓存时间戳
        cache_key = f"{ticker}_insider"
        self._update_cache_timestamp(cache_key)

    def get_company_news(self, ticker: str) -> List[dict] | None:
        """获取缓存的公司新闻数据（保持原有结构）"""
        ticker = ticker.upper()
        cache_key = f"{ticker}_news"
        
        # 检查缓存是否新鲜（新闻数据保持6小时新鲜）
        if self._is_cache_fresh(cache_key, max_age_hours=6):
            return self._company_news_cache.get(ticker)
        return None

    def set_company_news(self, ticker: str, data: List[dict]):
        """存储公司新闻数据"""
        ticker = ticker.upper()
        
        # 合并数据，避免重复
        existing_data = self._company_news_cache.get(ticker, [])
        if existing_data:
            existing_keys = {item.get('date') for item in existing_data}
            new_items = [item for item in data if item.get('date') not in existing_keys]
            self._company_news_cache[ticker] = existing_data + new_items
        else:
            self._company_news_cache[ticker] = data
        
        # 更新缓存时间戳
    def clear_expired_cache(self):
        """清理过期的缓存数据"""
        now = datetime.now()
        expired_keys = []
        
        for cache_key, cache_time in self._cache_timestamps.items():
            # 默认保持24小时，财务数据保持7天，新闻6小时
            max_age = 24  # 默认值
            if "_financial_" in cache_key or "_lineitem_" in cache_key:
                max_age = 24 * 7  # 7天
            elif "_news" in cache_key:
                max_age = 6  # 6小时
            
            age_hours = (now - cache_time).total_seconds() / 3600
            if age_hours > max_age:
                expired_keys.append(cache_key)
        
        # 清理过期的缓存数据
        for cache_key in expired_keys:
            ticker = cache_key.split('_')[0]
            
            if "_financial_" in cache_key:
                period = cache_key.split('_financial_')[1]
                if ticker in self._financial_metrics_cache and period in self._financial_metrics_cache[ticker]:
                    del self._financial_metrics_cache[ticker][period]
            elif "_lineitem_" in cache_key:
                period = cache_key.split('_lineitem_')[1]
                if ticker in self._line_items_cache and period in self._line_items_cache[ticker]:
                    del self._line_items_cache[ticker][period]
            elif "_insider" in cache_key:
                if ticker in self._insider_trades_cache:
                    del self._insider_trades_cache[ticker]
            elif "_news" in cache_key:
                if ticker in self._company_news_cache:
                    del self._company_news_cache[ticker]
            else:  # 价格数据
                date_key = '_'.join(cache_key.split('_')[1:])
                if ticker in self._prices_cache and date_key in self._prices_cache[ticker]:
                    del self._prices_cache[ticker][date_key]
            
            # 清理时间戳
            del self._cache_timestamps[cache_key]
        
        return len(expired_keys)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            'cache_summary': {
                'total_tickers': len(set(
                    list(self._prices_cache.keys()) + 
                    list(self._financial_metrics_cache.keys()) + 
                    list(self._line_items_cache.keys()) + 
                    list(self._insider_trades_cache.keys()) + 
                    list(self._company_news_cache.keys())
                )),
                'total_cache_entries': len(self._cache_timestamps),
                'fresh_entries': sum(1 for key in self._cache_timestamps if self._is_cache_fresh(key, 24))
            },
            'price_cache': {
                'tickers_count': len(self._prices_cache),
                'total_date_entries': sum(len(dates) for dates in self._prices_cache.values()),
                'fresh_entries': sum(
                    1 for ticker, dates in self._prices_cache.items() 
                    for date_key in dates 
                    if self._is_cache_fresh(f"{ticker}_{date_key}", 24)
                )
            },
            'financial_cache': {
                'tickers_count': len(self._financial_metrics_cache),
                'total_period_entries': sum(len(periods) for periods in self._financial_metrics_cache.values()),
                'fresh_entries': sum(
                    1 for ticker, periods in self._financial_metrics_cache.items() 
                    for period_key in periods 
                    if self._is_cache_fresh(f"{ticker}_financial_{period_key}", 24*7)
                )
            },
            'other_cache': {
                'insider_trades': len(self._insider_trades_cache),
                'company_news': len(self._company_news_cache),
                'line_items': len(self._line_items_cache)
            }
        }
        return stats
    
    def clear_all_cache(self):
        """清空所有缓存数据"""
        self._prices_cache.clear()
        self._financial_metrics_cache.clear()
        self._line_items_cache.clear()
        self._insider_trades_cache.clear()
        self._company_news_cache.clear()
        self._cache_timestamps.clear()
    
    def clear_ticker_cache(self, ticker: str):
        """清除特定股票的所有缓存数据"""
        ticker = ticker.upper()
        
        # 清除各类型缓存
        if ticker in self._prices_cache:
            del self._prices_cache[ticker]
        if ticker in self._financial_metrics_cache:
            del self._financial_metrics_cache[ticker]
        if ticker in self._line_items_cache:
            del self._line_items_cache[ticker]
        if ticker in self._insider_trades_cache:
            del self._insider_trades_cache[ticker]
        if ticker in self._company_news_cache:
            del self._company_news_cache[ticker]
        
        # 清除相关的时间戳
        keys_to_remove = [key for key in self._cache_timestamps.keys() if key.startswith(f"{ticker}_")]
        for key in keys_to_remove:
            del self._cache_timestamps[key]


# Global cache instance
_cache = Cache()


def get_cache() -> Cache:
    """Get the global cache instance."""
    return _cache
