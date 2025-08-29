from futu import *
from typing import Tuple

def test_futu_quote() -> bool:
    """测试Futu Quote API连接"""
    print("Testing Futu Quote API connection...")
    quote_ctx = None
    try:
        quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
        print("Successfully connected to Futu Quote API")
        
        # Test getting market snapshot for HK.00700 (Tencent)
        ret, data = quote_ctx.get_market_snapshot(['HK.00700'])
        if ret == 0:  # RET_OK
            print("Market snapshot test successful")
            print(data)
        else:
            print(f"Failed to get market snapshot: {data}")
        
        return True
    except Exception as e:
        print(f"Failed to connect to Futu Quote API: {str(e)}")
        return False
    finally:
        if quote_ctx:
            quote_ctx.close()

if __name__ == "__main__":
    test_futu_quote()