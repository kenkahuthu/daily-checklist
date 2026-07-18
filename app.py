import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Daily Routine", page_icon="✅")
st.title("Daily Routine ✅")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    df = conn.read(ttl=0)
    
    if df.empty:
        tasks = [
            "Ab roller & core training",
            "Prep chicken, rice, and peas",
            "Review Python/PySpark notes"
        ]
        df = pd.DataFrame({
            "Task": tasks,
            "Completed": [False] * len(tasks),
            "Date": [str(date.today())] * len(tasks)
        })
        conn.update(data=df)
        st.cache_data.clear()
        return df

    if df['Date'].iloc[0] != str(date.today()):
        df['Completed'] = False
        df['Date'] = str(date.today())
        conn.update(data=df)
        st.cache_data.clear()
        
    return df

df = load_data()
st.write(f"### {date.today().strftime('%A, %B %d')}")

updated = False
for index, row in df.iterrows():
    checked = st.checkbox(row['Task'], value=row['Completed'], key=row['Task'])
    if checked != row['Completed']:
        df.at[index, 'Completed'] = checked
        updated = True

if updated:
    conn.update(data=df)
    st.cache_data.clear()
    st.rerun()