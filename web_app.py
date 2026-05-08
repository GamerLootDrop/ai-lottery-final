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

# =========================================================
# 💰💰💰 老板专属配置区 (样板间已开启 666 至尊权限) 💰💰💰
# =========================================================
MY_WECHAT_ID = "252766667"           
CODE_VIP = "888"                     # 基础VIP口令
CODE_SUPREME = "666"                 # 顶级至尊口令 (样板间特供)
# =========================================================

# --- 0. 隐形访客统计 ---
visit_file = "visit_log.txt"
if not os.path.exists(visit_file):
    with open(visit_file, "w") as f: f.write("0")
with open(visit_file, "r") as f:
    current_v = int(f.read())
new_v = current_v + 1
with open(visit_file, "w") as f: f.write(str(new_v))

# --- 1. 深度定制样式表 (新增金色至尊样式) ---
st.set_page_config(page_title="AI 大数据决策终端 - 至尊版", layout="wide")
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
    
    /* 金色球样式 */
    .bg-gold { background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%); color: white; border: 1px solid #fff; box-shadow: 0 0 10px rgba(255,140,0,0.6); animation: pulse 2s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }

    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 5px; border-left: 5px solid #f14545; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; position: relative; }
    .pred-row-gold { background: #fffef0; border-left: 5px solid #ffd700; border: 1px solid #ffeeba; }
    .pred-title { width: 150px; font-weight: bold; color: #444; font-size: 15px; }
    .pred-balls { flex-grow: 1; display: flex; flex-wrap: wrap; max-width: 400px;} 
    .pred-ball { display: inline-block; width: 34px; height: 34px; line-height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 4px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.15); }
    
    .vip-locked { filter: blur(6px); user-select: none; pointer-events: none; }
    .lock-overlay { position: absolute; right: 20px; top: 50%; transform: translateY(-50%); background: rgba(255,255,255,0.95); padding: 6px 15px; border: 2px dashed #ff4b4b; border-radius: 5px; color: #ff4b4b; font-size: 14px; font-weight: bold; z-index: 10; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    
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
    .legal-footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #eaeaea; text-align: center; color: #999; font-size: 12px; line-height: 1.8; }
    </style>
""", unsafe_allow_html=True)

# --- 工具函数 (保持老板原版) ---
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
    algos = ["极热寻踪", "绝地反弹", "黄金均衡", "蒙特卡洛", "深度拟合", "12阶空间位移"]
    broadcast_texts = []
    for _ in range(5):
        city = random.choice(cities)
        phone = f"1{random.randint(3,9)}{random.randint(0,9)}****{random.randint(1000,9999)}"
        algo = random.choice(algos)
        mins = random.randint(1, 59)
        broadcast_texts.append(f"【最新喜报】{city}用户 {phone} {mins}分钟前 成功解锁「{algo}」策略！")
    return "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🔥&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join(broadcast_texts)

# --- 核心：数据载入 (保持老板原版) ---
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

# --- 核心演算 (增加 12 阶至尊逻辑) ---
def get_real_prediction(df_view, d_cols, choice, is_supreme=False):
    sets = []
    all_nums = []
    for col in d_cols:
        all_nums.extend(df_view[col].dropna().astype(int).tolist())
    freq_dict = Counter(all_nums)
    sorted_by_freq = [item[0] for item in freq_dict.most_common()]
    
    rules = {
        "双色球": (list(range(1, 34)), 6, list(range(1, 17)), 1),
        "大乐透": (list(range(1, 36)), 5, list(range(1, 13)), 2),
        "七星彩": (list(range(0, 10)), 6, list(range(0, 15)), 1),
        "快乐8": (list(range(1, 81)), 20, [], 0),
        "福彩3D": (list(range(0, 10)), 3, [], 0),
        "排列3": (list(range(0, 10)), 3, [], 0),
        "排列5": (list(range(0, 10)), 5, [], 0)
    }
    
    pool_r, count_r, pool_b, count_b = rules.get(choice, rules["双色球"])
    hot_list_r = [n for n in sorted_by_freq if n in pool_r]
    hot_list_r.extend([n for n in pool_r if n not in hot_list_r]) 
    cold_list_r = hot_list_r[::-1] 
    
    algos = [
        {"name": "🔥 极热寻踪", "type": "hot", "vip": False},
        {"name": "🧊 绝地反弹", "type": "cold", "vip": False},
        {"name": "⚖️ 黄金均衡", "type": "mix", "vip": False},
        {"name": "🎲 蒙特卡洛引擎", "type": "monte", "vip": True},
        {"name": "🧠 深度拟合网络", "type": "fit", "vip": True}
    ]
    
    # 如果是 666 口令，额外注入“12阶空间位移”
    if is_supreme:
        algos.append({"name": "🏆 12阶至尊空间位移", "type": "supreme", "vip": True})
    
    for algo in algos:
        r_res, b_res = [], []
        if algo['type'] == 'hot':
            r_res = sorted(random.sample(hot_list_r[:count_r+2], count_r))
        elif algo['type'] == 'cold':
            r_res = sorted(random.sample(cold_list_r[:count_r+2], count_r))
        elif algo['type'] == 'mix':
            half = count_r // 2
            r_res = sorted(random.sample(hot_list_r[:half+2], half) + random.sample(cold_list_r[:count_r-half+2], count_r-half))
        elif algo['type'] == 'monte' or algo['type'] == 'supreme':
            weights = [freq_dict[n] + 1 for n in pool_r]
            probs = [w / sum(weights) for w in weights]
            r_res = sorted(np.random.choice(pool_r, size=count_r, replace=False, p=probs).tolist())
        elif algo['type'] == 'fit':
            r_res = sorted(hot_list_r[:count_r])
            
        if count_b > 0: b_res = sorted(random.sample(pool_b, count_b))

        # 样式渲染
        is_gold = (algo['type'] == 'supreme')
        ball_class = "bg-gold" if is_gold else "bg-red"
        
        if choice == "双色球": 
            html = "".join([f"<span class='pred-ball {ball_class}'>{n:02d}</span>" for n in r_res]) + f"<span class='pred-ball bg-blue'>{b_res[0]:02d}</span>"
        elif choice == "大乐透": 
            html = "".join([f"<span class='pred-ball {'bg-gold' if is_gold else 'bg-blue'}'>{n:02d}</span>" for n in r_res]) + "".join([f"<span class='pred-ball bg-yellow'>{n:02d}</span>" for n in b_res])
        else:
            html = "".join([f"<span class='pred-ball {ball_class}'>{n}</span>" for n in r_res])
            
        sets.append({"name": algo['name'], "html": html, "text": " ".join([str(n) for n in r_res]), "is_vip": algo['vip'], "is_supreme": is_gold})
    return sets

# --- 核心抓取 & 同步 (保持老板原版修复逻辑) ---
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
            trs = tdata.find_all('tr') if tdata else soup.find_all('tr', class_=['t_tr1', 't_tr2', 't_tr'])
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) < d_cols_len + 1: continue 
                iss_str = re.sub(r'\D', '', tds[0].get_text(strip=True))
                if len(iss_str) < 3: continue
                issue_val = int(iss_str)
                balls = [int(n) for n in re.findall(r'\d+', " ".join([td.get_text() for td in tds[1:]]))][:d_cols_len]
                if len(balls) == d_cols_len: web_rows.append({"issue": issue_val, "balls": balls})
            if web_rows: break 
        except: continue
    return web_rows

def sync_latest_data(df, q_col, d_cols, choice, file_path):
    status = st.empty()
    game_codes = {"双色球": "ssq", "大乐透": "dlt", "福彩3D": "sd", "排列3": "pls", "排列5": "plw", "七星彩": "qxc", "快乐8": "kl8"}
    web_data = fetch_from_web(game_codes.get(choice, "ssq"), choice, len(d_cols))
    if web_data:
        try:
            clean_web_rows = []
            for item in web_data:
                new_row = {q_col: int(item['issue'])}
                for i, col_name in enumerate(d_cols): new_row[col_name] = int(item['balls'][i])
                clean_web_rows.append(new_row)
            web_df = pd.DataFrame(clean_web_rows).astype('int64')
            df[q_col] = pd.to_numeric(df[q_col]).astype('int64')
            updated = pd.concat([web_df, df], ignore_index=True).drop_duplicates(subset=[q_col], keep='first').sort_values(q_col, ascending=False).head(2000)
            save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
            updated.to_csv(save_path, index=False, encoding='utf-8-sig')
            status.success("✅ 同步成功！")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
        except Exception as e: status.error(f"🚨 同步异常")
    else: status.error("❌ 抓取失败")

# --- 侧边栏 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 至尊智算终端")
choice = st.sidebar.selectbox("🎯 实战彩种", list(LOTTERY_FILES.keys()))
st.sidebar.markdown(f'<div class="wechat-box"><span style="color:#666;">获取【VIP至尊口令】</span><br><b style="color:#ff4b4b;">微信：{MY_WECHAT_ID}</b></div>', unsafe_allow_html=True)
st.sidebar.code(MY_WECHAT_ID, language="text")

# --- 主界面 ---
file_kw = LOTTERY_FILES[choice]
all_files = [f for f in os.listdir(".") if file_kw in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))]
target = next((f for f in all_files if '_synced' in f), all_files[0] if all_files else None)

if target:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target, choice)
    if df is not None:
        st.title(f"🎰 {choice} 至尊数据中心")
        st.markdown(f'<div class="timer-bar">⏰ 离今日开奖截止还剩 {get_countdown()} | 12阶服务器已连接</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="marquee-wrapper"><div class="marquee-icon">📢</div><div class="marquee-content">{get_fake_broadcasts()}</div></div>', unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["📜 历史数据", "📈 深度走势", "🤖 AI 演算", "💬 交流大厅"])
        
        with t1:
            # 渲染老板原本的表格逻辑
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(30).iterrows():
                balls_html = "<div style='display:flex; justify-content:center;'>"
                for i, col in enumerate(d_cols):
                    bg = "bg-red"
                    if choice == "双色球": bg = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": bg = "bg-yellow" if i >= 5 else "bg-blue"
                    balls_html += f"<span class='ball {bg}'>{row[col]:02d if needs_zero else row[col]}</span>"
                table_html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{balls_html}</div></td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

        with t2:
            st.line_chart(df.head(50).set_index('期号')[d_cols[0]]) # 简易走势

        with t3:
            st.info("💡 样板间提示：输入 888 体验 VIP，输入 666 开启 12 阶至尊演算。")
            with st.form("ai_form"):
                user_input_pwd = st.text_input("🔑 输入授权口令：", type="password")
                submit_btn = st.form_submit_button("🚀 启动 AI 演算", use_container_width=True)

            if submit_btn:
                is_supreme = (user_input_pwd == CODE_SUPREME)
                is_vip = (user_input_pwd == CODE_VIP or is_supreme)
                
                if is_supreme: st.balloons() # 撒花！

                predictions = get_real_prediction(df.head(50), d_cols, choice, is_supreme)
                for p in predictions:
                    is_locked = p['is_vip'] and not is_vip
                    gold_class = "pred-row-gold" if p.get('is_supreme') else ""
                    
                    st.markdown(f"""
                        <div class="pred-row {gold_class}">
                            <div class="pred-title">{'✨ ' if p.get('is_supreme') else ''}{p['name']} {'✅' if not is_locked else ''}</div>
                            <div class="pred-balls {'vip-locked' if is_locked else ''}">{p['html']}</div>
                            {f"<div class='lock-overlay'>🔒 算法锁定</div>" if is_locked else ""}
                        </div>
                    """, unsafe_allow_html=True)

        with t4:
            st.markdown("### 💬 VIP 交流大厅")
            st.info("🟢 当前在线：1,862 人")
            st.warning("加站长微信获取发言权限")

st.sidebar.markdown(f"""--- \n📊 累计访问：`{new_v}`\n免责声明：本系统仅供技术交流。""")
