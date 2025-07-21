"""验证工具模块"""

import re
from typing import Optional
from urllib.parse import urlparse

def validate_email(email: str) -> bool:
    """验证邮箱地址格式"""
    if not email or not email.strip():
        return False

    email = email.strip()

    # 基本格式检查
    if '@' not in email:
        return False

    # 分割用户名和域名
    parts = email.split('@')
    if len(parts) != 2:
        return False

    username, domain = parts

    # 检查用户名
    if not username or len(username) > 64:
        return False

    # 检查域名
    if not domain or '.' not in domain:
        return False

    # 使用正则表达式进行更严格的验证
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_url(url: str) -> bool:
    """验证URL格式"""
    if not url or not url.strip():
        return False

    url = url.strip()

    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except Exception:
        return False

def validate_webhook_url(url: str) -> tuple[bool, Optional[str]]:
    """验证Webhook URL并返回错误信息"""
    if not url or not url.strip():
        return False, "Webhook URL不能为空"

    url = url.strip()

    if not validate_url(url):
        return False, "Webhook URL格式不正确，必须是有效的HTTP或HTTPS地址"

    # 检查是否为本地地址（可选的安全检查）
    parsed = urlparse(url)
    if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
        return False, "不允许使用本地地址作为Webhook URL"

    return True, None

def validate_email_address(email: str) -> tuple[bool, Optional[str]]:
    """验证邮箱地址并返回错误信息"""
    if not email or not email.strip():
        return False, "邮箱地址不能为空"

    email = email.strip()

    if not validate_email(email):
        return False, "邮箱地址格式不正确"

    return True, None

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """清理输入文本"""
    if not text:
        return ""

    # 移除前后空白
    text = text.strip()

    # 限制长度
    if len(text) > max_length:
        text = text[:max_length]

    return text
