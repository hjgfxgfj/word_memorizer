#!/usr/bin/env python3
"""
Core Logic Module for Word Memorizer - Enhanced Version
精简版
"""

import json
import csv
import random
import heapq
import os
import logging
import uuid
from collections import deque, defaultdict
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 复习参数配置类
@dataclass
class ReviewParameters:
    initial_easiness: float = 2.5  # 初始记忆难度系数
    min_easiness: float = 1.3      # 最小记忆难度系数
    perfect_score: int = 5         # 最高评分
    min_quality: int = 0           # 最低评分
    interval_modifier: float = 1.0 # 间隔调整系数
    penalty_factor: float = 0.2    # 错误惩罚系数
    bonus_factor: float = 0.1      # 连续正确奖励系数
    consecutive_bonus: int = 3     # 连续正确奖励阈值

# 单词项目数据类
@dataclass
class WordItem:
    word: str  # 单词
    meaning: str  # 释义
    pronunciation: str = ""  # 发音
    difficulty: int = 1  # 难度等级 (1-5)
    review_count: int = 0  # 复习次数
    correct_count: int = 0  # 正确次数
    consecutive_correct: int = 0  # 连续正确次数
    last_review: Optional[str] = None  # 上次复习时间
    next_review: Optional[str] = None  # 下次复习时间
    easiness_factor: float = 2.5  # 记忆难度因子
    interval: int = 1  # 复习间隔天数
    tags: List[str] = field(default_factory=list)  # 标签
    examples: List[str] = field(default_factory=list)  # 例句
    synonyms: List[str] = field(default_factory=list)  # 同义词
    antonyms: List[str] = field(default_factory=list)  # 反义词
    word_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # 唯一ID
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())  # 创建时间
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())  # 更新时间
    
    def __post_init__(self):
        """初始化后验证和设置默认值"""
        if not self.word or not self.meaning:
            raise ValueError("单词和释义不能为空")
        if self.difficulty < 1 or self.difficulty > 5:
            raise ValueError("难度等级必须在1-5之间")
        if self.last_review is None:
            self.last_review = datetime.now().isoformat()
        if self.next_review is None:
            self.next_review = datetime.now().isoformat()
        if self.easiness_factor < 1.3:
            self.easiness_factor = 1.3
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """将对象转换为字典"""
        return asdict(self)

# 复习调度器类
class ReviewScheduler:
    def __init__(self, params: ReviewParameters = ReviewParameters()):
        self.words_queue = deque()  # 当前复习队列
        self.review_heap = []  # 基于下次复习时间的堆
        self.params = params  # 复习参数配置
        self.session_history = []  # 复习历史记录

    def calculate_next_review(self, item: WordItem, quality: int) -> Tuple[int, float]:
        """计算下次复习时间和新的记忆难度因子"""
        # 验证质量评分范围
        if quality < self.params.min_quality or quality > self.params.perfect_score:
            raise ValueError(f"质量评分必须在{self.params.min_quality}-{self.params.perfect_score}之间")
        
        q_diff = self.params.perfect_score - quality
        
        # 处理回答错误或质量低的情况
        if quality < 3:
            new_interval = max(1, int(self.params.interval_modifier))
            penalty = self.params.penalty_factor * (3 - quality)
            new_ef = max(self.params.min_easiness, item.easiness_factor - penalty)
            item.consecutive_correct = 0
        # 处理回答正确的情况
        else:
            item.consecutive_correct += 1
            consecutive_bonus = 1.0
            # 连续正确奖励
            if item.consecutive_correct >= self.params.consecutive_bonus:
                consecutive_bonus += self.params.bonus_factor
            
            # 根据当前间隔确定新间隔
            if item.interval <= 1:
                new_interval = 6
            elif item.interval == 6:
                new_interval = 14
            else:
                new_interval = max(1, int(item.interval * item.easiness_factor * consecutive_bonus))
            
            # 更新记忆难度因子
            ef_change = (0.1 - q_diff * (0.08 + q_diff * 0.02))
            new_ef = max(self.params.min_easiness, item.easiness_factor + ef_change)
        
        # 应用间隔调整系数
        new_interval = int(new_interval * self.params.interval_modifier)
        
        # 记录决策日志
        decision_log = {
            'timestamp': datetime.now().isoformat(),
            'word_id': item.word_id,
            'quality': quality,
            'old_interval': item.interval,
            'new_interval': new_interval,
            'old_ef': item.easiness_factor,
            'new_ef': new_ef,
            'consecutive': item.consecutive_correct
        }
        self.session_history.append(decision_log)
        
        return new_interval, new_ef
    
    def update_item_after_review(self, item: WordItem, is_correct: bool, quality: int = None):
        """更新单词复习后的状态"""
        # 确定质量评分
        if quality is None:
            quality = self.params.perfect_score if is_correct else self.params.min_quality
        if quality < self.params.min_quality or quality > self.params.perfect_score:
            quality = self.params.perfect_score if is_correct else self.params.min_quality
        
        # 更新复习统计
        item.review_count += 1
        if is_correct:
            item.correct_count += 1
        
        # 计算新的复习间隔和记忆难度
        new_interval, new_ef = self.calculate_next_review(item, quality)
        item.interval = new_interval
        item.easiness_factor = new_ef
        item.last_review = datetime.now().isoformat()
        next_review_date = datetime.now() + timedelta(days=new_interval)
        item.next_review = next_review_date.isoformat()
        item.updated_at = datetime.now().isoformat()
        
        # 添加到复习堆
        heapq.heappush(self.review_heap, (next_review_date.timestamp(), item))
        
        # 记录复习事件
        review_event = {
            'word': item.word,
            'word_id': item.word_id,
            'timestamp': item.last_review,
            'correct': is_correct,
            'quality': quality,
            'next_review': item.next_review,
            'interval': new_interval,
            'easiness': new_ef
        }
        self.session_history.append(review_event)
    
    def get_due_items(self, limit: int = 50) -> List[WordItem]:
        """获取到期的复习项目"""
        due_items = []
        current_time = datetime.now().timestamp()
        
        # 从堆中提取到期项目
        while self.review_heap and self.review_heap[0][0] <= current_time and len(due_items) < limit:
            _, item = heapq.heappop(self.review_heap)
            due_items.append(item)
        return due_items
    
    def shuffle_queue(self, method: str = "random"):
        """对复习队列进行排序或洗牌"""
        if not self.words_queue:
            return
            
        queue_list = list(self.words_queue)
        # 随机洗牌
        if method == "random":
            random.shuffle(queue_list)
        # 按难度排序
        elif method == "difficulty":
            queue_list.sort(key=lambda x: x.difficulty, reverse=True)
        # 按正确率排序
        elif method == "performance":
            queue_list.sort(key=lambda x: x.correct_count / x.review_count if x.review_count > 0 else 0)
        # 按间隔排序
        elif method == "interval":
            queue_list.sort(key=lambda x: x.interval)
        self.words_queue = deque(queue_list)
    
    def clear_history(self):
        """清除当前会话历史"""
        self.session_history = []
    
    def get_review_history(self) -> List[Dict]:
        """获取复习历史记录"""
        return self.session_history

# 数据管理类
class DataManager:
    def __init__(self, data_dir: str = "data", backup_count: int = 5):
        self.data_dir = Path(data_dir)  # 数据目录
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.backup_count = backup_count  # 备份保留数量
        self.words: Dict[str, WordItem] = {}  # 单词字典（按单词索引）
        self.word_id_index: Dict[str, WordItem] = {}  # 单词字典（按ID索引）
        self.progress_file = self.data_dir / "progress.json"  # 进度文件
        self.backup_dir = self.data_dir / "backups"  # 备份目录
        self.backup_dir.mkdir(exist_ok=True)
        self.stats_file = self.data_dir / "statistics.json"  # 统计文件
        self.import_history_file = self.data_dir / "import_history.csv"  # 导入历史文件
        
    def _create_backup(self, file_path: Path):
        """创建文件备份"""
        if not file_path.exists():
            return
        # 清理旧备份
        backups = sorted(self.backup_dir.glob(f"{file_path.stem}_backup_*"), 
                         key=os.path.getmtime, reverse=True)
        for old_backup in backups[self.backup_count - 1:]:
            old_backup.unlink()
        # 创建新备份
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        with open(file_path, 'rb') as src, open(backup_file, 'wb') as dst:
            dst.write(src.read())
    
    def _validate_word_data(self, row: Dict) -> bool:
        """验证单词数据有效性"""
        required_fields = ['word', 'meaning']
        for field in required_fields:
            if field not in row or not row[field].strip():
                return False
        return True
    
    def load_words_from_csv(self, csv_file: str, source: str = "unknown") -> int:
        """从CSV文件加载单词"""
        csv_path = self.data_dir / csv_file
        if not csv_path.exists():
            logger.warning(f"CSV文件不存在: {csv_path}")
            return 0
            
        count = 0
        new_words = 0
        updated_words = 0
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, 1):
                    # 验证数据
                    if not self._validate_word_data(row):
                        logger.warning(f"第{row_num}行数据不完整，跳过")
                        continue
                    
                    word = row['word'].strip()
                    meaning = row['meaning'].strip()
                    
                    # 更新已存在的单词
                    if word in self.words:
                        existing = self.words[word]
                        existing.meaning = meaning
                        existing.pronunciation = row.get('pronunciation', existing.pronunciation)
                        existing.difficulty = int(row.get('difficulty', existing.difficulty))
                        existing.tags = row.get('tags', '').split(',') if 'tags' in row else existing.tags
                        existing.updated_at = datetime.now().isoformat()
                        updated_words += 1
                        continue
                    
                    # 创建新单词项
                    word_item = WordItem(
                        word=word,
                        meaning=meaning,
                        pronunciation=row.get('pronunciation', ''),
                        difficulty=int(row.get('difficulty', 1)),
                        tags=row.get('tags', '').split(',') if 'tags' in row else []
                    )
                    
                    # 处理额外字段
                    if 'examples' in row:
                        examples = [ex.strip() for ex in row['examples'].split(';') if ex.strip()]
                        word_item.examples = examples
                    if 'synonyms' in row:
                        synonyms = [syn.strip() for syn in row['synonyms'].split(',') if syn.strip()]
                        word_item.synonyms = synonyms
                    if 'antonyms' in row:
                        antonyms = [ant.strip() for ant in row['antonyms'].split(',') if ant.strip()]
                        word_item.antonyms = antonyms
                    
                    # 添加到字典
                    self.words[word] = word_item
                    self.word_id_index[word_item.word_id] = word_item
                    count += 1
                    new_words += 1
            
            # 记录导入事件
            self._record_import_event(csv_file, source, new_words, updated_words)
            logger.info(f"成功导入 {count} 个单词 (新增: {new_words}, 更新: {updated_words})")
            return count
        except Exception as e:
            logger.error(f"加载CSV文件失败: {e}")
            return 0
    
    def _record_import_event(self, filename: str, source: str, new_words: int, updated_words: int):
        """记录导入事件到CSV"""
        if not self.import_history_file.exists():
            with open(self.import_history_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'filename', 'source', 'new_words', 'updated_words', 'total_words'])
        
        # 写入新记录
        with open(self.import_history_file, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                filename,
                source,
                new_words,
                updated_words,
                len(self.words)
            ])
    
    def save_progress(self) -> bool:
        """保存学习进度"""
        try:
            if self.progress_file.exists():
                self._create_backup(self.progress_file)
            
            # 构建进度数据
            progress_data = {
                'version': '2.0',
                'timestamp': datetime.now().isoformat(),
                'word_count': len(self.words),
                'words': {k: v.to_dict() for k, v in self.words.items()}
            }
            
            # 保存到文件
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
            self.save_statistics()
            logger.info(f"学习进度已保存 ({len(self.words)}个单词)")
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
            
            self.words.clear()
            self.word_id_index.clear()
            
            # 加载单词数据
            for word, word_data in data.get('words', {}).items():
                try:
                    word_item = WordItem(**word_data)
                    self.words[word] = word_item
                    self.word_id_index[word_item.word_id] = word_item
                except Exception as e:
                    logger.error(f"加载单词 '{word}' 失败: {e}")
            logger.info(f"成功加载进度: {len(self.words)}个单词")
            return True
        except Exception as e:
            logger.error(f"加载进度失败: {e}")
            return False
    
    def save_statistics(self):
        """保存统计数据"""
        stats = self.get_statistics()
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存统计信息失败: {e}")
    
    def get_statistics(self) -> Dict:
        """获取统计数据"""
        word_stats = self._calculate_item_stats(self.words.values())
        difficulty_stats = self._get_difficulty_stats()
        tag_stats = self._get_tag_stats()
        retention_rates = self._get_retention_rates()
        
        return {
            'words': {
                'total': len(self.words),
                'reviewed': word_stats['reviewed'],
                'unreviewed': len(self.words) - word_stats['reviewed'],
                'accuracy': word_stats['accuracy'],
                'avg_difficulty': word_stats['avg_difficulty'],
                'avg_interval': word_stats['avg_interval'],
                'avg_ef': word_stats['avg_ef']
            },
            'difficulty': difficulty_stats,
            'tags': tag_stats,
            'retention': retention_rates,
            'daily_progress': self._get_daily_progress(),
            'last_updated': datetime.now().isoformat()
        }
    
    def _calculate_item_stats(self, items) -> Dict:
        """计算单词项统计"""
        if not items:
            return {'reviewed': 0, 'accuracy': 0.0, 'avg_difficulty': 0.0, 'avg_interval': 0.0, 'avg_ef': 0.0}
            
        # 筛选已复习项目
        reviewed_items = [item for item in items if item.review_count > 0]
        total_reviews = sum(item.review_count for item in items)
        total_correct = sum(item.correct_count for item in items)
        total_interval = sum(item.interval for item in reviewed_items)
        total_ef = sum(item.easiness_factor for item in reviewed_items)
        
        # 计算各项指标
        accuracy = (total_correct / total_reviews * 100) if total_reviews > 0 else 0
        avg_difficulty = sum(item.difficulty for item in items) / len(items)
        avg_interval = total_interval / len(reviewed_items) if reviewed_items else 0
        avg_ef = total_ef / len(reviewed_items) if reviewed_items else 0
        
        return {
            'reviewed': len(reviewed_items),
            'unreviewed': len(items) - len(reviewed_items),
            'accuracy': round(accuracy, 2),
            'avg_difficulty': round(avg_difficulty, 2),
            'avg_interval': round(avg_interval, 2),
            'avg_ef': round(avg_ef, 2)
        }
    
    def _get_difficulty_stats(self) -> Dict[int, Dict]:
        """按难度分组统计"""
        difficulty_groups = defaultdict(list)
        for item in self.words.values():
            difficulty_groups[item.difficulty].append(item)
        
        stats = {}
        for level, items in difficulty_groups.items():
            level_stats = self._calculate_item_stats(items)
            level_stats['count'] = len(items)
            stats[level] = level_stats
        return stats
    
    def _get_tag_stats(self) -> Dict[str, Dict]:
        """按标签分组统计"""
        tag_groups = defaultdict(list)
        for item in self.words.values():
            for tag in item.tags:
                tag_groups[tag].append(item)
        
        stats = {}
        for tag, items in tag_groups.items():
            tag_stats = self._calculate_item_stats(items)
            tag_stats['count'] = len(items)
            stats[tag] = tag_stats
        return stats
    
    def _get_retention_rates(self) -> Dict[int, float]:
        """计算各间隔的记忆保留率"""
        interval_groups = defaultdict(lambda: {'correct': 0, 'total': 0})
        for item in self.words.values():
            if item.review_count > 0:
                interval = item.interval
                interval_groups[interval]['correct'] += item.correct_count
                interval_groups[interval]['total'] += item.review_count
        
        retention_rates = {}
        for interval, counts in sorted(interval_groups.items()):
            if counts['total'] > 0:
                rate = counts['correct'] / counts['total'] * 100
                retention_rates[interval] = round(rate, 2)
        return retention_rates
    
    def _get_daily_progress(self, days: int = 30) -> List[Dict]:
        """获取每日进度"""
        daily_data = defaultdict(lambda: {'words': 0, 'correct': 0, 'total': 0})
        for word_item in self.words.values():
            if word_item.last_review:
                date = datetime.fromisoformat(word_item.last_review).date()
                daily_data[date.isoformat()]['words'] += 1
        
        # 生成最近days天的数据
        progress_list = []
        today = datetime.now().date()
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.isoformat()
            data = daily_data.get(date_str, {'words': 0, 'correct': 0, 'total': 0})
            accuracy = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            progress_list.append({
                'date': date_str,
                'words': data['words'],
                'correct': data['correct'],
                'total': data['total'],
                'accuracy': accuracy
            })
        return sorted(progress_list, key=lambda x: x['date'])
    
    def get_word_by_id(self, word_id: str) -> Optional[WordItem]:
        """通过ID获取单词项"""
        return self.word_id_index.get(word_id)
    
    def update_word_item(self, word_id: str, **kwargs) -> bool:
        """更新单词项属性"""
        item = self.word_id_index.get(word_id)
        if not item:
            return False
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)
        item.updated_at = datetime.now().isoformat()
        return True
    
    def add_custom_word(self, word: str, meaning: str, **kwargs) -> bool:
        """添加自定义单词"""
        if word in self.words:
            return False
        word_item = WordItem(word=word, meaning=meaning, **kwargs)
        self.words[word] = word_item
        self.word_id_index[word_item.word_id] = word_item
        return True

# 核心记忆系统类
class MemorizerCore:
    def __init__(self, data_dir: str = "data", review_params: ReviewParameters = None):
        self.data_manager = DataManager(data_dir)  # 数据管理器
        self.review_params = review_params or ReviewParameters()  # 复习参数
        self.scheduler = ReviewScheduler(self.review_params)  # 复习调度器
        # 当前会话信息
        self.current_session = {
            'session_id': str(uuid.uuid4()),
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'words_reviewed': 0,
            'correct_answers': 0,
            'total_answers': 0,
            'words': []
        }
        # 用户偏好设置
        self.user_preferences = {
            'new_words_per_day': 20,
            'review_limit': 100,
            'shuffle_method': 'random',
            'difficulty_weight': 1.0
        }
    
    def initialize(self) -> bool:
        """初始化记忆系统"""
        # 尝试加载进度，失败则加载示例词库
        if not self.data_manager.load_progress():
            if not self.data_manager.load_words_from_csv("words_cet6.csv", "system"):
                logger.warning("初始化示例词库失败")
        # 初始化复习队列
        self._initialize_review_queues()
        logger.info(f"记忆系统初始化完成，共加载 {len(self.data_manager.words)} 个单词")
        return True
    
    def _initialize_review_queues(self):
        """初始化复习队列"""
        self.scheduler.words_queue.clear()
        self.scheduler.review_heap = []
        current_time = datetime.now()
        due_items = []
        
        # 分离到期项目和未到期项目
        for word in self.data_manager.words.values():
            next_review = datetime.fromisoformat(word.next_review)
            if next_review <= current_time:
                due_items.append(word)
            else:
                heapq.heappush(self.scheduler.review_heap, (next_review.timestamp(), word))
        
        # 根据用户偏好排序
        if self.user_preferences['shuffle_method'] == 'difficulty':
            due_items.sort(key=lambda x: x.difficulty * self.user_preferences['difficulty_weight'], reverse=True)
        elif self.user_preferences['shuffle_method'] == 'performance':
            due_items.sort(key=lambda x: x.correct_count / x.review_count if x.review_count > 0 else 0)
        else:
            random.shuffle(due_items)
        
        # 限制复习数量
        due_items = due_items[:self.user_preferences['review_limit']]
        self.scheduler.words_queue = deque(due_items)
    
    def get_next_review_item(self, *args, **kwargs) -> Optional[WordItem]:
        """获取下一个复习项"""
        if self.scheduler.words_queue:
            item = self.scheduler.words_queue.popleft()
            self.current_session['words'].append(item.word_id)
            return item
        return None
    
    def submit_answer(self, item: WordItem, is_correct: bool, quality: int = None):
        """提交答案并更新状态"""
        self.scheduler.update_item_after_review(item, is_correct, quality)
        self.current_session['total_answers'] += 1
        if is_correct:
            self.current_session['correct_answers'] += 1
        self.current_session['words_reviewed'] += 1
        self.data_manager.save_progress()
    
    def end_session(self):
        """结束当前会话"""
        self.current_session['end_time'] = datetime.now().isoformat()
        self.scheduler.clear_history()
    
    def get_session_stats(self) -> Dict:
        """获取会话统计信息"""
        if self.current_session['end_time']:
            session_time = datetime.fromisoformat(self.current_session['end_time']) - \
                          datetime.fromisoformat(self.current_session['start_time'])
        else:
            session_time = datetime.now() - datetime.fromisoformat(self.current_session['start_time'])
        
        # 计算准确率
        accuracy = 0
        if self.current_session['total_answers'] > 0:
            accuracy = self.current_session['correct_answers'] / self.current_session['total_answers'] * 100
        
        return {
            'session_id': self.current_session['session_id'],
            'start_time': self.current_session['start_time'],
            'end_time': self.current_session['end_time'],
            'session_duration': str(session_time).split('.')[0],
            'words_reviewed': self.current_session['words_reviewed'],
            'total_answers': self.current_session['total_answers'],
            'accuracy': round(accuracy, 2),
            'remaining_words': len(self.scheduler.words_queue)
        }
    
    def get_overall_stats(self) -> Dict:
        """获取整体统计信息"""
        return self.data_manager.get_statistics()
    
    def import_custom_wordbook(self, file_path: str, file_type: str, source: str = "user") -> bool:
        """导入自定义词书"""
        try:
            if file_type.lower() == 'csv':
                count = self.data_manager.load_words_from_csv(file_path, source)
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
    
    def add_custom_word(self, word: str, meaning: str, **kwargs) -> bool:
        """添加自定义单词"""
        success = self.data_manager.add_custom_word(word, meaning, **kwargs)
        if success:
            self._initialize_review_queues()
            self.data_manager.save_progress()
        return success
    
    def update_user_preferences(self, **prefs):
        """更新用户偏好设置"""
        valid_keys = ['new_words_per_day', 'review_limit', 'shuffle_method', 'difficulty_weight']
        for key, value in prefs.items():
            if key in valid_keys:
                self.user_preferences[key] = value
        self._initialize_review_queues()

# 测试代码
if __name__ == "__main__":
    print("=== 单词记忆系统增强版测试 ===")
    core = MemorizerCore(data_dir="test_data")
    core.initialize()
    
    print("\n系统统计信息:")
    stats = core.get_overall_stats()
    print(f"总单词数: {stats['words']['total']}")
    print(f"已复习: {stats['words']['reviewed']}")
    print(f"平均准确率: {stats['words']['accuracy']}%")
    
    print("\n模拟复习流程:")
    for i in range(5):
        item = core.get_next_review_item()
        if item:
            print(f"\n复习项目 {i+1}:")
            print(f"单词: {item.word} - {item.meaning}")
            is_correct = random.random() > 0.3
            core.submit_answer(item, is_correct)
            print(f"回答: {'正确' if is_correct else '错误'}")
        else:
            print("没有更多复习项目")
            break
    
    print("\n会话统计:")
    session_stats = core.get_session_stats()
    for key, value in session_stats.items():
        print(f"{key}: {value}")
    
    print("\n添加自定义单词:")
    success = core.add_custom_word("ephemeral", "短暂的，瞬息的", 
                                pronunciation="ɪˈfemərəl", 
                                difficulty=4,
                                tags=["literary", "advanced"])
    print("成功添加单词 'ephemeral'" if success else "添加单词失败")
    
    core.end_session()
    print("\n测试完成")
