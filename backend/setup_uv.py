#!/usr/bin/env python3
"""
MCPS.ONE Backend UV Setup Script
快速设置 uv 虚拟环境和依赖的脚本

使用方法:
    python setup_uv.py
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """运行命令并返回结果"""
    print(f"🔄 执行命令: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.stdout:
            print(f"✅ 输出: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr.strip()}")
        raise


def check_uv_installed() -> bool:
    """检查 uv 是否已安装"""
    try:
        result = run_command("uv --version", check=False)
        return result.returncode == 0
    except:
        return False


def install_uv():
    """安装 uv"""
    print("📦 安装 uv...")
    run_command("pip install uv")


def setup_virtual_environment():
    """设置虚拟环境"""
    print("🏗️ 创建虚拟环境...")
    
    # 删除现有的虚拟环境（如果存在）
    venv_path = Path(".venv")
    if venv_path.exists():
        print("🗑️ 删除现有虚拟环境...")
        import shutil
        shutil.rmtree(venv_path)
    
    # 创建新的虚拟环境
    run_command("uv venv")
    
    print("✅ 虚拟环境创建完成")


def install_dependencies():
    """安装依赖"""
    print("📚 安装项目依赖...")
    
    # 检查 requirements.txt 是否存在
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt 文件不存在")
        return
    
    # 使用 uv pip 安装依赖
    run_command("uv pip install -r requirements.txt")
    
    print("✅ 依赖安装完成")


def generate_activation_script():
    """生成激活脚本"""
    print("📝 生成激活脚本...")
    
    # Windows 激活脚本
    activate_bat = """
@echo off
echo 🚀 激活 MCPS.ONE 后端虚拟环境...
call .venv\Scripts\activate.bat
echo ✅ 虚拟环境已激活
echo 💡 使用 'deactivate' 命令退出虚拟环境
cmd /k
"""
    
    with open("activate.bat", "w", encoding="utf-8") as f:
        f.write(activate_bat)
    
    # Unix/Linux 激活脚本
    activate_sh = """
#!/bin/bash
echo "🚀 激活 MCPS.ONE 后端虚拟环境..."
source .venv/bin/activate
echo "✅ 虚拟环境已激活"
echo "💡 使用 'deactivate' 命令退出虚拟环境"
exec "$SHELL"
"""
    
    with open("activate.sh", "w", encoding="utf-8") as f:
        f.write(activate_sh)
    
    # 设置执行权限（Unix/Linux）
    try:
        os.chmod("activate.sh", 0o755)
    except:
        pass  # Windows 上可能会失败，忽略
    
    print("✅ 激活脚本生成完成")
    print("   Windows: 运行 activate.bat")
    print("   Linux/Mac: 运行 ./activate.sh")


def main():
    """主函数"""
    print("🎯 MCPS.ONE Backend UV 环境设置")
    print("=" * 40)
    
    try:
        # 检查当前目录
        if not Path("requirements.txt").exists():
            print("❌ 请在 backend 目录下运行此脚本")
            sys.exit(1)
        
        # 检查并安装 uv
        if not check_uv_installed():
            print("📦 uv 未安装，正在安装...")
            install_uv()
        else:
            print("✅ uv 已安装")
        
        # 设置虚拟环境
        setup_virtual_environment()
        
        # 安装依赖
        install_dependencies()
        
        # 生成激活脚本
        generate_activation_script()
        
        print("\n🎉 设置完成！")
        print("\n📋 下一步操作:")
        print("1. 激活虚拟环境:")
        if os.name == 'nt':  # Windows
            print("   activate.bat")
        else:  # Unix/Linux
            print("   ./activate.sh")
        print("2. 启动应用:")
        print("   uvicorn app.main:app --reload")
        print("\n💡 提示:")
        print("- uv.lock 文件已生成，确保环境一致性")
        print("- 使用 'uv sync' 可快速同步依赖")
        print("- 使用 'uv add <package>' 添加新依赖")
        
    except Exception as e:
        print(f"\n❌ 设置过程中出现错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()