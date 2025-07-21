"""代理管理服务"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import json
from app.core import get_logger, LogLevel, LogCategory, create_log_context, cached
import asyncio
import aiohttp
import time
from urllib.parse import urlparse

from app.models.proxy import MCPProxy, ProxyCategory, ProxyTestResult, ProxyStatus, ProxyType, ProxyProtocol
from app.schemas.log import SystemLogCreate, LogLevel, LogCategory
from app.core import get_unified_config_manager
from app.core import MCPSError, handle_error, error_handler, error_context
from app.utils.exceptions import (
    ProxyNotFoundError,
    ProxyValidationError,
    CategoryNotFoundError,
)

logger = get_logger(__name__)

# 常量定义
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
DEFAULT_TEST_URL = "http://httpbin.org/ip"
DEFAULT_TEST_TIMEOUT = 10
MAX_CONCURRENT_TESTS = 10

class ProxyService:
    """代理管理服务"""

    @error_handler
    def __init__(self, db: Session):
        self.db = db

    # 代理 CRUD 操作
    def get_proxies(
        self,
        page: int = 1,
        size: int = DEFAULT_PAGE_SIZE,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[MCPProxy], int]:
        """获取代理列表"""
        # 限制页面大小
        size = min(size, MAX_PAGE_SIZE)
        query = self.db.query(MCPProxy)

        # 应用过滤条件
        if filters:
            if filters.get('category'):
                query = query.filter(MCPProxy.category == filters['category'])

            if filters.get('proxy_type'):
                query = query.filter(MCPProxy.proxy_type == ProxyType(filters['proxy_type']))

            if filters.get('status'):
                query = query.filter(MCPProxy.status == ProxyStatus(filters['status']))

            if filters.get('enabled') is not None:
                query = query.filter(MCPProxy.enabled == filters['enabled'])

            if filters.get('country'):
                query = query.filter(MCPProxy.country == filters['country'])

            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        MCPProxy.name.ilike(search_term),
                        MCPProxy.display_name.ilike(search_term),
                        MCPProxy.description.ilike(search_term),
                        MCPProxy.host.ilike(search_term)
                    )
                )

        # 获取总数
        total = query.count()

        # 分页和排序
        proxies = query.order_by(MCPProxy.priority.desc(), MCPProxy.created_at.desc()).offset(
            (page - 1) * size
        ).limit(size).all()

        return proxies, total

    @error_handler
    @cached(ttl=300)
    def get_proxy(self, proxy_id: int) -> Optional[MCPProxy]:
        """获取代理详情"""
        return self.db.query(MCPProxy).filter(MCPProxy.id == proxy_id).first()

    @error_handler
    @cached(ttl=300)
    def get_proxy_by_name(self, name: str) -> Optional[MCPProxy]:
        """根据名称获取代理"""
        return self.db.query(MCPProxy).filter(MCPProxy.name == name).first()

    @error_handler
    @cached(ttl=300)
    def get_active_proxies(self) -> List[MCPProxy]:
        """获取活跃代理列表"""
        try:
            return self.db.query(MCPProxy).filter(
                and_(
                    MCPProxy.enabled == True,
                    MCPProxy.status == ProxyStatus.ACTIVE
                )
            ).order_by(MCPProxy.priority.desc()).all()
        except Exception as e:
            logger.error(f"获取活跃代理列表失败: {e}", category=LogCategory.SYSTEM)
            return []

    @error_handler
    def create_proxy(self, proxy_data: Dict[str, Any]) -> MCPProxy:
        """创建代理"""
        try:
            # 验证代理配置
            self._validate_proxy_config(proxy_data)

            # 创建代理实例
            proxy = MCPProxy(
                name=proxy_data['name'],
                display_name=proxy_data['display_name'],
                description=proxy_data.get('description'),
                proxy_type=ProxyType(proxy_data['proxy_type']),
                protocol=ProxyProtocol(proxy_data['protocol']),
                host=proxy_data['host'],
                port=proxy_data['port'],
                username=proxy_data.get('username'),
                password=proxy_data.get('password'),
                auth_required=proxy_data.get('auth_required', False),
                timeout=proxy_data.get('timeout', 30),
                max_connections=proxy_data.get('max_connections', 100),
                keep_alive=proxy_data.get('keep_alive', True),
                country=proxy_data.get('country'),
                region=proxy_data.get('region'),
                city=proxy_data.get('city'),
                latitude=proxy_data.get('latitude'),
                longitude=proxy_data.get('longitude'),
                tags=proxy_data.get('tags', []),
                category=proxy_data.get('category'),
                priority=proxy_data.get('priority', 0),
                enabled=proxy_data.get('enabled', True),
                status=ProxyStatus.INACTIVE
            )

            self.db.add(proxy)
            self.db.commit()
            self.db.refresh(proxy)

            logger.info(f"代理创建成功: {proxy.name} (ID: {proxy.id})", category=LogCategory.SYSTEM)

            # 记录系统日志
            self._log_proxy_operation("create", proxy)

            return proxy

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建代理失败: {e}", category=LogCategory.SYSTEM)
            raise ProxyValidationError(f"创建代理失败: {e}")

    @error_handler
    def update_proxy(self, proxy_id: int, proxy_data: Dict[str, Any]) -> MCPProxy:
        """更新代理"""
        try:
            proxy = self.get_proxy(proxy_id)
            if not proxy:
                raise ProxyNotFoundError(f"代理不存在: {proxy_id}")

            # 验证更新数据
            if proxy_data.get('name') and proxy_data['name'] != proxy.name:
                existing = self.get_proxy_by_name(proxy_data['name'])
                if existing:
                    raise ProxyValidationError("代理名称已存在")

            # 更新字段
            for field, value in proxy_data.items():
                if hasattr(proxy, field) and value is not None:
                    if field in ['proxy_type', 'protocol', 'status']:
                        # 处理枚举类型
                        if field == 'proxy_type':
                            value = ProxyType(value)
                        elif field == 'protocol':
                            value = ProxyProtocol(value)
                        elif field == 'status':
                            value = ProxyStatus(value)
                    setattr(proxy, field, value)

            proxy.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(proxy)

            logger.info(f"代理更新成功: {proxy.name} (ID: {proxy.id})", category=LogCategory.SYSTEM)

            # 记录系统日志
            self._log_proxy_operation("update", proxy)

            return proxy

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新代理失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    def delete_proxy(self, proxy_id: int) -> bool:
        """删除代理"""
        try:
            proxy = self.get_proxy(proxy_id)
            if not proxy:
                raise ProxyNotFoundError(f"代理不存在: {proxy_id}")

            # 删除相关测试结果
            self.db.query(ProxyTestResult).filter(
                ProxyTestResult.proxy_id == proxy_id
            ).delete()

            # 删除代理
            self.db.delete(proxy)
            self.db.commit()

            logger.info(f"代理删除成功: {proxy.name} (ID: {proxy.id})", category=LogCategory.SYSTEM)

            # 记录系统日志
            self._log_proxy_operation("delete", proxy)

            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除代理失败: {e}", category=LogCategory.SYSTEM)
            raise

    # 代理测试功能
    @error_handler
    async def test_proxy(self, proxy_id: int, test_url: str = None) -> ProxyTestResult:
        """测试单个代理"""
        proxy = self.get_proxy(proxy_id)
        if not proxy:
            raise ProxyNotFoundError(f"代理不存在: {proxy_id}")

        if not proxy.can_test:
            raise ProxyValidationError("代理当前无法测试")

        test_url = test_url or DEFAULT_TEST_URL

        # 更新代理状态为测试中
        proxy.status = ProxyStatus.TESTING
        self.db.commit()

        try:
            result = await self._perform_proxy_test(proxy, test_url)

            # 更新代理状态和统计信息
            if result.success:
                proxy.status = ProxyStatus.ACTIVE
                proxy.last_success_at = datetime.utcnow()
                proxy.response_time_ms = result.response_time_ms
                proxy.success_requests += 1
            else:
                proxy.status = ProxyStatus.ERROR
                proxy.last_error_at = datetime.utcnow()
                proxy.last_error = result.error_message
                proxy.failed_requests += 1

            proxy.total_requests += 1
            proxy.last_tested_at = datetime.utcnow()

            # 计算成功率
            if proxy.total_requests > 0:
                proxy.success_rate = (proxy.success_requests / proxy.total_requests) * 100

            self.db.commit()

            return result

        except Exception as e:
            proxy.status = ProxyStatus.ERROR
            proxy.last_error_at = datetime.utcnow()
            proxy.last_error = str(e)
            proxy.failed_requests += 1
            proxy.total_requests += 1

            if proxy.total_requests > 0:
                proxy.success_rate = (proxy.success_requests / proxy.total_requests) * 100

            self.db.commit()
            raise

    @error_handler
    async def test_all_proxies(self) -> List[ProxyTestResult]:
        """测试所有启用的代理"""
        proxies = self.db.query(MCPProxy).filter(
            and_(
                MCPProxy.enabled == True,
                MCPProxy.status != ProxyStatus.TESTING
            )
        ).all()

        if not proxies:
            return []

        # 限制并发数量
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_TESTS)

        async def test_with_semaphore(proxy):
            async with semaphore:
                try:
                    return await self.test_proxy(proxy.id)
                except Exception as e:
                    logger.error(f"测试代理 {proxy.name} 失败: {e}", category=LogCategory.SYSTEM)
                    return None

        # 并发测试
        tasks = [test_with_semaphore(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤有效结果
        valid_results = [r for r in results if isinstance(r, ProxyTestResult)]

        logger.info(f"批量测试完成，共测试 {len(proxies)} 个代理，成功 {len(valid_results)} 个", category=LogCategory.SYSTEM)

        return valid_results

    @error_handler
    async def _perform_proxy_test(self, proxy: MCPProxy, test_url: str) -> ProxyTestResult:
        """执行代理测试"""
        start_time = time.time()

        # 构建代理配置
        proxy_url = proxy.proxy_url

        # 创建测试结果记录
        test_result = ProxyTestResult(
            proxy_id=proxy.id,
            test_url=test_url,
            success=False
        )

        try:
            timeout = aiohttp.ClientTimeout(total=proxy.timeout or DEFAULT_TEST_TIMEOUT)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    test_url,
                    proxy=proxy_url,
                    headers={'User-Agent': 'MCPS-Proxy-Tester/1.0'}
                ) as response:
                    response_time = (time.time() - start_time) * 1000  # 转换为毫秒
                    response_text = await response.text()

                    # 更新测试结果
                    test_result.success = response.status == 200
                    test_result.response_time_ms = response_time
                    test_result.status_code = response.status
                    test_result.response_headers = dict(response.headers)
                    test_result.response_size = len(response_text.encode('utf-8'))

                    # 尝试解析IP地址
                    try:
                        if 'httpbin.org' in test_url:
                            import json
                            data = json.loads(response_text)
                            test_result.ip_address = data.get('origin')
                    except:
                        pass

        except asyncio.TimeoutError:
            test_result.error_message = "连接超时"
        except aiohttp.ClientProxyConnectionError:
            test_result.error_message = "代理连接失败"
        except aiohttp.ClientConnectorError as e:
            test_result.error_message = f"连接错误: {str(e)}"
        except Exception as e:
            test_result.error_message = f"测试失败: {str(e)}"

        # 保存测试结果
        self.db.add(test_result)
        self.db.commit()
        self.db.refresh(test_result)

        return test_result

    # 统计功能
    @error_handler
    @cached(ttl=300)
    def get_proxy_stats(self) -> Dict[str, Any]:
        """获取代理统计信息"""
        try:
            total_proxies = self.db.query(MCPProxy).count()
            active_proxies = self.db.query(MCPProxy).filter(
                MCPProxy.status == ProxyStatus.ACTIVE
            ).count()
            inactive_proxies = self.db.query(MCPProxy).filter(
                MCPProxy.status == ProxyStatus.INACTIVE
            ).count()
            error_proxies = self.db.query(MCPProxy).filter(
                MCPProxy.status == ProxyStatus.ERROR
            ).count()

            # 按类型统计
            type_stats = {}
            for proxy_type in ProxyType:
                count = self.db.query(MCPProxy).filter(
                    MCPProxy.proxy_type == proxy_type
                ).count()
                type_stats[proxy_type.value] = count

            # 按国家统计
            country_stats = self.db.query(
                MCPProxy.country,
                func.count(MCPProxy.id).label('count')
            ).filter(
                MCPProxy.country.isnot(None)
            ).group_by(MCPProxy.country).all()

            # 平均响应时间
            avg_response_time = self.db.query(
                func.avg(MCPProxy.response_time_ms)
            ).filter(
                MCPProxy.response_time_ms.isnot(None)
            ).scalar() or 0

            # 平均成功率
            avg_success_rate = self.db.query(
                func.avg(MCPProxy.success_rate)
            ).filter(
                MCPProxy.success_rate.isnot(None)
            ).scalar() or 0

            return {
                "total_proxies": total_proxies,
                "active_proxies": active_proxies,
                "inactive_proxies": inactive_proxies,
                "error_proxies": error_proxies,
                "type_stats": type_stats,
                "country_stats": dict(country_stats),
                "avg_response_time_ms": round(avg_response_time, 2),
                "avg_success_rate": round(avg_success_rate, 2)
            }

        except Exception as e:
            logger.error(f"获取代理统计信息失败: {e}", category=LogCategory.SYSTEM)
            return {
                "total_proxies": 0,
                "active_proxies": 0,
                "inactive_proxies": 0,
                "error_proxies": 0,
                "type_stats": {},
                "country_stats": {},
                "avg_response_time_ms": 0,
                "avg_success_rate": 0
            }

    # 分类管理
    @error_handler
    @cached(ttl=300)
    def get_categories(self) -> List[ProxyCategory]:
        """获取代理分类列表"""
        return self.db.query(ProxyCategory).order_by(ProxyCategory.sort_order).all()

    @error_handler
    def create_category(self, category_data: Dict[str, Any]) -> ProxyCategory:
        """创建代理分类"""
        try:
            category = ProxyCategory(**category_data)
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

            logger.info(f"代理分类创建成功: {category.name}", category=LogCategory.SYSTEM)
            return category

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建代理分类失败: {e}", category=LogCategory.SYSTEM)
            raise

    # 辅助方法
    @error_handler
    def _validate_proxy_config(self, proxy_data: Dict[str, Any]):
        """验证代理配置"""
        required_fields = ['name', 'display_name', 'proxy_type', 'protocol', 'host', 'port']

        for field in required_fields:
            if not proxy_data.get(field):
                raise ProxyValidationError(f"缺少必需字段: {field}")

        # 验证端口范围
        port = proxy_data.get('port')
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ProxyValidationError("端口号必须在1-65535范围内")

        # 验证代理类型和协议
        try:
            ProxyType(proxy_data['proxy_type'])
            ProxyProtocol(proxy_data['protocol'])
        except ValueError as e:
            raise ProxyValidationError(f"无效的代理类型或协议: {e}")

        # 检查名称唯一性
        existing = self.get_proxy_by_name(proxy_data['name'])
        if existing:
            raise ProxyValidationError("代理名称已存在")

    @error_handler
    def _log_proxy_operation(self, operation: str, proxy: MCPProxy):
        """记录代理操作日志"""
        try:
            from ..system import LogService
            log_service = LogService(self.db)
            log_data = SystemLogCreate(
                level=LogLevel.INFO,
                category=LogCategory.SYSTEM,
                message=f"代理{operation}成功: {proxy.name}",
                details={
                    "proxy_id": proxy.id,
                    "proxy_name": proxy.name,
                    "proxy_type": proxy.proxy_type.value,
                    "host": proxy.host,
                    "port": proxy.port,
                    "operation": operation
                }
            )
            log_service.create_system_log(log_data)
        except Exception as log_error:
            logger.warning(f"记录代理操作日志失败: {log_error}", category=LogCategory.SYSTEM)

# 异常类已在 app.utils.exceptions 中定义
