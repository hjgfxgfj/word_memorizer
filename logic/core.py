#!/usr/bin/env python3
"""
Core Logic Module for Word Memorizer
单词记忆系统核心逻辑模块

This module handles:
- Word data management
- Review scheduling using simplified SM-2 algorithm
- Data persistence with JSON format
- Progress tracking and statistics
"""

import json
import csv
import random
import heapq
from collections import deque, Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WordItem:
    """单词数据结构"""
    word: str
    meaning: str
    pronunciation: str = ""
    difficulty: int = 1  # 1-5 难度等级
    review_count: int = 0
    correct_count: int = 0
    last_review: Optional[str] = None
    next_review: Optional[str] = None
    easiness_factor: float = 2.5  # SM-2算法易度因子
    interval: int = 1  # 复习间隔(天)
    
    def __post_init__(self):
        if self.last_review is None:
            self.last_review = datetime.now().isoformat()
        if self.next_review is None:
            self.next_review = datetime.now().isoformat()




class ReviewScheduler:
    """复习调度器 - 实现简化的SM-2算法"""
    
    def __init__(self):
        self.words_queue = deque()
        self.review_heap = []  # 按复习时间排序的堆
        
    def calculate_next_review(self, item: WordItem, 
                            quality: int) -> Tuple[int, float]:
        """
        计算下次复习时间和新的易度因子
        quality: 0-5 (0=完全错误, 5=完全正确)
        """
        if quality < 3:
            # 回答错误，重置间隔
            new_interval = 1
            new_ef = max(1.3, item.easiness_factor - 0.8 + 0.28 * quality - 0.02 * quality * quality)
        else:
            # 回答正确，增加间隔
            if item.interval == 1:
                new_interval = 6
            elif item.interval == 6:
                new_interval = 14
            else:
                new_interval = round(item.interval * item.easiness_factor)
            
            new_ef = item.easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            new_ef = max(1.3, new_ef)
        
        return new_interval, new_ef
    
    def update_item_after_review(self, item: WordItem, 
                               is_correct: bool, quality: int = None):
        """更新项目复习状态"""
        if quality is None:
            quality = 4 if is_correct else 1
            
        item.review_count += 1
        if is_correct:
            item.correct_count += 1
            
        new_interval, new_ef = self.calculate_next_review(item, quality)
        item.interval = new_interval
        item.easiness_factor = new_ef
        item.last_review = datetime.now().isoformat()
        
        next_review_date = datetime.now() + timedelta(days=new_interval)
        item.next_review = next_review_date.isoformat()
        
        # 添加到复习堆中
        heapq.heappush(self.review_heap, 
                      (next_review_date.timestamp(), item))
    
    def get_due_items(self) -> List[WordItem]:
        """获取到期需要复习的项目"""
        due_items = []
        current_time = datetime.now().timestamp()
        
        # 从堆中取出到期项目
        while self.review_heap and self.review_heap[0][0] <= current_time:
            _, item = heapq.heappop(self.review_heap)
            if isinstance(item, WordItem):
                due_items.append(item)
        
        return due_items
    
    def shuffle_queue(self):
        """随机打乱队列顺序"""
        queue_list = list(self.words_queue)
        random.shuffle(queue_list)
        self.words_queue = deque(queue_list)


class DataManager:
    """数据管理器 - 处理词汇的I/O操作"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.words: Dict[str, WordItem] = {}
        self.progress_file = self.data_dir / "progress.json"
        
    def load_words_from_csv(self, csv_file: str) -> int:
        """从CSV文件加载单词"""
        csv_path = self.data_dir / csv_file
        if not csv_path.exists():
            logger.warning(f"CSV文件不存在: {csv_path}")
            return 0
            
        count = 0
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    word_item = WordItem(
                        word=row['word'],
                        meaning=row['meaning'],
                        pronunciation=row.get('pronunciation', ''),
                        difficulty=int(row.get('difficulty', 1))
                    )
                    self.words[word_item.word] = word_item
                    count += 1
        except Exception as e:
            logger.error(f"加载CSV文件失败: {e}")
            
        logger.info(f"成功加载 {count} 个单词")
        return count
    
    
    def save_progress(self) -> bool:
        """保存学习进度"""
        try:
            progress_data = {
                'timestamp': datetime.now().isoformat(),
                'words': {k: asdict(v) for k, v in self.words.items()}
            }
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
                
            logger.info("学习进度已保存")
            return True
        except Exception as e:
            logger.error(f"保存进度失败: {e}")
            return False
    
    def load_progress(self) -> bool:
        """加载学习进度"""
        if not self.progress_file.exists():
            logger.info("进度文件不存在，使用默认数据")
            return False
            
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 恢复单词数据
            for word, word_data in data.get('words', {}).items():
                self.words[word] = WordItem(**word_data)
                
            logger.info(f"成功加载进度: {len(self.words)}个单词")
            return True
        except Exception as e:
            logger.error(f"加载进度失败: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """获取学习统计信息"""
        word_stats = self._calculate_item_stats(self.words.values())
        
        # 现在只有单词数据，句子数据暂时返回空的统计
        sentence_stats = {
            'reviewed': 0,
            'accuracy': 0.0,
            'avg_difficulty': 0.0
        }
        
        return {
            'words': {
                'total': len(self.words),
                'reviewed': word_stats['reviewed'],
                'accuracy': word_stats['accuracy'],
                'avg_difficulty': word_stats['avg_difficulty']
            },
            'sentences': {
                'total': 0,  # 暂时没有句子数据
                'reviewed': sentence_stats['reviewed'],
                'accuracy': sentence_stats['accuracy'],
                'avg_difficulty': sentence_stats['avg_difficulty']
            },
            'daily_progress': self._get_daily_progress()
        }
    
    def _calculate_item_stats(self, items) -> Dict:
        """计算项目统计信息"""
        if not items:
            return {'reviewed': 0, 'accuracy': 0.0, 'avg_difficulty': 0.0}
            
        reviewed_items = [item for item in items if item.review_count > 0]
        total_reviews = sum(item.review_count for item in items)
        total_correct = sum(item.correct_count for item in items)
        
        accuracy = (total_correct / total_reviews * 100) if total_reviews > 0 else 0
        avg_difficulty = sum(item.difficulty for item in items) / len(items)
        
        return {
            'reviewed': len(reviewed_items),
            'accuracy': round(accuracy, 2),
            'avg_difficulty': round(avg_difficulty, 2)
        }
    
    def _get_daily_progress(self) -> List[Dict]:
        """获取每日学习进度"""
        daily_data = defaultdict(lambda: {'words': 0, 'sentences': 0})
        
        # 统计单词复习记录
        for word_item in self.words.values():
            if word_item.last_review:
                date = datetime.fromisoformat(word_item.last_review).date()
                daily_data[date.isoformat()]['words'] += 1
        
        # TODO: 句子数据统计（暂时设为0）
        # 当添加句子功能时，在这里添加句子统计逻辑
        
        # 转换为列表格式
        progress_list = []
        for date_str, counts in sorted(daily_data.items()):
            progress_list.append({
                'date': date_str,
                'words': counts['words'],
                'sentences': counts['sentences']  # 添加句子统计
            })
        
        return progress_list[-30:]  # 返回最近30天的数据
    
    def get_error_prone_items(self, limit: int = 10) -> List[WordItem]:
        """获取容易出错的项目"""
        word_errors = [(item, self._calculate_error_rate(item)) 
                      for item in self.words.values() if item.review_count > 0]
        word_errors.sort(key=lambda x: x[1], reverse=True)
        error_items = [item for item, _ in word_errors[:limit]]
        
        return error_items
    
    def _calculate_error_rate(self, item: WordItem) -> float:
        """计算错误率"""
        if item.review_count == 0:
            return 0.0
        return (item.review_count - item.correct_count) / item.review_count


class MemorizerCore:
    """记忆系统核心类 - 整合所有功能"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_manager = DataManager(data_dir)
        self.scheduler = ReviewScheduler()
        self.current_session = {
            'start_time': datetime.now(),
            'words_reviewed': 0,
            'correct_answers': 0,
            'total_answers': 0
        }
    
    def initialize(self) -> bool:
        """初始化系统"""
        # 加载进度或创建示例数据
        if not self.data_manager.load_progress():
            self.data_manager.load_words_from_csv("words_cet6.csv")
        
        # 初始化复习队列
        self._initialize_review_queues()
        return True
    
    def _initialize_review_queues(self):
        """初始化复习队列"""
        # 添加到期的项目到队列
        current_time = datetime.now()
        
        for word in self.data_manager.words.values():
            next_review = datetime.fromisoformat(word.next_review)
            if next_review <= current_time:
                self.scheduler.words_queue.append(word)
            else:
                heapq.heappush(self.scheduler.review_heap, 
                              (next_review.timestamp(), word))
        
        # 随机打乱队列
        self.scheduler.shuffle_queue()
    
    def get_next_review_item(self, item_type: str = "word") -> Optional[WordItem]:
        """获取下一个复习项目"""
        if self.scheduler.words_queue:
            return self.scheduler.words_queue.popleft()
        
        return None
    
    def submit_answer(self, item: WordItem, 
                     is_correct: bool, quality: int = None):
        """提交答案并更新学习状态"""
        self.scheduler.update_item_after_review(item, is_correct, quality)
        
        # 更新会话统计
        self.current_session['total_answers'] += 1
        if is_correct:
            self.current_session['correct_answers'] += 1
        
        self.current_session['words_reviewed'] += 1
        
        # 自动保存进度
        self.data_manager.save_progress()
    
    def get_session_stats(self) -> Dict:
        """获取当前会话统计"""
        session_time = datetime.now() - self.current_session['start_time']
        accuracy = 0
        if self.current_session['total_answers'] > 0:
            accuracy = self.current_session['correct_answers'] / self.current_session['total_answers'] * 100
        
        return {
            'session_time': str(session_time).split('.')[0],  # 去掉微秒
            'words_reviewed': self.current_session['words_reviewed'],
            'total_reviewed': self.current_session['total_answers'],
            'accuracy': round(accuracy, 2),
            'remaining_words': len(self.scheduler.words_queue)
        }
    
    def get_overall_stats(self) -> Dict:
        """获取总体统计信息"""
        return self.data_manager.get_statistics()
    
    def import_custom_wordbook(self, file_path: str, file_type: str) -> bool:
        """导入自定义词书"""
        try:
            if file_type.lower() == 'csv':
                count = self.data_manager.load_words_from_csv(file_path)
            else:
                logger.error(f"不支持的文件类型: {file_type}")
                return False
            
            if count > 0:
                self._initialize_review_queues()
                self.data_manager.save_progress()
                return True
            return False
        except Exception as e:
            logger.error(f"导入词书失败: {e}")
            return False


if __name__ == "__main__":
    # 测试核心功能
    core = MemorizerCore()
    core.initialize()
    
    print("=== 词汇记忆系统测试 ===")
    print(f"总体统计: {core.get_overall_stats()}")
    print(f"会话统计: {core.get_session_stats()}")
    
    # 模拟复习流程
    for i in range(5):
        item = core.get_next_review_item()
        if item:
            print(f"\n复习项目 {i+1}:")
            if isinstance(item, WordItem):
                print(f"单词: {item.word} - {item.meaning}")
            else:
                print(f"句子: {item.sentence[:50]}...")
            
            # 模拟用户回答
            is_correct = random.choice([True, False])
            core.submit_answer(item, is_correct)
            print(f"回答: {'正确' if is_correct else '错误'}")
        else:
            break
    
    print(f"\n最终会话统计: {core.get_session_stats()}")