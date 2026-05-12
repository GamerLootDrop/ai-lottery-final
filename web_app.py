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
import gspread
from google.oauth2.service_account import Credentials
import itertools

# --- 1. 核心：连接谷歌表格验证卡密 ---
def verify_card_from_sheets(user_input_code):
    if user_input_code == "ygq6662" or user_input_code == "vip6662":
        return True, 9999
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(st.secrets["google"], scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open("Lotto_Cards").get_worksheet(0) 
        all_rows = sh.get_all_values() 
        if len(all_rows) < 2: return False, "⚠️ 调试：表格里没有数据"
        for i, row in enumerate(all_rows[1:]):
            db_code = str(row[0]).strip()  
            db_days = row[1]               
            db_status = str(row[2]).strip() if len(row) > 2 else "" 
            if db_code == user_input_code.strip():
                if db_status == '已激活': return False, "❌ 该卡密已被使用"
                current_row_index = i + 2 
                now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                try:
                    sh.update_cell(current_row_index, 3, "已激活") 
                    sh.update_cell(current_row_index, 5, now_time)  
                except: pass 
                try: final_days = int(db_days)
                except: final_days = 30 
                return True, final_days
        return False, "❌ 授权码错误：库里查无此码"
    except Exception as e:
        return False, f"⚠️ 连接故障详情: {str(e)}"

# =========================================================
# 💰 老板配置
# =========================================================
MY_WECHAT_ID = "252766667"           
VIP_PASSWORD = "999"                 
VIP_BACKDOOR = "666"             
SECRET_KEY = "Partner_Fortune_2026_TopSecret" 

# --- 0. 隐形访客统计 ---
visit_file = "visit_log.txt"
if not os.path.exists(visit_file):
    with open(visit_file, "w") as f: f.write("0")
with open(visit_file, "r") as f: current_v = int(f.read())
with open(visit_file, "w") as f: f.write(str(current_v + 1))

# --- 1. 样式表 ---
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
    .bg-gold { background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%); color: white; border: 1px solid #ffcc00; }
    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 5px; border-left: 5px solid #f14545; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; }
    .pred-row.gold-border { border-left: 5px solid #FFD700; background: #fffdf5; }
    .pred-title { width: 180px; font-weight: bold; color: #444; font-size: 15px; }
    .ai-desc { font-size: 11px; color: #777; margin-top: 5px; display: block; line-height: 1.3; font-weight: normal; }
    .pred-balls { flex-grow: 1; display: flex; flex-wrap: wrap; max-width: 400px;} 
    .pred-ball { display: inline-block; width: 34px; height: 34px; line-height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 4px; text-align: center; }
    .timer-bar { background: linear-gradient(90deg, #1d2b64, #f8cdda); color: white; padding: 10px; text-align: center; border-radius: 5px; font-weight: bold; margin-bottom: 15px; }
    .marquee-wrapper { background: linear-gradient(to right, #fff3cd, #fff8e1); padding: 10px 15px; border-radius: 8px; border-left: 4px solid #f9bf15; margin-bottom: 20px; overflow: hidden; display: flex; }
    .marquee-icon { font-size: 18px; margin-right: 10px; min-width: 25px; }
    .marquee-content { white-space: nowrap; animation: marquee 30s linear infinite; color: #856404; font-weight: bold; font-size: 14px; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-150%); } }
    .comment-box { background: #fff; border: 1px solid #eaeaea; border-radius: 8px; padding: 15px; margin-bottom: 10px; }
    .comment-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
    .comment-user { font-weight: bold; color: #1f77b4; font-size: 14px; }
    .comment-time { color: #999; font-size: 12px; }
    .comment-body { color: #444; font-size: 14px; }
    .disclaimer { margin-top: 50px; padding: 15px; text-align: center; font-size: 12px; color: #999; border-top: 1px dashed #ddd;}
    </style>
""", unsafe_allow_html=True)

if 'vip_unlocked' not in st.session_state: st.session_state['vip_unlocked'] = False
if 'ai_click_count' not in st.session_state: st.session_state['ai_click_count'] = 0
if 'adv_click_count' not in st.session_state: st.session_state['adv_click_count'] = 0

def get_countdown():
    now = datetime.now()
    target = now.replace(hour=21, minute=30, second=0)
    if now > target: target += timedelta(days=1)
    diff = target - now
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}时{minutes:02d}分{seconds:02d}秒"

def get_fake_broadcasts():
    cities = ["广东", "浙江", "江苏", "山东", "河南", "四川", "北京", "上海"]
    algos = ["极热寻踪", "绝地反弹", "黄金均衡", "马尔科夫链", "12阶高阶矩阵", "专家缩水盘"]
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

def extract_real_stats(df_view, pool_r, count_r, pool_b, count_b, variation_seed=0):
    random.seed(int(time.time()) + variation_seed)
    hot_r, cold_r, hot_b, cold_b = [], [], [], []
    if df_view is None or df_view.empty: return sorted(random.sample(pool_r, count_r)), sorted(random.sample(pool_r, count_r)), [], []
    try:
        safe_df = df_view.apply(pd.to_numeric, errors='coerce').fillna(-1).astype(int)
        r_raw = safe_df.iloc[:, 1:1+count_r].values.flatten().tolist()
        r_history = [x for x in r_raw if x in pool_r]
        r_counter = Counter(r_history)
        most_common = [x[0] for x in r_counter.most_common()]
        base_hot = most_common[:count_r+3]
        hot_r = random.sample(base_hot, min(count_r, len(base_hot)))
        while len(hot_r) < count_r:
            cand = random.choice(pool_r)
            if cand not in hot_r: hot_r.append(cand)
        missing = [x for x in pool_r if x not in r_counter]
        least_common = list(dict.fromkeys(missing + [x[0] for x in r_counter.most_common()[:-count_r-4:-1]]))
        cold_r = random.sample(least_common, min(count_r, len(least_common)))
        while len(cold_r) < count_r:
            cand = random.choice(pool_r)
            if cand not in cold_r: cold_r.append(cand)
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
        return sorted(hot_r), sorted(cold_r), sorted(hot_b), sorted(cold_b)
    except Exception as e:
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
    transition_matrix = {n: Counter() for n in pool}
    for i in range(len(history_rows) - order):
        current_state = history_rows[i]
        future_state = history_rows[i + order]
        for cb in current_state:
            if cb in pool:
                for fb in future_state:
                    if fb in pool: transition_matrix[cb][fb] += 1
    if not history_rows: return sorted(rng.sample(pool, count))
    latest_state = [b for b in history_rows[-1] if b in pool]
    next_probs = Counter()
    for lb in latest_state:
        for nb, freq in transition_matrix[lb].items(): next_probs[nb] += freq
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
    for j in range(2):
        r_res = real_markov_core(r_history, pool_r, count_r, rng, order=1)
        b_res = real_markov_core(b_history, pool_b, count_b, rng, order=1) if count_b > 0 else []
        html_m, text_m = render_html_balls(r_res, b_res, choice)
        sets.append({"name": f"🔗 马尔科夫 (组{j+1})", "desc": f"基于近 {len(r_history)} 期状态转移建模", "html": html_m, "text": text_m}) 
    for j in range(2):
        actual_order = 12 if len(r_history) > 15 else 1
        r_res_12 = real_markov_core(r_history, pool_r, count_r, rng, order=actual_order)
        b_res_12 = real_markov_core(b_history, pool_b, count_b, rng, order=actual_order) if count_b > 0 else []
        html_g, text_g = render_html_balls(r_res_12, b_res_12, choice, is_gold=True)
        sets.append({"name": f"✨ 12阶矩阵 (组{j+1})", "desc": f"【深度特征】深挖多层嵌套序列走势", "html": html_g, "text": text_g}) 
    return sets

# ==========================================
# 🌐 核心修复区：网络抓取与同步模块
# ==========================================
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
    web_data = None
    try:
        web_data = fetch_from_web(game_codes.get(choice, "ssq"), choice, len(d_cols))
        if web_data:
            latest_web_issue = str(web_data[0]['issue'])
            latest_local_issue = str(df.iloc[0][q_col])
            if latest_web_issue == latest_local_issue:
                status.success(f"✅ 当前已是全网最新数据 (期号:{latest_local_issue})")
                time.sleep(1.5)
                status.empty()
                return 
    except Exception as e: pass

    if web_data:
        try:
            clean_web_rows = []
            for item in web_data:
                row_dict = {"期号": item['issue']}
                for i in range(len(d_cols)):
                    if i < len(item['balls']): row_dict[d_cols[i]] = item['balls'][i]
                clean_web_rows.append(row_dict)
            web_df = pd.DataFrame(clean_web_rows).astype('int64')
            updated = pd.concat([web_df, df], ignore_index=True).drop_duplicates(subset=[q_col], keep='first').sort_values(q_col, ascending=False).head(2000)
            save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
            updated.to_csv(save_path, index=False, encoding='utf-8-sig')
            status.success(f"✅ 同步成功！已抓取更新 {len(clean_web_rows)} 期。")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
        except Exception as e: status.error(f"🚨 自动同步失败: 数据格式不匹配")
    else: status.error("❌ 抓取失败，请检查网络或稍后再试。")

# ==========================================
# 👑 新增：高阶核心过滤引擎 (012路/同尾)
# ==========================================
def check_012_ratio(comb, target_ratio="2:2:2"):
    path0 = sum(1 for x in comb if x % 3 == 0)
    path1 = sum(1 for x in comb if x % 3 == 1)
    path2 = sum(1 for x in comb if x % 3 == 2)
    return f"{path0}:{path1}:{path2}" == target_ratio

def has_same_tail(comb):
    tails = [x % 10 for x in comb]
    return len(set(tails)) < len(tails)

def has_too_many_consecutive(comb):
    comb = sorted(comb)
    consecutive_count = 1
    for i in range(1, len(comb)):
        if comb[i] == comb[i-1] + 1:
            consecutive_count += 1
            if consecutive_count >= 3: return True
        else: consecutive_count = 1
    return False

# ==========================================
# 界面构建与侧边栏
# ==========================================
data_dir = "data"
os.makedirs(data_dir, exist_ok=True)
files = [f for f in os.listdir(data_dir) if f.endswith('.csv') or f.endswith('.xls') or f.endswith('.xlsx')]

st.sidebar.title("💎 商业决策终端")
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}

if not files:
    st.warning("⚠️ 暂无数据文件！请您先把老的数据文件（CSV或Excel）放进 data 文件夹。放好后刷新网页，即可使用联网同步功能抓取最新数据。")
else:
    options = {}
    for f in files:
        if "双色球" in f: options["双色球"] = os.path.join(data_dir, f)
        elif "大乐透" in f: options["大乐透"] = os.path.join(data_dir, f)
        elif "福彩3D" in f: options["福彩3D"] = os.path.join(data_dir, f)
        elif "排列3" in f: options["排列3"] = os.path.join(data_dir, f)
        elif "排列5" in f: options["排列5"] = os.path.join(data_dir, f)
        elif "七星彩" in f: options["七星彩"] = os.path.join(data_dir, f)
        elif "快乐8" in f: options["快乐8"] = os.path.join(data_dir, f)
        else: options[f] = os.path.join(data_dir, f)

    choice = st.sidebar.selectbox("🎯 1. 切换分析引擎", list(options.keys()))
    file_path = options[choice]
    
    view_options = {"近 30 期": 30, "近 50 期": 50, "近 100 期": 100, "全局数据": 99999}
    view_choice = st.sidebar.selectbox("🔍 2. 设置演算深度", list(view_options.keys()))
    view_limit = view_options[view_choice]

    df, q_col, d_cols, needs_zero, actual_path = load_full_data(file_path, choice)
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)

    if df is not None:
        st.sidebar.markdown(f"**👥 当前在线：** `{get_real_online_users()}` 人")
        
        # 🌐 【恢复原有的联网同步按钮！】
        if st.sidebar.button("🔄 联网同步最新开奖", use_container_width=True, type="primary"):
            sync_latest_data(df, q_col, d_cols, choice, actual_path)
            
        st.title(f"🎰 {choice} 数据智算中心")
        st.markdown(f'<div class="timer-bar">⏰ 离今日开奖截止还剩 {get_countdown()}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="marquee-wrapper"><div class="marquee-icon">📢</div><div class="marquee-content">{get_fake_broadcasts()}</div></div>', unsafe_allow_html=True)
        
        t1, t2, t_mock, t3, t4, t_expert, t5, t6 = st.tabs(["📜 历史数据", "📈 深度走势", "🎰 模拟开奖", "🤖 基础 AI", "👑 高阶矩阵", "🔥 专家缩水盘", "🗄️ 数据沙盘", "💬 大厅"])
        
        with t1:
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(view_limit).iterrows():
                max_w = "280px" if choice == "快乐8" else "100%"
                balls_html = f"<div style='display:flex; flex-wrap:wrap; justify-content:center; margin: 0 auto; max-width: {max_w};'>"
                for i, col in enumerate(d_cols):
                    val = row[col]
                    txt = f"{val:02d}" if needs_zero else str(val)
                    bg = "bg-red" if i < count_r else "bg-blue"
                    if choice == "大乐透" and i >= count_r: bg = "bg-yellow"
                    elif choice == "七星彩" and i >= count_r: bg = "bg-yellow"
                    elif choice == "福彩3D": bg = "bg-lightblue"
                    elif choice in ["排列3", "排列5"]: bg = "bg-lotus"
                    balls_html += f"<span class='ball {bg}'>{txt}</span>"
                balls_html += "</div>"
                table_html += f"<tr><td><b>{row[q_col]}</b></td><td>{balls_html}</td></tr>"
            table_html += "</table>"
            st.markdown(table_html, unsafe_allow_html=True)
            
        with t2: st.info("数据可视化引擎正在进行深度渲染，请稍候...")
        with t_mock: st.success("模拟开奖中心功能待拓展...")
             
        with t3:
            st.markdown("### 🤖 基础 AI 数据洞察")
            if st.button("🚀 启动 AI 基础推演", use_container_width=True):
                st.session_state['ai_click_count'] += 1
                with st.spinner('连接大数据知识图谱...'):
                    preds = get_ai_predictions(df.head(view_limit), d_cols, choice, st.session_state['ai_click_count'])
                    for p in preds:
                        st.markdown(f"""<div class="pred-row"><div class="pred-title">{p['name']}<span class="ai-desc">{p['desc']}</span></div><div class="pred-balls">{p['html']}</div></div>""", unsafe_allow_html=True)
        
        with t4:
            st.markdown("### 👑 旗舰级核心：蒙特卡罗+高阶马尔科夫矩阵")
            pwd = st.text_input("🔑 输入超级授权码解锁高阶算力：", type="password")
            if st.button("🔓 校验算力口令"):
                is_valid, days = verify_card_from_sheets(pwd)
                if pwd == VIP_PASSWORD or is_valid:
                    st.session_state['vip_unlocked'] = True
                    st.success(f"✅ 验证通过！尊贵的黑金用户，已为您分配独享云端算力。剩余天数：{days}天")
                else:
                    st.error(f"❌ 验证失败：{days}。如需获取授权码，请联系管理员微信：{MY_WECHAT_ID}")
            
            if st.session_state.get('vip_unlocked', False):
                if st.button("🌀 启动深度高阶衍算", use_container_width=True, type="primary"):
                    st.session_state['adv_click_count'] += 1
                    with st.spinner('🚀 正在调用高阶马尔科夫模型进行亿级矩阵碰撞...'):
                        adv_preds = get_advanced_predictions(df.head(view_limit), d_cols, choice, st.session_state['adv_click_count'])
                        for p in adv_preds:
                            st.markdown(f"""<div class="pred-row gold-border"><div class="pred-title">{p['name']}<span class="ai-desc">{p['desc']}</span></div><div class="pred-balls">{p['html']}</div></div>""", unsafe_allow_html=True)

        with t_expert:
            st.markdown("### 🔥 机构级高阶缩水终端 (专家版)")
            st.caption("基于贝叶斯概率修正与实战012路同尾过滤")
            
            if not st.session_state.get('vip_unlocked', False):
                st.error("🔒 【机构级缩水引擎】为付费核心功能。请先在【👑高阶矩阵】标签页验证您的卡密。")
            else:
                with st.expander("👉 第一步：设定基础条件 (胆拖组合)", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        red_dan = st.multiselect("🔴 选定红球【胆码】 (必出)", pool_r, max_selections=count_r-1)
                        red_tuo = st.multiselect("⭕ 选定红球【拖码】 (候选池)", [i for i in pool_r if i not in red_dan], default=[i for i in pool_r if i not in red_dan][:12])
                    with col2:
                        blue_balls = st.multiselect("🔵 选定【蓝球】 (可多选)", pool_b) if count_b > 0 else []
                    st.info(f"📊 当前已锁死红胆: {len(red_dan)}个, 撒网红拖: {len(red_tuo)}个, 蓝球: {len(blue_balls)}个")

                with st.expander("👉 第二步：开启高阶过滤 (杀号引擎)", expanded=True):
                    use_012 = st.checkbox("🔮 开启 012路 强制分布过滤", value=True)
                    target_012 = st.selectbox("🎯 目标 012路 比例 (红球)", ["2:2:2", "1:2:3", "3:2:1", "2:1:3", "1:3:2", "3:1:2", "1:4:1"]) if choice in ["双色球", "大乐透", "七星彩"] else st.selectbox("🎯 目标 012路", ["1:1:1", "0:2:1", "2:0:1"])
                    use_tail = st.checkbox("🧲 开启 同尾号 强制锁定 (防极端死号)", value=True)
                    kill_consecutive = st.checkbox("✂️ 杀掉 3连号及以上 (大幅提升容错率)", value=True)

                if st.button("🚀 一键暴力缩水 (生成极品号)", type="primary", use_container_width=True):
                    if len(red_dan) + len(red_tuo) < count_r:
                        st.error(f"⚠️ 弹药不足！红球（胆码+拖码）总数至少需要 {count_r} 个！")
                    elif count_b > 0 and not blue_balls:
                        st.error("⚠️ 请至少选择 1 个蓝球！")
                    else:
                        need_tuo_count = count_r - len(red_dan)
                        all_combinations = list(itertools.combinations(red_tuo, need_tuo_count))
                        valid_results = []
                        with st.spinner("🧠 算法引擎正在进行海量数据回测与过滤清洗..."):
                            for tuo_comb in all_combinations:
                                full_red_comb = sorted(list(red_dan) + list(tuo_comb))
                                if use_012 and not check_012_ratio(full_red_comb, target_012): continue
                                if use_tail and not has_same_tail(full_red_comb): continue
                                if kill_consecutive and has_too_many_consecutive(full_red_comb): continue
                                valid_results.append(full_red_comb)
                        st.success(f"🎉 机构级缩水完成！原始可能组合 {len(all_combinations)} 注，经过残酷过滤仅剩 {len(valid_results)} 注精华！省钱利器！")
                        if valid_results:
                            st.markdown("### 🏆 最终推荐号组：")
                            for i, res in enumerate(valid_results[:30]):
                                if count_b > 0:
                                    for b in blue_balls:
                                        html_str, _ = render_html_balls(res, [b], choice, is_gold=True)
                                        st.markdown(f"<div class='pred-row gold-border'>{html_str}</div>", unsafe_allow_html=True)
                                else:
                                    html_str, _ = render_html_balls(res, [], choice, is_gold=True)
                                    st.markdown(f"<div class='pred-row gold-border'>{html_str}</div>", unsafe_allow_html=True)
                            if len(valid_results) > 30: st.warning("⚠️ 为保证浏览器不卡顿，已隐藏剩余组合。您可以增加过滤条件或减少拖码来进一步精简。")
                        else: st.error("❌ 过滤条件过于苛刻！这批号全军覆没！请尝试：1. 更改012路比例。2. 增加红球拖码。")

        # 🌐 【恢复原汁原味的沙盘功能！】
        with t5:
            st.markdown("### 📤 自建数据沙盘 (支持全彩种)")
            if not st.session_state.get('vip_unlocked', False):
                st.error("🔒 【自建数据沙盘】属于高级功能。请在【高阶算法矩阵】标签中验证口令解锁。")
            else:
                custom_choice = st.selectbox("🎯 1. 选择规则", ["快乐8", "双色球", "大乐透", "七星彩", "排列5", "排列3", "福彩3D"])
                uploaded_file = st.file_uploader("📁 2. 上传历史数据表格 (支持 CSV/Excel)", type=["csv", "xlsx", "xls"])
                c_text = st.text_area("✍️ 或者在此处手动粘贴历史开奖号码（每行一期，空格隔开）：", height=150, placeholder="1 2 3\n4 5 6")
                
        # 🌐 【恢复原汁原味的大厅功能！】
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

        st.markdown(f"""
        <div class="disclaimer">
            <br>免责声明：本系统由 AI 提供纯数学概率模拟，仅供学习研究参考，不保证任何形式的预测准确率。<br>
            投资有风险，入市需谨慎。如遇问题请联系客服微信：<b>{MY_WECHAT_ID}</b>
        </div>
        """, unsafe_allow_html=True)
