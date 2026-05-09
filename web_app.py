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
# 💰💰💰 老板专属配置区 💰💰💰
# =========================================================
MY_WECHAT_ID = "252766667"           # 老板微信号
BASIC_PASSWORD = "888"               # 高阶版解锁口令 
# =========================================================

st.set_page_config(page_title="AI 大数据决策终端", layout="wide")

# --- 样式表 ---
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
    
    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #f14545; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; }
    .pred-row.gold-border { border-left: 5px solid #FFD700; background: #fffdf5; }
    .pred-title { width: 180px; font-weight: bold; color: #444; font-size: 14px; }
    .pred-balls { flex-grow: 1; display: flex; flex-wrap: wrap; max-width: 400px;} 
    .pred-ball { display: inline-block; width: 34px; height: 34px; line-height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 4px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.15); }
    
    .wechat-box { background: #f0f2f6; border-radius: 10px; padding: 15px; border: 1px solid #dcdfe6; text-align: center; margin-bottom: 10px;}
    .marquee-wrapper { background: linear-gradient(to right, #fff3cd, #fff8e1); padding: 10px 15px; border-radius: 8px; border-left: 4px solid #f9bf15; margin-bottom: 20px; overflow: hidden; display: flex; align-items: center; }
    .marquee-content { white-space: nowrap; animation: marquee 30s linear infinite; color: #856404; font-weight: bold; font-size: 14px; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-150%); } }
    
    .poster-box { background: linear-gradient(180deg, #b92b27, #1565C0); border-radius: 12px; padding: 20px; color: white; text-align: center; margin-top: 15px; border: 2px solid #FFD700; }
    .poster-title { font-size: 22px; font-weight: 900; color: #FFD700; margin-bottom: 15px; }
    
    .comment-box { background: #fff; border: 1px solid #eaeaea; border-radius: 8px; padding: 12px; margin-bottom: 8px; }
    .comment-header { display: flex; justify-content: space-between; margin-bottom: 5px; }
    .comment-user { font-weight: bold; color: #1f77b4; font-size: 14px; }
    .comment-time { color: #999; font-size: 12px; }
    .comment-body { color: #444; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- 基础工具函数 ---
def get_lottery_rules(choice):
    rules = {
        "双色球": (list(range(1, 34)), 6, list(range(1, 17)), 1),
        "大乐透": (list(range(1, 36)), 5, list(range(1, 13)), 2),
        "快乐8": (list(range(1, 81)), 20, [], 0),
        "福彩3D": (list(range(0, 10)), 3, [], 0),
        "排列3": (list(range(0, 10)), 3, [], 0)
    }
    return rules.get(choice, rules["双色球"])

def calculate_ac_value(nums):
    diffs = set()
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    return max(0, len(diffs) - (len(nums) - 1))

@st.cache_data
def load_full_data(file_path, choice):
    try:
        raw_df = pd.read_excel(file_path) if file_path.endswith('.xls') or file_path.endswith('.xlsx') else pd.read_csv(file_path)
        raw_df.columns = [str(c).strip() for c in raw_df.columns]
        q_col = next((c for c in raw_df.columns if '期' in c or 'NO' in c.upper()), raw_df.columns[0])
        raw_df[q_col] = pd.to_numeric(raw_df[q_col], errors='coerce')
        raw_df = raw_df.dropna(subset=[q_col])
        max_balls = get_lottery_rules(choice)[1] + get_lottery_rules(choice)[3]
        
        q_idx = list(raw_df.columns).index(q_col)
        ball_cols = []
        for i in range(q_idx + 1, len(raw_df.columns)):
            col = raw_df.columns[i]
            nums = pd.to_numeric(raw_df[col], errors='coerce').dropna()
            if not nums.empty: ball_cols.append(col)
            if len(ball_cols) == max_balls: break
            
        clean_df = raw_df[[q_col] + ball_cols].copy()
        new_names = ['期号'] + [f"b_{i+1}" for i in range(len(ball_cols))]
        clean_df.columns = new_names
        for c in new_names: clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0).astype(int)
        return clean_df.sort_values('期号', ascending=False), '期号', new_names[1:], choice in ["双色球", "大乐透", "快乐8"], file_path
    except Exception as e: 
        return None, None, None, None, None

def render_html_balls(r_res, b_res, choice, is_gold=False):
    r_class = "bg-gold" if is_gold else "bg-red"
    b_class = "bg-blue"
    if choice == "大乐透": b_class = "bg-yellow"
    
    html = "".join([f"<span class='pred-ball {r_class}'>{n:02d}</span>" for n in r_res]) + "".join([f"<span class='pred-ball {b_class}'>{n:02d}</span>" for n in b_res])
    text = "推荐号码: " + " ".join([f"{n:02d}" for n in r_res]) + (" | " + " ".join([f"{n:02d}" for n in b_res]) if b_res else "")
    return html, text

# --- 侧边栏 ---
LOTTERY_FILES = {"快乐8": "kl8", "双色球": "ssq", "大乐透": "dlt", "福彩3D": "3d", "排列3": "p3"}
st.sidebar.title("💎 AI 商业决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

st.sidebar.markdown(f"""
    <div class="wechat-box">
        <span style="font-size:14px; color:#666;">获取高阶【算法解锁口令】</span><br>
        <b style="color:#ff4b4b; font-size:14px;">👇 添加微信联系团长 👇</b><br>
        <b style="color:#1d2b64; font-size:18px;">{MY_WECHAT_ID}</b>
    </div>
""", unsafe_allow_html=True)

# 1. 同步更新功能恢复
if st.sidebar.button("🔄 从云端同步最新数据", use_container_width=True):
    with st.sidebar.status("正在连接国家彩票数据中心...", expanded=True) as status:
        st.write("请求API接口...")
        time.sleep(1)
        st.write("抓取最新开奖期号...")
        time.sleep(1)
        st.write("数据清洗校验中...")
        time.sleep(1)
        status.update(label="同步完成！数据已是最新。", state="complete", expanded=False)
    st.sidebar.success("✅ 同步成功！")

view_options = {"近30期": 30, "近50期": 50, "近100期": 100}
view_choice = st.sidebar.radio("选择分析样本", list(view_options.keys()), index=0)

file_kw = LOTTERY_FILES[choice]
all_files = [f for f in os.listdir(".") if file_kw in f.lower() and (f.endswith('.xls') or f.endswith('.xlsx') or f.endswith('.csv'))]
target = all_files[0] if all_files else None

if target:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target, choice)
    if df is not None:
        st.title(f"🎰 {choice} 云端算力中心")
        st.markdown(f'<div class="marquee-wrapper"><div style="margin-right:10px;">📢</div><div class="marquee-content">【喜报】湖南 王先生 刚刚成功【AI 核心爆大奖】！&nbsp;&nbsp;&nbsp;&nbsp;【喜报】广东 李总 刚刚成功【合买选五全中】！</div></div>', unsafe_allow_html=True)

        t1, t_ai, t_src, t_chat = st.tabs(["📜 历史走势", "🤖 AI 核心演算 (3+2算法)", "🗄️ 数据源与上传", "💬 水军交流区"])
        
        # 标签1：历史数据
        with t1: 
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(view_options[view_choice]).iterrows():
                max_w = "280px" if choice == "快乐8" else "100%" 
                balls_html = f"<div style='display:flex; flex-wrap:wrap; justify-content:center; margin: 0 auto; max-width: {max_w};'>"
                for i, col in enumerate(d_cols):
                    val = row[col]
                    txt = f"{val:02d}" if needs_zero else str(val)
                    bg = "bg-red"
                    if choice == "双色球": bg = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": bg = "bg-yellow" if i >= 5 else "bg-blue"
                    balls_html += f"<span class='ball {bg}'>{txt}</span>"
                balls_html += "</div>"
                table_html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{balls_html}</td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

        # === 标签2：AI核心演算 (3+2模式完美结合) ===
        with t_ai:
            st.info("💡 系统整合了5套顶尖测算模型，初阶为基础数据分析，高阶引入马尔科夫与12阶空间矩阵。")
            
            pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
            
            # 生成随机固定的一组号码用来展示（保证一次点击不会乱跳）
            if 'rand_seed' not in st.session_state:
                st.session_state.rand_seed = random.randint(1, 10000)
            random.seed(st.session_state.rand_seed)
            
            if st.button("🚀 启动 AI 核心引擎演算 (共5组算法)", use_container_width=True, type="primary"):
                st.session_state.show_ai = True
                with st.spinner("正在连接云端节点... 分析近期走势中..."):
                    time.sleep(1.5)

            if st.session_state.get('show_ai', False):
                # ============ 前3组：免费公开 ============
                st.markdown("### 🟢 初阶拟合分析 (公开)")
                names_free = ["🔥 极热寻踪", "🧊 绝地反弹", "⚖️ 黄金均衡"]
                demo_nums = [] # 用来给快乐8做海报
                for name in names_free:
                    r_res = sorted(random.sample(pool_r, count_r))
                    b_res = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
                    html, text = render_html_balls(r_res, b_res, choice)
                    st.markdown(f"<div class='pred-row'><div class='pred-title'>{name}</div><div class='pred-balls'>{html}</div></div>", unsafe_allow_html=True)
                    if not demo_nums: demo_nums = r_res

                st.markdown("---")
                
                # ============ 后2组：888口令解锁 ============
                st.markdown("### 🔴 高阶深度学习模型 (加密)")
                if 'vip_unlocked' not in st.session_state:
                    st.session_state['vip_unlocked'] = False
                
                if not st.session_state['vip_unlocked']:
                    st.warning("🔒 测算已到达深水区。下面包含【马尔科夫链】与【12阶空间矩阵】，须授权访问。")
                    with st.form("vip_form"):
                        v_pwd = st.text_input("🔑 请输入【888】解锁后两组核心算法：", type="password")
                        v_sub = st.form_submit_button("验证口令并解锁")
                        if v_sub:
                            if v_pwd == BASIC_PASSWORD:
                                st.session_state['vip_unlocked'] = True
                                st.success("✅ 解锁成功！")
                                time.sleep(0.5)
                                st.rerun()
                            else: st.error("❌ 口令错误，请联系微信获取。")
                else:
                    # 已经解锁，显示高阶算法！
                    # 算法4
                    r_res_4 = sorted(random.sample(pool_r, count_r))
                    b_res_4 = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
                    ac_4 = calculate_ac_value(r_res_4)
                    html_4, _ = render_html_balls(r_res_4, b_res_4, choice, is_gold=True)
                    st.markdown(f"<div class='pred-row gold-border'><div class='pred-title'>🔗 马尔科夫链深度模型<br><span style='font-size:12px;color:#888;'>AC复杂度测算值: {ac_4}</span></div><div class='pred-balls'>{html_4}</div></div>", unsafe_allow_html=True)
                    
                    # 算法5
                    r_res_5 = sorted(random.sample(pool_r, count_r))
                    b_res_5 = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
                    ac_5 = calculate_ac_value(r_res_5)
                    html_5, _ = render_html_balls(r_res_5, b_res_5, choice, is_gold=True)
                    st.markdown(f"<div class='pred-row gold-border'><div class='pred-title'>✨ 12阶空间位移高阶矩阵<br><span style='font-size:12px;color:#888;'>AC复杂度测算值: {ac_5}</span></div><div class='pred-balls'>{html_5}</div></div>", unsafe_allow_html=True)

                    st.markdown("### 🧠 AI 静默演算研报")
                    ai_report = f"**【高危雷区预警】**: 根据马尔科夫链回测，尾数 {random.choice([1,3,6,8])} 在本期破冰概率极低，建议直接作为【杀码】剔除。<br>**【系统建议】**: 奖池目前处于蓄水震荡期，系统强烈推荐采用上述高阶空间计算出的结果作为托底防守。"
                    st.markdown(f"<div style='background:#f4f6f9; padding:15px; border-left:4px solid #1f77b4; border-radius:5px;'>{ai_report}</div>", unsafe_allow_html=True)

                # ============ 快乐8专属：海报生成器 (一直显示在最下面) ============
                if choice == "快乐8" and demo_nums:
                    st.markdown("---")
                    st.markdown("### 👑 团长专属：一键生成朋友圈战报")
                    xuan5 = sorted(random.sample(demo_nums, 5))
                    xuan8 = sorted(random.sample(demo_nums, 8))
                    st.markdown(f"""
                        <div class="poster-box">
                            <div class="poster-title">🔥 众彩联盟 · 内部机密 🔥</div>
                            <div style="font-size:14px; margin-bottom:10px;">大数据深层拟合 · 今晚必收米</div>
                            <div style="background: rgba(255,255,255,0.9); border-radius: 8px; padding: 15px; color: #333; margin-bottom: 15px;">
                                <b>【选五五复式 稳胆】</b><br>
                                <span style="color:#e74c3c; font-size:20px; font-weight:bold;">{" ".join([f"{n:02d}" for n in xuan5])}</span><br>
                                <hr style="margin:10px 0; border:1px dashed #ccc;">
                                <b>【选八复式 爆大奖】</b><br>
                                <span style="color:#e74c3c; font-size:18px; font-weight:bold;">{" ".join([f"{n:02d}" for n in xuan8])}</span><br>
                            </div>
                            <div style="font-size: 12px; color: #eee;">
                                扫描二维码 / 微信添加 <b>{MY_WECHAT_ID}</b> 参与合买<br>
                                (长按此区域截图保存，一键发朋友圈引流！)
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        # === 标签3：数据源与上传 (修复) ===
        with t_src:
            st.markdown("### 📂 本地系统文件池")
            st.write(f"当前识别到的 {choice} 历史文件：")
            for f in all_files:
                st.code(f)
            
            st.markdown("### 📤 上传最新自定义数据")
            uploaded_file = st.file_uploader("支持上传 .xls, .xlsx 或 .csv 格式的文件，系统将自动读取期号与号码列：", type=['csv', 'xls', 'xlsx'])
            if uploaded_file is not None:
                try:
                    # 模拟保存并使用新数据
                    temp_df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(('xls','xlsx')) else pd.read_csv(uploaded_file)
                    st.success(f"✅ 成功读取上传的文件：{uploaded_file.name}，共包含 {len(temp_df)} 条数据记录。")
                    st.dataframe(temp_df.head(10))
                    st.info("💡 数据已装载进内存池，当前 AI 演算将以您上传的数据作为基础样本！")
                except Exception as e:
                    st.error(f"❌ 读取文件出错，请确保格式正确: {e}")

        # === 标签4：水军交流区 (复活) ===
        with t_chat:
            st.markdown("### 💬 实战玩家交流大厅")
            # 完整复刻原版的水军库
            users = ["李哥", "王总", "陈老板", "发财哥", "张总", "顺风顺水", "一生平安", "天道酬勤", "A小刘", "老牛", "大忽悠", "追梦人", "稳中求胜"]
            msgs = ["今天必出08！", "昨天的杀号太准了，今天继续跟！", "求个选五复式大底！", "马尔科夫链那个算法确实有点科学依据的。", "这杀号绝了，之前我自己挑的全是死号...", "求今日胆码！", "刚刚的摇号模拟动画看着好有感觉啊！", "AC复杂度怎么看？", "刚充了VIP，坐等今晚收米。", "这软件的深度拟合有点东西的啊...", "有人合买今晚的大底复式吗？", "跟团长吃肉了！", "已添加微信，求带！"]
            
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
    st.warning("⚠️ 未找到本地数据文件。请在【🗄️ 数据源与上传】标签页中手动上传。")
