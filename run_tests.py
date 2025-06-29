#!/usr/bin/env python3
"""
Test Runner for Word & Sentence Memorizer
测试运行器 - 运行所有单元测试
"""

import unittest
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_all_tests():
    """运行所有测试"""
    # 发现并运行所有测试
    loader = unittest.TestLoader()
    start_dir = project_root / 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 配置测试运行器
    runner = unittest.TextTestRunner(
        verbosity=2,
        buffer=True,  # 捕获测试期间的stdout/stderr
        failfast=False  # 遇到失败不立即停止
    )
    
    print("=" * 70)
    print("🧪 英语听写与词汇记忆系统 - 单元测试")
    print("=" * 70)
    
    # 运行测试
    result = runner.run(suite)
    
    # 输出测试总结
    print("\n" + "=" * 70)
    print("📊 测试结果总结")
    print("=" * 70)
    print(f"✅ 总共运行测试: {result.testsRun}")
    print(f"❌ 失败测试: {len(result.failures)}")
    print(f"⚠️  错误测试: {len(result.errors)}")
    print(f"⏭️  跳过测试: {len(result.skipped)}")
    
    # 计算成功率
    if result.testsRun > 0:
        success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
        print(f"🎯 成功率: {success_rate:.1f}%")
    
    # 详细错误信息
    if result.failures:
        print("\n" + "🔴 失败的测试:")
        print("-" * 50)
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"{i}. {test}")
            print(f"   错误: {traceback.split('AssertionError: ')[-1].split('\\n')[0] if 'AssertionError: ' in traceback else 'Unknown error'}")
    
    if result.errors:
        print("\n" + "⚠️  出错的测试:")
        print("-" * 50)
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"{i}. {test}")
            error_line = traceback.split('\\n')[-2] if traceback.split('\\n') else "Unknown error"
            print(f"   错误: {error_line}")
    
    # 返回退出码
    if result.failures or result.errors:
        print("\n❌ 测试未完全通过!")
        return 1
    else:
        print("\n✅ 所有测试通过!")
        return 0

def run_specific_test(test_name):
    """运行特定测试模块"""
    if test_name not in ['core', 'ai', 'audio']:
        print(f"❌ 未知的测试模块: {test_name}")
        print("可用模块: core, ai, audio")
        return 1
    
    module_name = f"tests.test_{test_name}"
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(module_name)
    
    runner = unittest.TextTestRunner(verbosity=2)
    
    print("=" * 70)
    print(f"🧪 运行 {test_name} 模块测试")
    print("=" * 70)
    
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1

def main():
    """主函数"""
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        return run_specific_test(test_name)
    else:
        return run_all_tests()

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 测试运行器出错: {e}")
        sys.exit(1)