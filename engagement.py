import hashlib
import random
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st


DRAW_SCHEDULES = {
    "双色球": {"weekdays": [1, 3, 6], "close_time": "21:15"},
    "大乐透": {"weekdays": [0, 2, 5], "close_time": "21:10"},
    "七星彩": {"weekdays": [1, 4, 6], "close_time": "21:10"},
    "七乐彩": {"weekdays": [0, 2, 4], "close_time": "21:15"},
    "福彩3D": {"weekdays": [0, 1, 2, 3, 4, 5, 6], "close_time": "21:10"},
    "排列3": {"weekdays": [0, 1, 2, 3, 4, 5, 6], "close_time": "21:10"},
    "排列5": {"weekdays": [0, 1, 2, 3, 4, 5, 6], "close_time": "21:10"},
    "快乐8": {"weekdays": [0, 1, 2, 3, 4, 5, 6], "close_time": "21:30"},
}

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def get_next_draw(choice, now=None):
    now = now or datetime.now()
    schedule = DRAW_SCHEDULES.get(choice, DRAW_SCHEDULES["双色球"])
    hour, minute = [int(x) for x in schedule["close_time"].split(":")]
    for day_offset in range(8):
        candidate_date = now.date() + timedelta(days=day_offset)
        candidate = datetime.combine(candidate_date, datetime.min.time()).replace(hour=hour, minute=minute)
        if candidate.weekday() in schedule["weekdays"] and candidate > now:
            diff = candidate - now
            hours, remainder = divmod(int(diff.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            return {
                "target": candidate,
                "weekday": WEEKDAY_NAMES[candidate.weekday()],
                "remaining": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
                "close_time": schedule["close_time"],
            }
    return None


def visitor_alias(seed_text):
    digest = hashlib.md5(str(seed_text).encode("utf-8")).hexdigest().upper()
    return f"游客 {digest[:4]}"


def get_usage_snapshot(choice):
    if "visit_count" not in st.session_state:
        st.session_state["visit_count"] = random.randint(1200, 1800)
    st.session_state["visit_count"] += random.randint(0, 2)
    return {
        "today_visits": st.session_state["visit_count"],
        "active_choice": choice,
        "online_estimate": 1500 + random.randint(-40, 120),
    }


def _comments_sheet():
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(st.secrets["google"], scopes=scopes)
        client = gspread.authorize(creds)
        return client.open("Lotto_Comments").get_worksheet(0)
    except Exception:
        return None


def load_comments(limit=30):
    sh = _comments_sheet()
    if sh is None:
        return []
    try:
        rows = sh.get_all_records()
        df = pd.DataFrame(rows)
        if df.empty:
            return []
        if "是否展示" in df.columns:
            df = df[df["是否展示"].astype(str).isin(["是", "TRUE", "true", "1", ""])]
        return df.tail(limit).iloc[::-1].to_dict("records")
    except Exception:
        return []


def submit_comment(nickname, content, choice):
    content = str(content or "").strip()
    nickname = str(nickname or "").strip()
    if not content:
        return False, "请输入内容。"
    if len(content) > 120:
        return False, "内容请控制在 120 字以内。"
    banned = ["加微信", "VX", "qq", "QQ", "赌博", "博彩广告"]
    if any(word.lower() in content.lower() for word in banned):
        return False, "内容包含不适合展示的词，请调整后再提交。"

    sh = _comments_sheet()
    if sh is None:
        return False, "评论表未配置，暂时无法提交。"
    alias = nickname or visitor_alias(content + datetime.now().isoformat())
    try:
        sh.append_row(
            [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), alias[:12], content, choice, "是"],
            value_input_option="USER_ENTERED",
        )
        return True, "提交成功。"
    except Exception as exc:
        return False, f"提交失败：{exc}"

