import random
from collections import Counter

import pandas as pd
import streamlit as st

from auth import MY_WECHAT_ID, logout, unlock_with_code
from components import render_bottom_nav, render_hero_card, render_metric_cards, render_prediction_card
from data_fetch import build_synced_dataframe, load_cloud_or_local_data, save_synced_dataframe
from formula_engine import (
    build_probability_profile,
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
    _, count_r, _, count_b = get_lottery_rules(choice)
    latest = df.iloc[0]
    values = [int(latest[col]) for col in d_cols[: count_r + count_b]]
    red_nums = values[:count_r]
    blue_nums = values[count_r:]
    render_hero_card(choice, f"{choice} #{int(latest['期号'])}", "最新样本已载入", red_nums, blue_nums)

    calc_df = df.head(view_limit).copy()
    calc_df["和值"] = calc_df[d_cols].sum(axis=1)
    calc_df["跨度"] = calc_df[d_cols].max(axis=1) - calc_df[d_cols].min(axis=1)

    repeat_count, consecutive_count = 0, 0
    detail_rows = []
    for idx, (_, row) in enumerate(calc_df.iterrows()):
        nums = sorted([int(row[col]) for col in d_cols])
        odd_count = sum(1 for n in nums if n % 2 == 1)
        even_count = len(nums) - odd_count
        consecutive = any(nums[i + 1] - nums[i] == 1 for i in range(len(nums) - 1))
        if consecutive:
            consecutive_count += 1

        repeat_status = "无重号"
        if idx + 1 < len(calc_df):
            prev_nums = set(int(calc_df.iloc[idx + 1][col]) for col in d_cols)
            intersects = sorted(set(nums).intersection(prev_nums))
            if intersects:
                repeat_count += 1
                repeat_status = "重号 " + " ".join(format_number(x, choice) for x in intersects)

        detail_rows.append(
            {
                "期号": f"第 {int(row['期号'])} 期",
                "和值": int(row["和值"]),
                "跨度": int(row["跨度"]),
                "奇偶比": f"{odd_count}:{even_count}",
                "连号": "有" if consecutive else "无",
                "重号": repeat_status,
            }
        )

    mean_value = int(calc_df["和值"].mean()) if not calc_df.empty else 0
    spread = int((calc_df["和值"].max() - calc_df["和值"].min()) / 2) if len(calc_df) > 1 else 0
    repeat_rate = f"{(repeat_count / len(calc_df) * 100):.0f}%" if len(calc_df) else "0%"
    consecutive_rate = f"{(consecutive_count / len(calc_df) * 100):.0f}%" if len(calc_df) else "0%"
    metrics = [
        {"label": "均值和值", "value": mean_value, "hint": f"取样窗口 {view_limit} 期", "color": "#81cfff"},
        {"label": "平均偏差", "value": spread, "hint": "波动宽度估算", "color": "#ff8a73"},
        {"label": "历史重号率", "value": repeat_rate, "hint": "与上一期重复占比", "color": "#7dffa2"},
        {"label": "历史连号率", "value": consecutive_rate, "hint": "连号出现频率", "color": "#ffb4a5"},
    ]
    render_metric_cards(metrics)

    st.markdown('<div class="section-title">和值走势</div>', unsafe_allow_html=True)
    chart_df = calc_df[["期号", "和值"]].sort_values(by="期号").set_index("期号")
    st.line_chart(chart_df, use_container_width=True)

    st.markdown('<div class="section-title">形态明细</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

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

    st.markdown('<div class="section-title">窗口概率画像</div>', unsafe_allow_html=True)
    bet_count = st.number_input("评估注数", min_value=1, max_value=500, value=10, step=1, key=f"bet_count_{choice}")
    profile = build_probability_profile(df.head(view_limit), choice, bet_count=bet_count)
    if profile:
        probability_metrics = [
            {"label": "理论组合数", "value": f"{profile['total_combinations']:,}", "hint": f"基于近 {profile['window_size']} 期窗口", "color": "#81cfff"},
            {"label": "和值期望", "value": f"{profile['expected_sum']:.1f}", "hint": "真实窗口均值", "color": "#7dffa2"},
            {"label": "和值方差", "value": f"{profile['variance']:.1f}", "hint": f"标准差 {profile['std_dev']:.1f}", "color": "#ff8a73"},
            {"label": "风险指数", "value": f"{profile['risk_index']:.3f}", "hint": "标准差 / 期望", "color": "#ffb4a5"},
        ]
        render_metric_cards(probability_metrics)

        st.markdown(
            f"""
            <div class="glass-card result-card">
              <div class="result-title">真实窗口概率说明</div>
              <div class="result-desc">以下结果严格基于当前期数窗口 {view_limit} 期历史样本，不读取更长样本，不做伪随机修饰。</div>
              <div class="code-line">单注命中概率：{profile['single_hit_probability']:.10f} | {bet_count} 注不重复命中概率：{profile['no_repeat_multi_probability']:.10f} | {bet_count} 注可重复命中概率：{profile['repeatable_multi_probability']:.10f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="glass-card result-card">
              <div class="result-title">结构分布</div>
              <div class="result-desc">奇偶与重号概率按当前彩种的真实组合空间计算。</div>
              <div class="code-line">主奇偶结构：{profile['common_odd_count']} 奇 | 概率 {profile['odd_probability']:.6f} | 常见重号数：{profile['common_repeat_count']} | 概率 {profile['repeat_probability']:.6f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-title">冷热修正排名</div>', unsafe_allow_html=True)
        hot_cold_df = pd.DataFrame(profile["corrected_rank"][:15]).copy()
        hot_cold_df["号码"] = hot_cold_df["号码"].map(lambda x: format_number(x, choice))
        hot_cold_df["修正概率"] = hot_cold_df["修正概率"].map(lambda x: f"{x:.6f}")
        st.dataframe(hot_cold_df, use_container_width=True, hide_index=True)

        if profile["back_summary"]:
            st.markdown('<div class="section-title">后区频次</div>', unsafe_allow_html=True)
            back_df = pd.DataFrame(profile["back_summary"][:8]).copy()
            back_df["号码"] = back_df["号码"].map(lambda x: format_number(x, choice))
            st.dataframe(back_df, use_container_width=True, hide_index=True)

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
