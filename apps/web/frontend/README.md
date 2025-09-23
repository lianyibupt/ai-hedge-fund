# 🎯 DaisyUI 交易分析系统前端

基于 FastAPI + DaisyUI 构建的现代化交易分析系统前端。

## 🚀 功能特性

- ✅ 现代化 UI 设计，使用 DaisyUI 组件库
- ✅ 响应式布局，支持移动端和桌面端
- ✅ 实时技术分析和基本面分析
- ✅ 交互式图表展示
- ✅ 智能缓存管理
- ✅ 自动刷新功能

## 📦 技术栈

- **前端**: HTML5 + DaisyUI + Tailwind CSS
- **图表**: Plotly.js
- **HTTP客户端**: Axios
- **后端**: FastAPI (Python)
- **构建工具**: 无构建步骤，直接使用CDN

## 🛠️ 安装和运行

### 前置要求

- Python 3.8+
- pip

### 安装依赖

```bash
cd apps/web/frontend
pip install -r requirements.txt
```

### 启动开发服务器

```bash
# 方法1: 使用提供的启动脚本
python ../../../run_daisyui_app.py

# 方法2: 直接运行
cd apps/web/frontend
python server.py
```

### 访问应用

打开浏览器访问: http://localhost:8000

## 📁 项目结构

```
apps/web/frontend/
├── index.html          # 主页面
├── app.js              # 前端JavaScript逻辑
├── server.py           # FastAPI后端服务器
├── requirements.txt    # Python依赖
└── README.md          # 说明文档
```

## 🎨 自定义主题

DaisyUI 支持多种主题，可以通过修改 `index.html` 中的 `data-theme` 属性来切换主题。

## 🔧 配置选项

### API 基础URL

在 `app.js` 中修改 `apiBase`:

```javascript
this.apiBase = 'http://localhost:8000';  // 开发环境
```

### 图表配置

在 `renderChart` 方法中自定义Plotly图表样式和布局。

## 📊 功能说明

### 1. 股票分析
- 支持多股票同时分析
- 技术指标计算（MACD、RSI、布林带等）
- 基本面分析（美股）

### 2. 缓存管理
- 智能缓存策略
- 手动清理缓存
- 缓存统计