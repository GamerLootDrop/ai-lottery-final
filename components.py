import streamlit as st

from lottery_rules import format_number


def render_topbar(title):
    st.markdown(
        f"""
        <div class="topbar">
          <div class="muted">战术中控</div>
          <div class="topbar-title">{title}</div>
          <div class="muted">设置</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero_card(choice, issue_text, date_text, red_nums, blue_nums):
    red_html = "".join([f'<div class="number-orb orb-primary">{format_number(n, choice)}</div>' for n in red_nums])
    blue_html = "".join([f'<div class="number-orb orb-accent">{format_number(n, choice)}</div>' for n in blue_nums])
    sep_html = '<div class="muted" style="text-align:center;">|</div>' if blue_nums else ""
    st.markdown(
        f"""
        <section class="glass-card">
          <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;">
            <div>
              <div class="section-title" style="margin-top:0;border-left:none;padding-left:0;">最新截获</div>
              <div class="hero-issue">{issue_text}</div>
              <div class="hero-date">{date_text}</div>
            </div>
            <div class="status-pill"><span class="status-dot"></span>已核实</div>
          </div>
          <div style="height:12px;"></div>
          <div class="number-row">{red_html}{sep_html}{blue_html}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_metric_cards(metrics):
    cards = []
    for item in metrics:
        cards.append(
            f"""
            <div class="glass-card metric-card">
              <div class="metric-label">{item["label"]}</div>
              <div class="metric-value" style="color:{item.get("color", "#81cfff")};">{item["value"]}</div>
              <div class="metric-hint">{item["hint"]}</div>
            </div>
            """
        )
    st.markdown(f'<div class="metric-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_prediction_card(title, desc, red_nums, blue_nums, choice, tone="primary"):
    primary_class = "accent" if tone == "accent" else "primary"
    balls = "".join([f'<span class="ball-mini {primary_class}">{format_number(n, choice)}</span>' for n in red_nums])
    if blue_nums:
        balls += "".join([f'<span class="ball-mini accent">{format_number(n, choice)}</span>' for n in blue_nums])
    st.markdown(
        f"""
        <div class="glass-card result-card">
          <div class="result-title">{title}</div>
          <div class="result-desc">{desc}</div>
          <div class="ball-strip">{balls}</div>
          <div class="code-line">{' '.join([format_number(n, choice) for n in red_nums])}{(' | ' + ' '.join([format_number(n, choice) for n in blue_nums])) if blue_nums else ''}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bottom_nav(active_label):
    labels = ["看板", "录入", "公式", "大厅"]
    items = []
    for label in labels:
        klass = "nav-item active" if label == active_label else "nav-item"
        items.append(f'<div class="{klass}"><div>{label}</div></div>')
    st.markdown(f'<div class="bottom-nav">{"".join(items)}</div>', unsafe_allow_html=True)

