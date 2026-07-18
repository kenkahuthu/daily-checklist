import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Daily Routine", page_icon="✅")

# 1. Connect to Database
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    df = conn.read(ttl=0)
    
    # Inject default tasks if the sheet is completely empty
    if df.empty:
        tasks = [
            "Ab roller & core training",
            "Goblet squats",
            "Track daily protein intake",
            "Prep chicken, rice, and peas",
            "Review Python/PySpark notes",
            "Sort living room boxes"
        ]
        df = pd.DataFrame({
            "Task": tasks,
            "Completed": [False] * len(tasks),
            "Date": [str(date.today())] * len(tasks)
        })
        conn.update(data=df)
        st.cache_data.clear()
        return df

    # The Daily Reset Logic
    if df['Date'].iloc[0] != str(date.today()):
        df['Completed'] = False
        df['Date'] = str(date.today())
        conn.update(data=df)
        st.cache_data.clear()
        
    return df

df = load_data()

# 2. Header & Countdown Widget
move_date = date(2026, 8, 22)
days_left = (move_date - date.today()).days

col1, col2 = st.columns([3, 1])
with col1:
    st.title("Daily Routine ✅")
    st.write(f"### {date.today().strftime('%A, %B %d')}")
with col2:
    st.metric(label="Days Until Move", value=days_left)

# 3. Progress Bar & Balloons
completed_count = df['Completed'].sum()
total_tasks = len(df)
progress_pct = int((completed_count / total_tasks) * 100) if total_tasks > 0 else 0

st.progress(progress_pct, text=f"Daily Progress: {progress_pct}%")
if progress_pct == 100 and total_tasks > 0:
    st.balloons()

st.divider()

# 4. Render Checkboxes
updated = False
for index, row in df.iterrows():
    checked = st.checkbox(row['Task'], value=row['Completed'], key=f"task_{index}")
    if checked != row['Completed']:
        df.at[index, 'Completed'] = checked
        updated = True

if updated:
    conn.update(data=df)
    st.cache_data.clear()
    st.rerun()

st.divider()

# 5. Add New Task Feature
st.write("### Add a one-off task")
new_task = st.text_input("Task name:")
if st.button("Add to list"):
    if new_task:
        new_row = pd.DataFrame({"Task": [new_task], "Completed": [False], "Date": [str(date.today())]})
        df = pd.concat([df, new_row], ignore_index=True)
        conn.update(data=df)
        st.cache_data.clear()
        st.rerun()
