import math
import random
import re
import time
from collections import Counter

import pandas as pd

from lottery_rules import format_number, get_lottery_rules, should_zero_pad


def calculate_ac_value(nums):
    diffs = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    return max(0, len(diffs) - (len(nums) - 1))


def render_number_text(r_res, b_res, choice):
    text = " ".join([format_number(n, choice) for n in r_res])
    if b_res:
        text += " | " + " ".join([format_number(n, choice) for n in b_res])
    return text


def extract_real_stats(df_view, pool_r, count_r, pool_b, count_b, variation_seed=0):
    random.seed(int(time.time()) + variation_seed)
    hot_r, cold_r, hot_b, cold_b = [], [], [], []

    if df_view is None or df_view.empty:
        return sorted(random.sample(pool_r, count_r)), sorted(random.sample(pool_r, count_r)), [], []

    try:
        safe_df = df_view.apply(pd.to_numeric, errors="coerce").fillna(-1).astype(int)
        r_raw = safe_df.iloc[:, 1 : 1 + count_r].values.flatten().tolist()
        r_history = [x for x in r_raw if x in pool_r]
        r_counter = Counter(r_history)

        most_common = [x[0] for x in r_counter.most_common()]
        base_hot = most_common[: count_r + 3]
        hot_r = random.sample(base_hot, min(count_r, len(base_hot)))
        while len(hot_r) < count_r:
            cand = random.choice(pool_r)
            if cand not in hot_r:
                hot_r.append(cand)

        missing = [x for x in pool_r if x not in r_counter]
        least_common = missing + [x[0] for x in r_counter.most_common()[: -count_r - 4 : -1]]
        least_common = list(dict.fromkeys(least_common))
        cold_r = random.sample(least_common, min(count_r, len(least_common)))
        while len(cold_r) < count_r:
            cand = random.choice(pool_r)
            if cand not in cold_r:
                cold_r.append(cand)

        if count_b > 0:
            b_raw = safe_df.iloc[:, 1 + count_r : 1 + count_r + count_b].values.flatten().tolist()
            b_history = [x for x in b_raw if x in pool_b]
            b_counter = Counter(b_history)

            b_most = [x[0] for x in b_counter.most_common()]
            hot_b = random.sample(b_most[: count_b + 2], min(count_b, len(b_most[: count_b + 2])))
            while len(hot_b) < count_b:
                cand = random.choice(pool_b)
                if cand not in hot_b:
                    hot_b.append(cand)

            b_missing = [x for x in pool_b if x not in b_counter]
            b_least = list(dict.fromkeys(b_missing + [x[0] for x in b_counter.most_common()[: -count_b - 3 : -1]]))
            cold_b = random.sample(b_least[: count_b + 2], min(count_b, len(b_least[: count_b + 2])))
            while len(cold_b) < count_b:
                cand = random.choice(pool_b)
                if cand not in cold_b:
                    cold_b.append(cand)

        return sorted(hot_r), sorted(cold_r), sorted(hot_b), sorted(cold_b)
    except Exception:
        return sorted(random.sample(pool_r, count_r)), sorted(random.sample(pool_r, count_r)), [], []


def get_basic_predictions(df_view, choice, click_count):
    sets = []
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    hot_r, cold_r, hot_b, cold_b = extract_real_stats(df_view, pool_r, count_r, pool_b, count_b, click_count)

    sets.append(
        {
            "name": "极热寻踪",
            "desc": f"统计学排查，分析近 {len(df_view)} 期高频热点。",
            "red": hot_r,
            "blue": hot_b,
            "text": render_number_text(hot_r, hot_b, choice),
        }
    )
    sets.append(
        {
            "name": "绝地反弹",
            "desc": "均值回归，追踪近期遗漏偏大的冷门样本。",
            "red": cold_r,
            "blue": cold_b,
            "text": render_number_text(cold_r, cold_b, choice),
        }
    )

    mix_r = sorted(list(set(hot_r[: max(1, count_r // 2)] + cold_r[: max(1, count_r // 3)])))
    while len(mix_r) < count_r:
        cand = random.choice(pool_r)
        if cand not in mix_r:
            mix_r.append(cand)
    mix_r = sorted(mix_r[:count_r])

    mix_b = []
    if count_b > 0:
        mix_b = sorted(list(set(hot_b[: max(1, count_b // 2)] + cold_b[: max(1, count_b // 2)])))
        while len(mix_b) < count_b:
            cand = random.choice(pool_b)
            if cand not in mix_b:
                mix_b.append(cand)
        mix_b = sorted(mix_b[:count_b])

    sets.append(
        {
            "name": "黄金均衡",
            "desc": "自然分布下的冷热混合配比。",
            "red": mix_r,
            "blue": mix_b,
            "text": render_number_text(mix_r, mix_b, choice),
        }
    )
    return sets


def real_markov_core(history_rows, pool, count, rng, order=1):
    transition_matrix = {n: Counter() for n in pool}
    for i in range(len(history_rows) - order):
        current_state = history_rows[i]
        future_state = history_rows[i + order]
        for cb in current_state:
            if cb in pool:
                for fb in future_state:
                    if fb in pool:
                        transition_matrix[cb][fb] += 1

    if not history_rows:
        return sorted(rng.sample(pool, count))

    latest_state = [b for b in history_rows[-1] if b in pool]
    next_probs = Counter()
    for lb in latest_state:
        for nb, freq in transition_matrix[lb].items():
            next_probs[nb] += freq

    candidates = [x[0] for x in next_probs.most_common()]
    top_k_pool = candidates[: count + 5]
    if len(top_k_pool) < count:
        missing = [x for x in pool if x not in top_k_pool]
        top_k_pool.extend(rng.sample(missing, min(count - len(top_k_pool), len(missing))))

    return sorted(rng.sample(top_k_pool, count))


def get_advanced_predictions(df_view, choice, click_count):
    sets = []
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    rng = random.Random(int(time.time()) + click_count)

    safe_df = df_view.apply(pd.to_numeric, errors="coerce").fillna(-1).astype(int)
    r_history = safe_df.iloc[:, 1 : 1 + count_r].values.tolist()
    r_history.reverse()

    b_history = []
    if count_b > 0:
        b_history = safe_df.iloc[:, 1 + count_r : 1 + count_r + count_b].values.tolist()
        b_history.reverse()

    for idx in range(3):
        r_res = real_markov_core(r_history, pool_r, count_r, rng, order=1)
        b_res = real_markov_core(b_history, pool_b, count_b, rng, order=1) if count_b > 0 else []
        sets.append(
            {
                "name": f"马尔科夫链 {idx + 1}",
                "desc": f"状态转移建模 | AC 值 {calculate_ac_value(r_res)}",
                "red": r_res,
                "blue": b_res,
                "text": render_number_text(r_res, b_res, choice),
                "tone": "primary",
            }
        )

    for idx in range(3):
        actual_order = 12 if len(r_history) > 15 else 1
        r_res = real_markov_core(r_history, pool_r, count_r, rng, order=actual_order)
        b_res = real_markov_core(b_history, pool_b, count_b, rng, order=actual_order) if count_b > 0 else []
        sets.append(
            {
                "name": f"AC12 高阶 {idx + 1}",
                "desc": f"高阶跨度 {actual_order} 期 | 样本 {len(r_history)}",
                "red": r_res,
                "blue": b_res,
                "text": render_number_text(r_res, b_res, choice),
                "tone": "accent",
            }
        )

    return sets


def parse_red_blue_from_text(text, is_dlt=True):
    red_balls = []
    blue_balls = []
    text_clean = text.replace("：", ":").replace("，", ",").replace("；", ";").replace("—", "-")
    lines = re.split(r"[\n\r;,\t]", text_clean)

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if any(sep in line for sep in ["+", "-", "|", "蓝", "后"]):
            parts = re.split(r"[\+\-\|蓝后]", line, maxsplit=1)
            r_part = re.findall(r"\b(0?[1-9]|[1-2][0-9]|3[0-5])\b", parts[0])
            if len(parts) > 1:
                if is_dlt:
                    b_part = re.findall(r"\b(0?[1-9]|1[0-2])\b", parts[1])
                else:
                    b_part = re.findall(r"\b(0?[1-9]|1[0-6])\b", parts[1])
            else:
                b_part = []

            red_balls.extend([int(x) for x in r_part if (is_dlt and int(x) <= 35) or (not is_dlt and int(x) <= 33)])
            blue_balls.extend([int(x) for x in b_part])
        else:
            all_nums = re.findall(r"\b([0-3]?[0-9])\b", line)
            all_nums = [int(x) for x in all_nums if 1 <= int(x) <= 35]
            if not all_nums:
                continue

            if is_dlt and len(all_nums) >= 7:
                if all_nums[-1] <= 12 and all_nums[-2] <= 12:
                    red_balls.extend([x for x in all_nums[:-2] if x <= 35])
                    blue_balls.extend(all_nums[-2:])
                else:
                    red_balls.extend([x for x in all_nums if x <= 35])
            elif (not is_dlt) and len(all_nums) >= 7:
                if all_nums[-1] <= 16:
                    red_balls.extend([x for x in all_nums[:-1] if x <= 33])
                    blue_balls.extend([all_nums[-1]])
                else:
                    red_balls.extend([x for x in all_nums if x <= 33])
            else:
                if is_dlt:
                    red_balls.extend([x for x in all_nums if x <= 35])
                else:
                    red_balls.extend([x for x in all_nums if x <= 33])

    if not blue_balls:
        all_matches = re.findall(r"\b(0?[1-9]|[1-2][0-9]|3[0-5])\b", text)
        red_balls = [int(x) for x in all_matches if (is_dlt and int(x) <= 35) or (not is_dlt and int(x) <= 33)]

    return red_balls, blue_balls


def calculate_frequencies(df, is_dlt=True):
    if is_dlt:
        front_nums = df[["前1", "前2", "前3", "前4", "前5"]].values.flatten()
        back_nums = df[["后1", "后2"]].values.flatten()
        front_max, back_max = 35, 12
    else:
        front_nums = df[["前1", "前2", "前3", "前4", "前5", "前6"]].values.flatten()
        back_nums = df[["后1"]].values.flatten()
        front_max, back_max = 33, 16
    front_counts, back_counts = Counter(front_nums), Counter(back_nums)
    for i in range(1, front_max + 1):
        front_counts.setdefault(i, 0)
    for i in range(1, back_max + 1):
        back_counts.setdefault(i, 0)
    return front_counts, back_counts


def calculate_bets(n, r):
    return math.comb(n, r) if r <= n and r >= 0 else 0


def scan_advanced_patterns(df_slice, df_full, is_dlt):
    front_cols = ["前1", "前2", "前3", "前4", "前5"] if is_dlt else ["前1", "前2", "前3", "前4", "前5", "前6"]
    repeat_count = 0
    consecutive_count = 0
    for _, row in df_slice.iterrows():
        nums = sorted([row[c] for c in front_cols])
        if any(nums[i + 1] - nums[i] == 1 for i in range(len(nums) - 1)):
            consecutive_count += 1
        full_idx = df_full.index[df_full["期号"] == row["期号"]].tolist()
        if full_idx and full_idx[0] + 1 < len(df_full):
            prev_nums = set([df_full.iloc[full_idx[0] + 1][c] for c in front_cols])
            if len(set(nums).intersection(prev_nums)) > 0:
                repeat_count += 1
    return repeat_count, consecutive_count


def run_tactical_manual_analysis(raw_text, is_dlt, history_limit, recent_red_pool=None, recent_blue_pool=None, history_tongqi_pool=None, weekday_pool=None, weekday_blue_pool=None):
    red_nums, blue_nums = parse_red_blue_from_text(raw_text, is_dlt=is_dlt)
    if not red_nums:
        return {"ok": False, "message": "未检测到有效号码，请检查输入格式。"}

    counts_red = Counter(red_nums)
    counts_blue = Counter(blue_nums)
    sorted_red = counts_red.most_common()
    hot_nums = [x[0] for x in sorted_red[:6]]

    max_n = 35 if is_dlt else 33
    all_possible = set(range(1, max_n + 1))
    appeared_nums = set(red_nums)
    cold_nums = list(all_possible - appeared_nums)
    low_freq_nums = [x[0] for x in sorted_red if x[1] == 1]
    potential_nums = sorted(list(set(cold_nums + low_freq_nums)))

    offset_recommend = set()
    for h in hot_nums:
        for offset in [-2, -1, 1, 2]:
            target = h + offset
            if 1 <= target <= max_n and target not in hot_nums:
                offset_recommend.add(target)
    offset_recommend = sorted(list(offset_recommend))

    max_b = 12 if is_dlt else 16
    req_r = 5 if is_dlt else 6
    req_b = 2 if is_dlt else 1
    recent_red_pool = recent_red_pool or list(range(1, max_n + 1))
    history_tongqi_pool = history_tongqi_pool or list(range(1, max_n + 1))
    weekday_pool = weekday_pool or list(range(1, max_n + 1))
    recent_blue_pool = recent_blue_pool or list(range(1, max_b + 1))
    weekday_blue_pool = weekday_blue_pool or list(range(1, max_b + 1))

    red_scores = {}
    for num in range(1, max_n + 1):
        score = 0
        if num in recent_red_pool:
            score += 3
        if num in history_tongqi_pool:
            score += 2
        if num in weekday_pool:
            score += 2
        if num in hot_nums:
            score = 0
        red_scores[num] = score

    blue_scores = {}
    for num in range(1, max_b + 1):
        score = 0
        if num in recent_blue_pool:
            score += 3
        if num in weekday_blue_pool:
            score += 2
        score = score - (counts_blue.get(num, 0) * 2)
        blue_scores[num] = score

    sorted_math_reds = [num for num, score in sorted(red_scores.items(), key=lambda x: (x[1], -x[0]), reverse=True) if score > 0]
    sorted_math_blues = [num for num, score in sorted(blue_scores.items(), key=lambda x: (x[1], -x[0]), reverse=True)]
    if len(sorted_math_reds) < req_r + 2:
        sorted_math_reds = [x for x in range(1, max_n + 1) if x not in hot_nums]
    if len(sorted_math_blues) < req_b + 2:
        sorted_math_blues = [x for x in range(1, max_b + 1)]

    final_math_reds = sorted(sorted_math_reds[:req_r])
    final_math_blues = sorted(sorted_math_blues[:req_b])
    fushi_math_reds = sorted(sorted_math_reds[: req_r + 2])
    fushi_blue_count = req_b + 2 if is_dlt else req_b + 1
    fushi_math_blues = sorted(sorted_math_blues[:fushi_blue_count])
    zhusu = math.comb(len(fushi_math_reds), req_r) * math.comb(len(fushi_math_blues), req_b)

    dan_source = potential_nums if potential_nums else offset_recommend
    if is_dlt:
        dan_primary = (dan_source + [1, 2, 3, 4])[:4]
        dan_secondary = (dan_source + [1, 2, 3])[:3]
    else:
        dan_primary = (dan_source + [1, 2, 3, 4, 5])[:5]
        dan_secondary = []

    return {
        "ok": True,
        "red_nums": red_nums,
        "blue_nums": blue_nums,
        "counts_red": counts_red,
        "counts_blue": counts_blue,
        "hot_nums": hot_nums,
        "potential_nums": potential_nums,
        "offset_recommend": offset_recommend,
        "final_math_reds": final_math_reds,
        "final_math_blues": final_math_blues,
        "fushi_math_reds": fushi_math_reds,
        "fushi_math_blues": fushi_math_blues,
        "zhusu": zhusu,
        "dan_primary": dan_primary,
        "dan_secondary": dan_secondary,
        "history_limit": history_limit,
        "is_dlt": is_dlt,
    }

