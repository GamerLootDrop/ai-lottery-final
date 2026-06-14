import streamlit as st


TACTICAL_CSS = """
<style>
:root {
  --bg: #131313;
  --bg-soft: #1c1b1b;
  --panel: rgba(28, 27, 27, 0.68);
  --panel-strong: #201f1f;
  --panel-border: rgba(135, 146, 155, 0.16);
  --text: #e5e2e1;
  --muted: #bdc8d1;
  --primary: #81cfff;
  --primary-strong: #29b6f6;
  --success: #05e777;
  --danger: #ff8a73;
  --warning: #ffb4a5;
}

.stApp {
  background:
    radial-gradient(circle at top right, rgba(41, 182, 246, 0.08), transparent 24%),
    linear-gradient(180deg, #0f0f0f 0%, #131313 100%);
  color: var(--text);
}

[data-testid="stHeader"], #MainMenu, footer, .stDeployButton, [data-testid="stToolbar"] {
  display: none !important;
}

.block-container {
  max-width: 820px !important;
  padding: 1rem 1rem 6rem !important;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  margin-bottom: 12px;
  padding: 0 12px;
  border: 1px solid var(--panel-border);
  border-radius: 16px;
  background: rgba(19, 19, 19, 0.78);
  backdrop-filter: blur(18px);
}

.topbar-title {
  color: var(--primary);
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0;
}

.glass-card {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: 16px;
  padding: 16px;
  backdrop-filter: blur(16px);
  box-shadow: 0 0 0 1px rgba(129, 207, 255, 0.03) inset;
}

.section-title {
  font-size: 12px;
  color: var(--muted);
  margin: 12px 0 8px;
  padding-left: 10px;
  border-left: 2px solid var(--primary);
}

.hero-issue {
  color: var(--text);
  font-weight: 700;
  font-size: 16px;
}

.hero-date {
  color: var(--muted);
  font-size: 12px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(32, 31, 31, 0.95);
  border: 1px solid var(--panel-border);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--success);
  box-shadow: 0 0 8px var(--success);
}

.number-row {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 8px;
  align-items: center;
}

.number-orb {
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "JetBrains Mono", monospace;
  font-weight: 700;
  font-size: 22px;
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.13), transparent 62%),
    rgba(28, 27, 27, 0.9);
}

.orb-primary {
  color: var(--primary);
  border: 1px solid rgba(129, 207, 255, 0.45);
  box-shadow: 0 0 12px rgba(129, 207, 255, 0.18);
}

.orb-accent {
  color: var(--danger);
  border: 1px solid rgba(255, 138, 115, 0.45);
  box-shadow: 0 0 12px rgba(255, 138, 115, 0.16);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  min-height: 132px;
}

.metric-label {
  color: var(--muted);
  font-size: 12px;
}

.metric-value {
  margin-top: 18px;
  font-size: 40px;
  line-height: 1;
  font-family: "JetBrains Mono", monospace;
  font-weight: 700;
}

.metric-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--muted);
}

.result-card {
  margin-bottom: 12px;
}

.result-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 4px;
}

.result-desc {
  color: var(--muted);
  font-size: 12px;
  margin-bottom: 10px;
}

.ball-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.ball-mini {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: "JetBrains Mono", monospace;
  font-weight: 700;
  background: rgba(19, 19, 19, 0.92);
}

.ball-mini.primary {
  color: var(--primary);
  border: 1px solid rgba(129, 207, 255, 0.38);
}

.ball-mini.accent {
  color: var(--danger);
  border: 1px solid rgba(255, 138, 115, 0.38);
}

.code-line {
  font-family: "JetBrains Mono", monospace;
  color: var(--text);
  background: rgba(14, 14, 14, 0.78);
  border: 1px solid var(--panel-border);
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 13px;
}

.bottom-nav {
  position: sticky;
  bottom: 8px;
  z-index: 40;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-top: 16px;
  padding: 8px;
  border-radius: 18px;
  background: rgba(19, 19, 19, 0.92);
  border: 1px solid var(--panel-border);
  backdrop-filter: blur(18px);
}

.nav-item {
  min-height: 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border-radius: 12px;
  color: var(--muted);
  font-size: 11px;
}

.nav-item.active {
  color: #0c1a22;
  background: var(--primary-strong);
  font-weight: 700;
}

.muted {
  color: var(--muted);
  font-size: 13px;
}

.small-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 6px;
}

.heat-box {
  border-radius: 8px;
  min-height: 54px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  border: 1px solid rgba(135, 146, 155, 0.18);
}

.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pill {
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid var(--panel-border);
  background: rgba(19, 19, 19, 0.9);
  font-family: "JetBrains Mono", monospace;
  font-size: 13px;
}

.divider {
  height: 1px;
  background: rgba(135, 146, 155, 0.14);
  margin: 16px 0;
}

@media (max-width: 640px) {
  .block-container {
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
  }
  .number-row {
    gap: 6px;
  }
  .number-orb {
    font-size: 18px;
  }
}
</style>
"""


def inject_styles():
    st.markdown(TACTICAL_CSS, unsafe_allow_html=True)

