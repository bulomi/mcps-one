"""代理相关数据模型"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, Dict, Any

from app.core.database import Base

class ProxyStatus(PyEnum):
    """代理状态枚举"""
    INACTIVE = "inactive"    # 未激活
    ACTIVE = "active"        # 激活
    ERROR = "error"          # 错误状态
    TESTING = "testing"      # 测试中
    UNKNOWN = "unknown"      # 未知状态

class ProxyType(PyEnum):
    """代理类型枚举"""
    HTTP = "http"            # HTTP代理
    HTTPS = "https"          # HTTPS代理
    SOCKS4 = "socks4"        # SOCKS4代理
    SOCKS5 = "socks5"        # SOCKS5代理

class ProxyProtocol(PyEnum):
    """代理协议枚举"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS = "socks"

class MCPProxy(Base):
    """MCP 代理配置模型"""
    __tablename__ = "mcp_proxies"

    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False, comment="代理名称")
    display_name = Column(String(200), nullable=False, comment="显示名称")
    description = Column(Text, comment="代理描述")

    # 代理配置
    proxy_type = Column(Enum(ProxyType, values_callable=lambda x: [e.value for e in x]), default=ProxyType.HTTP, comment="代理类型")
    protocol = Column(Enum(ProxyProtocol, values_callable=lambda x: [e.value for e in x]), default=ProxyProtocol.HTTP, comment="代理协议")
    host = Column(String(255), nullable=False, comment="代理主机")
    port = Column(Integer, nullable=False, comment="代理端口")

    # 认证信息
    username = Column(String(100), comment="用户名")
    password = Column(String(255), comment="密码")
    auth_required = Column(Boolean, default=False, comment="是否需要认证")

    # 连接配置
    timeout = Column(Integer, default=30, comment="连接超时时间（秒）")
    max_connections = Column(Integer, default=100, comment="最大连接数")
    keep_alive = Column(Boolean, default=True, comment="保持连接")

    # 状态信息
    status = Column(Enum(ProxyStatus, values_callable=lambda x: [e.value for e in x]), default=ProxyStatus.INACTIVE, comment="当前状态")
    last_tested_at = Column(DateTime, comment="最后测试时间")
    last_success_at = Column(DateTime, comment="最后成功时间")
    last_error_at = Column(DateTime, comment="最后错误时间")
    last_error = Column(Text, comment="最后错误信息")

    # 性能统计
    response_time_ms = Column(Float, comment="响应时间（毫秒）")
    success_rate = Column(Float, default=0.0, comment="成功率")
    total_requests = Column(Integer, default=0, comment="总请求数")
    success_requests = Column(Integer, default=0, comment="成功请求数")
    failed_requests = Column(Integer, default=0, comment="失败请求数")

    # 地理位置信息
    country = Column(String(50), comment="国家")
    region = Column(String(100), comment="地区")
    city = Column(String(100), comment="城市")
    latitude = Column(Float, comment="纬度")
    longitude = Column(Float, comment="经度")

    # 标签和分类
    tags = Column(JSON, default=list, comment="代理标签")
    category = Column(String(50), index=True, comment="代理分类")
    priority = Column(Integer, default=0, comment="优先级")

    # 系统字段
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<MCPProxy(id={self.id}, name='{self.name}', status='{self.status}')>"

    @property
    def is_active(self) -> bool:
        """检查代理是否激活"""
        return self.status == ProxyStatus.ACTIVE

    @property
    def can_test(self) -> bool:
        """检查代理是否可以测试"""
        return self.enabled and self.status != ProxyStatus.TESTING

    @property
    def proxy_url(self) -> str:
        """获取代理URL"""
        if self.auth_required and self.username and self.password:
            return f"{self.protocol.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        else:
            return f"{self.protocol.value}://{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "proxy_type": self.proxy_type.value if self.proxy_type else None,
            "protocol": self.protocol.value if self.protocol else None,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "auth_required": self.auth_required,
            "timeout": self.timeout,
            "max_connections": self.max_connections,
            "keep_alive": self.keep_alive,
            "status": self.status.value if self.status else None,
            "last_tested_at": self.last_tested_at.isoformat() if self.last_tested_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_error_at": self.last_error_at.isoformat() if self.last_error_at else None,
            "last_error": self.last_error,
            "response_time_ms": self.response_time_ms,
            "success_rate": self.success_rate,
            "total_requests": self.total_requests,
            "success_requests": self.success_requests,
            "failed_requests": self.failed_requests,
            "country": self.country,
            "region": self.region,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "tags": self.tags or [],
            "category": self.category,
            "priority": self.priority,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "proxy_url": self.proxy_url
        }

class ProxyCategory(Base):
    """代理分类模型"""
    __tablename__ = "proxy_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False, comment="分类名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, comment="分类描述")
    icon = Column(String(50), comment="图标")
    color = Column(String(20), comment="颜色")
    sort_order = Column(Integer, default=0, comment="排序")

    # 系统字段
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<ProxyCategory(id={self.id}, name='{self.name}')>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class ProxyTestResult(Base):
    """代理测试结果模型"""
    __tablename__ = "proxy_test_results"

    id = Column(Integer, primary_key=True, index=True)
    proxy_id = Column(Integer, nullable=False, comment="代理ID")
    test_url = Column(String(500), nullable=False, comment="测试URL")

    # 测试结果
    success = Column(Boolean, nullable=False, comment="是否成功")
    response_time_ms = Column(Float, comment="响应时间（毫秒）")
    status_code = Column(Integer, comment="HTTP状态码")
    error_message = Column(Text, comment="错误信息")

    # 响应信息
    response_headers = Column(JSON, comment="响应头")
    response_size = Column(Integer, comment="响应大小（字节）")

    # 网络信息
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(String(500), comment="用户代理")

    # 系统字段
    tested_at = Column(DateTime, default=func.now(), comment="测试时间")

    def __repr__(self):
        return f"<ProxyTestResult(id={self.id}, proxy_id={self.proxy_id}, success={self.success})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "proxy_id": self.proxy_id,
            "test_url": self.test_url,
            "success": self.success,
            "response_time_ms": self.response_time_ms,
            "status_code": self.status_code,
            "error_message": self.error_message,
            "response_headers": self.response_headers,
            "response_size": self.response_size,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "tested_at": self.tested_at.isoformat() if self.tested_at else None,
        }
