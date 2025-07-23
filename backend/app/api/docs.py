"""文档管理 API 路由

提供文档读取和管理功能，支持：
- 获取文档列表
- 读取文档内容
- 文档搜索
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.utils.response import success_response, error_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/docs", tags=["文档管理"])

# 文档根目录
DOCS_ROOT = Path("../docs").resolve()

# 响应模型
class DocInfo(BaseModel):
    """文档信息"""
    name: str
    title: str
    path: str
    size: int
    modified_time: str
    is_directory: bool = False

class DocContent(BaseModel):
    """文档内容"""
    name: str
    title: str
    path: str
    content: str
    content_type: str = "markdown"


def get_doc_title(content: str) -> str:
    """从markdown内容中提取标题"""
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
    return "无标题"


def is_markdown_file(file_path: Path) -> bool:
    """检查是否为markdown文件"""
    return file_path.suffix.lower() in ['.md', '.markdown']


@router.get("/", response_model=dict, summary="获取文档列表")
async def get_docs_list(
    path: Optional[str] = Query(None, description="子目录路径"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """获取文档列表"""
    try:
        # 构建目标路径
        if path:
            target_path = DOCS_ROOT / path
        else:
            target_path = DOCS_ROOT
        
        # 检查路径是否存在
        if not target_path.exists():
            return error_response(message="路径不存在", status_code=404)
        
        if not target_path.is_dir():
            return error_response(message="路径不是目录", status_code=400)
        
        docs = []
        
        # 遍历目录
        for item in target_path.iterdir():
            # 跳过隐藏文件
            if item.name.startswith('.'):
                continue
            
            # 如果是目录
            if item.is_dir():
                docs.append(DocInfo(
                    name=item.name,
                    title=item.name,
                    path=str(item.relative_to(DOCS_ROOT)),
                    size=0,
                    modified_time=str(item.stat().st_mtime),
                    is_directory=True
                ).dict())
            # 如果是markdown文件
            elif is_markdown_file(item):
                try:
                    # 读取文件内容获取标题
                    content = item.read_text(encoding='utf-8')
                    title = get_doc_title(content)
                    
                    # 搜索过滤
                    if search:
                        search_lower = search.lower()
                        if (search_lower not in title.lower() and 
                            search_lower not in content.lower() and
                            search_lower not in item.name.lower()):
                            continue
                    
                    docs.append(DocInfo(
                        name=item.name,
                        title=title,
                        path=str(item.relative_to(DOCS_ROOT)),
                        size=item.stat().st_size,
                        modified_time=str(item.stat().st_mtime),
                        is_directory=False
                    ).dict())
                except Exception as e:
                    logger.warning(f"读取文档 {item} 失败: {e}")
                    continue
        
        # 排序：目录在前，文件在后，按名称排序
        docs.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))
        
        return success_response(
            data={
                "items": docs,
                "total": len(docs),
                "current_path": str(target_path.relative_to(DOCS_ROOT)) if path else ""
            },
            message="获取文档列表成功"
        )
    
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        return error_response(message="获取文档列表失败", error_code=str(e))


@router.get("/content", response_model=dict, summary="获取文档内容")
async def get_doc_content(
    path: str = Query(..., description="文档路径")
):
    """获取文档内容"""
    try:
        # 构建文件路径
        file_path = DOCS_ROOT / path
        
        # 检查文件是否存在
        if not file_path.exists():
            return error_response(message="文档不存在", status_code=404)
        
        if not file_path.is_file():
            return error_response(message="路径不是文件", status_code=400)
        
        if not is_markdown_file(file_path):
            return error_response(message="不支持的文件类型", status_code=400)
        
        # 读取文件内容
        try:
            content = file_path.read_text(encoding='utf-8')
            title = get_doc_title(content)
            
            doc_content = DocContent(
                name=file_path.name,
                title=title,
                path=path,
                content=content,
                content_type="markdown"
            )
            
            return success_response(
                data=doc_content.dict(),
                message="获取文档内容成功"
            )
        
        except UnicodeDecodeError:
            return error_response(message="文档编码错误", status_code=400)
    
    except Exception as e:
        logger.error(f"获取文档内容失败: {e}")
        return error_response(message="获取文档内容失败", error_code=str(e))


@router.get("/search", response_model=dict, summary="搜索文档")
async def search_docs(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="结果数量限制")
):
    """搜索文档"""
    try:
        if not DOCS_ROOT.exists():
            return success_response(
                data={"items": [], "total": 0},
                message="文档目录不存在"
            )
        
        results = []
        query_lower = query.lower()
        
        # 递归搜索所有markdown文件
        def search_in_directory(directory: Path, relative_base: Path = DOCS_ROOT):
            for item in directory.iterdir():
                if item.name.startswith('.'):
                    continue
                
                if item.is_dir():
                    search_in_directory(item, relative_base)
                elif is_markdown_file(item):
                    try:
                        content = item.read_text(encoding='utf-8')
                        title = get_doc_title(content)
                        
                        # 检查是否匹配搜索条件
                        if (query_lower in title.lower() or 
                            query_lower in content.lower() or
                            query_lower in item.name.lower()):
                            
                            # 查找匹配的上下文
                            lines = content.split('\n')
                            context_lines = []
                            for i, line in enumerate(lines):
                                if query_lower in line.lower():
                                    # 获取前后各2行作为上下文
                                    start = max(0, i - 2)
                                    end = min(len(lines), i + 3)
                                    context = '\n'.join(lines[start:end])
                                    context_lines.append(context)
                                    if len(context_lines) >= 3:  # 最多3个匹配片段
                                        break
                            
                            results.append({
                                "name": item.name,
                                "title": title,
                                "path": str(item.relative_to(relative_base)),
                                "context": context_lines[:3],  # 最多返回3个上下文片段
                                "size": item.stat().st_size,
                                "modified_time": str(item.stat().st_mtime)
                            })
                    
                    except Exception as e:
                        logger.warning(f"搜索文档 {item} 时出错: {e}")
                        continue
        
        search_in_directory(DOCS_ROOT)
        
        # 按相关性排序（标题匹配优先）
        def relevance_score(result):
            score = 0
            if query_lower in result["title"].lower():
                score += 10
            if query_lower in result["name"].lower():
                score += 5
            score += len(result["context"])  # 匹配片段越多，相关性越高
            return score
        
        results.sort(key=relevance_score, reverse=True)
        
        # 限制结果数量
        results = results[:limit]
        
        return success_response(
            data={
                "items": results,
                "total": len(results),
                "query": query
            },
            message=f"搜索完成，找到 {len(results)} 个结果"
        )
    
    except Exception as e:
        logger.error(f"搜索文档失败: {e}")
        return error_response(message="搜索文档失败", error_code=str(e))