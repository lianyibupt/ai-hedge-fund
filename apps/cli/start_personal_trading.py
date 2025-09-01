#!/usr/bin/env python3
"""
个性化交易分析系统启动器
"""

import subprocess
import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def main():
    print("🎯 启动个性化交易分析系统...")
    
    # 检查Streamlit是否可用
    # try:
    #     import streamlit
    #     print("✅ Streamlit已安装")
    # except ImportError:
    #     print("❌ Streamlit未安装，请先运行: pip install streamlit plotly")
    #     sys.exit(1)
    
    # # 检查Plotly是否可用
    # try:
    #     import plotly
    #     print("✅ Plotly已安装")
    # except ImportError:
    #     print("⚠️ Plotly未安装，将尝试安装...")
    #     subprocess.run([sys.executable, "-m", "pip", "install", "plotly"])
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..', '..')
    app_path = os.path.join(project_root, "apps", "web", "personal_trading_app.py")
    
    if not os.path.exists(app_path):
        print(f"❌ 找不到应用文件: {app_path}")
        sys.exit(1)
    
    print("🚀 启动中...")
    print("📍 应用地址: http://localhost:8501")
    print("💡 按 Ctrl+C 停止应用")
    
    # 启动Streamlit应用
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            app_path,
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()