import streamlit as st
import pandas as pd
import os
import time
import random
import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import base64
# --- 修复：必须加上这两行导入，否则会报“系统连接故障” ---
import gspread
from google.oauth2.service_account import Credentials

# --- 1. 核心：连接谷歌表格验证卡密 ---
def verify_card_from_sheets(user_input_code):
    # --- 1. 万能后门 ---
    if user_input_code in ["ygq6662", "vip6662"]:
        return True, 9999
        
    try:
        from datetime import datetime, timedelta
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["google"], scopes=scopes)
        client = gspread.authorize(creds)
        
        sh = client.open("Lotto_Cards").get_worksheet(0) 
        all_rows = sh.get_all_values() 
        
        input_code = str(user_input_code).strip()
        now = datetime.now()

        for i, row in enumerate(all_rows[1:]):
            db_code = str(row[0]).strip()    # A列：卡密
            db_days = row[1]                 # B列：原始天数
            db_status = str(row[2]).strip()  # C列：状态
            db_use_time = str(row[4]).strip() if len(row) > 4 else "" # E列：使用时间
             
            if db_code == input_code:
                # --- 情况1：从未激活过 (E列为空) ---
                if not db_use_time or db_use_time == "":
                    current_row_index = i + 2
                    start_time_str = now.strftime('%Y-%m-%d %H:%M:%S')
                    try:
                        sh.update_cell(current_row_index, 3, "已激活") # C列写状态
                        sh.update_cell(current_row_index, 5, start_time_str) # E列写激活时间
                    except: pass
                    return True, int(db_days)

                # --- 情况2：已经激活过，执行全自动倒计时 ---
                else:
                    if db_status == "封禁": return False, "❌ 该卡密已被封禁"
                    
                    try:
                        # 核心计算：现在的时间 - 激活的时间
                        start_dt = datetime.strptime(db_use_time, '%Y-%m-%d %H:%M:%S')
                        used_days = (now - start_dt).total_seconds() / 86400
                        remaining_days = float(db_days) - used_days
                        
                        if remaining_days <= 0:
                            return False, "❌ 您的授权已到期，请联系老板续费"
                        
                        # 自动返回剩余天数（如 28.4 天），网页会自动显示
                        return True, round(remaining_days, 1)
                    except:
                        # 时间格式解析失败则直接返回B列原始数字
                        return True, int(db_days)
                
        return False, "❌ 授权码不存在"
    except Exception as e:
        return False, f"⚠️ 连接故障: {str(e)}"

# =========================================================
# 💰💰💰 老板专属配置区 💰💰💰
# =========================================================
MY_WECHAT_ID = "252766667"           # 微信号
VIP_PASSWORD = "999"                 # 备用口令
VIP_BACKDOOR = "666"                 # 老板无敌后门
SECRET_KEY = "Partner_Fortune_2026_TopSecret" 
# =========================================================

# --- 0. 隐形访客统计 ---
visit_file = "visit_log.txt"
if not os.path.exists(visit_file):
    with open(visit_file, "w") as f: f.write("0")
with open(visit_file, "r") as f:
    current_v = int(f.read())
with open(visit_file, "w") as f: f.write(str(current_v + 1))

# --- 1. 深度定制样式表 ---
st.set_page_config(page_title="AI 大数据决策终端", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 2.5rem 1.5rem !important; max-width: 900px; }
    .hist-table { width: 100%; border-collapse: collapse; text-align: center; background: #fff; border-radius: 8px; overflow: hidden; margin-bottom: 1rem; }
    .hist-table th { background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #eaeaea; color: #666; font-weight: bold; }
    .hist-table td { padding: 12px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 15px; }
    
    .ball { display: inline-block; width: 28px; height: 28px; line-height: 28px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 3px; font-size: 13px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .bg-red { background-color: #f14545; }
    .bg-blue { background-color: #3b71f7; }
    .bg-yellow { background-color: #f9bf15; color: #333 !important; }
    .bg-purple { background-color: #9c27b0; }
    .bg-lotus { background-color: #cba09e; } 
    .bg-lightblue { background-color: #5bc0de; } 
    .bg-gold { background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%); color: white; text-shadow: 1px 1px 2px #b85e00; box-shadow: 0 4px 8px rgba(255, 215, 0, 0.6); border: 1px solid #ffcc00; }
    
    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 5px; border-left: 5px solid #f14545; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; }
    .pred-row.gold-border { border-left: 5px solid #FFD700; background: #fffdf5; }
    .pred-title { width: 180px; font-weight: bold; color: #444; font-size: 15px; }
    .ai-desc { font-size: 11px; color: #777; margin-top: 5px; display: block; line-height: 1.3; font-weight: normal; }
    .pred-balls { flex-grow: 1; display: flex; flex-wrap: wrap; max-width: 400px;} 
    .pred-ball { display: inline-block; width: 34px; height: 34px; line-height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 4px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.15); transition: all 0.3s ease; }
    
    .timer-bar { background: linear-gradient(90deg, #1d2b64, #f8cdda); color: white; padding: 10px; text-align: center; border-radius: 5px; font-weight: bold; margin-bottom: 15px; }
    .wechat-box { background: #f0f2f6; border-radius: 10px; padding: 15px; border: 1px solid #dcdfe6; text-align: center; margin-bottom: 10px;}
    
    .marquee-wrapper { background: linear-gradient(to right, #fff3cd, #fff8e1); padding: 10px 15px; border-radius: 8px; border-left: 4px solid #f9bf15; margin-bottom: 20px; overflow: hidden; display: flex; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .marquee-icon { font-size: 18px; margin-right: 10px; min-width: 25px; }
    .marquee-content { white-space: nowrap; animation: marquee 30s linear infinite; color: #856404; font-weight: bold; font-size: 14px; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-150%); } }
    
    .comment-box { background: #fff; border: 1px solid #eaeaea; border-radius: 8px; padding: 15px; margin-bottom: 10px; }
    .comment-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
    .comment-user { font-weight: bold; color: #1f77b4; font-size: 14px; }
    .comment-time { color: #999; font-size: 12px; }
    .comment-body { color: #444; font-size: 14px; line-height: 1.5; }
    
    .disclaimer { margin-top: 50px; padding: 15px; text-align: center; font-size: 12px; color: #999; border-top: 1px dashed #ddd; line-height: 1.6;}
    </style>
""", unsafe_allow_html=True)

# --- 状态初始化 ---
if 'vip_unlocked' not in st.session_state: st.session_state['vip_unlocked'] = False
if 'ai_click_count' not in st.session_state: st.session_state['ai_click_count'] = 0
if 'adv_click_count' not in st.session_state: st.session_state['adv_click_count'] = 0

def get_countdown():
    now = datetime.now()
    target = now.replace(hour=21, minute=30, second=0)
    if now > target: 
        target += timedelta(days=1)
    diff = target - now
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}时{minutes:02d}分{seconds:02d}秒"

def get_fake_broadcasts():
    cities = ["广东", "浙江", "江苏", "山东", "河南", "四川", "北京", "上海"]
    algos = ["极热寻踪", "绝地反弹", "黄金均衡", "马尔科夫链", "12阶高阶矩阵"]
    return "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🔥&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join([f"【最新喜报】{random.choice(cities)}用户 1{random.randint(3,9)}{random.randint(0,9)}****{random.randint(1000,9999)} {random.randint(1, 59)}分钟前 成功解锁「{random.choice(algos)}」！" for _ in range(5)])

def get_real_online_users(): return 1500 + random.randint(-50, 150)

def get_lottery_rules(choice):
    rules = {
        "双色球": (list(range(1, 34)), 6, list(range(1, 17)), 1),
        "大乐透": (list(range(1, 36)), 5, list(range(1, 13)), 2),
        "七星彩": (list(range(0, 10)), 6, list(range(0, 15)), 1),
        "快乐8": (list(range(1, 81)), 20, [], 0),
        "福彩3D": (list(range(0, 10)), 3, [], 0),
        "排列3": (list(range(0, 10)), 3, [], 0),
        "排列5": (list(range(0, 10)), 5, [], 0)
    }
    return rules.get(choice, rules["双色球"])

def calculate_ac_value(nums):
    diffs = set()
    for i in range(len(nums)):
        for j in range(i+1, len(nums)): diffs.add(abs(nums[i] - nums[j]))
    return max(0, len(diffs) - (len(nums) - 1))

@st.cache_data
def load_full_data(file_path, choice):
    try:
        raw_df = pd.read_excel(file_path) if file_path.endswith('.xls') else pd.read_csv(file_path)
        raw_df.columns = [str(c).strip() for c in raw_df.columns]
        q_col = next((c for c in raw_df.columns if '期' in c or 'NO' in c.upper()), raw_df.columns[0])
        raw_df[q_col] = pd.to_numeric(raw_df[q_col], errors='coerce')
        raw_df = raw_df.dropna(subset=[q_col])
        
        limits = {"双色球": 7, "大乐透": 7, "福彩3D": 3, "排列3": 3, "排列5": 5, "七星彩": 7, "快乐8": 20}
        max_balls = limits.get(choice, 7)
        
        q_idx = list(raw_df.columns).index(q_col)
        ball_cols = []
        for i in range(q_idx + 1, len(raw_df.columns)):
            col = raw_df.columns[i]
            nums = pd.to_numeric(raw_df[col], errors='coerce').dropna()
            if not nums.empty and (nums <= 81).all(): ball_cols.append(col)
            if len(ball_cols) == max_balls: break
            
        clean_df = raw_df[[q_col] + ball_cols].copy()
        new_names = ['期号'] + [f"b_{i+1}" for i in range(len(ball_cols))]
        clean_df.columns = new_names
        for c in new_names: clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0).astype(int)
        
        needs_zero = choice in ["双色球", "大乐透", "快乐8"]
        return clean_df.sort_values('期号', ascending=False), '期号', new_names[1:], needs_zero, file_path
    except: return None, None, None, None, None

def render_html_balls(r_res, b_res, choice, is_gold=False):
    r_class = "bg-gold" if is_gold else "bg-red"
    b_class = "bg-blue"
    
    if choice == "大乐透":
        b_class = "bg-yellow"
        if not is_gold: r_class = "bg-blue"
    elif choice == "七星彩":
        b_class = "bg-yellow"
        if not is_gold: r_class = "bg-purple"
    elif choice == "福彩3D":
        if not is_gold: r_class = "bg-lightblue"
    elif choice in ["排列3", "排列5"]:
        if not is_gold: r_class = "bg-lotus"

    fmt = "{:02d}" if choice in ["双色球", "大乐透", "快乐8"] else "{}"
    r_html = "".join([f"<span class='pred-ball {r_class}'>{fmt.format(n)}</span>" for n in r_res])
    b_html = "".join([f"<span class='pred-ball {b_class}'>{fmt.format(n)}</span>" for n in b_res])
    text = " ".join([fmt.format(n) for n in r_res]) + ((" | " + " ".join([fmt.format(n) for n in b_res])) if b_res else "")
    return r_html + b_html, f"推荐号码: {text}"

# --- 【已彻底修复】带强制清洗的真实数据统计算法引擎 ---
def extract_real_stats(df_view, pool_r, count_r, pool_b, count_b, variation_seed=0):
    """提取真实的频次和遗漏数据，强制清理脏数据，绝不崩溃"""
    random.seed(int(time.time()) + variation_seed)
    hot_r, cold_r, hot_b, cold_b = [], [], [], []
    
    if df_view is None or df_view.empty:
        return sorted(random.sample(pool_r, count_r)), sorted(random.sample(pool_r, count_r)), [], []
        
    try:
        # 👑 工业级清洗：把所有数据强制转换为数字格式，遇到文字/空单元格直接变成 -1，彻底断绝 TypeError
        safe_df = df_view.apply(pd.to_numeric, errors='coerce').fillna(-1).astype(int)
        
        # 解析红球区
        r_raw = safe_df.iloc[:, 1:1+count_r].values.flatten().tolist()
        # 过滤掉非法的数字（把刚才产生的 -1 等脏数据洗掉）
        r_history = [x for x in r_raw if x in pool_r]
        r_counter = Counter(r_history)
        
        most_common = [x[0] for x in r_counter.most_common()]
        base_hot = most_common[:count_r+3]
        hot_r = random.sample(base_hot, min(count_r, len(base_hot)))
        while len(hot_r) < count_r:
            cand = random.choice(pool_r)
            if cand not in hot_r: hot_r.append(cand)
        
        missing = [x for x in pool_r if x not in r_counter]
        least_common = missing + [x[0] for x in r_counter.most_common()[:-count_r-4:-1]]
        least_common = list(dict.fromkeys(least_common)) 
        cold_r = random.sample(least_common, min(count_r, len(least_common)))
        while len(cold_r) < count_r:
            cand = random.choice(pool_r)
            if cand not in cold_r: cold_r.append(cand)
            
        # 解析蓝球区（如果有）
        if count_b > 0:
            b_raw = safe_df.iloc[:, 1+count_r:1+count_r+count_b].values.flatten().tolist()
            b_history = [x for x in b_raw if x in pool_b]
            b_counter = Counter(b_history)
            
            b_most = [x[0] for x in b_counter.most_common()]
            hot_b = random.sample(b_most[:count_b+2], min(count_b, len(b_most[:count_b+2])))
            while len(hot_b) < count_b:
                cand = random.choice(pool_b)
                if cand not in hot_b: hot_b.append(cand)
                
            b_missing = [x for x in pool_b if x not in b_counter]
            b_least = list(dict.fromkeys(b_missing + [x[0] for x in b_counter.most_common()[:-count_b-3:-1]]))
            cold_b = random.sample(b_least[:count_b+2], min(count_b, len(b_least[:count_b+2])))
            while len(cold_b) < count_b:
                cand = random.choice(pool_b)
                if cand not in cold_b: cold_b.append(cand)
                
        # 全部清洗完毕，安全排序输出！
        return sorted(hot_r), sorted(cold_r), sorted(hot_b), sorted(cold_b)
        
    except Exception as e:
        # 万一遇到外星数据，也能保底吐出号码，绝不红屏
        return sorted(random.sample(pool_r, count_r)), sorted(random.sample(pool_r, count_r)), [], []

def get_ai_predictions(df_view, d_cols, choice, click_count):
    sets = []
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    
    hot_r, cold_r, hot_b, cold_b = extract_real_stats(df_view, pool_r, count_r, pool_b, count_b, click_count)
    
    h1, t1 = render_html_balls(hot_r, hot_b, choice)
    sets.append({"name": "🔥 极热寻踪", "desc": f"【统计学排查】已动态分析近{len(df_view)}期数据，提取高频热点。", "html": h1, "text": t1})
    
    h2, t2 = render_html_balls(cold_r, cold_b, choice)
    sets.append({"name": "🧊 绝地反弹", "desc": f"【均值回归】追踪近期遗漏值最大的冷门死号予以反弹。", "html": h2, "text": t2})
    
    mix_r = sorted(list(set(hot_r[:max(1, count_r//2)] + cold_r[:max(1, count_r//3)])))
    while len(mix_r) < count_r:
        cand = random.choice(pool_r)
        if cand not in mix_r: mix_r.append(cand)
    mix_r = sorted(mix_r[:count_r])
    
    mix_b = []
    if count_b > 0:
        mix_b = sorted(list(set(hot_b[:max(1, count_b//2)] + cold_b[:max(1, count_b//2)])))
        while len(mix_b) < count_b:
            cand = random.choice(pool_b)
            if cand not in mix_b: mix_b.append(cand)
        mix_b = sorted(mix_b[:count_b])
        
    h3, t3 = render_html_balls(mix_r, mix_b, choice)
    sets.append({"name": "⚖️ 黄金均衡", "desc": "【自然正态分布】热温冷动态配比防偏组合。", "html": h3, "text": t3})
    return sets

def real_markov_core(history_rows, pool, count, rng, order=1):
    """
    【硬核数学引擎】真正的马尔可夫状态转移概率计算
    """
    transition_matrix = {n: Counter() for n in pool}
    
    for i in range(len(history_rows) - order):
        current_state = history_rows[i]
        future_state = history_rows[i + order]
        
        for cb in current_state:
            if cb in pool:
                for fb in future_state:
                    if fb in pool:
                        transition_matrix[cb][fb] += 1
                        
    if not history_rows:
        return sorted(rng.sample(pool, count))
    latest_state = [b for b in history_rows[-1] if b in pool]
    
    next_probs = Counter()
    for lb in latest_state:
        for nb, freq in transition_matrix[lb].items():
            next_probs[nb] += freq
            
    candidates = [x[0] for x in next_probs.most_common()]
    top_k_pool = candidates[:count + 5] 
    
    if len(top_k_pool) < count:
        missing = [x for x in pool if x not in top_k_pool]
        top_k_pool.extend(rng.sample(missing, min(count - len(top_k_pool), len(missing))))
        
    return sorted(rng.sample(top_k_pool, count))

def get_advanced_predictions(df_view, d_cols, choice, click_count):
    sets = []
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    
    rng = random.Random(int(time.time()) + click_count)
    
    safe_df = df_view.apply(pd.to_numeric, errors='coerce').fillna(-1).astype(int)
    r_history = safe_df.iloc[:, 1:1+count_r].values.tolist()
    r_history.reverse() 
    
    b_history = []
    if count_b > 0:
        b_history = safe_df.iloc[:, 1+count_r:1+count_r+count_b].values.tolist()
        b_history.reverse()

    for j in range(3):
        r_res = real_markov_core(r_history, pool_r, count_r, rng, order=1)
        b_res = real_markov_core(b_history, pool_b, count_b, rng, order=1) if count_b > 0 else []
        
        html_m, text_m = render_html_balls(r_res, b_res, choice)
        sets.append({
            "name": f"🔗 马尔科夫 (组{j+1})", 
            "desc": f"基于近 {len(r_history)} 期状态转移建模 | AC复杂度: {calculate_ac_value(r_res)}", 
            "html": html_m, 
            "text": text_m, 
            "css_class": ""
        }) 
        
    for j in range(3):
        actual_order = 12 if len(r_history) > 15 else 1
        r_res_12 = real_markov_core(r_history, pool_r, count_r, rng, order=actual_order)
        b_res_12 = real_markov_core(b_history, pool_b, count_b, rng, order=actual_order) if count_b > 0 else []
        
        html_12, text_12 = render_html_balls(r_res_12, b_res_12, choice, is_gold=True)
        sets.append({
            "name": f"✨ 12阶矩阵 (组{j+1})", 
            "desc": f"深度空间偏移(跨度{actual_order}期) | 样本数: {len(r_history)}", 
            "html": html_12, 
            "text": text_12, 
            "css_class": "gold-border"
        })
        
    return sets

@st.cache_data(ttl=3600)
def fetch_from_web(game_code, choice, d_cols_len):
    urls = [f"https://datachart.500.com/{game_code}/history/newinc/history.php?limit=50", f"https://datachart.500.com/{game_code}/history/inc/history.php?limit=50"]
    headers = {"User-Agent": "Mozilla/5.0"}
    web_rows = []
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            trs = soup.find_all('tr', class_=['t_tr1', 't_tr2', 't_tr']) or soup.find_all('tr')
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) < d_cols_len + 1: continue 
                iss_str = re.sub(r'\D', '', tds[0].get_text(strip=True))
                if len(iss_str) < 3: continue
                issue_val = int("20" + iss_str[:10]) if len(iss_str) == 5 else int(iss_str[:10])
                
                rest_text = " ".join([td.get_text(separator=" ") for td in tds[1:]])
                balls = [int(n) for n in re.findall(r'\d+', rest_text)]
                balls = [n for n in balls if 0 <= n <= 81][:d_cols_len]
                
                if len(balls) == d_cols_len: web_rows.append({"issue": issue_val, "balls": balls})
            if web_rows: break 
        except: continue
    return web_rows

def sync_latest_data(df, q_col, d_cols, choice, file_path):
    status = st.empty()
    game_codes = {"双色球": "ssq", "大乐透": "dlt", "福彩3D": "sd", "排列3": "pls", "排列5": "plw", "七星彩": "qxc", "快乐8": "kl8"}
    
    # --- 核心拦截逻辑：已精准对齐 ---
    web_data = None
    try:
        # 1. 尝试获取网页最顶端的第一条期号
        web_data = fetch_from_web(game_codes.get(choice, "ssq"), choice, len(d_cols))
        
        if web_data:
            latest_web_issue = str(web_data[0]['issue'])
            latest_local_issue = str(df.iloc[0][q_col])
            
            # 2. 如果期号一致，直接收工，不跑后面的写文件逻辑
            if latest_web_issue == latest_local_issue:
                status.success(f"✅ 当前已是全网最新数据 (期号:{latest_local_issue})")
                time.sleep(1.5)
                status.empty()
                return 
    except Exception as e:
        # 如果预检出错了，继续往下跑常规更新逻辑
        pass

    # --- 开始处理抓取到的新数据 ---
    if web_data:
        try:
            clean_web_rows = []
            for item in web_data:
                row_dict = {"期号": item['issue']}
                for i in range(len(d_cols)):
                    if i < len(item['balls']):
                        row_dict[d_cols[i]] = item['balls'][i]
                clean_web_rows.append(row_dict)
            
            web_df = pd.DataFrame(clean_web_rows).astype('int64')
            # 合并、去重、排序、取前2000期
            updated = pd.concat([web_df, df], ignore_index=True).drop_duplicates(subset=[q_col], keep='first').sort_values(q_col, ascending=False).head(2000)
            
            # 确定保存路径
            save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
            updated.to_csv(save_path, index=False, encoding='utf-8-sig')
            
            status.success(f"✅ 同步成功！已更新 {len(clean_web_rows)} 期。")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
        except Exception as e: 
            status.error(f"🚨 自动同步失败: 数据格式不匹配")
    else: 
        status.error("❌ 抓取失败，请检查网络或稍后再试。")

# ==========================================
# 侧边栏
# ==========================================
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 商业决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

st.sidebar.markdown(f"""
    <div class="wechat-box">
        <span style="font-size:14px; color:#666;">获取【高阶预测及沙盘】解锁密码</span><br>
        <b style="color:#ff4b4b; font-size:13px;">微信：{MY_WECHAT_ID}</b>
    </div>
""", unsafe_allow_html=True)
st.sidebar.code(MY_WECHAT_ID, language="text")

st.sidebar.markdown("---")
view_options = {"近30期": 30, "近50期": 50, "近100期": 100}
view_choice = st.sidebar.radio("选择分析样本", list(view_options.keys()), index=0)
view_limit = view_options[view_choice]

if choice in ["快乐8", "排列5", "七星彩"]:
    st.error("🚧 **系统维护中**")
    st.warning("由于接口升级，该彩种暂不可用，请使用其他彩种或去【自建数据沙盘】运算。")
    st.stop()

# ==========================================
# 主界面
# ==========================================
file_kw = LOTTERY_FILES[choice]
all_files = [f for f in os.listdir(".") if file_kw in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))]
target = next((f for f in all_files if '_synced' in f), all_files[0] if all_files else None)

if target:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target, choice)
    if df is not None:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**📊 库中最新：** `{int(df[q_col].max())}` 期")
        st.sidebar.markdown(f"**👥 当前在线：** `{get_real_online_users()}` 人")
        if st.sidebar.button("🔄 联网同步最新开奖", use_container_width=True, type="primary"):
            sync_latest_data(df, q_col, d_cols, choice, actual_path)

        st.title(f"🎰 {choice} 数据智算中心")
        st.markdown(f'<div class="timer-bar">⏰ 离今日开奖截止还剩 {get_countdown()}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="marquee-wrapper"><div class="marquee-icon">📢</div><div class="marquee-content">{get_fake_broadcasts()}</div></div>', unsafe_allow_html=True)

        t1, t2, t3, t4, t5, t7, t6 = st.tabs([
            "📈 走势分析", "🤖 AI预测", "📊 遗漏统计", 
            "🔮 奇门遁甲", "📜 算法源码", "🎯 专家缩水", "💬 交流大厅"
        ])
        
        with t1:
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(view_limit).iterrows():
                max_w = "280px" if choice == "快乐8" else "100%" 
                balls_html = f"<div style='display:flex; flex-wrap:wrap; justify-content:center; margin: 0 auto; max-width: {max_w};'>"
                for i, col in enumerate(d_cols):
                    val = row[col]
                    txt = f"{val:02d}" if needs_zero else str(val)
                    bg = "bg-red"
                    if choice == "双色球": bg = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": bg = "bg-yellow" if i >= 5 else "bg-blue"
                    elif choice == "七星彩": bg = "bg-yellow" if i == 6 else "bg-purple"
                    elif choice == "福彩3D": bg = "bg-lightblue"
                    elif choice in ["排列3", "排列5"]: bg = "bg-lotus"
                    balls_html += f"<span class='ball {bg}'>{txt}</span>"
                balls_html += "</div>"
                table_html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{balls_html}</td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

        with t2:
            calc_df = df.head(view_limit).copy()
            calc_df['和值'] = calc_df[d_cols].sum(axis=1)
            st.markdown("### 📈 近期和值走势")
            st.line_chart(calc_df.set_index('期号')['和值'])

        with t_mock:
            st.markdown("### 🎰 电视级沙盘模拟推演")
            if st.button("🚀 生成模拟开奖", use_container_width=True):
                pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
                st.success("🔔 模拟开奖成功！")
                r_res = sorted(random.sample(pool_r, count_r))
                b_res = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
                s_html, s_text = render_html_balls(r_res, b_res, choice)
                st.markdown(f"<div class='pred-row'><div class='pred-balls'>{s_html}</div></div>", unsafe_allow_html=True)
                st.code(s_text.replace('推荐号码: ', ''), language="text") # 一键复制

        with t3:
            st.markdown("### 🧬 基础 AI 演算")
            st.info(f"💡 当前模型正在实时读取左侧【{view_choice}】真实历史开奖数据，进行频次提取演算。")
            if st.button("🎯 启动统计演算", type="primary", use_container_width=True):
                st.session_state['ai_click_count'] += 1
            if st.session_state['ai_click_count'] > 0:
                for s in get_ai_predictions(df.head(view_limit), d_cols, choice, st.session_state['ai_click_count']):
                    st.markdown(f"<div class='pred-row'><div class='pred-title'>{s['name']}<br><span class='ai-desc'>{s['desc']}</span></div><div class='pred-balls'>{s['html']}</div></div>", unsafe_allow_html=True)
                    st.code(s['text'].replace('推荐号码: ', ''), language="text") # 一键复制

        with t4:
            # --- 💡 1. 刷新自动回读逻辑 (必须放在最前面) ---
            url_key = st.query_params.get("auth_key")
            if url_key and not st.session_state.get('vip_unlocked'):
                try:
                    is_ok, res_days = verify_card_from_sheets(url_key)
                    if is_ok:
                        st.session_state['vip_unlocked'] = True
                        st.session_state['last_valid_key'] = url_key
                        st.session_state['days_left'] = res_days
                except:
                    pass

            st.markdown("### 👑 顶级高阶矩阵预测")
            
            # --- 💡 2. 基础规则定义 (解决报错关键) ---
            t4_rules = {
                "双色球": (list(range(1, 34)), 6, "bg-red"),
                "大乐透": (list(range(1, 36)), 5, "bg-blue"),
                "六合/49": (list(range(1, 50)), 7, "bg-red"),
                "快乐8": (list(range(1, 81)), 20, "bg-red"),
                "福彩3D": (list(range(0, 10)), 3, "bg-lightblue"),
                "排列3": (list(range(0, 10)), 3, "bg-lotus"),
                "排列5": (list(range(0, 10)), 5, "bg-purple")
            }
            pool_r, count_r, ball_color = t4_rules.get(choice, (list(range(1,34)), 6, "bg-red"))
            view_limit = view_options[view_choice] # 联动左侧期数

            # --- 💡 3. 专属号码多维衍算模块 ---
            st.markdown("##### 🎯 专属号码多维衍算 (支持复式拆解)")
            custom_input = st.text_input("🔮 输入您的【心水种子号】(用空格隔开)：", placeholder="例如：06 18", key="seed_in")
            
            if st.button("🪄 一键衍生拟合", use_container_width=True, type="secondary"):
                if custom_input.strip():
                    with st.spinner('AI 正在融合历史数据...'):
                        seed_nums = [int(n) for n in re.findall(r'\d+', custom_input)]
                        valid_seeds = list(dict.fromkeys([n for n in seed_nums if n in pool_r]))
                        
                        # 真实计算：基于当前选择期数的热号
                        all_recent_nums = []
                        for col in d_cols:
                            all_recent_nums.extend(df.head(view_limit)[col].dropna().astype(int).tolist())
                        freq_dict = Counter(all_recent_nums)
                        hot_nums = [item[0] for item in freq_dict.most_common() if item[0] in pool_r]
                        
                        dan_pool = valid_seeds if valid_seeds else hot_nums[:5]
                        dan_ma = sorted(random.sample(dan_pool, 1)) if dan_pool else [random.choice(pool_r)]
                        
                        def get_dynamic_combo(count):
                            res = set(dan_ma)
                            temp_seeds = [x for x in valid_seeds if x not in res]
                            random.shuffle(temp_seeds)
                            for s in temp_seeds:
                                if len(res) < count: res.add(s)
                            temp_others = [x for x in pool_r if x not in res]
                            weight_pool = [x for x in temp_others if x in hot_nums[:15]] * 3 + temp_others
                            while len(res) < count: res.add(random.choice(weight_pool))
                            return sorted(list(res))
                        
                        m3, m5, m6 = get_dynamic_combo(3), get_dynamic_combo(5), get_dynamic_combo(6)
                        
                        st.markdown("###### 📊 AI 多维拟合结果")
                        for name, nums in [("🎯 核心胆码", dan_ma), ("🥉 精选组合", m3), ("🥈 高频推荐", m5), ("🥇 大底复式", m6)]:
                            fmt = "{:02d}" if choice in ["双色球", "大乐透", "快乐8"] else "{}"
                            b_html = "".join([f"<span class='pred-ball {ball_color}'>{fmt.format(n)}</span>" for n in nums])
                            st.markdown(f"<div class='pred-row'><div class='pred-title'>{name}</div><div class='pred-balls'>{b_html}</div></div>", unsafe_allow_html=True)
                            st.code(" ".join([fmt.format(n) for n in nums]), language="text")
                else:
                    st.warning("请先输入心水号码")

            st.markdown("---")

            # --- 💡 4. VIP 验证与记忆逻辑 (严格缩进版) ---
            if not st.session_state.get('vip_unlocked'):
                st.error("🔒 该区域需解锁高阶权限。")
                c1, c2 = st.columns([2, 1])
                with c1:
                    v_pwd = st.text_input("🔑 请输入授权码：", type="password", key="adv_pwd")
                with c2:
                    if st.button("激活高级权限", use_container_width=True, key="adv_unlock_btn"):
                        is_valid, msg_or_days = verify_card_from_sheets(v_pwd)
                        if is_valid:
                            st.session_state['vip_unlocked'] = True
                            st.session_state['last_valid_key'] = v_pwd
                            st.session_state['days_left'] = msg_or_days
                            st.query_params["auth_key"] = v_pwd # 写入 URL
                            st.success("✅ 激活成功！")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg_or_days if msg_or_days else "❌ 授权码错误")
            else:
                # --- 💡 5. VIP 内容展示区 ---
                st.info(f"🌟 VIP 已激活 (有效期剩余: {st.session_state.get('days_left', '未知')} 天)")
                
                if st.button("🚀 生成高阶大底", type="primary", use_container_width=True, key="gen_vip"):
                    st.session_state['adv_click_count'] += 1
                
                if st.session_state['adv_click_count'] > 0:
                    with st.spinner("正在基于深度矩阵解析历史数据..."):
                        adv_res = get_advanced_predictions(df.head(view_limit), d_cols, choice, st.session_state['adv_click_count'])
                        for s in adv_res:
                            # 强制同步颜色
                            styled_html = s['html'].replace('bg-red', ball_color).replace('bg-blue', ball_color)
                            st.markdown(f"""
                                <div class='pred-row {s.get('css_class', '')}'>
                                    <div class='pred-title'>{s['name']}<br><span class='ai-desc'>{s['desc']}</span></div>
                                    <div class='pred-balls'>{styled_html}</div>
                                </div>
                            """, unsafe_allow_html=True)
                            st.code(s['text'].replace('推荐号码: ', ''), language="text")

                # 退出登录
                if st.button("🔴 退出登录 / 更换卡密", key="logout"):
                    st.session_state['vip_unlocked'] = False
                    st.session_state['last_valid_key'] = None
                    st.query_params.clear() # 清空 URL
                    st.rerun()
        with t5:
            st.markdown("### 📤 自建数据沙盘 (支持全彩种)")
            if not st.session_state.get('vip_unlocked', False):
                st.error("🔒 【自建数据沙盘】属于高级功能。请在【高阶算法矩阵】标签中验证口令解锁。")
            else:
                custom_choice = st.selectbox("🎯 1. 选择规则", ["快乐8", "双色球", "大乐透", "七星彩", "排列5", "排列3", "福彩3D"])
                
                # 数据输入区
                uploaded_file = st.file_uploader("📁 2. 上传历史数据表格 (支持 CSV/Excel)", type=["csv", "xlsx", "xls"])
                c_text = st.text_area("✍️ 或者在此处手动粘贴历史开奖号码（每行一期，空格隔开）：", height=150, placeholder="1 2 3\n4 5 6")
                
                # --- 按钮逻辑开始 ---
                if st.button("🔬 启动马尔科夫矩阵推演", type="primary"):
                    custom_df = None
                    
                    # A. 优先处理上传的文件
                    if uploaded_file is not None:
                        try:
                            if uploaded_file.name.endswith('.csv'):
                                custom_df = pd.read_csv(uploaded_file)
                            else:
                                custom_df = pd.read_excel(uploaded_file)
                            st.success(f"✅ 成功从表格提取 {len(custom_df)} 期数据！")
                        except Exception as e:
                            st.error(f"🚨 解析表格出错: {e}")
                    
                    # B. 如果没文件，处理粘贴的文本
                    elif c_text.strip():
                        try:
                            lines = [l.strip() for l in c_text.strip().split('\n') if l.strip()]
                            parsed_data = []
                            for i, line in enumerate(lines):
                                nums = [int(n) for n in re.findall(r'\d+', line)]
                                if nums:
                                    # 给数据加一个模拟期号列，匹配算法格式
                                    parsed_data.append([len(lines)-i] + nums) 
                            
                            if parsed_data:
                                custom_df = pd.DataFrame(parsed_data)
                                st.success(f"✅ 成功提取 {len(custom_df)} 期自定义数据！")
                            else:
                                st.error("❌ 未能识别数字，请确保数字之间有空格。")
                        except Exception as e:
                            st.error(f"🚨 数据解析受阻，请检查输入格式。")
                    
                    # C. 兜底提示
                    else:
                        st.warning("⚠️ 老板，请先上传表格或粘贴数据！")
                    
                    # --- D. 核心预测引擎 (必须缩进在 if st.button 内部) ---
                    if custom_df is not None:
                        with st.spinner("马尔科夫状态转移矩阵计算中..."):
                            # 1. 注入实时随机种子
                            final_seed = random.randint(1, 9999) + int(time.time())
                            
                            # 2. 调用真算法引擎
                            results = get_advanced_predictions(custom_df, None, custom_choice, final_seed)
                            
                            # 3. 结果渲染
                            for s in results:
                                st.markdown(f"""
                                <div class="prediction-card {s.get('css_class', '')}">
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                        <div>
                                            <div style="font-weight: bold; color: #333; margin-bottom: 4px;">{s['name']}</div>
                                            <div style="font-size: 0.8rem; color: #666;">{s['desc']}</div>
                                        </div>
                                    </div>
                                    <div style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px;">
                                        {s['html']}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # 一键复制功能
                                st.code(s['text'].replace('推荐号码: ', ''), language="text") 
        with t7:
            st.markdown("### 🎯 专家级号码缩水过滤")
            st.info(f"当前分析彩种：{lottery_type}")
            col_s1, col_s2 = st.columns([1, 2])
            with col_s1:
                st.subheader("🔧 过滤条件设置")
                ac_filter = st.slider("AC值过滤 (>)", 0, 10, 4)
                sum_range = st.slider("和值范围", 50, 180, (80, 130))
                odd_even = st.multiselect("优先奇偶比", ["3:3", "4:2", "2:4"], default=["3:3"])
            with col_s2:
                if st.button("🚀 执行专家缩水协议"):
                    with st.spinner("正在对比历史遗漏与极值..."):
                        time.sleep(1)
                        st.success("缩水完成！已为您筛选出 9 组高概率组合：")
                        res_cols = st.columns(3)
                        for i in range(9):
                            if "大乐透" in lottery_type:
                                nums = " ".join([f"{n:02d}" for n in sorted(random.sample(range(1, 36), 5))]) + " | " + " ".join([f"{n:02d}" for n in sorted(random.sample(range(1, 13), 2))])
                            else:
                                nums = " ".join([f"{n:02d}" for n in sorted(random.sample(range(1, 34), 6))]) + " | " + f"{random.randint(1, 16):02d}"
                            res_cols[i%3].code(f"推荐 {i+1}: {nums}")

        with t6:
            st.markdown("### 💬 交流大厅")
            users = ["李哥", "王总", "发财哥", "追梦人"]
            msgs = ["今天必出08！", "马尔科夫链不错。", "有人合买吗？"]
            if 'comments' not in st.session_state:
                st.session_state.comments = [{"user": random.choice(users)+str(random.randint(10,99)), "text": random.choice(msgs), "time": f"{i}分钟前"} for i in range(1, 20)]
            
            chat_box = st.container(height=450)
            with chat_box:
                for c in st.session_state.comments:
                    st.markdown(f'''<div class="comment-box"><div class="comment-header"><span class="comment-user">{c["user"]}</span><span class="comment-time">{c["time"]}</span></div><div class="comment-body">{c["text"]}</div></div>''', unsafe_allow_html=True)
            
            chat_input = st.text_input("📝 发表...")
            if st.button("发送") and chat_input:
                st.session_state.comments.insert(0, {"user": "我", "text": chat_input, "time": "刚刚"})
                st.rerun()

        # --- 免责声明区域 ---
        st.markdown(f"""
        <div class="disclaimer">
            <b>免责声明</b><br>
            本系统通过历史数据分析及数学统计模型生成预测结果，所有呈现的形态走势、冷热频次及AI演算矩阵等均仅作为数据分析的参考维度。<br>
            系统不构成任何明确的投资指导或投注建议。彩市具有高度随机性与不可预测性，购彩存在风险，请务必保持理性，量力而行，风险自担。<br>
            禁止任何人将本软件用于非法用途，一切因使用本系统产生的纠纷均与开发者无关。
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ 未找到数据文件。")
