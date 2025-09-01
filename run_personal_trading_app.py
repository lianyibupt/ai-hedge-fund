#!/usr/bin/env python3
"""
个性化交易分析系统主入口
运行Streamlit Web应用
"""
import os
import sys
import subprocess

def main():
    """主函数"""
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 设置应用文件路径
    app_file = os.path.join(current_dir, 'apps', 'web', 'personal_trading_app.py')
    
    if not os.path.exists(app_file):
        print(f"错误: 找不到应用文件 {app_file}")
        sys.exit(1)
    
    # 启动Streamlit应用
    print("🚀 启动个性化交易分析系统...")
    print(f"📁 应用文件: {app_file}")
    print("🌐 浏览器将自动打开 http://localhost:8501")
    print("按 Ctrl+C 退出")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', app_file,
            '--server.port', '8501',
            '--server.headless', 'false',
            '--browser.gatherUsageStats', 'false'
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()