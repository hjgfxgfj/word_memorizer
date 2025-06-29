import tkinter as tk
from tkinter import ttk, messagebox
import csv
import random
import json
import os

# --- 核心逻辑部分 (不含任何GUI代码) ---
class WordMemorizerLogic:
    def __init__(self, words_filepath='words.csv', progress_filepath='progress.json'):
        self.words_filepath = words_filepath
        self.progress_filepath = progress_filepath
        self.all_words = {}
        self.to_review = []
        self.mastered = []
        self.current_word = None

    def load_words(self):
        """从CSV文件加载所有单词"""
        try:
            with open(self.words_filepath, mode='r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                for row in reader:
                    self.all_words[row['word']] = row['meaning']
        except FileNotFoundError:
            return False
        return True

    def load_progress(self):
        """加载已掌握的单词列表，并计算需要复习的列表"""
        if os.path.exists(self.progress_filepath):
            with open(self.progress_filepath, 'r', encoding='utf-8') as f:
                self.mastered = json.load(f)
        
        # 计算需要复习的单词
        mastered_set = set(self.mastered)
        self.to_review = [word for word in self.all_words if word not in mastered_set]
        random.shuffle(self.to_review) # 打乱顺序

    def save_progress(self):
        """保存进度到JSON文件"""
        with open(self.progress_filepath, 'w', encoding='utf-8') as f:
            json.dump(self.mastered, f, indent=4)

    def get_next_word(self):
        """获取下一个需要复习的单词"""
        if not self.to_review:
            self.current_word = None
            return None
        
        self.current_word = self.to_review[0]
        return self.current_word, self.all_words[self.current_word]

    def mark_as_known(self):
        """将当前单词标记为已掌握"""
        if self.current_word and self.current_word in self.to_review:
            self.to_review.remove(self.current_word)
            self.mastered.append(self.current_word)
            
    def mark_as_unknown(self):
        """将当前单词移到复习列表的末尾，以便稍后再次复习"""
        if self.current_word and self.current_word in self.to_review:
            self.to_review.remove(self.current_word)
            self.to_review.append(self.current_word)

    def get_stats(self):
        """获取统计信息"""
        total = len(self.all_words)
        known_count = len(self.mastered)
        review_count = len(self.to_review)
        return f"总数: {total} | 已掌握: {known_count} | 待复习: {review_count}"

# --- GUI部分 (Tkinter) ---
class WordMemorizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("英语背单词")
        self.root.geometry("600x400")
        
        self.logic = WordMemorizerLogic()

        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('clam') # 你可以尝试 'alt', 'default', 'classic', 'clam'
        self.style.configure("TLabel", font=("Helvetica", 12))
        self.style.configure("TButton", font=("Helvetica", 12), padding=10)
        self.style.configure("Word.TLabel", font=("Helvetica", 32, "bold"))
        self.style.configure("Meaning.TLabel", font=("Helvetica", 16))
        self.style.configure("Status.TLabel", font=("Helvetica", 10))

        self._create_widgets()
        
        if not self.logic.load_words():
            messagebox.showerror("错误", "未找到 `words.csv` 文件！\n请在程序目录下创建该文件。")
            self.root.destroy()
            return
            
        self.logic.load_progress()
        
        self.display_next_word()
        
        # 绑定关闭窗口事件，用于自动保存
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # 单词显示区域
        self.word_label = ttk.Label(main_frame, text="Word", style="Word.TLabel", anchor="center")
        self.word_label.pack(pady=(20, 10))

        # 释义显示区域
        self.meaning_label = ttk.Label(main_frame, text="", style="Meaning.TLabel", anchor="center", wraplength=500)
        self.meaning_label.pack(pady=10)

        # 按钮控制区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        self.show_button = ttk.Button(button_frame, text="显示释义", command=self.show_meaning)
        self.show_button.pack(side=tk.LEFT, padx=10)
        
        self.known_button = ttk.Button(button_frame, text="我认识", command=self.process_known, state=tk.DISABLED)
        self.known_button.pack(side=tk.LEFT, padx=10)
        
        self.unknown_button = ttk.Button(button_frame, text="不认识", command=self.process_unknown, state=tk.DISABLED)
        self.unknown_button.pack(side=tk.LEFT, padx=10)

        # 状态栏
        self.status_label = ttk.Label(self.root, text="Status", style="Status.TLabel", anchor="center", padding=5)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def display_next_word(self):
        """获取并显示下一个单词"""
        word_data = self.logic.get_next_word()
        if word_data:
            word, _ = word_data
            self.word_label.config(text=word)
            self.meaning_label.config(text="") # 清空释义
            
            # 重置按钮状态
            self.show_button.config(state=tk.NORMAL)
            self.known_button.config(state=tk.DISABLED)
            self.unknown_button.config(state=tk.DISABLED)
        else:
            self.word_label.config(text="恭喜！")
            self.meaning_label.config(text="所有单词都已掌握！")
            self.show_button.config(state=tk.DISABLED)
            self.known_button.config(state=tk.DISABLED)
            self.unknown_button.config(state=tk.DISABLED)
            
        self.update_status()

    def show_meaning(self):
        """显示当前单词的释义"""
        if self.logic.current_word:
            _, meaning = self.logic.get_next_word() # 再次获取以确保数据同步
            self.meaning_label.config(text=meaning)
            self.show_button.config(state=tk.DISABLED)
            self.known_button.config(state=tk.NORMAL)
            self.unknown_button.config(state=tk.NORMAL)
    
    def process_known(self):
        """处理“认识”的逻辑"""
        self.logic.mark_as_known()
        self.display_next_word()
        
    def process_unknown(self):
        """处理“不认识”的逻辑"""
        self.logic.mark_as_unknown()
        self.display_next_word()

    def update_status(self):
        """更新状态栏信息"""
        stats = self.logic.get_stats()
        self.status_label.config(text=stats)
        
    def on_closing(self):
        """关闭窗口时保存进度"""
        if messagebox.askokcancel("退出", "你确定要退出吗？进度将会被保存。"):
            self.logic.save_progress()
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WordMemorizerApp(root)
    root.mainloop()