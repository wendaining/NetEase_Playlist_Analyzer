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
    * **求歌单之间的补集**
* **内部查重**：一键扫描歌单内部的重复曲目，辅助清理。

### 安装与使用

1.  克隆仓库或下载源码：
    ```bash
    git clone https://github.com/wendaining/NetEase_Playlist_Analyzer.git
    cd NetEase_Playlist_Analyzer
    ```

1.  运行安装命令：
    
    ```
    pip install -r requirements.txt
    ```

2.  直接运行：
    ```bash
    python main.py
    ```

### ⚠️ 免责声明

本项目仅供 Python 学习与技术交流使用。请勿用于商业用途或大规模爬取。数据版权归网易云音乐及创作者所有。
