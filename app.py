import streamlit as st
import pandas as pd
import random
from collections import Counter
from itertools import combinations
from datetime import date, timedelta

st.set_page_config(page_title="UK49s - Daily Triples Predictor", layout="centered")

st.markdown("""
<style>
.ball { width:52px; height:52px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; color:white; font-weight:bold; font-size:19px; border:2px solid silver; margin:3px; box-shadow: inset -5px -5px 10px rgba(0,0,0,0.5); }
.high { background: radial-gradient(circle at 30% 30%, #ff6b6b, #a80000); }
.low { background: radial-gradient(circle at 30% 30%, #6bb8ff, #0040a8); }
.ball-label { color:red; font-weight:bold; font-size:18px; width:70px; display:inline-block; }
.ball-label-blue { color:blue; font-weight:bold; font-size:18px; width:70px; display:inline-block; }
.header-bar { display:flex; background:linear-gradient(90deg, red, purple, blue); color:white; font-weight:bold; padding:8px; text-align:center; }
.gold { border: 4px solid gold !important; box-shadow: 0 0 15px gold !important; }
.yesterday-box { background:#1a1a1a; border:2px solid gold; padding:15px; border-radius:12px; color:white; margin-bottom:15px; }
.today-box { background: linear-gradient(90deg, #0040a8, #a80000); padding:10px; border-radius:10px; color:white; text-align:center; font-weight:bold; }
.today-result-box { background:#0a2a0a; border:2px solid #00ff00; padding:15px; border-radius:12px; color:white; margin-bottom:15px; }
.csv-badge { background:#ff9800; color:white; padding:3px 10px; border-radius:20px; font-size:13px; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

# ===== DATES =====
today = date.today()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)
cols_main = ['Num1','Num2','Num3','Num4','Num5','Num6']

st.markdown(f'<div class="today-box">📅 TODAY: {today.strftime("%A, %d %B %Y")} | Lunchtime 12:49 | Teatime 17:49 (UK Time) | SA Time: 13:49 / 18:49</div>', unsafe_allow_html=True)
st.write("")

selected_date = st.date_input("📅 Predict for date", value=today, min_value=today - timedelta(days=7), max_value=tomorrow)
st.caption(f"You are predicting for: {selected_date.strftime('%A, %d %B %Y')}")
draw_type = st.selectbox("Choose Draw", ["Lunchtime", "Teatime"])
lookback = st.slider("Use last N draws for stats", 20, 300, 100)

# ===== LOAD DATA: CSV ONLY - NO LIVE SCRAPER =====
# LIVE was disabled because it picked up times like 13:49 as balls
# and overwrote correct CSV data with wrong numbers.
try:
    csv_df = pd.read_csv('data.csv')
    csv_df['Date'] = pd.to_datetime(csv_df['Date']).dt.date
except:
    st.error("Need data.csv with Date,Draw,Num1...Booster")
    st.stop()

st.markdown('<span class="csv-badge">✓ Using data.csv - Verified Data Only</span> <small>No live scraper - CSV is the truth</small>', unsafe_allow_html=True)
df_all = csv_df.sort_values('Date', ascending=False).reset_index(drop=True)
data_source = "CSV"

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

# ===== TODAY'S RESULTS =====
st.subheader(f"🔴 TODAY'S Results - {today.strftime('%A, %d %B %Y')} - Source: {data_source}")
today_rows = df_all[df_all['Date'] == today]

if len(today_rows) == 0:
    st.info("⏳ No results for today yet. Lunchtime comes at 13:49 SA time, Teatime at 18:49 SA time. Prediction grid below is for the next draw.")
else:
    lunch_today = today_rows[today_rows['Draw'] == 'Lunchtime']
    if len(lunch_today) > 0:
        show_result_box(lunch_today.iloc[0], box_class="today-result-box")
    else:
        st.info("⏳ Lunchtime today - still to come (13:49 SA / 12:49 UK)")
    tea_today = today_rows[today_rows['Draw'] == 'Teatime']
    if len(tea_today) > 0:
        show_result_box(tea_today.iloc[0], box_class="today-result-box")
    else:
        st.info("⏳ Teatime today - still to come (18:49 SA / 17:49 UK)")

# ===== YESTERDAY RESULTS =====
st.subheader(f"📊 Yesterday's Results - {yesterday.strftime('%A, %d %B %Y')}")
yest = df_all[df_all['Date'] == yesterday]
if len(yest) == 0:
    last_date = df_all['Date'].max()
    yest = df_all[df_all['Date'] == last_date]
    st.warning(f"No data for yesterday yet - showing last available: {last_date.strftime('%A, %d %B %Y')}")
for _, row in yest.iterrows():
    show_result_box(row, box_class="yesterday-box")

st.caption("Check: Did any of yesterday's numbers appear in today's Hot list below? If yes, the system is tracking well.")

# ===== MAIN DATA FOR PREDICTION =====
df_pred = df[df['Draw'] == draw_type].head(lookback)
cols = ['Num1','Num2','Num3','Num4','Num5','Num6','Booster']
ball_names = ['Ball #1','Ball #2','Ball #3','Ball #4','Ball #5','Ball #6','Ball #7']

def calculate_scores(ball_idx):
    col = cols[ball_idx]
    freq = df_pred[col].value_counts()
    scores = {}
    for n in range(1, 50):
        score = freq.get(n, 0) * 8
        found = df_pred[df_pred[cols].eq(n).any(axis=1)]
        last = found.index[0] if len(found) > 0 else lookback
        if last <= 5: score += 15
        elif last <= 10: score += 8
        if last >= 20: score += 20
        elif last >= 15: score += 10
        if ball_idx <= 1 and n <= 24: score += 12
        if ball_idx >= 5 and n >= 25: score += 12
        prob = round(freq.get(n, 0) / max(len(df_pred),1) * 100, 1)
        scores[n] = (score, prob)
    return sorted(scores.items(), key=lambda x: x[1][0], reverse=True)[:5]

predictions = {ball_names[i]: calculate_scores(i) for i in range(7)}

pair_counts = Counter()
for _, row in df_pred.iterrows():
    nums = [row[c] for c in cols[:6]]
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

triple_counts = Counter()
for _, row in df_pred.iterrows():
    nums = [row[c] for c in cols[:6]]
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

st.subheader(f"🎱 Prediction Grid - {draw_type} - {selected_date.strftime('%d %B %Y')}")
st.markdown("""
<div class="header-bar">
  <div style="width:80px; background:#ddd; color:black;">Close</div>
  <div style="flex:1;">High</div>
  <div style="flex:1;">Probability</div>
  <div style="flex:1;">Low</div>
</div>
""", unsafe_allow_html=True)

all_scores = Counter()
for b in ball_names:
    for num, (score, prob) in predictions[b]:
        all_scores[num] += score
banker = all_scores.most_common(1)[0][0]

for idx, ball in enumerate(ball_names):
    label = "ball-label" if idx % 2 == 0 else "ball-label-blue"
    html = f'<div><span class="{label}">{ball}</span>'
    for num, (score, prob) in predictions[ball]:
        cls = "high" if num >= 25 else "low"
        gold = " gold" if num == banker else ""
        html += f'<span class="ball {cls}{gold}" title="Score {score} | Prob {prob}%">{num}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

st.success(f"⭐ BANKER: {banker} | Best Partner: {best_partner[banker][0]} ({best_partner[banker][1]}x)")

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

st.subheader(f"🎯 Final Combos for {selected_date.strftime('%A %d %B')} - {draw_type}")
def build_combo_from_triple(triple):
    combo = list(triple)
    if banker not in combo and len(combo) < 6:
        combo.append(banker)
    for b in ball_names[:6]:
        for num, _ in predictions[b]:
            if num not in combo and len(combo) < 6:
                combo.append(num)
                break
    while len(combo) < 6:
        n = random.randint(1,49)
        if n not in combo: combo.append(n)
    return sorted(combo)

combo1 = build_combo_from_triple(top_triples[0][0] if top_triples else (banker,1,2))
combo2 = build_combo_from_triple(top_triples[1][0] if len(top_triples)>1 else (banker,1,2))
combo3 = build_combo_from_triple(top_triples[2][0] if len(top_triples)>2 else (banker,1,2))
for i, combo in enumerate([combo1, combo2, combo3], 1):
    high = sum(1 for x in combo if x >= 25)
    st.success(f"**Combo {i} for {selected_date.strftime('%d %B')} {draw_type}: {combo}** → {high} High / {6-high} Low | Booster: {banker}")

st.subheader("📅 Last 7 Days - Lunchtime & Teatime")
last7 = df_all[df_all['Date'] >= today - timedelta(days=7)].sort_values('Date', ascending=False)
for _, row in last7.head(14).iterrows():
    nums = [int(row[c]) for c in cols_main]
    st.write(f"**{row['Date']} - {row['Draw']}:** {nums} + Booster {int(row['Booster'])}")

# ===== ADD RESULT HELPER - PREVENTS TYPING ERRORS =====
st.divider()
st.subheader("➕ Add New Result - Helper")
st.caption("Type the numbers exactly as you see them on the 49's app. This will build the correct line for data.csv. Do NOT add before the draw happens.")
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
    # Check for duplicates / booster clash
    if len(set([n1,n2,n3,n4,n5,n6])) < 6:
        st.error("❌ You have duplicate numbers - check again, 6 balls must all be different.")
    elif booster_in in balls_sorted:
        st.error("❌ Booster cannot be same as one of the 6 main balls.")
    else:
        line = f"{add_date},{add_draw},{balls_sorted[0]},{balls_sorted[1]},{balls_sorted[2]},{balls_sorted[3]},{balls_sorted[4]},{balls_sorted[5]},{booster_in}"
        st.success("Copy this ONE line to the TOP of data.csv (under the header):")
        st.code(line)
        # Check if already exists
        exists = ((df_all['Date'] == add_date) & (df_all['Draw'] == add_draw)).any()
        if exists:
            st.warning(f"⚠️ {add_date} {add_draw} ALREADY exists in data.csv - do NOT add again, you will duplicate it.")
        else:
            st.info("✅ This draw is not in data.csv yet - safe to add after the draw.")

st.warning("⚠️ Stats only - UK49s is random.")