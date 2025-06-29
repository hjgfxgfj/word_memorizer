#!/usr/bin/env python3
"""
英语听写与词汇记忆系统 - 命令行演示版
Word & Sentence Memorizer - Command Line Demo
"""

import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from logic.core import MemorizerCore, WordItem, SentenceItem
from logic.ai import get_ai_explainer

def print_header():
    """打印程序标题"""
    print("=" * 60)
    print("🎓 英语听写与词汇记忆系统 - 演示版")
    print("   Word & Sentence Memorizer - Demo")
    print("=" * 60)

def show_menu():
    """显示主菜单"""
    print("\n📋 主菜单:")
    print("1. 单词听写练习")
    print("2. 句子听写练习") 
    print("3. 查看学习统计")
    print("4. AI词汇释义演示")
    print("5. 数据管理")
    print("0. 退出程序")
    print("-" * 40)

def word_practice(core: MemorizerCore):
    """单词练习模式"""
    print("\n📝 单词听写练习")
    print("-" * 30)
    
    item = core.get_next_review_item("word")
    if not item:
        print("😊 所有单词已复习完成！")
        return
    
    print(f"📖 单词含义: {item.meaning}")
    if item.pronunciation:
        print(f"🔊 音标: {item.pronunciation}")
    print(f"📊 难度等级: {item.difficulty}/5")
    print(f"📈 复习记录: {item.review_count}次 (正确{item.correct_count}次)")
    
    print("\n请输入对应的英文单词:")
    user_input = input(">>> ").strip()
    
    if user_input.lower() == item.word.lower():
        print("✅ 正确！")
        core.submit_answer(item, True)
    else:
        print(f"❌ 错误！正确答案是: {item.word}")
        core.submit_answer(item, False)
    
    input("\n按回车继续...")

def sentence_practice(core: MemorizerCore):
    """句子练习模式"""
    print("\n📖 句子听写练习")
    print("-" * 30)
    
    item = core.get_next_review_item("sentence")
    if not item:
        print("😊 所有句子已复习完成！")
        return
    
    print(f"📖 中文翻译: {item.translation}")
    print(f"📊 难度等级: {item.difficulty}/5")
    print(f"📈 复习记录: {item.review_count}次 (正确{item.correct_count}次)")
    
    print("\n请输入对应的英文句子:")
    user_input = input(">>> ").strip()
    
    # 简单的相似度比较
    original_words = item.sentence.lower().split()
    user_words = user_input.lower().split()
    
    correct_words = sum(1 for word in user_words if word in original_words)
    similarity = (correct_words / len(original_words) * 100) if original_words else 0
    
    if similarity >= 80:
        print(f"✅ 很好！相似度: {similarity:.1f}%")
        core.submit_answer(item, True)
    else:
        print(f"❌ 需要改进。相似度: {similarity:.1f}%")
        print(f"📝 正确答案: {item.sentence}")
        core.submit_answer(item, False)
    
    input("\n按回车继续...")

def show_statistics(core: MemorizerCore):
    """显示学习统计"""
    print("\n📊 学习统计")
    print("-" * 30)
    
    overall_stats = core.get_overall_stats()
    session_stats = core.get_session_stats()
    
    print("📈 总体统计:")
    words = overall_stats.get('words', {})
    sentences = overall_stats.get('sentences', {})
    
    print(f"  📝 单词: {words.get('total', 0)}个 (已复习{words.get('reviewed', 0)}个)")
    print(f"      正确率: {words.get('accuracy', 0):.1f}%")
    
    print(f"  📖 句子: {sentences.get('total', 0)}个 (已复习{sentences.get('reviewed', 0)}个)")
    print(f"      正确率: {sentences.get('accuracy', 0):.1f}%")
    
    print("\n📊 当前会话:")
    print(f"  ⏱️  会话时长: {session_stats.get('session_time', '0:00:00')}")
    print(f"  📝 已复习: {session_stats.get('total_reviewed', 0)}个")
    print(f"  ✅ 正确率: {session_stats.get('accuracy', 0):.1f}%")
    print(f"  📚 待复习: 单词{session_stats.get('remaining_words', 0)}个, 句子{session_stats.get('remaining_sentences', 0)}个")
    
    input("\n按回车继续...")

def ai_demo():
    """AI释义演示"""
    print("\n🤖 AI智能释义演示")
    print("-" * 30)
    print("⚠️  注意: 需要配置Deepseek API密钥才能使用AI功能")
    print("   请在 logic/ai.py 中设置您的API密钥")
    
    word = input("\n请输入要查询的英文单词: ").strip()
    if not word:
        return
    
    print(f"\n🔍 正在查询 '{word}' 的释义...")
    
    try:
        ai_explainer = get_ai_explainer()
        result = ai_explainer.explain_word(word)
        
        print(f"\n📝 单词: {result['word']}")
        
        if result.get('pronunciation'):
            print(f"🔊 发音: {result['pronunciation']}")
        
        if result.get('word_type'):
            print(f"📚 词性: {result['word_type']}")
        
        if result.get('meanings'):
            print("💡 主要含义:")
            for i, meaning in enumerate(result['meanings'], 1):
                print(f"  {i}. {meaning}")
        
        if result.get('examples'):
            print("📖 例句:")
            for i, example in enumerate(result['examples'], 1):
                print(f"  {i}. {example}")
        
        if result.get('synonyms'):
            print(f"🔗 同义词: {', '.join(result['synonyms'])}")
    
    except Exception as e:
        print(f"❌ AI释义获取失败: {e}")
        print("💡 提示: 请检查网络连接和API密钥配置")
    
    input("\n按回车继续...")

def data_management(core: MemorizerCore):
    """数据管理"""
    print("\n💾 数据管理")
    print("-" * 30)
    print("1. 查看词汇列表")
    print("2. 查看句子列表")
    print("3. 保存学习进度")
    print("4. 返回主菜单")
    
    choice = input("\n请选择: ").strip()
    
    if choice == "1":
        print("\n📝 词汇列表:")
        for i, (word, item) in enumerate(core.data_manager.words.items(), 1):
            status = f"✅ 已掌握" if item.correct_count > item.review_count // 2 else "📚 学习中"
            print(f"{i:2d}. {word:15} - {item.meaning:20} {status}")
            if i >= 10:
                print(f"    ... 还有 {len(core.data_manager.words) - 10} 个单词")
                break
    
    elif choice == "2":
        print("\n📖 句子列表:")
        for i, (sentence, item) in enumerate(core.data_manager.sentences.items(), 1):
            status = f"✅ 已掌握" if item.correct_count > item.review_count // 2 else "📚 学习中"
            short_sentence = sentence[:40] + "..." if len(sentence) > 40 else sentence
            print(f"{i:2d}. {short_sentence:45} {status}")
            if i >= 10:
                print(f"    ... 还有 {len(core.data_manager.sentences) - 10} 个句子")
                break
    
    elif choice == "3":
        if core.data_manager.save_progress():
            print("✅ 学习进度已保存")
        else:
            print("❌ 保存失败")
    
    if choice in ["1", "2", "3"]:
        input("\n按回车继续...")

def main():
    """主函数"""
    print_header()
    
    # 初始化系统
    print("🚀 正在初始化系统...")
    core = MemorizerCore()
    core.initialize()
    
    print("✅ 初始化完成！")
    time.sleep(1)
    
    while True:
        show_menu()
        choice = input("请选择功能 (0-5): ").strip()
        
        if choice == "0":
            print("\n👋 感谢使用英语听写与词汇记忆系统！")
            print("📊 正在保存学习进度...")
            core.data_manager.save_progress()
            print("✅ 进度已保存，再见！")
            break
        elif choice == "1":
            word_practice(core)
        elif choice == "2":
            sentence_practice(core)
        elif choice == "3":
            show_statistics(core)
        elif choice == "4":
            ai_demo()
        elif choice == "5":
            data_management(core)
        else:
            print("❌ 无效选择，请输入 0-5")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断，再见！")
    except Exception as e:
        print(f"\n💥 程序出错: {e}")
        print("请检查系统配置或联系开发者")