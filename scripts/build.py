#!/usr/bin/env python3
"""
Build Script for Word & Sentence Memorizer
打包脚本 - 生成跨平台可执行文件

Supports:
- Windows: PyInstaller to create .exe
- macOS: py2app to create .app bundle
- Linux: PyInstaller to create executable
"""

import os
import sys
import platform
import shutil
import subprocess
from pathlib import Path
import json

# Project configuration
PROJECT_NAME = "WordMemorizer"
VERSION = "1.0.0"
AUTHOR = "Course Design Team"
DESCRIPTION = "English Dictation and Vocabulary Memory System"

# Paths
ROOT_DIR = Path(__file__).parent.parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
MAIN_SCRIPT = ROOT_DIR / "ui" / "main.py"


def clean_build_dirs():
    """清理构建目录"""
    print("🧹 Cleaning build directories...")
    
    dirs_to_clean = [DIST_DIR, BUILD_DIR]
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"   Removed: {dir_path}")
    
    print("✅ Build directories cleaned")


def install_dependencies():
    """安装构建依赖"""
    print("📦 Installing build dependencies...")
    
    current_platform = platform.system().lower()
    
    if current_platform == "windows":
        build_deps = ["pyinstaller"]
    elif current_platform == "darwin":  # macOS
        build_deps = ["py2app", "pyinstaller"]
    else:  # Linux and others
        build_deps = ["pyinstaller"]
    
    for dep in build_deps:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
            print(f"   ✅ Installed: {dep}")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to install {dep}: {e}")
            return False
    
    return True


def build_with_pyinstaller():
    """使用PyInstaller构建"""
    print("🔨 Building with PyInstaller...")
    
    # 根据平台选择路径分隔符
    current_platform = platform.system().lower()
    if current_platform == "windows":
        data_separator = ";"
    else:
        data_separator = ":"
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", PROJECT_NAME,
        "--onefile",  # Single executable file
        "--windowed",  # No console window
        "--add-data", f"{ROOT_DIR}/data{data_separator}data",  # Include data files
        "--hidden-import", "tkinter",
        "--hidden-import", "matplotlib",
        "--hidden-import", "PIL",
        "--hidden-import", "pygame",
        "--hidden-import", "sounddevice",
        "--hidden-import", "edge_tts",
        "--hidden-import", "pydub",
        "--hidden-import", "sqlite3",
        str(MAIN_SCRIPT)
    ]
    
    try:
        # Change to project root directory
        os.chdir(ROOT_DIR)
        
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("   ✅ PyInstaller build completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ PyInstaller build failed: {e}")
        print(f"   Error output: {e.stderr}")
        return False


def build_with_py2app():
    """使用py2app构建macOS应用"""
    print("🍎 Building macOS app with py2app...")
    
    # Create setup.py for py2app
    setup_py_content = f'''
from setuptools import setup
import py2app

APP = ['{MAIN_SCRIPT}']
DATA_FILES = [('data', ['{ROOT_DIR}/data/words_cet6.csv'])]
OPTIONS = {{
    'argv_emulation': True,
    'includes': ['tkinter', 'sqlite3'],
    'packages': ['matplotlib', 'PIL', 'pygame', 'sounddevice', 'edge_tts', 'pydub', 'numpy', 'scipy'],
    'excludes': ['PyQt4', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'PyInstaller', 'pytest'],
    'resources': [],
    'iconfile': None,
    'plist': {{
        'CFBundleName': '{PROJECT_NAME}',
        'CFBundleDisplayName': '{PROJECT_NAME}',
        'CFBundleGetInfoString': '{DESCRIPTION}',
        'CFBundleVersion': '{VERSION}',
        'CFBundleShortVersionString': '{VERSION}',
        'NSHumanReadableCopyright': 'Copyright © 2024 {AUTHOR}',
        'LSMinimumSystemVersion': '10.14.0',
    }}
}}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={{'py2app': OPTIONS}},
    setup_requires=['py2app'],
)
'''
    
    setup_py_path = ROOT_DIR / "setup.py"
    
    try:
        # Write setup.py
        with open(setup_py_path, 'w', encoding='utf-8') as f:
            f.write(setup_py_content)
        
        # Change to project root
        os.chdir(ROOT_DIR)
        
        # Run py2app
        cmd = [sys.executable, "setup.py", "py2app"]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("   ✅ py2app build completed")
        
        # Clean up setup.py
        setup_py_path.unlink()
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ py2app build failed: {e}")
        print(f"   Error output: {e.stderr}")
        return False
    finally:
        # Always clean up setup.py
        if setup_py_path.exists():
            setup_py_path.unlink()


def create_installer_info():
    """创建安装信息文件"""
    print("📄 Creating installer info...")
    
    info = {
        "name": PROJECT_NAME,
        "version": VERSION,
        "description": DESCRIPTION,
        "author": AUTHOR,
        "platform": platform.system(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "build_date": __import__('datetime').datetime.now().isoformat()
    }
    
    info_file = DIST_DIR / "build_info.json"
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Build info saved to: {info_file}")


def copy_additional_files():
    """复制额外文件到分发目录"""
    print("📋 Copying additional files...")
    
    files_to_copy = [
        (ROOT_DIR / "README.md", "README.md"),
        (ROOT_DIR / "requirements.txt", "requirements.txt"),
        (ROOT_DIR / "data", "data"),
    ]
    
    for src, dst_name in files_to_copy:
        if src.exists():
            dst = DIST_DIR / dst_name
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            print(f"   ✅ Copied: {src.name}")


def show_build_summary():
    """显示构建摘要"""
    print("\n" + "="*50)
    print("🎉 BUILD SUMMARY")
    print("="*50)
    
    if DIST_DIR.exists():
        print(f"📁 Distribution directory: {DIST_DIR}")
        print("📦 Generated files:")
        
        for item in DIST_DIR.iterdir():
            if item.is_file():
                size = item.stat().st_size / (1024 * 1024)  # MB
                print(f"   📄 {item.name} ({size:.1f} MB)")
            elif item.is_dir():
                print(f"   📁 {item.name}/")
        
        current_platform = platform.system().lower()
        if current_platform == "windows":
            print(f"\n🖥️  Run: {DIST_DIR / (PROJECT_NAME + '.exe')}")
        elif current_platform == "darwin":
            print(f"\n🍎 Run: open {DIST_DIR / (PROJECT_NAME + '.app')}")
        else:
            print(f"\n🐧 Run: {DIST_DIR / PROJECT_NAME}")
    else:
        print("❌ No distribution files found!")


def main():
    """主构建函数"""
    print(f"🚀 Building {PROJECT_NAME} v{VERSION}")
    print(f"🖥️  Platform: {platform.system()} {platform.machine()}")
    print(f"🐍 Python: {platform.python_version()}")
    print("-" * 50)
    
    # Step 1: Clean build directories
    clean_build_dirs()
    
    # Step 2: Install build dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return 1
    
    # Step 3: Build based on platform
    current_platform = platform.system().lower()
    build_success = False
    
    if current_platform == "darwin" and "--py2app" in sys.argv:
        # macOS with py2app
        build_success = build_with_py2app()
    else:
        # All platforms with PyInstaller
        build_success = build_with_pyinstaller()
    
    if not build_success:
        print("❌ Build failed!")
        return 1
    
    # Step 4: Create installer info
    create_installer_info()
    
    # Step 5: Copy additional files
    copy_additional_files()
    
    # Step 6: Show summary
    show_build_summary()
    
    print("\n✅ Build completed successfully!")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)