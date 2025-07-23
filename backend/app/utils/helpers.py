"""辅助工具函数"""

import json
import hashlib
import secrets
import re
import subprocess
import psutil
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def generate_id(length: int = 8) -> str:
    """生成随机ID"""
    return secrets.token_hex(length)

# 会话管理功能已移除
# def generate_session_id() -> str:
#     """生成会话ID"""
#     return f"session_{generate_id(16)}"

def generate_message_id() -> str:
    """生成消息ID"""
    return f"msg_{generate_id(12)}"

def hash_string(text: str, algorithm: str = "sha256") -> str:
    """计算字符串哈希值"""
    if algorithm == "md5":
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(text.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(text.encode()).hexdigest()
    else:
        raise ValueError(f"不支持的哈希算法: {algorithm}")

def validate_json(data: str) -> bool:
    """验证JSON格式"""
    try:
        json.loads(data)
        return True
    except (json.JSONDecodeError, TypeError):
        return False

def safe_json_loads(data: str, default: Any = None) -> Any:
    """安全的JSON解析"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(data: Any, default: Any = None) -> str:
    """安全的JSON序列化"""
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return json.dumps(default or {})

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_url(url: str) -> bool:
    """验证URL格式"""
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
    return re.match(pattern, url) is not None

def validate_port(port: Union[str, int]) -> bool:
    """验证端口号"""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    # 移除或替换非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(illegal_chars, '_', filename)

    # 移除前后空格和点
    sanitized = sanitized.strip(' .')

    # 限制长度
    if len(sanitized) > 255:
        sanitized = sanitized[:255]

    # 确保不为空
    if not sanitized:
        sanitized = 'unnamed'

    return sanitized

def format_bytes(bytes_value: int) -> str:
    """格式化字节数为人类可读格式"""
    if bytes_value == 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    size = float(bytes_value)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"

def format_duration(seconds: float) -> str:
    """格式化时间间隔为人类可读格式"""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def parse_duration(duration_str: str) -> Optional[float]:
    """解析时间间隔字符串为秒数"""
    pattern = r'^(\d+(?:\.\d+)?)(ms|s|m|h|d)$'
    match = re.match(pattern, duration_str.lower())

    if not match:
        return None

    value, unit = match.groups()
    value = float(value)

    multipliers = {
        'ms': 0.001,
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }

    return value * multipliers.get(unit, 1)

def get_file_size(file_path: Union[str, Path]) -> int:
    """获取文件大小"""
    try:
        return Path(file_path).stat().st_size
    except (OSError, FileNotFoundError):
        return 0

def ensure_directory(dir_path: Union[str, Path]) -> Path:
    """确保目录存在"""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def is_port_available(port: int, host: str = 'localhost') -> bool:
    """检查端口是否可用"""
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0
    except Exception:
        return False

def find_available_port(start_port: int = 8000, end_port: int = 9000) -> Optional[int]:
    """查找可用端口"""
    for port in range(start_port, end_port + 1):
        if is_port_available(port):
            return port
    return None

def kill_process_by_port(port: int) -> bool:
    """根据端口杀死进程"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                connections = proc.info['connections']
                if connections:
                    for conn in connections:
                        if conn.laddr.port == port:
                            proc.kill()
                            logger.info(f"已杀死占用端口 {port} 的进程: {proc.info['name']} (PID: {proc.info['pid']})")
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except Exception as e:
        logger.error(f"杀死进程失败: {e}")
        return False

def run_command(command: List[str], timeout: int = 30, cwd: Optional[str] = None) -> Dict[str, Any]:
    """执行命令"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )

        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': f'命令执行超时 ({timeout}s)'
        }
    except Exception as e:
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': str(e)
        }

def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    try:
        import platform

        return {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'hostname': platform.node(),
        }
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return {}

def get_memory_usage() -> Dict[str, Any]:
    """获取内存使用情况"""
    try:
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent,
            'free': memory.free
        }
    except Exception as e:
        logger.error(f"获取内存使用情况失败: {e}")
        return {}

def get_cpu_usage() -> Dict[str, Any]:
    """获取CPU使用情况"""
    try:
        return {
            'percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'count_logical': psutil.cpu_count(logical=True),
            'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
    except Exception as e:
        logger.error(f"获取CPU使用情况失败: {e}")
        return {}

def get_disk_usage(path: str = '/') -> Dict[str, Any]:
    """获取磁盘使用情况"""
    try:
        disk = psutil.disk_usage(path)
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': (disk.used / disk.total) * 100
        }
    except Exception as e:
        logger.error(f"获取磁盘使用情况失败: {e}")
        return {}

def truncate_string(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """截断字符串"""
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix

def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """遮蔽敏感数据"""
    if len(data) <= visible_chars * 2:
        return mask_char * len(data)

    start = data[:visible_chars]
    end = data[-visible_chars:]
    middle = mask_char * (len(data) - visible_chars * 2)

    return start + middle + end

def deep_merge_dict(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并字典"""
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value

    return result

def flatten_dict(data: Dict[str, Any], separator: str = '.', prefix: str = '') -> Dict[str, Any]:
    """扁平化字典"""
    result = {}

    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key

        if isinstance(value, dict):
            result.update(flatten_dict(value, separator, new_key))
        else:
            result[new_key] = value

    return result

def retry_on_exception(
    func,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """重试装饰器"""
    def decorator(*args, **kwargs):
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(f"函数 {func.__name__} 执行失败，{wait_time:.2f}s 后重试 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                    import time
                    time.sleep(wait_time)
                else:
                    logger.error(f"函数 {func.__name__} 重试 {max_retries} 次后仍然失败: {e}")

        raise last_exception

    return decorator

def batch_process(items: List[Any], batch_size: int = 100, processor=None):
    """批量处理数据"""
    if not processor:
        processor = lambda x: x

    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = [processor(item) for item in batch]
        results.extend(batch_results)

    return results

def debounce(wait_time: float):
    """防抖装饰器"""
    def decorator(func):
        last_called = [0]

        def wrapper(*args, **kwargs):
            import time
            now = time.time()

            if now - last_called[0] >= wait_time:
                last_called[0] = now
                return func(*args, **kwargs)

        return wrapper
    return decorator

def throttle(rate_limit: float):
    """节流装饰器"""
    def decorator(func):
        last_called = [0]

        def wrapper(*args, **kwargs):
            import time
            now = time.time()

            if now - last_called[0] >= 1.0 / rate_limit:
                last_called[0] = now
                return func(*args, **kwargs)
            else:
                raise Exception(f"调用频率超过限制: {rate_limit} 次/秒")

        return wrapper
    return decorator
