import streamlit as st
import pandas as pd
import altair as alt
import random
import base64
import os
from datetime import date
from streamlit_gsheets import GSheetsConnection

# 'layout="centered"' keeps the UI tight and readable on both phones and monitors
st.set_page_config(page_title="Daily Routine", page_icon="✨", layout="centered")

# --- 0.1 Inject Local Background Image ---
def set_bg_from_local(image_file):
    """Reads a local image and injects it into the CSS as a base64 background."""
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

# Looks for the newly uploaded prism.jpg file on GitHub
set_bg_from_local("prism.jpg")

# --- 0.2 Look & Feel: Dark/Neon Glassmorphism UI (Larger Fonts) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Poppins:wght@400;600&display=swap');

/* Bumped up the base font size for the whole app */
html, body, [class*="css"] { 
    font-family: 'Poppins', sans-serif; 
    color: #E2E8F0 !important; 
    font-size: 18px !important; 
}

/* Headers get a futuristic font, neon glow, and larger sizes */
h1, h2, h3, h4, h5, h6 { 
    font-family: 'Orbitron', sans-serif !important; 
    color: #00D4FF !important; 
    text-shadow: 0 0 10px rgba(0, 212, 255, 0.4); 
}
h1 { font-size: 2.6rem !important; }
h2 { font-size: 2.2rem !important; }
h3 { font-size: 1.8rem !important; }
h4 { font-size: 1.5rem !important; }

/* Ensure standard text and checkboxes are larger and crisp white */
p, label, .stMarkdown, .stCheckbox span { 
    color: #FFFFFF !important; 
    text-shadow: 0 1px 3px rgba(0,0,0,0.8);
    font-size: 18px !important; 
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: rgba(5, 10, 20, 0.85) !important;
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(0, 212, 255, 0.2);
}

/* Floating Dark Cards */
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

/* Metrics Dashboard Cards */
div[data-testid="stMetric"] {
    background: rgba(15, 20, 30, 0.75) !important;
    backdrop-filter: blur(8px);
    border-radius: 16px;
    padding: 12px;
    border: 1px solid rgba(0, 212, 255, 0.25);
}
/* Larger metric numbers */
div[data-testid="stMetricValue"] { 
    color: #00D4FF !important; 
    font-size: 2.2rem !important;
}

/* Animated glowing progress bar */
.stProgress > div > div > div {
    background-image: linear-gradient(90deg, #0055FF, #00D4FF, #0055FF);
    background-size: 200% 100%;
    animation: shimmer 2s linear infinite;
    border-radius: 20px;
    height: 12px; /* Slightly thicker progress bar */
}
@keyframes shimmer {
    0% { background-position: 100% 0; }
    100% { background-position: -100% 0; }
}

/* Buttons */
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

# --- Reward game ---
WORDLE_WORDS = ["FOCUS", "HABIT", "BOOST", "SWEAT", "CLEAN", "STUDY", "EARLY",
                "FRESH", "SPARK", "DAILY", "GRIND", "WORTH", "SMART", "BUILD", "PRIDE"]
SCRAMBLE_WORDS = ["EXERCISE", "PROTEIN", "STREAK", "CHECKLIST", "MOTIVATION", "DISCIPLINE",
                   "HYDRATE", "PLANNER", "CONSISTENCY", "MINDSET", "PROGRESS", "BALANCE", "ROUTINE"]

def daily_word(pool):
    return pool[date.today().toordinal() % len(pool)]

def score_guess(guess: str, target: str):
    result = ["absent"] * len(target)
    target_chars = list(target)
    for i, ch in enumerate(guess):
        if i < len(target_chars) and ch == target_chars[i]:
            result[i] = "correct"
            target_chars[i] = None
    for i, ch in enumerate(guess):
        if result[i] == "correct":
            continue
        if ch in target_chars:
            result[i] = "present"
            target_chars[target_chars.index(ch)] = None
    return result

def render_wordle_row(guess: str, statuses: list):
    colors = {"correct": "#4ECDC4", "present": "#FBBF24", "absent": "#334155"}
    cells = "".join(
        f"<span style='display:inline-block; width:50px; height:50px; line-height:50px; "
        f"text-align:center; margin:3px; border-radius:10px; font-weight:700; font-size:24px; "
        f"color:white; background:{colors[s]}; border: 1px solid rgba(255,255,255,0.1);'>{ch}</span>"
        for ch, s in zip(guess, statuses)
    )
    st.markdown(f"<div>{cells}</div>", unsafe_allow_html=True)

# --- 2. Database Connection & Load ---
conn = st.connection("gsheets", type=GSheetsConnection)

def _ensure_task_columns(df: pd.DataFrame) -> pd.DataFrame:
    defaults = {"Category": "✨ Other", "Priority": "⭐ Medium", "Streak": 0, "LastCompletedDate": ""}
    for col in TASK_COLS:
        if col not in df.columns:
            df[col] = defaults.get(col, "")
    return df[TASK_COLS]

def load_history():
    try:
        hist = conn.read(worksheet="History", ttl=20) 
        if hist.empty:
            hist = pd.DataFrame(columns=HISTORY_COLS)
    except Exception:
        hist = pd.DataFrame(columns=HISTORY_COLS)
        try:
            conn.create(worksheet="History", data=hist)
        except Exception:
            pass 
    return hist

def save_history(hist_df):
    try:
        conn.update(worksheet="History", data=hist_df)
    except Exception:
        try:
            conn.create(worksheet="History", data=hist_df)
        except Exception:
            pass

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
        df = pd.DataFrame({
            "Task": [t[0] for t in tasks],
            "Category": [t[1] for t in tasks],
            "Priority": [t[2] for t in tasks],
            "Completed": [False] * len(tasks),
            "Date": [str(date.today())] * len(tasks),
            "Streak": [0] * len(tasks),
            "LastCompletedDate": [""] * len(tasks),
        })
        conn.update(data=df)
        st.cache_data.clear()
        return df

    df = _ensure_task_columns(df)
    df['Completed'] = df['Completed'].astype(str).str.upper() == 'TRUE'
    df['Streak'] = pd.to_numeric(df['Streak'], errors="coerce").fillna(0).astype(int)

    if str(df['Date'].iloc[0]) != str(date.today()):
        prev_date = str(df['Date'].iloc[0])
        completed_yesterday = int(df['Completed'].sum())
        total = len(df)
        pct = round((completed_yesterday / total) * 100, 1) if total else 0.0

        hist = load_history()
        hist = pd.concat([hist, pd.DataFrame([{
            "Date": prev_date, "Completed": completed_yesterday, "Total": total, "Pct": pct
        }])], ignore_index=True)
        save_history(hist)

        df['LastCompletedDate'] = df.apply(
            lambda r: prev_date if r['Completed'] else r['LastCompletedDate'], axis=1
        )
        df['Streak'] = df.apply(lambda r: r['Streak'] + 1 if r['Completed'] else 0, axis=1)

        df['Completed'] = False
        df['Date'] = str(date.today())
        conn.update(data=df)
        st.cache_data.clear()

    return df

def persist_tasks(df, rerun=True, success_msg=None):
    st.session_state.tasks_df = df
    try:
        conn.update(data=df)
    except Exception:
        st.toast("⚠️ Google Sheets is rate-limited — your change is kept for this session.", icon="⚠️")
    if success_msg:
        st.success(success_msg)
    if rerun:
        st.rerun()

try:
    if "tasks_df" not in st.session_state:
        st.session_state.tasks_df = load_data()
    df = st.session_state.tasks_df
except Exception:
    if "tasks_df" in st.session_state:
        df = st.session_state.tasks_df
        st.warning("⏳ Google Sheets is briefly rate-limited — showing the last loaded data.")
    else:
        st.error("⏳ Google Sheets is rate-limited right now. Please wait a few seconds and refresh.")
        st.stop()

# --- 3. Sidebar Navigation & Global Metrics ---
st.sidebar.title("✨ Routine Hub")

move_date = date(2026, 8, 22)
days_left = (move_date - date.today()).days
st.sidebar.metric(label="🗓️ Days Until Move", value=days_left)

best_streak = int(df['Streak'].max()) if not df.empty else 0
st.sidebar.metric(label="Best Active Streak", value=f"{best_streak}d {streak_badge(best_streak)}")

if st.sidebar.button("🔄 Sync from Sheet"):
    st.session_state.pop("tasks_df", None)
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
page = st.sidebar.radio("Navigation", ["📝 Daily Checklist", "📊 Analytics", "⚙️ Manage Tasks", "🎮 Reward Game"])

# --- 4. Page: Daily Checklist ---
if page == "📝 Daily Checklist":
    from datetime import datetime
    
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting = "Good Morning! ☀️"
    elif 12 <= current_hour < 18:
        greeting = "Good Afternoon! ☕"
    else:
        greeting = "Good Evening! 🌙"

    st.markdown(f"<h1 style='text-align: center;'>{greeting}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: #94A3B8; margin-bottom: 30px;'>{date.today().strftime('%A, %B %d')}</h4>", unsafe_allow_html=True)

    completed_count = int(df['Completed'].sum())
    total_tasks = len(df)
    progress_pct = int((completed_count / total_tasks) * 100) if total_tasks > 0 else 0

    st.progress(progress_pct, text=f"Daily Progress: {progress_pct}%")
    if progress_pct == 100 and total_tasks > 0:
        st.balloons()

    st.divider()
    updated = False

    for cat, color in CATEGORIES.items():
        cat_tasks = df[df['Category'] == cat]
        if cat_tasks.empty:
            continue
        st.markdown(f"<h3 style='color:{color}; margin-bottom:10px;'>{cat}</h3>", unsafe_allow_html=True)

        for index, row in cat_tasks.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    checked = st.checkbox(row['Task'], value=row['Completed'], key=f"task_{index}")
                with c2:
                    badge = streak_badge(row['Streak'])
                    streak_txt = f"{badge}{row['Streak']}" if row['Streak'] > 0 else ""
                    pri_emoji = row['Priority'].split()[0] if row['Priority'] else ""
                    st.markdown(
                        f"<div style='text-align:right; padding-top:6px; font-size: 20px;'>{pri_emoji} {streak_txt}</div>",
                        unsafe_allow_html=True,
                    )
            if checked != row['Completed']:
                df.at[index, 'Completed'] = checked
                updated = True
                if checked:
                    st.toast(random.choice(CHEER_MESSAGES))

    if updated:
        persist_tasks(df)

    st.divider()
    st.write("### ➕ Add a Task")
    with st.form("add_task_form", clear_on_submit=True):
        new_task = st.text_input("New task name:", placeholder="e.g., Water the plants 🌱")
        c1, c2 = st.columns(2)
        with c1:
            new_cat = st.selectbox("Category", list(CATEGORIES.keys()))
        with c2:
            new_pri = st.selectbox("Priority", list(PRIORITIES.keys()), index=1)
        submitted = st.form_submit_button("Add to list", type="primary")
        if submitted and new_task:
            new_row = pd.DataFrame({
                "Task": [new_task], "Category": [new_cat], "Priority": [new_pri],
                "Completed": [False], "Date": [str(date.today())],
                "Streak": [0], "LastCompletedDate": [""],
            })
            df = pd.concat([df, new_row], ignore_index=True)
            persist_tasks(df)

# --- 5. Page: Analytics ---
elif page == "📊 Analytics":
    st.title("Performance Analytics 📈")

    completed_count = int(df['Completed'].sum())
    total_tasks = len(df)
    pending_count = total_tasks - completed_count
    pct = round((completed_count / total_tasks) * 100, 1) if total_tasks else 0
    best_streak_val = int(df['Streak'].max()) if not df.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Completed", completed_count)
    c2.metric("⏳ Pending", pending_count)
    c3.metric("📊 Rate", f"{pct}%")
    c4.metric("🔥 Best Streak", f"{best_streak_val}d")

    st.divider()
    st.write("#### Today's Split")
    if total_tasks > 0:
        chart_data = pd.DataFrame({"Status": ["Completed", "Pending"], "Count": [completed_count, pending_count]})
        base = alt.Chart(chart_data).encode(
            theta=alt.Theta("Count:Q", stack=True),
            color=alt.Color("Status:N",
                             scale=alt.Scale(domain=["Completed", "Pending"], range=["#00D4FF", "#334155"]),
                             legend=alt.Legend(title="Status", labelColor="white", titleColor="white")),
        ).properties(height=320)
        st.altair_chart(base.mark_arc(innerRadius=60), use_container_width=True)
    else:
        st.info("No tasks available to track.")

    st.divider()
    st.write("#### Completion by Category")
    if total_tasks > 0:
        cat_summary = df.groupby("Category").agg(Completed=("Completed", "sum"), Total=("Task", "count")).reset_index()
        cat_summary["Pct"] = (cat_summary["Completed"] / cat_summary["Total"] * 100).round(0)
        bar = alt.Chart(cat_summary).mark_bar(cornerRadius=6).encode(
            x=alt.X("Pct:Q", title="% Complete", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Category:N", sort="-x", title=""),
            color=alt.Color("Category:N",
                             scale=alt.Scale(domain=list(CATEGORIES.keys()), range=list(CATEGORIES.values())),
                             legend=None),
            tooltip=["Category", "Completed", "Total", "Pct"],
        ).properties(height=220)
        st.altair_chart(bar, use_container_width=True)

    st.divider()
    st.write("#### 14-Day Trend")
    hist = load_history()
    if not hist.empty:
        hist = hist.copy()
        hist["Date"] = pd.to_datetime(hist["Date"], errors="coerce")
        hist["Pct"] = pd.to_numeric(hist["Pct"], errors="coerce")
        hist = hist.dropna(subset=["Date"]).sort_values("Date").tail(14)
        area = alt.Chart(hist).mark_area(
            line={"color": "#00D4FF", "size": 3},
            color=alt.Gradient(gradient="linear", stops=[
                alt.GradientStop(color="rgba(0, 212, 255, 0.5)", offset=0),
                alt.GradientStop(color="rgba(0, 212, 255, 0)", offset=1)], x1=1, x2=1, y1=1, y2=0),
        ).encode(
            x=alt.X("Date:T", title=""),
            y=alt.Y("Pct:Q", title="% Complete", scale=alt.Scale(domain=[0, 100])),
            tooltip=["Date:T", "Pct:Q", "Completed:Q", "Total:Q"],
        ).properties(height=260)
        st.altair_chart(area, use_container_width=True)
    else:
        st.info("Trend data builds up automatically — check back after your first daily reset.")

    st.divider()
    st.write("#### 🏆 Streak Leaderboard")
    board = df[["Task", "Category", "Streak"]].sort_values("Streak", ascending=False).reset_index(drop=True)
    board["Badge"] = board["Streak"].apply(streak_badge)
    st.dataframe(board, use_container_width=True, hide_index=True)

# --- 6. Page: Manage Tasks ---
elif page == "⚙️ Manage Tasks":
    st.title("Task Management 🗑️")

    st.write("#### ✏️ Edit Tasks")
    st.caption("Rename tasks or change their category/priority, then save.")
    edited = st.data_editor(
        df[["Task", "Category", "Priority"]],
        column_config={
            "Category": st.column_config.SelectboxColumn(options=list(CATEGORIES.keys())),
            "Priority": st.column_config.SelectboxColumn(options=list(PRIORITIES.keys())),
        },
        use_container_width=True,
        hide_index=True,
        key="task_editor",
    )
    if st.button("💾 Save Changes", type="primary"):
        df["Task"] = edited["Task"]
        df["Category"] = edited["Category"]
        df["Priority"] = edited["Priority"]
        persist_tasks(df, success_msg="Changes saved!")

    st.divider()
    st.write("#### 🗑️ Delete Tasks")
    tasks_to_delete = st.multiselect("Select tasks to delete:", df['Task'].tolist())

    if st.button("Delete Selected Tasks", type="primary"):
        if tasks_to_delete:
            df = df[~df['Task'].isin(tasks_to_delete)].reset_index(drop=True)
            persist_tasks(df, success_msg="Tasks removed successfully!")
        else:
            st.warning("Please select at least one task to delete.")

# --- 7. Page: Reward Game ---
elif page == "🎮 Reward Game":
    completed_count = int(df['Completed'].sum())
    total_tasks = len(df)
    progress_pct = int((completed_count / total_tasks) * 100) if total_tasks > 0 else 0

    if progress_pct < 100:
        st.title("🔒 Reward Game")
        st.write("Finish every task on today's checklist to unlock a quick word game!")
        st.progress(progress_pct, text=f"{progress_pct}% complete — {total_tasks - completed_count} task(s) to go")
    else:
        st.title("🎉 All Done — Play!")
        st.write("Nice work finishing today's checklist. Pick a game:")
        tab1, tab2 = st.tabs(["🟩 Wordle", "🔀 Word Scramble"])

        with tab1:
            target = daily_word(WORDLE_WORDS)
            if st.session_state.get("wordle_target") != target:
                st.session_state.wordle_target = target
                st.session_state.wordle_guesses = []
                st.session_state.wordle_won = False

            for g in st.session_state.wordle_guesses:
                render_wordle_row(g, score_guess(g, target))

            if not st.session_state.wordle_won and len(st.session_state.wordle_guesses) < 6:
                with st.form("wordle_form", clear_on_submit=True):
                    guess = st.text_input(f"Guess the {len(target)}-letter word:", max_chars=len(target))
                    go = st.form_submit_button("Guess")
                    if go:
                        guess = guess.upper().strip()
                        if len(guess) != len(target) or not guess.isalpha():
                            st.warning(f"Enter a {len(target)}-letter word.")
                        else:
                            st.session_state.wordle_guesses.append(guess)
                            if guess == target:
                                st.session_state.wordle_won = True
                            st.rerun()

            if st.session_state.wordle_won:
                st.success(f"🎉 You got it — **{target}**!")
                st.balloons()
            elif len(st.session_state.wordle_guesses) >= 6:
                st.error(f"Out of guesses! The word was **{target}**.")

        with tab2:
            s_target = daily_word(SCRAMBLE_WORDS)
            if st.session_state.get("scramble_target") != s_target:
                st.session_state.scramble_target = s_target
                letters = list(s_target)
                random.shuffle(letters)
                while "".join(letters) == s_target and len(set(s_target)) > 1:
                    random.shuffle(letters)
                st.session_state.scramble_display = "".join(letters)
                st.session_state.scramble_solved = False
                st.session_state.scramble_tries = 0

            st.markdown(
                f"<h2 style='letter-spacing:8px; text-align:center;'>{st.session_state.scramble_display}</h2>",
                unsafe_allow_html=True,
            )

            if not st.session_state.scramble_solved:
                with st.form("scramble_form", clear_on_submit=True):
                    answer = st.text_input("Unscramble it:")
                    submit = st.form_submit_button("Submit")
                    if submit:
                        st.session_state.scramble_tries += 1
                        if answer.upper().strip() == s_target:
                            st.session_state.scramble_solved = True
                        else:
                            st.warning("Not quite — try again!")
                if st.button("💡 Hint (reveal first letter)"):
                    st.info(f"Starts with **{s_target[0]}**")
            else:
                st.success(f"🎉 Solved in {st.session_state.scramble_tries} tries — it was **{s_target}**!")
                st.balloons()
