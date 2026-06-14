import random
from collections import Counter

import pandas as pd
import streamlit as st

from auth import MY_WECHAT_ID, logout, unlock_with_code
from components import render_bottom_nav, render_hero_card, render_metric_cards, render_prediction_card
from data_fetch import build_synced_dataframe, load_cloud_or_local_data, save_synced_dataframe
from formula_engine import (
    calculate_bets,
    calculate_frequencies,
    get_advanced_predictions,
    get_basic_predictions,
    run_tactical_manual_analysis,
    scan_advanced_patterns,
)
from lottery_rules import format_number, get_lottery_rules


def render_dashboard(df, choice, view_limit):
    if df is None or df.empty:
        st.warning("当前没有可用数据。")
        return

    d_cols = [c for c in df.columns if c != "期号"]
    red_nums, blue_nums = [], []
    pool_r, count_r, _, count_b = get_lottery_rules(choice)
    latest = df.iloc[0]
    values = [int(latest[col]) for col in d_cols[: count_r + count_b]]
    red_nums = values[:count_r]
    blue_nums = values[count_r:]
    render_hero_card(choice, f"{choice} #{int(latest['期号'])}", "最新样本已载入", red_nums, blue_nums)

    calc_df = df.head(view_limit).copy()
    calc_df["和值"] = calc_df[d_cols].sum(axis=1)
    mean_value = int(calc_df["和值"].mean()) if not calc_df.empty else 0
    spread = int((calc_df["和值"].max() - calc_df["和值"].min()) / 2) if len(calc_df) > 1 else 0
    metrics = [
        {"label": "均值和值", "value": mean_value, "hint": f"取样窗口 {view_limit} 期", "color": "#81cfff"},
        {"label": "平均偏差", "value": spread, "hint": "波动宽度估算", "color": "#ff8a73"},
    ]
    render_metric_cards(metrics)

    st.markdown('<div class="section-title">历史样本</div>', unsafe_allow_html=True)
    show_df = df.head(min(view_limit, 12)).copy()
    for col in d_cols:
        show_df[col] = show_df[col].map(lambda x: format_number(x, choice))
    st.dataframe(show_df, use_container_width=True, hide_index=True)
    render_bottom_nav("看板")


def render_formula_section(df, choice, view_limit):
    if df is None or df.empty:
        st.warning("当前没有可用开奖数据，请先上传或同步对应彩种数据文件。")
        render_bottom_nav("公式")
        return

    st.markdown('<div class="section-title">统计推演</div>', unsafe_allow_html=True)
    if st.button("启动统计推演", use_container_width=True, key=f"basic_{choice}"):
        st.session_state["basic_click_count"] = st.session_state.get("basic_click_count", 0) + 1

    if st.session_state.get("basic_click_count", 0) > 0:
        for item in get_basic_predictions(df.head(view_limit), choice, st.session_state["basic_click_count"]):
            render_prediction_card(item["name"], item["desc"], item["red"], item["blue"], choice)

    st.markdown('<div class="section-title">高阶公式</div>', unsafe_allow_html=True)
    if not st.session_state.get("vip_unlocked"):
        code = st.text_input("输入授权码解锁高阶公式", type="password", key="vip_code")
        if st.button("激活高级权限", use_container_width=True, key="unlock_btn"):
            ok, message = unlock_with_code(code)
            if ok:
                st.success(f"激活成功，剩余 {message} 天。")
                st.rerun()
            else:
                st.error(message)
    else:
        st.info(f"已激活，剩余 {st.session_state.get('days_left', '未知')} 天")
        if st.button("生成高阶推演", use_container_width=True, key=f"adv_{choice}"):
            st.session_state["adv_click_count"] = st.session_state.get("adv_click_count", 0) + 1
        if st.session_state.get("adv_click_count", 0) > 0:
            for item in get_advanced_predictions(df.head(view_limit), choice, st.session_state["adv_click_count"]):
                render_prediction_card(item["name"], item["desc"], item["red"], item["blue"], choice, tone=item.get("tone", "primary"))

        if st.button("退出授权", use_container_width=True, key="logout_btn"):
            logout()
            st.rerun()
    render_bottom_nav("公式")


def render_tactical_section(df_base, choice, view_limit):
    if not st.session_state.get("vip_unlocked"):
        st.warning("该区域需先完成卡密授权。")
        render_bottom_nav("录入")
        return

    if choice not in ["双色球", "大乐透"]:
        st.warning("手动样本录入当前仅支持双色球和大乐透。")
        render_bottom_nav("录入")
        return

    is_dlt = choice == "大乐透"

    st.markdown('<div class="section-title">手动样本录入</div>', unsafe_allow_html=True)
    raw_text = st.text_area(
        "粘贴样本号码",
        height=140,
        placeholder="例如：01 02 03 04 05 + 06 07\\n08 12 19 23 31 + 03 11",
    )

    if st.button("启动样本分析", use_container_width=True, key="tactical_run"):
        history_limit = str(view_limit)
        recent_red_pool = None
        recent_blue_pool = None
        history_tongqi_pool = None
        weekday_pool = None
        weekday_blue_pool = None

        if df_base is not None and not df_base.empty:
            front_counts, back_counts = calculate_frequencies(df_base.head(view_limit), is_dlt=is_dlt)
            recent_red_pool = [x[0] for x in front_counts.most_common(15)]
            recent_blue_pool = [x[0] for x in back_counts.most_common(6)]

        result = run_tactical_manual_analysis(
            raw_text,
            is_dlt=is_dlt,
            history_limit=history_limit,
            recent_red_pool=recent_red_pool,
            recent_blue_pool=recent_blue_pool,
            history_tongqi_pool=history_tongqi_pool,
            weekday_pool=weekday_pool,
            weekday_blue_pool=weekday_blue_pool,
        )
        st.session_state["tactical_result"] = result

    result = st.session_state.get("tactical_result")
    if result and result.get("ok"):
        st.markdown('<div class="section-title">样本核对</div>', unsafe_allow_html=True)
        st.code(
            "红球: " + " ".join([f"{x:02d}" for x in result["red_nums"]]) +
            (("\n蓝球: " + " ".join([f"{x:02d}" for x in result["blue_nums"]])) if result["blue_nums"] else "")
        )

        st.markdown('<div class="section-title">反向结果</div>', unsafe_allow_html=True)
        render_prediction_card("高热区域", "高频撞车样本，优先规避。", result["hot_nums"], [], choice, tone="accent")
        render_prediction_card("潜伏区域", "冷区与单次出现样本的并集。", result["potential_nums"][:6], [], choice)
        render_prediction_card("偏移阵地", "围绕高热样本做左右偏移。", result["offset_recommend"][:6], [], choice)
        render_prediction_card("主推单式", "多维交集后的主推参考。", result["final_math_reds"], result["final_math_blues"], choice)
        render_prediction_card("复式扩容", f"理论组合 {result['zhusu']} 注。", result["fushi_math_reds"], result["fushi_math_blues"], choice, tone="accent")
    elif result and not result.get("ok"):
        st.error(result["message"])
    render_bottom_nav("录入")


def render_lobby():
    st.markdown('<div class="section-title">联络与说明</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="glass-card">
          <div class="result-title">授权与服务</div>
          <div class="result-desc">高阶公式、样本录入、组合压缩均需授权后使用。</div>
          <div class="code-line">微信：{MY_WECHAT_ID}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="glass-card">
          <div class="result-title">说明</div>
          <div class="muted">
            本系统展示的统计、路径、AC 约束、状态转移、过滤与压缩结果，仅作为样本分析参考。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_bottom_nav("大厅")
