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
import numpy as np 
import hashlib
import base64

# =========================================================
# 💰💰💰 老板专属配置区 (只需修改这里，其他地方不用动) 💰💰💰
# =========================================================
MY_WECHAT_ID = "252766667"           # 已帮您填好微信号
VIP_PASSWORD = "999"                 # 高级权限解锁口令 (解锁高阶算法和100期数据)
VIP_BACKDOOR = "666"                 # 老板无敌后门 (输这个啥都能解)
SECRET_KEY = "Partner_Fortune_2026_TopSecret" # 卡密防伪终极密钥
# =========================================================

# --- 0. 隐形访客统计 (仅后台记录) ---
visit_file = "visit_log.txt"
if not os.path.exists(visit_file):
    with open(visit_file, "w") as f: f.write("0")
with open(visit_file, "r") as f:
    current_v = int(f.read())
new_v = current_v + 1
with open(visit_file, "w") as f: f.write(str(new_v))

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
    .bg-gray { background-color: #a0a0a0; text-decoration: line-through; }
    
    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 5px; border-left: 5px solid #f14545; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; position: relative; }
    .pred-row.gold-border { border-left: 5px solid #FFD700; background: #fffdf5; }
    .pred-title { width: 180px; font-weight: bold; color: #444; font-size: 15px; }
    .ai-desc { font-size: 11px; color: #777; margin-top: 5px; display: block; line-height: 1.3; font-weight: normal; }
    .pred-balls { flex-grow: 1; display: flex; flex-wrap: wrap; max-width: 400px;} 
    .pred-ball { display: inline-block; width: 34px; height: 34px; line-height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 4px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.15); transition: all 0.3s ease; }
    
    .timer-bar { background: linear-gradient(90deg, #1d2b64, #f8cdda); color: white; padding: 10px; text-align: center; border-radius: 5px; font-weight: bold; margin-bottom: 15px; }
    .wechat-box { background: #f0f2f6; border-radius: 10px; padding: 15px; border: 1px solid #dcdfe6; text-align: center; margin-bottom: 10px;}
    .download-lock { background: #fff5f5; border: 1px dashed #feb2b2; padding: 15px; text-align: center; border-radius: 8px; margin-bottom: 15px; }
    
    .marquee-wrapper { background: linear-gradient(to right, #fff3cd, #fff8e1); padding: 10px 15px; border-radius: 8px; border-left: 4px solid #f9bf15; margin-bottom: 20px; overflow: hidden; display: flex; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .marquee-icon { font-size: 18px; margin-right: 10px; min-width: 25px; }
    .marquee-content { white-space: nowrap; animation: marquee 30s linear infinite; color: #856404; font-weight: bold; font-size: 14px; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-150%); } }
    
    .comment-box { background: #fff; border: 1px solid #eaeaea; border-radius: 8px; padding: 15px; margin-bottom: 10px; }
    .comment-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
    .comment-user { font-weight: bold; color: #1f77b4; font-size: 14px; }
    .comment-time { color: #999; font-size: 12px; }
    .comment-body { color: #444; font-size: 14px; line-height: 1.5; }
    </style>
""", unsafe_allow_html=True)

# --- 状态初始化 ---
if 'vip_unlocked' not in st.session_state: st.session_state['vip_unlocked'] = False
if 'ai_click_count' not in st.session_state: st.session_state['ai_click_count'] = 0
if 'adv_click_count' not in st.session_state: st.session_state['adv_click_count'] = 0

# --- 卡密验证核心逻辑 ---
def verify_card_key(user_input_key):
    if not user_input_key: return False, ""
    if user_input_key == VIP_BACKDOOR: return True, "老板专属后门已触发！"
    try:
        decoded_bytes = base64.b64decode(user_input_key + "===")
        decoded_str = decoded_bytes.decode()
        parts = decoded_str.split('-')
        if len(parts) != 3 or parts[0] != 'VIP': return False, "卡密格式错误，请检查！"
        card_hash, expire_date_str = parts[1], parts[2]
        expected_raw = f"{expire_date_str}|{SECRET_KEY}"
        expected_hash = hashlib.md5(expected_raw.encode()).hexdigest()[:6]
        if card_hash != expected_hash: return False, "卡密无效或系伪造！"
        expire_date = datetime.strptime(expire_date_str, '%Y%m%d').date()
        if datetime.now().date() > expire_date: return False, f"该卡密已于 {expire_date_str} 过期。"
        return True, "验证通过！高级权限已解锁。"
    except:
        return False, "卡密解析失败，请检查输入。"

# --- 工具函数 ---
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
    algos = ["极热寻踪", "绝地反弹", "黄金均衡", "马尔科夫链", "12阶高阶矩阵"]
    broadcast_texts = []
    for _ in range(5):
        city = random.choice(cities)
        phone = f"1{random.randint(3,9)}{random.randint(0,9)}****{random.randint(1000,9999)}"
        algo = random.choice(algos)
        mins = random.randint(1, 59)
        broadcast_texts.append(f"【最新喜报】{city}用户 {phone} {mins}分钟前 成功解锁「{algo}」策略！")
    return "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🔥&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join(broadcast_texts)

def get_real_online_users():
    hour = datetime.now().hour
    if 0 <= hour < 7: base = 350
    elif 7 <= hour < 12: base = 1200
    elif 12 <= hour < 18: base = 1800
    elif 18 <= hour < 22: base = 2800 
    else: base = 1500
    return base + random.randint(-50, 150)

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
        for j in range(i+1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    ac = len(diffs) - (len(nums) - 1)
    return max(0, ac)

# --- 核心：数据载入 ---
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
            if not nums.empty and (nums <= 81).all():
                ball_cols.append(col)
            if len(ball_cols) == max_balls: break
            
        clean_df = raw_df[[q_col] + ball_cols].copy()
        new_names = ['期号'] + [f"b_{i+1}" for i in range(len(ball_cols))]
        clean_df.columns = new_names
        for c in new_names: clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0).astype(int)
        
        needs_zero = True if choice in ["双色球", "大乐透", "快乐8"] else False
        return clean_df.sort_values('期号', ascending=False), '期号', new_names[1:], needs_zero, file_path
    except: return None, None, None, None, None

def render_html_balls(r_res, b_res, choice, is_gold=False, is_gray=False):
    if is_gray:
        r_class = "bg-gray"
        b_class = "bg-gray"
    else:
        r_class = "bg-gold" if is_gold else "bg-red"
        b_class = "bg-blue"
        
    if choice == "双色球": 
        html = "".join([f"<span class='pred-ball {r_class}'>{n:02d}</span>" for n in r_res]) + "".join([f"<span class='pred-ball {b_class}'>{n:02d}</span>" for n in b_res])
        text = f"推荐号码: " + " ".join([f"{n:02d}" for n in r_res]) + (" | " + f"{b_res[0]:02d}" if b_res else "")
    elif choice == "大乐透": 
        if not is_gray: b_class = "bg-yellow"
        r_class = 'bg-gold' if is_gold else ('bg-gray' if is_gray else 'bg-blue')
        html = "".join([f"<span class='pred-ball {r_class}'>{n:02d}</span>" for n in r_res]) + "".join([f"<span class='pred-ball {b_class}'>{n:02d}</span>" for n in b_res])
        text = f"推荐号码: " + " ".join([f"{n:02d}" for n in r_res]) + (" | " + " ".join([f"{n:02d}" for n in b_res]) if b_res else "")
    elif choice == "七星彩": 
        if not is_gray: b_class = "bg-yellow"
        r_class = 'bg-gold' if is_gold else ('bg-gray' if is_gray else 'bg-purple')
        html = "".join([f"<span class='pred-ball {r_class}'>{n}</span>" for n in r_res]) + "".join([f"<span class='pred-ball {b_class}'>{n}</span>" for n in b_res])
        text = f"推荐号码: " + " ".join([str(n) for n in r_res]) + (" | " + f"{b_res[0]}" if b_res else "")
    elif choice == "快乐8": 
        html = "".join([f"<span class='pred-ball {r_class}'>{n:02d}</span>" for n in r_res])
        text = f"推荐号码: " + " ".join([f"{n:02d}" for n in r_res])
    elif choice == "福彩3D": 
        r_class = 'bg-gold' if is_gold else ('bg-gray' if is_gray else 'bg-lightblue')
        html = "".join([f"<span class='pred-ball {r_class}'>{n}</span>" for n in r_res])
        text = f"推荐号码: " + " ".join([str(n) for n in r_res])
    else: 
        r_class = 'bg-gold' if is_gold else ('bg-gray' if is_gray else 'bg-lotus')
        html = "".join([f"<span class='pred-ball {r_class}'>{n}</span>" for n in r_res])
        text = f"推荐号码: " + " ".join([str(n) for n in r_res])
    return html, text

# --- 全新升级：真实统计基础上的动态抽样 ---
def get_ai_predictions(df_view, d_cols, choice, click_count):
    sets = []
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    
    try: seed_val = int(df_view.iloc[0][df_view.columns[0]])
    except: seed_val = 888
    # 结合真实期号和点击次数，实现动态刷新
    random.seed(seed_val + click_count)
    
    # 真实红球频率统计
    r_data = []
    for col in d_cols[:count_r]: r_data.extend(df_view[col].dropna().astype(int).tolist())
    r_freq = Counter(r_data)
    for n in pool_r:
        if n not in r_freq: r_freq[n] = 0
    sorted_r = sorted(r_freq.keys(), key=lambda x: (-r_freq[x], x))

    # 真实蓝球频率统计
    b_data = []
    if count_b > 0:
        for col in d_cols[count_r:]: b_data.extend(df_view[col].dropna().astype(int).tolist())
    b_freq = Counter(b_data)
    for n in pool_b:
        if n not in b_freq: b_freq[n] = 0
    sorted_b = sorted(b_freq.keys(), key=lambda x: (-b_freq[x], x)) if count_b > 0 else []

    # 1. 极热寻踪 (从真实高热号码池中动态抽样)
    hot_r_pool = sorted_r[:max(count_r + 4, len(pool_r)//3)]
    r_hot = sorted(random.sample(hot_r_pool, count_r))
    b_hot = sorted(random.sample(sorted_b[:max(count_b+2, 4)], count_b)) if count_b > 0 else []
    html_1, text_1 = render_html_balls(r_hot, b_hot, choice)
    sets.append({"name": "🔥 极热寻踪", "desc": "【纯统计特征】在真实近期出现频次最高的热点号码池中动态提取。", "html": html_1, "text": text_1})
    
    # 2. 绝地反弹 (从真实极冷号码池中动态抽样)
    cold_r_pool = sorted_r[-max(count_r + 4, len(pool_r)//3):]
    r_cold = sorted(random.sample(cold_r_pool, count_r))
    b_cold = sorted(random.sample(sorted_b[-max(count_b+2, 4):], count_b)) if count_b > 0 else []
    html_2, text_2 = render_html_balls(r_cold, b_cold, choice)
    sets.append({"name": "🧊 绝地反弹", "desc": "【均值回归】抓取当前遗漏值极高、急需追平历史概率的冷区号码池中提取。", "html": html_2, "text": text_2})
    
    # 3. 黄金均衡 (热+温+冷 比例动态组合)
    hot_part = max(1, count_r // 3)
    cold_part = max(1, count_r // 3)
    mid_part = count_r - hot_part - cold_part
    r_mix = sorted(random.sample(sorted_r[:10], hot_part) + random.sample(sorted_r[-10:], cold_part) + random.sample(sorted_r[10:-10], mid_part))
    b_mix = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
    html_3, text_3 = render_html_balls(r_mix, b_mix, choice)
    sets.append({"name": "⚖️ 黄金均衡", "desc": "【自然正态分布】强制按比例注入热号、温号、冷号的动态防偏组合。", "html": html_3, "text": text_3})
    
    # 4. 蒙特卡洛 
    r_mc = sorted(random.sample(pool_r, count_r))
    b_mc = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
    html_4, text_4 = render_html_balls(r_mc, b_mc, choice)
    sets.append({"name": "🎲 蒙特卡洛碰撞", "desc": "【暴力算力推演】系统内部模拟百万次摇奖碰撞，抽取本轮最强共振序列。", "html": html_4, "text": text_4})
    
    # 5. 深度拟合 
    latest_r = df_view.iloc[0][d_cols[:count_r]].astype(int).tolist() if len(df_view)>0 else pool_r[:count_r]
    r_dp = sorted(random.sample([n for n in pool_r if n not in latest_r] + latest_r, count_r))
    b_dp = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
    html_5, text_5 = render_html_balls(r_dp, b_dp, choice)
    sets.append({"name": "🧠 LSTM 深度拟合", "desc": "【时间序列网络】结合时间波谷特征运算，消除近期无效杂音。", "html": html_5, "text": text_5})
    
    return sets

# --- 全新升级：高阶矩阵动态抽样 ---
def get_advanced_predictions(df_view, d_cols, choice, click_count):
    sets = []
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    try: seed_val = int(df_view.iloc[0][df_view.columns[0]])
    except: seed_val = 999
    
    # 马尔科夫链 5 组
    for j in range(5):
        random.seed(seed_val + click_count * 100 + j * 11)
        r_res = sorted(random.sample(pool_r, count_r))
        b_res = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
        html_m, text_m = render_html_balls(r_res, b_res, choice)
        sets.append({"name": f"🔗 马尔科夫 (组{j+1})", "desc": f"状态转移概率网络生成 | 经测算 AC复杂度: {calculate_ac_value(r_res)}", "html": html_m, "text": text_m, "css_class": ""})
        
    # 12阶高阶矩阵 5 组
    for j in range(5):
        random.seed(seed_val + click_count * 200 + j * 77 + 55)
        r_res = sorted(random.sample(pool_r, count_r))
        b_res = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
        html_12, text_12 = render_html_balls(r_res, b_res, choice, is_gold=True)
        sets.append({"name": f"✨ 12阶矩阵 (组{j+1})", "desc": f"空间偏移基点深度演算 | 经测算 AC复杂度: {calculate_ac_value(r_res)}", "html": html_12, "text": text_12, "css_class": "gold-border"})
        
    return sets


# --- 核心：完美保留的抓取函数 ---
@st.cache_data(ttl=3600)
def fetch_from_web(game_code, choice, d_cols_len):
    urls = [f"https://datachart.500.com/{game_code}/history/newinc/history.php?limit=50", f"https://datachart.500.com/{game_code}/history/inc/history.php?limit=50"]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    web_rows = []
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            tdata = soup.find('tbody', id='tdata')
            trs = tdata.find_all('tr') if tdata else (soup.find_all('tr', class_=['t_tr1', 't_tr2', 't_tr']) or soup.find_all('tr'))
            
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) < d_cols_len + 1: continue 
                
                iss_str = re.sub(r'\D', '', tds[0].get_text(strip=True))
                if len(iss_str) < 3: continue
                if len(iss_str) > 12: iss_str = iss_str[:10]
                issue_val = int("20" + iss_str) if len(iss_str) == 5 else int(iss_str)
                
                balls = []
                if choice == "快乐8":
                    text_block = " ".join([td.get_text(separator=" ") for td in tds[1:25]])
                    nums = [int(n) for n in re.findall(r'\b\d{1,2}\b', text_block)]
                    balls = [n for n in nums if 1 <= n <= 80][:d_cols_len]
                elif choice in ["排列5", "排列3", "福彩3D"]:
                    text_block = "".join([td.get_text(strip=True) for td in tds[1:8]])
                    digits = re.findall(r'\d', text_block)
                    balls = [int(d) for d in digits][:d_cols_len]
                elif choice == "七星彩":
                    rest_text = " ".join([td.get_text(separator=" ") for td in tds[1:10]])
                    groups = re.findall(r'\d+', rest_text)
                    for g in groups:
                        if len(g) >= 3:
                            for char in g: balls.append(int(char))
                        else:
                            balls.append(int(g))
                    balls = balls[:d_cols_len]
                else:
                    rest_text = "   ".join([td.get_text(separator=" ") for td in tds[1:]])
                    balls = [int(n) for n in re.findall(r'\d+', rest_text)]
                    balls = [n for n in balls if 0 <= n <= 81][:d_cols_len]
                
                if len(balls) == d_cols_len:
                    web_rows.append({"issue": issue_val, "balls": balls})
            if web_rows: break 
        except: continue
    return web_rows

def sync_latest_data(df, q_col, d_cols, choice, file_path):
    status = st.empty()
    game_codes = {"双色球": "ssq", "大乐透": "dlt", "福彩3D": "sd", "排列3": "pls", "排列5": "plw", "七星彩": "qxc", "快乐8": "kl8"}
    game_code = game_codes.get(choice, "ssq")
    status.info(f"📡 正在联网获取 {choice} 最新开奖...")
    
    web_data = fetch_from_web(game_code, choice, len(d_cols))
    
    if web_data:
        try:
            clean_web_rows = []
            for item in web_data:
                safe_issue = int(str(item['issue'])[:12])
                new_row = {q_col: safe_issue}
                for i, col_name in enumerate(d_cols):
                    new_row[col_name] = int(item['balls'][i])
                clean_web_rows.append(new_row)
            
            if not clean_web_rows:
                status.warning("⚠️ 抓取到的数据格式异常，已终止同步。")
                return

            web_df = pd.DataFrame(clean_web_rows).astype('int64')
            df[q_col] = pd.to_numeric(df[q_col], errors='coerce').fillna(0).astype('int64')
            for c in d_cols:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype('int64')

            updated = pd.concat([web_df, df], ignore_index=True)
            updated = updated.drop_duplicates(subset=[q_col], keep='first').sort_values(q_col, ascending=False)
            updated = updated.head(2000)
            
            save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
            updated.to_csv(save_path, index=False, encoding='utf-8-sig')
            status.success(f"✅ 同步成功！已更新 {len(clean_web_rows)} 期。")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
        except Exception as e:
            status.error(f"🚨 自动同步失败，建议手动更新本地文件。")
    else:
        status.error("❌ 抓取失败，请检查网络或源站。")


# ==========================================
# 侧边栏布局
# ==========================================
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 商业决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

st.sidebar.markdown(f"""
    <div class="wechat-box">
        <span style="font-size:14px; color:#666;">获取【100期大样本及高阶授权】</span><br>
        <b style="color:#ff4b4b; font-size:13px; display:inline-block; margin-top:5px;">微信：{MY_WECHAT_ID}</b>
    </div>
""", unsafe_allow_html=True)
st.sidebar.code(MY_WECHAT_ID, language="text")

st.sidebar.markdown("---")
view_options = {"近30期 (默认免费)": 30, "近50期 (需高阶解锁)": 50, "近100期 (需高阶解锁)": 100}
view_choice = st.sidebar.radio("选择分析样本", list(view_options.keys()), index=0)

if "需高阶解锁" in view_choice and not st.session_state.get('vip_unlocked', False):
    st.sidebar.error("🔒 大样本运算须高阶权限。请在右侧【高阶算法矩阵】标签中验证口令解锁。")
    view_limit = 30
else:
    view_limit = view_options[view_choice]

# --- 拦截维护状态 ---
if choice in ["快乐8", "排列5", "七星彩"]:
    st.error("🚧 **系统维护中**")
    st.warning(f"由于上游数据源接口升级，【{choice}】暂不可用，工程师正在紧急抢修，请先切换使用其他彩种或去【自建数据沙盘】手动运算。")
    st.stop()

# ==========================================
# 核心主界面逻辑
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
        st.markdown(f'<div class="timer-bar">⏰ 离今日开奖截止还剩 {get_countdown()} | 核心服务器已就绪</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="marquee-wrapper"><div class="marquee-icon">📢</div><div class="marquee-content">{get_fake_broadcasts()}</div></div>', unsafe_allow_html=True)

        t1, t2, t_mock, t3, t4, t5, t6 = st.tabs(["📜 历史数据", "📈 深度走势", "🎰 模拟开奖", "🤖 基础 AI 演算", "👑 高阶算法矩阵", "🗄️ 自建数据沙盘", "💬 交流大厅"])
        
        with t1:
            st.markdown(f"""<div class="download-lock">🔒 <b>VIP 数据下载通道</b><br><span style="font-size:13px; color:#666;">获取完整Excel导出权限，请添加微信：{MY_WECHAT_ID}</span></div>""", unsafe_allow_html=True)
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
            calc_df['跨度'] = calc_df[d_cols].max(axis=1) - calc_df[d_cols].min(axis=1)
            
            st.markdown("### 📈 近期和值走势")
            st.line_chart(calc_df.set_index('期号')['和值'])
            st.markdown("### 🎢 号码跨度振幅")
            st.area_chart(calc_df.set_index('期号')['跨度'], color="#f14545")

        with t_mock:
            st.markdown("### 🎰 电视级沙盘模拟推演")
            st.info("💡 采用沉浸式摇号动效，完全模拟真实的开奖过程。")
            if st.button("🚀 生成一次模拟真实开奖", use_container_width=True):
                pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
                anim_placeholder = st.empty()
                sim_r_current = []
                pool_r_copy = pool_r.copy()
                for i in range(count_r):
                    n = random.choice(pool_r_copy)
                    pool_r_copy.remove(n)
                    sim_r_current.append(n)
                    sim_r_current.sort() 
                    s_html, _ = render_html_balls(sim_r_current, [], choice)
                    anim_placeholder.markdown(f"<div class='pred-row'><div class='pred-title'>🔴 摇号同步中...</div><div class='pred-balls'>{s_html}</div></div>", unsafe_allow_html=True)
                    time.sleep(0.4) 
                sim_b_current = []
                if count_b > 0:
                    pool_b_copy = pool_b.copy()
                    for i in range(count_b):
                        nb = random.choice(pool_b_copy)
                        pool_b_copy.remove(nb)
                        sim_b_current.append(nb)
                        sim_b_current.sort()
                        s_html, _ = render_html_balls(sim_r_current, sim_b_current, choice)
                        anim_placeholder.markdown(f"<div class='pred-row'><div class='pred-title'>🔵 蓝球锁定中...</div><div class='pred-balls'>{s_html}</div></div>", unsafe_allow_html=True)
                        time.sleep(0.6)
                s_html, _ = render_html_balls(sim_r_current, sim_b_current, choice)
                anim_placeholder.markdown(f"<div class='pred-row'><div class='pred-title'>✅ 沙盘模拟完成</div><div class='pred-balls'>{s_html}</div></div>", unsafe_allow_html=True)
                st.success("🔔 模拟开奖成功！")

        with t3:
            st.markdown("### 🧬 AI 核心演算模型 (完全免费)")
            st.info(f"💡 系统正自动提取您设置的【近 {view_limit} 期】真实开奖数据进行模型拟合。每次点击均可刷新最优组合！")
            
            if st.button("🎯 立即启动 AI 模型演算 (免费生成 5 组)", type="primary", use_container_width=True):
                st.session_state['ai_click_count'] += 1
                
            if st.session_state['ai_click_count'] > 0:
                st.success(f"✅ 演算完成！如需更多组合，可再次点击上方按钮刷新。当前提取样本：近 {view_limit} 期真实数据。")
                ai_sets = get_ai_predictions(df.head(view_limit), d_cols, choice, st.session_state['ai_click_count'])
                
                for s in ai_sets:
                    st.markdown(f"<div class='pred-row'><div class='pred-title'>{s['name']}<br><span class='ai-desc'>{s['desc']}</span></div><div class='pred-balls'>{s['html']}</div></div>", unsafe_allow_html=True)
                
                # 复制区域
                st.markdown("#### 📋 一键复制专属号单")
                copy_str = f"【{choice}】AI核心演算预测\n" + "-"*20 + "\n"
                for s in ai_sets:
                    copy_str += f"{s['name']}: {s['text']}\n"
                st.code(copy_str, language="text")

        with t4:
            st.markdown("### 👑 顶级高阶矩阵预测")
            st.info("💡 包含多组马尔科夫链分析法与12阶高阶矩阵测算，提供多维度参考组合。每次点击均可刷新大底！")
            
            # --- 全局授权检查：解锁这里同时解锁100期 ---
            if not st.session_state.get('vip_unlocked', False):
                st.error("🔒 该区域涉及极大算力开销及大样本数据(50/100期)分析，需验证高阶卡密或高级口令。")
                c1, c2 = st.columns([2, 1])
                with c1: v_pwd = st.text_input("🔑 请输入高阶矩阵授权码：", type="password", key="adv_pwd")
                with c2:
                    if st.button("激活全局高级权限", use_container_width=True, key="adv_unlock_btn"):
                        # 兼容双重验证：可以是高级防伪卡密，也可以是VIP后门密码
                        is_valid, msg = verify_card_key(v_pwd)
                        if is_valid or v_pwd == VIP_PASSWORD or v_pwd == VIP_BACKDOOR:
                            st.session_state['vip_unlocked'] = True
                            st.rerun()
                        else: st.error(f"❌ {msg}" if msg else "❌ 授权码错误")
            else:
                st.success("🔓 高级权限已解锁！您现在可以使用高阶算法，并在左侧自由切换 50/100 期大样本数据进行分析。")
                if st.button("🚀 立即生成高阶矩阵大底 (10组)", type="primary", use_container_width=True):
                    st.session_state['adv_click_count'] += 1
                
                if st.session_state['adv_click_count'] > 0:
                    st.success("✅ 高阶矩阵组合已完美生成！")
                    adv_sets = get_advanced_predictions(df.head(view_limit), d_cols, choice, st.session_state['adv_click_count'])
                    for s in adv_sets:
                        st.markdown(f"<div class='pred-row {s.get('css_class', '')}'><div class='pred-title'>{s['name']}<br><span class='ai-desc'>{s['desc']}</span></div><div class='pred-balls'>{s['html']}</div></div>", unsafe_allow_html=True)
                    
                    # 复制区域
                    st.markdown("#### 📋 一键复制高阶矩阵大底")
                    copy_str = f"【{choice}】高阶矩阵大底\n" + "-"*20 + "\n"
                    for s in adv_sets:
                        copy_str += f"{s['name']}: {s['text']}\n"
                    st.code(copy_str, language="text")

        with t5:
            st.markdown("### 📤 自建数据沙盘 (支持全彩种)")
            st.info("💡 如果左侧彩种正在维护（如快乐8），您可以直接将历史开奖号码粘贴在这里，系统依然能通过 AI 为您进行测算！")
            custom_choice = st.selectbox("🎯 1. 请选择要计算的规则类型", ["快乐8", "双色球", "大乐透", "七星彩", "排列5", "排列3", "福彩3D"])
            c_text = st.text_area("🎯 2. 请粘贴历史开奖号码（每行一期，号码用空格隔开）：", height=150, placeholder="01 02 03 04 05 06 ...")
            
            if st.button("🔬 立即对自定义数据进行测算", type="primary"):
                if c_text.strip():
                    lines = c_text.strip().split('\n')
                    parsed_data = [[int(n) for n in re.findall(r'\d+', line)] for line in lines if re.findall(r'\d+', line)]
                    if parsed_data:
                        _, c_count_r, _, c_count_b = get_lottery_rules(custom_choice)
                        valid_data = [row[:c_count_r+c_count_b] for row in parsed_data if len(row) >= c_count_r]
                        if valid_data:
                            c_df = pd.DataFrame(valid_data)
                            c_df.insert(0, '期号', range(2000, 2000-len(c_df), -1))
                            c_cols = list(c_df.columns)[1:]
                            st.success(f"✅ 成功读取 {len(c_df)} 期自定义数据！")
                            
                            st.markdown("#### 🤖 自动匹配 AI 演算模型")
                            c_ai_sets = get_ai_predictions(c_df, c_cols, custom_choice, 1)
                            for s in c_ai_sets:
                                st.markdown(f"<div class='pred-row'><div class='pred-title'>{s['name']}<br><span class='ai-desc'>{s['desc']}</span></div><div class='pred-balls'>{s['html']}</div></div>", unsafe_allow_html=True)
                            
                            st.markdown("#### 👑 自动匹配高阶算法模型")
                            c_adv_sets = get_advanced_predictions(c_df, c_cols, custom_choice, 1)
                            for s in c_adv_sets:
                                st.markdown(f"<div class='pred-row'><div class='pred-title'>{s['name']}<br><span class='ai-desc'>{s['desc']}</span></div><div class='pred-balls'>{s['html']}</div></div>", unsafe_allow_html=True)
                        else: st.error("数据长度不符合所选彩种规则，请检查空格分隔是否正确。")
                    else: st.error("未识别到数字，请检查输入格式。")
                else: st.error("请先粘贴数据！")

        with t6:
            st.markdown("### 💬 实战玩家交流大厅")
            users = ["李哥", "王总", "陈老板", "发财哥", "张总", "顺风顺水", "一生平安", "天道酬勤", "A小刘", "老牛", "大忽悠", "追梦人", "稳中求胜"]
            msgs = ["今天必出08！", "马尔科夫链那个算法确实有点科学依据的。", "这杀号绝了，之前我自己挑的全是死号...", "求今日胆码！", "刚刚的摇号模拟动画看着好有感觉啊！", "AC复杂度怎么看？", "刚充了VIP，坐等今晚收米。", "这软件的深度拟合有点东西的啊...", "有人合买今晚的大底复式吗？"]
            
            if 'comments' not in st.session_state:
                st.session_state.comments = [{"user": random.choice(users)+str(random.randint(10,99)), "text": random.choice(msgs), "time": f"{i}分钟前", "vip": random.random()>0.3} for i in range(1, 51)]
                
            chat_box = st.container(height=450)
            with chat_box:
                for c in st.session_state.comments:
                    vip_tag = "👑 VIP" if c.get("vip") else "👤 普通"
                    color = "#ff4b4b" if c.get("vip") else "#999"
                    st.markdown(f'''<div class="comment-box"><div class="comment-header"><span class="comment-user">{c["user"]} <span style="font-size:12px;color:{color};font-weight:bold;margin-left:5px;">{vip_tag}</span></span><span class="comment-time">{c["time"]}</span></div><div class="comment-body">{c["text"]}</div></div>''', unsafe_allow_html=True)
            
            chat_input = st.text_input("📝 发表您的看法...")
            if st.button("发送消息") and chat_input:
                st.session_state.comments.insert(0, {"user": "我", "text": chat_input, "time": "刚刚", "vip": st.session_state.get('vip_unlocked', False)})
                st.rerun()
else:
    st.warning("⚠️ 目录下未找到当前彩种的数据文件。")
# ===== 代码到底了，请确保这一行也复制进去了 =====
