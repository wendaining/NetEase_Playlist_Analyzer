import sys
import subprocess
import os

def check_and_install_dependencies():
    """
    自动检测并安装缺少的库
    """
    # 这里列出你所有的第三方库
    required_packages = {
        'pandas': 'pandas', 
        'pyncm': 'pyncm'
        # 如果以后用了 openpyxl 或 requests 也可以加在这里
        # 格式为 '导入名': 'pip安装名'
    }
    
    missing = []
    
    # 1. 检查哪些包缺失
    for import_name, install_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(install_name)
    
    # 2. 如果有缺失，执行安装
    if missing:
        print("="*50)
        print(f"检测到缺少必要运行库: {', '.join(missing)}")
        print("正在尝试自动安装，请稍候...")
        print("="*50)
        
        try:
            # 使用当前运行的 python 环境对应的 pip 进行安装
            # -i https://pypi.tuna.tsinghua.edu.cn/simple 是使用清华镜像源，下载更快
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', *missing, 
                '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'
            ])
            print("\n[√] 依赖安装成功！正在启动程序...\n")
            
            # 3. 安装完成后重启脚本，确保库能被正确加载
            # 这一步是为了防止 Python 缓存了“没有这个包”的状态
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
        except subprocess.CalledProcessError:
            print("[!] 自动安装失败。")
            print(f"请手动打开终端运行: pip install {' '.join(missing)}")
            input("按回车键退出...")
            sys.exit(1)

# --- 在程序最开始执行检查 ---
check_and_install_dependencies()

import re
import time
import glob
import pandas as pd
import pyncm
import pyncm.apis

# ==========================================
#  工具函数 / 配置
# ==========================================

def clear_screen():
    """清屏函数，适配 Windows/Mac/Linux"""
    os.system('cls' if os.name == 'nt' else 'clear')

def sanitize_filename(name):
    """文件名清洗，去除非法字符"""
    return re.sub(r'[\\/:*?"<>|]', '_', str(name))

def parse_id(url):
    """从链接中提取数字ID"""
    match = re.search(r'id=(\d+)', url)
    if match: return match.group(1)
    if url.isdigit(): return url
    return None

def normalize_title(title):
    """
    【核心清洗逻辑】
    1. 转小写
    2. 去除括号及内容 (Live)/(中文版)等
    3. 去除连字符后缀 - Remix/- 弹唱等
    """
    if not isinstance(title, str): return ""
    
    # 1. 基础清洗
    core = title.lower()
    
    # 2. 去除括号 (包含全角和半角)
    core = re.sub(r'\s*[（\(].*?[）\)]', '', core)
    
    # 3. 去除连字符后缀 (激进模式: 只要有 - 就截断)
    if '-' in core:
        core = core.split('-')[0]
        
    return core.strip()

def get_csv_files():
    """获取当前目录下所有的 playlist_*.csv"""
    return glob.glob("playlist_*.csv")

def select_files(count=1):
    """交互式文件选择器"""
    files = get_csv_files()
    if len(files) < count:
        print(f"\n[!] 错误: 当前目录下 'playlist_*.csv' 文件不足 {count} 个。")
        print("    -> 请先使用功能 [1] 下载歌单。")
        return None

    print("\n--- 本地已下载歌单 ---")
    for i, f in enumerate(files):
        print(f"[{i}] {f}")
    print("-" * 30)

    try:
        if count == 1:
            idx = int(input(f"请输入 1 个文件的序号: "))
            f = files[idx]
            # 读取时强制 id 为 str
            return (f, pd.read_csv(f, dtype={'id': str}))
        
        elif count == 2:
            sel = input(f"请输入 2 个文件的序号 (用空格分隔，如 0 1): ").split()
            idx1, idx2 = int(sel[0]), int(sel[1])
            f1, f2 = files[idx1], files[idx2]
            return (f1, pd.read_csv(f1, dtype={'id': str}), 
                    f2, pd.read_csv(f2, dtype={'id': str}))
    except (ValueError, IndexError):
        print("[!] 输入无效，请重试。")
        return None

# ==========================================
#  核心功能模块
# ==========================================

def module_crawler():
    print("\n>>> 功能: 歌单下载为csv文件 | 支持>1000首)")
    raw = input("请输入歌单链接或ID: ").strip()
    pid = parse_id(raw)
    
    if not pid:
        print("[!] 无法识别 ID")
        return

    print(f"\n正在连接 API 获取歌单 [{pid}] 信息...")
    try:
        # 1. 获取歌单详情 (拿到所有 Track ID)
        playlist_info = pyncm.apis.playlist.GetPlaylistInfo(pid)
        
        # 解析元数据
        playlist_data = playlist_info['playlist']
        title = playlist_data['name']
        track_ids = [str(t['id']) for t in playlist_data['trackIds']]
        
        print(f"歌单名: 《{title}》")
        print(f"歌曲数: {len(track_ids)} 首")
        
        # 2. 分批获取详情 (每次500首，防止请求过大)
        all_songs = []
        batch_size = 500
        print("开始下载歌曲详情...")
        
        for i in range(0, len(track_ids), batch_size):
            chunk = track_ids[i : i + batch_size]
            print(f"  -> 处理进度: {i} - {min(i+batch_size, len(track_ids))} ...")
            
            details = pyncm.apis.track.GetTrackDetail(chunk)
            
            for song in details['songs']:
                try:
                    # 提取需要的字段
                    s_id = str(song['id'])
                    s_title = song['name']
                    # 歌手可能由多个，用 / 拼接
                    s_artist = "/".join([ar['name'] for ar in song['ar']])
                    # 专辑名
                    s_album = song['al']['name'] if song['al'] else ""
                    # 时长 (毫秒 -> mm:ss)
                    dt = song['dt']
                    s_duration = f"{dt//60000:02d}:{(dt%60000)//1000:02d}"
                    
                    all_songs.append({
                        "id": s_id,
                        "title": s_title,
                        "artist": s_artist,
                        "album": s_album,
                        "duration": s_duration
                    })
                except:
                    continue
            
            # 稍微停顿，防止被封IP
            time.sleep(0.2)

        # 3. 保存文件
        if all_songs:
            safe_title = sanitize_filename(title)
            filename = f"playlist_{safe_title}.csv"
            
            df = pd.DataFrame(all_songs)
            # 调整列顺序
            df = df[['id', 'title', 'artist', 'album', 'duration']]
            
            df.to_csv(filename, index=False, encoding='utf_8_sig')
            print(f"\n[成功] 已保存至: {filename}")
        else:
            print("[失败] 未能获取到歌曲数据。")

    except Exception as e:
        print(f"\n[错误] 发生异常: {e}")
        print("可能原因: 歌单不存在 / 私密歌单 / 网络问题")
    
    input("\n按回车键返回主菜单...")

def module_strict_intersection():
    print("\n>>> 功能: 严格交集 (ID 完全一致)")
    print("说明: 找出两个歌单中，完全是同一首歌（文件ID相同）的曲目。")
    
    data = select_files(count=2)
    if not data: return input("按回车返回...")
    
    name1, df1, name2, df2 = data
    
    # Merge
    merged = pd.merge(df1, df2, on='id', how='inner', suffixes=('_A', '_B'))
    
    print(f"\n[结果] 共有 {len(merged)} 首完全相同的歌。")
    
    if not merged.empty:
        # 整理输出列
        out_cols = ['id', 'title_A', 'artist_A', 'album_A']
        out_df = merged[out_cols].rename(columns={
            'title_A': 'title', 'artist_A': 'artist', 'album_A': 'album'
        })
        
        # 生成文件名
        n1_clean = name1.replace("playlist_", "").replace(".csv", "")
        n2_clean = name2.replace("playlist_", "").replace(".csv", "")
        out_name = f"交集_严格_{n1_clean}_x_{n2_clean}.csv"
        
        out_df.to_csv(out_name, index=False, encoding='utf_8_sig')
        print(f"已保存文件: {out_name}")
        
    input("\n按回车键返回...")

def module_fuzzy_intersection():
    print("\n>>> 功能: 智能模糊交集 (忽略版本/Live后缀)")
    print("说明: 清洗歌名（去括号、去后缀、忽略大小写）后进行匹配。")
    
    data = select_files(count=2)
    if not data: return input("按回车返回...")
    
    name1, df1, name2, df2 = data
    
    # 1. 应用清洗逻辑
    df1['clean_title'] = df1['title'].apply(normalize_title)
    df2['clean_title'] = df2['title'].apply(normalize_title)
    
    # 2. 匹配 (使用 清洗后的歌名 进行连接)
    # 这里我们只 merge clean_title，不 merge artist，
    # 但会在结果里列出两边的 artist 供人工排查 "同名不同人" 的情况
    merged = pd.merge(df1, df2, on='clean_title', how='inner', suffixes=('_A', '_B'))
    
    print(f"\n[结果] 共有 {len(merged)} 首相似歌曲。")
    
    if not merged.empty:
        # 整理输出列：保留双方原始标题和歌手，方便核对
        cols = ['clean_title', 'title_A', 'title_B', 'artist_A', 'artist_B', 'album_A', 'album_B']
        out_df = merged[cols]
        
        n1_clean = name1.replace("playlist_", "").replace(".csv", "")
        n2_clean = name2.replace("playlist_", "").replace(".csv", "")
        out_name = f"交集_模糊_{n1_clean}_x_{n2_clean}.csv"
        
        out_df.to_csv(out_name, index=False, encoding='utf_8_sig')
        print(f"已保存文件: {out_name}")
        print("提示: 请打开 CSV 核对 'artist_A' 和 'artist_B' 列以排除同名不同曲。")
        
    input("\n按回车键返回...")

def module_internal_check():
    print("\n>>> 功能: 单歌单查重")
    print("说明: 在一个歌单内查找歌名（清洗后）重复的歌曲。")
    
    data = select_files(count=1)
    if not data: return input("按回车返回...")
    
    name, df = data
    
    # 清洗
    df['clean_title'] = df['title'].apply(normalize_title)
    
    # 查找重复 keep=False 表示标记所有重复项
    dupes = df[df.duplicated(subset=['clean_title'], keep=False)]
    
    if dupes.empty:
        print("\n[结果] 没有发现重复歌曲。")
    else:
        print(f"\n[结果] 发现 {len(dupes)} 条重复/相似记录。")
        dupes = dupes.sort_values(by='clean_title')
        
        out_name = f"查重结果_{name}"
        dupes.to_csv(out_name, index=False, encoding='utf_8_sig')
        print(f"详细列表已保存至: {out_name}")
        
    input("\n按回车键返回...")

# ==========================================
#  主程序入口
# ==========================================

def main():
    while True:
        clear_screen()
        print("=" * 40)
        print("   网易云歌单集成工具")
        print("=" * 40)
        print(" [1] 下载歌单 (支持 >1000 首)")
        print(" [2] 两个歌单取交集 (严格 ID 匹配)")
        print(" [3] 两个歌单取交集 (智能 歌名匹配)")
        print(" [4] 单个歌单内部查重")
        print(" [0] 退出")
        print("-" * 40)
        
        choice = input("请输入选项: ").strip()
        
        if choice == '1':
            module_crawler()
        elif choice == '2':
            module_strict_intersection()
        elif choice == '3':
            module_fuzzy_intersection()
        elif choice == '4':
            module_internal_check()
        elif choice == '0':
            print("Bye~")
            break
        else:
            input("无效输入，按回车继续...")

if __name__ == "__main__":
    main()