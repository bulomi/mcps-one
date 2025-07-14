"""分页工具模块"""

from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Generic
from sqlalchemy.orm import Query, Session
from sqlalchemy import func, text
from pydantic import BaseModel, Field
from math import ceil

T = TypeVar('T')

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码，从1开始")
    size: int = Field(20, ge=1, le=100, description="每页大小，最大100")
    
class PaginationMeta(BaseModel):
    """分页元数据"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")
    next_page: Optional[int] = Field(None, description="下一页页码")
    prev_page: Optional[int] = Field(None, description="上一页页码")
    
class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T] = Field(..., description="数据列表")
    meta: PaginationMeta = Field(..., description="分页元数据")
    
def paginate(
    query: Query,
    page: int = 1,
    size: int = 20,
    max_size: int = 100
) -> Tuple[List[Any], PaginationMeta]:
    """分页查询
    
    Args:
        query: SQLAlchemy查询对象
        page: 页码，从1开始
        size: 每页大小
        max_size: 最大每页大小
        
    Returns:
        Tuple[List[Any], PaginationMeta]: 数据列表和分页元数据
    """
    # 参数验证
    page = max(1, page)
    size = min(max(1, size), max_size)
    
    # 获取总记录数
    total = query.count()
    
    # 计算总页数
    total_pages = ceil(total / size) if total > 0 else 1
    
    # 确保页码不超过总页数
    page = min(page, total_pages)
    
    # 计算偏移量
    offset = (page - 1) * size
    
    # 获取数据
    items = query.offset(offset).limit(size).all()
    
    # 构建分页元数据
    meta = PaginationMeta(
        total=total,
        page=page,
        size=size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
        next_page=page + 1 if page < total_pages else None,
        prev_page=page - 1 if page > 1 else None
    )
    
    return items, meta

def paginate_list(
    items: List[Any],
    page: int = 1,
    size: int = 20,
    max_size: int = 100
) -> Tuple[List[Any], PaginationMeta]:
    """对列表进行分页
    
    Args:
        items: 数据列表
        page: 页码，从1开始
        size: 每页大小
        max_size: 最大每页大小
        
    Returns:
        Tuple[List[Any], PaginationMeta]: 分页后的数据列表和分页元数据
    """
    # 参数验证
    page = max(1, page)
    size = min(max(1, size), max_size)
    
    # 获取总记录数
    total = len(items)
    
    # 计算总页数
    total_pages = ceil(total / size) if total > 0 else 1
    
    # 确保页码不超过总页数
    page = min(page, total_pages)
    
    # 计算偏移量
    start = (page - 1) * size
    end = start + size
    
    # 获取分页数据
    paginated_items = items[start:end]
    
    # 构建分页元数据
    meta = PaginationMeta(
        total=total,
        page=page,
        size=size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
        next_page=page + 1 if page < total_pages else None,
        prev_page=page - 1 if page > 1 else None
    )
    
    return paginated_items, meta

def paginate_with_cursor(
    query: Query,
    cursor_field: str,
    cursor_value: Optional[Any] = None,
    size: int = 20,
    direction: str = 'next',
    max_size: int = 100
) -> Tuple[List[Any], Dict[str, Any]]:
    """基于游标的分页
    
    Args:
        query: SQLAlchemy查询对象
        cursor_field: 游标字段名
        cursor_value: 游标值
        size: 每页大小
        direction: 分页方向，'next' 或 'prev'
        max_size: 最大每页大小
        
    Returns:
        Tuple[List[Any], Dict[str, Any]]: 数据列表和游标信息
    """
    # 参数验证
    size = min(max(1, size), max_size)
    
    # 构建查询条件
    if cursor_value is not None:
        cursor_column = getattr(query.column_descriptions[0]['type'], cursor_field)
        if direction == 'next':
            query = query.filter(cursor_column > cursor_value)
        else:
            query = query.filter(cursor_column < cursor_value)
    
    # 排序
    cursor_column = getattr(query.column_descriptions[0]['type'], cursor_field)
    if direction == 'next':
        query = query.order_by(cursor_column.asc())
    else:
        query = query.order_by(cursor_column.desc())
    
    # 获取数据（多取一条用于判断是否还有更多数据）
    items = query.limit(size + 1).all()
    
    # 判断是否还有更多数据
    has_more = len(items) > size
    if has_more:
        items = items[:size]
    
    # 构建游标信息
    cursor_info = {
        'has_more': has_more,
        'size': len(items),
        'direction': direction
    }
    
    if items:
        if direction == 'next':
            cursor_info['next_cursor'] = getattr(items[-1], cursor_field)
            cursor_info['prev_cursor'] = getattr(items[0], cursor_field)
        else:
            cursor_info['next_cursor'] = getattr(items[0], cursor_field)
            cursor_info['prev_cursor'] = getattr(items[-1], cursor_field)
    
    return items, cursor_info

class PaginationHelper:
    """分页助手类"""
    
    @staticmethod
    def get_pagination_params(
        page: Optional[int] = None,
        size: Optional[int] = None,
        default_size: int = 20,
        max_size: int = 100
    ) -> PaginationParams:
        """获取分页参数"""
        page = page or 1
        size = size or default_size
        
        return PaginationParams(
            page=max(1, page),
            size=min(max(1, size), max_size)
        )
    
    @staticmethod
    def build_pagination_links(
        base_url: str,
        meta: PaginationMeta,
        query_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Optional[str]]:
        """构建分页链接"""
        query_params = query_params or {}
        
        def build_url(page: int) -> str:
            params = query_params.copy()
            params.update({
                'page': page,
                'size': meta.size
            })
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            return f"{base_url}?{query_string}"
        
        links = {
            'self': build_url(meta.page),
            'first': build_url(1),
            'last': build_url(meta.total_pages),
            'next': build_url(meta.next_page) if meta.has_next else None,
            'prev': build_url(meta.prev_page) if meta.has_prev else None
        }
        
        return links
    
    @staticmethod
    def calculate_page_range(
        current_page: int,
        total_pages: int,
        window_size: int = 5
    ) -> Tuple[int, int]:
        """计算页码范围"""
        half_window = window_size // 2
        
        start = max(1, current_page - half_window)
        end = min(total_pages, current_page + half_window)
        
        # 调整范围以保持窗口大小
        if end - start + 1 < window_size:
            if start == 1:
                end = min(total_pages, start + window_size - 1)
            elif end == total_pages:
                start = max(1, end - window_size + 1)
        
        return start, end
    
    @staticmethod
    def get_page_numbers(
        current_page: int,
        total_pages: int,
        window_size: int = 5
    ) -> List[int]:
        """获取页码列表"""
        start, end = PaginationHelper.calculate_page_range(
            current_page, total_pages, window_size
        )
        return list(range(start, end + 1))

def create_paginated_response(
    items: List[Any],
    meta: PaginationMeta,
    message: str = "获取成功"
) -> Dict[str, Any]:
    """创建分页响应"""
    return {
        "success": True,
        "message": message,
        "data": items,
        "meta": meta.dict()
    }

def simple_paginate(
    total: int,
    page: int = 1,
    size: int = 20
) -> Dict[str, Any]:
    """简单分页计算函数
    
    Args:
        total: 总记录数
        page: 页码，从1开始
        size: 每页大小
        
    Returns:
        Dict[str, Any]: 分页信息
    """
    # 参数验证
    page = max(1, page)
    size = max(1, size)
    total = max(0, total)
    
    # 计算总页数
    total_pages = (total + size - 1) // size if total > 0 else 1
    
    # 确保页码不超过总页数
    page = min(page, total_pages)
    
    return {
        "total": total,
        "page": page,
        "size": size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

def extract_pagination_params(
    request_params: Dict[str, Any],
    default_size: int = 20,
    max_size: int = 100
) -> PaginationParams:
    """从请求参数中提取分页参数"""
    page = request_params.get('page', 1)
    size = request_params.get('size', default_size)
    
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    
    try:
        size = int(size)
    except (ValueError, TypeError):
        size = default_size
    
    return PaginationParams(
        page=max(1, page),
        size=min(max(1, size), max_size)
    )

class AsyncPaginator:
    """异步分页器"""
    
    def __init__(self, session: Session):
        self.session = session
    
    async def paginate(
        self,
        query: Query,
        page: int = 1,
        size: int = 20,
        max_size: int = 100
    ) -> Tuple[List[Any], PaginationMeta]:
        """异步分页查询"""
        # 这里可以添加异步数据库查询逻辑
        # 目前使用同步方法
        return paginate(query, page, size, max_size)

# 分页装饰器
def paginated(default_size: int = 20, max_size: int = 100):
    """分页装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 提取分页参数
            page = kwargs.pop('page', 1)
            size = kwargs.pop('size', default_size)
            
            # 验证参数
            page = max(1, page)
            size = min(max(1, size), max_size)
            
            # 调用原函数
            result = func(*args, page=page, size=size, **kwargs)
            
            return result
        return wrapper
    return decorator