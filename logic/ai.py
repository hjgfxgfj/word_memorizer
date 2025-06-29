#!/usr/bin/env python3
"""
AI Explanation Module for Word & Sentence Memorizer
AI释义模块 - 调用Deepseek API提供词汇解释和例句

This module handles:
- Deepseek API integration for word explanations
- Caching system with SQLite to reduce API calls
- Retry mechanism for failed requests
- TTL (Time-To-Live) cache management
"""

import json
import sqlite3
import time
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import asyncio
import aiohttp
import requests
from concurrent.futures import ThreadPoolExecutor
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepseekAPIClient:
    """Deepseek API客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com/v1"):
        self.api_key = api_key or "your-deepseek-api-key-here"  # 需要替换为实际API密钥
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        self.timeout = 30
        self.max_retries = 3
        
    def explain_word(self, word: str, context: str = None) -> Dict:
        """
        获取单词的详细解释
        返回格式: {
            'word': str,
            'meanings': List[str],
            'examples': List[str],
            'synonyms': List[str],
            'pronunciation': str,
            'word_type': str
        }
        """
        prompt = self._build_word_prompt(word, context)
        response = self._call_api(prompt)
        return self._parse_word_response(response, word)
    
    def explain_sentence(self, sentence: str) -> Dict:
        """
        获取句子的详细解释
        返回格式: {
            'sentence': str,
            'translation': str,
            'grammar_points': List[str],
            'key_words': List[Dict],
            'difficulty_level': int
        }
        """
        prompt = self._build_sentence_prompt(sentence)
        response = self._call_api(prompt)
        return self._parse_sentence_response(response, sentence)
    
    def _build_word_prompt(self, word: str, context: str = None) -> str:
        """构建单词解释的提示词"""
        base_prompt = f"""
请为英语单词 "{word}" 提供详细解释，要求返回JSON格式：

{{
    "word": "{word}",
    "meanings": ["中文含义1", "中文含义2"],
    "examples": ["例句1 (带中文翻译)", "例句2 (带中文翻译)"],
    "synonyms": ["同义词1", "同义词2"],
    "pronunciation": "音标",
    "word_type": "词性"
}}

要求：
1. 提供2-3个最常用的中文含义
2. 给出2-3个实用例句，每个例句后面用括号标注中文翻译
3. 列出2-3个常用同义词
4. 标注国际音标
5. 标明词性（名词/动词/形容词等）
"""
        
        if context:
            base_prompt += f"\n\n上下文提示: {context}"
        
        return base_prompt
    
    def _build_sentence_prompt(self, sentence: str) -> str:
        """构建句子解释的提示词"""
        return f"""
请为英语句子 "{sentence}" 提供详细分析，要求返回JSON格式：

{{
    "sentence": "{sentence}",
    "translation": "中文翻译",
    "grammar_points": ["语法点1", "语法点2"],
    "key_words": [
        {{"word": "关键词", "meaning": "含义", "usage": "用法说明"}},
        {{"word": "关键词2", "meaning": "含义2", "usage": "用法说明2"}}
    ],
    "difficulty_level": 3
}}

要求：
1. 提供准确的中文翻译
2. 分析1-3个重要语法点
3. 提取2-4个关键词汇并解释
4. 评估难度等级(1-5，1最简单，5最难)
"""
    
    def _call_api(self, prompt: str) -> str:
        """调用Deepseek API"""
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content']
                elif response.status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt
                    logger.warning(f"API限流，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API调用失败，状态码: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"API请求异常 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        
        raise Exception("API调用失败，已达到最大重试次数")
    
    def _parse_word_response(self, response: str, word: str) -> Dict:
        """解析单词解释响应"""
        try:
            # 尝试解析JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            else:
                json_str = response
            
            result = json.loads(json_str)
            
            # 确保返回格式正确
            return {
                'word': result.get('word', word),
                'meanings': result.get('meanings', []),
                'examples': result.get('examples', []),
                'synonyms': result.get('synonyms', []),
                'pronunciation': result.get('pronunciation', ''),
                'word_type': result.get('word_type', '')
            }
        except json.JSONDecodeError:
            logger.warning(f"无法解析API响应为JSON: {response[:200]}...")
            # 返回基本格式
            return {
                'word': word,
                'meanings': [response[:100] + "..."],
                'examples': [],
                'synonyms': [],
                'pronunciation': '',
                'word_type': ''
            }
    
    def _parse_sentence_response(self, response: str, sentence: str) -> Dict:
        """解析句子解释响应"""
        try:
            # 尝试解析JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            else:
                json_str = response
            
            result = json.loads(json_str)
            
            return {
                'sentence': result.get('sentence', sentence),
                'translation': result.get('translation', ''),
                'grammar_points': result.get('grammar_points', []),
                'key_words': result.get('key_words', []),
                'difficulty_level': result.get('difficulty_level', 3)
            }
        except json.JSONDecodeError:
            logger.warning(f"无法解析API响应为JSON: {response[:200]}...")
            return {
                'sentence': sentence,
                'translation': response[:200] + "...",
                'grammar_points': [],
                'key_words': [],
                'difficulty_level': 3
            }


class AIExplanationCache:
    """AI解释缓存系统"""
    
    def __init__(self, cache_dir: str = "data", ttl_hours: int = 168):  # 默认7天TTL
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.db_path = self.cache_dir / "ai_cache.db"
        self.ttl_hours = ttl_hours
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """初始化缓存数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS explanations (
                    key TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    hit_count INTEGER DEFAULT 0
                )
            """)
            
            # 创建索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON explanations(created_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_type ON explanations(type)
            """)
    
    def _generate_cache_key(self, content: str, explanation_type: str) -> str:
        """生成缓存键"""
        combined = f"{explanation_type}:{content.lower().strip()}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def get(self, content: str, explanation_type: str) -> Optional[Dict]:
        """从缓存获取解释"""
        key = self._generate_cache_key(content, explanation_type)
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT content, created_at FROM explanations 
                    WHERE key = ? AND type = ?
                """, (key, explanation_type))
                
                row = cursor.fetchone()
                if row:
                    content_json, created_at = row
                    created_time = datetime.fromisoformat(created_at)
                    
                    # 检查是否过期
                    if datetime.now() - created_time < timedelta(hours=self.ttl_hours):
                        # 更新访问时间和命中次数
                        conn.execute("""
                            UPDATE explanations 
                            SET accessed_at = CURRENT_TIMESTAMP, hit_count = hit_count + 1
                            WHERE key = ?
                        """, (key,))
                        
                        logger.info(f"缓存命中: {explanation_type} - {content[:30]}...")
                        return json.loads(content_json)
                    else:
                        # 删除过期缓存
                        conn.execute("DELETE FROM explanations WHERE key = ?", (key,))
                        logger.info(f"缓存过期已删除: {explanation_type} - {content[:30]}...")
        
        return None
    
    def set(self, content: str, explanation_type: str, explanation: Dict):
        """设置缓存"""
        key = self._generate_cache_key(content, explanation_type)
        content_json = json.dumps(explanation, ensure_ascii=False)
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO explanations (key, content, type)
                    VALUES (?, ?, ?)
                """, (key, content_json, explanation_type))
        
        logger.info(f"缓存已保存: {explanation_type} - {content[:30]}...")
    
    def cleanup_expired(self):
        """清理过期缓存"""
        cutoff_time = datetime.now() - timedelta(hours=self.ttl_hours)
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM explanations 
                    WHERE created_at < ?
                """, (cutoff_time.isoformat(),))
                
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    logger.info(f"清理了 {deleted_count} 个过期缓存项")
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            # 总缓存数量
            cursor = conn.execute("SELECT COUNT(*) FROM explanations")
            total_count = cursor.fetchone()[0]
            
            # 按类型统计
            cursor = conn.execute("""
                SELECT type, COUNT(*), AVG(hit_count) 
                FROM explanations 
                GROUP BY type
            """)
            type_stats = {}
            for type_name, count, avg_hits in cursor.fetchall():
                type_stats[type_name] = {
                    'count': count,
                    'avg_hits': round(avg_hits or 0, 2)
                }
            
            # 缓存命中率（最近的记录）
            cursor = conn.execute("""
                SELECT AVG(hit_count) FROM explanations 
                WHERE created_at > datetime('now', '-7 days')
            """)
            recent_avg_hits = cursor.fetchone()[0] or 0
            
            return {
                'total_cached': total_count,
                'by_type': type_stats,
                'recent_avg_hits': round(recent_avg_hits, 2),
                'cache_size_mb': self._get_db_size_mb()
            }
    
    def _get_db_size_mb(self) -> float:
        """获取数据库文件大小（MB）"""
        try:
            size_bytes = self.db_path.stat().st_size
            return round(size_bytes / (1024 * 1024), 2)
        except:
            return 0.0


class AIExplainerManager:
    """AI解释管理器 - 整合API调用和缓存"""
    
    def __init__(self, api_key: str = None, cache_dir: str = "data"):
        self.api_client = DeepseekAPIClient(api_key)
        self.cache = AIExplanationCache(cache_dir)
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # 定期清理过期缓存
        self._schedule_cache_cleanup()
    
    def explain_word(self, word: str, context: str = None) -> Dict:
        """获取单词解释（优先使用缓存）"""
        # 先检查缓存
        cached_result = self.cache.get(word, "word")
        if cached_result:
            return cached_result
        
        try:
            # 调用API获取解释
            result = self.api_client.explain_word(word, context)
            
            # 保存到缓存
            self.cache.set(word, "word", result)
            
            return result
        except Exception as e:
            logger.error(f"获取单词解释失败: {word} - {e}")
            # 返回基本格式，避免程序崩溃
            return {
                'word': word,
                'meanings': [f"无法获取解释: {str(e)}"],
                'examples': [],
                'synonyms': [],
                'pronunciation': '',
                'word_type': ''
            }
    
    def explain_sentence(self, sentence: str) -> Dict:
        """获取句子解释（优先使用缓存）"""
        # 先检查缓存
        cached_result = self.cache.get(sentence, "sentence")
        if cached_result:
            return cached_result
        
        try:
            # 调用API获取解释
            result = self.api_client.explain_sentence(sentence)
            
            # 保存到缓存
            self.cache.set(sentence, "sentence", result)
            
            return result
        except Exception as e:
            logger.error(f"获取句子解释失败: {sentence[:50]}... - {e}")
            return {
                'sentence': sentence,
                'translation': f"无法获取翻译: {str(e)}",
                'grammar_points': [],
                'key_words': [],
                'difficulty_level': 3
            }
    
    def batch_explain_words(self, words: List[str]) -> Dict[str, Dict]:
        """批量获取单词解释"""
        results = {}
        
        # 使用线程池并发处理
        future_to_word = {
            self.executor.submit(self.explain_word, word): word 
            for word in words
        }
        
        for future in future_to_word:
            word = future_to_word[future]
            try:
                result = future.result(timeout=60)
                results[word] = result
            except Exception as e:
                logger.error(f"批量处理单词失败: {word} - {e}")
                results[word] = {
                    'word': word,
                    'meanings': [f"处理失败: {str(e)}"],
                    'examples': [],
                    'synonyms': [],
                    'pronunciation': '',
                    'word_type': ''
                }
        
        return results
    
    def get_cache_statistics(self) -> Dict:
        """获取缓存统计信息"""
        return self.cache.get_cache_stats()
    
    def _schedule_cache_cleanup(self):
        """定期清理缓存的后台任务"""
        def cleanup_task():
            while True:
                try:
                    time.sleep(3600)  # 每小时清理一次
                    self.cache.cleanup_expired()
                except Exception as e:
                    logger.error(f"缓存清理任务失败: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
    
    def preload_common_words(self, words: List[str]):
        """预加载常用词汇"""
        def preload_task():
            logger.info(f"开始预加载 {len(words)} 个常用词汇...")
            for word in words:
                if not self.cache.get(word, "word"):
                    try:
                        self.explain_word(word)
                        time.sleep(0.5)  # 避免API限流
                    except Exception as e:
                        logger.warning(f"预加载单词失败: {word} - {e}")
            logger.info("常用词汇预加载完成")
        
        preload_thread = threading.Thread(target=preload_task, daemon=True)
        preload_thread.start()


# 单例模式的全局AI解释器
_ai_explainer = None

def get_ai_explainer(api_key: str = None) -> AIExplainerManager:
    """获取全局AI解释器实例"""
    global _ai_explainer
    if _ai_explainer is None:
        _ai_explainer = AIExplainerManager(api_key)
    return _ai_explainer


if __name__ == "__main__":
    # 测试AI解释功能
    explainer = AIExplainerManager()
    
    print("=== AI解释模块测试 ===")
    
    # 测试单词解释
    word_result = explainer.explain_word("apple")
    print(f"\n单词解释测试:")
    print(f"单词: {word_result['word']}")
    print(f"含义: {word_result['meanings']}")
    print(f"例句: {word_result['examples']}")
    
    # 测试句子解释
    sentence_result = explainer.explain_sentence("The quick brown fox jumps over the lazy dog.")
    print(f"\n句子解释测试:")
    print(f"句子: {sentence_result['sentence']}")
    print(f"翻译: {sentence_result['translation']}")
    print(f"语法点: {sentence_result['grammar_points']}")
    
    # 测试缓存统计
    cache_stats = explainer.get_cache_statistics()
    print(f"\n缓存统计: {cache_stats}")
    
    # 测试批量处理
    batch_words = ["hello", "world", "python"]
    batch_results = explainer.batch_explain_words(batch_words)
    print(f"\n批量处理结果: {len(batch_results)} 个单词")