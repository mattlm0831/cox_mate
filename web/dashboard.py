import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from cox_mate.database import DatabaseManager
import pandas as pd
import os

BASE_DIR = Path(__file__).parent.parent
SCREENSHOT_DIR = BASE_DIR / "test_screenshots"
DB_PATH = BASE_DIR / "cox_tracker.db"

db = DatabaseManager(str(DB_PATH))
raids = db.get_all_raids()

st.set_page_config(page_title="COX Mate Dashboard", layout="wide")
st.title("COX Mate - Chambers of Xeric Stats")

# Sidebar navigation
page = st.sidebar.radio("Navigate", ["Dashboard", "Points Over Time", "Purple Drops", "Image Gallery", "Dry Streaks", "Score New Images"])

if page == "Dashboard":
    st.header("Recent Raids")
    df = pd.DataFrame([r.to_dict() for r in raids])
    if not df.empty:
        df["date_completed"] = pd.to_datetime(df["date_completed"])
        st.dataframe(df.sort_values("date_completed", ascending=False).head(20))
    else:
        st.info("No raids found.")

elif page == "Points Over Time":
    st.header("Points Over Time")
    df = pd.DataFrame([r.to_dict() for r in raids if r.date_completed and r.points])
    if not df.empty:
        df["date_completed"] = pd.to_datetime(df["date_completed"])
        st.line_chart(df.set_index("date_completed")["points"])
    else:
        st.info("No points data available.")

elif page == "Purple Drops":
    st.header("Purple Drops Timeline")
    purples = [r for r in raids if r.is_purple]
    if purples:
        for r in purples:
            st.write(f"{r.date_completed}: {r.item_list}")
            if r.image_path and (SCREENSHOT_DIR / Path(r.image_path).name).exists():
                st.image(str(SCREENSHOT_DIR / Path(r.image_path).name), width=300)
    else:
        st.info("No purple drops found.")

elif page == "Image Gallery":
    st.header("Image Gallery")
    images = [(r, SCREENSHOT_DIR / Path(r.image_path).name) for r in raids if r.image_path and (SCREENSHOT_DIR / Path(r.image_path).name).exists()]
    for r, img_path in images:
        st.image(str(img_path), caption=f"{r.date_completed} | Points: {r.points} | {'🟣' if r.is_purple else '⚪'}", width=200)

elif page == "Dry Streaks":
    st.header("Longest Dry Streaks")
    streaks = []
    current = 0
    for r in raids:
        if r.is_purple:
            if current > 0:
                streaks.append(current)
            current = 0
        else:
            current += 1
    if current > 0:
        streaks.append(current)
    longest = max(streaks) if streaks else 0
    st.write(f"Longest dry streak: {longest} raids")
    st.bar_chart(pd.Series(streaks))

elif page == "Score New Images":
    st.header("Score New Images")
    gemini_key = st.text_input("Gemini API Key", type="password")
    if st.button("Start Scoring Run"):
        st.info("Scoring run would be triggered here (implement logic as needed).")
        # TODO: Call your scoring logic here
