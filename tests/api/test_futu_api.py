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
    us_stocks = ["HK.00700", "HK.09988", "HK.03690"]
    print(f"\nTesting US market snapshot for {us_stocks}...")
    us_snapshot = api.get_market_snapshot(us_stocks)
    
    if us_snapshot:
        print("US market snapshot test successful")
        print(us_snapshot)
    else:
        print("Failed to get US market snapshot")
    
    # Test financial data for HK.00700 (Tencent)
    print("\nTesting financial data for HK.00700...")
    income_data = api.get_financial_data("HK.00700", "income")
    balance_data = api.get_financial_data("HK.00700", "balance")
    cashflow_data = api.get_financial_data("HK.00700", "cashflow")
    
    if income_data and balance_data and cashflow_data:
        print("Financial data test successful")
        print(f"Income statement: {income_data[0]}")
        print(f"Balance sheet: {balance_data[0]}")
        print(f"Cash flow: {cashflow_data[0]}")
    else:
        print("Failed to get financial data")
    
    api.close()
    return True

if __name__ == "__main__":
    test_futu_connection()