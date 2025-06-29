下面是一份面向 2 人团队、工期 14 天的全新《课程设计任务书》示例，已把“英语听写（单词 + 句子）”“AI 接口释义”与“人均 ≥ 500 行代码”等要求全部体现。你只需把课程/姓名等信息替换即可直接交给老师。

⸻

任务名称

英语听写与词汇记忆系统（Word & Sentence Memorizer）

⸻

一、问题阐述与分析

项目	说明
1. 问题背景	六级/考研备考阶段，学生既要大规模记忆词汇，又需提升听力和长难句反应速度。市面 App 多联网依赖大厂服务，难以二次开发。
2. 应用意义	- 教学示范：展示 Python 在 GUI、音频处理、AI API 调用、数据持久化上的综合实践。- 学习价值：离线背词 + 本地听写，AI 实时释义、造句，提升英语综合能力。
3. 主要问题	1. 如何同时管理“单词”和“句子”两类复习队列。2. 如何在本地生成/缓存 TTS 音频并与 GUI 流程同步。3. 如何调用 Deepseek API 返回简洁释义、例句、同义词，并控制并发/缓存。


⸻

二、计划实施方案

周次	里程碑 & 主要任务	具体成果
D1-D3	需求细化，确定 CSV/JSON 数据格式；完成词库 / 句库解析 & 基础复习算法（随机 + 简化 SM-2）。	✅ CLI 单元测试通过；README 初始化
D4-D6	Listen 模块：接入 edge-tts（离线）和 sounddevice 播放；实现录入/比对；GUI 雏形（Tkinter Tab 页：Word / Sentence）。	✅ 最小可运行 GUI演示★ 中期检查
D7-D9	AIExplain 模块：封装 Deepseek API（函数 explain(term) & 缓存 SQLite）；GUI 中右侧弹窗显示释义/同义词/例句。	✅ 缓存命中率日志；错误重试机制
D10-D11	高级功能：• 错词重听• 统计面板（Matplotlib 嵌入 Tk）• 导入自定义词书向导	✅ Stats 页折线图 / 词云
D12	打包脚本：PyInstaller + --onefile（Win） & py2app（macOS）；生成 词库示例 3 k 词 + 500 句。	✅ 安装包 (.app / .exe)
D13-D14	报告 & PPT：系统架构图、数据结构/算法复杂度、性能测试；录制 3 min 演示视频。	✅ 报告 PDF + 视频★ 终期验收


⸻

三、拟采用的数据结构与算法

功能	数据结构 / 算法	复杂度	说明
词/句索引	dict[str, Dataclass]	O(1)	word → Meaning / Sentence → Translation
复习调度	deque + random.shuffle 或 heapq(权重)	O(1)/O(log n)	简化 SM-2
音频缓存	sqlite (key=url, val=blob)	O(1)	避免重复 TTS
AI 释义缓存	同上；TTL 字段	O(1)	控制 API 次数
统计分析	Counter、collections	O(n)	生成词频、错题 TOP-N


⸻

四、工作量说明

团队总行数 ≈ 1 300 行；单人 ≥ 650 行

模块	负责人	预计行数	关键文件
Core Logic (词/句 I/O、调度、持久化)	成员 A	≈ 300	logic/core.py
Listen Engine (TTS 播放、录音对比)	成员 B	≈ 200	audio/listen.py
AIExplain (Deepseek 调用 + 缓存)	成员 A	≈ 150	logic/ai.py
GUI (Tk Tabs, Stats, Threading)	成员 B	≈ 350	ui/main.py
打包 & 文档脚本、测试	A &B	≈ 300	scripts/build.py, tests/


⸻

五、工作计划 & 检查节点

日期	检查要点	验收标准
D6 (中期)	单词/句子听写闭环；数据可保存	演示 5 词 3 句；progress.json 生成
D12	AI 释义 + 统计面板	显示 Deepseek 返回内容 & 折线图刷新
D14	所有功能稳定；打包成功	课设报告 + 安装包 + 演示视频


⸻

六、成员与分工

成员	具体职责	关键成果
王 ×× (成员 A)	- 词/句数据层 & 调度算法- AIExplain 接口封装- 单元测试、报告算法章节	core.py, ai.py, tests/
张 ×× (成员 B)	- 听写音频引擎、TTS 缓存- Tkinter GUI (多标签/统计)- 打包脚本、用户手册	listen.py, ui/main.py, build.py

代码行数：两人各负责 ≥ 650 行（含注释 & 文档字符串），满足老师 “人均 ≥ 500 行” 要求。若行数偏差，按最终 Git 统计对等补充。

⸻

交付物清单
	1.	源码仓库：README、requirements.txt、.gitignore
	2.	多平台安装包：WordMemorizer.app、WordMemorizer.exe
	3.	词库/句库示例：data/words_cet6.csv、data/sentences_500.json
	4.	课设报告：PDF 4 000+ 字，含架构图、算法复杂度、测试数据、总结
	5.	演示视频：≤ 3 min，展示听写 + AI 释义 + 统计
	6.	PPT：答辩 10 页

⸻

本任务书覆盖了：
	•	问题分析、应用意义、主要技术难点
	•	两周实施计划与里程碑
	•	数据结构 & 算法说明
	•	成员分工与代码行数考核

