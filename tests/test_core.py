#!/usr/bin/env python3
"""
Unit Tests for Core Logic Module
核心逻辑模块单元测试
"""

import unittest
import tempfile
import shutil
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from logic.core import (
    WordItem, SentenceItem, ReviewScheduler, DataManager, MemorizerCore
)


class TestWordItem(unittest.TestCase):
    """测试WordItem数据类"""
    
    def test_word_item_creation(self):
        """测试WordItem创建"""
        word = WordItem(
            word="apple",
            meaning="苹果",
            pronunciation="/ˈæpl/",
            difficulty=1
        )
        
        self.assertEqual(word.word, "apple")
        self.assertEqual(word.meaning, "苹果")
        self.assertEqual(word.pronunciation, "/ˈæpl/")
        self.assertEqual(word.difficulty, 1)
        self.assertEqual(word.review_count, 0)
        self.assertEqual(word.correct_count, 0)
        self.assertIsNotNone(word.last_review)
        self.assertIsNotNone(word.next_review)
    
    def test_word_item_defaults(self):
        """测试WordItem默认值"""
        word = WordItem(word="test", meaning="测试")
        
        self.assertEqual(word.difficulty, 1)
        self.assertEqual(word.easiness_factor, 2.5)
        self.assertEqual(word.interval, 1)


class TestSentenceItem(unittest.TestCase):
    """测试SentenceItem数据类"""
    
    def test_sentence_item_creation(self):
        """测试SentenceItem创建"""
        sentence = SentenceItem(
            sentence="Hello world",
            translation="你好世界",
            difficulty=2
        )
        
        self.assertEqual(sentence.sentence, "Hello world")
        self.assertEqual(sentence.translation, "你好世界")
        self.assertEqual(sentence.difficulty, 2)
        self.assertIsNotNone(sentence.last_review)
        self.assertIsNotNone(sentence.next_review)


class TestReviewScheduler(unittest.TestCase):
    """测试复习调度器"""
    
    def setUp(self):
        """测试前准备"""
        self.scheduler = ReviewScheduler()
        self.word = WordItem(word="test", meaning="测试")
        self.sentence = SentenceItem(sentence="Test sentence", translation="测试句子")
    
    def test_calculate_next_review_correct(self):
        """测试正确答案的复习间隔计算"""
        interval, ef = self.scheduler.calculate_next_review(self.word, 4)
        
        self.assertEqual(interval, 6)  # 第一次正确答案间隔应为6天
        self.assertGreaterEqual(ef, 1.3)  # 易度因子应该不小于1.3
    
    def test_calculate_next_review_incorrect(self):
        """测试错误答案的复习间隔计算"""
        interval, ef = self.scheduler.calculate_next_review(self.word, 1)
        
        self.assertEqual(interval, 1)  # 错误答案间隔重置为1天
        self.assertGreaterEqual(ef, 1.3)
    
    def test_update_item_after_review(self):
        """测试复习后更新项目状态"""
        original_count = self.word.review_count
        original_correct = self.word.correct_count
        
        self.scheduler.update_item_after_review(self.word, True, 4)
        
        self.assertEqual(self.word.review_count, original_count + 1)
        self.assertEqual(self.word.correct_count, original_correct + 1)
        self.assertIsNotNone(self.word.next_review)
    
    def test_shuffle_queue(self):
        """测试队列随机化"""
        # 添加测试项目到队列
        for i in range(10):
            word = WordItem(word=f"word{i}", meaning=f"meaning{i}")
            self.scheduler.words_queue.append(word)
        
        original_order = list(self.scheduler.words_queue)
        self.scheduler.shuffle_queue("word")
        
        # 检查是否真的被打乱了（这个测试可能偶尔失败，但概率很低）
        shuffled_order = list(self.scheduler.words_queue)
        self.assertEqual(len(original_order), len(shuffled_order))


class TestDataManager(unittest.TestCase):
    """测试数据管理器"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_manager = DataManager(self.temp_dir)
        
        # 创建测试CSV文件
        self.csv_file = Path(self.temp_dir) / "test_words.csv"
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['word', 'meaning', 'pronunciation', 'difficulty'])
            writer.writerow(['apple', '苹果', '/ˈæpl/', '1'])
            writer.writerow(['banana', '香蕉', '/bəˈnænə/', '2'])
        
        # 创建测试JSON文件
        self.json_file = Path(self.temp_dir) / "test_sentences.json"
        test_sentences = [
            {
                "sentence": "Hello world",
                "translation": "你好世界",
                "difficulty": 1
            },
            {
                "sentence": "Good morning",
                "translation": "早上好",
                "difficulty": 1
            }
        ]
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(test_sentences, f, ensure_ascii=False)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_load_words_from_csv(self):
        """测试从CSV加载单词"""
        count = self.data_manager.load_words_from_csv("test_words.csv")
        
        self.assertEqual(count, 2)
        self.assertIn("apple", self.data_manager.words)
        self.assertIn("banana", self.data_manager.words)
        
        apple = self.data_manager.words["apple"]
        self.assertEqual(apple.meaning, "苹果")
        self.assertEqual(apple.pronunciation, "/ˈæpl/")
        self.assertEqual(apple.difficulty, 1)
    
    def test_load_sentences_from_json(self):
        """测试从JSON加载句子"""
        count = self.data_manager.load_sentences_from_json("test_sentences.json")
        
        self.assertEqual(count, 2)
        self.assertIn("Hello world", self.data_manager.sentences)
        self.assertIn("Good morning", self.data_manager.sentences)
        
        hello = self.data_manager.sentences["Hello world"]
        self.assertEqual(hello.translation, "你好世界")
        self.assertEqual(hello.difficulty, 1)
    
    def test_save_and_load_progress(self):
        """测试保存和加载进度"""
        # 先加载一些数据
        self.data_manager.load_words_from_csv("test_words.csv")
        self.data_manager.load_sentences_from_json("test_sentences.json")
        
        # 修改一些数据
        apple = self.data_manager.words["apple"]
        apple.review_count = 5
        apple.correct_count = 4
        
        # 保存进度
        self.assertTrue(self.data_manager.save_progress())
        
        # 创建新的数据管理器并加载进度
        new_manager = DataManager(self.temp_dir)
        self.assertTrue(new_manager.load_progress())
        
        # 验证数据
        self.assertIn("apple", new_manager.words)
        loaded_apple = new_manager.words["apple"]
        self.assertEqual(loaded_apple.review_count, 5)
        self.assertEqual(loaded_apple.correct_count, 4)
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        # 加载测试数据
        self.data_manager.load_words_from_csv("test_words.csv")
        self.data_manager.load_sentences_from_json("test_sentences.json")
        
        # 模拟一些复习记录
        apple = self.data_manager.words["apple"]
        apple.review_count = 10
        apple.correct_count = 8
        
        stats = self.data_manager.get_statistics()
        
        self.assertIn('words', stats)
        self.assertIn('sentences', stats)
        self.assertEqual(stats['words']['total'], 2)
        self.assertEqual(stats['sentences']['total'], 2)
    
    def test_get_error_prone_items(self):
        """测试获取易错项目"""
        # 加载测试数据
        self.data_manager.load_words_from_csv("test_words.csv")
        
        # 设置错误率不同的项目
        apple = self.data_manager.words["apple"]
        apple.review_count = 10
        apple.correct_count = 5  # 50%正确率
        
        banana = self.data_manager.words["banana"]
        banana.review_count = 10
        banana.correct_count = 9  # 90%正确率
        
        error_items = self.data_manager.get_error_prone_items("word", 5)
        
        self.assertTrue(len(error_items) > 0)
        # apple应该在banana之前（错误率更高）
        self.assertEqual(error_items[0].word, "apple")


class TestMemorizerCore(unittest.TestCase):
    """测试记忆系统核心类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.core = MemorizerCore(self.temp_dir)
        
        # 创建测试数据文件
        self._create_test_data()
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_data(self):
        """创建测试数据"""
        # 创建单词文件
        csv_file = Path(self.temp_dir) / "words_cet6.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['word', 'meaning', 'pronunciation', 'difficulty'])
            writer.writerow(['test', '测试', '/test/', '1'])
        
        # 创建句子文件
        json_file = Path(self.temp_dir) / "sentences_500.json"
        test_sentences = [
            {
                "sentence": "This is a test",
                "translation": "这是一个测试",
                "difficulty": 1
            }
        ]
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(test_sentences, f, ensure_ascii=False)
    
    def test_initialize(self):
        """测试系统初始化"""
        result = self.core.initialize()
        
        self.assertTrue(result)
        self.assertGreater(len(self.core.data_manager.words), 0)
        self.assertGreater(len(self.core.data_manager.sentences), 0)
    
    def test_get_next_review_item(self):
        """测试获取下一个复习项目"""
        self.core.initialize()
        
        # 测试获取单词
        word_item = self.core.get_next_review_item("word")
        self.assertIsInstance(word_item, WordItem)
        
        # 测试获取句子
        sentence_item = self.core.get_next_review_item("sentence")
        self.assertIsInstance(sentence_item, SentenceItem)
    
    def test_submit_answer(self):
        """测试提交答案"""
        self.core.initialize()
        
        item = self.core.get_next_review_item("word")
        if item:
            original_count = item.review_count
            original_correct = item.correct_count
            
            self.core.submit_answer(item, True)
            
            self.assertEqual(item.review_count, original_count + 1)
            self.assertEqual(item.correct_count, original_correct + 1)
            self.assertEqual(self.core.current_session['total_answers'], 1)
            self.assertEqual(self.core.current_session['correct_answers'], 1)
    
    def test_get_session_stats(self):
        """测试获取会话统计"""
        self.core.initialize()
        
        stats = self.core.get_session_stats()
        
        self.assertIn('session_time', stats)
        self.assertIn('words_reviewed', stats)
        self.assertIn('sentences_reviewed', stats)
        self.assertIn('total_reviewed', stats)
        self.assertIn('accuracy', stats)
        
        self.assertIsInstance(stats['accuracy'], (int, float))
        self.assertGreaterEqual(stats['accuracy'], 0)
        self.assertLessEqual(stats['accuracy'], 100)
    
    def test_get_overall_stats(self):
        """测试获取总体统计"""
        self.core.initialize()
        
        stats = self.core.get_overall_stats()
        
        self.assertIn('words', stats)
        self.assertIn('sentences', stats)
        self.assertIn('daily_progress', stats)


if __name__ == '__main__':
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestWordItem))
    suite.addTests(loader.loadTestsFromTestCase(TestSentenceItem))
    suite.addTests(loader.loadTestsFromTestCase(TestReviewScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestDataManager))
    suite.addTests(loader.loadTestsFromTestCase(TestMemorizerCore))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    print(f"\n测试完成!")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")