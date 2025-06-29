#!/usr/bin/env python3
"""
Audio Listen Engine for Word & Sentence Memorizer
音频听写引擎 - 处理TTS生成、音频播放和录音识别

This module handles:
- Text-to-Speech using edge-tts (offline)
- Audio playback with sounddevice
- Audio recording and speech recognition
- Audio caching system
- Volume control and audio format handling
"""

import asyncio
import io
import os
import sqlite3
import threading
import time
import wave
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Callable
import tempfile
import json

# Third-party imports
import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import edge_tts
# 移除语音识别依赖，专注于TTS和手动输入功能
from pydub import AudioSegment
from pydub.playback import play
import pygame

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TTSEngine:
    """Text-to-Speech引擎，使用edge-tts实现离线TTS"""
    
    def __init__(self):
        self.voice_map = {
            'en-US': 'en-US-AriaNeural',
            'en-GB': 'en-GB-SoniaNeural', 
            'zh-CN': 'zh-CN-XiaoxiaoNeural'
        }
        self.default_voice = 'en-US-AriaNeural'
        self.rate = '+0%'  # 语速
        self.volume = '+0%'  # 音量
        self.pitch = '+0Hz'  # 音调
    
    async def text_to_audio_async(self, text: str, language: str = 'en-US') -> bytes:
        """异步将文本转换为音频数据"""
        voice = self.voice_map.get(language, self.default_voice)
        
        # 创建TTS通信对象
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch
        )
        
        # 生成音频数据
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        return audio_data
    
    def text_to_audio(self, text: str, language: str = 'en-US') -> bytes:
        """同步将文本转换为音频数据"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.text_to_audio_async(text, language))
    
    def save_audio_file(self, text: str, output_path: str, language: str = 'en-US') -> bool:
        """将文本保存为音频文件"""
        try:
            audio_data = self.text_to_audio(text, language)
            
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"音频文件已保存: {output_path}")
            return True
        except Exception as e:
            logger.error(f"保存音频文件失败: {e}")
            return False
    
    def set_voice_parameters(self, rate: str = None, volume: str = None, pitch: str = None):
        """设置语音参数"""
        if rate:
            self.rate = rate
        if volume:
            self.volume = volume
        if pitch:
            self.pitch = pitch
    
    def get_available_voices(self) -> List[Dict]:
        """获取可用语音列表"""
        async def get_voices():
            return await edge_tts.list_voices()
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        voices = loop.run_until_complete(get_voices())
        return [{"name": v["Name"], "lang": v["Locale"], "gender": v["Gender"]} for v in voices]


class AudioCache:
    """音频缓存系统"""
    
    def __init__(self, cache_dir: str = "data"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.db_path = self.cache_dir / "audio_cache.db"
        self.audio_dir = self.cache_dir / "audio"
        self.audio_dir.mkdir(exist_ok=True)
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """初始化缓存数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audio_cache (
                    text_hash TEXT PRIMARY KEY,
                    text_content TEXT NOT NULL,
                    language TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    file_size INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_language ON audio_cache(language)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON audio_cache(created_at)
            """)
    
    def _generate_hash(self, text: str, language: str) -> str:
        """生成文本和语言的哈希值"""
        combined = f"{language}:{text.strip().lower()}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def get_audio_path(self, text: str, language: str = 'en-US') -> Optional[str]:
        """获取缓存的音频文件路径"""
        text_hash = self._generate_hash(text, language)
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT file_path FROM audio_cache 
                    WHERE text_hash = ? AND language = ?
                """, (text_hash, language))
                
                row = cursor.fetchone()
                if row:
                    file_path = row[0]
                    full_path = self.cache_dir / file_path
                    
                    if full_path.exists():
                        # 更新访问记录
                        conn.execute("""
                            UPDATE audio_cache 
                            SET accessed_at = CURRENT_TIMESTAMP, access_count = access_count + 1
                            WHERE text_hash = ?
                        """, (text_hash,))
                        
                        logger.info(f"音频缓存命中: {text[:30]}...")
                        return str(full_path)
                    else:
                        # 文件不存在，删除缓存记录
                        conn.execute("DELETE FROM audio_cache WHERE text_hash = ?", (text_hash,))
        
        return None
    
    def cache_audio(self, text: str, audio_data: bytes, language: str = 'en-US') -> str:
        """缓存音频数据并返回文件路径"""
        text_hash = self._generate_hash(text, language)
        filename = f"{text_hash}.mp3"
        file_path = self.audio_dir / filename
        
        with self.lock:
            # 保存音频文件
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            file_size = len(audio_data)
            relative_path = f"audio/{filename}"
            
            # 保存到数据库
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO audio_cache 
                    (text_hash, text_content, language, file_path, file_size)
                    VALUES (?, ?, ?, ?, ?)
                """, (text_hash, text, language, relative_path, file_size))
        
        logger.info(f"音频已缓存: {text[:30]}... -> {filename}")
        return str(file_path)
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*), SUM(file_size) FROM audio_cache")
            count, total_size = cursor.fetchone()
            
            cursor = conn.execute("""
                SELECT language, COUNT(*), SUM(file_size) 
                FROM audio_cache 
                GROUP BY language
            """)
            lang_stats = {}
            for lang, lang_count, lang_size in cursor.fetchall():
                lang_stats[lang] = {
                    'count': lang_count,
                    'size_mb': round((lang_size or 0) / (1024 * 1024), 2)
                }
            
            return {
                'total_files': count or 0,
                'total_size_mb': round((total_size or 0) / (1024 * 1024), 2),
                'by_language': lang_stats
            }
    
    def cleanup_old_cache(self, days: int = 30):
        """清理旧的缓存文件"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT file_path FROM audio_cache 
                    WHERE accessed_at < ?
                """, (cutoff_date.isoformat(),))
                
                old_files = cursor.fetchall()
                
                for (file_path,) in old_files:
                    full_path = self.cache_dir / file_path
                    if full_path.exists():
                        full_path.unlink()
                
                conn.execute("""
                    DELETE FROM audio_cache 
                    WHERE accessed_at < ?
                """, (cutoff_date.isoformat(),))
                
                logger.info(f"清理了 {len(old_files)} 个旧音频文件")


class AudioPlayer:
    """音频播放器"""
    
    def __init__(self):
        pygame.mixer.init()
        self.current_audio = None
        self.is_playing = False
        self.volume = 0.7
        pygame.mixer.music.set_volume(self.volume)
    
    def play_audio_file(self, file_path: str, callback: Callable = None) -> bool:
        """播放音频文件"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"音频文件不存在: {file_path}")
                return False
            
            self.stop_audio()
            
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.is_playing = True
            
            logger.info(f"开始播放音频: {os.path.basename(file_path)}")
            
            # 如果有回调函数，启动监听线程
            if callback:
                def monitor_playback():
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    self.is_playing = False
                    callback()
                
                threading.Thread(target=monitor_playback, daemon=True).start()
            
            return True
        except Exception as e:
            logger.error(f"播放音频失败: {e}")
            self.is_playing = False
            return False
    
    def play_audio_data(self, audio_data: bytes, callback: Callable = None) -> bool:
        """播放音频数据"""
        try:
            # 将音频数据写入临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            result = self.play_audio_file(temp_path, callback)
            
            # 播放完成后删除临时文件
            def cleanup():
                time.sleep(1)  # 等待播放完成
                try:
                    os.unlink(temp_path)
                except:
                    pass
            
            threading.Thread(target=cleanup, daemon=True).start()
            
            return result
        except Exception as e:
            logger.error(f"播放音频数据失败: {e}")
            return False
    
    def stop_audio(self):
        """停止音频播放"""
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
            logger.info("音频播放已停止")
    
    def pause_audio(self):
        """暂停音频播放"""
        if self.is_playing:
            pygame.mixer.music.pause()
            logger.info("音频播放已暂停")
    
    def resume_audio(self):
        """恢复音频播放"""
        pygame.mixer.music.unpause()
        logger.info("音频播放已恢复")
    
    def set_volume(self, volume: float):
        """设置音量 (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
        logger.info(f"音量已设置为: {self.volume:.1f}")
    
    def get_volume(self) -> float:
        """获取当前音量"""
        return self.volume
    
    def is_audio_playing(self) -> bool:
        """检查是否正在播放音频"""
        return self.is_playing and pygame.mixer.music.get_busy()


class AudioRecorder:
    """简化的音频录制器 - 仅支持手动输入模式"""
    
    def __init__(self):
        self.is_recording = False
        logger.info("音频录制器已初始化 - 手动输入模式")
    
    def start_recording(self) -> bool:
        """模拟开始录音 - 实际只是状态切换"""
        if self.is_recording:
            logger.warning("录音已经在进行中")
            return False
        
        self.is_recording = True
        logger.info("模拟录音开始 - 请手动输入文本")
        return True
    
    def stop_recording(self) -> Optional[str]:
        """模拟停止录音 - 返回提示信息"""
        if not self.is_recording:
            logger.warning("没有正在进行的录音")
            return None
        
        self.is_recording = False
        logger.info("模拟录音结束 - 请在文本框中手动输入")
        return "请手动输入听到的内容"
    
    def record_for_duration(self, duration: float) -> str:
        """模拟录制指定时长"""
        self.start_recording()
        time.sleep(0.5)  # 短暂延迟模拟录音过程
        self.stop_recording()
        return "请手动输入听到的内容"
    
    def recognize_speech(self, text_input: str = None) -> str:
        """直接返回手动输入的文本"""
        if text_input:
            logger.info(f"手动输入内容: {text_input}")
            return text_input
        else:
            return "请在文本框中输入内容"
    
    def get_audio_level(self) -> float:
        """返回模拟音量级别"""
        return 50.0  # 固定返回中等音量级别


class ListenEngine:
    """听写引擎 - 整合TTS、播放、录音和识别功能"""
    
    def __init__(self, cache_dir: str = "data"):
        self.tts_engine = TTSEngine()
        self.audio_cache = AudioCache(cache_dir)
        self.player = AudioPlayer()
        self.recorder = AudioRecorder()
        self.current_text = ""
        self.current_language = "en-US"
        self.playback_callback = None
    
    def play_text(self, text: str, language: str = 'en-US', callback: Callable = None) -> bool:
        """播放文本语音"""
        self.current_text = text
        self.current_language = language
        self.playback_callback = callback
        
        # 先检查缓存
        cached_path = self.audio_cache.get_audio_path(text, language)
        if cached_path:
            return self.player.play_audio_file(cached_path, callback)
        
        # 缓存不存在，生成音频
        try:
            audio_data = self.tts_engine.text_to_audio(text, language)
            cached_path = self.audio_cache.cache_audio(text, audio_data, language)
            return self.player.play_audio_file(cached_path, callback)
        except Exception as e:
            logger.error(f"播放文本失败: {e}")
            return False
    
    def replay_current(self) -> bool:
        """重播当前文本"""
        if self.current_text:
            return self.play_text(self.current_text, self.current_language, self.playback_callback)
        return False
    
    def start_dictation(self, duration: float = 10.0) -> bool:
        """开始听写录音"""
        return self.recorder.start_recording()
    
    def stop_dictation(self) -> Tuple[str, float]:
        """停止听写并返回提示信息"""
        result = self.recorder.stop_recording()
        if result is None:
            return "", 0.0
        
        # 获取模拟音量级别
        volume_level = self.recorder.get_audio_level()
        
        # 返回提示信息
        return result, volume_level
    
    def record_for_duration(self, duration: float) -> Tuple[str, float]:
        """模拟录制并返回提示"""
        result = self.recorder.record_for_duration(duration)
        volume_level = self.recorder.get_audio_level()
        
        return result, volume_level
    
    def compare_texts(self, original: str, recognized: str) -> Dict:
        """比较原文和识别文本"""
        # 简单的文本比较
        original_words = original.lower().split()
        recognized_words = recognized.lower().split()
        
        # 计算相似度
        if not original_words:
            similarity = 0.0
        else:
            correct_words = sum(1 for word in recognized_words if word in original_words)
            similarity = correct_words / len(original_words) * 100
        
        return {
            'original': original,
            'recognized': recognized,
            'similarity': round(similarity, 2),
            'is_correct': similarity >= 80.0,  # 80%以上认为正确
            'word_count': len(original_words),
            'recognized_count': len(recognized_words)
        }
    
    def set_tts_parameters(self, rate: str = None, volume: str = None, pitch: str = None):
        """设置TTS参数"""
        self.tts_engine.set_voice_parameters(rate, volume, pitch)
    
    def set_playback_volume(self, volume: float):
        """设置播放音量"""
        self.player.set_volume(volume)
    
    def get_cache_statistics(self) -> Dict:
        """获取缓存统计信息"""
        return self.audio_cache.get_cache_stats()
    
    def preload_audio(self, texts: List[str], language: str = 'en-US'):
        """预加载音频"""
        def preload_task():
            logger.info(f"开始预加载 {len(texts)} 个音频...")
            for text in texts:
                if not self.audio_cache.get_audio_path(text, language):
                    try:
                        audio_data = self.tts_engine.text_to_audio(text, language)
                        self.audio_cache.cache_audio(text, audio_data, language)
                        time.sleep(0.1)  # 避免过于频繁
                    except Exception as e:
                        logger.warning(f"预加载音频失败: {text[:30]}... - {e}")
            logger.info("音频预加载完成")
        
        preload_thread = threading.Thread(target=preload_task, daemon=True)
        preload_thread.start()
    
    def cleanup_cache(self, days: int = 30):
        """清理旧缓存"""
        self.audio_cache.cleanup_old_cache(days)


# 全局听写引擎实例
_listen_engine = None

def get_listen_engine(cache_dir: str = "data") -> ListenEngine:
    """获取全局听写引擎实例"""
    global _listen_engine
    if _listen_engine is None:
        _listen_engine = ListenEngine(cache_dir)
    return _listen_engine


if __name__ == "__main__":
    # 测试听写引擎
    engine = ListenEngine()
    
    print("=== 听写引擎测试 ===")
    
    # 测试TTS播放
    test_text = "Hello, this is a test of the dictation system."
    print(f"播放测试文本: {test_text}")
    
    def playback_finished():
        print("播放完成")
    
    if engine.play_text(test_text, callback=playback_finished):
        print("开始播放...")
        time.sleep(3)  # 等待播放完成
    
    # 测试录音
    print("\n录音测试 (3秒)...")
    recognized, volume = engine.record_for_duration(3.0)
    print(f"识别结果: {recognized}")
    print(f"音量级别: {volume:.1f}%")
    
    # 测试文本比较
    comparison = engine.compare_texts(test_text, recognized)
    print(f"文本比较结果: {comparison}")
    
    # 获取缓存统计
    cache_stats = engine.get_cache_statistics()
    print(f"缓存统计: {cache_stats}")
    
    print("测试完成")