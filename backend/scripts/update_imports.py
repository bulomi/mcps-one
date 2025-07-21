#!/usr/bin/env python3
"""更新导入路径脚本 - 适应新的服务模块化结构"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# 导入路径映射表
IMPORT_MAPPING = {
    # 基础服务
    'from app.services.base_service import': 'from app.services.base import',
    'from app.services.cache_service import': 'from app.services.base import',
    'from app.services.error_handler import': 'from app.services.base import',

    # MCP服务
    'from app.services.mcp_service import': 'from app.services.mcp import',
    'from app.services.mcp_server import': 'from app.services.mcp import',
    'from app.services.mcp_proxy_server import': 'from app.services.mcp import',
    'from app.services.mcp_unified_service import': 'from app.services.mcp import',
    'from app.services.mcp_agent_service import': 'from app.services.mcp import',

    # 系统服务
    'from app.services.system_service import': 'from app.services.system import',
    'from app.services.log_service import': 'from app.services.system import',
    'from app.services.config_manager import': 'from app.services.system import',
    'from app.services.process_manager import': 'from app.services.system import',

    # 工具服务
    'from app.services.tool_service import': 'from app.services.tools import',
    'from app.services.tool_registry import': 'from app.services.tools import',

    # 任务服务
    'from app.services.task_service import': 'from app.services.tasks import',

    # 会话服务
    'from app.services.session_service import': 'from app.services.sessions import',
    'from app.services.auto_session_service import': 'from app.services.sessions import',

    # 用户服务
    'from app.services.user_service import': 'from app.services.users import',
    'from app.services.email_service import': 'from app.services.users import',

    # 集成服务
    'from app.services.proxy_service import': 'from app.services.integrations import',
    'from app.services.request_router import': 'from app.services.integrations import',
    'from app.services.webhook_service import': 'from app.services.integrations import',
}

def find_python_files(directory: str) -> List[Path]:
    """查找所有Python文件"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # 跳过__pycache__目录
        dirs[:] = [d for d in dirs if d != '__pycache__']

        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)

    return python_files

def update_imports_in_file(file_path: Path) -> Tuple[bool, List[str]]:
    """更新文件中的导入路径"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes = []

        # 应用导入映射
        for old_import, new_import in IMPORT_MAPPING.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes.append(f"{old_import} -> {new_import}")

        # 如果有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes

        return False, []

    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return False, []

def main():
    """主函数"""
    backend_dir = Path(__file__).parent.parent
    print(f"开始更新导入路径，目录: {backend_dir}")

    # 查找所有Python文件
    python_files = find_python_files(str(backend_dir))
    print(f"找到 {len(python_files)} 个Python文件")

    updated_files = 0
    total_changes = 0

    # 更新每个文件
    for file_path in python_files:
        # 跳过当前脚本文件
        if file_path.name == 'update_imports.py':
            continue

        changed, changes = update_imports_in_file(file_path)
        if changed:
            updated_files += 1
            total_changes += len(changes)
            print(f"\n更新文件: {file_path}")
            for change in changes:
                print(f"  - {change}")

    print(f"\n更新完成!")
    print(f"更新了 {updated_files} 个文件")
    print(f"总共进行了 {total_changes} 次导入路径更改")

if __name__ == '__main__':
    main()
