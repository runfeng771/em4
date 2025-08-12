#!/bin/bash

# 自动登录管理系统启动脚本

echo "🌟 欢迎使用自动登录管理系统！"
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📚 安装依赖包..."
pip install -r requirements.txt

# 初始化数据库
echo "🗄️ 初始化数据库..."
export FLASK_APP=app.py
flask db init 2>/dev/null || true
flask db migrate -m "Initial migration" 2>/dev/null || true
flask db upgrade

# 创建日志目录
mkdir -p logs

echo "✅ 准备完成！"
echo "🚀 启动应用..."
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo "================================"

# 启动应用
python app.py