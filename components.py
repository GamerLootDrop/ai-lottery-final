import streamlit as st

from auth import MY_WECHAT_ID, logout, unlock_with_code
from lottery_rules import format_number


def render_topbar(title):
    st.markdown(
        f'<div class="topbar"><div class="muted">战术中控</div><div class="topbar-title">{title}</div><div class="muted">设置</div></div>',
        unsafe_allow_html=True,
    )


def render_hero_card(choice, issue_text, date_text, red_nums, blue_nums):
    red_html = "".join([f'<div class="number-orb orb-primary">{format_number(n, choice)}</div>' for n in red_nums])
    blue_html = "".join([f'<div class="number-orb orb-accent">{format_number(n, choice)}</div>' for n in blue_nums])
    sep_html = '<div class="muted" style="text-align:center;">|</div>' if blue_nums else ""
    st.markdown(
        f'<section class="glass-card"><div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;"><div><div class="section-title" style="margin-top:0;border-left:none;padding-left:0;">最新截获</div><div class="hero-issue">{issue_text}</div><div class="hero-date">{date_text}</div></div><div class="status-pill"><span class="status-dot"></span>已核实</div></div><div style="height:12px;"></div><div class="number-row">{red_html}{sep_html}{blue_html}</div></section>',
        unsafe_allow_html=True,
    )


def render_metric_cards(metrics):
    cards = []
    for item in metrics:
        cards.append(
            f'<div class="glass-card metric-card"><div class="metric-label">{item["label"]}</div><div class="metric-value" style="color:{item.get("color", "#81cfff")};">{item["value"]}</div><div class="metric-hint">{item["hint"]}</div></div>'
        )
    st.markdown(f'<div class="metric-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_prediction_card(title, desc, red_nums, blue_nums, choice, tone="primary"):
    primary_class = "accent" if tone == "accent" else "primary"
    balls = "".join([f'<span class="ball-mini {primary_class}">{format_number(n, choice)}</span>' for n in red_nums])
    if blue_nums:
        balls += "".join([f'<span class="ball-mini accent">{format_number(n, choice)}</span>' for n in blue_nums])
    number_text = " ".join([format_number(n, choice) for n in red_nums])
    if blue_nums:
        number_text += " | " + " ".join([format_number(n, choice) for n in blue_nums])
    st.markdown(
        f'<div class="glass-card result-card"><div class="result-title">{title}</div><div class="result-desc">{desc}</div><div class="ball-strip">{balls}</div><div class="code-line">{number_text}</div></div>',
        unsafe_allow_html=True,
    )
    st.code(number_text, language="text")


def render_access_banner():
    if st.session_state.get("vip_unlocked"):
        days_left = st.session_state.get("days_left", "未知")
        st.markdown(
            f"""
            <div class="access-strip access-compact">
              <div>
                <div class="result-title">高阶版已解锁</div>
                <div class="result-desc">剩余 {days_left} 天，AC12 / 马尔科夫链 / 样本反向已开放。</div>
              </div>
              <div class="access-badge">已解锁</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        """
        <div class="access-strip locked">
          <div>
            <div class="result-title">当前权限：基础版</div>
            <div class="result-desc">数据看板可直接使用；高阶公式、手动样本和组合压缩需授权。</div>
          </div>
          <div class="access-badge">待解锁</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("解锁高阶功能", use_container_width=True, key="top_unlock_go"):
        st.session_state["show_top_unlock"] = True
        st.session_state["page"] = "公式中心"
    render_top_unlock_dialog()


def render_top_unlock_dialog():
    if not st.session_state.get("show_top_unlock"):
        return

    dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
    if dialog:
        @dialog("快速解锁高阶功能")
        def _unlock_dialog():
            render_unlock_panel("快速解锁高阶功能", key_prefix="top")
            if st.button("暂不解锁", use_container_width=True, key="close_top_unlock"):
                st.session_state["show_top_unlock"] = False
                st.rerun()

        _unlock_dialog()
        return

    if st.session_state.get("show_top_unlock"):
        render_unlock_panel("快速解锁高阶功能", key_prefix="top")


def render_unlock_panel(title="高阶权限未解锁", key_prefix="vip"):
    if st.session_state.get("vip_unlocked"):
        days_left = st.session_state.get("days_left", "未知")
        st.markdown(
            f"""
            <div class="glass-card unlock-panel">
              <div class="result-title">高阶权限已生效</div>
              <div class="result-desc">当前剩余 {days_left} 天。需要续费、换设备或开通新授权，可添加微信处理。</div>
              <div class="code-line">微信：{MY_WECHAT_ID}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.code(MY_WECHAT_ID, language="text")
        return True

    benefits = [
        "AC12 高阶约束",
        "马尔科夫链转移",
        "手动样本反向分析",
        "专家组合压缩",
        "自建数据沙盘",
    ]
    benefit_html = "".join(f'<span class="access-chip">{item}</span>' for item in benefits)
    st.markdown(
        f"""
        <div class="glass-card unlock-panel">
          <div class="result-title">{title}</div>
          <div class="result-desc">输入授权码后开放完整公式模块。没有授权码可以添加微信办理，备注“高阶公式”。</div>
          <div class="access-chip-row">{benefit_html}</div>
          <div class="code-line">微信：{MY_WECHAT_ID}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(MY_WECHAT_ID, language="text")

    code = st.text_input("授权码", type="password", key=f"{key_prefix}_code", placeholder="输入后点击激活")
    if st.button("激活高阶权限", use_container_width=True, key=f"{key_prefix}_unlock_btn"):
        ok, message = unlock_with_code(code)
        if ok:
            st.session_state[f"{key_prefix}_auth_message"] = ("success", f"激活成功，剩余 {message} 天。")
            st.session_state["show_top_unlock"] = False
            st.rerun()
        else:
            st.session_state[f"{key_prefix}_auth_message"] = ("error", f"{message}。如需开通或续费，请添加微信 {MY_WECHAT_ID}。")

    auth_message = st.session_state.get(f"{key_prefix}_auth_message")
    if auth_message:
        level, text = auth_message
        if level == "success":
            st.success(text)
        else:
            st.error(text)
    return st.session_state.get("vip_unlocked", False)


def render_bottom_nav(active_label):
    labels = [("看板", "数据看板"), ("录入", "手动录入"), ("公式", "公式中心"), ("大厅", "交流大厅")]
    cols = st.columns(4)
    for col, (label, page_name) in zip(cols, labels):
        button_label = f"● {label}" if label == active_label else label
        with col:
            if st.button(button_label, use_container_width=True, key=f"nav_{label}"):
                st.session_state["page"] = page_name
                st.rerun()
