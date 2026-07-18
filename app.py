import streamlit as st
import pandas as pd
import altair as alt
import random
import base64
import os
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Daily Routine", page_icon="✨", layout="centered")

# --- 0.1 Inject Local Background Image ---
def set_bg_from_local(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url(data:image/jpeg;base64,{encoded_string});
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

set_bg_from_local("prism.jpg")

# --- 0.2 Look & Feel: Dark/Neon Glassmorphism UI ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Poppins:wght@400;600&display=swap');

html, body, [class*="css"] { 
    font-family: 'Poppins', sans-serif; 
    color: #E2E8F0 !important; 
    font-size: 18px !important; 
}

h1, h2, h3, h4, h5, h6 { 
    font-family: 'Orbitron', sans-serif !important; 
    color: #00D4FF !important; 
    text-shadow: 0 0 10px rgba(0, 212, 255, 0.4); 
}
h1 { font-size: 2.6rem !important; }
h2 { font-size: 2.2rem !important; }
h3 { font-size: 1.8rem !important; }
h4 { font-size: 1.5rem !important; }

p, label, .stMarkdown, .stCheckbox span { 
    color: #FFFFFF !important; 
    text-shadow: 0 1px 3px rgba(0,0,0,0.8);
    font-size: 18px !important; 
}

section[data-testid="stSidebar"] {
    background-color: rgba(5, 10, 20, 0.85) !important;
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(0, 212, 255, 0.2);
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(15, 20, 30, 0.75) !important;
    backdrop-filter: blur(10px);
    border-radius: 18px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    padding: 12px 16px;
    margin-bottom: 16px;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    border: 1px solid rgba(0, 212, 255, 0.25) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0, 212, 255, 0.15);
    border: 1px solid rgba(0, 212, 255, 0.6) !important;
}

div[data-testid="stMetric"] {
    background: rgba(15, 20, 30, 0.75) !important;
    backdrop-filter: blur(8px);
    border-radius: 16px;
    padding: 12px;
    border: 1px solid rgba(0, 212, 255, 0.25);
}
div[data-testid="stMetricValue"] { 
    color: #00D4FF !important; 
    font-size: 2.2rem !important;
}

.stProgress > div > div > div {
    background-image: linear-gradient(90deg, #0055FF, #00D4FF, #0055FF);
    background-size: 200% 100%;
    animation: shimmer 2s linear infinite;
    border-radius: 20px;
    height: 12px;
}
@keyframes shimmer {
    0% { background-position: 100% 0; }
    100% { background-position: -100% 0; }
}

.stButton > button {
    border-radius: 999px;
    border: 1px solid #00D4FF;
    background: rgba(0, 212, 255, 0.1);
    color: #00D4FF !important;
    font-weight: 600;
    font-size: 16px !important;
    padding: 10px 24px;
    transition: all 0.2s ease;
}
.stButton > button:hover { 
    transform: scale(1.04); 
    background: #00D4FF;
    color: #000000 !important;
    box-shadow: 0 0 15px rgba(0, 212, 255, 0.6);
}
</style>
""", unsafe_allow_html=True)

# --- 1. Constants ---
CATEGORIES = {
    "💪 Fitness":   "#FF6B6B",
    "🥗 Nutrition": "#4ECDC4",
    "💻 Learning":  "#A78BFA",
    "🏠 Home":      "#FBBF24",
    "✨ Other":     "#00D4FF",
}
PRIORITIES = {"🔥 High": 3, "⭐ Medium": 2, "🌙 Low": 1}
CHEER_MESSAGES = [
    "Nice work! 🎉", "You're on fire! 🔥", "Crushing it! 💪",
    "One step closer! ✨", "Keep the streak alive! ⚡", "Boom, done! 🚀",
]
TASK_COLS = ["Task", "Category", "Priority", "Completed", "Date", "Streak", "LastCompletedDate"]
HISTORY_COLS = ["Date", "Completed", "Total", "Pct"]

def streak_badge(n: int) -> str:
    if n >= 30: return "👑"
    if n >= 14: return "🏆"
    if n >= 7:  return "🔥"
    if n >= 3:  return "⚡"
    if n >= 1:  return "✨"
    return ""

WORDLE_WORDS = ["FOCUS", "HABIT", "BOOST", "SWEAT", "CLEAN", "STUDY", "EARLY", "FRESH", "SPARK", "DAILY", "GRIND", "WORTH", "SMART", "BUILD", "PRIDE"]
SCRAMBLE_WORDS = ["EXERCISE", "PROTEIN", "STREAK", "CHECKLIST", "MOTIVATION", "DISCIPLINE", "HYDRATE", "PLANNER", "CONSISTENCY", "MINDSET", "PROGRESS", "BALANCE", "ROUTINE"]

def daily_word(pool): return pool[date.today().toordinal() % len(pool)]

def score_guess(guess: str, target: str):
    result = ["absent"] * len(target)
    target_chars = list(target)
    for i, ch in enumerate(guess):
        if i < len(target_chars) and ch == target_chars[i]:
            result[i], target_chars[i] = "correct", None
    for i, ch in enumerate(guess):
        if result[i] == "correct": continue
        if ch in target_chars:
            result[i], target_chars[target_chars.index(ch)] = "present", None
    return result

def render_wordle_row(guess: str, statuses: list):
    colors = {"correct": "#4ECDC4", "present": "#FBBF24", "absent": "#334155"}
    cells = "".join(f"<span style='display:inline-block; width:50px; height:50px; line-height:50px; text-align:center; margin:3px; border-radius:10px; font-weight:700; font-size:24px; color:white; background:{colors[s]}; border: 1px solid rgba(255,255,255,0.1);'>{ch}</span>" for ch, s in zip(guess, statuses))
    st.markdown(f"<div>{cells}</div>", unsafe_allow_html=True)

# --- 2. Database Connection & Core Load ---
conn = st.connection("gsheets", type=GSheetsConnection)

def _ensure_task_columns(df: pd.DataFrame) -> pd.DataFrame:
    defaults = {"Category": "✨ Other", "Priority": "⭐ Medium", "Streak": 0, "LastCompletedDate": ""}
    for col in TASK_COLS:
        if col not in df.columns: df[col] = defaults.get(col, "")
    return df[TASK_COLS]

def load_history():
    try:
        hist = conn.read(worksheet="History", ttl=20) 
        if hist.empty: hist = pd.DataFrame(columns=HISTORY_COLS)
    except:
        hist = pd.DataFrame(columns=HISTORY_COLS)
        try: conn.create(worksheet="History", data=hist)
        except: pass 
    return hist

def save_history(hist_df):
    try: conn.update(worksheet="History", data=hist_df)
    except:
        try: conn.create(worksheet="History", data=hist_df)
        except: pass

def load_data():
    df = conn.read(ttl=5) 
    if df.empty:
        tasks = [
            ("💪 Ab roller & core training", "💪 Fitness", "⭐ Medium"),
            ("🏋️ Goblet squats", "💪 Fitness", "⭐ Medium"),
            ("🥩 Track daily protein intake", "🥗 Nutrition", "🔥 High"),
            ("🍱 Prep chicken, rice, and peas", "🥗 Nutrition", "🔥 High"),
            ("💻 Review Python/PySpark notes", "💻 Learning", "⭐ Medium"),
            ("📦 Sort living room boxes", "🏠 Home", "🌙 Low"),
        ]
        df = pd.DataFrame({"Task": [t[0] for t in tasks], "Category": [t[1] for t in tasks], "Priority": [t[2] for t in tasks], "Completed": [False] * len(tasks), "Date": [str(date.today())] * len(tasks), "Streak": [0] * len(tasks), "LastCompletedDate": [""] * len(tasks)})
        conn.update(data=df)
        st.cache_data.clear()
        return df

    df = _ensure_task_columns(df)
    df['Completed'] = df['Completed'].astype(str).str.upper() == 'TRUE'
    df['Streak'] = pd.to_numeric(df['Streak'], errors="coerce").fillna(0).astype(int)

    if str(df['Date'].iloc[0]) != str(date.today()):
        prev_date, completed_yesterday, total = str(df['Date'].iloc[0]), int(df['Completed'].sum()), len(df)
        pct = round((completed_yesterday / total) * 100, 1) if total else 0.0
        hist = load_history()
        hist = pd.concat([hist, pd.DataFrame([{"Date": prev_date, "Completed": completed_yesterday, "Total": total, "Pct": pct}])], ignore_index=True)
        save_history(hist)
        df['LastCompletedDate'] = df.apply(lambda r: prev_date if r['Completed'] else r['LastCompletedDate'], axis=1)
        df['Streak'] = df.apply(lambda r: r['Streak'] + 1 if r['Completed'] else 0, axis=1)
        df['Completed'] = False
        df['Date'] = str(date.today())
        conn.update(data=df)
        st.cache_data.clear()
    return df

def persist_tasks(df, rerun=True, success_msg=None):
    st.session_state.tasks_df = df
    try: conn.update(data=df)
    except: st.toast("⚠️ Rate limited — kept for this session.", icon="⚠️")
    if success_msg: st.success(success_msg)
    if rerun: st.rerun()

try:
    if "tasks_df" not in st.session_state: st.session_state.tasks_df = load_data()
    df = st.session_state.tasks_df
except:
    if "tasks_df" in st.session_state: df = st.session_state.tasks_df
    else:
        st.error("⏳ Google Sheets is rate-limited right now. Please wait a few seconds and refresh.")
        st.stop()

# --- Lazy Loaders for Health and Budget ---
def load_steps_data():
    try:
        steps_df = conn.read(worksheet="Steps", ttl=5)
        if steps_df.empty: steps_df = pd.DataFrame(columns=["Date", "Steps"])
    except:
        steps_df = pd.DataFrame(columns=["Date", "Steps"])
        try: conn.create(worksheet="Steps", data=steps_df)
        except: pass
    return steps_df

def load_budget_data():
    try:
        budget_df = conn.read(worksheet="Budget", ttl=5)
        if budget_df.empty:
            budget_df = pd.DataFrame({
                "Item": ["Main Income", "Shared Household Fund", "Rent/Mortgage", "Groceries & Meal Prep", "Moving & Furniture Fund", "Gym & Supplements"],
                "Category": ["Income", "Income", "Housing", "Food", "Savings", "Health"],
                "Type": ["Income", "Income", "Expense", "Expense", "Expense", "Expense"],
                "Amount": [2500, 1000, 1200, 400, 400, 100]
            })
            conn.create(worksheet="Budget", data=budget_df)
    except:
        budget_df = pd.DataFrame(columns=["Item", "Category", "Type", "Amount"])
        try: conn.create(worksheet="Budget", data=budget_df)
        except: pass
    return budget_df

# --- 3. Sidebar Navigation & Global Metrics ---
st.sidebar.title("✨ Routine Hub")

move_date = date(2026, 8, 22)
days_left = (move_date - date.today()).days
st.sidebar.metric(label="🗓️ Days Until Move", value=days_left)

best_streak = int(df['Streak'].max()) if not df.empty else 0
st.sidebar.metric(label="Best Active Streak", value=f"{best_streak}d {streak_badge(best_streak)}")

if st.sidebar.button("🔄 Sync from Sheet"):
    st.session_state.clear()
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
page = st.sidebar.radio("Navigation", ["📝 Daily Checklist", "📊 Analytics", "👟 Health Tracker", "💸 Monthly Budget", "⚙️ Manage Tasks", "🎮 Reward Game"])

# --- 4. Page: Daily Checklist ---
if page == "📝 Daily Checklist":
    from datetime import datetime
    current_hour = datetime.now().hour
    greeting = "Good Morning! ☀️" if current_hour < 12 else "Good Afternoon! ☕" if current_hour < 18 else "Good Evening! 🌙"

    st.markdown(f"<h1 style='text-align: center;'>{greeting}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: #94A3B8; margin-bottom: 30px;'>{date.today().strftime('%A, %B %d')}</h4>", unsafe_allow_html=True)

    completed_count, total_tasks = int(df['Completed'].sum()), len(df)
    progress_pct = int((completed_count / total_tasks) * 100) if total_tasks > 0 else 0
    st.progress(progress_pct, text=f"Daily Progress: {progress_pct}%")
    if progress_pct == 100 and total_tasks > 0: st.balloons()

    st.divider()
    updated = False

    for cat, color in CATEGORIES.items():
        cat_tasks = df[df['Category'] == cat]
        if cat_tasks.empty: continue
        st.markdown(f"<h3 style='color:{color}; margin-bottom:10px;'>{cat}</h3>", unsafe_allow_html=True)

        for index, row in cat_tasks.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1: checked = st.checkbox(row['Task'], value=row['Completed'], key=f"task_{index}")
                with c2:
                    badge = streak_badge(row['Streak'])
                    streak_txt = f"{badge}{row['Streak']}" if row['Streak'] > 0 else ""
                    pri_emoji = row['Priority'].split()[0] if row['Priority'] else ""
                    st.markdown(f"<div style='text-align:right; padding-top:6px; font-size: 20px;'>{pri_emoji} {streak_txt}</div>", unsafe_allow_html=True)
            if checked != row['Completed']:
                df.at[index, 'Completed'] = checked
                updated = True
                if checked: st.toast(random.choice(CHEER_MESSAGES))

    if updated: persist_tasks(df)

    st.divider()
    st.write("### ➕ Add a Task")
    with st.form("add_task_form", clear_on_submit=True):
        new_task = st.text_input("New task name:", placeholder="e.g., Water the plants 🌱")
        c1, c2 = st.columns(2)
        with c1: new_cat = st.selectbox("Category", list(CATEGORIES.keys()))
        with c2: new_pri = st.selectbox("Priority", list(PRIORITIES.keys()), index=1)
        if st.form_submit_button("Add to list", type="primary") and new_task:
            new_row = pd.DataFrame({"Task": [new_task], "Category": [new_cat], "Priority": [new_pri], "Completed": [False], "Date": [str(date.today())], "Streak": [0], "LastCompletedDate": [""]})
            df = pd.concat([df, new_row], ignore_index=True)
            persist_tasks(df)

# --- 5. Page: Analytics ---
elif page == "📊 Analytics":
    st.title("Performance Analytics 📈")
    completed_count, total_tasks = int(df['Completed'].sum()), len(df)
    pending_count = total_tasks - completed_count
    pct = round((completed_count / total_tasks) * 100, 1) if total_tasks else 0
    best_streak_val = int(df['Streak'].max()) if not df.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Completed", completed_count)
    c2.metric("⏳ Pending", pending_count)
    c3.metric("📊 Rate", f"{pct}%")
    c4.metric("🔥 Best Streak", f"{best_streak_val}d")

    st.divider()
    if total_tasks > 0:
        chart_data = pd.DataFrame({"Status": ["Completed", "Pending"], "Count": [completed_count, pending_count]})
        base = alt.Chart(chart_data).encode(theta=alt.Theta("Count:Q", stack=True), color=alt.Color("Status:N", scale=alt.Scale(domain=["Completed", "Pending"], range=["#00D4FF", "#334155"]), legend=alt.Legend(title="Status", labelColor="white", titleColor="white"))).properties(height=320)
        st.altair_chart(base.mark_arc(innerRadius=60), use_container_width=True)
    else: st.info("No tasks available to track.")

    st.divider()
    st.write("#### 14-Day Trend")
    hist = load_history()
    if not hist.empty:
        hist["Date"] = pd.to_datetime(hist["Date"], errors="coerce")
        hist["Pct"] = pd.to_numeric(hist["Pct"], errors="coerce")
        hist = hist.dropna(subset=["Date"]).sort_values("Date").tail(14)
        area = alt.Chart(hist).mark_area(line={"color": "#00D4FF", "size": 3}, color=alt.Gradient(gradient="linear", stops=[alt.GradientStop(color="rgba(0, 212, 255, 0.5)", offset=0), alt.GradientStop(color="rgba(0, 212, 255, 0)", offset=1)], x1=1, x2=1, y1=1, y2=0)).encode(x=alt.X("Date:T", title=""), y=alt.Y("Pct:Q", title="% Complete", scale=alt.Scale(domain=[0, 100])), tooltip=["Date:T", "Pct:Q", "Completed:Q", "Total:Q"]).properties(height=260)
        st.altair_chart(area, use_container_width=True)
    else: st.info("Trend data builds up automatically — check back after your first daily reset.")

# --- 6. Page: Health Tracker ---
elif page == "👟 Health Tracker":
    st.title("Activity Tracker 👟")
    steps_df = load_steps_data()
    
    st.write("#### Log Today's Steps")
    today_str = str(date.today())
    current_steps = 0
    if today_str in steps_df['Date'].values:
        current_steps = int(steps_df.loc[steps_df['Date'] == today_str, 'Steps'].iloc[0])

    with st.form("steps_form"):
        new_steps = st.number_input("How many steps today?", min_value=0, max_value=100000, value=current_steps, step=500)
        if st.form_submit_button("Save Steps", type="primary"):
            if today_str in steps_df['Date'].values:
                steps_df.loc[steps_df['Date'] == today_str, 'Steps'] = new_steps
            else:
                new_row = pd.DataFrame({"Date": [today_str], "Steps": [new_steps]})
                steps_df = pd.concat([steps_df, new_row], ignore_index=True)
            conn.update(worksheet="Steps", data=steps_df)
            st.cache_data.clear()
            st.success("Steps logged successfully!")
            st.rerun()

    st.divider()
    st.write("#### Recent Activity")
    if not steps_df.empty:
        steps_df['Date'] = pd.to_datetime(steps_df['Date'])
        steps_df['Steps'] = pd.to_numeric(steps_df['Steps'])
        plot_df = steps_df.sort_values('Date').tail(14)
        
        bars = alt.Chart(plot_df).mark_bar(color="#00D4FF", cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X("Date:T", title=""),
            y=alt.Y("Steps:Q", title="Steps"),
            tooltip=["Date:T", "Steps:Q"]
        )
        rule = alt.Chart(pd.DataFrame({'Goal': [10000]})).mark_rule(color='#FF6B6B', strokeDash=[5,5], size=2).encode(y='Goal:Q')
        st.altair_chart((bars + rule).properties(height=300), use_container_width=True)
    else:
        st.info("Log your first steps to see your chart!")

# --- 7. Page: Monthly Budget ---
elif page == "💸 Monthly Budget":
    st.title("Financial Hub 💸")
    budget_df = load_budget_data()
    
    budget_df['Amount'] = pd.to_numeric(budget_df['Amount'], errors='coerce').fillna(0)
    total_income = budget_df[budget_df['Type'] == 'Income']['Amount'].sum()
    total_expense = budget_df[budget_df['Type'] == 'Expense']['Amount'].sum()
    net_funds = total_income - total_expense

    c1, c2, c3 = st.columns(3)
    c1.metric("Gross Income", f"£{total_income:,.2f}")
    c2.metric("Total Expenses", f"£{total_expense:,.2f}")
    c3.metric("Net Remaining", f"£{net_funds:,.2f}", delta=float(net_funds))

    st.divider()
    st.write("#### ✏️ Manage Budget Items")
    edited_budget = st.data_editor(
        budget_df,
        column_config={
            "Type": st.column_config.SelectboxColumn(options=["Income", "Expense"]),
            "Category": st.column_config.SelectboxColumn(options=["Income", "Housing", "Food", "Transport", "Utilities", "Health", "Savings", "Entertainment", "Other"]),
            "Amount": st.column_config.NumberColumn(format="£%d")
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )
    
    if st.button("💾 Save Ledger", type="primary"):
        conn.update(worksheet="Budget", data=edited_budget)
        st.cache_data.clear()
        st.success("Budget saved!")
        st.rerun()

    st.divider()
    st.write("#### Expense Breakdown")
    expenses_only = edited_budget[edited_budget['Type'] == 'Expense']
    if not expenses_only.empty:
        summary = expenses_only.groupby('Category')['Amount'].sum().reset_index()
        donut = alt.Chart(summary).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Amount", type="quantitative"),
            color=alt.Color(field="Category", type="nominal", legend=alt.Legend(labelColor="white", titleColor="white")),
            tooltip=["Category", "Amount"]
        ).properties(height=350)
        st.altair_chart(donut, use_container_width=True)

# --- 8. Page: Manage Tasks ---
elif page == "⚙️ Manage Tasks":
    st.title("Task Management 🗑️")
    st.write("#### ✏️ Edit Tasks")
    edited = st.data_editor(
        df[["Task", "Category", "Priority"]],
        column_config={"Category": st.column_config.SelectboxColumn(options=list(CATEGORIES.keys())), "Priority": st.column_config.SelectboxColumn(options=list(PRIORITIES.keys()))},
        use_container_width=True, hide_index=True
    )
    if st.button("💾 Save Changes", type="primary"):
        df["Task"], df["Category"], df["Priority"] = edited["Task"], edited["Category"], edited["Priority"]
        persist_tasks(df, success_msg="Changes saved!")

    st.divider()
    st.write("#### 🗑️ Delete Tasks")
    tasks_to_delete = st.multiselect("Select tasks to delete:", df['Task'].tolist())
    if st.button("Delete Selected Tasks", type="primary"):
        if tasks_to_delete:
            df = df[~df['Task'].isin(tasks_to_delete)].reset_index(drop=True)
            persist_tasks(df, success_msg="Tasks removed successfully!")
        else: st.warning("Please select at least one task to delete.")

# --- 9. Page: Reward Game ---
elif page == "🎮 Reward Game":
    completed_count, total_tasks = int(df['Completed'].sum()), len(df)
    progress_pct = int((completed_count / total_tasks) * 100) if total_tasks > 0 else 0

    if progress_pct < 100:
        st.title("🔒 Reward Game")
        st.progress(progress_pct, text=f"{progress_pct}% complete — {total_tasks - completed_count} task(s) to go")
    else:
        st.title("🎉 All Done — Play!")
        tab1, tab2 = st.tabs(["🟩 Wordle", "🔀 Word Scramble"])
        with tab1:
            target = daily_word(WORDLE_WORDS)
            if st.session_state.get("wordle_target") != target:
                st.session_state.update({"wordle_target": target, "wordle_guesses": [], "wordle_won": False})
            for g in st.session_state.wordle_guesses: render_wordle_row(g, score_guess(g, target))
            if not st.session_state.wordle_won and len(st.session_state.wordle_guesses) < 6:
                with st.form("wordle_form", clear_on_submit=True):
                    guess = st.text_input(f"Guess the {len(target)}-letter word:", max_chars=len(target))
                    if st.form_submit_button("Guess"):
                        guess = guess.upper().strip()
                        if len(guess) != len(target) or not guess.isalpha(): st.warning(f"Enter a {len(target)}-letter word.")
                        else:
                            st.session_state.wordle_guesses.append(guess)
                            if guess == target: st.session_state.wordle_won = True
                            st.rerun()
            if st.session_state.wordle_won:
                st.success(f"🎉 You got it — **{target}**!")
                st.balloons()
            elif len(st.session_state.wordle_guesses) >= 6: st.error(f"Out of guesses! The word was **{target}**.")

        with tab2:
            s_target = daily_word(SCRAMBLE_WORDS)
            if st.session_state.get("scramble_target") != s_target:
                letters = list(s_target)
                random.shuffle(letters)
                while "".join(letters) == s_target and len(set(s_target)) > 1: random.shuffle(letters)
                st.session_state.update({"scramble_target": s_target, "scramble_display": "".join(letters), "scramble_solved": False, "scramble_tries": 0})
            st.markdown(f"<h2 style='letter-spacing:8px; text-align:center;'>{st.session_state.scramble_display}</h2>", unsafe_allow_html=True)
            if not st.session_state.scramble_solved:
                with st.form("scramble_form", clear_on_submit=True):
                    answer = st.text_input("Unscramble it:")
                    if st.form_submit_button("Submit"):
                        st.session_state.scramble_tries += 1
                        if answer.upper().strip() == s_target: st.session_state.scramble_solved = True
                        else: st.warning("Not quite — try again!")
                if st.button("💡 Hint (reveal first letter)"): st.info(f"Starts with **{s_target[0]}**")
            else:
                st.success(f"🎉 Solved in {st.session_state.scramble_tries} tries — it was **{s_target}**!")
                st.balloons()
