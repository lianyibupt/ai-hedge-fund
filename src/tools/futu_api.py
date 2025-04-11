import os
from typing import Optional
from futu import OpenQuoteContext, OpenCNTradeContext, RET_OK, TrdEnv

class FutuAPI:
    def __init__(self):
        self.appid = os.getenv("FUTU_APPID")
        self.token = os.getenv("FUTU_TOKEN")
        self.quote_ctx = None
        self.trade_ctx = None
        
    def connect(self) -> bool:
        """Connect to Futu API"""
        try:
            self.quote_ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
            self.trade_ctx = OpenCNTradeContext(host="127.0.0.1", port=11111,
                                             security_firm=TrdEnv.SIMULATE)
            return True
        except Exception as e:
            print(f"Failed to connect to Futu API: {str(e)}")
            return False
            
    def get_history_kline(self, code: str, start: str, end: str, ktype="K_DAY") -> Optional[dict]:
        """Get historical kline data"""
        if not self.quote_ctx:
            return None
            
        ret, data, page_req_key = self.quote_ctx.request_history_kline(
            code=code,
            start=start,
            end=end,
            ktype=ktype,
            max_count=1000
        )
        
        if ret != RET_OK:
            print(f"Failed to get kline data: {data}")
            return None
            
        return data.to_dict("records")
        
    def get_market_snapshot(self, code_list: list[str]) -> Optional[dict]:
        """Get market snapshot data"""
        if not self.quote_ctx:
            return None
            
        ret, data = self.quote_ctx.get_market_snapshot(code_list)
        
        if ret != RET_OK:
            print(f"Failed to get market snapshot: {data}")
            return None
            
        return data.to_dict("records")
        
    def get_financial_data(self, code: str, financial_type: str) -> Optional[dict]:
        """Get financial data"""
        if not self.quote_ctx:
            return None
            
        ret, data = self.quote_ctx.get_stock_quote(code)
        
        if ret != RET_OK:
            print(f"Failed to get financial data: {data}")
            return None
            
        return data.to_dict("records")
        
    def close(self):
        """Close connections"""
        if self.quote_ctx:
            self.quote_ctx.close()
        if self.trade_ctx:
            self.trade_ctx.close()