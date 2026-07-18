import streamlit as st
import pandas as pd
import altair as alt
from datetime import date
from streamlit_gsheets import GSheetsConnection

# 'layout="centered"' keeps the UI tight and readable on both phones and monitors
st.set_page_config(page_title="Daily Routine", page_icon="✨", layout="centered")

# --- 1. Database Connection & Load ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    df = conn.read(ttl=0)
    
    if df.empty:
        # Added emojis to the default tasks for a cleaner UI
        tasks = [
            "💪 Ab roller & core training",
            "🏋️ Goblet squats",
            "🥩 Track daily protein intake",
            "🍱 Prep chicken, rice, and peas",
            "💻 Review Python/PySpark notes",
            "📦 Sort living room boxes"
        ]
        df = pd.DataFrame({
            "Task": tasks,
            "Completed": [False] * len(tasks),
            "Date": [str(date.today())] * len(tasks)
        })
        conn.update(data=df)
        st.cache_data.clear()
        return df

    # Force Boolean formatting to prevent pandas crashes
    df['Completed'] = df['Completed'].astype(str).str.upper() == 'TRUE'

    # The Daily Reset Logic
    if str(df['Date'].iloc[0]) != str(date.today()):
        df['Completed'] = False
        df['Date'] = str(date.today())
        conn.update(data=df)
        st.cache_data.clear()
        
    return df

df = load_data()

# --- 2. Sidebar Navigation & Global Metrics ---
st.sidebar.title("✨ Routine Hub")

# The countdown is moved to the sidebar so it is always visible
move_date = date(2026, 8, 22)
days_left = (move_date - date.today()).days
st.sidebar.metric(label="🗓️ Days Until Move", value=days_left)
st.sidebar.divider()

# Creates the navigation links
page = st.sidebar.radio("Navigation", ["📝 Daily Checklist", "📊 Analytics", "⚙️ Manage Tasks"])

# --- 3. Page: Daily Checklist ---
if page == "📝 Daily Checklist":
    st.title("Today's Action Plan 🎯")
    st.write(f"**{date.today().strftime('%A, %B %d')}**")
    
    completed_count = df['Completed'].sum()
    total_tasks = len(df)
    progress_pct = int((completed_count / total_tasks) * 100) if total_tasks > 0 else 0
    
    st.progress(progress_pct, text=f"Daily Progress: {progress_pct}%")
    if progress_pct == 100 and total_tasks > 0:
        st.balloons()
        
    st.divider()

    updated = False
    st.write("### ✅ Your Tasks")
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
    
    st.write("### ➕ Add a Task")
    new_task = st.text_input("New task name:", placeholder="e.g., Water the plants 🌱")
    # 'type="primary"' makes the button stand out with a solid color
    if st.button("Add to list", type="primary"):
        if new_task:
            new_row = pd.DataFrame({"Task": [new_task], "Completed": [False], "Date": [str(date.today())]})
            df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=df)
            st.cache_data.clear()
            st.rerun()

# --- 4. Page: Analytics ---
elif page == "📊 Analytics":
    st.title("Performance Analytics 📈")
    st.write("Visualizing your completion rate for today.")
    
    completed_count = df['Completed'].sum()
    total_tasks = len(df)
    pending_count = total_tasks - completed_count
    
    col1, col2 = st.columns(2)
    col1.metric("Tasks Completed", f"{completed_count}")
    col2.metric("Tasks Pending", f"{pending_count}")
    
    st.divider()
    
    if total_tasks > 0:
        chart_data = pd.DataFrame({
            "Status": ["Completed", "Pending"],
            "Count": [completed_count, pending_count]
        })
        
        # Build a modern donut chart
        base = alt.Chart(chart_data).encode(
            theta=alt.Theta("Count:Q", stack=True),
            color=alt.Color("Status:N", scale=alt.Scale(domain=["Completed", "Pending"], range=["#28a745", "#dc3545"]), legend=alt.Legend(title="Task Status"))
        ).properties(height=400)
        
        pie = base.mark_arc(innerRadius=60)
        st.altair_chart(pie, use_container_width=True)
    else:
        st.info("No tasks available to track.")

# --- 5. Page: Manage Tasks ---
elif page == "⚙️ Manage Tasks":
    st.title("Task Management 🗑️")
    st.write("Select the tasks you want to permanently remove from your routine.")
    
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
