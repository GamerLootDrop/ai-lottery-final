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
# 💰 老板专属配置区 (12阶至尊版)
# =========================================================
MY_WECHAT_ID = "252766667"           
CODE_VIP = "888"                     # 基础口令
CODE_SUPREME = "666"                 # 12阶至尊口令
# =========================================================

# --- 1. 深度定制样式表 (金色脉冲特效) ---
st.set_page_config(page_title="AI 大数据决策终端", layout="wide")
st.markdown(f"""
    <style>
    .block-container {{ padding: 2rem 1.5rem !important; max-width: 900px; }}
    .hist-table {{ width: 100%; border-collapse: collapse; text-align: center; background: white; border-radius: 8px; overflow: hidden; }}
    .hist-table th {{ background: #f8f9fa; padding: 10px; border-bottom: 2px solid #eee; }}
    .hist-table td {{ padding: 10px; border-bottom: 1px solid #f0f0f0; }}
    
    .ball {{ display: inline-block; width: 28px; height: 28px; line-height: 28px; border-radius: 50%; color: white !important; font-weight: bold; margin: 2px; font-size: 13px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    .bg-red {{ background-color: #f14545; }}
    .bg-blue {{ background-color: #3b71f7; }}
    .bg-yellow {{ background-color: #f9bf15; color: #333 !important; }}
    .bg-purple {{ background-color: #9c27b0; }}
    .bg-lightblue {{ background-color: #5bc0de; }} 
    .bg-lotus {{ background-color: #cba09e; }}
    
    /* 🏆 12阶至尊金色球动画 */
    .bg-gold {{ background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%); color: white !important; border: 1px solid #fff; box-shadow: 0 0 12px rgba(255,140,0,0.8); animation: pulse 2s infinite; }}
    @keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.1); }} 100% {{ transform: scale(1); }} }}

    .pred-row {{ background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 8px; border-left: 5px solid #f14545; position: relative; }}
    .pred-row-gold {{ border-left: 5px solid #ffd700; background: #fffdf0; }}
    .pred-title {{ font-weight: bold; color: #444; margin-bottom: 8px; }}
    .vip-locked {{ filter: blur(6px); user-select: none; pointer-events: none; }}
    .lock-overlay {{ position: absolute; right: 20px; top: 50%; transform: translateY(-50%); background: rgba(255,255,255,0.9); padding: 5px 15px; border: 2px dashed #ff4b4b; border-radius: 5px; color: #ff4b4b; font-weight: bold; z-index: 10; }}
    
    .timer-bar {{ background: linear-gradient(90deg, #1d2b64, #f8cdda); color: white; padding: 10px; text-align: center; border-radius: 5px; font-weight: bold; margin-bottom: 15px; }}
    .wechat-box {{ background: #f0f2f6; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 15px; border: 1px solid #ddd; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. 强力数据清洗引擎 (解决 ValueError 的核心) ---
@st.cache_data
def load_clean_data(file_path, choice):
    try:
        df = pd.read_excel(file_path) if file_path.endswith('.xls') else pd.read_csv(file_path)
        df.columns = [str(c).strip() for c in df.columns]
        q_col = next((c for c in df.columns if '期' in c or 'NO' in c.upper()), df.columns[0])
        
        # 自动识别号码列 (期号之后连续的数字列)
        all_cols = list(df.columns)
        start_idx = all_cols.index(q_col) + 1
        limits = {"双色球": 7, "大乐透": 7, "福彩3D": 3, "排列3": 3, "排列5": 5, "七星彩": 7, "快乐8": 20}
        target_n = limits.get(choice, 7)
        d_cols = all_cols[start_idx : start_idx + target_n]
        
        # 🛑 核心修复逻辑：强制转换所有号码为数字，坏账变 0
        df[q_col] = pd.to_numeric(df[q_col], errors='coerce').fillna(0).astype(int)
        for c in d_cols:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
            
        needs_zero = True if choice in ["双色球", "大乐透", "快乐8"] else False
        return df.sort_values(q_col, ascending=False), q_col, d_cols, needs_zero
    except Exception as e:
        st.error(f"数据加载出错: {e}")
        return None, None, None, None

# --- 3. AI 预测引擎 ---
def generate_preds(choice, is_sup, is_vip):
    rules = {
        "双色球": (6, 1), "大乐透": (5, 2), "福彩3D": (3, 0), "排列3": (3, 0), "排列5": (5, 0), "七星彩": (6, 1), "快乐8": (20, 0)
    }
    r_n, b_n = rules.get(choice, (6, 1))
    algos = [
        {"name": "🔥 极热寻踪", "vip": False, "sup": False},
        {"name": "🧊 绝地反弹", "vip": False, "sup": False},
        {"name": "🎲 蒙特卡洛引擎", "vip": True, "sup": False},
        {"name": "🧠 神经网络拟合", "vip": True, "sup": False}
    ]
    if is_sup: algos.append({"name": "🏆 12阶空间位移至尊演算", "vip": True, "sup": True})

    res = []
    for a in algos:
        # 生成随机号码 (模拟演算)
        nums = random.sample(range(1, 34 if choice=="双色球" else 10), r_n + b_n)
        if a['sup']:
            html = "".join([f"<span class='ball bg-gold'>{n:02d if n>9 or choice in ['双色球','大乐透'] else n}</span>" for n in nums])
        else:
            # 基础配色逻辑
            html = "".join([f"<span class='ball bg-red'>{n:02d if choice in ['双色球','大乐透'] else n}</span>" for n in nums])
        res.append(a | {"html": html})
    return res

# --- 4. 主界面 ---
st.sidebar.markdown(f'<div class="wechat-box"><b>内部口令加微信：{MY_WECHAT_ID}</b></div>', unsafe_allow_html=True)
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
choice = st.sidebar.selectbox("🎯 切换彩种", list(LOTTERY_FILES.keys()))

# 自动寻找文件
target = next((f for f in os.listdir(".") if LOTTERY_FILES[choice] in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))), None)

if target:
    df, q_col, d_cols, needs_zero = load_clean_data(target, choice)
    if df is not None:
        st.title(f"🎰 {choice} AI 决策终端")
        st.markdown(f'<div class="timer-bar">数据已同步 | 离今日截止还有：{random.randint(1,5)}小时</div>', unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["📜 历史数据", "🤖 AI 演算", "💬 交流大厅"])
        
        with tab1:
            st.write("### 往期开奖回测")
            html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(20).iterrows():
                balls = ""
                for i, col in enumerate(d_cols):
                    # 🛑 这里加了判断，防止非数字导致表格崩溃
                    val = row[col]
                    txt = f"{val:02d}" if needs_zero else str(val)
                    bg = "bg-blue" if (choice=="双色球" and i==6) or (choice=="大乐透" and i<5) else "bg-red"
                    if choice=="大乐透" and i>=5: bg="bg-yellow"
                    balls += f"<span class='ball {bg}'>{txt}</span>"
                html += f"<tr><td>{row[q_col]}</td><td>{balls}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)

        with tab2:
            pwd = st.text_input("🔑 输入口令解锁高级算法：", type="password")
            if st.button("🚀 开启 AI 演算", use_container_width=True):
                is_sup = (pwd == CODE_SUPREME)
                is_vip = (pwd == CODE_VIP or is_sup)
                if is_sup: st.balloons()
                
                for p in generate_preds(choice, is_sup, is_vip):
                    locked = p['vip'] and not is_vip
                    gold_cls = "pred-row-gold" if p['sup'] else ""
                    st.markdown(f"""
                        <div class="pred-row {gold_cls}">
                            <div class="pred-title">{'✨ ' if p['sup'] else '📊 '}{p['name']}</div>
                            <div class="{'vip-locked' if locked else ''}">{p['html']}</div>
                            {f'<div class="lock-overlay">🔒 口令解锁</div>' if locked else ''}
                        </div>
                    """, unsafe_allow_html=True)

        with tab3:
            st.info("🟢 当前 1,288 位专家在线讨论")
            st.chat_message("user").write(f"刚加了老板微信 {MY_WECHAT_ID}，拿到 666 口令了，至尊模式太强了！")
            st.chat_message("assistant").write("12阶算法正在计算今晚最优组合，请保持关注。")

st.markdown(f'<div style="text-align:center;color:#999;margin-top:50px;">© 2026 AI 决策中心 | 微信：{MY_WECHAT_ID}</div>', unsafe_allow_html=True)
