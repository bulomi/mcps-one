"""数据库备份服务"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import shutil
import gzip
import json
import logging
from pathlib import Path

from app.models.system import DatabaseBackup
from app.schemas.system import (
    DatabaseBackupCreate,
    BackupType,
    BackupStatus
)
from app.core.config import settings
from app.utils.exceptions import DatabaseError
from app.utils.helpers import format_bytes, ensure_directory

logger = logging.getLogger(__name__)

class BackupService:
    """数据库备份服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.backup_dir = Path(settings.BACKUP_DIR)
        ensure_directory(self.backup_dir)
    
    def get_backups(
        self,
        page: int = 1,
        size: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[DatabaseBackup], int]:
        """获取备份列表"""
        query = self.db.query(DatabaseBackup)
        
        # 应用过滤条件
        if filters:
            if filters.get('backup_type'):
                query = query.filter(DatabaseBackup.backup_type == filters['backup_type'])
            
            if filters.get('status'):
                query = query.filter(DatabaseBackup.status == filters['status'])
            
            if filters.get('start_time'):
                query = query.filter(DatabaseBackup.created_at >= filters['start_time'])
            
            if filters.get('end_time'):
                query = query.filter(DatabaseBackup.created_at <= filters['end_time'])
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        backups = query.order_by(desc(DatabaseBackup.created_at)).offset(
            (page - 1) * size
        ).limit(size).all()
        
        return backups, total
    
    def get_backup(self, backup_id: int) -> Optional[DatabaseBackup]:
        """获取备份详情"""
        return self.db.query(DatabaseBackup).filter(DatabaseBackup.id == backup_id).first()
    
    def create_backup(
        self,
        backup_data: DatabaseBackupCreate,
        user_id: Optional[int] = None
    ) -> DatabaseBackup:
        """创建数据库备份"""
        try:
            # 生成备份文件名
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"mcps_backup_{timestamp}.db"
            
            if backup_data.compress:
                backup_filename += ".gz"
            
            backup_path = self.backup_dir / backup_filename
            
            # 创建备份记录
            backup = DatabaseBackup(
                name=backup_data.name or f"自动备份_{timestamp}",
                description=backup_data.description,
                backup_type=backup_data.backup_type,
                file_path=str(backup_path),
                compress=backup_data.compress,
                status=BackupStatus.RUNNING,
                created_by=user_id,
                created_at=datetime.utcnow()
            )
            
            self.db.add(backup)
            self.db.commit()
            self.db.refresh(backup)
            
            # 执行备份
            try:
                self._perform_backup(backup)
                
                # 更新备份状态
                backup.status = BackupStatus.COMPLETED
                backup.completed_at = datetime.utcnow()
                backup.file_size = backup_path.stat().st_size if backup_path.exists() else 0
                
                self.db.commit()
                
                logger.info(f"数据库备份创建成功: {backup.name} -> {backup_path}")
                
            except Exception as e:
                backup.status = BackupStatus.FAILED
                backup.error_message = str(e)
                backup.completed_at = datetime.utcnow()
                
                self.db.commit()
                
                logger.error(f"数据库备份失败: {e}")
                raise DatabaseError(f"数据库备份失败: {e}")
            
            return backup
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建数据库备份失败: {e}")
            raise
    
    def restore_backup(self, backup_id: int, user_id: Optional[int] = None) -> bool:
        """恢复数据库备份"""
        try:
            backup = self.get_backup(backup_id)
            if not backup:
                raise DatabaseError(f"备份不存在: {backup_id}")
            
            if backup.status != BackupStatus.COMPLETED:
                raise DatabaseError("只能恢复已完成的备份")
            
            backup_path = Path(backup.file_path)
            if not backup_path.exists():
                raise DatabaseError(f"备份文件不存在: {backup_path}")
            
            # 创建当前数据库的备份
            current_backup_data = DatabaseBackupCreate(
                name=f"恢复前备份_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                description="恢复数据库前的自动备份",
                backup_type=BackupType.MANUAL,
                compress=True
            )
            
            self.create_backup(current_backup_data, user_id)
            
            # 执行恢复
            self._perform_restore(backup)
            
            logger.info(f"数据库恢复成功: {backup.name}")
            return True
            
        except Exception as e:
            logger.error(f"恢复数据库备份失败: {e}")
            raise
    
    def delete_backup(self, backup_id: int) -> bool:
        """删除备份"""
        try:
            backup = self.get_backup(backup_id)
            if not backup:
                raise DatabaseError(f"备份不存在: {backup_id}")
            
            # 删除备份文件
            backup_path = Path(backup.file_path)
            if backup_path.exists():
                backup_path.unlink()
            
            # 删除备份记录
            self.db.delete(backup)
            self.db.commit()
            
            logger.info(f"备份删除成功: {backup.name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除备份失败: {e}")
            raise
    
    def cleanup_old_backups(self, keep_days: int = 30) -> Dict[str, Any]:
        """清理旧备份"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=keep_days)
            
            # 查找需要清理的备份
            old_backups = self.db.query(DatabaseBackup).filter(
                and_(
                    DatabaseBackup.created_at < cutoff_date,
                    DatabaseBackup.backup_type == BackupType.AUTO
                )
            ).all()
            
            deleted_count = 0
            freed_space = 0
            errors = []
            
            for backup in old_backups:
                try:
                    backup_path = Path(backup.file_path)
                    if backup_path.exists():
                        freed_space += backup_path.stat().st_size
                        backup_path.unlink()
                    
                    self.db.delete(backup)
                    deleted_count += 1
                    
                except Exception as e:
                    errors.append(f"删除备份 {backup.name} 失败: {e}")
            
            self.db.commit()
            
            result = {
                "deleted_count": deleted_count,
                "freed_space": freed_space,
                "freed_space_formatted": format_bytes(freed_space),
                "errors": errors
            }
            
            logger.info(f"清理旧备份完成: {result}")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"清理旧备份失败: {e}")
            raise
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """获取备份统计"""
        try:
            # 总备份数
            total_backups = self.db.query(DatabaseBackup).count()
            
            # 按状态统计
            status_stats = self.db.query(
                DatabaseBackup.status,
                func.count(DatabaseBackup.id).label('count')
            ).group_by(DatabaseBackup.status).all()
            
            # 按类型统计
            type_stats = self.db.query(
                DatabaseBackup.backup_type,
                func.count(DatabaseBackup.id).label('count')
            ).group_by(DatabaseBackup.backup_type).all()
            
            # 总文件大小
            total_size = self.db.query(
                func.sum(DatabaseBackup.file_size)
            ).scalar() or 0
            
            # 最近备份
            latest_backup = self.db.query(DatabaseBackup).order_by(
                desc(DatabaseBackup.created_at)
            ).first()
            
            # 最近成功备份
            latest_successful = self.db.query(DatabaseBackup).filter(
                DatabaseBackup.status == BackupStatus.COMPLETED
            ).order_by(desc(DatabaseBackup.created_at)).first()
            
            return {
                "total_backups": total_backups,
                "total_size": total_size,
                "total_size_formatted": format_bytes(total_size),
                "by_status": {status.value: count for status, count in status_stats},
                "by_type": {backup_type.value: count for backup_type, count in type_stats},
                "latest_backup": {
                    "id": latest_backup.id,
                    "name": latest_backup.name,
                    "status": latest_backup.status.value,
                    "created_at": latest_backup.created_at.isoformat()
                } if latest_backup else None,
                "latest_successful": {
                    "id": latest_successful.id,
                    "name": latest_successful.name,
                    "created_at": latest_successful.created_at.isoformat()
                } if latest_successful else None
            }
            
        except Exception as e:
            logger.error(f"获取备份统计失败: {e}")
            raise
    
    def verify_backup(self, backup_id: int) -> Dict[str, Any]:
        """验证备份完整性"""
        try:
            backup = self.get_backup(backup_id)
            if not backup:
                raise DatabaseError(f"备份不存在: {backup_id}")
            
            backup_path = Path(backup.file_path)
            if not backup_path.exists():
                return {
                    "valid": False,
                    "error": "备份文件不存在"
                }
            
            # 检查文件大小
            actual_size = backup_path.stat().st_size
            if backup.file_size and actual_size != backup.file_size:
                return {
                    "valid": False,
                    "error": f"文件大小不匹配: 期望 {backup.file_size}, 实际 {actual_size}"
                }
            
            # 如果是压缩文件，尝试解压测试
            if backup.compress and backup_path.suffix == '.gz':
                try:
                    with gzip.open(backup_path, 'rb') as f:
                        # 读取前1KB测试
                        f.read(1024)
                except Exception as e:
                    return {
                        "valid": False,
                        "error": f"压缩文件损坏: {e}"
                    }
            
            # 尝试连接数据库文件（如果不是压缩文件）
            if not backup.compress:
                try:
                    import sqlite3
                    conn = sqlite3.connect(str(backup_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    conn.close()
                    
                    if not tables:
                        return {
                            "valid": False,
                            "error": "数据库文件为空或损坏"
                        }
                        
                except Exception as e:
                    return {
                        "valid": False,
                        "error": f"数据库文件损坏: {e}"
                    }
            
            return {
                "valid": True,
                "file_size": actual_size,
                "file_size_formatted": format_bytes(actual_size)
            }
            
        except Exception as e:
            logger.error(f"验证备份失败: {e}")
            raise
    
    # 私有方法
    def _perform_backup(self, backup: DatabaseBackup) -> None:
        """执行备份操作"""
        try:
            source_db = Path(settings.DATABASE_URL.replace('sqlite:///', ''))
            backup_path = Path(backup.file_path)
            
            if backup.compress:
                # 压缩备份
                with open(source_db, 'rb') as f_in:
                    with gzip.open(backup_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # 直接复制
                shutil.copy2(source_db, backup_path)
            
            logger.info(f"备份文件创建成功: {backup_path}")
            
        except Exception as e:
            logger.error(f"执行备份操作失败: {e}")
            raise
    
    def _perform_restore(self, backup: DatabaseBackup) -> None:
        """执行恢复操作"""
        try:
            backup_path = Path(backup.file_path)
            target_db = Path(settings.DATABASE_URL.replace('sqlite:///', ''))
            
            # 停止应用连接（这里需要根据实际情况实现）
            # 在生产环境中，可能需要更复杂的连接管理
            
            if backup.compress:
                # 解压恢复
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(target_db, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # 直接复制
                shutil.copy2(backup_path, target_db)
            
            logger.info(f"数据库恢复成功: {backup_path} -> {target_db}")
            
        except Exception as e:
            logger.error(f"执行恢复操作失败: {e}")
            raise