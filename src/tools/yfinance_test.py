import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ================== 设置参数 ==================
# 股票代码（可替换为任意股票，如 'AAPL', 'SH600519.SH' 等）
ticker = "000001.SZ"  # 深圳000001：平安银行（示例，A股）
period = "2023-01-01"  # 起始日期（可自定义）
lookback = 50          # 历史数据周期（50日）
trade_freq = 14         # 14天=2周，用于判断是否满足交易条件

# ================== 读取数据 ==================
def get_data(ticker, period):
    data = yf.download(ticker, start=period, period="200d")
    return data

# ================== 计算技术指标 ==================
def calculate_indicators(df):
    # MACD
    df['MACD'], df['MACD_signal'], df['MACD_hist'] = \
        pd.signal.macrossover(df['Close'], window=12, signal=9)
    df['MACD_diff'] = df['MACD'] - df['MACD_signal']

    # RSI (14日)
    delta = df['Close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # BOLL (20日，2个标准差)
    df['BOLL_mid'] = df['Close'].rolling(20).mean()
    df['BOLL_std'] = df['Close'].rolling(20).std()
    df['BOLL_upper'] = df['BOLL_mid'] + 2 * df['BOLL_std']
    df['BOLL_lower'] = df['BOLL_mid'] - 2 * df['BOLL_std']

    # 交易量
    df['Volume'] = df['Volume']

    return df

# ================== 交易信号判断函数 ==================
def generate_signals(df):
    signals = []
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]

        # 买点条件（必须同时满足）
        buy_conditions = (
            row['MACD'] > prev_row['MACD'] and           # MACD金叉
            row['RSI'] > 30 and row['RSI'] > prev_row['RSI'] and  # RSI上穿30
            row['Close'] >= row['BOLL_lower'] and      # 价格在布林带下轨之上
            row['Volume'] > df['Volume'].rolling(5).mean().iloc[i-1] * 1.5  # 放量
        )

        # 卖点条件（任一满足）
        sell_conditions = (
            row['MACD'] < prev_row['MACD'] and         # MACD死叉
            row['RSI'] > 70 and row['RSI'] < prev_row['RSI'] and  # RSI超买回落
            row['Close'] >= row['BOLL_upper']         # 价格触及上轨
        )

        if buy_conditions:
            signals.append((row.name, 'BUY'))
        elif sell_conditions:
            signals.append((row.name, 'SELL'))

    return signals

# ================== 主程序 ==================
def main():
    print(f"🔍 正在获取 {ticker} 的数据...")
    df = get_data(ticker, period)
    
    if df.empty:
        print("⚠️ 未获取到数据，请检查股票代码或网络连接")
        return
    
    # 计算指标
    df = calculate_indicators(df.copy())
    
    # 生成交易信号
    signals = generate_signals(df)
    
    # 输出交易信号
    print(f"\n📊 交易信号（2周周期）：")
    for date, signal in signals:
        print(f"📅 {date.strftime('%Y-%m-%d')} → {signal}")
    
    # 可视化（可选）
    plt.figure(figsize=(16, 8))

    plt.subplot(2, 2, 1)
    plt.plot(df.index, df['Close'], label='Close',, color='blue')
    plt.plot(df.index, df['BOLL_upper'], '--', color='red', label='BOLL Upper')
    plt.plot(df.index, df['BOLL_lower'], '--', color='green', label='BOLL Lower')
    plt.title('Price & BOLL')
    plt.legend()

    plt.subplot(2, 2, 2)
    plt.plot(df.index, df['MACD'], label='MACD', color='orange')
    plt.plot(df.index, df['MACD_signal'], label='Signal', color='purple', linestyle='--')
    plt.title('MACD Signal')
    plt.legend()

    plt.subplot(2, 2, 3)
    plt.plot(df.index, df['RSI'], label='RSI', color='magenta')
    plt.axhline(30, color='g', linestyle='--', alpha=0.5)
    plt.axhline(70, color='r', linestyle='--', alpha=0.5)
    plt.title('RSI')
    plt.legend()

    plt.subplot(2, 2, 4)
    plt.plot(df.index, df['Volume'], label='Volume', color='brown')
    plt.title('Volume')
    plt.legend()

    plt.tight_layout()
    plt.show()

# ================== 运行 ==================
if __name__ == "__main__":
    main()
