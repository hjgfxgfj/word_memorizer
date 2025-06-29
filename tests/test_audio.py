#!/usr/bin/env python3
"""
Unit Tests for Audio Listen Engine Module
音频听写引擎模块单元测试
"""

import unittest
import tempfile
import shutil
import time
import sqlite3
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock, AsyncMock
import numpy as np

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from audio.listen import (
    TTSEngine, AudioCache, AudioPlayer, AudioRecorder, ListenEngine, get_listen_engine
)


class TestTTSEngine(unittest.TestCase):
    """测试TTS引擎"""
    
    def setUp(self):
        """测试前准备"""
        self.tts = TTSEngine()
    
    def test_voice_map_initialization(self):
        """测试语音映射初始化"""
        self.assertIn('en-US', self.tts.voice_map)
        self.assertIn('en-GB', self.tts.voice_map)
        self.assertIn('zh-CN', self.tts.voice_map)
        
        self.assertEqual(self.tts.default_voice, 'en-US-AriaNeural')
    
    def test_set_voice_parameters(self):
        """测试设置语音参数"""
        self.tts.set_voice_parameters(rate='+10%', volume='-5%', pitch='+100Hz')
        
        self.assertEqual(self.tts.rate, '+10%')
        self.assertEqual(self.tts.volume, '-5%')
        self.assertEqual(self.tts.pitch, '+100Hz')
    
    @patch('edge_tts.Communicate')
    async def test_text_to_audio_async(self, mock_communicate):
        """测试异步文本转音频"""
        # Mock the communicate object
        mock_instance = MagicMock()
        mock_communicate.return_value = mock_instance
        
        # Mock the stream method to return audio chunks
        async def mock_stream():
            yield {"type": "audio", "data": b"audio_chunk_1"}
            yield {"type": "audio", "data": b"audio_chunk_2"}
            yield {"type": "other", "data": b"ignore_this"}
        
        mock_instance.stream = mock_stream
        
        # Test the method
        result = await self.tts.text_to_audio_async("Hello world", "en-US")
        
        self.assertEqual(result, b"audio_chunk_1audio_chunk_2")
        mock_communicate.assert_called_once()
    
    @patch.object(TTSEngine, 'text_to_audio_async')
    def test_text_to_audio(self, mock_async):
        """测试同步文本转音频"""
        mock_async.return_value = b"test_audio_data"
        
        # Mock asyncio event loop
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop
            mock_loop.run_until_complete.return_value = b"test_audio_data"
            
            result = self.tts.text_to_audio("Hello world")
            
            self.assertEqual(result, b"test_audio_data")
    
    @patch.object(TTSEngine, 'text_to_audio')
    def test_save_audio_file(self, mock_text_to_audio):
        """测试保存音频文件"""
        mock_text_to_audio.return_value = b"test_audio_data"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = self.tts.save_audio_file("Hello world", temp_path)
            
            self.assertTrue(result)
            
            # 验证文件内容
            with open(temp_path, 'rb') as f:
                content = f.read()
            self.assertEqual(content, b"test_audio_data")
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestAudioCache(unittest.TestCase):
    """测试音频缓存系统"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = AudioCache(self.temp_dir)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_cache_initialization(self):
        """测试缓存初始化"""
        db_path = Path(self.temp_dir) / "audio_cache.db"
        audio_dir = Path(self.temp_dir) / "audio"
        
        self.assertTrue(db_path.exists())
        self.assertTrue(audio_dir.exists())
        
        # 检查数据库表
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='audio_cache'
            """)
            self.assertIsNotNone(cursor.fetchone())
    
    def test_generate_hash(self):
        """测试哈希生成"""
        hash1 = self.cache._generate_hash("hello world", "en-US")
        hash2 = self.cache._generate_hash("HELLO WORLD", "en-US")  # 大小写不同
        hash3 = self.cache._generate_hash("hello world", "zh-CN")  # 语言不同
        
        self.assertEqual(hash1, hash2)  # 应该相同（忽略大小写）
        self.assertNotEqual(hash1, hash3)  # 应该不同（语言不同）
        self.assertEqual(len(hash1), 32)  # MD5哈希长度
    
    def test_cache_audio_and_get_path(self):
        """测试缓存音频和获取路径"""
        test_audio_data = b"fake_audio_data_for_testing"
        text = "Hello world"
        language = "en-US"
        
        # 缓存音频
        file_path = self.cache.cache_audio(text, test_audio_data, language)
        
        self.assertTrue(Path(file_path).exists())
        
        # 验证文件内容
        with open(file_path, 'rb') as f:
            cached_data = f.read()
        self.assertEqual(cached_data, test_audio_data)
        
        # 测试获取缓存路径
        cached_path = self.cache.get_audio_path(text, language)
        self.assertEqual(str(Path(cached_path)), str(Path(file_path)))
    
    def test_cache_miss(self):
        """测试缓存未命中"""
        result = self.cache.get_audio_path("nonexistent text", "en-US")
        self.assertIsNone(result)
    
    def test_get_cache_stats(self):
        """测试获取缓存统计"""
        # 添加一些测试数据
        self.cache.cache_audio("text1", b"audio1", "en-US")
        self.cache.cache_audio("text2", b"audio2", "zh-CN")
        
        stats = self.cache.get_cache_stats()
        
        self.assertIn('total_files', stats)
        self.assertIn('total_size_mb', stats)
        self.assertIn('by_language', stats)
        
        self.assertEqual(stats['total_files'], 2)
        self.assertIn('en-US', stats['by_language'])
        self.assertIn('zh-CN', stats['by_language'])
    
    def test_cleanup_old_cache(self):
        """测试清理旧缓存"""
        # 添加测试数据
        file_path = self.cache.cache_audio("test", b"audio", "en-US")
        
        # 验证文件存在
        self.assertTrue(Path(file_path).exists())
        
        # 手动设置过期时间
        db_path = Path(self.temp_dir) / "audio_cache.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                UPDATE audio_cache 
                SET accessed_at = datetime('now', '-40 days')
            """)
        
        # 清理30天前的缓存
        self.cache.cleanup_old_cache(30)
        
        # 验证文件被删除
        self.assertFalse(Path(file_path).exists())


class TestAudioPlayer(unittest.TestCase):
    """测试音频播放器"""
    
    def setUp(self):
        """测试前准备"""
        # Mock pygame.mixer to avoid actual audio initialization
        with patch('pygame.mixer.init'), \
             patch('pygame.mixer.music.set_volume'):
            self.player = AudioPlayer()
    
    @patch('pygame.mixer.music.load')
    @patch('pygame.mixer.music.play')
    @patch('os.path.exists')
    def test_play_audio_file_success(self, mock_exists, mock_play, mock_load):
        """测试音频文件播放成功"""
        mock_exists.return_value = True
        
        result = self.player.play_audio_file("test_file.mp3")
        
        self.assertTrue(result)
        self.assertTrue(self.player.is_playing)
        mock_load.assert_called_once_with("test_file.mp3")
        mock_play.assert_called_once()
    
    @patch('os.path.exists')
    def test_play_audio_file_not_exists(self, mock_exists):
        """测试播放不存在的音频文件"""
        mock_exists.return_value = False
        
        result = self.player.play_audio_file("nonexistent.mp3")
        
        self.assertFalse(result)
        self.assertFalse(self.player.is_playing)
    
    @patch('tempfile.NamedTemporaryFile')
    @patch.object(AudioPlayer, 'play_audio_file')
    def test_play_audio_data(self, mock_play_file, mock_temp_file):
        """测试播放音频数据"""
        # Mock temporary file
        mock_temp = MagicMock()
        mock_temp.name = "temp_audio_file.mp3"
        mock_temp_file.return_value.__enter__.return_value = mock_temp
        
        mock_play_file.return_value = True
        
        test_audio_data = b"fake_audio_data"
        result = self.player.play_audio_data(test_audio_data)
        
        self.assertTrue(result)
        mock_temp.write.assert_called_once_with(test_audio_data)
        mock_play_file.assert_called_once()
    
    @patch('pygame.mixer.music.stop')
    def test_stop_audio(self, mock_stop):
        """测试停止音频播放"""
        self.player.is_playing = True
        
        self.player.stop_audio()
        
        self.assertFalse(self.player.is_playing)
        mock_stop.assert_called_once()
    
    @patch('pygame.mixer.music.set_volume')
    def test_set_volume(self, mock_set_volume):
        """测试设置音量"""
        self.player.set_volume(0.8)
        
        self.assertEqual(self.player.volume, 0.8)
        mock_set_volume.assert_called_with(0.8)
        
        # 测试边界值
        self.player.set_volume(1.5)  # 超过最大值
        self.assertEqual(self.player.volume, 1.0)
        
        self.player.set_volume(-0.1)  # 低于最小值
        self.assertEqual(self.player.volume, 0.0)


class TestAudioRecorder(unittest.TestCase):
    """测试音频录制器"""
    
    def setUp(self):
        """测试前准备"""
        # Mock speech_recognition components
        with patch('speech_recognition.Recognizer'), \
             patch('speech_recognition.Microphone'):
            self.recorder = AudioRecorder()
    
    @patch('sounddevice.InputStream')
    def test_start_recording(self, mock_input_stream):
        """测试开始录音"""
        mock_stream = MagicMock()
        mock_input_stream.return_value = mock_stream
        
        result = self.recorder.start_recording()
        
        self.assertTrue(result)
        self.assertTrue(self.recorder.is_recording)
        mock_stream.start.assert_called_once()
    
    def test_start_recording_already_recording(self):
        """测试已在录音时开始录音"""
        self.recorder.is_recording = True
        
        result = self.recorder.start_recording()
        
        self.assertFalse(result)
    
    def test_stop_recording_not_recording(self):
        """测试未在录音时停止录音"""
        self.recorder.is_recording = False
        
        result = self.recorder.stop_recording()
        
        self.assertIsNone(result)
    
    def test_stop_recording_with_data(self):
        """测试有数据时停止录音"""
        # 模拟录音数据
        self.recorder.is_recording = True
        self.recorder.recorded_data = [
            np.array([[1, 2, 3]], dtype=np.int16),
            np.array([[4, 5, 6]], dtype=np.int16)
        ]
        
        # Mock stream
        mock_stream = MagicMock()
        self.recorder._stream = mock_stream
        
        result = self.recorder.stop_recording()
        
        self.assertIsNotNone(result)
        self.assertFalse(self.recorder.is_recording)
        self.assertEqual(len(result), 6)  # 合并后的数据长度
        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()
    
    @patch('scipy.io.wavfile.write')
    def test_save_recording(self, mock_wavfile_write):
        """测试保存录音"""
        test_audio = np.array([1, 2, 3, 4, 5], dtype=np.int16)
        
        result = self.recorder.save_recording(test_audio, "test.wav")
        
        self.assertTrue(result)
        mock_wavfile_write.assert_called_once_with("test.wav", 16000, test_audio)
    
    def test_get_audio_level(self):
        """测试获取音频级别"""
        # 测试空数据
        level = self.recorder.get_audio_level(None)
        self.assertEqual(level, 0.0)
        
        level = self.recorder.get_audio_level(np.array([]))
        self.assertEqual(level, 0.0)
        
        # 测试有数据
        test_audio = np.array([1000, 2000, 3000], dtype=np.int16)
        level = self.recorder.get_audio_level(test_audio)
        self.assertGreater(level, 0.0)
        self.assertLessEqual(level, 100.0)
    
    @patch('speech_recognition.Recognizer.recognize_google')
    @patch('speech_recognition.Recognizer.record')
    @patch('speech_recognition.AudioFile')
    @patch.object(AudioRecorder, 'save_recording')
    def test_recognize_speech(self, mock_save, mock_audio_file, mock_record, mock_recognize):
        """测试语音识别"""
        # Mock dependencies
        mock_save.return_value = True
        mock_audio_file.return_value.__enter__ = MagicMock()
        mock_audio_file.return_value.__exit__ = MagicMock()
        mock_record.return_value = MagicMock()
        mock_recognize.return_value = "recognized text"
        
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        result = self.recorder.recognize_speech(test_audio)
        
        self.assertEqual(result, "recognized text")
        mock_recognize.assert_called_once()


class TestListenEngine(unittest.TestCase):
    """测试听写引擎"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock all audio components
        with patch('audio.listen.TTSEngine'), \
             patch('audio.listen.AudioCache'), \
             patch('audio.listen.AudioPlayer'), \
             patch('audio.listen.AudioRecorder'):
            self.engine = ListenEngine(self.temp_dir)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_play_text_with_cache(self):
        """测试播放文本（有缓存）"""
        # Mock cache hit
        self.engine.audio_cache.get_audio_path.return_value = "cached_file.mp3"
        self.engine.player.play_audio_file.return_value = True
        
        result = self.engine.play_text("Hello world", "en-US")
        
        self.assertTrue(result)
        self.assertEqual(self.engine.current_text, "Hello world")
        self.assertEqual(self.engine.current_language, "en-US")
        self.engine.player.play_audio_file.assert_called_once_with("cached_file.mp3", None)
    
    def test_play_text_without_cache(self):
        """测试播放文本（无缓存）"""
        # Mock cache miss and TTS generation
        self.engine.audio_cache.get_audio_path.return_value = None
        self.engine.tts_engine.text_to_audio.return_value = b"audio_data"
        self.engine.audio_cache.cache_audio.return_value = "new_cached_file.mp3"
        self.engine.player.play_audio_file.return_value = True
        
        result = self.engine.play_text("Hello world", "en-US")
        
        self.assertTrue(result)
        self.engine.tts_engine.text_to_audio.assert_called_once_with("Hello world", "en-US")
        self.engine.audio_cache.cache_audio.assert_called_once()
    
    def test_replay_current(self):
        """测试重播当前文本"""
        self.engine.current_text = "Hello world"
        self.engine.current_language = "en-US"
        
        # Mock play_text method
        with patch.object(self.engine, 'play_text') as mock_play:
            mock_play.return_value = True
            result = self.engine.replay_current()
            
            self.assertTrue(result)
            mock_play.assert_called_once_with("Hello world", "en-US", None)
    
    def test_start_stop_dictation(self):
        """测试开始和停止听写"""
        # Mock recorder methods
        self.engine.recorder.start_recording.return_value = True
        self.engine.recorder.stop_recording.return_value = np.array([1, 2, 3])
        self.engine.recorder.get_audio_level.return_value = 75.5
        self.engine.recorder.recognize_speech.return_value = "recognized text"
        
        # 开始听写
        result = self.engine.start_dictation()
        self.assertTrue(result)
        
        # 停止听写
        text, volume = self.engine.stop_dictation()
        self.assertEqual(text, "recognized text")
        self.assertEqual(volume, 75.5)
    
    def test_compare_texts(self):
        """测试文本比较"""
        original = "Hello world test"
        recognized = "hello world test"  # 大小写不同
        
        comparison = self.engine.compare_texts(original, recognized)
        
        self.assertIn('original', comparison)
        self.assertIn('recognized', comparison)
        self.assertIn('similarity', comparison)
        self.assertIn('is_correct', comparison)
        
        self.assertEqual(comparison['original'], original)
        self.assertEqual(comparison['recognized'], recognized)
        self.assertGreaterEqual(comparison['similarity'], 80.0)  # 应该很高
        self.assertTrue(comparison['is_correct'])
    
    def test_compare_texts_different(self):
        """测试比较不同文本"""
        original = "apple banana orange"
        recognized = "cat dog elephant"
        
        comparison = self.engine.compare_texts(original, recognized)
        
        self.assertLess(comparison['similarity'], 80.0)
        self.assertFalse(comparison['is_correct'])
    
    def test_set_parameters(self):
        """测试设置参数"""
        # 测试设置TTS参数
        self.engine.set_tts_parameters(rate='+10%', volume='-5%')
        self.engine.tts_engine.set_voice_parameters.assert_called_once_with('+10%', '-5%', None)
        
        # 测试设置播放音量
        self.engine.set_playback_volume(0.8)
        self.engine.player.set_volume.assert_called_once_with(0.8)


class TestGlobalListenEngine(unittest.TestCase):
    """测试全局听写引擎"""
    
    def test_get_listen_engine_singleton(self):
        """测试单例模式"""
        with patch('audio.listen.ListenEngine'):
            engine1 = get_listen_engine()
            engine2 = get_listen_engine()
            
            self.assertIs(engine1, engine2)  # 应该是同一个对象


if __name__ == '__main__':
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestTTSEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioCache))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioPlayer))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioRecorder))
    suite.addTests(loader.loadTestsFromTestCase(TestListenEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalListenEngine))
    
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