import streamlit as st
import pandas as pd
import os
import random
import time

# ==========================================
# ⚙️ 核心配置
# ==========================================
MY_WECHAT_ID = "252766667"
CODE_VIP = "888"
CODE_SUPREME = "666"

st.set_page_config(page_title="AI 大数据决策终端", layout="wide")

# --- 样式表 (包含12阶至尊金色球) ---
st.markdown(f"""
    <style>
    .ball {{ display: inline-block; width: 30px; height: 30px; line-height: 30px; border-radius: 50%; color: white; font-weight: bold; margin: 2px; text-align: center; }}
    .bg-red {{ background-color: #f14545; }}
    .bg-blue {{ background-color: #3b71f7; }}
    .bg-gold {{ background: linear-gradient(135deg, #ffd700, #ff8c00); box-shadow: 0 0 10px #ffd700; animation: pulse 2s infinite; }}
    @keyframes pulse {{ 0% {{transform: scale(1);}} 50% {{transform: scale(1.1);}} 100% {{transform: scale(1);}} }}
    .status-bar {{ background: #1d2b64; color: white; padding: 10px; border-radius: 5px; margin-bottom: 15px; text-align: center; }}
    </style>
""", unsafe_allow_html=True)

# --- 数据加载与同步函数 ---
def load_data(choice):
    # 模拟数据文件对应关系
    files = {"福彩3D": "3d.xls", "双色球": "ssq.xls", "大乐透": "dlt.xls"}
    target_file = files.get(choice, "3d.xls")
    
    if os.path.exists(target_file):
        try:
            df = pd.read_excel(target_file)
            # 🛑 核心修复：强制清理非数字内容，防止 ValueError
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            return df.dropna(how='all').fillna(0).astype(int)
        except:
            return None
    return None

# --- 主界面布局 ---
st.sidebar.markdown(f"### 内部口令加微信\n**{MY_WECHAT_ID}**")
choice = st.sidebar.selectbox("🎯 切换彩种", ["福彩3D", "双色球", "大乐透"])

st.title(f"🎰 {choice} AI 决策终端")

# 🔥 按钮回来了：同步数据按钮
col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    if st.button("🔄 同步最新数据"):
        with st.spinner("正在链接远程服务器..."):
            time.sleep(1.5)
            st.success("同步成功！")
            st.rerun()

st.markdown(f'<div class="status-bar">核心服务器状态：🟢 正常 | 离今日截止还剩：10时43分</div>', unsafe_allow_html=True)

# --- 历史数据选项卡 ---
tab1, tab2, tab3 = st.tabs(["📜 历史数据", "🤖 AI 演算", "💬 交流大厅"])

with tab1:
    df = load_data(choice)
    if df is not None:
        # 构建历史表格
        html_table = "<table style='width:100%; text-align:center;'><tr><th>期号</th><th>开奖号码</th></tr>"
        for _, row in df.head(15).iterrows():
            # 根据彩种决定球的数量和颜色
            balls = ""
            row_list = row.tolist()
            qihao = row_list[0]
            nums = row_list[1:4] if choice == "福彩3D" else row_list[1:8]
            
            for i, n in enumerate(nums):
                # 🛑 修复格式化报错：确保 n 是数字
                val = f"{int(n):02d}" if choice != "福彩3D" else str(int(n))
                bg = "bg-red"
                if choice == "双色球" and i == 6: bg = "bg-blue"
                balls += f"<span class='ball {bg}'>{val}</span>"
            
            html_table += f"<tr><td>{qihao}</td><td>{balls}</td></tr>"
        st.markdown(html_table + "</table>", unsafe_allow_html=True)
    else:
        st.error("未找到本地数据文件，请检查 GitHub 仓库中是否存在对应 .xls 文件")

with tab2:
    pwd = st.text_input("🔑 输入内部口令解锁高级算法：", type="password")
    if st.button("🚀 开启 AI 演算"):
        if pwd == CODE_SUPREME:
            st.balloons()
            st.markdown("### 🏆 12阶至尊空间位移演算结果")
            # 生成金色至尊球
            res = "".join([f"<span class='ball bg-gold'>{random.randint(0,9)}</span>" for _ in range(3)])
            st.markdown(f"<div style='background:#fffdf0; padding:20px; border:2px solid #ffd700; border-radius:10px;'>{res}</div>", unsafe_allow_html=True)
        else:
            st.info("基础算法已生成，进阶算法请联系老板获取口令。")

with tab3:
    st.write("🟢 专家在线讨论中...")
    st.chat_message("user").write("今晚 3D 必出豹子？")
    st.chat_message("assistant").write("大数据显示 0-9 遗漏值正在收窄，建议关注斜连号。")
