"""服务注册表

统一管理所有服务的注册、发现和生命周期。
"""

import asyncio
from typing import Dict, Type, Any, Optional
from app.core import get_logger
from .base import BaseService

logger = get_logger(__name__)

class ServiceRegistry:
    """服务注册表"""

    def __init__(self):
        self._services: Dict[str, BaseService] = {}
        self._service_types: Dict[str, Type[BaseService]] = {}
        self._dependencies: Dict[str, list] = {}

    def register(self, name: str, service_type: Type[BaseService], dependencies: list = None):
        """注册服务"""
        self._service_types[name] = service_type
        self._dependencies[name] = dependencies or []
        logger.info(f"服务已注册: {name}")

    async def get_service(self, name: str) -> Optional[BaseService]:
        """获取服务实例"""
        if name not in self._services:
            await self._initialize_service(name)
        return self._services.get(name)

    async def _initialize_service(self, name: str):
        """初始化服务"""
        if name in self._services:
            return

        # 先初始化依赖服务
        for dep in self._dependencies.get(name, []):
            await self._initialize_service(dep)

        # 初始化当前服务
        service_type = self._service_types.get(name)
        if service_type:
            service = service_type()
            await service.initialize()
            self._services[name] = service
            logger.info(f"服务已初始化: {name}")

# 全局服务注册表实例
service_registry = ServiceRegistry()
