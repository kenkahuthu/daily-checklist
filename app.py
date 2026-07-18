import streamlit as st
import pandas as pd
import altair as alt
import random
from datetime import date
from streamlit_gsheets import GSheetsConnection

# 'layout="centered"' keeps the UI tight and readable on both phones and monitors
st.set_page_config(page_title="Daily Routine", page_icon="✨", layout="centered")

# --- 0. Look & Feel: colorful, card-based, playful UI ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;700&family=Poppins:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
h1, h2, h3 { font-family: 'Baloo 2', cursive; }

/* App background: a colorful gradient tint over a real daily-routine style photo
   (flat-lay planner + coffee + laptop, free to use under the Unsplash License,
   photo by Sincerely Media: https://unsplash.com/photos/EhU_E_0s3wE) */
.stApp {
    background-image:
        linear-gradient(135deg, rgba(253,235,113,0.55) 0%, rgba(255,234,167,0.55) 20%, rgba(250,178,255,0.55) 60%, rgba(160,231,229,0.55) 100%),
        url('https://images.unsplash.com/photo-1546352214-9148ef4d8c9c?fm=jpg&q=80&w=1920&auto=format&fit=crop');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    background-repeat: no-repeat;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #6C5CE7 0%, #8E7CFB 100%);
}
section[data-testid="stSidebar"] * { color: #FFFFFF !important; }

/* Card containers -> every st.container(border=True) becomes a soft floating card */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.88);
    border-radius: 18px !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.12);
    padding: 4px 10px;
    margin-bottom: 10px;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    border: none !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-2px) scale(1.01);
    box-shadow: 0 8px 20px rgba(0,0,0,0.18);
}

/* Metrics */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.85);
    border-radius: 16px;
    padding: 10px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.10);
}

/* Animated shimmering progress bar */
.stProgress > div > div > div {
    background-image: linear-gradient(90deg, #FF6B6B, #FFD93D, #6BCB77, #4D96FF);
    background-size: 300% 100%;
    animation: shimmer 3s linear infinite;
    border-radius: 20px;
}
@keyframes shimmer {
    0% { background-position: 0% 50%; }
    100% { background-position: 300% 50%; }
}

/* Buttons */
.stButton > button {
    border-radius: 999px;
    border: none;
    font-weight: 600;
    transition: transform 0.15s ease;
}
.stButton > button:hover { transform: scale(1.04); }
</style>
""", unsafe_allow_html=True)

# --- 1. Constants ---
CATEGORIES = {
    "💪 Fitness":   "#FF6B6B",
    "🥗 Nutrition": "#4ECDC4",
    "💻 Learning":  "#845EC2",
    "🏠 Home":      "#FFC75F",
    "✨ Other":     "#00C2A8",
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


# --- 2. Database Connection & Load ---
conn = st.connection("gsheets", type=GSheetsConnection)


def _ensure_task_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Backfills any new columns (Category/Priority/Streak/etc.) onto older sheets."""
    defaults = {"Category": "✨ Other", "Priority": "⭐ Medium", "Streak": 0, "LastCompletedDate": ""}
    for col in TASK_COLS:
        if col not in df.columns:
            df[col] = defaults.get(col, "")
    return df[TASK_COLS]


def load_history():
    """Reads the 'History' worksheet (daily completion log), creating it if missing."""
    try:
        hist = conn.read(worksheet="History", ttl=20)  # history changes once/day, cache longer
        if hist.empty:
            hist = pd.DataFrame(columns=HISTORY_COLS)
    except Exception:
        hist = pd.DataFrame(columns=HISTORY_COLS)
        try:
            conn.create(worksheet="History", data=hist)
        except Exception:
            pass  # tab may need to be created manually if the connection lacks permission
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
    df = conn.read(ttl=5)  # short cache: avoids a fresh API read on every single rerun

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
    # Force Boolean formatting to prevent pandas crashes
    df['Completed'] = df['Completed'].astype(str).str.upper() == 'TRUE'
    df['Streak'] = pd.to_numeric(df['Streak'], errors="coerce").fillna(0).astype(int)

    # --- The Daily Reset Logic, now with streak tracking + history logging ---
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

        # Streak = consecutive days completed; resets to 0 the moment a task is missed
        df['LastCompletedDate'] = df.apply(
            lambda r: prev_date if r['Completed'] else r['LastCompletedDate'], axis=1
        )
        df['Streak'] = df.apply(lambda r: r['Streak'] + 1 if r['Completed'] else 0, axis=1)

        df['Completed'] = False
        df['Date'] = str(date.today())
        conn.update(data=df)
        st.cache_data.clear()

    return df


try:
    df = load_data()
    st.session_state["last_good_df"] = df
except Exception:
    # Most likely a transient Google Sheets rate limit (429) — fall back to the
    # last successfully loaded data instead of crashing the whole app.
    if "last_good_df" in st.session_state:
        df = st.session_state["last_good_df"]
        st.warning("⏳ Google Sheets is briefly rate-limited — showing the last loaded data. It'll refresh in a few seconds.")
    else:
        st.error("⏳ Google Sheets is rate-limited right now (too many requests in the last minute). Please wait a few seconds and refresh the page.")
        st.stop()

# --- 3. Sidebar Navigation & Global Metrics ---
st.sidebar.title("✨ Routine Hub")

move_date = date(2026, 8, 22)
days_left = (move_date - date.today()).days
st.sidebar.metric(label="🗓️ Days Until Move", value=days_left)

best_streak = int(df['Streak'].max()) if not df.empty else 0
st.sidebar.metric(label="Best Active Streak", value=f"{best_streak}d {streak_badge(best_streak)}")

st.sidebar.divider()
page = st.sidebar.radio("Navigation", ["📝 Daily Checklist", "📊 Analytics", "⚙️ Manage Tasks"])

# --- 4. Page: Daily Checklist ---
if page == "📝 Daily Checklist":
    st.title("Today's Action Plan 🎯")
    st.write(f"**{date.today().strftime('%A, %B %d')}**")

    completed_count = int(df['Completed'].sum())
    total_tasks = len(df)
    progress_pct = int((completed_count / total_tasks) * 100) if total_tasks > 0 else 0

    st.progress(progress_pct, text=f"Daily Progress: {progress_pct}%")
    if progress_pct == 100 and total_tasks > 0:
        st.balloons()

    st.divider()
    updated = False

    # Tasks are grouped into colorful category sections, each rendered as a card
    for cat, color in CATEGORIES.items():
        cat_tasks = df[df['Category'] == cat]
        if cat_tasks.empty:
            continue
        st.markdown(f"<h4 style='color:{color}; margin-bottom:4px;'>{cat}</h4>", unsafe_allow_html=True)

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
                        f"<div style='text-align:right; padding-top:6px;'>{pri_emoji} {streak_txt}</div>",
                        unsafe_allow_html=True,
                    )
            if checked != row['Completed']:
                df.at[index, 'Completed'] = checked
                updated = True
                if checked:
                    st.toast(random.choice(CHEER_MESSAGES))

    if updated:
        conn.update(data=df)
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.write("### ➕ Add a Task")
    with st.form("add_task_form", clear_on_submit=True):
        new_task = st.text_input("New task name:", placeholder="e.g., Water the plants 🌱")
        c1, c2 = st.columns(2)
        with c1:
            new_cat = st.selectbox("Category", list(CATEGORIES.keys()))
        with c2:
            new_pri = st.selectbox("Priority", list(PRIORITIES.keys()), index=1)
        # 'type="primary"' makes the button stand out with a solid color
        submitted = st.form_submit_button("Add to list", type="primary")
        if submitted and new_task:
            new_row = pd.DataFrame({
                "Task": [new_task], "Category": [new_cat], "Priority": [new_pri],
                "Completed": [False], "Date": [str(date.today())],
                "Streak": [0], "LastCompletedDate": [""],
            })
            df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=df)
            st.cache_data.clear()
            st.rerun()

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
                             scale=alt.Scale(domain=["Completed", "Pending"], range=["#6BCB77", "#FF6B6B"]),
                             legend=alt.Legend(title="Status")),
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
            line={"color": "#845EC2", "size": 2},
            color=alt.Gradient(gradient="linear", stops=[
                alt.GradientStop(color="white", offset=0),
                alt.GradientStop(color="#845EC2", offset=1)], x1=1, x2=1, y1=1, y2=0),
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
        conn.update(data=df)
        st.cache_data.clear()
        st.success("Changes saved!")
        st.rerun()

    st.divider()
    st.write("#### 🗑️ Delete Tasks")
    # Creates a clean dropdown where you can click multiple tasks to tag them for deletion
    tasks_to_delete = st.multiselect("Select tasks to delete:", df['Task'].tolist())

    if st.button("Delete Selected Tasks", type="primary"):
        if tasks_to_delete:
            # Filters the dataframe to keep only the tasks NOT in the deletion list
            df = df[~df['Task'].isin(tasks_to_delete)].reset_index(drop=True)
            conn.update(data=df)
            st.cache_data.clear()
            st.success("Tasks removed successfully!")
            st.rerun()
        else:
            st.warning("Please select at least one task to delete.")
