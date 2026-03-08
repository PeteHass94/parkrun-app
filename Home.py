"""
parkrun Analytics — Home
Welcome and explainer; enter your athlete ID to open analytics.

cd "parkrun app"
pip install -r requirements.txt
streamlit run Home.py

conda create --name streamlit_env
conda activate streamlit_env
pip install -r requirements.txt
streamlit run Home.py
"""

import streamlit as st

st.set_page_config(
    page_title="Parkrun Analytics",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("🏃 Parkrun Analytics")
st.markdown("---")

st.markdown("""
Welcome to **Parkrun Analytics**. This app fetches your (or any Parkrunner's) public results from 
[parkrun UK](https://www.parkrun.org.uk) and lets you explore your runs over time and compare with friends or family.

### How to use

1. **Find your athlete number**  
   This can be found on your barcode or in your parkrun profile page. It normally starts with an "A" but this app only needs the numeric part.  
   It’s used in the URL for your results page on parkrun.org.uk:  
   For example, my parkrun results page is `https://www.parkrun.org.uk/parkrunner/2099834/all/`  
   so my athlete number is **2099834**.

2. **Enter your number below** and click **View my analytics**.

### Data and privacy

- This app only reads **public parkrun results pages** based on the athlete number you enter.  
- No data is persisted to disk or sent to any external service; everything is processed in memory while the app is running in your browser session.  
- You can close the browser tab at any time to clear the current analysis.

### Official parkrun app

- To find your **nearest parkrun**, discover new events, and follow your friends' results, try the official [parkrun app](https://www.parkrun.com/app/).
""")

st.markdown("---")
st.caption("⚠️ The app may not load data on Saturdays or other run days when parkrun’s servers are busy. If it fails, try again later.")
st.subheader("Enter your parkrun athlete number")

if "primary_athlete_id" not in st.session_state:
    st.session_state["primary_athlete_id"] = ""
if "athlete_input" not in st.session_state:
    st.session_state["athlete_input"] = st.session_state.get("primary_athlete_id", "")

# Autofill: set input before widget runs (on_click sets flag; we apply it next run)
if st.session_state.pop("do_autofill", None):
    st.session_state["athlete_input"] = "2099834"
    st.rerun()

col1, col2, col3 = st.columns([2, 0.35, 1])
with col1:
    athlete_id = st.text_input(
        "Athlete number",
        placeholder="e.g. 2099834",
        label_visibility="collapsed",
        key="athlete_input",
    ).strip()
with col2:
    st.button("✏️", key="autofill_btn", use_container_width=True, help="Autofill with 2099834", on_click=lambda: st.session_state.update(do_autofill=True))
with col3:
    go_btn = st.button("View my analytics", type="primary", use_container_width=True)

if go_btn:
    if not athlete_id or not athlete_id.isdigit():
        st.warning("Please enter a valid athlete number (digits only).")
    else:
        st.session_state["primary_athlete_id"] = athlete_id
        st.switch_page("pages/1_analytics.py")

st.markdown("---")
st.caption(
    "parkrun® is a registered trademark. This app is not affiliated with parkrun. "
    "Data is fetched from public parkrun pages for personal, non-commercial use only. "
    "No result data is stored by this app."
)
