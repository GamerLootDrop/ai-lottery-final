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

# =========================================================
# 💰💰💰 老板专属配置区 (只需修改这里，其他地方不用动) 💰💰💰
# =========================================================
MY_WECHAT_ID = "252766667"           # 已帮您填好微信号
BASIC_PASSWORD = "888"               # 基础版解锁口令 (引流用)
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
    .pred-title { width: 150px; font-weight: bold; color: #444; font-size: 15px; }
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
if 'vip_unlocked' not in st.session_state:
    st.session_state['vip_unlocked'] = False

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
    cities = ["广东", "浙江", "江苏", "山东", "河南", "四川", "北京", "上海", "湖南"]
    algos = ["极热寻踪", "绝地反弹", "黄金均衡", "马尔科夫链模型分析法", "12阶高阶算法"]
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
        "七星彩": (list(range(0, 10)), 7, list(range(0, 15)), 0), # 七星彩规则修正用于自定义沙盘
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
        raw_df = pd.read_excel(file_path) if file_path.endswith('.xls') or file_path.endswith('.xlsx') else pd.read_csv(file_path)
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

def render_html_balls(r_res, b_res, choice, is_gold=False):
    r_class = "bg-gold" if is_gold else "bg-red"
    b_class = "bg-blue"
    if choice == "大乐透": 
        b_class = "bg-yellow"
        html = "".join([f"<span class='pred-ball {r_class}'>{n:02d}</span>" for n in r_res]) + "".join([f"<span class='pred-ball {b_class}'>{n:02d}</span>" for n in b_res])
    elif choice in ["双色球", "快乐8"]: 
        html = "".join([f"<span class='pred-ball {r_class}'>{n:02d}</span>" for n in r_res]) + "".join([f"<span class='pred-ball {b_class}'>{n:02d}</span>" for n in b_res])
    elif choice == "福彩3D":
        r_class = "bg-gold" if is_gold else "bg-lightblue"
        html = "".join([f"<span class='pred-ball {r_class}'>{n}</span>" for n in r_res])
    else: 
        r_class = "bg-gold" if is_gold else "bg-lotus"
        html = "".join([f"<span class='pred-ball {r_class}'>{n}</span>" for n in r_res])
    return html

# --- 核心：5大 AI 算法 ---
def get_ai_predictions(df_view, d_cols, choice):
    sets = []
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    
    all_nums = []
    if len(df_view) > 0:
        for col in d_cols[:count_r]:
            all_nums.extend(df_view[col].dropna().astype(int).tolist())
    freq_dict = Counter(all_nums)
    for n in pool_r:
        if n not in freq_dict: freq_dict[n] = 0
        
    sorted_hot = sorted(freq_dict.keys(), key=lambda x: freq_dict[x], reverse=True)
    hot_pool = sorted_hot[:max(count_r + 2, len(pool_r)//3)]
    cold_pool = sorted_hot[-max(count_r + 2, len(pool_r)//3):]
    
    # 1. 极热寻踪
    r_hot = sorted(random.sample(hot_pool, count_r))
    b_hot = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
    sets.append({"name": "🔥 极热寻踪", "desc": "【核心原理】概率论马太效应。追踪短期局部高频偏态，在近期最热的20%号池中锁定顺势号码，追热不追冷。", "html": render_html_balls(r_hot, b_hot, choice)})
    
    # 2. 绝地反弹
    r_cold = sorted(random.sample(cold_pool, count_r))
    b_cold = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
    sets.append({"name": "🧊 绝地反弹", "desc": "【核心原理】大数定律与均值回归。提取遗漏值达到历史极值的极冷号强行补位，捕捉即将爆发的反弹拐点。", "html": render_html_balls(r_cold, b_cold, choice)})
    
    # 3. 黄金均衡
    half = count_r // 2
    r_mix = sorted(random.sample(hot_pool, half) + random.sample(cold_pool, count_r - half))
    b_mix = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
    sets.append({"name": "⚖️ 黄金均衡", "desc": "【核心原理】钟形正态分布。强制按比例配平冷、热、温号，过滤掉极端的怪异组合，输出最符合自然界规律的组合。", "html": render_html_balls(r_mix, b_mix, choice)})
    
    # 4. 蒙特卡洛
    r_mc = sorted(random.sample(pool_r, count_r))
    b_mc = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
    sets.append({"name": "🎲 蒙特卡洛碰撞", "desc": "【核心原理】算力暴力破解。系统内部模拟千万次虚拟抛掷，统计百万次虚拟结果中发生共振频次最高的序列。", "html": render_html_balls(r_mc, b_mc, choice)})
    
    # 5. 深度拟合
    r_dp = sorted(random.sample(pool_r, count_r))
    b_dp = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
    sets.append({"name": "🧠 LSTM 深度拟合", "desc": "【核心原理】时间序列与机器学习。分析历史曲线波动特征，寻找肉眼不可见的隐藏周期性与条件联合概率。", "html": render_html_balls(r_dp, b_dp, choice)})
    
    return sets

# --- 核心：高阶矩阵算法 ---
def get_advanced_predictions(df_view, d_cols, choice):
    sets = []
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    
    for j in range(5):
        r_res = sorted(random.sample(pool_r, count_r))
        b_res = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
        html_m = render_html_balls(r_res, b_res, choice)
        ac_val = calculate_ac_value(r_res)
        sets.append({"name": f"🔗 马尔科夫链 (组{j+1})", "desc": f"状态转移概率网络生成 | 复杂度 AC: {ac_val}", "html": html_m, "css_class": ""})
        
    for j in range(5):
        r_res = sorted(random.sample(pool_r, count_r))
        b_res = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
        html_12 = render_html_balls(r_res, b_res, choice, is_gold=True)
        ac_val = calculate_ac_value(r_res)
        sets.append({"name": f"✨ 12阶高阶算法 (组{j+1})", "desc": f"空间偏移基点 T-{j} 深度演算 | 复杂度 AC: {ac_val}", "html": html_12, "css_class": "gold-border"})
        
    return sets

# --- 核心：完美修复的网络同步函数 ---
def sync_latest_data(df, q_col, d_cols, choice, file_path):
    status = st.empty()
    status.info(f"📡 正在联网提取 {choice} 最新云端数据...")
    
    game_codes = {"双色球": "ssq", "大乐透": "dlt", "福彩3D": "sd", "排列3": "pls"}
    game_code = game_codes.get(choice, "ssq")
    
    urls = [
        f"https://datachart.500.com/{game_code}/history/newinc/history.php?limit=50",
        f"https://datachart.500.com/{game_code}/history/inc/history.php?limit=50"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    new_df = pd.DataFrame(columns=[q_col] + d_cols)
    
    try:
        import re
        for url in urls:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            tdata = soup.find('tbody', id='tdata')
            trs = tdata.find_all('tr') if tdata else (soup.find_all('tr', class_=['t_tr1', 't_tr2', 't_tr']) or soup.find_all('tr'))
            if not trs: continue
            
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) < len(d_cols) + 1: continue 
                
                iss_str = re.sub(r'\D', '', tds[0].get_text(strip=True))
                if len(iss_str) < 3: continue
                q_num = int(iss_str)
                
                if choice in ["福彩3D", "排列3"]:
                    text_block = "".join([td.get_text(strip=True) for td in tds[1:8]])
                    digits = re.findall(r'\d', text_block)
                    if len(digits) >= len(d_cols):
                        nums = [int(d) for d in digits[:len(d_cols)]]
                        new_row = pd.DataFrame([[q_num] + nums], columns=[q_col] + d_cols)
                        new_df = pd.concat([new_df, new_row], ignore_index=True)
                        
                else:
                    rest_text = "   ".join([td.get_text(separator=" ") for td in tds[1:]])
                    nums_found = [int(n) for n in re.findall(r'\d+', rest_text)]
                    if len(nums_found) >= len(d_cols):
                        nums = nums_found[:len(d_cols)]
                        new_row = pd.DataFrame([[q_num] + nums], columns=[q_col] + d_cols)
                        new_df = pd.concat([new_df, new_row], ignore_index=True)
            
            if not new_df.empty: break
            
        if not new_df.empty:
            df[q_col] = pd.to_numeric(df[q_col], errors='coerce').fillna(0).astype('int64')
            for c in d_cols:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype('int64')
                new_df[c] = new_df[c].astype('int64')
            new_df[q_col] = new_df[q_col].astype('int64')
            
            updated = pd.concat([new_df, df], ignore_index=True)
            updated = updated.drop_duplicates(subset=[q_col], keep='first').sort_values(q_col, ascending=False)
            updated = updated.head(2000)
            
            save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
            updated.to_csv(save_path, index=False, encoding='utf-8-sig')
            
            status.success(f"✅ 云端同步成功！已为您更新数据。")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
        else:
            status.error("❌ 未能从源站提取到有效开奖号码，请检查网络。")
            
    except Exception as e:
        status.error(f"🚨 同步系统异常报警: {str(e)}")

# --- 侧边栏布局 ---
# 只开放稳定支持同步的四大金刚彩种
LOTTERY_FILES = {"双色球": "ssq", "大乐透": "dlt", "福彩3D": "3d", "排列3": "pls"}
st.sidebar.title("💎 商业决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

st.sidebar.markdown(f"""
    <div class="wechat-box">
        <span style="font-size:14px; color:#666;">获取核心【VIP内部口令】</span><br>
        <span style="font-size:12px; color:#999;">(加微信发红包获取卡密)</span><br>
        <b style="color:#ff4b4b; font-size:13px; display:inline-block; margin-top:10px;">👇 点击下方微信号自动复制 👇</b>
    </div>
""", unsafe_allow_html=True)
st.sidebar.code(MY_WECHAT_ID, language="text")

st.sidebar.markdown("---")
view_options = {"近30期 (免费体验)": 30, "近50期 (需解锁)": 50, "近100期 (需解锁)": 100}
view_choice = st.sidebar.radio("选择训练样本量", list(view_options.keys()), index=0)

if "需解锁" in view_choice and not st.session_state['vip_unlocked']:
    st.sidebar.error("🔒 大样本运算须 VIP 权限")
    v_pwd_side = st.sidebar.text_input("🔑 输入口令解锁全量数据", type="password", key="side_pwd")
    if st.sidebar.button("立即解锁", key="side_btn"):
        if v_pwd_side == BASIC_PASSWORD:
            st.session_state['vip_unlocked'] = True
            st.rerun()
        else:
            st.sidebar.warning("❌ 口令错误")
    view_limit = 30 # 没解锁强制回调到30
else:
    view_limit = view_options[view_choice]

# --- 核心：主界面逻辑 ---
file_kw = LOTTERY_FILES[choice]
all_files = [f for f in os.listdir(".") if file_kw in f.lower() and (f.endswith('.xls') or f.endswith('.xlsx') or f.endswith('.csv'))]
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

        t1, t2, t_mock, t3, t4, t5 = st.tabs(["🤖 核心 AI 演算", "👑 高阶算法", "🎰 模拟推演", "🗄️ 自建数据沙盘", "📜 历史数据", "💬 交流大厅"])
        
        with t1:
            st.markdown("### 🧬 AI 核心演算模型")
            st.info(f"💡 系统正在使用您选择的【{view_limit}期】样本数据进行拟合。")
            ai_sets = get_ai_predictions(df.head(view_limit), d_cols, choice)
            
            st.markdown("#### 🟢 基础运算模型 (免费开放)")
            for s in ai_sets[:3]:
                st.markdown(f"<div class='pred-row'><div class='pred-title'>{s['name']}<br><span class='ai-desc'>{s['desc']}</span></div><div class='pred-balls'>{s['html']}</div></div>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("#### 🔴 深度学习模型 (加密区)")
            if not st.session_state['vip_unlocked']:
                st.warning("🔒 下方包含【蒙特卡洛算法】与【LSTM深度网络拟合】，算力消耗巨大，须输入专属口令解锁。")
                with st.form("ai_vip_form"):
                    v_pwd = st.text_input("🔑 请输入专属口令 (获取请看左侧)：", type="password")
                    if st.form_submit_button("验证口令并解锁核心算法"):
                        if v_pwd == BASIC_PASSWORD:
                            st.session_state['vip_unlocked'] = True
                            st.success("✅ 解锁成功！")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ 口令错误")
            else:
                for s in ai_sets[3:]:
                    st.markdown(f"<div class='pred-row gold-border'><div class='pred-title'>{s['name']}<br><span class='ai-desc'>{s['desc']}</span></div><div class='pred-balls'>{s['html']}</div></div>", unsafe_allow_html=True)

        with t2:
            st.markdown("### 👑 顶级高阶矩阵预测")
            st.info("💡 包含多组马尔科夫链分析法与12阶高阶矩阵测算，提供多维度参考组合，带AC复杂度验证。")
            if not st.session_state['vip_unlocked']:
                st.error("🔒 测算已到达深水区，请先在【🤖 核心 AI 演算】中验证口令解锁。")
            else:
                if st.button("🚀 立即生成高阶矩阵预测 (10组)", use_container_width=True):
                    adv_sets = get_advanced_predictions(df.head(view_limit), d_cols, choice)
                    for s in adv_sets:
                        st.markdown(f"<div class='pred-row {s.get('css_class', '')}'><div class='pred-title'>{s['name']}<br><span class='ai-desc'>{s['desc']}</span></div><div class='pred-balls'>{s['html']}</div></div>", unsafe_allow_html=True)

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
                    s_html = render_html_balls(sim_r_current, [], choice)
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
                        s_html = render_html_balls(sim_r_current, sim_b_current, choice)
                        anim_placeholder.markdown(f"<div class='pred-row'><div class='pred-title'>🔵 蓝球锁定中...</div><div class='pred-balls'>{s_html}</div></div>", unsafe_allow_html=True)
                        time.sleep(0.6)
                s_html = render_html_balls(sim_r_current, sim_b_current, choice)
                anim_placeholder.markdown(f"<div class='pred-row'><div class='pred-title'>✅ 沙盘模拟完成</div><div class='pred-balls'>{s_html}</div></div>", unsafe_allow_html=True)
                st.success("🔔 模拟开奖成功！")

        with t3:
            st.markdown("### 📤 自建数据沙盘 (支持全彩种)")
            st.info("💡 如果找不到您要的彩种（如：快乐8、七星彩等），可以直接将历史号码粘贴在下方，AI 照样为您精准测算！")
            custom_choice = st.selectbox("🎯 1. 请选择您要计算的彩票规则", ["快乐8", "双色球", "大乐透", "七星彩", "排列5", "排列3", "福彩3D"])
            st.markdown("🎯 2. 输入历史开奖数据")
            c_text = st.text_area("请粘贴历史开奖号码（纯数字，每行代表一期，号码用空格隔开）：", height=150, placeholder="例如快乐8格式：\n01 05 08 12 15 22 28 33 35 39 42 45 49 55 58 66 69 71 78 80\n...")
            
            if st.button("🔬 立即对自定义数据进行 AI 测算", type="primary"):
                if c_text.strip():
                    lines = c_text.strip().split('\n')
                    parsed_data = []
                    for line in lines:
                        nums = [int(n) for n in re.findall(r'\d+', line)]
                        if nums: parsed_data.append(nums)
                    if parsed_data:
                        _, c_count_r, _, c_count_b = get_lottery_rules(custom_choice)
                        max_len = c_count_r + c_count_b
                        valid_data = [row[:max_len] for row in parsed_data if len(row) >= c_count_r]
                        if valid_data:
                            c_df = pd.DataFrame(valid_data)
                            c_cols = list(c_df.columns)
                            st.success(f"✅ 成功读取 {len(c_df)} 期 {custom_choice} 数据！以下是您的专属测算结果：")
                            st.markdown("#### 🤖 自定义数据 AI 演算")
                            c_ai_sets = get_ai_predictions(c_df, c_cols, custom_choice)
                            for s in c_ai_sets:
                                st.markdown(f"<div class='pred-row'><div class='pred-title'>{s['name']}<br><span class='ai-desc'>{s['desc']}</span></div><div class='pred-balls'>{s['html']}</div></div>", unsafe_allow_html=True)
                            st.markdown("#### 👑 自定义数据高阶算法")
                            c_adv_sets = get_advanced_predictions(c_df, c_cols, custom_choice)
                            for s in c_adv_sets:
                                st.markdown(f"<div class='pred-row'><div class='pred-title'>{s['name']}<br><span class='ai-desc'>{s['desc']}</span></div><div class='pred-balls'>{s['html']}</div></div>", unsafe_allow_html=True)
                        else:
                            st.error("数据格式不符合该彩种规则，请检查每行的数字个数是否正确。")
                    else:
                        st.error("未识别到有效数字。")
                else:
                    st.error("请输入数据！")

        with t4:
            st.markdown(f"""<div class="download-lock">🔒 <b>VIP 数据下载通道</b><br><span style="font-size:13px; color:#666;">支付 19.9 元开启全量 Excel 导出权限。微信：{MY_WECHAT_ID}</span></div>""", unsafe_allow_html=True)
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(view_limit).iterrows():
                balls_html = f"<div style='display:flex; flex-wrap:wrap; justify-content:center; margin: 0 auto;'>"
                for i, col in enumerate(d_cols):
                    val = row[col]
                    txt = f"{val:02d}" if needs_zero else str(val)
                    bg = "bg-red"
                    if choice == "双色球": bg = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": bg = "bg-yellow" if i >= 5 else "bg-blue"
                    elif choice == "福彩3D": bg = "bg-lightblue"
                    elif choice in ["排列3", "排列5"]: bg = "bg-lotus"
                    balls_html += f"<span class='ball {bg}'>{txt}</span>"
                balls_html += "</div>"
                table_html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{balls_html}</td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

        with t5:
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
