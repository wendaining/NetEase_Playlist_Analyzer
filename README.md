# NetEase Playlist Analyzer (网易云歌单助手)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

**本程序全程vibe coding生成**

## 中文说明

**网易云歌单助手** 是一个轻量级、交互式的 Python 工具，提供强大的本地数据分析功能。

无论是为了备份歌单，还是寻找两个人的共同喜好，这个工具都能帮你轻松搞定。

### 核心功能

* 基于 API (pyncm) 获取数据，轻松爬取超过 1000 首歌曲的超大歌单。
* 自动生成 `CSV` 文件，包含 ID、歌名、歌手、专辑、时长。
* **支持智能匹配**：采用简单的模糊匹配算法，自动处理 `(Live)`、`- Remix`、`（中文版）` 等后缀，准确识别同一首歌。
* **集合运算**：有两种
    * **严格交集**：基于文件 ID，找出完全一致的歌曲。
    * **模糊交集**：基于清洗后的歌名，找出“虽然版本不同但其实是同一首”的歌。
* **内部查重**：一键扫描歌单内部的重复曲目，辅助清理。

### 安装与使用

本程序内置了**依赖自动检测**功能。你不需要手动安装复杂的库，只要你的电脑有 Python 环境。

1.  克隆仓库或下载源码：
    ```bash
    git clone https://github.com/wendaining/NetEase_Playlist_Analyzer.git
    cd NetEase_Playlist_Analyzer
    ```

2.  直接运行：
    ```bash
    python main.py
    ```
    *程序会自动检测并安装`pyncm`等必要依赖。*

### 使用指南

1.  **下载歌单**：选择功能 `[1]`，粘贴网易云歌单链接（或分享链接），程序会自动保存为 CSV（格式为`playlist_歌单名.csv`）。
2.  **数据分析**：确保目录下有两个以上的 CSV 文件，选择功能 `[2]` 或 `[3]` 进行交集分析。
3.  **结果查看**：所有分析结果会自动生成新的 CSV 文件保存在当前目录。

### ⚠️ 免责声明

本项目仅供 Python 学习与技术交流使用。请勿用于商业用途或大规模爬取。数据版权归网易云音乐及创作者所有。
