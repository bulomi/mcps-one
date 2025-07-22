#!/bin/bash

# MCPS.ONE 一键启动脚本 (Unix/Linux/macOS)

set -e  # 遇到错误立即退出

echo "========================================"
echo "MCPS.ONE 一键启动脚本 (Unix/Linux/macOS)"
echo "========================================"
echo

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

log_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查是否在项目根目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    log_error "请在项目根目录运行此脚本"
    exit 1
fi

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        log_error "Python 未安装或未添加到PATH"
        log_error "请安装 Python 3.8+ 并添加到系统PATH"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# 检查Python版本
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    log_error "Python 版本过低，需要 Python 3.8+，当前版本: $PYTHON_VERSION"
    exit 1
fi

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    log_error "Node.js 未安装或未添加到PATH"
    log_error "请安装 Node.js 16+ 并添加到系统PATH"
    exit 1
fi

# 检查Node.js版本
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    log_error "Node.js 版本过低，需要 Node.js 16+，当前版本: $(node --version)"
    exit 1
fi

# 检查npm是否安装
if ! command -v npm &> /dev/null; then
    log_error "npm 未安装或未添加到PATH"
    exit 1
fi

log_success "环境检查通过"
echo

# 启动后端服务
echo "========================================"
log_info "启动后端服务..."
echo "========================================"
cd backend

# 检查uv是否安装
if ! command -v uv &> /dev/null; then
    log_info "uv 未安装，正在安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
    if [ $? -ne 0 ]; then
        log_error "安装 uv 失败"
        exit 1
    fi
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    log_info "使用 uv 创建虚拟环境..."
    uv venv
    if [ $? -ne 0 ]; then
        log_error "创建虚拟环境失败"
        exit 1
    fi
fi

# 激活虚拟环境
log_info "激活虚拟环境..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    log_error "激活虚拟环境失败"
    exit 1
fi

# 安装Python依赖（如果需要）
if [ ! -f ".venv/pyvenv.cfg" ]; then
    log_info "使用 uv 安装Python依赖..."
    uv pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        log_error "安装Python依赖失败"
        exit 1
    fi
else
    log_info "检查Python依赖更新..."
    uv pip install -r requirements.txt --quiet
fi

# 检查数据库目录
if [ ! -d "data" ]; then
    log_info "创建数据目录..."
    mkdir -p data
fi

# 启动后端服务（后台运行）
log_info "启动后端服务..."
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid

# 等待后端服务启动
log_info "等待后端服务启动..."
sleep 5

# 检查后端服务是否启动成功
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    log_error "后端服务启动失败，请检查 backend.log"
    exit 1
fi

# 返回项目根目录
cd ..

# 启动前端服务
echo "========================================"
log_info "启动前端服务..."
echo "========================================"
cd frontend

# 检查node_modules
if [ ! -d "node_modules" ]; then
    log_info "安装前端依赖..."
    npm install
    if [ $? -ne 0 ]; then
        log_error "安装前端依赖失败"
        exit 1
    fi
else
    log_info "前端依赖已安装，跳过..."
fi

# 启动前端开发服务器（后台运行）
log_info "启动前端开发服务器..."
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid

# 返回项目根目录
cd ..

# 等待前端服务启动
log_info "等待前端服务启动..."
sleep 3

# 检查前端服务是否启动成功
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    log_error "前端服务启动失败，请检查 frontend.log"
    exit 1
fi

echo
echo "========================================"
log_success "启动完成！"
echo "========================================"
echo "后端服务: http://localhost:8000"
echo "前端服务: http://localhost:5173"
echo "API文档: http://localhost:8000/docs"
echo
echo "日志文件:"
echo "  后端日志: backend.log"
echo "  前端日志: frontend.log"
echo
echo "进程ID:"
echo "  后端PID: $BACKEND_PID (保存在 backend.pid)"
echo "  前端PID: $FRONTEND_PID (保存在 frontend.pid)"
echo
echo "停止服务请运行: ./stop.sh"
echo