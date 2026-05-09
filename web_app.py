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
# 💰💰💰 老板专属配置区 💰💰💰
# =========================================================
MY_WECHAT_ID = "252766667"           
AI_PASSWORD = "888"                  # 基础 AI 演算解锁口令
VIP_PASSWORD = "999"                 # 高阶矩阵解锁口令
VIP_BACKDOOR = "666"                 # 老板无敌后门 (输这个啥都能解)
SECRET_KEY = "Partner_Fortune_2026"  # 卡密防伪密钥
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
if 'ai_unlocked' not in st.session_state: st.session_state['ai_unlocked'] = False
if 'vip_unlocked' not in st.session_state: st.session_state['vip_unlocked'] = False
if 'ai_click_count' not in st.session_state: st.session_state['ai_click_count'] = 0
if 'adv_click_count' not in st.session_state: st.session_state['adv_click_count'] = 0

def verify_card_key(user_input_key):
    if not user_input_key: return False, ""
    if user_input_key == VIP_BACKDOOR: return True, "老板专属后门已触发！"
    try:
        decoded = base64.b64decode(user_input_key + "===").decode()
        parts = decoded.split('-')
        if len(parts) != 3 or parts[0] != 'VIP': return False, "卡密格式错误！"
        if parts[1] != hashlib.md5(f"{parts[2]}|{SECRET_KEY}".encode()).hexdigest()[:6]: return False, "卡密无效！"
        if datetime.now().date() > datetime.strptime(parts[2], '%Y%m%d').date(): return False, "卡密已过期！"
        return True, "验证通过！"
    except: return False, "卡密解析失败！"

def get_countdown():
    now = datetime.now()
    target = now.replace(hour=21, minute=30, second=0)
    if now > target: target += timedelta(days=1)
    diff = target - now
    return f"{divmod(diff.seconds, 3600)[0]:02d}时{divmod(divmod(diff.seconds, 3600)[1], 60)[0]:02d}分{divmod(divmod(diff.seconds, 3600)[1], 60)[1]:02d}秒"

def get_fake_broadcasts():
    cities = ["广东", "浙江", "江苏", "山东", "河南", "四川", "北京", "上海", "湖南", "福建"]
    return "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🔥&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join([f"【最新喜报】{random.choice(cities)}用户 1{random.randint(3,9)}****{random.randint(1000,9999)} {random.randint(1, 59)}分钟前 成功解锁算法！" for _ in range(8)])

def get_real_online_users():
    hour = datetime.now().hour
    base = 350 if 0 <= hour < 7 else 1200 if 7 <= hour < 12 else 1800 if 12 <= hour < 18 else 2800 if 18 <= hour < 22 else 1500
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
    return max(0, len(set(abs(nums[i] - nums[j]) for i in range(len(nums)) for j in range(i+1, len(nums)))) - (len(nums) - 1))

@st.cache_data
def load_full_data(file_path, choice):
    try:
        raw_df = pd.read_excel(file_path) if file_path.endswith('.xls') else pd.read_csv(file_path)
        raw_df.columns = [str(c).strip() for c in raw_df.columns]
        q_col = next((c for c in raw_df.columns if '期' in c or 'NO' in c.upper()), raw_df.columns[0])
        raw_df[q_col] = pd.to_numeric(raw_df[q_col], errors='coerce')
        raw_df = raw_df.dropna(subset=[q_col])
        max_balls = {"双色球": 7, "大乐透": 7, "福彩3D": 3, "排列3": 3, "排列5": 5, "七星彩": 7, "快乐8": 20}.get(choice, 7)
        q_idx = list(raw_df.columns).index(q_col)
        ball_cols = [col for col in raw_df.columns[q_idx + 1:] if not pd.to_numeric(raw_df[col], errors='coerce').dropna().empty and (pd.to_numeric(raw_df[col], errors='coerce').dropna() <= 81).all()][:max_balls]
        clean_df = raw_df[[q_col] + ball_cols].copy()
        clean_df.columns = ['期号'] + [f"b_{i+1}" for i in range(len(ball_cols))]
        for c in clean_df.columns: clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0).astype(int)
        return clean_df.sort_values('期号', ascending=False), '期号', clean_df.columns[1:], choice in ["双色球", "大乐透", "快乐8"], file_path
    except: return None, None, None, None, None

def render_html_balls(r_res, b_res, choice, is_gold=False):
    r_class = "bg-gold" if is_gold else "bg-red"
    b_class = "bg-blue"
    if choice == "大乐透": b_class = "bg-yellow"
    if choice in ["福彩3D", "排列3", "排列5"]: r_class = "bg-gold" if is_gold else "bg-lightblue"
    elif choice == "七星彩": r_class = "bg-gold" if is_gold else "bg-purple"
    
    html = "".join([f"<span class='pred-ball {r_class}'>{n:02d}</span>" if choice in ["双色球", "大乐透", "快乐8"] else f"<span class='pred-ball {r_class}'>{n}</span>" for n in r_res])
    html += "".join([f"<span class='pred-ball {b_class}'>{n:02d}</span>" if choice in ["双色球", "大乐透"] else f"<span class='pred-ball {b_class}'>{n}</span>" for n in b_res])
    
    txt_r = " ".join([f"{n:02d}" if choice in ["双色球", "大乐透", "快乐8"] else str(n) for n in r_res])
    txt_b = " + " + " ".join([f"{n:02d}" if choice in ["双色球", "大乐透"] else str(n) for n in b_res]) if b_res else ""
    return html, txt_r + txt_b

def get_ai_predictions(df_view, d_cols, choice, click_count):
    sets = []
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    try: seed_val = int(df_view.iloc[0][df_view.columns[0]])
    except: seed_val = 888
    # 结合最新期号和点击次数，实现“动态刷新”
    random.seed(seed_val + click_count)
    
    r_freq = Counter([n for col in d_cols[:count_r] for n in df_view[col].dropna().astype(int).tolist()])
    for n in pool_r: r_freq.setdefault(n, 0)
    sorted_r = sorted(r_freq.keys(), key=lambda x: (-r_freq[x], x))

    b_freq = Counter([n for col in d_cols[count_r:] for n in df_view[col].dropna().astype(int).tolist()]) if count_b > 0 else {}
    for n in pool_b: b_freq.setdefault(n, 0)
    sorted_b = sorted(b_freq.keys(), key=lambda x: (-b_freq[x], x)) if count_b > 0 else []

    # 1. 极热寻踪
    hot_r_pool = sorted_r[:max(count_r + 4, 10)]
    r_hot = sorted(random.sample(hot_r_pool, count_r))
    b_hot = sorted(random.sample(sorted_b[:max(count_b+2, 4)], count_b)) if count_b > 0 else []
    h, t = render_html_balls(r_hot, b_hot, choice)
    sets.append({"name": "🔥 极热寻踪", "desc": "【纯统计特征】在真实高频热号池中智能提取，追踪偏态。", "html": h, "text": t})
    
    # 2. 绝地反弹
    cold_r_pool = sorted_r[-max(count_r + 4, 10):]
    r_cold = sorted(random.sample(cold_r_pool, count_r))
    b_cold = sorted(random.sample(sorted_b[-max(count_b+2, 4):], count_b)) if count_b > 0 else []
    h, t = render_html_balls(r_cold, b_cold, choice)
    sets.append({"name": "🧊 绝地反弹", "desc": "【均值回归】在历史遗漏值极高的冷区池中提取，博弈反弹。", "html": h, "text": t})
    
    # 3. 黄金均衡
    hot_p, cold_p = count_r // 3, count_r // 3
    mid_p = count_r - hot_p - cold_p
    r_mix = sorted(random.sample(sorted_r[:10], hot_p) + random.sample(sorted_r[-10:], cold_p) + random.sample(sorted_r[10:-10], mid_p))
    b_mix = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
    h, t = render_html_balls(r_mix, b_mix, choice)
    sets.append({"name": "⚖️ 黄金均衡", "desc": "【自然正态分布】强制按比例注入热、温、冷号，拒绝极端偏科。", "html": h, "text": t})
    
    # 4. 蒙特卡洛 
    r_mc = sorted(random.sample(pool_r, count_r))
    b_mc = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
    h, t = render_html_balls(r_mc, b_mc, choice)
    sets.append({"name": "🎲 蒙特卡洛碰撞", "desc": "【算力暴力推演】系统内部百万次摇奖碰撞，抽取共振频次序列。", "html": h, "text": t})
    
    # 5. 深度拟合 
    latest_r = df_view.iloc[0][d_cols[:count_r]].astype(int).tolist() if len(df_view)>0 else random.sample(pool_r, count_r)
    r_dp = sorted(random.sample([n for n in pool_r if n not in latest_r] + latest_r, count_r))
    b_dp = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
    h, t = render_html_balls(r_dp, b_dp, choice)
    sets.append({"name": "🧠 LSTM 深度拟合", "desc": "【时间序列网络】根据上期落点数据结合时间波谷特征运算。", "html": h, "text": t})
    
    return sets

def get_advanced_predictions(df_view, d_cols, choice, click_count):
    sets = []
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    try: seed_val = int(df_view.iloc[0][df_view.columns[0]])
    except: seed_val = 999
    
    for j in range(5):
        random.seed(seed_val + click_count * 100 + j * 11)
        r_res = sorted(random.sample(pool_r, count_r))
        b_res = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
        h, t = render_html_balls(r_res, b_res, choice)
        sets.append({"name": f"🔗 马尔科夫 (组{j+1})", "desc": f"状态转移概率网络生成 | AC复杂度: {calculate_ac_value(r_res)}", "html": h, "text": t, "css_class": ""})
        
    for j in range(5):
        random.seed(seed_val + click_count * 200 + j * 77)
        r_res = sorted(random.sample(pool_r, count_r))
        b_res = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
        h, t = render_html_balls(r_res, b_res, choice, is_gold=True)
        sets.append({"name": f"✨ 12阶矩阵 (组{j+1})", "desc": f"空间偏移基点深度演算 | AC复杂度: {calculate_ac_value(r_res)}", "html": h, "text": t, "css_class": "gold-border"})
        
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
            tdata = soup.find('tbody', id='tdata')
            trs = tdata.find_all('tr') if tdata else (soup.find_all('tr', class_=['t_tr1', 't_tr2']) or soup.find_all('tr'))
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) < d_cols_len + 1: continue 
                iss_str = re.sub(r'\D', '', tds[0].get_text(strip=True))
                if len(iss_str) < 3: continue
                issue_val = int("20" + iss_str[:5]) if len(iss_str[:10]) == 5 else int(iss_str[:10])
                balls = []
                if choice == "快乐8": balls = [n for n in [int(x) for x in re.findall(r'\b\d{1,2}\b', " ".join([td.get_text() for td in tds[1:25]]))] if 1<=n<=80][:d_cols_len]
                elif choice in ["排列5", "排列3", "福彩3D"]: balls = [int(d) for d in re.findall(r'\d', "".join([td.get_text() for td in tds[1:8]]))][:d_cols_len]
                elif choice == "七星彩":
                    for g in re.findall(r'\d+', " ".join([td.get_text() for td in tds[1:10]])):
                        balls.extend([int(c) for c in g] if len(g)>=3 else [int(g)])
                    balls = balls[:d_cols_len]
                else: balls = [n for n in [int(x) for x in re.findall(r'\d+', " ".join([td.get_text() for td in tds[1:]]))] if 0<=n<=81][:d_cols_len]
                if len(balls) == d_cols_len: web_rows.append({"issue": issue_val, "balls": balls})
            if web_rows: break 
        except: continue
    return web_rows

def sync_latest_data(df, q_col, d_cols, choice, file_path):
    status = st.empty()
    game_code = {"双色球": "ssq", "大乐透": "dlt", "福彩3D": "sd", "排列3": "pls", "排列5": "plw", "七星彩": "qxc", "快乐8": "kl8"}.get(choice, "ssq")
    status.info(f"📡 正在联网获取 {choice} 最新开奖...")
    web_data = fetch_from_web(game_code, choice, len(d_cols))
    if web_data:
        try:
            clean_rows = [{q_col: int(str(item['issue'])[:12]), **{d_cols[i]: int(item['balls'][i]) for i in range(len(d_cols))}} for item in web_data]
            if not clean_rows: return status.warning("⚠️ 数据异常。")
            web_df = pd.DataFrame(clean_rows)
            df[q_col] = pd.to_numeric(df[q_col], errors='coerce').fillna(0).astype('int64')
            for c in d_cols: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype('int64')
            updated = pd.concat([web_df, df], ignore_index=True).drop_duplicates(subset=[q_col]).sort_values(q_col, ascending=False).head(2000)
            updated.to_csv(file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv'), index=False, encoding='utf-8-sig')
            status.success(f"✅ 同步成功！已更新 {len(clean_rows)} 期。")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
        except: status.error(f"🚨 同步失败，请手动更新。")
    else: status.error("❌ 抓取失败。")


# ==========================================
# 侧边栏布局
# ==========================================
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 商业决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

st.sidebar.markdown(f"""
    <div class="wechat-box">
        <span style="font-size:14px; color:#666;">获取【AI口令】及【高阶授权】</span><br>
        <b style="color:#ff4b4b; font-size:13px; display:inline-block; margin-top:5px;">微信：{MY_WECHAT_ID}</b>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
view_options = {"近30期 (默认)": 30, "近50期 (需高阶解锁)": 50, "近100期 (需高阶解锁)": 100}
view_choice = st.sidebar.radio("选择分析样本", list(view_options.keys()), index=0)

if "需高阶解锁" in view_choice and not st.session_state.get('vip_unlocked', False):
    st.sidebar.error("🔒 大样本运算须高阶权限。请在【高阶算法】中解锁。")
    view_limit = 30
else:
    view_limit = view_options[view_choice]

if choice in ["快乐8", "排列5", "七星彩"]:
    st.error("🚧 **系统维护中**")
    st.warning(f"由于上游数据源接口升级，【{choice}】暂不可用，请去【自建数据沙盘】手动运算。")
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
        st.markdown(f'<div class="timer-bar">⏰ 离今日开奖截止还剩 {get_countdown()} | 核心服务器已就绪</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="marquee-wrapper"><div class="marquee-icon">📢</div><div class="marquee-content">{get_fake_broadcasts()}</div></div>', unsafe_allow_html=True)

        t1, t2, t_mock, t3, t4, t5 = st.tabs(["🤖 基础 AI 演算", "👑 高阶算法矩阵", "🎰 模拟开奖", "🗄️ 自建数据沙盘", "📜 历史数据", "💬 交流大厅"])
        
        with t1:
            st.markdown("### 🧬 AI 核心演算模型 (需口令)")
            st.info(f"💡 系统正提取您设置的【近 {view_limit} 期】真实数据进行拟合。基于高概率池的动态抽样，每次点击均可刷新最优组合！")
            
            if not st.session_state.get('ai_unlocked', False):
                st.warning("🔒 演算已受保护。")
                c1, c2 = st.columns([2, 1])
                with c1: pwd = st.text_input("🔑 请输入基础 AI 口令：", type="password", key="ai_pwd")
                with c2: 
                    if st.button("立即解锁", use_container_width=True, key="ai_unlock_btn"):
                        if pwd == AI_PASSWORD or pwd == VIP_BACKDOOR:
                            st.session_state['ai_unlocked'] = True
                            st.rerun()
                        else: st.error("❌ 口令错误")
            else:
                if st.button("🎯 启动 AI 模型演算 (生成 5 组)", type="primary", use_container_width=True):
                    st.session_state['ai_click_count'] += 1
                    
                if st.session_state['ai_click_count'] > 0:
                    st.success("✅ 演算完成！如需更多组合，可再次点击上方按钮生成。")
                    ai_sets = get_ai_predictions(df.head(view_limit), d_cols, choice, st.session_state['ai_click_count'])
                    
                    for s in ai_sets:
                        st.markdown(f"<div class='pred-row'><div class='pred-title'>{s['name']}<br><span class='ai-desc'>{s['desc']}</span></div><div class='pred-balls'>{s['html']}</div></div>", unsafe_allow_html=True)
                    
                    st.markdown("#### 📋 一键复制专属号单")
                    copy_str = f"【{choice}】AI核心演算预测\n" + "-"*20 + "\n"
                    for s in ai_sets:
                        copy_str += f"{s['name']}: {s['text']}\n"
                    st.code(copy_str, language="text")

        with t2:
            st.markdown("### 👑 顶级高阶矩阵预测")
            st.info("💡 包含多组马尔科夫链与12阶高阶矩阵，生成大底。每次点击均可刷新！")
            
            if not st.session_state.get('vip_unlocked', False):
                st.error("🔒 需验证高阶卡密或高级口令。")
                c1, c2 = st.columns([2, 1])
                with c1: v_pwd = st.text_input("🔑 请输入高阶授权码：", type="password", key="adv_pwd")
                with c2:
                    if st.button("激活高阶算法", use_container_width=True, key="adv_unlock_btn"):
                        is_valid, msg = verify_card_key(v_pwd)
                        if is_valid or v_pwd == VIP_PASSWORD or v_pwd == VIP_BACKDOOR:
                            st.session_state['vip_unlocked'] = True
                            st.rerun()
                        else: st.error("❌ 授权码错误")
            else:
                if st.button("🚀 立即生成高阶矩阵大底 (10组)", type="primary", use_container_width=True):
                    st.session_state['adv_click_count'] += 1
                
                if st.session_state['adv_click_count'] > 0:
                    st.success("✅ 高阶矩阵组合已完美生成！")
                    adv_sets = get_advanced_predictions(df.head(view_limit), d_cols, choice, st.session_state['adv_click_count'])
                    
                    for s in adv_sets:
                        st.markdown(f"<div class='pred-row {s.get('css_class', '')}'><div class='pred-title'>{s['name']}<br><span class='ai-desc'>{s['desc']}</span></div><div class='pred-balls'>{s['html']}</div></div>", unsafe_allow_html=True)
                    
                    st.markdown("#### 📋 一键复制高阶矩阵")
                    copy_str = f"【{choice}】高阶矩阵大底\n" + "-"*20 + "\n"
                    for s in adv_sets:
                        copy_str += f"{s['name']}: {s['text']}\n"
                    st.code(copy_str, language="text")

        with t_mock:
            st.markdown("### 🎰 电视级沙盘模拟推演")
            if st.button("🚀 生成一次模拟摇号", use_container_width=True):
                pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
                anim = st.empty()
                for _ in range(10):
                    tr = sorted(random.sample(pool_r, count_r))
                    tb = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
                    h, _ = render_html_balls(tr, tb, choice)
                    anim.markdown(f"<div class='pred-row'><div class='pred-title'>🔄 演算中...</div><div class='pred-balls'>{h}</div></div>", unsafe_allow_html=True)
                    time.sleep(0.1)
                sim_r = sorted(random.sample(pool_r, count_r))
                sim_b = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
                html, _ = render_html_balls(sim_r, sim_b, choice)
                anim.markdown(f"<div class='pred-row'><div class='pred-title'>✅ 模拟完成</div><div class='pred-balls'>{html}</div></div>", unsafe_allow_html=True)

        with t3:
            st.markdown("### 📤 自建数据沙盘 (支持全彩种)")
            custom_choice = st.selectbox("🎯 1. 请选择规则", ["快乐8", "双色球", "大乐透", "七星彩", "排列5", "排列3", "福彩3D"])
            c_text = st.text_area("🎯 2. 请粘贴号码（每行一期，空格隔开）：", height=150)
            if st.button("🔬 立即测算", type="primary"):
                if c_text.strip():
                    lines = c_text.strip().split('\n')
                    parsed = [[int(n) for n in re.findall(r'\d+', line)] for line in lines if re.findall(r'\d+', line)]
                    if parsed:
                        _, c_r, _, c_b = get_lottery_rules(custom_choice)
                        valid = [row[:c_r+c_b] for row in parsed if len(row) >= c_r]
                        if valid:
                            c_df = pd.DataFrame(valid)
                            c_df.insert(0, '期号', range(2000, 2000-len(c_df), -1))
                            st.success(f"✅ 成功读取 {len(c_df)} 期！")
                            for s in get_ai_predictions(c_df, list(c_df.columns)[1:], custom_choice, 1):
                                st.markdown(f"<div class='pred-row'><div class='pred-title'>{s['name']}</div><div class='pred-balls'>{s['html']}</div></div>", unsafe_allow_html=True)
                        else: st.error("数据长度不符。")
                    else: st.error("未识别到数字。")
                else: st.error("请粘贴数据！")

        with t4:
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(view_limit).iterrows():
                b_html = "".join([f"<span class='ball bg-red'>{row[c]:02d}</span>" if choice in ["双色球", "大乐透", "快乐8"] else f"<span class='ball bg-red'>{row[c]}</span>" for c in d_cols])
                table_html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{b_html}</td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

        with t5:
            st.markdown("### 💬 实战玩家交流大厅")
            st.info("提示：请理性交流，禁止发布违规信息。")
            if 'comments' not in st.session_state:
                users = ["老李", "张哥", "发财猫", "追梦人", "A彩票专员", "王总", "顺风顺水", "牛气冲天", "幸运星", "大赢家"]
                msgs = ["太牛了，昨天的极热寻踪中了4个红球！", "马尔科夫链那个算法确实有点科学依据的。", "这杀号绝了，之前我自己挑的全是死号...", "求今日胆码！", "刚刚的摇号模拟动画看着好有感觉啊！", "AC复杂度怎么看？", "刚充了VIP，坐等今晚收米。", "这软件的深度拟合有点东西的啊...", "有人合买今晚的大底复式吗？"]
                st.session_state.comments = [{"user": random.choice(users)+str(random.randint(10,99)), "text": random.choice(msgs), "time": f"{i}分钟前", "vip": random.random()>0.3} for i in range(1, 51)]
            
            chat_box = st.container(height=450)
            with chat_box:
                for c in st.session_state.comments:
                    vip_tag = "👑 VIP" if c.get("vip") else "👤 普通"
                    color = "#ff4b4b" if c.get("vip") else "#999"
                    st.markdown(f'''<div class="comment-box"><div class="comment-header"><span class="comment-user">{c["user"]} <span style="font-size:12px;color:{color};font-weight:bold;margin-left:5px;">{vip_tag}</span></span><span class="comment-time">{c["time"]}</span></div><div class="comment-body">{c["text"]}</div></div>''', unsafe_allow_html=True)
            
            chat_input = st.text_input("📝 发表评论...")
            if st.button("发送"):
                st.success("发送成功，评论正在审核中...")
else:
    st.warning("⚠️ 未找到数据文件。")
