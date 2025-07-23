#!/bin/bash

# MCPS.ONE 停止服务脚本 (Unix/Linux/macOS)

set -e  # 遇到错误立即退出

echo "========================================"
echo "MCPS.ONE 停止服务脚本"
echo "========================================"
echo

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 停止后端服务
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        log_info "停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        sleep 2
        if kill -0 $BACKEND_PID 2>/dev/null; then
            log_warning "强制停止后端服务..."
            kill -9 $BACKEND_PID
        fi
        log_success "后端服务已停止"
    else
        log_warning "后端服务进程不存在"
    fi
    rm -f backend.pid
else
    log_warning "未找到后端服务PID文件"
fi

# 停止前端服务
if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        log_info "停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        sleep 2
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            log_warning "强制停止前端服务..."
            kill -9 $FRONTEND_PID
        fi
        log_success "前端服务已停止"
    else
        log_warning "前端服务进程不存在"
    fi
    rm -f frontend.pid
else
    log_warning "未找到前端服务PID文件"
fi

# 清理其他可能的进程
log_info "清理其他相关进程..."

# 查找并停止可能的uvicorn进程
UVICORN_PIDS=$(pgrep -f "uvicorn.*app.main:app" 2>/dev/null || true)
if [ ! -z "$UVICORN_PIDS" ]; then
    log_info "发现uvicorn进程，正在停止..."
    echo $UVICORN_PIDS | xargs kill 2>/dev/null || true
    sleep 1
    echo $UVICORN_PIDS | xargs kill -9 2>/dev/null || true
fi

# 查找并停止可能的npm/node进程（谨慎处理，只停止dev server）
NODE_PIDS=$(pgrep -f "node.*vite" 2>/dev/null || true)
if [ ! -z "$NODE_PIDS" ]; then
    log_info "发现Vite开发服务器进程，正在停止..."
    echo $NODE_PIDS | xargs kill 2>/dev/null || true
    sleep 1
    echo $NODE_PIDS | xargs kill -9 2>/dev/null || true
fi

echo
log_success "所有服务已停止"
echo