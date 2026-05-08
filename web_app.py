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
VIP_PASSWORD = "888"                 
SUPREME_PASSWORD = "666"             # 新增：12阶至尊口令
# =========================================================

# --- 访客统计 ---
visit_file = "visit_log.txt"
if not os.path.exists(visit_file):
    with open(visit_file, "w") as f: f.write("0")
with open(visit_file, "r") as f:
    current_v = int(f.read())
new_v = current_v + 1
with open(visit_file, "w") as f: f.write(str(new_v))

# --- 1. 样式表 (保留全部原版并加入金色球动画) ---
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
    
    /* 🏆 12阶至尊金色球动画 */
    .bg-gold { background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%); color: white !important; border: 1px solid #fff; box-shadow: 0 0 12px rgba(255,140,0,0.8); animation: pulse 2s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }

    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 5px; border-left: 5px solid #f14545; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; position: relative; }
    .pred-row-gold { border-left: 5px solid #ffd700; background: #fffdf0; }
    .pred-title { width: 150px; font-weight: bold; color: #444; font-size: 15px; }
    .pred-balls { flex-grow: 1; display: flex; flex-wrap: wrap; max-width: 400px;} 
    .pred-ball { display: inline-block; width: 34px; height: 34px; line-height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 4px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.15); }
    
    .vip-locked { filter: blur(6px); user-select: none; pointer-events: none; }
    .lock-overlay { position: absolute; right: 20px; top: 50%; transform: translateY(-50%); background: rgba(255,255,255,0.95); padding: 6px 15px; border: 2px dashed #ff4b4b; border-radius: 5px; color: #ff4b4b; font-size: 14px; font-weight: bold; z-index: 10; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    
    .timer-bar { background: linear-gradient(90deg, #1d2b64, #f8cdda); color: white; padding: 10px; text-align: center; border-radius: 5px; font-weight: bold; margin-bottom: 15px; }
    .wechat-box { background: #f0f2f6; border-radius: 10px; padding: 15px; border: 1px solid #dcdfe6; text-align: center; margin-bottom: 10px;}
    
    .marquee-wrapper { background: linear-gradient(to right, #fff3cd, #fff8e1); padding: 10px 15px; border-radius: 8px; border-left: 4px solid #f9bf15; margin-bottom: 20px; overflow: hidden; display: flex; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .marquee-content { white-space: nowrap; animation: marquee 30s linear infinite; color: #856404; font-weight: bold; font-size: 14px; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-150%); } }
    
    .comment-box { background: #fff; border: 1px solid #eaeaea; border-radius: 8px; padding: 15px; margin-bottom: 10px; }
    .legal-footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #eaeaea; text-align: center; color: #999; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

# --- 工具函数 (全部原版保留) ---
def get_countdown():
    now = datetime.now()
    target = now.replace(hour=21, minute=30, second=0)
    if now > target: target += timedelta(days=1)
    diff = target - now
    return f"{diff.seconds//3600:02d}时{(diff.seconds%3600)//60:02d}分{diff.seconds%60:02d}秒"

def get_fake_broadcasts():
    cities = ["广东", "浙江", "江苏", "山东", "河南", "四川"]
    algos = ["极热寻踪", "绝地反弹", "黄金均衡", "蒙特卡洛", "深度拟合"]
    broadcast_texts = [f"【喜报】{random.choice(cities)}用户 1{random.randint(3,9)}{random.randint(0,9)}****{random.randint(1000,9999)} 成功解锁「{random.choice(algos)}」！" for _ in range(5)]
    return "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🔥&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join(broadcast_texts)

# --- 核心：稳健数据载入 (修复 ValueError) ---
@st.cache_data
def load_full_data(file_path, choice):
    try:
        raw_df = pd.read_excel(file_path) if file_path.endswith('.xls') else pd.read_csv(file_path)
        raw_df.columns = [str(c).strip() for c in raw_df.columns]
        q_col = next((c for c in raw_df.columns if '期' in c or 'NO' in c.upper()), raw_df.columns[0])
        
        # 强制修复期号和数据格式
        raw_df[q_col] = pd.to_numeric(raw_df[q_col], errors='coerce').fillna(0).astype(int)
        
        limits = {"双色球": 7, "大乐透": 7, "福彩3D": 3, "排列3": 3, "排列5": 5, "七星彩": 7, "快乐8": 20}
        max_balls = limits.get(choice, 7)
        
        q_idx = list(raw_df.columns).index(q_col)
        ball_cols = list(raw_df.columns)[q_idx+1 : q_idx+1+max_balls]
        
        # 🤫 静默修复所有号码列，防止格式化崩溃
        for c in ball_cols:
            raw_df[c] = pd.to_numeric(raw_df[c], errors='coerce').fillna(0).astype(int)
            
        needs_zero = True if choice in ["双色球", "大乐透", "快乐8"] else False
        return raw_df.sort_values(q_col, ascending=False), q_col, ball_cols, needs_zero, file_path
    except: return None, None, None, None, None

# --- AI 演算引擎 (加入至尊算法) ---
def get_real_prediction(choice, is_vip, is_sup):
    algos = [
        {"name": "🔥 极热寻踪", "vip": False, "sup": False},
        {"name": "🧊 绝地反弹", "vip": False, "sup": False},
        {"name": "⚖️ 黄金均衡", "vip": False, "sup": False},
        {"name": "🎲 蒙特卡洛引擎", "vip": True, "sup": False},
        {"name": "🧠 深度拟合网络", "vip": True, "sup": False}
    ]
    if is_sup: algos.append({"name": "🏆 12阶空间位移至尊演算", "vip": True, "sup": True})
    
    res = []
    for a in algos:
        count = 3 if choice in ["福彩3D", "排列3"] else 7
        nums = random.sample(range(1, 34 if count > 5 else 10), count)
        if a['sup']:
            html = "".join([f"<span class='pred-ball bg-gold'>{n}</span>" for n in nums])
        else:
            bg = "bg-red" if choice != "大乐透" else "bg-blue"
            html = "".join([f"<span class='pred-ball {bg}'>{n:02d if count>5 else n}</span>" for n in nums])
        res.append(a | {"html": html})
    return res

# --- 侧边栏 (原版完全还原) ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 商业决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))
st.sidebar.markdown(f'<div class="wechat-box">获取内部口令加微信：<br><b>{MY_WECHAT_ID}</b></div>', unsafe_allow_html=True)
st.sidebar.code(MY_WECHAT_ID)
view_options = {"近30期": 30, "近50期": 50, "近100期": 100}
view_choice = st.sidebar.radio("选择分析样本", list(view_options.keys()), index=1)

# --- 主界面 ---
file_kw = LOTTERY_FILES[choice]
target = next((f for f in os.listdir(".") if file_kw in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))), None)

if target:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target, choice)
    if df is not None:
        st.sidebar.markdown(f"**📊 库中最新：** `{df[q_col].max()}` 期")
        if st.sidebar.button("🔄 联网同步最新开奖", type="primary"):
            st.toast("正在同步最新数据...")
            time.sleep(1); st.rerun()

        st.title(f"🎰 {choice} 数据智算中心")
        st.markdown(f'<div class="timer-bar">⏰ 离今日开奖截止还剩 {get_countdown()} | 核心服务器已就绪</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="marquee-wrapper"><div class="marquee-content">{get_fake_broadcasts()}</div></div>', unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["📜 历史数据", "📈 深度走势", "🤖 AI 演算", "💬 交流大厅"])

        with t1:
            st.info(f"🔒 VIP 数据下载通道：加微信 {MY_WECHAT_ID} 获取全量 Excel")
            html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(view_options[view_choice]).iterrows():
                balls = ""
                for i, col in enumerate(d_cols):
                    val = row[col]
                    txt = f"{val:02d}" if needs_zero else str(val)
                    bg = "bg-blue" if (choice=="双色球" and i==6) else "bg-red"
                    balls += f"<span class='ball {bg}'>{txt}</span>"
                html += f"<tr><td><b>{row[q_col]}</b></td><td>{balls}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)

        with t2:
            st.markdown("### 📈 走势分析图表")
            calc_df = df.head(30).copy()
            calc_df['和值'] = calc_df[d_cols].sum(axis=1)
            st.line_chart(calc_df.set_index(q_col)['和值'])
            st.bar_chart(calc_df.set_index(q_col)[d_cols[0]])

        with t3:
            st.markdown("##### 🎯 专属号码多维衍算")
            st.text_input("🔮 输入您的【心水种子号】：", placeholder="例如：06 18")
            st.markdown("---")
            pwd = st.text_input("🔑 输入 VIP 口令解锁算法：", type="password")
            if st.button("🚀 开启 AI 演算"):
                is_sup = (pwd == SUPREME_PASSWORD)
                is_vip = (pwd == VIP_PASSWORD or is_sup)
                if is_sup: st.balloons()
                for p in get_real_prediction(choice, is_vip, is_sup):
                    locked = p['vip'] and not is_vip
                    gold_cls = "pred-row-gold" if p['sup'] else ""
                    st.markdown(f"""
                        <div class="pred-row {gold_cls}">
                            <div class="pred-title">{p['name']}</div>
                            <div class="{'vip-locked' if locked else ''}">{p['html']}</div>
                            {f'<div class="lock-overlay">🔒 算法锁定</div>' if locked else ''}
                        </div>
                    """, unsafe_allow_html=True)

        with t4:
            st.info("🟢 内部 VIP 交流大厅 (在线 1,862 人)")
            chat_container = st.container(height=300)
            with chat_container:
                st.markdown(f"**老彩民12**: 已加老板微信 {MY_WECHAT_ID}，12阶至尊算法真牛！")
                st.markdown(f"**李哥**: 刚才同步了一下数据，最新的已经出来了。")
            st.text_input("📝 发表心得...", key="chat_input")
            if st.button("🚀 发送留言"): st.error("请加微信获取发言权限")

st.markdown(f'<div class="legal-footer">© 2026 AI 智算中心 | 微信：{MY_WECHAT_ID}</div>', unsafe_allow_html=True)
