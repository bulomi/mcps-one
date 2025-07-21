"""请求路由器模块

负责MCP请求的智能路由和负载均衡。
主要功能：
- 请求路由策略
- 负载均衡算法
- 故障转移机制
- 请求重试逻辑
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from app.core import get_logger
from app.utils.exceptions import (
    ToolNotFoundError,
    MCPSException as MCPServiceError,
    RequestRoutingError
)

logger = get_logger(__name__)

# 临时占位符类，待实现
class ToolRegistry:
    pass

class ToolInstance:
    def __init__(self, instance_id: str):
        self.instance_id = instance_id

class ToolHealthStatus:
    pass

class LoadBalanceStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RANDOM = "weighted_random"
    HEALTH_AWARE = "health_aware"

class FailoverStrategy(Enum):
    """故障转移策略"""
    IMMEDIATE = "immediate"  # 立即转移到其他实例
    RETRY_THEN_FAILOVER = "retry_then_failover"  # 重试后转移
    CIRCUIT_BREAKER = "circuit_breaker"  # 熔断器模式

@dataclass
class RoutingRule:
    """路由规则"""
    tool_pattern: str  # 工具名称模式
    method_pattern: Optional[str] = None  # 方法名称模式
    load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN
    failover_strategy: FailoverStrategy = FailoverStrategy.RETRY_THEN_FAILOVER
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    priority: int = 0  # 优先级，数字越大优先级越高

@dataclass
class RequestContext:
    """请求上下文"""
    request_id: str
    tool_name: str
    method: str
    params: Dict[str, Any]
    timestamp: datetime
    client_info: Optional[Dict[str, Any]] = None
    routing_metadata: Optional[Dict[str, Any]] = None

@dataclass
class RoutingResult:
    """路由结果"""
    instance: ToolInstance
    routing_rule: RoutingRule
    attempt_count: int = 1
    total_time: float = 0.0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class RequestRouter:
    """请求路由器

    负责将MCP请求路由到合适的工具实例，支持多种负载均衡和故障转移策略。
    """

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry

        # 路由规则
        self._routing_rules: List[RoutingRule] = []
        self._default_rule = RoutingRule(
            tool_pattern="*",
            load_balance_strategy=LoadBalanceStrategy.HEALTH_AWARE,
            failover_strategy=FailoverStrategy.RETRY_THEN_FAILOVER
        )

        # 负载均衡状态
        self._round_robin_counters: Dict[str, int] = {}  # tool_name -> counter
        self._connection_counts: Dict[str, int] = {}  # instance_id -> count

        # 熔断器状态
        self._circuit_breakers: Dict[str, Dict[str, Any]] = {}  # instance_id -> state

        # 统计信息
        self._request_stats: Dict[str, Dict[str, Any]] = {}  # tool_name -> stats

        # 路由钩子
        self.before_route_hooks: List[Callable] = []
        self.after_route_hooks: List[Callable] = []
        self.on_route_error_hooks: List[Callable] = []

    async def initialize(self) -> None:
        """初始化路由器"""
        try:
            logger.info("初始化请求路由器...")

            # 加载默认路由规则
            await self._load_default_rules()

            logger.info("请求路由器初始化完成")

        except Exception as e:
            logger.error(f"请求路由器初始化失败: {e}")
            raise MCPServiceError(f"路由器初始化失败: {e}")

    async def route_request(self, context: RequestContext) -> RoutingResult:
        """路由请求到合适的工具实例

        Args:
            context: 请求上下文

        Returns:
            路由结果

        Raises:
            ToolNotFoundError: 工具不存在
            RequestRoutingError: 路由失败
        """
        start_time = datetime.now()

        try:
            logger.debug(f"路由请求: {context.tool_name}.{context.method} [{context.request_id}]")

            # 执行前置钩子
            for hook in self.before_route_hooks:
                await hook(context)

            # 查找匹配的路由规则
            routing_rule = self._find_matching_rule(context)

            # 获取可用实例
            available_instances = await self._get_available_instances(context.tool_name)
            if not available_instances:
                raise ToolNotFoundError(f"没有可用的工具实例: {context.tool_name}")

            # 执行路由策略
            result = await self._execute_routing_strategy(
                context, routing_rule, available_instances, start_time
            )

            # 更新统计信息
            await self._update_stats(context.tool_name, True, result.total_time)

            # 执行后置钩子
            for hook in self.after_route_hooks:
                await hook(context, result)

            logger.debug(f"路由成功: {context.tool_name} -> {result.instance.instance_id} [{context.request_id}]")

            return result

        except Exception as e:
            # 更新统计信息
            total_time = (datetime.now() - start_time).total_seconds()
            await self._update_stats(context.tool_name, False, total_time)

            # 执行错误钩子
            for hook in self.on_route_error_hooks:
                try:
                    await hook(context, e)
                except Exception as hook_error:
                    logger.error(f"路由错误钩子执行失败: {hook_error}")

            logger.error(f"路由失败: {context.tool_name}.{context.method} [{context.request_id}], error: {e}")
            raise RequestRoutingError(f"请求路由失败: {e}")

    async def add_routing_rule(self, rule: RoutingRule) -> None:
        """添加路由规则

        Args:
            rule: 路由规则
        """
        # 按优先级插入
        inserted = False
        for i, existing_rule in enumerate(self._routing_rules):
            if rule.priority > existing_rule.priority:
                self._routing_rules.insert(i, rule)
                inserted = True
                break

        if not inserted:
            self._routing_rules.append(rule)

        logger.info(f"添加路由规则: {rule.tool_pattern} (优先级: {rule.priority})")

    async def remove_routing_rule(self, tool_pattern: str) -> None:
        """移除路由规则

        Args:
            tool_pattern: 工具名称模式
        """
        self._routing_rules = [
            rule for rule in self._routing_rules
            if rule.tool_pattern != tool_pattern
        ]

        logger.info(f"移除路由规则: {tool_pattern}")

    async def update_connection_count(self, instance_id: str, delta: int) -> None:
        """更新连接计数

        Args:
            instance_id: 实例ID
            delta: 变化量（+1表示增加连接，-1表示减少连接）
        """
        current_count = self._connection_counts.get(instance_id, 0)
        new_count = max(0, current_count + delta)
        self._connection_counts[instance_id] = new_count

        logger.debug(f"更新连接计数: {instance_id}, {current_count} -> {new_count}")

    async def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息

        Returns:
            路由统计信息
        """
        return {
            "routing_rules_count": len(self._routing_rules),
            "connection_counts": self._connection_counts.copy(),
            "circuit_breakers": self._circuit_breakers.copy(),
            "request_stats": self._request_stats.copy()
        }

    def _find_matching_rule(self, context: RequestContext) -> RoutingRule:
        """查找匹配的路由规则

        Args:
            context: 请求上下文

        Returns:
            匹配的路由规则
        """
        for rule in self._routing_rules:
            if self._match_pattern(context.tool_name, rule.tool_pattern):
                if rule.method_pattern is None or self._match_pattern(context.method, rule.method_pattern):
                    return rule

        return self._default_rule

    def _match_pattern(self, value: str, pattern: str) -> bool:
        """匹配模式

        Args:
            value: 值
            pattern: 模式（支持*通配符）

        Returns:
            是否匹配
        """
        if pattern == "*":
            return True

        if "*" not in pattern:
            return value == pattern

        # 简单的通配符匹配
        import fnmatch
        return fnmatch.fnmatch(value, pattern)

    async def _get_available_instances(self, tool_name: str) -> List[ToolInstance]:
        """获取可用实例

        Args:
            tool_name: 工具名称

        Returns:
            可用实例列表
        """
        all_instances = await self.tool_registry.get_tool_instances(tool_name)
        available_instances = []

        for instance in all_instances:
            # 检查实例健康状态
            if instance.status != ToolHealthStatus.HEALTHY:
                continue

            # 检查熔断器状态
            if self._is_circuit_breaker_open(instance.instance_id):
                continue

            available_instances.append(instance)

        return available_instances

    async def _execute_routing_strategy(
        self,
        context: RequestContext,
        routing_rule: RoutingRule,
        available_instances: List[ToolInstance],
        start_time: datetime
    ) -> RoutingResult:
        """执行路由策略

        Args:
            context: 请求上下文
            routing_rule: 路由规则
            available_instances: 可用实例列表
            start_time: 开始时间

        Returns:
            路由结果
        """
        errors = []

        for attempt in range(routing_rule.max_retries + 1):
            try:
                # 选择实例
                instance = self._select_instance(
                    available_instances,
                    routing_rule.load_balance_strategy,
                    context.tool_name
                )

                if not instance:
                    raise RequestRoutingError("没有可用的实例")

                # 创建路由结果
                total_time = (datetime.now() - start_time).total_seconds()
                result = RoutingResult(
                    instance=instance,
                    routing_rule=routing_rule,
                    attempt_count=attempt + 1,
                    total_time=total_time,
                    errors=errors.copy()
                )

                return result

            except Exception as e:
                error_msg = f"尝试 {attempt + 1}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"路由尝试失败: {error_msg}")

                # 如果不是最后一次尝试，等待后重试
                if attempt < routing_rule.max_retries:
                    await asyncio.sleep(routing_rule.retry_delay * (attempt + 1))

                    # 根据故障转移策略处理
                    if routing_rule.failover_strategy == FailoverStrategy.IMMEDIATE:
                        # 立即从可用实例中移除失败的实例
                        available_instances = [
                            inst for inst in available_instances
                            if inst.instance_id != (instance.instance_id if 'instance' in locals() else None)
                        ]
                    elif routing_rule.failover_strategy == FailoverStrategy.CIRCUIT_BREAKER:
                        # 触发熔断器
                        if 'instance' in locals():
                            await self._trigger_circuit_breaker(instance.instance_id)

        # 所有尝试都失败
        raise RequestRoutingError(f"所有路由尝试都失败: {'; '.join(errors)}")

    def _select_instance(
        self,
        instances: List[ToolInstance],
        strategy: LoadBalanceStrategy,
        tool_name: str
    ) -> Optional[ToolInstance]:
        """选择实例

        Args:
            instances: 实例列表
            strategy: 负载均衡策略
            tool_name: 工具名称

        Returns:
            选中的实例
        """
        if not instances:
            return None

        if strategy == LoadBalanceStrategy.RANDOM:
            return random.choice(instances)

        elif strategy == LoadBalanceStrategy.ROUND_ROBIN:
            counter = self._round_robin_counters.get(tool_name, 0)
            selected = instances[counter % len(instances)]
            self._round_robin_counters[tool_name] = counter + 1
            return selected

        elif strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            # 选择连接数最少的实例
            min_connections = float('inf')
            selected = None

            for instance in instances:
                connections = self._connection_counts.get(instance.instance_id, 0)
                if connections < min_connections:
                    min_connections = connections
                    selected = instance

            return selected

        elif strategy == LoadBalanceStrategy.WEIGHTED_RANDOM:
            # 基于健康状态的加权随机
            weights = []
            for instance in instances:
                # 根据错误计数计算权重
                weight = max(1, 10 - instance.error_count)
                weights.append(weight)

            return random.choices(instances, weights=weights)[0]

        elif strategy == LoadBalanceStrategy.HEALTH_AWARE:
            # 健康感知选择：优先选择错误最少的实例
            instances_sorted = sorted(instances, key=lambda x: x.error_count)
            return instances_sorted[0]

        else:
            # 默认随机选择
            return random.choice(instances)

    def _is_circuit_breaker_open(self, instance_id: str) -> bool:
        """检查熔断器是否开启

        Args:
            instance_id: 实例ID

        Returns:
            熔断器是否开启
        """
        breaker_state = self._circuit_breakers.get(instance_id)
        if not breaker_state:
            return False

        # 检查熔断器是否应该重置
        if breaker_state['state'] == 'open':
            reset_time = breaker_state['reset_time']
            if datetime.now() >= reset_time:
                # 进入半开状态
                breaker_state['state'] = 'half_open'
                logger.info(f"熔断器进入半开状态: {instance_id}")
                return False
            return True

        return False

    async def _trigger_circuit_breaker(self, instance_id: str) -> None:
        """触发熔断器

        Args:
            instance_id: 实例ID
        """
        breaker_state = self._circuit_breakers.get(instance_id, {
            'state': 'closed',
            'failure_count': 0,
            'last_failure_time': None,
            'reset_time': None
        })

        breaker_state['failure_count'] += 1
        breaker_state['last_failure_time'] = datetime.now()

        # 如果失败次数超过阈值，开启熔断器
        if breaker_state['failure_count'] >= 5:  # 阈值可配置
            breaker_state['state'] = 'open'
            breaker_state['reset_time'] = datetime.now() + timedelta(seconds=60)  # 60秒后重试
            logger.warning(f"熔断器开启: {instance_id}")

        self._circuit_breakers[instance_id] = breaker_state

    async def _reset_circuit_breaker(self, instance_id: str) -> None:
        """重置熔断器

        Args:
            instance_id: 实例ID
        """
        if instance_id in self._circuit_breakers:
            self._circuit_breakers[instance_id] = {
                'state': 'closed',
                'failure_count': 0,
                'last_failure_time': None,
                'reset_time': None
            }
            logger.info(f"熔断器重置: {instance_id}")

    async def _update_stats(self, tool_name: str, success: bool, response_time: float) -> None:
        """更新统计信息

        Args:
            tool_name: 工具名称
            success: 是否成功
            response_time: 响应时间
        """
        if tool_name not in self._request_stats:
            self._request_stats[tool_name] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'total_response_time': 0.0,
                'avg_response_time': 0.0,
                'last_request_time': None
            }

        stats = self._request_stats[tool_name]
        stats['total_requests'] += 1
        stats['total_response_time'] += response_time
        stats['last_request_time'] = datetime.now().isoformat()

        if success:
            stats['successful_requests'] += 1
        else:
            stats['failed_requests'] += 1

        # 计算平均响应时间
        if stats['total_requests'] > 0:
            stats['avg_response_time'] = stats['total_response_time'] / stats['total_requests']

    async def _load_default_rules(self) -> None:
        """加载默认路由规则"""
        # 可以从配置文件加载路由规则
        # 这里先添加一些默认规则

        # 文件系统工具使用轮询策略
        await self.add_routing_rule(RoutingRule(
            tool_pattern="filesystem-mcp",
            load_balance_strategy=LoadBalanceStrategy.ROUND_ROBIN,
            priority=10
        ))

        # 数据库工具使用最少连接策略
        await self.add_routing_rule(RoutingRule(
            tool_pattern="*-mcp",
            method_pattern="query*",
            load_balance_strategy=LoadBalanceStrategy.LEAST_CONNECTIONS,
            priority=5
        ))

        logger.info(f"加载默认路由规则完成，共 {len(self._routing_rules)} 条规则")

    async def start(self) -> None:
        """启动路由器"""
        try:
            logger.info("启动请求路由器...")

            # 初始化统计信息
            self._request_stats.clear()
            self._connection_counts.clear()
            self._circuit_breakers.clear()

            logger.info("请求路由器启动完成")

        except Exception as e:
            logger.error(f"请求路由器启动失败: {e}")
            raise MCPServiceError(f"路由器启动失败: {e}")

    async def stop(self) -> None:
        """停止路由器"""
        try:
            logger.info("停止请求路由器...")

            # 清理状态
            self._round_robin_counters.clear()
            self._connection_counts.clear()
            self._circuit_breakers.clear()

            logger.info("请求路由器停止完成")

        except Exception as e:
            logger.error(f"请求路由器停止失败: {e}")
            raise MCPServiceError(f"路由器停止失败: {e}")

    async def reload_config(self) -> None:
        """重新加载配置"""
        try:
            logger.info("重新加载路由器配置...")

            # 清理现有规则
            self._routing_rules.clear()

            # 重新加载默认规则
            await self._load_default_rules()

            logger.info("路由器配置重新加载完成")

        except Exception as e:
            logger.error(f"路由器配置重新加载失败: {e}")
            raise MCPServiceError(f"路由器配置重新加载失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        return {
            "routing_rules_count": len(self._routing_rules),
            "active_connections": sum(self._connection_counts.values()),
            "circuit_breakers": len([cb for cb in self._circuit_breakers.values() if cb['state'] == 'open']),
            "request_stats": self._request_stats.copy()
        }

    async def forward_request(self, tool_config: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
        """转发请求到工具实例

        Args:
            tool_config: 工具配置
            request: MCP请求

        Returns:
            MCP响应
        """
        # 创建请求上下文
        context = RequestContext(
            request_id=request.get('id', 'unknown'),
            tool_name=tool_config.get('name', 'unknown'),
            method=request.get('method', 'unknown'),
            params=request.get('params', {}),
            timestamp=datetime.now()
        )

        # 路由请求
        result = await self.route_request(context)

        # 这里应该实际转发请求到工具实例
        # 暂时返回模拟响应
        return {
            "jsonrpc": "2.0",
            "id": request.get('id'),
            "result": {
                "routed_to": result.instance.instance_id,
                "tool_name": context.tool_name,
                "method": context.method
            }
        }
