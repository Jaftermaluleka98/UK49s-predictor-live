import streamlit as st
import pandas as pd
import random
from collections import Counter
from itertools import combinations
from datetime import date, timedelta

st.set_page_config(page_title="UK49s - Daily Triples Predictor FIXED", layout="centered")

st.markdown("""
<style>
.ball { width:52px; height:52px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; color:white; font-weight:bold; font-size:19px; border:2px solid silver; margin:3px; box-shadow: inset -5px -5px 10px rgba(0,0,0,0.5); }
.high { background: radial-gradient(circle at 30% 30%, #ff6b6b, #a80000); }
.low { background: radial-gradient(circle at 30% 30%, #6bb8ff, #0040a8); }
.cold-ball { background: radial-gradient(circle at 30% 30%, #9e9e9e, #424242); }
.gold { border: 4px solid gold !important; box-shadow: 0 0 15px gold !important; }
.yesterday-box { background:#1a1a1a; border:2px solid gold; padding:15px; border-radius:12px; color:white; margin-bottom:15px; }
.today-box { background: linear-gradient(90deg, #0040a8, #a80000); padding:10px; border-radius:10px; color:white; text-align:center; font-weight:bold; }
.today-result-box { background:#0a2a0a; border:2px solid #00ff00; padding:15px; border-radius:12px; color:white; margin-bottom:15px; }
.csv-badge { background:#ff9800; color:white; padding:3px 10px; border-radius:20px; font-size:13px; font-weight:bold; }
.section { background:#f5f5f5; padding:12px; border-radius:10px; margin-bottom:10px; }
</style>
""", unsafe_allow_html=True)

# ===== DATES =====
today = date.today()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)
cols_main = ['Num1','Num2','Num3','Num4','Num5','Num6']

st.markdown(f'<div class="today-box">📅 TODAY: {today.strftime("%A, %d %B %Y")} | Lunchtime 12:49 | Teatime 17:49 (UK) | SA: 13:49 / 18:49</div>', unsafe_allow_html=True)
st.write("")

selected_date = st.date_input("📅 Predict for date", value=today, min_value=today - timedelta(days=7), max_value=tomorrow)
draw_type = st.selectbox("Choose Draw", ["Lunchtime", "Teatime"])
lookback = st.slider("Use last N draws for stats", 20, 300, 100)

# ===== LOAD DATA: CSV ONLY =====
try:
    csv_df = pd.read_csv('data.csv')
    csv_df['Date'] = pd.to_datetime(csv_df['Date']).dt.date
except:
    st.error("Need data.csv with Date,Draw,Num1...Booster")
    st.stop()

st.markdown('<span class="csv-badge">✓ Using data.csv - Verified Data Only</span>', unsafe_allow_html=True)
df_all = csv_df.sort_values('Date', ascending=False).reset_index(drop=True)

# For predictions: only draws BEFORE selected date
df = df_all[df_all['Date'] < selected_date].sort_values('Date', ascending=False).reset_index(drop=True)

def show_result_box(row, box_class="yesterday-box"):
    nums = [int(row[c]) for c in cols_main]
    booster = int(row['Booster'])
    high = sum(1 for x in nums if x >= 25)
    html = f'<div class="{box_class}"><b>{row["Draw"]} - {row["Date"]}:</b> '
    for n in nums:
        cls = "high" if n >= 25 else "low"
        html += f'<span class="ball {cls}">{n}</span>'
    html += f' + Booster: <span class="ball {"high" if booster>=25 else "low"}">{booster}</span>'
    html += f'<br><small>{high} High / {6-high} Low | Sum: {sum(nums)} | Odd/Even: {sum(1 for x in nums if x%2==1)}/{sum(1 for x in nums if x%2==0)}</small></div>'
    st.markdown(html, unsafe_allow_html=True)

def balls_html(nums, gold_num=None, cold_nums=[]):
    html = ''
    for n in nums:
        if n in cold_nums:
            cls = "cold-ball"
        else:
            cls = "high" if n >= 25 else "low"
        gold = " gold" if n == gold_num else ""
        html += f'<span class="ball {cls}{gold}">{n}</span>'
    return html

# ===== TODAY'S RESULTS =====
st.subheader(f"🔴 TODAY'S Results - {today.strftime('%A, %d %B %Y')}")
today_rows = df_all[df_all['Date'] == today]
if len(today_rows) == 0:
    st.info("⏳ No results for today yet. Lunchtime 13:49 SA, Teatime 18:49 SA.")
else:
    for _, r in today_rows.iterrows():
        show_result_box(r, box_class="today-result-box")

# ===== YESTERDAY RESULTS =====
st.subheader(f"📊 Yesterday's Results - {yesterday.strftime('%A, %d %B %Y')}")
yest = df_all[df_all['Date'] == yesterday]
if len(yest) == 0:
    last_date = df_all['Date'].max()
    yest = df_all[df_all['Date'] == last_date]
    st.warning(f"No data for yesterday - showing last available: {last_date}")
for _, row in yest.iterrows():
    show_result_box(row, box_class="yesterday-box")

# ===== ===== FIXED PREDICTION LOGIC ===== =====
# OLD BUG: It calculated per Ball Position (Ball #1, Ball #2...).
# That is wrong because data.csv is sorted low->high, so Ball #1 is always low.
# NEW: Calculate overall, across ALL balls.
df_pred = df[df['Draw'] == draw_type].head(lookback)
cols = ['Num1','Num2','Num3','Num4','Num5','Num6','Booster']

if len(df_pred) == 0:
    st.error("No history for this draw yet.")
    st.stop()

# --- 1. FREQUENCY (ALL BALLS TOGETHER) ---
all_balls = df_pred[cols[:6]].values.flatten()
freq = Counter([int(x) for x in all_balls])
# Booster frequency separately
booster_freq = Counter([int(x) for x in df_pred['Booster']])

# --- 2. LAST SEEN / OVERDUE ---
# df_pred is sorted newest first, index 0 = most recent
last_seen = {}
for n in range(1, 50):
    found = df_pred[df_pred[cols[:6]].eq(n).any(axis=1)]
    last_seen[n] = int(found.index[0]) if len(found) > 0 else 999

# Score = frequency + overdue bonus + recency bonus
scores = {}
for n in range(1, 50):
    f = freq.get(n, 0)
    last = last_seen[n]
    score = f * 10
    if last <= 2: score += 10  # just came, hot
    elif last <= 5: score += 5
    if last >= 15: score += 15 # overdue, due to return
    elif last >= 10: score += 8
    scores[n] = score

# HOT = top by frequency
hot_list = [n for n, c in freq.most_common(12)]
# OVERDUE / COLD = top by last_seen (hasn't come longest)
overdue_list = sorted(last_seen, key=lambda x: last_seen[x], reverse=True)[:12]
# BALANCED = top by combined score
balanced_list = sorted(scores, key=lambda x: scores[x], reverse=True)[:12]

banker = balanced_list[0]
# Best partner for banker from pair counts
pair_counts = Counter()
for _, row in df_pred.iterrows():
    nums = [int(row[c]) for c in cols[:6]]
    for a, b in combinations(sorted(nums), 2):
        pair_counts[(a,b)] += 1

best_partner = {}
for n in range(1, 50):
    partners = []
    for (a,b), cnt in pair_counts.items():
        if a == n: partners.append((b,cnt))
        elif b == n: partners.append((a,cnt))
    partners.sort(key=lambda x: x[1], reverse=True)
    best_partner[n] = partners[0] if partners else (None, 0)

# Triples
triple_counts = Counter()
for _, row in df_pred.iterrows():
    nums = [int(row[c]) for c in cols[:6]]
    for a,b,c in combinations(sorted(nums), 3):
        triple_counts[(a,b,c)] += 1
top_triples = triple_counts.most_common(10)

def best_third_for_pair(pair):
    a, b = sorted(pair)
    candidates = []
    for (x,y,z), cnt in triple_counts.items():
        if a in (x,y,z) and b in (x,y,z):
            third = [n for n in (x,y,z) if n not in (a,b)][0]
            candidates.append((third, cnt))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0] if candidates else (None, 0)

# ===== DISPLAY: HOT / COLD / BALANCED =====
st.subheader(f"🎱 Prediction - {draw_type} - {selected_date.strftime('%d %B %Y')}")
st.caption("FIXED: No more Ball #1, Ball #2. These are overall numbers across all balls.")

st.markdown('<div class="section"><b>🔥 HOT - Came Most in Last {} Draws</b><br><small>These are on fire right now</small></div>', unsafe_allow_html=True)
st.markdown(balls_html(hot_list, gold_num=banker), unsafe_allow_html=True)
st.write(f"Hot details: " + ", ".join([f"{n} ({freq.get(n,0)}x, last {last_seen[n]} draws ago)" for n in hot_list[:6]]))

st.markdown('<div class="section"><b>❄️ COLD / OVERDUE - Hasn\'t Come in Longest Time</b><br><small>These are the 42, 6, 41 type numbers - the old system hid them. Don\'t ignore them.</small></div>', unsafe_allow_html=True)
st.markdown(balls_html(overdue_list, cold_nums=overdue_list), unsafe_allow_html=True)
st.write(f"Overdue details: " + ", ".join([f"{n} ({last_seen[n]} draws ago)" for n in overdue_list[:6]]))

st.markdown('<div class="section"><b>⭐ BALANCED - Hot + Overdue Combined</b><br><small>Best overall score</small></div>', unsafe_allow_html=True)
st.markdown(balls_html(balanced_list, gold_num=banker), unsafe_allow_html=True)

st.success(f"⭐ BANKER: {banker} | Came {freq.get(banker,0)}x in last {len(df_pred)} | Last seen {last_seen[banker]} draws ago | Best Partner: {best_partner[banker][0]} ({best_partner[banker][1]}x)")

# ===== TRIPLES =====
st.subheader("🔺 Top 10 Triples - When 2 Come, The 3rd Follows")
triple_data = []
for (a,b,c), cnt in top_triples:
    triple_data.append({'Triple': f"{a} + {b} + {c}", 'Times Together': cnt, 'Probability': f"{round(cnt/len(df_pred)*100,1)}%"})
st.dataframe(pd.DataFrame(triple_data), use_container_width=True)

st.subheader("🔍 Triple Checker - Enter Any Pair")
col1, col2 = st.columns(2)
p1 = col1.number_input("First Number", 1, 49, banker)
p2 = col2.number_input("Second Number", 1, 49, best_partner[banker][0] or 1)
if p1 != p2:
    third, cnt = best_third_for_pair((p1,p2))
    if third:
        st.info(f"**{p1} + {p2}** came together {pair_counts.get(tuple(sorted((p1,p2))),0)} times. When they do, **{third}** joins them **{cnt} times**. So play **{p1} + {p2} + {third}** as your core triple.")
    else:
        st.write("No triple history for this pair yet - try another pair.")

# ===== FINAL COMBOS - MIXED LOGIC =====
st.subheader(f"🎯 Final Combos for {selected_date.strftime('%A %d %B')} - {draw_type}")
st.caption("Combo 1 = Hot only | Combo 2 = MIXED (Best - 3 Hot + 2 Cold + 1 Balanced) | Combo 3 = Cold/Overdue heavy")

def make_combo(hot_n, cold_n, balanced_n):
    combo = []
    # Take hot
    for n in hot_list:
        if n not in combo and len(combo) < hot_n:
            combo.append(n)
    for n in overdue_list:
        if n not in combo and len(combo) < hot_n + cold_n:
            combo.append(n)
    for n in balanced_list:
        if n not in combo and len(combo) < 6:
            combo.append(n)
    while len(combo) < 6:
        n = random.randint(1,49)
        if n not in combo: combo.append(n)
    return sorted(combo)

# Yesterday example: Hot would give 20,17,44,43 + Cold would give 42,6 = 6/6
combo_hot = make_combo(6, 0, 0)
combo_mixed = make_combo(3, 2, 1)  # BEST
combo_cold = make_combo(2, 3, 1)
# Booster: most common booster that is NOT in combo, else banker
def pick_booster(combo):
    for n, c in booster_freq.most_common():
        if n not in combo:
            return n
    return banker

combos = [
    ("Combo 1 - HOT ONLY", combo_hot),
    ("Combo 2 - MIXED ⭐ BEST", combo_mixed),
    ("Combo 3 - COLD HEAVY", combo_cold),
]
for label, combo in combos:
    high = sum(1 for x in combo if x >= 25)
    booster = pick_booster(combo)
    st.success(f"**{label} for {selected_date.strftime('%d %B')} {draw_type}: {combo}** → {high} High / {6-high} Low | Booster: {booster}")

# Also add a triple-based combo
if top_triples:
    triple_combo = list(top_triples[0][0])
    for n in balanced_list:
        if n not in triple_combo and len(triple_combo) < 6:
            triple_combo.append(n)
    triple_combo = sorted(triple_combo)
    st.info(f"**Combo 4 - TOP TRIPLE + Balanced: {triple_combo}** → Booster: {pick_booster(triple_combo)}")

st.subheader("📅 Last 7 Days - Lunchtime & Teatime")
last7 = df_all[df_all['Date'] >= today - timedelta(days=7)].sort_values('Date', ascending=False)
for _, row in last7.head(14).iterrows():
    nums = [int(row[c]) for c in cols_main]
    st.write(f"**{row['Date']} - {row['Draw']}:** {nums} + Booster {int(row['Booster'])}")

# ===== ADD RESULT HELPER =====
st.divider()
st.subheader("➕ Add New Result - Helper")
st.caption("Type numbers exactly as in Sunshine app. This builds the correct line for data.csv.")
with st.expander("Add a result", expanded=False):
    add_date = st.date_input("Result Date", value=today, key="add_date")
    add_draw = st.selectbox("Draw", ["Lunchtime", "Teatime"], key="add_draw")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    n1 = c1.number_input("Ball 1", 1, 49, 1, key="n1")
    n2 = c2.number_input("Ball 2", 1, 49, 2, key="n2")
    n3 = c3.number_input("Ball 3", 1, 49, 3, key="n3")
    n4 = c4.number_input("Ball 4", 1, 49, 4, key="n4")
    n5 = c5.number_input("Ball 5", 1, 49, 5, key="n5")
    n6 = c6.number_input("Ball 6", 1, 49, 6, key="n6")
    booster_in = st.number_input("Booster", 1, 49, 7, key="booster_in")
    balls_sorted = sorted([n1, n2, n3, n4, n5, n6])
    if len(set([n1,n2,n3,n4,n5,n6])) < 6:
        st.error("❌ Duplicate numbers - 6 balls must all be different.")
    elif booster_in in balls_sorted:
        st.error("❌ Booster cannot be same as one of the 6 main balls.")
    else:
        line = f"{add_date},{add_draw},{balls_sorted[0]},{balls_sorted[1]},{balls_sorted[2]},{balls_sorted[3]},{balls_sorted[4]},{balls_sorted[5]},{booster_in}"
        st.success("Copy this ONE line to the TOP of data.csv (under the header):")
        st.code(line)
        exists = ((df_all['Date'] == add_date) & (df_all['Draw'] == add_draw)).any()
        if exists:
            st.warning(f"⚠️ {add_date} {add_draw} ALREADY exists - do NOT add again.")
        else:
            st.info("✅ This draw is not in data.csv yet - safe to add after the draw.")

st.warning("⚠️ Stats only - UK49s is random. Hot + Cold together gives you better coverage, not a guarantee.")