"""系统配置相关数据模型"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.database import Base

class SystemConfig(Base):
    """系统配置模型"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False, comment="配置键")
    value = Column(Text, comment="配置值")
    value_type = Column(String(20), default="string", comment="值类型: string, int, float, bool, json")
    category = Column(String(50), index=True, comment="配置分类")
    description = Column(Text, comment="配置描述")
    is_public = Column(Boolean, default=False, comment="是否为公开配置")
    is_readonly = Column(Boolean, default=False, comment="是否只读")

    # 系统字段
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', value='{self.value}')>"

    def get_typed_value(self) -> Any:
        """获取类型化的值"""
        if self.value is None:
            return None

        try:
            if self.value_type == "int":
                return int(self.value)
            elif self.value_type == "float":
                return float(self.value)
            elif self.value_type == "bool":
                return self.value.lower() in ("true", "1", "yes", "on")
            elif self.value_type == "json":
                import json
                return json.loads(self.value)
            else:
                return self.value
        except (ValueError, TypeError):
            return self.value

    def set_typed_value(self, value: Any) -> None:
        """设置类型化的值"""
        if value is None:
            self.value = None
            return

        if self.value_type == "json":
            import json
            self.value = json.dumps(value, ensure_ascii=False)
        else:
            self.value = str(value)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "key": self.key,
            "value": self.get_typed_value(),
            "value_type": self.value_type,
            "category": self.category,
            "description": self.description,
            "is_public": self.is_public,
            "is_readonly": self.is_readonly,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class SystemInfo(Base):
    """系统信息模型"""
    __tablename__ = "system_info"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), index=True, nullable=False, comment="指标名称")
    metric_value = Column(Text, comment="指标值")
    metric_type = Column(String(20), default="gauge", comment="指标类型: gauge, counter, histogram")
    unit = Column(String(20), comment="单位")
    category = Column(String(50), index=True, comment="分类")
    tags = Column(JSON, default=dict, comment="标签")

    # 时间字段
    timestamp = Column(DateTime, default=func.now(), index=True, comment="时间戳")

    def __repr__(self):
        return f"<SystemInfo(metric='{self.metric_name}', value='{self.metric_value}')>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "metric_type": self.metric_type,
            "unit": self.unit,
            "category": self.category,
            "tags": self.tags or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
