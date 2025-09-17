#!/usr/bin/env python3
"""
DaisyUI版本交易分析系统启动脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

def main():
    """启动DaisyUI版本的应用"""
    print("🚀 启动 DaisyUI 交易分析系统...")
    
    # 检查前端目录是否存在
    frontend_dir = project_root / "apps" / "web" / "frontend"
    if not frontend_dir.exists():
        print("❌ 前端目录不存在，请先创建前端文件")
        return
    
    # 启动FastAPI服务器
    os.chdir(str(frontend_dir))
    
    try:
        from server import app
        import uvicorn
        
        print("✅ 服务器启动成功")
        print("📊 访问地址: http://localhost:8000")
        print("🛑 按 Ctrl+C 停止服务器")
        
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所需依赖:")
        print("pip install fastapi uvicorn python-multipart")
    except Exception as e:
        print(f"❌ 启动错误: {e}")

if __name__ == "__main__":
    main()