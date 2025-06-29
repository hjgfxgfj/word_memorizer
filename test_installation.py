#!/usr/bin/env python3
"""
Installation Test Script
安装测试脚本 - 验证依赖和核心功能
"""

import sys
import importlib
from pathlib import Path

def test_import(module_name, package_name=None):
    """测试模块导入"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name or module_name} - 成功导入")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name} - 导入失败: {e}")
        return False

def test_core_modules():
    """测试核心模块"""
    print("🧪 测试核心模块...")
    
    # 添加项目路径
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from logic.core import MemorizerCore, WordItem, SentenceItem
        print("✅ 核心逻辑模块 - 成功导入")
        
        # 测试基本功能
        word = WordItem(word="test", meaning="测试")
        sentence = SentenceItem(sentence="Test sentence", translation="测试句子")
        print("✅ 数据类 - 创建成功")
        
        core = MemorizerCore("test_data")
        print("✅ 记忆系统核心 - 初始化成功")
        
        return True
    except Exception as e:
        print(f"❌ 核心模块测试失败: {e}")
        return False

def test_ai_module():
    """测试AI模块"""
    print("\n🤖 测试AI模块...")
    
    try:
        from logic.ai import DeepseekAPIClient, AIExplanationCache
        print("✅ AI模块 - 成功导入")
        
        # 测试API客户端创建
        client = DeepseekAPIClient("test-key")
        print("✅ API客户端 - 创建成功")
        
        # 测试缓存系统
        cache = AIExplanationCache("test_cache")
        print("✅ 缓存系统 - 初始化成功")
        
        return True
    except Exception as e:
        print(f"❌ AI模块测试失败: {e}")
        return False

def test_audio_module():
    """测试音频模块"""
    print("\n🔊 测试音频模块...")
    
    try:
        from audio.listen import TTSEngine, AudioCache
        print("✅ 音频模块 - 成功导入")
        
        # 测试TTS引擎
        tts = TTSEngine()
        print("✅ TTS引擎 - 创建成功")
        
        # 测试音频缓存
        audio_cache = AudioCache("test_audio_cache")
        print("✅ 音频缓存 - 初始化成功")
        
        return True
    except Exception as e:
        print(f"❌ 音频模块测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 英语听写与词汇记忆系统 - 安装验证")
    print("=" * 60)
    
    # 测试Python版本
    python_version = sys.version_info
    print(f"🐍 Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python版本过低，需要3.8+")
        return False
    
    print("\n📦 测试第三方依赖...")
    
    # 测试核心依赖
    dependencies = [
        ("numpy", "NumPy"),
        ("scipy", "SciPy"), 
        ("matplotlib", "Matplotlib"),
        ("PIL", "Pillow"),
        ("tkinter", "Tkinter"),
        ("pygame", "Pygame"),
        ("requests", "Requests"),
        ("edge_tts", "Edge-TTS"),
        ("sv_ttk", "sv-ttk"),
    ]
    
    success_count = 0
    for module, name in dependencies:
        if test_import(module, name):
            success_count += 1
    
    print(f"\n依赖测试结果: {success_count}/{len(dependencies)} 成功")
    
    # 测试项目模块
    print("\n" + "=" * 60)
    print("🧩 测试项目模块...")
    
    module_tests = [
        test_core_modules,
        test_ai_module,
        test_audio_module
    ]
    
    module_success = 0
    for test_func in module_tests:
        if test_func():
            module_success += 1
    
    print(f"\n模块测试结果: {module_success}/{len(module_tests)} 成功")
    
    # 总结
    print("\n" + "=" * 60)
    
    total_success = success_count == len(dependencies) and module_success == len(module_tests)
    
    if total_success:
        print("🎉 安装验证成功！系统已准备就绪")
        print("\n📋 运行方式:")
        print("1. 激活虚拟环境: source venv/bin/activate")
        print("2. 运行GUI程序: python ui/main.py")
        print("3. 运行单元测试: python run_tests.py")
        print("4. 构建安装包: python scripts/build.py")
    else:
        print("❌ 安装验证失败，请检查依赖安装")
        print("\n🛠️ 解决方案:")
        print("1. 确保在虚拟环境中运行")
        print("2. 重新安装依赖: pip install -r requirements-basic.txt")
        print("3. 检查Python版本是否为3.8+")
    
    return total_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)