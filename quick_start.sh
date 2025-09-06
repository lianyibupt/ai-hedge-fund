#!/bin/bash
# AI Hedge Fund 快速启动脚本 - 基本面分析应用
# 自动检查依赖并使用国内镜像源

echo "🚀 启动 AI Hedge Fund 基本面分析应用..."

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python"
    exit 1
fi

# 检查 Streamlit 是否安装
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "⚠️  检测到缺少依赖，正在使用国内镜像安装..."
    pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple streamlit pandas matplotlib plotly yfinance python-dotenv
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 复制环境变量模板..."
        cp .env.example .env
        echo "✅ 已创建 .env 文件，请编辑并添加你的 API keys"
    else
        echo "⚠️  警告: 未找到 .env.example 文件"
    fi
fi

# 启动应用
echo "🌐 启动基本面分析应用..."
python3 run_fundamental_analysis_app.py