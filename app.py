import streamlit as st
import pandas as pd
import random
from collections import Counter
from itertools import combinations
from datetime import date, timedelta, datetime

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
</style>
""", unsafe_allow_html=True)

# ===== DATES - EVERYDAY =====
today = date.today()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)

st.markdown(f'<div class="today-box">📅 TODAY: {today.strftime("%A, %d %B %Y")} | Lunchtime 12:49 | Teatime 17:49 (UK Time) | SA Time: 13:49 / 18:49</div>', unsafe_allow_html=True)
st.write("")

# Date selector - pick any day to predict for
selected_date = st.date_input("📅 Predict for date", value=today, min_value=today - timedelta(days=7), max_value=tomorrow)
st.caption(f"You are predicting for: {selected_date.strftime('%A, %d %B %Y')}")

draw_type = st.selectbox("Choose Draw", ["Lunchtime", "Teatime"])
lookback = st.slider("Use last N draws for stats", 20, 300, 100)
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date, timedelta

@st.cache_data(ttl=3600)  # refresh every 1 hour
def get_live_data():
    try:
        # 49s official results page - Lunchtime & Teatime
        url = "https://www.49s.co.uk/results"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = []
        # The site lists results in tables - we parse them
        # Fallback if site blocks us: use backup API
        return None
    except:
        return None

def load_data():
    # Try live first
    live = get_live_data()
    if live is not None:
        return live
    # Fallback to CSV
    df = pd.read_csv('data.csv')
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    return df

try:
    df = pd.read_csv('data.csv')
    # Make sure Date is date type
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    # Only use draws BEFORE selected date (no future leaking)
    df = df[df['Date'] < selected_date].sort_values('Date', ascending=False).reset_index(drop=True)
    df_all = pd.read_csv('data.csv')
    df_all['Date'] = pd.to_datetime(df_all['Date']).dt.date
except:
    st.error("Need data.csv with Date,Draw,Num1...Booster")
    st.stop()

# ===== YESTERDAY RESULTS ON TOP - BOTH DRAWS =====
st.subheader(f"📊 Yesterday's Results - {yesterday.strftime('%A, %d %B %Y')}")
yest = df_all[df_all['Date'] == yesterday]

if len(yest) == 0:
    # Fallback: show most recent date in file
    last_date = df_all['Date'].max()
    yest = df_all[df_all['Date'] == last_date]
    st.warning(f"No data for yesterday yet - showing last available: {last_date.strftime('%A, %d %B %Y')}")

cols_main = ['Num1','Num2','Num3','Num4','Num5','Num6']
for _, row in yest.iterrows():
    nums = [int(row[c]) for c in cols_main]
    booster = int(row['Booster'])
    high = sum(1 for x in nums if x >= 25)
    html = f'<div class="yesterday-box"><b>{row["Draw"]} - {row["Date"]}:</b> '
    for n in nums:
        cls = "high" if n >= 25 else "low"
        html += f'<span class="ball {cls}">{n}</span>'
    html += f' + Booster: <span class="ball {"high" if booster>=25 else "low"}">{booster}</span>'
    html += f'<br><small>{high} High / {6-high} Low | Sum: {sum(nums)} | Odd/Even: {sum(1 for x in nums if x%2==1)}/{sum(1 for x in nums if x%2==0)}</small></div>'
    st.markdown(html, unsafe_allow_html=True)

# Did yesterday's numbers hit our hot numbers?
st.caption("Check: Did any of yesterday's numbers appear in today's Hot list below? If yes, the system is tracking well.")

# ===== MAIN DATA FOR PREDICTION =====
df_pred = df[df['Draw'] == draw_type].head(lookback)
cols = ['Num1','Num2','Num3','Num4','Num5','Num6','Booster']
ball_names = ['Ball #1','Ball #2','Ball #3','Ball #4','Ball #5','Ball #6','Ball #7']

# ===== 1. SCORES PER BALL =====
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

# ===== 2. PAIRS =====
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

# ===== 3. NEW: TRIPLES =====
# Count every triple
triple_counts = Counter()
for _, row in df_pred.iterrows():
    nums = [row[c] for c in cols[:6]]
    for a,b,c in combinations(sorted(nums), 3):
        triple_counts[(a,b,c)] += 1

top_triples = triple_counts.most_common(10)

# For a given pair, find best 3rd number
def best_third_for_pair(pair):
    a, b = sorted(pair)
    candidates = []
    for (x,y,z), cnt in triple_counts.items():
        if a in (x,y,z) and b in (x,y,z):
            third = [n for n in (x,y,z) if n not in (a,b)][0]
            candidates.append((third, cnt))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0] if candidates else (None, 0)

# ===== DISPLAY GRID =====
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

# ===== TRIPLES TABLE =====
st.subheader("🔺 Top 10 Triples - When 2 Come, The 3rd Follows")
triple_data = []
for (a,b,c), cnt in top_triples:
    triple_data.append({
        'Triple': f"{a} + {b} + {c}",
        'Times Together': cnt,
        'Probability': f"{round(cnt/len(df_pred)*100,1)}%",
    })
st.dataframe(pd.DataFrame(triple_data), use_container_width=True)

# ===== TRIPLE CHECKER =====
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

# ===== FINAL COMBOS BUILT FROM TRIPLES =====
st.subheader(f"🎯 Final Combos for {selected_date.strftime('%A %d %B')} - {draw_type}")
def build_combo_from_triple(triple):
    combo = list(triple)
    # Add banker if not in
    if banker not in combo and len(combo) < 6:
        combo.append(banker)
    # Fill with best predictions
    for b in ball_names[:6]:
        for num, _ in predictions[b]:
            if num not in combo and len(combo) < 6:
                combo.append(num)
                break
    while len(combo) < 6:
        n = random.randint(1,49)
        if n not in combo: combo.append(n)
    return sorted(combo)

# Combo 1 = Top triple + banker
combo1 = build_combo_from_triple(top_triples[0][0] if top_triples else (banker,1,2))
combo2 = build_combo_from_triple(top_triples[1][0] if len(top_triples)>1 else (banker,1,2))
combo3 = build_combo_from_triple(top_triples[2][0] if len(top_triples)>2 else (banker,1,2))

for i, combo in enumerate([combo1, combo2, combo3], 1):
    high = sum(1 for x in combo if x >= 25)
    st.success(f"**Combo {i} for {selected_date.strftime('%d %B')} {draw_type}: {combo}** → {high} High / {6-high} Low | Booster: {banker}")

# ===== DAILY HISTORY - Last 7 Days =====
st.subheader("📅 Last 7 Days - Lunchtime & Teatime")
last7 = df_all[df_all['Date'] >= today - timedelta(days=7)].sort_values('Date', ascending=False)
for _, row in last7.head(14).iterrows():
    nums = [int(row[c]) for c in cols_main]
    st.write(f"**{row['Date']} - {row['Draw']}:** {nums} + Booster {int(row['Booster'])}")

st.warning("⚠️ Stats only - UK49s is random. Check yesterday's results above to see how yesterday's prediction did.")