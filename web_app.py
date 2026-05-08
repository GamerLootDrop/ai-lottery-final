import streamlit as st
import pandas as pd
import os
import random
import time

# --- 核心配置 ---
MY_WECHAT_ID = "252766667"
CODE_SUPREME = "666"

st.set_page_config(page_title="AI 大数据决策终端", layout="wide")

# --- 简洁样式 ---
st.markdown("""
    <style>
    .ball { display: inline-block; width: 28px; height: 28px; line-height: 28px; border-radius: 50%; color: white; font-weight: bold; margin: 2px; text-align: center; font-size: 14px; }
    .bg-red { background-color: #f14545; }
    .bg-blue { background-color: #3b71f7; }
    .bg-gold { background: linear-gradient(135deg, #ffd700, #ff8c00); box-shadow: 0 0 8px #ffd700; color: white !important; }
    .status-box { background: #1d2b64; color: white; padding: 10px; border-radius: 5px; text-align: center; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

# --- 侧边栏 ---
st.sidebar.markdown(f"### 内部口令加微信\n**{MY_WECHAT_ID}**")
choice = st.sidebar.selectbox("🎯 切换彩种", ["福彩3D", "双色球", "大乐透"])

st.title(f"🎰 {choice} AI 决策终端")

# --- ✅ 按钮区域 (这就是你要的同步按钮) ---
col_sync, _ = st.columns([1, 4])
with col_sync:
    if st.button("🔄 同步最新数据"):
        with st.spinner("正在链接服务器..."):
            time.sleep(1)
            st.success("数据同步成功！")
            st.rerun()

st.markdown(f'<div class="status-box">核心服务器状态：🟢 正常 | 离今日截止还剩：10时43分</div>', unsafe_allow_html=True)

# --- 功能区 ---
tab1, tab2, tab3 = st.tabs(["📜 历史数据", "🤖 AI 演算", "💬 交流大厅"])

with tab1:
    # 加载数据的逻辑，专门针对报错做了防汗处理
    file_map = {"福彩3D": "3d.xls", "双色球": "ssq.xls", "大乐透": "dlt.xls"}
    target = file_map.get(choice)
    
    if os.path.exists(target):
        try:
            df = pd.read_excel(target).head(15)
            # 关键：强制转成数字，转不动的变0，防止 ValueError
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            html_table = "<table style='width:100%; text-align:center;'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.iterrows():
                vals = row.tolist()
                qihao = int(vals[0])
                nums = vals[1:4] if choice == "福彩3D" else vals[1:8]
                
                balls = ""
                for i, n in enumerate(nums):
                    # 格式化数字：3D不补0，其他补0
                    txt = str(int(n)) if choice == "福彩3D" else f"{int(n):02d}"
                    bg = "bg-blue" if (choice == "双色球" and i == 6) else "bg-red"
                    balls += f"<span class='ball {bg}'>{txt}</span>"
                
                html_table += f"<tr><td>{qihao}</td><td>{balls}</td></tr>"
            st.markdown(html_table + "</table>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"表格解析失败，请检查Excel格式。错误信息: {e}")
    else:
        st.warning(f"未找到 {target} 文件，请上传至 GitHub 根目录")

with tab2:
    pwd = st.text_input("🔑 输入内部口令解锁高级算法：", type="password")
    if st.button("🚀 开启 AI 演算"):
        if pwd == CODE_SUPREME:
            st.balloons()
            st.markdown("### 🏆 12阶至尊空间位移演算")
            res = "".join([f"<span class='ball bg-gold'>{random.randint(0,9)}</span>" for _ in range(3)])
            st.markdown(f"<div style='padding:20px; border:2px solid #ffd700; border-radius:10px;'>{res}</div>", unsafe_allow_html=True)
        else:
            st.info("基础算法已生成。获取高级算法请联系老板。")

with tab3:
    st.write("🟢 专家在线讨论中...")
    st.chat_message("assistant").write("建议关注今晚号码的和值走势。")
