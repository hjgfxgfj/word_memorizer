#!/usr/bin/env python3
"""
Unit Tests for AI Explanation Module
AI释义模块单元测试
"""

import unittest
import tempfile
import shutil
import json
import time
import sqlite3
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from logic.ai import (
    DeepseekAPIClient, AIExplanationCache, AIExplainerManager, get_ai_explainer
)


class TestDeepseekAPIClient(unittest.TestCase):
    """测试Deepseek API客户端"""
    
    def setUp(self):
        """测试前准备"""
        self.client = DeepseekAPIClient("test-api-key")
    
    def test_build_word_prompt(self):
        """测试单词提示词构建"""
        prompt = self.client._build_word_prompt("apple")
        
        self.assertIn("apple", prompt)
        self.assertIn("JSON", prompt)
        self.assertIn("meanings", prompt)
        self.assertIn("examples", prompt)
    
    def test_build_sentence_prompt(self):
        """测试句子提示词构建"""
        prompt = self.client._build_sentence_prompt("Hello world")
        
        self.assertIn("Hello world", prompt)
        self.assertIn("JSON", prompt)
        self.assertIn("translation", prompt)
        self.assertIn("grammar_points", prompt)
    
    def test_parse_word_response(self):
        """测试单词响应解析"""
        # 测试正常JSON响应
        json_response = '''
        {
            "word": "apple",
            "meanings": ["苹果", "苹果公司"],
            "examples": ["I eat an apple.", "Apple is a tech company."],
            "synonyms": ["fruit"],
            "pronunciation": "/ˈæpl/",
            "word_type": "noun"
        }
        '''
        
        result = self.client._parse_word_response(json_response, "apple")
        
        self.assertEqual(result['word'], "apple")
        self.assertEqual(len(result['meanings']), 2)
        self.assertEqual(len(result['examples']), 2)
        self.assertEqual(result['pronunciation'], "/ˈæpl/")
    
    def test_parse_word_response_invalid_json(self):
        """测试无效JSON响应的处理"""
        invalid_response = "This is not a valid JSON response"
        
        result = self.client._parse_word_response(invalid_response, "apple")
        
        self.assertEqual(result['word'], "apple")
        self.assertIsInstance(result['meanings'], list)
        self.assertGreater(len(result['meanings']), 0)
    
    def test_parse_sentence_response(self):
        """测试句子响应解析"""
        json_response = '''
        {
            "sentence": "Hello world",
            "translation": "你好世界",
            "grammar_points": ["简单句"],
            "key_words": [{"word": "hello", "meaning": "你好", "usage": "问候语"}],
            "difficulty_level": 1
        }
        '''
        
        result = self.client._parse_sentence_response(json_response, "Hello world")
        
        self.assertEqual(result['sentence'], "Hello world")
        self.assertEqual(result['translation'], "你好世界")
        self.assertEqual(result['difficulty_level'], 1)
        self.assertIsInstance(result['key_words'], list)
    
    @patch('requests.Session.post')
    def test_call_api_success(self, mock_post):
        """测试API调用成功"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'test response'}}]
        }
        mock_post.return_value = mock_response
        
        result = self.client._call_api("test prompt")
        
        self.assertEqual(result, "test response")
        mock_post.assert_called_once()
    
    @patch('requests.Session.post')
    def test_call_api_rate_limit(self, mock_post):
        """测试API限流处理"""
        # Mock rate limit response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response
        
        with self.assertRaises(Exception):
            self.client._call_api("test prompt")
    
    @patch('requests.Session.post')
    def test_call_api_failure(self, mock_post):
        """测试API调用失败"""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        with self.assertRaises(Exception):
            self.client._call_api("test prompt")


class TestAIExplanationCache(unittest.TestCase):
    """测试AI释义缓存系统"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = AIExplanationCache(self.temp_dir, ttl_hours=1)  # 1小时TTL用于测试
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_cache_initialization(self):
        """测试缓存初始化"""
        db_path = Path(self.temp_dir) / "ai_cache.db"
        self.assertTrue(db_path.exists())
        
        # 检查表是否创建
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='explanations'
            """)
            self.assertIsNotNone(cursor.fetchone())
    
    def test_generate_cache_key(self):
        """测试缓存键生成"""
        key1 = self.cache._generate_cache_key("apple", "word")
        key2 = self.cache._generate_cache_key("APPLE", "word")  # 大小写不同
        key3 = self.cache._generate_cache_key("apple", "sentence")  # 类型不同
        
        self.assertEqual(key1, key2)  # 应该相同（忽略大小写）
        self.assertNotEqual(key1, key3)  # 应该不同（类型不同）
    
    def test_set_and_get_cache(self):
        """测试缓存设置和获取"""
        test_data = {
            "word": "apple",
            "meanings": ["苹果"],
            "examples": ["I eat an apple."]
        }
        
        # 设置缓存
        self.cache.set("apple", "word", test_data)
        
        # 获取缓存
        cached_data = self.cache.get("apple", "word")
        
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data["word"], "apple")
        self.assertEqual(cached_data["meanings"], ["苹果"])
    
    def test_cache_miss(self):
        """测试缓存未命中"""
        result = self.cache.get("nonexistent", "word")
        self.assertIsNone(result)
    
    def test_cache_expiry(self):
        """测试缓存过期"""
        # 创建一个很短TTL的缓存用于测试
        short_cache = AIExplanationCache(self.temp_dir, ttl_hours=0.001)  # 约3.6秒
        
        test_data = {"word": "test"}
        short_cache.set("test", "word", test_data)
        
        # 立即获取应该成功
        result = short_cache.get("test", "word")
        self.assertIsNotNone(result)
        
        # 等待过期后应该为None
        time.sleep(4)
        result = short_cache.get("test", "word")
        self.assertIsNone(result)
    
    def test_cleanup_expired(self):
        """测试清理过期缓存"""
        # 添加一些测试数据
        test_data = {"word": "test"}
        self.cache.set("test1", "word", test_data)
        self.cache.set("test2", "word", test_data)
        
        # 手动设置过期时间（修改数据库）
        db_path = Path(self.temp_dir) / "ai_cache.db"
        with sqlite3.connect(db_path) as conn:
            # 设置一个项目为过期
            conn.execute("""
                UPDATE explanations 
                SET created_at = datetime('now', '-2 hours')
                WHERE key = ?
            """, (self.cache._generate_cache_key("test1", "word"),))
        
        # 清理过期缓存
        self.cache.cleanup_expired()
        
        # 检查结果
        result1 = self.cache.get("test1", "word")
        result2 = self.cache.get("test2", "word")
        
        self.assertIsNone(result1)  # 应该被清理
        self.assertIsNotNone(result2)  # 应该还在
    
    def test_get_cache_stats(self):
        """测试获取缓存统计"""
        # 添加一些测试数据
        test_data = {"word": "test"}
        self.cache.set("test1", "word", test_data)
        self.cache.set("test2", "sentence", test_data)
        
        # 模拟一些访问
        self.cache.get("test1", "word")
        self.cache.get("test1", "word")
        
        stats = self.cache.get_cache_stats()
        
        self.assertIn('total_cached', stats)
        self.assertIn('by_type', stats)
        self.assertIn('recent_avg_hits', stats)
        self.assertIn('cache_size_mb', stats)
        
        self.assertEqual(stats['total_cached'], 2)
        self.assertIn('word', stats['by_type'])
        self.assertIn('sentence', stats['by_type'])


class TestAIExplainerManager(unittest.TestCase):
    """测试AI解释管理器"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = AIExplainerManager(api_key="test-key", cache_dir=self.temp_dir)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    @patch.object(DeepseekAPIClient, 'explain_word')
    def test_explain_word_with_cache(self, mock_explain):
        """测试带缓存的单词解释"""
        # Mock API response
        mock_response = {
            "word": "test",
            "meanings": ["测试"],
            "examples": [],
            "synonyms": [],
            "pronunciation": "",
            "word_type": ""
        }
        mock_explain.return_value = mock_response
        
        # 第一次调用（应该调用API）
        result1 = self.manager.explain_word("test")
        self.assertEqual(result1["word"], "test")
        mock_explain.assert_called_once()
        
        # 第二次调用（应该使用缓存）
        mock_explain.reset_mock()
        result2 = self.manager.explain_word("test")
        self.assertEqual(result2["word"], "test")
        mock_explain.assert_not_called()  # 不应该再调用API
    
    @patch.object(DeepseekAPIClient, 'explain_sentence')
    def test_explain_sentence_with_cache(self, mock_explain):
        """测试带缓存的句子解释"""
        mock_response = {
            "sentence": "test sentence",
            "translation": "测试句子",
            "grammar_points": [],
            "key_words": [],
            "difficulty_level": 1
        }
        mock_explain.return_value = mock_response
        
        result = self.manager.explain_sentence("test sentence")
        self.assertEqual(result["sentence"], "test sentence")
        mock_explain.assert_called_once()
    
    @patch.object(DeepseekAPIClient, 'explain_word')
    def test_explain_word_api_failure(self, mock_explain):
        """测试API失败时的处理"""
        # Mock API failure
        mock_explain.side_effect = Exception("API Error")
        
        result = self.manager.explain_word("test")
        
        # 应该返回错误格式而不是抛出异常
        self.assertEqual(result["word"], "test")
        self.assertIn("无法获取解释", result["meanings"][0])
    
    @patch.object(DeepseekAPIClient, 'explain_word')
    def test_batch_explain_words(self, mock_explain):
        """测试批量单词解释"""
        mock_explain.side_effect = lambda word: {
            "word": word,
            "meanings": [f"{word}的含义"],
            "examples": [],
            "synonyms": [],
            "pronunciation": "",
            "word_type": ""
        }
        
        words = ["apple", "banana", "orange"]
        results = self.manager.batch_explain_words(words)
        
        self.assertEqual(len(results), 3)
        for word in words:
            self.assertIn(word, results)
            self.assertEqual(results[word]["word"], word)
    
    def test_get_cache_statistics(self):
        """测试获取缓存统计"""
        stats = self.manager.get_cache_statistics()
        
        self.assertIn('total_cached', stats)
        self.assertIsInstance(stats['total_cached'], int)


class TestGlobalAIExplainer(unittest.TestCase):
    """测试全局AI解释器"""
    
    def test_get_ai_explainer_singleton(self):
        """测试单例模式"""
        explainer1 = get_ai_explainer()
        explainer2 = get_ai_explainer()
        
        self.assertIs(explainer1, explainer2)  # 应该是同一个对象
    
    def test_get_ai_explainer_with_api_key(self):
        """测试带API密钥的获取"""
        explainer = get_ai_explainer("custom-api-key")
        self.assertIsInstance(explainer, AIExplainerManager)


if __name__ == '__main__':
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestDeepseekAPIClient))
    suite.addTests(loader.loadTestsFromTestCase(TestAIExplanationCache))
    suite.addTests(loader.loadTestsFromTestCase(TestAIExplainerManager))
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalAIExplainer))
    
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
            print(f"- {test}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}")