# 国内镜像源配置指南

本项目已针对国内用户配置了多种 PyPI 镜像源，以提升依赖包下载速度。

## 快速开始

### 方式1: 一键安装脚本（推荐）

```bash
# 运行自动安装脚本
./install_dependencies.sh

# 快速启动应用
./quick_start.sh
```

### 方式2: 手动使用镜像源

```bash
# 安装核心依赖
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple streamlit pandas matplotlib plotly yfinance python-dotenv

# 安装完整依赖
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

### 方式3: Poetry 配置镜像源

```bash
# 配置 Poetry 使用清华镜像源
poetry config repositories.tsinghua https://pypi.tuna.tsinghua.edu.cn/simple
poetry install
```

## 可用的镜像源

### 1. 清华大学镜像源（推荐）
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple package_name
```

### 2. 阿里云镜像源
```bash
pip install -i https://mirrors.aliyun.com/pypi/simple package_name
```

### 3. 中科大镜像源
```bash
pip install -i https://pypi.mirrors.ustc.edu.cn/simple package_name
```

### 4. 豆瓣镜像源
```bash
pip install -i https://pypi.douban.com/simple package_name
```

## 永久配置

### 配置 pip 默认镜像源

**Linux/macOS:**
```bash
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
```

**Windows:**
```bash
# 在 %APPDATA%\pip\pip.ini 文件中添加：
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

### Poetry 永久配置

```bash
# 配置默认镜像源
poetry config repositories.tsinghua https://pypi.tuna.tsinghua.edu.cn/simple

# 查看配置
poetry config --list
```

## 项目内置配置

本项目已包含以下配置文件：

1. **pip.conf** - pip 镜像源配置
2. **install_dependencies.sh** - 自动安装脚本
3. **quick_start.sh** - 快速启动脚本
4. **requirements.txt** - 带镜像源说明的依赖文件

## 使用建议

1. **国内用户**: 优先使用清华镜像源，速度最稳定
2. **企业用户**: 可考虑阿里云镜像源
3. **学术用户**: 推荐中科大镜像源

## 故障排除

### 证书错误
如果遇到 SSL 证书错误，可以临时使用：
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn package_name
```

### 网络超时
尝试切换不同的镜像源：
```bash
# 尝试阿里云镜像
pip install -i https://mirrors.aliyun.com/pypi/simple package_name

# 尝试豆瓣镜像
pip install -i https://pypi.douban.com/simple package_name
```

## 相关链接

- [清华大学 PyPI 镜像](https://mirrors.tuna.tsinghua.edu.cn/help/pypi/)
- [阿里云 PyPI 镜像](https://developer.aliyun.com/mirror/pypi)
- [中科大 PyPI 镜像](https://mirrors.ustc.edu.cn/help/pypi.html)