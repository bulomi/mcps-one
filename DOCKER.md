# MCPS.ONE Docker 部署指南

本项目提供了完整的 Docker 和 Docker Compose 开发环境部署方案。

## 📋 部署文件说明

- `docker-compose.yml` - 基础配置文件
- `docker-compose.override.yml` - 开发环境覆盖配置（自动加载）
- `.env` - 环境变量配置文件

## 🚀 快速开始

### 开发环境部署

```bash
# 克隆项目
git clone <repository-url>
cd MCPS.ONE

# 启动开发环境（自动加载 override 配置）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 🔧 配置说明

### 环境变量配置

编辑 `.env` 文件来自定义配置：

```bash
# 端口配置
BACKEND_PORT=8000
FRONTEND_PORT=5173

# 安全配置（生产环境必须修改）
SECRET_KEY=your-super-secret-key-change-this-in-production

# API 地址配置
VITE_API_BASE_URL=http://localhost:8000
```

### 数据持久化

项目使用 Docker 数据卷来持久化数据：

- `backend_data` - 数据库和应用数据
- `backend_logs` - 应用日志
- `backend_uploads` - 上传文件
- `backend_config` - 配置文件

## 🌐 访问地址

- 前端应用：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/monitoring/health/live


### 数据备份与恢复

```bash
# 备份数据卷
docker run --rm -v mcps-backend-data:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz -C /data .

# 恢复数据卷
docker run --rm -v mcps-backend-data:/data -v $(pwd):/backup alpine tar xzf /backup/backup.tar.gz -C /data
```

## 🔧 开发环境配置

### 环境变量自定义

可以通过修改 `.env` 文件来自定义配置：

```bash
# 端口配置
BACKEND_PORT=8000
FRONTEND_PORT=5173

# 日志级别
LOG_LEVEL=DEBUG

# API 地址
VITE_API_BASE_URL=http://localhost:8000
```

## 📚 相关文档

- [项目主文档](./README.md)
- [后端 API 文档](./backend/README.md)
- [前端开发文档](./frontend/README.md)
- [前端 API 模块说明](./frontend/src/api/README.md)