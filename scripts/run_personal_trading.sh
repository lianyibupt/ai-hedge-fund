#!/bin/bash

# 个性化交易分析系统 - Streamlit启动脚本

echo "🎯 启动个性化交易分析系统..."

# 检查是否安装了必要的依赖
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit未安装，请先安装："
    echo "   poetry add streamlit plotly"
    exit 1
fi

# 设置工作目录
cd "$(dirname "$0")"

# 启动Streamlit应用
echo "🚀 启动中..."
echo "📍 应用地址: http://localhost:8501"
echo "💡 按 Ctrl+C 停止应用"

streamlit run src/personal_trading_app.py --server.port 8501 --server.address localhost