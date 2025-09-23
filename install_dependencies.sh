#!/bin/bash
# AI Hedge Fund 项目依赖安装脚本
# 自动使用国内镜像源进行安装

echo "🚀 开始安装 AI Hedge Fund 项目依赖..."

# 检测 Poetry 是否安装
if command -v poetry &> /dev/null; then
    echo "✅ 检测到 Poetry，使用 Poetry 安装..."
    
    # 配置 Poetry 使用国内镜像
    poetry config repositories.tsinghua https://pypi.tuna.tsinghua.edu.cn/simple
    poetry config pypi-token.tsinghua ""
    
    # 使用 Poetry 安装
    poetry install
else
    echo "⚠️  未检测到 Poetry，使用 pip 安装..."
    
    # 升级 pip
    echo "📦 升级 pip..."
    python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    # 使用清华镜像安装核心依赖
    echo "📦 安装核心依赖..."
    pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple \
        streamlit pandas matplotlib plotly yfinance python-dotenv
    
    # 安装完整依赖（如果需要）
    if [ -f "requirements.txt" ]; then
        echo "📦 安装完整依赖..."
        pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
    fi
fi

echo "✅ 依赖安装完成！"
echo ""
echo "🔧 下一步操作:"
echo "1. 复制并配置环境变量: cp .env.example .env"
echo "2. 编辑 .env 文件，添加你的 API keys"
echo "3. 运行基本面分析应用: python3 run_fundamental_analysis_app.py"