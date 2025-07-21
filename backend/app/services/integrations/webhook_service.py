import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from urllib.parse import urlparse
from app.core import get_logger

logger = get_logger(__name__)

class WebhookService:
    """Webhook服务类"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def send_webhook(self, url: str, data: Dict[str, Any],
                          headers: Optional[Dict[str, str]] = None,
                          method: str = "POST") -> Dict[str, Any]:
        """发送Webhook请求"""
        try:
            # 验证URL格式
            if not url or not url.strip():
                return {
                    "success": False,
                    "message": "Webhook URL不能为空",
                    "timestamp": datetime.utcnow().isoformat()
                }

            url = url.strip()
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]) or parsed_url.scheme not in ['http', 'https']:
                return {
                    "success": False,
                    "message": "Webhook URL格式不正确，必须是有效的HTTP或HTTPS地址",
                    "url": url,
                    "timestamp": datetime.utcnow().isoformat()
                }
            # 默认headers
            default_headers = {
                "Content-Type": "application/json",
                "User-Agent": "MCPS.ONE-Webhook/1.0"
            }

            if headers:
                default_headers.update(headers)

            timeout = aiohttp.ClientTimeout(total=self.timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                if method.upper() == "POST":
                    async with session.post(url, json=data, headers=default_headers) as response:
                        response_text = await response.text()

                        result = {
                            "success": response.status < 400,
                            "status_code": response.status,
                            "response_text": response_text[:1000],  # 限制响应长度
                            "url": url,
                            "timestamp": datetime.utcnow().isoformat()
                        }

                        if response.status < 400:
                            result["message"] = f"Webhook请求成功 (状态码: {response.status})"
                            logger.info(f"Webhook发送成功: {url} - {response.status}")
                        else:
                            result["message"] = f"Webhook请求失败 (状态码: {response.status})"
                            logger.warning(f"Webhook发送失败: {url} - {response.status}")

                        return result

                elif method.upper() == "GET":
                    async with session.get(url, headers=default_headers) as response:
                        response_text = await response.text()

                        result = {
                            "success": response.status < 400,
                            "status_code": response.status,
                            "response_text": response_text[:1000],
                            "url": url,
                            "timestamp": datetime.utcnow().isoformat()
                        }

                        if response.status < 400:
                            result["message"] = f"Webhook GET请求成功 (状态码: {response.status})"
                            logger.info(f"Webhook GET成功: {url} - {response.status}")
                        else:
                            result["message"] = f"Webhook GET请求失败 (状态码: {response.status})"
                            logger.warning(f"Webhook GET失败: {url} - {response.status}")

                        return result

                else:
                    return {
                        "success": False,
                        "message": f"不支持的HTTP方法: {method}",
                        "timestamp": datetime.utcnow().isoformat()
                    }

        except aiohttp.ClientConnectorError:
            error_msg = f"无法连接到目标URL: {url}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "url": url,
                "timestamp": datetime.utcnow().isoformat()
            }
        except aiohttp.ClientTimeout:
            error_msg = f"Webhook请求超时 (超过{self.timeout}秒): {url}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "url": url,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            error_msg = f"Webhook请求失败: {str(e)}"
            logger.error(f"Webhook发送异常: {url} - {e}")
            return {
                "success": False,
                "message": error_msg,
                "url": url,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def send_test_webhook(self, url: str) -> Dict[str, Any]:
        """发送测试Webhook"""
        # 检测URL是否为飞书群机器人webhook
        if "open.feishu.cn" in url or "open-feishu.cn" in url:
            # 飞书群机器人格式
            test_data = {
                "msg_type": "text",
                "content": {
                    "text": f"🤖 MCPS.ONE 系统测试通知\n\n📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n✅ 状态: Webhook连接正常\n🔗 来源: MCPS.ONE 系统"
                }
            }
        else:
            # 通用格式
            test_data = {
                "event": "test",
                "source": "MCPS.ONE",
                "message": "这是一个来自 MCPS.ONE 系统的测试Webhook请求",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "test_id": f"test_{int(datetime.utcnow().timestamp())}",
                    "system_status": "healthy",
                    "version": "1.0.0"
                }
            }

        return await self.send_webhook(url, test_data)

    def send_webhook_sync(self, url: str, data: Dict[str, Any],
                         headers: Optional[Dict[str, str]] = None,
                         method: str = "POST") -> Dict[str, Any]:
        """同步发送Webhook请求"""
        try:
            # 检查是否已有运行中的事件循环
            loop = asyncio.get_running_loop()
            # 如果有运行中的循环，使用线程池执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_async_webhook_with_data, url, data, headers, method)
                return future.result(timeout=self.timeout)
        except RuntimeError:
            # 没有运行中的事件循环，创建新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.send_webhook(url, data, headers, method)
                )
            finally:
                loop.close()

    def _run_async_webhook_with_data(self, url: str, data: Dict[str, Any],
                                   headers: Optional[Dict[str, str]] = None,
                                   method: str = "POST") -> Dict[str, Any]:
        """在新的事件循环中运行异步webhook（带数据）"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.send_webhook(url, data, headers, method))
        finally:
            loop.close()

    def send_test_webhook_sync(self, url: str) -> Dict[str, Any]:
        """同步发送测试Webhook"""
        try:
            # 检查是否已有运行中的事件循环
            loop = asyncio.get_running_loop()
            # 如果有运行中的循环，使用asyncio.create_task在当前循环中运行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_async_webhook, url)
                return future.result(timeout=self.timeout)
        except RuntimeError:
            # 没有运行中的事件循环，创建新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.send_test_webhook(url))
            finally:
                loop.close()

    def _run_async_webhook(self, url: str) -> Dict[str, Any]:
        """在新的事件循环中运行异步webhook"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.send_test_webhook(url))
        finally:
            loop.close()

    async def validate_webhook_url(self, url: str) -> Dict[str, Any]:
        """验证Webhook URL的可达性"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)  # 验证时使用较短超时

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.head(url) as response:
                    return {
                        "success": True,
                        "status_code": response.status,
                        "message": f"URL可达 (状态码: {response.status})",
                        "url": url,
                        "timestamp": datetime.utcnow().isoformat()
                    }

        except Exception as e:
            return {
                "success": False,
                "message": f"URL验证失败: {str(e)}",
                "url": url,
                "timestamp": datetime.utcnow().isoformat()
            }

    def validate_webhook_url_sync(self, url: str) -> Dict[str, Any]:
        """同步验证Webhook URL"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.validate_webhook_url(url))
