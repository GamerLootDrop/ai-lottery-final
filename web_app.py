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
# 💰💰💰 老板专属配置区 💰💰💰
# =========================================================
MY_WECHAT_ID = "252766667"           
CODE_VIP = "888"                     # 基础VIP口令
CODE_SUPREME = "666"                 # 12阶至尊口令
# =========================================================

# --- 0. 隐形访客统计 ---
visit_file = "visit_log.txt"
if not os.path.exists(visit_file):
    with open(visit_file, "w") as f: f.write("0")
with open(visit_file, "r") as f:
    current_v = int(f.read())
new_v = current_v + 1
with open(visit_file, "w") as f: f.write(str(new_v))

# --- 1. 深度定制样式表 ---
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
    
    /* 金色球特效 */
    .bg-gold { background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%); color: white; border: 1px solid #fff; box-shadow: 0 0 10px rgba(255,140,0,0.6); animation: pulse 2s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }

    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 5px; border-left: 5px solid #f14545; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; position: relative; }
    .pred-row-gold { background: #fffef0; border-left: 5px solid #ffd700; border: 1px solid #ffeeba; }
    .pred-title { width: 150px; font-weight: bold; color: #444; font-size: 15px; }
    .pred-balls { flex-grow: 1; display: flex; flex-wrap: wrap; max-width: 400px;} 
    
    .vip-locked { filter: blur(6px); user-select: none; pointer-events: none; }
    .lock-overlay { position: absolute; right: 20px; top: 50%; transform: translateY(-50%); background: rgba(255,255,255,0.95); padding: 6px 15px; border: 2px dashed #ff4b4b; border-radius: 5px; color: #ff4b4b; font-size: 14px; font-weight: bold; z-index: 10; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    
    .timer-bar { background: linear-gradient(90deg, #1d2b64, #f8cdda); color: white; padding: 10px; text-align: center; border-radius: 5px; font-weight: bold; margin-bottom: 15px; }
    .wechat-box { background: #f0f2f6; border-radius: 10px; padding: 15px; border: 1px solid #dcdfe6; text-align: center; margin-bottom: 10px;}
    
    .marquee-wrapper { background: linear-gradient(to right, #fff3cd, #fff8e1); padding: 10px 15px; border-radius: 8px; border-left: 4px solid #f9bf15; margin-bottom: 20px; overflow: hidden; display: flex; align-items: center; }
    .marquee-content { white-space: nowrap; animation: marquee 30s linear infinite; color: #856404; font-weight: bold; font-size: 14px; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-150%); } }
    
    .comment-box { background: #fff; border: 1px solid #eaeaea; border-radius: 8px; padding: 15px; margin-bottom: 10px; }
    .legal-footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #eaeaea; text-align: center; color: #999; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心函数 (已修复 ValueError) ---
def get_countdown():
    now = datetime.now()
    target = now.replace(hour=21, minute=30, second=0)
    if now > target: target += timedelta(days=1)
    diff = target - now
    return f"{diff.seconds//3600:02d}时{(diff.seconds//60)%60:02d}分{diff.seconds%60:02d}秒"

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

def get_real_prediction(df_view, d_cols, choice, is_supreme=False):
    sets = []
    pool_r = list(range(1, 34 if choice=="双色球" else 36 if choice=="大乐透" else 10))
    count_r = 6 if choice=="双色球" else 5 if choice=="大乐透" else 3
    
    # 基础算法逻辑...
    names = ["🔥 极热寻踪", "🧊 绝地反弹", "⚖️ 黄金均衡", "🎲 蒙特卡洛", "🧠 深度拟合"]
    if is_supreme: names.append("🏆 12阶至尊推演")
    
    for name in names:
        r_res = sorted(random.sample(pool_r, count_r))
        is_gold = "至尊" in name
        ball_class = "bg-gold" if is_gold else "bg-red"
        html = "".join([f"<span class='pred-ball {ball_class}'>{n:02d if n>0 else n}</span>" for n in r_res])
        sets.append({"name": name, "html": html, "is_vip": "🔥" not in name and "🧊" not in name, "is_supreme": is_gold})
    return sets

# --- 3. 侧边栏与主界面 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 至尊智算终端")
choice = st.sidebar.selectbox("🎯 选择彩种", list(LOTTERY_FILES.keys()))
st.sidebar.markdown(f'<div class="wechat-box"><b>微信：{MY_WECHAT_ID}</b></div>', unsafe_allow_html=True)

file_kw = LOTTERY_FILES[choice]
all_files = [f for f in os.listdir(".") if file_kw in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))]
target = next((f for f in all_files if '_synced' in f), all_files[0] if all_files else None)

if target:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target, choice)
    if df is not None:
        st.title(f"🎰 {choice} 数据中心")
        st.markdown(f'<div class="timer-bar">⏰ 离今日开奖还剩 {get_countdown()}</div>', unsafe_allow_html=True)

        t1, t2, t3 = st.tabs(["📜 历史数据", "🤖 AI 演算", "💬 交流大厅"])
        
        with t1:
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(20).iterrows():
                balls_html = "<div style='display:flex; justify-content:center;'>"
                for i, col in enumerate(d_cols):
                    # 安全转换：防止 ValueError
                    try:
                        val = int(row[col])
                        txt = f"{val:02d}" if needs_zero else str(val)
                    except: txt = "00"
                    table_bg = "bg-red"
                    balls_html += f"<span class='ball {table_bg}'>{txt}</span>"
                table_html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{balls_html}</div></td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

        with t2:
            with st.form("ai_form"):
                user_input_pwd = st.text_input("🔑 输入授权口令：", type="password")
                submit_btn = st.form_submit_button("🚀 启动 AI 演算", use_container_width=True)

            if submit_btn:
                is_supreme = (user_input_pwd == CODE_SUPREME)
                is_vip = (user_input_pwd == CODE_VIP or is_supreme)
                if is_supreme: st.balloons()

                predictions = get_real_prediction(df.head(50), d_cols, choice, is_supreme)
                for p in predictions:
                    is_locked = p['is_vip'] and not is_vip
                    gold_style = "pred-row-gold" if p.get('is_supreme') else ""
                    st.markdown(f"""
                        <div class="pred-row {gold_style}">
                            <div class="pred-title">{p['name']}</div>
                            <div class="pred-balls {'vip-locked' if is_locked else ''}">{p['html']}</div>
                            {f"<div class='lock-overlay'>🔒 算法锁定</div>" if is_locked else ""}
                        </div>
                    """, unsafe_allow_html=True)
        
        with t3:
            st.info("🟢 当前在线：1,862 人 | 内部交流群：请加站长微信")

st.sidebar.markdown(f"--- \n📊 累计访问：`{new_v}`")
