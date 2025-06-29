# 🚀 多平台发布指南

本文档说明如何为Windows、macOS和Linux构建和发布可执行版本。

## 📦 自动构建（推荐）

### GitHub Actions自动构建
项目已配置GitHub Actions，可自动为三个平台构建：

#### 🏷️ 创建发布版本
```bash
# 1. 提交所有更改
git add -A
git commit -m "准备发布 v1.0.0"

# 2. 创建版本标签
git tag v1.0.0

# 3. 推送到GitHub
git push origin main
git push origin v1.0.0
```

#### 🎯 自动构建流程
推送标签后，GitHub Actions会自动：
1. 在Windows、macOS、Linux上并行构建
2. 生成各平台的可执行文件
3. 创建GitHub Release
4. 上传压缩包供下载

#### 📥 下载地址
构建完成后，用户可在以下位置下载：
`https://github.com/BillWang-dev/word_memorizer/releases`

## 🔧 手动构建

### 本地构建（当前平台）
```bash
# macOS上构建macOS版本
python scripts/build.py --py2app

# 任何平台构建通用版本
python scripts/build.py
```

### 跨平台构建策略

#### 方法1：使用不同设备
- **Windows版本**: 在Windows电脑上运行build.py
- **macOS版本**: 在Mac上运行build.py --py2app
- **Linux版本**: 在Linux上运行build.py

#### 方法2：使用虚拟机
```bash
# 在macOS上使用虚拟机构建Windows版本
# 1. 安装VMware/VirtualBox + Windows
# 2. 在虚拟机中安装Python和依赖
# 3. 运行构建脚本
```

#### 方法3：使用Docker（实验性）
```bash
# 为Linux构建（在任何平台）
docker run --rm -v $(pwd):/app python:3.11 bash -c "
  cd /app && 
  pip install -r requirements-basic.txt &&
  python scripts/build.py
"
```

## 📋 构建产物说明

### 文件结构
```
dist/
├── WordMemorizer.exe        # Windows可执行文件
├── WordMemorizer.app/       # macOS应用包
├── WordMemorizer           # Linux可执行文件
├── data/                   # 词汇数据
├── README.md              # 使用说明
└── build_info.json       # 构建信息
```

### 平台特定要求

#### Windows (.exe)
- 目标：Windows 10+
- 大小：~50-80MB
- 依赖：内置所有依赖
- 运行：双击exe文件

#### macOS (.app)
- 目标：macOS 10.14+  
- 大小：~60-100MB
- 依赖：内置所有依赖
- 运行：双击app包
- 注意：可能需要在安全设置中允许运行

#### Linux (executable)
- 目标：Ubuntu 18.04+ / CentOS 7+
- 大小：~50-80MB
- 依赖：系统需要基础GUI库
- 运行：`./WordMemorizer`

## 🛠️ 分发准备

### 创建分发包
```bash
# 自动创建分发包（包含所有必要文件）
python scripts/create_distribution.py
```

### 发布检查清单
- [ ] 在目标平台测试可执行文件
- [ ] 验证所有功能正常工作
- [ ] 检查数据文件完整性
- [ ] 确认版本号正确
- [ ] 更新README和文档

## 📱 用户获取方式

### GitHub Releases（推荐）
1. 访问：`https://github.com/BillWang-dev/word_memorizer/releases`
2. 下载对应平台的压缩包
3. 解压并运行

### 直接下载链接
```markdown
## 下载链接

### Windows用户
[下载 WordMemorizer-Windows.zip](https://github.com/BillWang-dev/word_memorizer/releases/latest/download/WordMemorizer-Windows.zip)

### macOS用户  
[下载 WordMemorizer-macOS.zip](https://github.com/BillWang-dev/word_memorizer/releases/latest/download/WordMemorizer-macOS.zip)

### Linux用户
[下载 WordMemorizer-Linux.tar.gz](https://github.com/BillWang-dev/word_memorizer/releases/latest/download/WordMemorizer-Linux.tar.gz)
```

## 🔍 故障排除

### 构建失败
```bash
# 清理并重试
rm -rf build dist *.spec
python scripts/build.py
```

### 依赖问题
```bash
# 更新构建依赖
pip install --upgrade pyinstaller py2app

# 检查隐藏导入
python -c "import sys; print(sys.path)"
```

### 大小优化
在`scripts/build.py`中调整PyInstaller选项：
```python
# 排除不需要的模块
"--exclude-module", "matplotlib.tests",
"--exclude-module", "numpy.tests",
```

## 📊 版本管理

### 语义化版本
- `v1.0.0` - 主要版本
- `v1.1.0` - 功能更新  
- `v1.0.1` - Bug修复

### 发布周期
- **开发版**: 每周构建
- **测试版**: 每月发布
- **稳定版**: 按需发布

---

🎉 现在你可以轻松为所有平台构建和分发程序了！