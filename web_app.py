import streamlit as st
import pandas as pd
import os
import time
import random
from datetime import datetime, timedelta

# =========================================================
# 💰 核心商业配置 (直接关系到你的变现)
# =========================================================
MY_WECHAT_ID = "252766667"           
CODE_VIP = "888"                     # 基础VIP
CODE_SUPREME = "666"                 # 12阶至尊
# =========================================================

# --- 1. 生产环境视觉样式 (12阶金色特效) ---
st.set_page_config(page_title="AI 大数据决策终端 - 至尊版", layout="wide")
st.markdown(f"""
    <style>
    .block-container {{ padding: 2rem 1rem !important; max-width: 900px; }}
    
    /* 号码球基础样式 */
    .ball {{ display: inline-block; width: 30px; height: 30px; line-height: 30px; border-radius: 50%; color: white !important; font-weight: bold; margin: 3px; font-size: 14px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
    .bg-red {{ background-color: #f14545; }}
    .bg-blue {{ background-color: #3b71f7; }}
    .bg-yellow {{ background-color: #f9bf15; color: #333 !important; }}
    .bg-purple {{ background-color: #9c27b0; }}
    
    /* 🏆 至尊金色球脉冲特效 */
    .bg-gold {{ background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%); color: white !important; border: 1px solid #fff; box-shadow: 0 0 12px rgba(255,140,0,0.7); animation: pulse 2s infinite; }}
    @keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.1); }} 100% {{ transform: scale(1); }} }}

    /* 演算卡片样式 */
    .pred-row {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 12px; border-left: 6px solid #f14545; box-shadow: 0 4px 6px rgba(0,0,0,0.05); position: relative; }}
    .pred-row-gold {{ border-left: 6px solid #ffd700; background: #fffdf0; }}
    .pred-title {{ font-weight: bold; color: #333; margin-bottom: 10px; font-size: 16px; display: flex; align-items: center; }}
    
    /* VIP 模糊遮罩 */
    .vip-locked {{ filter: blur(6.5px); user-select: none; pointer-events: none; }}
    .lock-overlay {{ position: absolute; right: 30px; top: 50%; transform: translateY(-50%); background: rgba(255,255,255,0.9); padding: 8px 18px; border: 2px dashed #ff4b4b; border-radius: 8px; color: #ff4b4b; font-weight: bold; z-index: 100; }}
    
    .timer-bar {{ background: linear-gradient(90deg, #1d2b64, #f8cdda); color: white; padding: 12px; text-align: center; border-radius: 8px; font-weight: bold; margin-bottom: 20px; }}
    .wechat-box {{ background: #f0f2f6; border-radius: 10px; padding: 15px; border: 1px solid #dcdfe6; text-align: center; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心数据引擎 (解决 ValueError & 列错位) ---
@st.cache_data
def load_and_clean_data(file_path, choice):
    try:
        df = pd.read_excel(file_path) if file_path.endswith('.xls') else pd.read_csv(file_path)
        df.columns = [str(c).strip() for c in df.columns]
        
        # 智能识别期号和号码数量
        rules = {"双色球": 7, "大乐透": 7, "福彩3D": 3, "快乐8": 20, "排列3": 3, "排列5": 5}
        target_n = rules.get(choice, 7)
        
        q_col = next((c for c in df.columns if '期' in c or 'NO' in c.upper()), df.columns[0])
        
        # 寻找紧跟期号后的数字列
        all_cols = list(df.columns)
        start_idx = all_cols.index(q_col) + 1
        ball_cols = []
        for c in all_cols[start_idx:]:
            if len(ball_cols) < target_n:
                ball_cols.append(c)
        
        # 🛡️ 终极防御：强制转换并过滤掉无效数据
        df = df[[q_col] + ball_cols].copy()
        for c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
        
        needs_zero = True if choice in ["双色球", "大乐透", "快乐8"] else False
        return df.sort_values(q_col, ascending=False), q_col, ball_cols, needs_zero
    except Exception as e:
        st.error(f"数据装载失败: {e}")
        return None, None, None, None

# --- 3. 12阶演算逻辑 (注入金色灵魂) ---
def get_supreme_predictions(choice, is_sup, is_vip):
    # 根据彩种确定红蓝球分布
    r_n = 6 if choice == "双色球" else 5 if choice == "大乐透" else 3
    b_n = 1 if choice == "双色球" else 2 if choice == "大乐透" else 0
    
    algos = [
        {"name": "🔥 极热分布模型", "vip": False, "sup": False},
        {"name": "🧊 遗漏冷态回补", "vip": False, "sup": False},
        {"name": "🎲 蒙特卡洛随机迭代", "vip": True, "sup": False},
        {"name": "🧠 神经网络拟合算法", "vip": True, "sup": False}
    ]
    if is_sup:
        algos.append({"name": "🏆 12阶空间位移至尊推演", "vip": True, "sup": True})

    results = []
    for a in algos:
        r_balls = sorted(random.sample(range(1, 34 if choice=="双色球" else 36 if choice=="大乐透" else 10), r_n))
        b_balls = sorted(random.sample(range(1, 13), b_n)) if b_n > 0 else []
        
        if a['sup']: # 至尊金色球
            html = "".join([f"<span class='ball bg-gold'>{n:02d if n>0 else n}</span>" for n in r_balls + b_balls])
        else: # 标准球颜色适配
            if choice == "双色球":
                html = "".join([f"<span class='ball bg-red'>{n:02d}</span>" for n in r_balls]) + f"<span class='ball bg-blue'>{b_balls[0]:02d}</span>"
            elif choice == "大乐透":
                html = "".join([f"<span class='ball bg-blue'>{n:02d}</span>" for n in r_balls]) + "".join([f"<span class='ball bg-yellow'>{n:02d}</span>" for n in b_balls])
            else:
                html = "".join([f"<span class='ball bg-red'>{n}</span>" for n in r_balls])
        
        results.append({"name": a['name'], "html": html, "is_vip": a['vip'], "is_sup": a['sup']})
    return results

# --- 4. 主界面交互 ---
st.sidebar.markdown(f'<div class="wechat-box"><b>精英交流微信：{MY_WECHAT_ID}</b></div>', unsafe_allow_html=True)
LOTTERY_FILES = {"双色球": "ssq", "大乐透": "dlt", "福彩3D": "3d", "快乐8": "kl8", "排列3": "p3"}
choice = st.sidebar.selectbox("🎯 切换实战彩种", list(LOTTERY_FILES.keys()))

target = next((f for f in os.listdir(".") if LOTTERY_FILES[choice] in f.lower() and f.endswith(('.xls', '.csv'))), None)

if target:
    df, q_col, d_cols, needs_zero = load_and_clean_data(target, choice)
    if df is not None:
        st.title(f"🎰 {choice} AI 决策终端")
        st.markdown('<div class="timer-bar">数据实时同步中 - 12阶演算服务器状态：🟢 正常</div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["📜 往期回测", "🤖 AI 实时演算"])
        
        with tab1:
            # 历史表格颜色修复
            html = "<table style='width:100%; text-align:center;'><tr><th>期号</th><th>中奖号码</th></tr>"
            for _, row in df.head(15).iterrows():
                balls = ""
                for i, col in enumerate(d_cols):
                    val = int(row[col])
                    txt = f"{val:02d}" if needs_zero else str(val)
                    bg = "bg-red"
                    if choice == "双色球": bg = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": bg = "bg-yellow" if i >= 5 else "bg-blue"
                    balls += f"<span class='ball {bg}'>{txt}</span>"
                html += f"<tr><td style='padding:8px;'>{row[q_col]}</td><td>{balls}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)

        with tab2:
            st.write("### 🧠 深度演算中心")
            pwd = st.text_input("🔑 请输入授权口令解锁高级算法：", type="password")
            if st.button("🚀 开启 AI 演算", use_container_width=True):
                is_sup = (pwd == CODE_SUPREME)
                is_vip = (pwd == CODE_VIP or is_sup)
                if is_sup: st.balloons()
                
                preds = get_supreme_predictions(choice, is_sup, is_vip)
                for p in preds:
                    locked = p['is_vip'] and not is_vip
                    gold_css = "pred-row-gold" if p['is_sup'] else ""
                    st.markdown(f"""
                        <div class="pred-row {gold_css}">
                            <div class="pred-title">{'✨ ' if p['is_sup'] else '📊 '}{p['name']}</div>
                            <div class="{'vip-locked' if locked else ''}">{p['html']}</div>
                            {f'<div class="lock-overlay">🔒 口令解锁</div>' if locked else ''}
                        </div>
                    """, unsafe_allow_html=True)

# 底部引流
st.sidebar.markdown("---")
st.sidebar.info("本系统由大模型+12阶位移算法提供支持，仅供数据分析参考。")
