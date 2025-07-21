import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.core import get_logger

logger = get_logger(__name__)

class EmailService:
    """邮件服务类"""

    def __init__(self, smtp_server: str = None, smtp_port: int = 587,
                 username: str = None, password: str = None, use_tls: bool = True):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def configure(self, config: Dict[str, Any]) -> None:
        """配置邮件服务"""
        self.smtp_server = config.get('smtp_server')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.use_tls = config.get('use_tls', True)

    def send_email(self, to_email: str, subject: str, body: str,
                   html_body: Optional[str] = None, from_email: Optional[str] = None) -> Dict[str, Any]:
        """发送邮件"""
        try:
            # 验证配置
            if not all([self.smtp_server, self.username, self.password]):
                return {
                    "success": False,
                    "message": "邮件服务配置不完整，请检查SMTP服务器、用户名和密码设置",
                    "timestamp": datetime.utcnow().isoformat()
                }

            # 创建邮件消息
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = from_email or self.username
            message["To"] = to_email

            # 添加文本内容
            text_part = MIMEText(body, "plain", "utf-8")
            message.attach(text_part)

            # 添加HTML内容（如果提供）
            if html_body:
                html_part = MIMEText(html_body, "html", "utf-8")
                message.attach(html_part)

            # 创建SMTP连接
            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)

                server.login(self.username, self.password)
                server.sendmail(from_email or self.username, to_email, message.as_string())

            logger.info(f"邮件发送成功: {to_email}")
            return {
                "success": True,
                "message": f"邮件已成功发送到 {to_email}",
                "timestamp": datetime.utcnow().isoformat()
            }

        except smtplib.SMTPAuthenticationError:
            error_msg = "SMTP认证失败，请检查用户名和密码"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
        except smtplib.SMTPConnectError:
            error_msg = "无法连接到SMTP服务器，请检查服务器地址和端口"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
        except smtplib.SMTPRecipientsRefused:
            error_msg = f"收件人地址被拒绝: {to_email}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            error_msg = f"邮件发送失败: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }

    def send_test_email(self, to_email: str) -> Dict[str, Any]:
        """发送测试邮件"""
        subject = "MCPS.ONE 系统测试邮件"
        body = f"""这是一封来自 MCPS.ONE 系统的测试邮件。

如果您收到这封邮件，说明邮件通知功能配置正确。

发送时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

此邮件由系统自动发送，请勿回复。"""

        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MCPS.ONE 系统测试邮件</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">MCPS.ONE 系统测试邮件</h2>
        <p>这是一封来自 <strong>MCPS.ONE</strong> 系统的测试邮件。</p>
        <p>如果您收到这封邮件，说明邮件通知功能配置正确。</p>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p><strong>发送时间:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
        <p style="color: #666; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
    </div>
</body>
</html>"""

        return self.send_email(to_email, subject, body, html_body)

    def test_connection(self) -> Dict[str, Any]:
        """测试邮件服务器连接"""
        try:
            if not all([self.smtp_server, self.username, self.password]):
                return {
                    "success": False,
                    "message": "邮件服务配置不完整",
                    "timestamp": datetime.utcnow().isoformat()
                }

            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.username, self.password)

            return {
                "success": True,
                "message": "邮件服务器连接测试成功",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"邮件服务器连接测试失败: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
