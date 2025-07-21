import os
import shutil
import tempfile
import gc
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging
import psutil
from pathlib import Path
from app.core.unified_logging import get_logger

logger = get_logger(__name__)

class CacheService:
    """缓存服务类"""

    def __init__(self, cache_dirs: List[str] = None):
        # 默认缓存目录
        self.cache_dirs = cache_dirs or [
            tempfile.gettempdir(),
            os.path.join(os.path.expanduser("~"), ".cache"),
            "./cache",
            "./logs",
            "./temp"
        ]

        # 可清理的文件扩展名
        self.cleanable_extensions = {
            '.tmp', '.temp', '.cache', '.log', '.bak', '.old',
            '.pyc', '.pyo', '__pycache__'
        }

    def clear_cache(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """清理缓存"""
        try:
            result = {
                "success": True,
                "message": "缓存清理完成",
                "details": {
                    "files_deleted": 0,
                    "dirs_deleted": 0,
                    "space_freed_bytes": 0,
                    "space_freed_mb": 0,
                    "errors": []
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            total_freed = 0

            # 清理Python内存缓存
            gc.collect()

            # 清理各个缓存目录
            for cache_dir in self.cache_dirs:
                if os.path.exists(cache_dir):
                    freed_bytes = self._clean_directory(cache_dir, cutoff_time, result["details"])
                    total_freed += freed_bytes

            # 清理临时文件
            temp_freed = self._clean_temp_files(cutoff_time, result["details"])
            total_freed += temp_freed

            # 清理Python缓存文件
            pyc_freed = self._clean_python_cache(result["details"])
            total_freed += pyc_freed

            result["details"]["space_freed_bytes"] = total_freed
            result["details"]["space_freed_mb"] = round(total_freed / (1024 * 1024), 2)

            if result["details"]["errors"]:
                result["message"] += f" (有 {len(result['details']['errors'])} 个错误)"

            logger.info(f"缓存清理完成: 删除 {result['details']['files_deleted']} 个文件, "
                       f"释放 {result['details']['space_freed_mb']} MB 空间")

            return result

        except Exception as e:
            error_msg = f"缓存清理失败: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }

    def _clean_directory(self, directory: str, cutoff_time: datetime, details: Dict[str, Any]) -> int:
        """清理指定目录"""
        freed_bytes = 0

        try:
            for root, dirs, files in os.walk(directory):
                # 清理文件
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if self._should_delete_file(file_path, cutoff_time):
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            details["files_deleted"] += 1
                            freed_bytes += file_size
                    except Exception as e:
                        details["errors"].append(f"删除文件失败 {file_path}: {str(e)}")

                # 清理空目录
                for dir_name in dirs[:]:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if self._is_empty_directory(dir_path):
                            os.rmdir(dir_path)
                            details["dirs_deleted"] += 1
                            dirs.remove(dir_name)
                    except Exception as e:
                        details["errors"].append(f"删除目录失败 {dir_path}: {str(e)}")

        except Exception as e:
            details["errors"].append(f"清理目录失败 {directory}: {str(e)}")

        return freed_bytes

    def _clean_temp_files(self, cutoff_time: datetime, details: Dict[str, Any]) -> int:
        """清理临时文件"""
        freed_bytes = 0
        temp_dir = tempfile.gettempdir()

        try:
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                try:
                    if os.path.isfile(item_path):
                        if self._should_delete_file(item_path, cutoff_time):
                            file_size = os.path.getsize(item_path)
                            os.remove(item_path)
                            details["files_deleted"] += 1
                            freed_bytes += file_size
                    elif os.path.isdir(item_path):
                        # 清理临时目录中的旧文件夹
                        if self._should_delete_directory(item_path, cutoff_time):
                            dir_size = self._get_directory_size(item_path)
                            shutil.rmtree(item_path)
                            details["dirs_deleted"] += 1
                            freed_bytes += dir_size
                except Exception as e:
                    details["errors"].append(f"清理临时项失败 {item_path}: {str(e)}")

        except Exception as e:
            details["errors"].append(f"清理临时目录失败: {str(e)}")

        return freed_bytes

    def _clean_python_cache(self, details: Dict[str, Any]) -> int:
        """清理Python缓存文件"""
        freed_bytes = 0

        try:
            # 查找并删除 __pycache__ 目录
            for root, dirs, files in os.walk("."):
                if "__pycache__" in dirs:
                    pycache_path = os.path.join(root, "__pycache__")
                    try:
                        dir_size = self._get_directory_size(pycache_path)
                        shutil.rmtree(pycache_path)
                        details["dirs_deleted"] += 1
                        freed_bytes += dir_size
                        dirs.remove("__pycache__")
                    except Exception as e:
                        details["errors"].append(f"删除Python缓存目录失败 {pycache_path}: {str(e)}")

                # 删除 .pyc 和 .pyo 文件
                for file in files:
                    if file.endswith(('.pyc', '.pyo')):
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            details["files_deleted"] += 1
                            freed_bytes += file_size
                        except Exception as e:
                            details["errors"].append(f"删除Python缓存文件失败 {file_path}: {str(e)}")

        except Exception as e:
            details["errors"].append(f"清理Python缓存失败: {str(e)}")

        return freed_bytes

    def _should_delete_file(self, file_path: str, cutoff_time: datetime) -> bool:
        """判断文件是否应该被删除"""
        try:
            # 检查文件扩展名
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.cleanable_extensions:
                return False

            # 检查文件修改时间
            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            return mtime < cutoff_time

        except Exception:
            return False

    def _should_delete_directory(self, dir_path: str, cutoff_time: datetime) -> bool:
        """判断目录是否应该被删除"""
        try:
            # 只删除空目录或临时目录
            if not self._is_empty_directory(dir_path):
                return False

            # 检查目录修改时间
            mtime = datetime.fromtimestamp(os.path.getmtime(dir_path))
            return mtime < cutoff_time

        except Exception:
            return False

    def _is_empty_directory(self, dir_path: str) -> bool:
        """检查目录是否为空"""
        try:
            return len(os.listdir(dir_path)) == 0
        except Exception:
            return False

    def _get_directory_size(self, dir_path: str) -> int:
        """获取目录大小"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except Exception:
                        pass
        except Exception:
            pass
        return total_size

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        try:
            cache_info = {
                "directories": [],
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "total_files": 0,
                "cleanable_files": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

            for cache_dir in self.cache_dirs:
                if os.path.exists(cache_dir):
                    dir_info = self._get_directory_info(cache_dir)
                    cache_info["directories"].append(dir_info)
                    cache_info["total_size_bytes"] += dir_info["size_bytes"]
                    cache_info["total_files"] += dir_info["file_count"]
                    cache_info["cleanable_files"] += dir_info["cleanable_files"]

            cache_info["total_size_mb"] = round(cache_info["total_size_bytes"] / (1024 * 1024), 2)

            return cache_info

        except Exception as e:
            logger.error(f"获取缓存信息失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _get_directory_info(self, directory: str) -> Dict[str, Any]:
        """获取目录信息"""
        info = {
            "path": directory,
            "exists": False,
            "size_bytes": 0,
            "size_mb": 0,
            "file_count": 0,
            "cleanable_files": 0
        }

        try:
            if os.path.exists(directory):
                info["exists"] = True

                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            info["size_bytes"] += file_size
                            info["file_count"] += 1

                            # 检查是否可清理
                            file_ext = Path(file_path).suffix.lower()
                            if file_ext in self.cleanable_extensions:
                                info["cleanable_files"] += 1

                        except Exception:
                            pass

                info["size_mb"] = round(info["size_bytes"] / (1024 * 1024), 2)

        except Exception as e:
            info["error"] = str(e)

        return info
