import streamlit as st
import pandas as pd
import os
import time
import random
from datetime import datetime, timedelta

# =========================================================
# 配置区
# =========================================================
MY_WECHAT_ID = "252766667"           
CODE_VIP = "888"                     
CODE_SUPREME = "666"                 

# --- 访客统计 ---
visit_file = "visit_log.txt"
if not os.path.exists(visit_file):
    with open(visit_file, "w") as f: f.write("0")
with open(visit_file, "r") as f:
    current_v = int(f.read())
new_v = current_v + 1
with open(visit_file, "w") as f: f.write(str(new_v))

# --- 样式表 (修复颜色逻辑) ---
st.set_page_config(page_title="AI 至尊决策终端", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 2.5rem 1.5rem !important; max-width: 900px; }
    .hist-table { width: 100%; border-collapse: collapse; text-align: center; background: #fff; border-radius: 8px; overflow: hidden; margin-bottom: 1rem; }
    .hist-table th { background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #eaeaea; color: #666; font-weight: bold; }
    .hist-table td { padding: 12px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 15px; }
    
    .ball { display: inline-block; width: 28px; height: 28px; line-height: 28px; border-radius: 50%; color: white !important; font-weight: bold; margin: 3px 3px; font-size: 13px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .bg-red { background-color: #f14545; }
    .bg-blue { background-color: #3b71f7; }
    .bg-yellow { background-color: #f9bf15; color: #333 !important; }
    .bg-purple { background-color: #9c27b0; }
    .bg-lightblue { background-color: #5bc0de; } 
    
    .bg-gold { background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%); color: #fff !important; border: 1px solid #fff; box-shadow: 0 0 10px rgba(255,140,0,0.6); animation: pulse 2s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.08); } 100% { transform: scale(1); } }

    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 5px; border-left: 5px solid #f14545; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; position: relative; }
    .pred-row-gold { background: #fffef0; border-left: 5px solid #ffd700; border: 1px solid #ffeeba; }
    .pred-title { width: 160px; font-weight: bold; color: #444; font-size: 15px; }
    .pred-ball { display: inline-block; width: 34px; height: 34px; line-height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 4px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.15); }
    .vip-locked { filter: blur(6px); }
    .lock-overlay { position: absolute; right: 20px; top: 50%; transform: translateY(-50%); background: rgba(255,255,255,0.95); padding: 6px 15px; border: 2px dashed #ff4b4b; border-radius: 5px; color: #ff4b4b; font-size: 14px; font-weight: bold; }
    .timer-bar { background: linear-gradient(90deg, #1d2b64, #f8cdda); color: white; padding: 10px; text-align: center; border-radius: 5px; font-weight: bold; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- 数据加载 ---
@st.cache_data
def load_data(file_path, choice):
    try:
        df = pd.read_excel(file_path) if file_path.endswith('.xls') else pd.read_csv(file_path)
        df.columns = [str(c).strip() for c in df.columns]
        q_col = next((c for c in df.columns if '期' in c or 'NO' in c.upper()), df.columns[0])
        ball_cols = [c for i, c in enumerate(df.columns) if i > list(df.columns).index(q_col)][:20]
        
        # 强制数值化，防止 ValueError
        for c in [q_col] + ball_cols:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
            
        needs_zero = True if choice in ["双色球", "大乐透", "快乐8"] else False
        return df.sort_values(q_col, ascending=False), q_col, ball_cols, needs_zero
    except: return None, None, None, None

# --- 预测引擎 ---
def get_preds(choice, is_supreme):
    sets = [{"name": "🔥 极热寻踪", "vip": False}, {"name": "🎲 蒙特卡洛引擎", "vip": True}]
    if is_supreme: sets.append({"name": "🏆 12阶至尊演算", "vip": True, "gold": True})
    
    res = []
    for s in sets:
        nums = sorted(random.sample(range(1, 34), 6))
        b = [random.randint(1, 16)]
        
        if s.get("gold"):
            html = "".join([f"<span class='pred-ball bg-gold'>{n:02d}</span>" for n in nums+b])
        else:
            html = "".join([f"<span class='pred-ball bg-red'>{n:02d}</span>" for n in nums]) + f"<span class='pred-ball bg-blue'>{b[0]:02d}</span>"
        
        res.append({"name": s['name'], "html": html, "vip": s['vip'], "supreme": s.get("gold", False)})
    return res

# --- 主程序 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8"}
choice = st.sidebar.selectbox("🎯 实战彩种", list(LOTTERY_FILES.keys()))
file_kw = LOTTERY_FILES[choice]
target = next((f for f in os.listdir(".") if file_kw in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))), None)

if target:
    df, q_col, d_cols, needs_zero = load_data(target, choice)
    if df is not None:
        st.title(f"🎰 {choice} 至尊数据中心")
        t1, t2 = st.tabs(["📜 历史数据", "🤖 AI 演算"])
        
        with t1:
            html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(20).iterrows():
                balls = ""
                for i, col in enumerate(d_cols):
                    val = int(row[col])
                    txt = f"{val:02d}" if needs_zero else str(val)
                    bg = "bg-red"
                    if choice == "双色球": bg = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": bg = "bg-yellow" if i >= 5 else "bg-blue"
                    balls += f"<span class='ball {bg}'>{txt}</span>"
                html += f"<tr><td>{row[q_col]}</td><td>{balls}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)

        with t2:
            pwd = st.text_input("🔑 输入授权口令：", type="password")
            if st.button("🚀 启动演算"):
                is_sup = (pwd == CODE_SUPREME)
                is_vip = (pwd == CODE_VIP or is_sup)
                if is_sup: st.balloons()
                for p in get_preds(choice, is_sup):
                    locked = p['vip'] and not is_vip
                    css = "pred-row-gold" if p['supreme'] else ""
                    st.markdown(f'<div class="pred-row {css}"><div class="pred-title">{p["name"]}</div><div class="{"vip-locked" if locked else ""}">{p["html"]}</div>{"<div class=\"lock-overlay\">🔒 权限不足</div>" if locked else ""}</div>', unsafe_allow_html=True)

st.sidebar.markdown(f"--- \n微信：{MY_WECHAT_ID}\n累计访问：`{new_v}`")
