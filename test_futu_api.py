from src.tools.futu_api import FutuAPI

def test_futu_connection():
    print("Testing Futu API connection...")
    api = FutuAPI()
    
    if not api.connect():
        print("Failed to connect to Futu API")
        return False
    
    print("Successfully connected to Futu API")
    
    # Test getting market snapshot for HK.00700 (Tencent)
    print("Testing HK market snapshot...")
    hk_snapshot = api.get_market_snapshot(["HK.00700"])
    
    if hk_snapshot:
        print("HK market snapshot test successful")
        print(hk_snapshot)
    else:
        print("Failed to get HK market snapshot")
    
    # Test US market stocks that failed in logs
    us_stocks = ["US.NBIS", "US.SMCI", "US.RXRX", "US.CLSK", "US.NVDA"]
    print(f"\nTesting US market snapshot for {us_stocks}...")
    us_snapshot = api.get_market_snapshot(us_stocks)
    
    if us_snapshot:
        print("US market snapshot test successful")
        print(us_snapshot)
    else:
        print("Failed to get US market snapshot")
    
    api.close()
    return True

if __name__ == "__main__":
    test_futu_connection()