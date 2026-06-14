import os
import re
import time

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

from lottery_rules import LOTTERY_FILES, WEB_GAME_CODES


def find_lottery_file(choice, base_dir="."):
    file_kw = LOTTERY_FILES[choice]
    all_files = [
        f
        for f in os.listdir(base_dir)
        if file_kw in f.lower() and (f.endswith(".xls") or f.endswith(".xlsx") or f.endswith(".csv"))
    ]
    return next((f for f in all_files if "_synced" in f), all_files[0] if all_files else None)


@st.cache_data
def load_full_data(file_path, choice):
    try:
        raw_df = pd.read_excel(file_path) if file_path.endswith((".xls", ".xlsx")) else pd.read_csv(file_path)
        raw_df.columns = [str(c).strip() for c in raw_df.columns]
        q_col = next((c for c in raw_df.columns if "期" in c or "NO" in c.upper()), raw_df.columns[0])
        raw_df[q_col] = pd.to_numeric(raw_df[q_col], errors="coerce")
        raw_df = raw_df.dropna(subset=[q_col])

        limits = {
            "双色球": 7,
            "大乐透": 7,
            "福彩3D": 3,
            "排列3": 3,
            "排列5": 5,
            "七星彩": 7,
            "快乐8": 20,
        }
        max_balls = limits.get(choice, 7)

        q_idx = list(raw_df.columns).index(q_col)
        ball_cols = []
        for i in range(q_idx + 1, len(raw_df.columns)):
            col = raw_df.columns[i]
            nums = pd.to_numeric(raw_df[col], errors="coerce").dropna()
            if not nums.empty and (nums <= 81).all():
                ball_cols.append(col)
            if len(ball_cols) == max_balls:
                break

        clean_df = raw_df[[q_col] + ball_cols].copy()
        new_names = ["期号"] + [f"b_{i + 1}" for i in range(len(ball_cols))]
        clean_df.columns = new_names
        for c in new_names:
            clean_df[c] = pd.to_numeric(clean_df[c], errors="coerce").fillna(0).astype(int)

        needs_zero = choice in ["双色球", "大乐透", "快乐8"]
        return clean_df.sort_values("期号", ascending=False), "期号", new_names[1:], needs_zero, file_path
    except Exception:
        return None, None, None, None, None


@st.cache_data(ttl=3600)
def fetch_from_web(game_code, choice, d_cols_len, limit=50):
    urls = [
        f"https://datachart.500.com/{game_code}/history/newinc/history.php?limit={limit}",
        f"https://datachart.500.com/{game_code}/history/inc/history.php?limit={limit}",
    ]
    headers = {"User-Agent": "Mozilla/5.0"}
    web_rows = []
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text, "html.parser")
            trs = soup.find_all("tr", class_=["t_tr1", "t_tr2", "t_tr"]) or soup.find_all("tr")
            for tr in trs:
                tds = tr.find_all("td")
                if len(tds) < d_cols_len + 1:
                    continue
                iss_str = re.sub(r"\D", "", tds[0].get_text(strip=True))
                if len(iss_str) < 3:
                    continue
                issue_val = int("20" + iss_str[:10]) if len(iss_str) == 5 else int(iss_str[:10])

                rest_text = " ".join([td.get_text(separator=" ") for td in tds[1:]])
                balls = [int(n) for n in re.findall(r"\d+", rest_text)]
                balls = [n for n in balls if 0 <= n <= 81][:d_cols_len]

                if len(balls) == d_cols_len:
                    web_rows.append({"issue": issue_val, "balls": balls})
            if web_rows:
                break
        except Exception:
            continue
    return web_rows


def build_synced_dataframe(df, q_col, d_cols, choice):
    web_data = fetch_from_web(WEB_GAME_CODES.get(choice, "ssq"), choice, len(d_cols))
    if not web_data:
        return None, "抓取失败，请检查网络或稍后再试。"

    latest_web_issue = str(web_data[0]["issue"])
    latest_local_issue = str(df.iloc[0][q_col])
    if latest_web_issue == latest_local_issue:
        return df, f"当前已是全网最新数据，期号 {latest_local_issue}。"

    clean_web_rows = []
    for item in web_data:
        row_dict = {"期号": item["issue"]}
        for i, col in enumerate(d_cols):
            if i < len(item["balls"]):
                row_dict[col] = item["balls"][i]
        clean_web_rows.append(row_dict)

    web_df = pd.DataFrame(clean_web_rows).astype("int64")
    updated = (
        pd.concat([web_df, df], ignore_index=True)
        .drop_duplicates(subset=[q_col], keep="first")
        .sort_values(q_col, ascending=False)
        .head(2000)
    )
    return updated, f"同步成功，已抓取 {len(clean_web_rows)} 条网页数据。"


def save_synced_dataframe(updated, file_path):
    save_path = file_path if file_path.endswith(".csv") else file_path.replace(".xls", "_synced.csv")
    save_path = save_path.replace(".xlsx", "_synced.csv")
    updated.to_csv(save_path, index=False, encoding="utf-8-sig")
    st.cache_data.clear()
    return save_path


def fetch_latest_window(lottery_code, local_latest_issue=0, custom_limit=100):
    now_time = time.time()
    urls = [
        f"https://datachart.500.com/{lottery_code}/history/newinc/history.php?limit={custom_limit}&_t={int(now_time)}",
        f"https://datachart.500.com/{lottery_code}/history/inc/history.php?limit={custom_limit}&_t={int(now_time)}",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Referer": f"https://datachart.500.com/{lottery_code}/history/history.shtml",
    }

    new_rows = []
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code != 200:
                continue
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text, "html.parser")
            trs = soup.find_all("tr", class_=["t_tr1", "t_tr2", "t_tr"]) or soup.find_all("tr")

            for tr in trs:
                tds = tr.find_all("td")
                if len(tds) < 8:
                    continue

                iss_str = re.sub(r"\D", "", tds[0].get_text(strip=True))
                if len(iss_str) < 3:
                    continue
                issue_val = int("20" + iss_str[:10]) if len(iss_str) == 5 else int(iss_str[:10])
                if custom_limit == 50 and issue_val <= local_latest_issue:
                    continue

                balls = []
                for td in tds[1:]:
                    text = td.get_text(strip=True)
                    if text.isdigit():
                        balls.append(int(text))

                date_str = tds[-1].get_text(strip=True)
                if not re.search(r"\d{4}-\d{2}-\d{2}", date_str):
                    date_str = time.strftime("%Y-%m-%d", time.localtime())

                if len(balls) >= 7:
                    core_balls = balls[:7]
                    new_rows.append(
                        [
                            issue_val,
                            date_str,
                            core_balls[0],
                            core_balls[1],
                            core_balls[2],
                            core_balls[3],
                            core_balls[4],
                            core_balls[5],
                            core_balls[6],
                        ]
                    )
            if new_rows:
                break
        except Exception:
            continue

    if new_rows:
        cols = (
            ["期号", "日期", "前1", "前2", "前3", "前4", "前5", "后1", "后2"]
            if lottery_code == "dlt"
            else ["期号", "日期", "前1", "前2", "前3", "前4", "前5", "前6", "后1"]
        )
        return pd.DataFrame(new_rows, columns=cols).sort_values(by="期号", ascending=False).reset_index(drop=True)
    return pd.DataFrame()


@st.cache_data(ttl=5)
def load_cloud_or_local_data(lottery_code, uploaded_file=None, target_mode="默认"):
    df_local = pd.DataFrame()
    source = uploaded_file if uploaded_file else (
        f"{lottery_code}.csv"
        if os.path.exists(f"{lottery_code}.csv")
        else (f"{lottery_code}.xls" if os.path.exists(f"{lottery_code}.xls") else None)
    )

    if source:
        try:
            if hasattr(source, "seek"):
                source.seek(0)
            if str(source).endswith(("xls", "xlsx")):
                df_raw = pd.read_excel(source, header=None, dtype=str)
            else:
                df_raw = pd.read_csv(source, encoding_errors="ignore", header=None, dtype=str)

            cols_use = [0, 1, 2, 3, 4, 5, 6, 7, 8]
            c_names = (
                ["期号", "日期", "前1", "前2", "前3", "前4", "前5", "后1", "后2"]
                if lottery_code == "dlt"
                else ["期号", "日期", "前1", "前2", "前3", "前4", "前5", "前6", "后1"]
            )

            df_raw = df_raw.iloc[:, cols_use]
            df_raw.columns = c_names
            df_raw["前1"] = pd.to_numeric(df_raw["前1"], errors="coerce")
            df_raw = df_raw.dropna(subset=["前1"])
            df_raw["期号"] = df_raw["期号"].astype(str).str.replace(r"\D", "", regex=True)
            df_raw["期号"] = pd.to_numeric(df_raw["期号"], errors="coerce").fillna(0).astype(int)

            for c in c_names[2:]:
                df_raw[c] = pd.to_numeric(df_raw[c], errors="coerce").fillna(0).astype(int)
            df_local = df_raw[(df_raw["前1"] > 0) & (df_raw["前1"] <= 35)].sort_values(by="期号", ascending=False).reset_index(drop=True)
        except Exception:
            pass

    local_latest = int(df_local.iloc[0]["期号"]) if not df_local.empty else 0
    limit = 3000 if target_mode == "历史同期对比" and df_local.empty else 100
    df_new = fetch_latest_window(lottery_code, local_latest, custom_limit=limit)
    new_count = len(df_new)

    df_final = pd.concat([df_new, df_local], ignore_index=True) if not df_new.empty else df_local
    if not df_final.empty:
        df_final = df_final.drop_duplicates(subset=["期号"], keep="first")
        df_final = df_final.sort_values(by="期号", ascending=False).reset_index(drop=True)
        df_final["日期_解析"] = pd.to_datetime(df_final["日期"], errors="coerce")
        df_final["星期"] = df_final["日期_解析"].dt.dayofweek

    return df_final, new_count

