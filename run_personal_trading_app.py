#!/usr/bin/env python3
"""
个性化交易分析系统主入口
运行Streamlit Web应用

使用前准备:
1. 安装依赖: poetry install
2. 配置API密钥: 复制 .env.example 为 .env 并填入相关API密钥
3. 确保Python版本 >= 3.10

运行方式:
- 直接运行: python run_personal_trading_app.py
- 使用Poetry: poetry run python run_personal_trading_app.py
"""
import os
import sys
import subprocess

def check_dependencies():
    """检查依赖和环境配置"""
    try:
        import streamlit
    except ImportError:
        print("❌ 缺少依赖包，请先安装:")
        print("   poetry install")
        print("   或者: pip install -r requirements.txt")
        sys.exit(1)
    
    # 检查环境变量文件
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_file):
        print("⚠️  警告: 未找到 .env 文件")
        print("   请复制 .env.example 为 .env 并配置相关API密钥")
        print("   系统将使用默认配置启动")
        print()

def main():
    """主函数"""
    print("🔍 检查环境依赖...")
    check_dependencies()
    
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
    print("")
    print("💡 使用提示:")
    print("   - 确保已配置 API 密钥 (OpenAI, Groq, iTick等)")
    print("   - 支持美股、港股、A股等多个市场")
    print("   - 提供技术分析、基本面分析等功能")
    print("")
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