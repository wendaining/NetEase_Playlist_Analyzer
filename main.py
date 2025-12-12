import sys
import os

# --- 标准的依赖检查 (Graceful Check) ---
try:
    # 尝试导入核心第三方库
    import pandas as pd
    import pyncm
    import pyncm.apis # 确保子模块也能被加载
    
except ImportError as e:
    # 如果缺少库，捕获错误并输出友好的提示信息
    print("=" * 60)
    print(f"❌ 启动失败：缺少必要的运行库。")
    print(f"错误详情: {e}")
    print("-" * 60)
    print("请按照以下步骤安装依赖：")
    print("\n1. 确保当前目录有 'requirements.txt' 文件")
    print("2. 在终端/命令行运行以下命令：")
    print("\n   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple")
    print("=" * 60)
    # 非正常退出，返回状态码 1
    input("按回车键退出...")
    sys.exit(1)

# ==========================================
#  下面是你的核心逻辑代码
# ==========================================
import re
import time
import glob

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

def select_files(min_count=1, max_count=None, msg=""):
    """交互式文件选择器，支持选择任意数量文件"""
    files = get_csv_files()
    if len(files) < min_count:
        print(f"\n[!] 错误: 当前目录下 'playlist_*.csv' 文件不足 {min_count} 个。")
        print("    -> 请先使用功能 [1] 下载歌单。")
        return None

    print("\n--- 本地已下载歌单 ---")
    for i, f in enumerate(files):
        print(f"[{i}] {f}")
    print("-" * 30)

    try:
        if min_count == 1 and max_count == 1:
            idx = int(input(f"请输入 1 个文件的序号: "))
            f = files[idx]
            return [(f, pd.read_csv(f, dtype={'id': str}))]
        else:
            if max_count:
                prompt = f"请输入 {min_count}-{max_count} 个文件的序号 (用空格分隔)"
            else:
                prompt = f"请输入至少 {min_count} 个文件的序号 (用空格分隔)"
            if msg:
                prompt = msg
            
            sel = input(f"{prompt}: ").split()
            if len(sel) < min_count:
                print(f"[!] 至少需要选择 {min_count} 个文件。")
                return None
            if max_count and len(sel) > max_count:
                print(f"[!] 最多只能选择 {max_count} 个文件。")
                return None
            
            result = []
            for idx_str in sel:
                idx = int(idx_str)
                f = files[idx]
                result.append((f, pd.read_csv(f, dtype={'id': str})))
            return result
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
    print("说明: 找出多个歌单中，完全是同一首歌（文件ID相同）的曲目。")
    
    data = select_files(min_count=2, msg="请输入至少2个文件的序号 (用空格分隔)")
    if not data: return input("按回车返回...")
    
    # 从第一个歌单开始，逐个取交集
    result_df = data[0][1]
    names = [data[0][0]]
    
    for i in range(1, len(data)):
        names.append(data[i][0])
        result_df = pd.merge(result_df, data[i][1], on='id', how='inner', suffixes=('', f'_{i}'))
    
    print(f"\n[结果] 共有 {len(result_df)} 首完全相同的歌。")
    
    if not result_df.empty:
        # 只保留基本信息列（来自第一个歌单）
        base_cols = ['id', 'title', 'artist', 'album', 'duration']
        # 找出实际存在的列
        out_cols = [col for col in base_cols if col in result_df.columns]
        out_df = result_df[out_cols]
        
        # 生成文件名
        name_parts = [n.replace("playlist_", "").replace(".csv", "") for n in names]
        out_name = f"交集_严格_{'_x_'.join(name_parts)}.csv"
        
        out_df.to_csv(out_name, index=False, encoding='utf_8_sig')
        print(f"已保存文件: {out_name}")
        
    input("\n按回车键返回...")

def module_fuzzy_intersection():
    print("\n>>> 功能: 智能模糊交集 (上下对照版)")
    print("说明: 清洗歌名后，将匹配成功的歌曲聚类展示，方便上下对比。")
    
    data = select_files(min_count=2, max_count=2)
    if not data: return input("按回车返回...")
    
    name1, df1 = data[0]
    name2, df2 = data[1]
    
    # 1. 清洗歌名
    df1['clean_title'] = df1['title'].apply(normalize_title)
    df2['clean_title'] = df2['title'].apply(normalize_title)
    
    # 2. 找出交集 (只获取两个歌单都有的 clean_title 列表)
    # intersection 是一个集合，比如 {'hello', '晴天'}
    common_clean_titles = set(df1['clean_title']).intersection(set(df2['clean_title']))
    
    if not common_clean_titles:
        print("\n[结果] 没有发现相似歌曲。")
        input("\n按回车键返回...")
        return

    # 3. 筛选数据 (只保留在交集里的歌)
    #isin() 函数判断是否在交集列表中
    result_df1 = df1[df1['clean_title'].isin(common_clean_titles)].copy()
    result_df2 = df2[df2['clean_title'].isin(common_clean_titles)].copy()
    
    # 4. 标记来源 (这样你才知道这行是 A 的还是 B 的)
    # 去掉文件名里的 .csv 后缀，让来源名字好看点
    source_name1 = name1.replace("playlist_", "").replace(".csv", "")
    source_name2 = name2.replace("playlist_", "").replace(".csv", "")
    
    result_df1['source'] = f"[A] {source_name1}"
    result_df2['source'] = f"[B] {source_name2}"
    
    # 5. 上下合并 (Concat)
    final_df = pd.concat([result_df1, result_df2])
    
    # 6. 【关键一步】排序
    # 先按 'clean_title' 排序，这样同名的歌就会聚在一起
    # 再按 'source' 排序，保证 A 歌单总是在 B 歌单上面
    final_df = final_df.sort_values(by=['clean_title', 'source'])
    
    # 7. 整理列顺序 (把 'clean_title' 放在第一列作为索引)
    cols = ['clean_title', 'source', 'title', 'artist', 'album', 'duration']
    final_df = final_df[cols]
    
    # 8. 保存
    count = len(common_clean_titles)
    print(f"\n[结果] 发现 {count} 组相似歌曲。")
    
    out_name = f"交集_对照视图_{source_name1}_x_{source_name2}.csv"
    final_df.to_csv(out_name, index=False, encoding='utf_8_sig')
    
    print(f"已保存文件: {out_name}")
    print("提示: 打开 Excel 后，第一列相同的行即为同一组匹配。")
        
    input("\n按回车键返回...")
    
def module_difference():
    print("\n>>> 功能: 差集/补集 (A中有但B中没有)")
    print("说明: 找出第一个歌单中有，但其他歌单中都没有的歌曲。")
    print("      支持严格模式(ID匹配)和模糊模式(歌名匹配)。")
    
    mode = input("\n请选择模式 [1]严格ID匹配 [2]模糊歌名匹配: ").strip()
    if mode not in ['1', '2']:
        print("[!] 无效选项")
        return input("按回车返回...")
    
    data = select_files(min_count=2, max_count=2, msg="请输入2个文件的序号 (用空格分隔): A B")
    if not data: return input("按回车返回...")
    
    name_a, df_a = data[0]
    name_b, df_b = data[1]
    
    if mode == '1':
        # 严格ID匹配
        # 找出在A中但不在B中的ID
        diff_df = df_a[~df_a['id'].isin(df_b['id'])]
        mode_str = "严格"
    else:
        # 模糊歌名匹配
        df_a['clean_title'] = df_a['title'].apply(normalize_title)
        df_b['clean_title'] = df_b['title'].apply(normalize_title)
        diff_df = df_a[~df_a['clean_title'].isin(df_b['clean_title'])]
        mode_str = "模糊"
    
    print(f"\n[结果] A中有但B中没有的歌曲: {len(diff_df)} 首")
    
    if not diff_df.empty:
        # 保留基本信息
        base_cols = ['id', 'title', 'artist', 'album', 'duration']
        out_cols = [col for col in base_cols if col in diff_df.columns]
        out_df = diff_df[out_cols]
        
        na_clean = name_a.replace("playlist_", "").replace(".csv", "")
        nb_clean = name_b.replace("playlist_", "").replace(".csv", "")
        out_name = f"差集_{mode_str}_{na_clean}_减_{nb_clean}.csv"
        
        out_df.to_csv(out_name, index=False, encoding='utf_8_sig')
        print(f"已保存文件: {out_name}")
    
    input("\n按回车键返回...")

def module_union():
    print("\n>>> 功能: 并集 (合并多个歌单并去重)")
    print("说明: 将多个歌单合并，去除重复歌曲。")
    print("      支持严格模式(ID去重)和模糊模式(歌名去重)。")
    
    mode = input("\n请选择模式 [1]严格ID去重 [2]模糊歌名去重: ").strip()
    if mode not in ['1', '2']:
        print("[!] 无效选项")
        return input("按回车返回...")
    
    data = select_files(min_count=2, msg="请输入至少2个文件的序号 (用空格分隔)")
    if not data: return input("按回车返回...")
    
    # 合并所有歌单
    all_dfs = []
    names = []
    for name, df in data:
        names.append(name)
        if mode == '2':  # 模糊模式需要添加清洗后的标题
            df['clean_title'] = df['title'].apply(normalize_title)
        all_dfs.append(df)
    
    # 合并所有数据
    union_df = pd.concat(all_dfs, ignore_index=True)
    
    original_count = len(union_df)
    
    if mode == '1':
        # 严格ID去重
        union_df = union_df.drop_duplicates(subset=['id'], keep='first')
        mode_str = "严格"
    else:
        # 模糊歌名去重
        union_df = union_df.drop_duplicates(subset=['clean_title'], keep='first')
        mode_str = "模糊"
    
    print(f"\n[结果] 合并前总计: {original_count} 首")
    print(f"        去重后保留: {len(union_df)} 首")
    print(f"        移除重复: {original_count - len(union_df)} 首")
    
    if not union_df.empty:
        # 保留基本信息
        base_cols = ['id', 'title', 'artist', 'album', 'duration']
        out_cols = [col for col in base_cols if col in union_df.columns]
        out_df = union_df[out_cols]
        
        name_parts = [n.replace("playlist_", "").replace(".csv", "") for n in names]
        out_name = f"并集_{mode_str}_{'_合_'.join(name_parts)}.csv"
        
        out_df.to_csv(out_name, index=False, encoding='utf_8_sig')
        print(f"已保存文件: {out_name}")
    
    input("\n按回车键返回...")

def module_internal_check():
    print("\n>>> 功能: 单歌单查重 (分组对照版)")
    print("说明: 找出歌单内“核心歌名”相同的歌曲，并聚类展示，方便你决定删哪首。")
    
    data = select_files(min_count=1, max_count=1)
    if not data: return input("按回车返回...")
    
    name, df = data[0]
    
    # 1. 计算清洗后的歌名 (作为查重依据)
    df['clean_title'] = df['title'].apply(normalize_title)
    
    # 2. 查找重复
    # keep=False 的意思是：所有重复的行都标记为 True (而不是保留第一个)
    # 比如有3首《晴天》，这3首都会被选出来
    dupes = df[df.duplicated(subset=['clean_title'], keep=False)].copy()
    
    if dupes.empty:
        print("\n[结果] 恭喜！该歌单非常干净，没有发现重复歌曲。")
    else:
        # 3. 【关键】排序
        # 按照 clean_title 排序，这样相同的歌就会在 Excel 里紧挨着显示
        dupes = dupes.sort_values(by=['clean_title', 'artist'])
        
        # 4. 整理列顺序
        # 把 clean_title 放在第一列，作为“组名”
        cols = ['clean_title', 'title', 'artist', 'album', 'duration', 'id']
        dupes = dupes[cols]
        
        count = len(dupes)
        unique_groups = dupes['clean_title'].nunique()
        print(f"\n[结果] 发现 {unique_groups} 组疑似重复歌曲，共 {count} 条记录。")
        
        # 5. 保存
        # 文件名处理一下
        simple_name = name.replace("playlist_", "").replace(".csv", "")
        out_name = f"查重_分组视图_{simple_name}.csv"
        
        dupes.to_csv(out_name, index=False, encoding='utf_8_sig')
        print(f"已保存文件: {out_name}")
        print("提示: 打开 Excel 后，第一列相同的行即为同一组，可直接对比删除。")
        
    input("\n按回车键返回...")

# ==========================================
#  主程序入口
# ==========================================

def main():
    while True:
        clear_screen()
        print("=" * 50)
        print("   网易云歌单集成工具")
        print("=" * 50)
        print(" [1] 下载歌单（支持 >1000 首）")
        print(" [2] 多歌单取交集（严格匹配）")
        print(" [3] 多歌单取交集（模糊歌名匹配）")
        print(" [4] 两歌单取差集（A有B没有）")
        print(" [5] 多歌单取并集（合并去重）")
        print(" [6] 单个歌单内部查重（模糊歌名匹配）")
        print(" [0] 退出")
        print("-" * 50)
        
        choice = input("请输入选项: ").strip()
        
        if choice == '1':
            module_crawler()
        elif choice == '2':
            module_strict_intersection()
        elif choice == '3':
            module_fuzzy_intersection()
        elif choice == '4':
            module_difference()
        elif choice == '5':
            module_union()
        elif choice == '6':
            module_internal_check()
        elif choice == '0':
            print("Bye~")
            break
        else:
            input("无效输入，按回车继续...")

if __name__ == "__main__":
    main()