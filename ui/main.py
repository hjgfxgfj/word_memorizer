#!/usr/bin/env python3
"""
Main GUI Interface for Word Memorizer
主界面GUI - 使用Tkinter实现标签页界面

This module provides:
- Main window with tabbed interface (Word/Stats)
- Word dictation interface with audio controls
- Statistics panel with matplotlib charts
- AI explanation popup windows
- Settings and preferences
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import tkinter.font as tkFont
import threading
import queue
import time
import json
from pathlib import Path
from typing import Dict, Optional, List, Callable
import logging

# Third-party imports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.font_manager as fm
import numpy as np
from PIL import Image, ImageTk
import sv_ttk  # Sun Valley theme for modern look

# 配置matplotlib中文字体支持
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# Local imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
from logic.core import MemorizerCore, WordItem
from logic.ai import get_ai_explainer
from audio.listen import get_listen_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIExplanationWindow:
    """AI释义弹窗"""
    
    def __init__(self, parent, item: WordItem):
        self.parent = parent
        self.item = item
        self.ai_explainer = get_ai_explainer()
        self.window = None
        self.explanation_data = None
    
    def show(self):
        """显示AI释义窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("AI 智能释义")
        self.window.geometry("600x500")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # 设置窗口图标和样式
        self._setup_window_style()
        
        # 创建界面
        self._create_widgets()
        
        # 异步获取AI释义
        self._load_explanation()
    
    def _setup_window_style(self):
        """设置窗口样式"""
        self.window.configure(bg='#f0f0f0')
        
        # 居中显示
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"600x500+{x}+{y}")
    
    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题区域
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_text = f"单词: {self.item.word}"
        subtitle_text = f"含义: {self.item.meaning}"
        
        title_label = ttk.Label(title_frame, text=title_text, font=('Arial', 16, 'bold'))
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(title_frame, text=subtitle_text, font=('Arial', 10))
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
        
        # 内容区域
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 加载提示
        self.loading_label = ttk.Label(self.content_frame, text="正在获取AI释义，请稍候...", 
                                     font=('Arial', 12))
        self.loading_label.pack(expand=True)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="关闭", command=self.window.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="复制内容", command=self._copy_content).pack(side=tk.RIGHT, padx=(0, 10))
    
    def _load_explanation(self):
        """异步加载AI释义"""
        def load_task():
            try:
                if isinstance(self.item, WordItem):
                    self.explanation_data = self.ai_explainer.explain_word(self.item.word)
                else:
                    self.explanation_data = self.ai_explainer.explain_sentence(self.item.sentence)
                
                # 在主线程更新UI
                self.window.after(0, self._update_content)
            except Exception as e:
                logger.error(f"获取AI释义失败: {e}")
                self.window.after(0, lambda: self._show_error(str(e)))
        
        threading.Thread(target=load_task, daemon=True).start()
    
    def _update_content(self):
        """更新内容显示"""
        # 清除加载提示
        self.loading_label.destroy()
        
        # 创建滚动文本区域
        text_widget = scrolledtext.ScrolledText(self.content_frame, wrap=tk.WORD, 
                                              font=('Arial', 11), height=20)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # 显示AI释义内容
        if isinstance(self.item, WordItem):
            self._display_word_explanation(text_widget)
        else:
            self._display_sentence_explanation(text_widget)
        
        text_widget.config(state=tk.DISABLED)  # 设置为只读
    
    def _display_word_explanation(self, text_widget):
        """显示单词释义"""
        data = self.explanation_data
        
        text_widget.insert(tk.END, f"📝 单词: {data['word']}\n\n")
        
        if data.get('pronunciation'):
            text_widget.insert(tk.END, f"🔊 发音: {data['pronunciation']}\n\n")
        
        if data.get('word_type'):
            text_widget.insert(tk.END, f"📚 词性: {data['word_type']}\n\n")
        
        if data.get('meanings'):
            text_widget.insert(tk.END, "💡 主要含义:\n")
            for i, meaning in enumerate(data['meanings'], 1):
                text_widget.insert(tk.END, f"  {i}. {meaning}\n")
            text_widget.insert(tk.END, "\n")
        
        if data.get('examples'):
            text_widget.insert(tk.END, "📖 例句:\n")
            for i, example in enumerate(data['examples'], 1):
                text_widget.insert(tk.END, f"  {i}. {example}\n")
            text_widget.insert(tk.END, "\n")
        
        if data.get('synonyms'):
            text_widget.insert(tk.END, "🔗 同义词:\n")
            synonyms_text = ", ".join(data['synonyms'])
            text_widget.insert(tk.END, f"  {synonyms_text}\n")
    
    def _display_sentence_explanation(self, text_widget):
        """显示句子释义"""
        data = self.explanation_data
        
        text_widget.insert(tk.END, "📝 原句:\n")
        text_widget.insert(tk.END, f"{data['sentence']}\n\n")
        
        if data.get('translation'):
            text_widget.insert(tk.END, "🌍 翻译:\n")
            text_widget.insert(tk.END, f"{data['translation']}\n\n")
        
        if data.get('difficulty_level'):
            text_widget.insert(tk.END, f"⭐ 难度等级: {data['difficulty_level']}/5\n\n")
        
        if data.get('grammar_points'):
            text_widget.insert(tk.END, "📐 语法要点:\n")
            for i, point in enumerate(data['grammar_points'], 1):
                text_widget.insert(tk.END, f"  {i}. {point}\n")
            text_widget.insert(tk.END, "\n")
        
        if data.get('key_words'):
            text_widget.insert(tk.END, "🔑 关键词汇:\n")
            for word_info in data['key_words']:
                text_widget.insert(tk.END, f"  • {word_info.get('word', '')}: {word_info.get('meaning', '')}\n")
                if word_info.get('usage'):
                    text_widget.insert(tk.END, f"    用法: {word_info['usage']}\n")
    
    def _show_error(self, error_message):
        """显示错误信息"""
        self.loading_label.config(text=f"获取释义失败: {error_message}")
    
    def _copy_content(self):
        """复制内容到剪贴板"""
        if self.explanation_data:
            content = json.dumps(self.explanation_data, ensure_ascii=False, indent=2)
            self.window.clipboard_clear()
            self.window.clipboard_append(content)
            messagebox.showinfo("提示", "内容已复制到剪贴板")


class StatisticsPanel:
    """统计面板"""
    
    def __init__(self, parent_frame, core: MemorizerCore):
        self.parent_frame = parent_frame
        self.core = core
        self.figure = None
        self.canvas = None
        self._setup_fonts()
        self._create_widgets()
    
    def _setup_fonts(self):
        """设置中文字体支持"""
        try:
            # 尝试查找系统中可用的中文字体
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            
            # 优先选择的中文字体列表
            chinese_fonts = [
                'PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'SimHei', 
                'Microsoft YaHei', 'Arial Unicode MS', 'Noto Sans CJK'
            ]
            
            # 找到第一个可用的中文字体
            selected_font = 'DejaVu Sans'  # 默认字体
            for font in chinese_fonts:
                if font in available_fonts:
                    selected_font = font
                    break
            
            # 设置matplotlib字体
            plt.rcParams['font.sans-serif'] = [selected_font, 'DejaVu Sans', 'Arial']
            plt.rcParams['axes.unicode_minus'] = False
            
            logger.info(f"字体设置成功: {selected_font}")
            
        except Exception as e:
            logger.warning(f"字体设置失败: {e}")
            # 使用默认设置
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
            plt.rcParams['axes.unicode_minus'] = False
    
    def _create_widgets(self):
        """创建统计面板组件"""
        # 顶部控制面板
        control_frame = ttk.Frame(self.parent_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(control_frame, text="📊 学习统计", font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(control_frame, text="刷新数据", command=self.refresh_data).pack(side=tk.RIGHT)
        ttk.Button(control_frame, text="导出报告", command=self.export_report).pack(side=tk.RIGHT, padx=(0, 10))
        
        # 数据显示区域
        self.stats_frame = ttk.LabelFrame(self.parent_frame, text="概览统计", padding="10")
        self.stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 图表显示区域
        self.chart_frame = ttk.LabelFrame(self.parent_frame, text="数据图表", padding="10")
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.refresh_data()
    
    def refresh_data(self):
        """刷新统计数据"""
        try:
            stats = self.core.get_overall_stats()
            session_stats = self.core.get_session_stats()
            
            # 更新概览统计
            self._update_overview(stats, session_stats)
            
            # 更新图表
            self._update_charts(stats)
        except Exception as e:
            logger.error(f"刷新统计数据失败: {e}")
            messagebox.showerror("错误", f"刷新数据失败: {e}")
    
    def _update_overview(self, stats: Dict, session_stats: Dict):
        """更新概览统计"""
        # 清除旧的统计显示
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        # 创建统计信息网格
        info_frame = ttk.Frame(self.stats_frame)
        info_frame.pack(fill=tk.X)
        
        # 单词统计
        word_frame = ttk.LabelFrame(info_frame, text="单词统计", padding="10")
        word_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        word_stats = stats.get('words', {})
        self._create_stat_item(word_frame, "总数", word_stats.get('total', 0))
        self._create_stat_item(word_frame, "已复习", word_stats.get('reviewed', 0))
        self._create_stat_item(word_frame, "正确率", f"{word_stats.get('accuracy', 0):.1f}%")
        
        
        # 当前会话统计
        session_frame = ttk.LabelFrame(info_frame, text="当前会话", padding="10")
        session_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self._create_stat_item(session_frame, "会话时长", session_stats.get('session_time', '0:00:00'))
        self._create_stat_item(session_frame, "已复习", session_stats.get('total_reviewed', 0))
        self._create_stat_item(session_frame, "正确率", f"{session_stats.get('accuracy', 0):.1f}%")
    
    def _create_stat_item(self, parent, label: str, value):
        """创建统计项"""
        item_frame = ttk.Frame(parent)
        item_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(item_frame, text=f"{label}:", font=('Arial', 9)).pack(side=tk.LEFT)
        ttk.Label(item_frame, text=str(value), font=('Arial', 9, 'bold')).pack(side=tk.RIGHT)
    
    def _update_charts(self, stats: Dict):
        """更新图表显示"""
        # 清除旧图表
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        
        # 创建matplotlib图表
        self.figure = Figure(figsize=(12, 6), dpi=100)
        
        # 创建子图
        ax1 = self.figure.add_subplot(221)  # 左上
        ax2 = self.figure.add_subplot(222)  # 右上
        ax3 = self.figure.add_subplot(212)  # 下方整行
        
        # 图1: 单词统计柱状图
        self._create_word_stats_chart(ax1, stats)
        
        # 图2: 单词正确率饼图
        self._create_word_accuracy_chart(ax2, stats)
        
        # 图3: 每日单词学习进度
        self._create_daily_word_progress_chart(ax3, stats)
        
        self.figure.tight_layout()
        
        # 嵌入到Tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_word_stats_chart(self, ax, stats: Dict):
        """创建单词统计柱状图"""
        words = stats.get('words', {})
        
        categories = ['Total', 'Reviewed', 'Accuracy%']
        word_values = [words.get('total', 0), words.get('reviewed', 0), words.get('accuracy', 0)]
        
        x = np.arange(len(categories))
        
        ax.bar(x, word_values, color='skyblue', alpha=0.8)
        
        ax.set_title('Word Learning Statistics')
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.grid(True, alpha=0.3)
        
        # 在柱状图上显示数值
        for i, v in enumerate(word_values):
            ax.text(i, v + max(word_values) * 0.01, str(v), ha='center', va='bottom')
    
    def _create_word_accuracy_chart(self, ax, stats: Dict):
        """创建单词正确率饼图"""
        words = stats.get('words', {})
        
        word_accuracy = words.get('accuracy', 0)
        word_reviewed = words.get('reviewed', 0)
        word_total = words.get('total', 0)
        
        if word_reviewed > 0:
            correct_count = int(word_reviewed * word_accuracy / 100)
            incorrect_count = word_reviewed - correct_count
            
            labels = ['Correct', 'Incorrect']
            sizes = [correct_count, incorrect_count]
            colors = ['lightgreen', 'lightcoral']
            
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title(f'Word Accuracy ({word_accuracy:.1f}%)')
        else:
            ax.text(0.5, 0.5, 'No learning data yet', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title('Word Accuracy')
    
    def _create_daily_word_progress_chart(self, ax, stats: Dict):
        """创建每日单词学习进度折线图"""
        daily_progress = stats.get('daily_progress', [])
        
        if daily_progress:
            dates = [item['date'] for item in daily_progress[-14:]]  # 最近14天
            word_counts = [item.get('words', 0) for item in daily_progress[-14:]]
            
            ax.plot(dates, word_counts, marker='o', linewidth=2, color='blue', 
                   markersize=6, markerfacecolor='lightblue')
            
            ax.set_title('Daily Word Learning Progress (Last 14 Days)')
            ax.set_xlabel('Date')
            ax.set_ylabel('Words Reviewed')
            ax.grid(True, alpha=0.3)
            
            # 填充区域
            ax.fill_between(dates, word_counts, alpha=0.3, color='lightblue')
            
            # 旋转x轴标签
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        else:
            ax.text(0.5, 0.5, 'No word learning records yet', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title('Daily Word Learning Progress')
    
    def export_report(self):
        """导出统计报告"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="保存统计报告"
            )
            
            if file_path:
                stats = self.core.get_overall_stats()
                session_stats = self.core.get_session_stats()
                
                report = {
                    'export_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'overall_stats': stats,
                    'session_stats': session_stats
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("成功", f"统计报告已保存到: {file_path}")
        except Exception as e:
            logger.error(f"导出报告失败: {e}")
            messagebox.showerror("错误", f"导出失败: {e}")


class DictationInterface:
    """听写界面基类"""
    
    def __init__(self, parent_frame, core: MemorizerCore, item_type: str):
        self.parent_frame = parent_frame
        self.core = core
        self.item_type = item_type  # "word" or "sentence"
        self.listen_engine = get_listen_engine()
        self.ai_explainer = get_ai_explainer()
        
        self.current_item = None
        self.is_recording = False
        self.answer_submitted = False
        
        self._create_widgets()
        self._load_next_item()
    
    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.parent_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部控制区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        item_type_text = "单词" if self.item_type == "word" else "句子"
        ttk.Label(control_frame, text=f"🎧 {item_type_text}听写", 
                 font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(control_frame, text="下一个", command=self._load_next_item).pack(side=tk.RIGHT)
        ttk.Button(control_frame, text="跳过", command=self._skip_current).pack(side=tk.RIGHT, padx=(0, 10))
        
        # 内容显示区域
        self.content_frame = ttk.LabelFrame(main_frame, text="听写内容", padding="20")
        self.content_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 音频控制区域
        audio_frame = ttk.LabelFrame(main_frame, text="音频控制", padding="15")
        audio_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.play_button = ttk.Button(audio_frame, text="🔊 播放", command=self._play_audio)
        self.play_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(audio_frame, text="🔁 重播", command=self._replay_audio).pack(side=tk.LEFT, padx=(0, 10))
        
        # 音量控制
        volume_frame = ttk.Frame(audio_frame)
        volume_frame.pack(side=tk.RIGHT)
        
        ttk.Label(volume_frame, text="音量:").pack(side=tk.LEFT)
        self.volume_var = tk.DoubleVar(value=0.7)
        volume_scale = ttk.Scale(volume_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL,
                               variable=self.volume_var, command=self._on_volume_change)
        volume_scale.pack(side=tk.LEFT, padx=(5, 0))
        
        # 答案输入区域
        answer_frame = ttk.LabelFrame(main_frame, text="答案输入", padding="15")
        answer_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 答案输入
        ttk.Label(answer_frame, text="请输入您听到的内容:").pack(anchor=tk.W)
        self.answer_input = scrolledtext.ScrolledText(answer_frame, height=4, wrap=tk.WORD,
                                                    font=('Arial', 12))
        self.answer_input.pack(fill=tk.X, pady=(5, 10))
        
        # 提交按钮
        submit_frame = ttk.Frame(answer_frame)
        submit_frame.pack(fill=tk.X)
        
        self.submit_button = ttk.Button(submit_frame, text="✅ 提交答案", command=self._submit_answer)
        self.submit_button.pack(side=tk.LEFT)
        
        ttk.Button(submit_frame, text="💡 AI释义", command=self._show_ai_explanation).pack(side=tk.LEFT, padx=(10, 0))
        
        # 结果显示区域
        self.result_frame = ttk.LabelFrame(main_frame, text="结果", padding="15")
        self.result_frame.pack(fill=tk.X)
        
        self.result_text = scrolledtext.ScrolledText(self.result_frame, height=4, wrap=tk.WORD,
                                                   font=('Arial', 10), state=tk.DISABLED)
        self.result_text.pack(fill=tk.X)
    
    def _load_next_item(self):
        """加载下一个项目"""
        self.current_item = self.core.get_next_review_item(self.item_type)
        
        if self.current_item is None:
            messagebox.showinfo("完成", f"所有{self.item_type}已复习完成！")
            return
        
        self._reset_interface()
        self._display_current_item()
    
    def _reset_interface(self):
        """重置界面状态"""
        self.answer_submitted = False
        self.answer_input.delete(1.0, tk.END)
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        # 重置按钮文本和状态
        self.submit_button.config(text="✅ 提交答案", state=tk.NORMAL)
        # 隐藏结果区域（可选）
        # self.result_frame.pack_forget()
    
    def _display_current_item(self):
        """显示当前项目"""
        # 清除旧内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if isinstance(self.current_item, WordItem):
            # 显示单词信息（隐藏单词本身）
            info_text = f"听写单词，含义: {self.current_item.meaning}"
            if self.current_item.pronunciation:
                info_text += f"\n音标: {self.current_item.pronunciation}"
        else:
            # 显示句子信息（隐藏句子本身）
            info_text = f"听写句子，参考翻译: {self.current_item.translation}"
        
        content_label = ttk.Label(self.content_frame, text=info_text, 
                                font=('Arial', 12), justify=tk.LEFT)
        content_label.pack(anchor=tk.W)
        
        # 显示复习统计
        stats_text = f"复习次数: {self.current_item.review_count}, " \
                    f"正确次数: {self.current_item.correct_count}"
        stats_label = ttk.Label(self.content_frame, text=stats_text, 
                              font=('Arial', 9), foreground='gray')
        stats_label.pack(anchor=tk.W, pady=(10, 0))
    
    def _play_audio(self):
        """播放音频"""
        if self.current_item is None:
            return
        
        text_to_play = self.current_item.word if isinstance(self.current_item, WordItem) else self.current_item.sentence
        
        def play_finished():
            self.play_button.config(text="🔊 播放", state=tk.NORMAL)
        
        self.play_button.config(text="播放中...", state=tk.DISABLED)
        self.listen_engine.play_text(text_to_play, callback=play_finished)
    
    def _replay_audio(self):
        """重播音频"""
        self.listen_engine.replay_current()
    
    def _on_volume_change(self, value):
        """音量变化回调"""
        volume = float(value)
        self.listen_engine.set_playback_volume(volume)
    
    
    def _submit_answer(self):
        """提交答案"""
        # 获取用户输入的答案
        user_answer = self.answer_input.get(1.0, tk.END).strip()
        
        if not user_answer:
            messagebox.showwarning("提示", "请输入您听到的内容")
            return
        
        try:
            # 比较答案 - 现在只处理单词
            correct_answer = self.current_item.word
            
            comparison_result = self.listen_engine.compare_texts(correct_answer, user_answer)
            is_correct = comparison_result['is_correct']
            
            # 只在第一次提交时更新学习状态
            if not self.answer_submitted:
                self.core.submit_answer(self.current_item, is_correct)
                self.answer_submitted = True
            
            # 显示结果
            self._display_result(comparison_result, correct_answer, user_answer)
            
            # 更新按钮文本提示用户可以重新尝试
            if is_correct:
                self.submit_button.config(text="✅ 正确！再试一次", state=tk.NORMAL)
            else:
                self.submit_button.config(text="❌ 再试一次", state=tk.NORMAL)
                
        except Exception as e:
            logger.error(f"提交答案时发生错误: {e}")
            messagebox.showerror("错误", f"提交答案时发生错误: {str(e)}")
            # 显示基本的错误信息
            self._display_simple_result(correct_answer, user_answer)
    
    def _display_result(self, comparison: Dict, correct: str, user_answer: str):
        """显示结果"""
        try:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            
            # 构建结果文本
            is_correct = comparison.get('is_correct', False)
            similarity = comparison.get('similarity', 0.0)
            
            result_text = f"{'🎉 正确！' if is_correct else '❌ 错误'}\n"
            result_text += f"正确答案: {correct}\n"
            result_text += f"你的答案: {user_answer}\n"
            result_text += f"相似度: {similarity:.1f}%\n"
            
            if is_correct:
                result_text += "✨ 做得很好！继续加油！"
            else:
                result_text += "💪 再试一次，你可以的！"
            
            self.result_text.insert(1.0, result_text)
            self.result_text.config(state=tk.DISABLED)
            
            # 确保结果区域可见
            self.result_frame.pack(fill=tk.X, pady=(10, 0))
            
        except Exception as e:
            logger.error(f"显示结果时发生错误: {e}")
            self._display_simple_result(correct, user_answer)
    
    def _display_simple_result(self, correct: str, user_answer: str):
        """显示简单的结果（当出现异常时使用）"""
        try:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            
            # 简单比较
            is_match = correct.lower().strip() == user_answer.lower().strip()
            
            result_text = f"{'✅ 正确' if is_match else '❌ 错误'}\n"
            result_text += f"正确答案: {correct}\n"
            result_text += f"你的答案: {user_answer}\n"
            result_text += "（简单比较模式）"
            
            self.result_text.insert(1.0, result_text)
            self.result_text.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"显示简单结果时也发生错误: {e}")
            messagebox.showinfo("结果", f"正确答案: {correct}\n你的答案: {user_answer}")
    
    def _show_ai_explanation(self):
        """显示AI释义"""
        if self.current_item is None:
            return
        
        explanation_window = AIExplanationWindow(self.parent_frame, self.current_item)
        explanation_window.show()
    
    def _skip_current(self):
        """跳过当前项目"""
        if messagebox.askyesno("确认", "确定要跳过当前项目吗？"):
            self._load_next_item()


class MainApplication:
    """主应用程序"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("英语单词记忆系统 - Word Memorizer")
        self.root.geometry("1000x700")
        
        # 设置主题
        sv_ttk.use_light_theme()
        
        # 初始化核心组件
        self.core = MemorizerCore()
        self.core.initialize()
        
        # 创建界面
        self._create_menu()
        self._create_main_interface()
        
        # 设置关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导入词书", command=self._import_wordbook)
        file_menu.add_command(label="导出进度", command=self._export_progress)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_closing)
        
        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="音频设置", command=self._show_audio_settings)
        settings_menu.add_command(label="AI设置", command=self._show_ai_settings)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _create_main_interface(self):
        """创建主界面"""
        # 创建标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 单词听写页
        self.word_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.word_frame, text="📝 单词听写")
        self.word_dictation = DictationInterface(self.word_frame, self.core, "word")
        
        # 统计页面
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="📊 学习统计")
        self.statistics_panel = StatisticsPanel(self.stats_frame, self.core)
        
        # 状态栏
        self.status_bar = ttk.Label(self.root, text="准备就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 定期更新状态
        self._update_status()
    
    def _update_status(self):
        """更新状态栏"""
        try:
            session_stats = self.core.get_session_stats()
            status_text = f"会话时长: {session_stats['session_time']} | " \
                         f"已复习: {session_stats['total_reviewed']} | " \
                         f"正确率: {session_stats['accuracy']:.1f}%"
            self.status_bar.config(text=status_text)
        except Exception as e:
            self.status_bar.config(text=f"状态更新失败: {e}")
        
        # 每5秒更新一次
        self.root.after(5000, self._update_status)
    
    def _import_wordbook(self):
        """导入词书"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")],
            title="选择词书文件"
        )
        
        if file_path:
            file_type = Path(file_path).suffix.lower().lstrip('.')
            if self.core.import_custom_wordbook(file_path, file_type):
                messagebox.showinfo("成功", "词书导入成功！")
                self.statistics_panel.refresh_data()
            else:
                messagebox.showerror("错误", "词书导入失败")
    
    def _export_progress(self):
        """导出学习进度"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="导出学习进度"
        )
        
        if file_path and self.core.data_manager.save_progress():
            messagebox.showinfo("成功", "学习进度已导出")
    
    def _show_audio_settings(self):
        """显示音频设置"""
        messagebox.showinfo("设置", "音频设置功能开发中...")
    
    def _show_ai_settings(self):
        """显示AI设置"""
        messagebox.showinfo("设置", "AI设置功能开发中...")
    
    def _show_help(self):
        """显示帮助"""
        help_text = """
        英语单词记忆系统使用说明：
        
        1. 单词听写：播放单词发音，通过手动输入进行听写
        2. AI释义：获取单词的详细解释和例句
        3. 学习统计：查看学习进度和统计图表
        4. 导入词书：支持CSV和JSON格式的自定义词书
        
        快捷键：
        - Ctrl+N：下一个项目
        - Ctrl+R：重播音频
        - Ctrl+Enter：提交答案
        """
        
        messagebox.showinfo("使用说明", help_text)
    
    def _show_about(self):
        """显示关于信息"""
        about_text = """
        英语单词记忆系统
        Word Memorizer
        
        版本：1.0.0
        开发：Python课程设计项目
        
        功能特性：
        ✓ 智能复习调度（SM-2算法）
        ✓ 离线TTS语音合成
        ✓ 单词听写练习
        ✓ AI智能释义
        ✓ 学习统计分析
        """
        
        messagebox.showinfo("关于", about_text)
    
    def _on_closing(self):
        """程序关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            # 保存进度
            self.core.data_manager.save_progress()
            self.root.destroy()
    
    def run(self):
        """运行主程序"""
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = MainApplication()
        app.run()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        messagebox.showerror("错误", f"程序启动失败: {e}")