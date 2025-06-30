#!/usr/bin/env python3
"""
Main GUI Interface for Word Memorizer
主界面GUI - 使用Tkinter实现标签页界面

This module provides:
- Main window with tabbed interface (Word/Stats)
- Word dictation interface with audio controls
- Statistics panel with matplotlib charts
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

# Third-party imports - 延迟导入matplotlib以提升启动速度
# matplotlib相关导入移到StatisticsPanel类中按需加载
from PIL import Image, ImageTk
import sv_ttk  # Sun Valley theme for modern look

# matplotlib配置移到StatisticsPanel中延迟加载

# Local imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
from logic.core import MemorizerCore, WordItem
from audio.listen import get_listen_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




class StatisticsPanel:
    """统计面板"""
    
    def __init__(self, parent_frame, core: MemorizerCore):
        self.parent_frame = parent_frame
        self.core = core
        self.figure = None
        self.canvas = None
        self.matplotlib_loaded = False
        self._create_widgets()
    
    def _load_matplotlib(self):
        """延迟加载matplotlib"""
        if not self.matplotlib_loaded:
            try:
                global plt, Figure, FigureCanvasTkAgg, fm, np
                import matplotlib.pyplot as plt
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
                from matplotlib.figure import Figure
                import matplotlib.font_manager as fm
                import numpy as np
                self.matplotlib_loaded = True
                self._setup_fonts()
                logger.info("matplotlib已加载")
            except Exception as e:
                logger.error(f"加载matplotlib失败: {e}")
                return False
        return True
    
    def _setup_fonts(self):
        """设置中文字体支持"""
        try:
            import platform
            system = platform.system()
            
            if system == 'Darwin':  # macOS
                # macOS使用系统自带的中文字体
                plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'PingFang SC', 'Arial Unicode MS', 'Arial']
                logger.info("matplotlib字体配置完成（macOS - 支持中文）")
            elif system == 'Windows':
                # Windows使用常见的中文字体
                plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'Arial']  
                logger.info("matplotlib字体配置完成（Windows - 支持中文）")
            else:
                # Linux等其他系统使用英文字体
                plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
                logger.info("matplotlib字体配置完成（Linux - 英文标签）")
            
            plt.rcParams['axes.unicode_minus'] = False
            
        except Exception as e:
            logger.warning(f"字体设置失败: {e}")
            # 使用默认设置
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
            plt.rcParams['axes.unicode_minus'] = False
    
    def _get_labels(self):
        """根据平台返回合适的标签"""
        import platform
        system = platform.system()
        
        if system in ['Darwin', 'Windows']:  # macOS and Windows
            return {
                'correct': '正确',
                'incorrect': '错误', 
                'word_accuracy': '单词准确率',
                'daily_progress': '每日学习进度（最近14天）',
                'date': '日期',
                'words_reviewed': '复习单词数',
                'no_records': '暂无学习记录'
            }
        else:  # Linux and others
            return {
                'correct': 'Correct',
                'incorrect': 'Incorrect',
                'word_accuracy': 'Word Accuracy', 
                'daily_progress': 'Daily Word Learning Progress (Last 14 Days)',
                'date': 'Date',
                'words_reviewed': 'Words Reviewed',
                'no_records': 'No word learning records yet'
            }
    
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
        # 加载matplotlib
        if not self._load_matplotlib():
            logger.error("无法加载matplotlib，跳过图表显示")
            return
            
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
            
            labels_dict = self._get_labels()
            labels = [labels_dict['correct'], labels_dict['incorrect']]
            sizes = [correct_count, incorrect_count]
            colors = ['lightgreen', 'lightcoral']
            
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title(f"{labels_dict['word_accuracy']} ({word_accuracy:.1f}%)")
        else:
            labels_dict = self._get_labels()
            ax.text(0.5, 0.5, labels_dict['no_records'], ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(labels_dict['word_accuracy'])
    
    def _create_daily_word_progress_chart(self, ax, stats: Dict):
        """创建每日单词学习进度折线图"""
        daily_progress = stats.get('daily_progress', [])
        
        if daily_progress:
            dates = [item['date'] for item in daily_progress[-14:]]  # 最近14天
            word_counts = [item.get('words', 0) for item in daily_progress[-14:]]
            
            ax.plot(dates, word_counts, marker='o', linewidth=2, color='blue', 
                   markersize=6, markerfacecolor='lightblue')
            
            labels_dict = self._get_labels()
            ax.set_title(labels_dict['daily_progress'])
            ax.set_xlabel(labels_dict['date'])
            ax.set_ylabel(labels_dict['words_reviewed'])
            ax.grid(True, alpha=0.3)
            
            # 填充区域
            ax.fill_between(dates, word_counts, alpha=0.3, color='lightblue')
            
            # 旋转x轴标签
            for label in ax.get_xticklabels():
                label.set_rotation(45)
                label.set_ha('right')
        else:
            labels_dict = self._get_labels()
            ax.text(0.5, 0.5, labels_dict['no_records'], ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(labels_dict['daily_progress'])
    
    def export_report(self):
        """导出统计报告"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[
                    ("HTML files", "*.html"), 
                    ("JSON files", "*.json"), 
                    ("All files", "*.*")
                ],
                title="保存统计报告"
            )
            
            if file_path:
                stats = self.core.get_overall_stats()
                session_stats = self.core.get_session_stats()
                
                if file_path.endswith('.html'):
                    self._export_html_report(file_path, stats, session_stats)
                else:
                    self._export_json_report(file_path, stats, session_stats)
                
                messagebox.showinfo("成功", f"统计报告已保存到: {file_path}")
        except Exception as e:
            logger.error(f"导出报告失败: {e}")
            messagebox.showerror("错误", f"导出失败: {e}")
    
    def _export_json_report(self, file_path: str, stats: Dict, session_stats: Dict):
        """导出JSON格式报告"""
        report = {
            'export_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'overall_stats': stats,
            'session_stats': session_stats
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def _export_html_report(self, file_path: str, stats: Dict, session_stats: Dict):
        """导出HTML格式报告（带图表）"""
        # 确保matplotlib已加载
        if not self._load_matplotlib():
            raise Exception("无法加载matplotlib，无法生成图表")
        
        # 生成图表
        fig = Figure(figsize=(12, 8), dpi=100)
        
        # 创建子图
        ax1 = fig.add_subplot(221)  # 左上：单词统计
        ax2 = fig.add_subplot(222)  # 右上：准确率
        ax3 = fig.add_subplot(212)  # 下方：每日进度
        
        # 生成图表
        self._create_word_stats_chart(ax1, stats)
        self._create_word_accuracy_chart(ax2, stats)
        self._create_daily_word_progress_chart(ax3, stats)
        
        fig.tight_layout()
        
        # 保存图表为base64字符串
        import io
        import base64
        
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_data = base64.b64encode(img_buffer.read()).decode()
        img_buffer.close()
        
        # 生成HTML内容
        html_content = self._generate_html_template(stats, session_stats, img_data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_html_template(self, stats: Dict, session_stats: Dict, chart_img: str) -> str:
        """生成HTML模板"""
        words = stats.get('words', {})
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WordMemorizer 学习报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(45deg, #1e3c72, #2a5298);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 1.1em;
        }}
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #2a5298;
            margin: 10px 0;
        }}
        .stat-card .unit {{
            color: #666;
            font-size: 0.9em;
        }}
        .chart-section {{
            margin-top: 30px;
            text-align: center;
        }}
        .chart-section h2 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .chart-image {{
            max-width: 100%;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .session-info {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }}
        .session-info h3 {{
            margin-top: 0;
            color: #495057;
        }}
        .progress-bar {{
            background: #e9ecef;
            border-radius: 10px;
            height: 8px;
            margin: 10px 0;
            overflow: hidden;
        }}
        .progress-fill {{
            background: linear-gradient(90deg, #28a745, #20c997);
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 WordMemorizer 学习报告</h1>
            <p>生成时间: {time.strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        </div>
        
        <div class="content">
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>📖 词汇总数</h3>
                    <div class="value">{words.get('total', 0)}</div>
                    <div class="unit">个单词</div>
                </div>
                <div class="stat-card">
                    <h3>✅ 已复习</h3>
                    <div class="value">{words.get('reviewed', 0)}</div>
                    <div class="unit">个单词</div>
                </div>
                <div class="stat-card">
                    <h3>🎯 准确率</h3>
                    <div class="value">{words.get('accuracy', 0):.1f}%</div>
                    <div class="unit">正确率</div>
                </div>
                <div class="stat-card">
                    <h3>📊 平均难度</h3>
                    <div class="value">{words.get('avg_difficulty', 0):.1f}</div>
                    <div class="unit">/ 5.0</div>
                </div>
            </div>
            
            <div class="session-info">
                <h3>🎮 本次学习session</h3>
                <p><strong>学习时长:</strong> {session_stats.get('session_time', '0:00:00')}</p>
                <p><strong>复习单词:</strong> {session_stats.get('words_reviewed', 0)} 个</p>
                <p><strong>本次准确率:</strong> {session_stats.get('accuracy', 0):.1f}%</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {min(session_stats.get('accuracy', 0), 100)}%"></div>
                </div>
                <p><strong>剩余待复习:</strong> {session_stats.get('remaining_words', 0)} 个单词</p>
            </div>
            
            <div class="chart-section">
                <h2>📈 学习统计图表</h2>
                <img src="data:image/png;base64,{chart_img}" alt="学习统计图表" class="chart-image">
            </div>
        </div>
        
        <div class="footer">
            <p>📱 Generated by WordMemorizer v1.1.0 | 英语单词记忆系统</p>
        </div>
    </div>
</body>
</html>'''


class DictationInterface:
    """听写界面基类"""
    
    def __init__(self, parent_frame, core: MemorizerCore, item_type: str):
        self.parent_frame = parent_frame
        self.core = core
        self.item_type = item_type  # "word" or "sentence"
        self.listen_engine = get_listen_engine()
        
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
    
    
    def _show_help(self):
        """显示帮助"""
        help_text = """
        英语单词记忆系统使用说明：
        
        1. 单词听写：播放单词发音，通过手动输入进行听写
        2. 学习统计：查看学习进度和统计图表
        3. 导入词书：支持CSV和JSON格式的自定义词书
        
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