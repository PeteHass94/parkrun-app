"""
parkrun Analytics — Athlete list, summaries, and charts.
"""

import numpy as np
import pandas as pd
import streamlit as st

from parkrun_scraper import fetch_parkrunner_results
from visuals.analytics_charts import render_analytics_charts

st.set_page_config(
    page_title="Analytics | parkrun",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

@st.cache_data(ttl=300)
def load_athlete(athlete_id: str):
    return fetch_parkrunner_results(athlete_id)

# ----- Session state: list of athletes {id, name} -----
if "athletes" not in st.session_state:
    st.session_state["athletes"] = []

primary_id = st.session_state.get("primary_athlete_id", "").strip()
# If we have a primary from Home but no athletes yet, fetch and add that one
if primary_id and not st.session_state["athletes"]:
    with st.spinner("Loading your results..."):
        df, name, err = load_athlete(primary_id)
    if err:
        st.error(err)
        st.stop()
    st.session_state["athletes"] = [{"id": primary_id, "name": name}]
    st.rerun()

athletes = st.session_state["athletes"]
if not athletes:
    st.info("Enter your athlete number on the **Home** page, then come back here.")
    if st.button("Go to Home"):
        st.switch_page("Home.py")
    st.stop()

def fmt_time(sec):
    if sec is None or pd.isna(sec):
        return "—"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

st.title("📊 parkrun Analytics")
st.markdown("---")

# ----- Tag list: athletes as tags with Remove (horizontal row) -----
st.subheader("Runners")
st.caption("All runners currently included in the analysis. You can remove anyone from this list.")
if athletes:
    tag_cols = st.columns(len(athletes))
    for i, a in enumerate(athletes):
        aid, aname = a["id"], a["name"]
        with tag_cols[i]:
            st.markdown(f"**{aname}** _(#{aid})_")
            if st.button("Remove", key=f"tag_remove_{aid}", type="secondary"):
                st.session_state["athletes"] = [x for x in athletes if x["id"] != aid]
                st.rerun()

# ----- Add runner -----
st.markdown("#### Add runner")
st.caption("Add another runner by their parkrun athlete number so they appear in all charts and summaries.")
add_col1, add_col2 = st.columns([2, 1])

if "new_athlete_id" not in st.session_state:
    st.session_state["new_athlete_id"] = ""
# Clear the input on the run *after* a successful add
if st.session_state.pop("clear_new_athlete_id", False):
    st.session_state["new_athlete_id"] = ""

with add_col1:
    new_id = st.text_input("Athlete number", placeholder="e.g. 2099834", key="new_athlete_id", label_visibility="collapsed").strip()
with add_col2:
    add_btn = st.button("Add", type="primary", use_container_width=True)

if add_btn:
    if not new_id or not new_id.isdigit():
        st.warning("Please enter a valid athlete number (digits only).")
    elif any(a["id"] == new_id for a in athletes):
        st.warning("That runner is already in the list.")
    else:
        with st.spinner("Loading..."):
            df_new, name_new, err_new = load_athlete(new_id)
        if err_new:
            st.warning(f"Could not add: {err_new}")
        else:
            st.session_state["athletes"] = athletes + [{"id": new_id, "name": name_new}]
            # Ask next run to clear the input
            st.session_state["clear_new_athlete_id"] = True
            st.rerun()

st.markdown("---")

# ----- Load all data and compute global date range -----
athlete_dfs = {}
for a in athletes:
    aid = a["id"]
    df_a, name_a, err_a = load_athlete(aid)
    if err_a:
        st.warning(f"{a['name']}: {err_a}")
        continue
    df_a = df_a.copy()
    df_a["run_date"] = pd.to_datetime(df_a["run_date"])
    df_a = df_a.sort_values("run_date").reset_index(drop=True)
    df_a["run_index"] = np.arange(1, len(df_a) + 1, dtype=int)
    df_a["time_min"] = pd.to_numeric(df_a["time_sec"], errors="coerce") / 60
    athlete_dfs[aid] = df_a

if not athlete_dfs:
    st.error("No runner data available.")
    st.stop()

all_dates = pd.concat([df["run_date"] for df in athlete_dfs.values()])
min_date = all_dates.min().date()
max_date = all_dates.max().date()

# ----- Summary by runner -----
st.subheader("Summary by runner")
st.caption("High-level stats for each runner across all of their recorded parkruns.")
for a in athletes:
    aid, aname = a["id"], a["name"]
    if aid not in athlete_dfs:
        continue
    df_a = athlete_dfs[aid]
    total = len(df_a)
    best_sec = df_a["time_sec"].min()
    avg_sec = df_a["time_sec"].mean()
    best_ag = df_a["age_grade"].max()
    avg_pos = df_a["position"].mean()
    cols = st.columns([2, 1, 1, 1, 1, 1, 1])
    cols[0].markdown(f"**{aname}** _(#{aid})_")
    cols[1].metric("Total runs", total)
    cols[2].metric("Best time", fmt_time(best_sec))
    cols[3].metric("Average time", fmt_time(avg_sec))
    cols[4].metric("Best age grade", f"{best_ag:.1f}%" if best_ag else "—")
    cols[5].metric("Avg position", f"{avg_pos:.0f}" if not pd.isna(avg_pos) else "—")
    with cols[6]:
        if st.button("Remove", key=f"summary_remove_{aid}"):
            st.session_state["athletes"] = [x for x in athletes if x["id"] != aid]
            st.rerun()
    st.markdown("---")




# ----- Analysis: date slider then metric then charts -----
st.subheader("Run Analysis")
st.caption("Set a date range and choose which metric and x-axis to use, then explore detailed charts below.")

start_date, end_date = st.slider(
    "Date range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="DD/MM/YYYY",
)

col_metric, col_xaxis = st.columns(2)
with col_metric:
    metric = st.selectbox(
        "Y-axis (metric to plot)",
        ["Time (minutes)", "Age grade (%)", "Position", "Run number (chronological)"],
        index=0,
    )
with col_xaxis:
    x_axis = st.selectbox(
        "X-axis",
        ["Date", "Run number"],
        index=0,
    )

if metric == "Time (minutes)":
    y_col, y_title = "time_min", "Time (minutes)"
elif metric == "Age grade (%)":
    y_col, y_title = "age_grade", "Age grade (%)"
elif metric == "Position":
    y_col, y_title = "position", "Position"
else:
    y_col, y_title = "run_index", "Run number"

if x_axis == "Date":
    x_col, x_title = "run_date", "Date"
else:
    x_col, x_title = "run_index", "Run number"

#
# Data table of the exact points used in the charts below.
#
with st.expander("Raw data (points plotted)"):
    for a in athletes:
        aid, aname = a["id"], a["name"]
        if aid not in athlete_dfs:
            continue
        df_a = athlete_dfs[aid]
        mask = (df_a["run_date"].dt.date >= start_date) & (df_a["run_date"].dt.date <= end_date)
        df_plot = df_a.loc[mask].sort_values(x_col).reset_index(drop=True)
        if df_plot.empty or y_col not in df_plot.columns or x_col not in df_plot.columns:
            continue

        display_df = pd.DataFrame()
        if x_col == "run_date":
            display_df[x_title] = df_plot["run_date"].dt.strftime("%d/%m/%Y").values
        else:
            display_df[x_title] = df_plot["run_index"].astype(int).values

        display_df[y_title] = pd.to_numeric(df_plot[y_col], errors="coerce").values
        if "event" in df_plot.columns:
            display_df.insert(1, "Event", df_plot["event"].fillna("—").astype(str).values)
        display_df.insert(2 if "event" in df_plot.columns else 1, "Time", df_plot["time_str"].astype(str).values)
        display_df["Age grade (%)"] = pd.to_numeric(df_plot["age_grade"], errors="coerce").values
        display_df["Position"] = pd.to_numeric(df_plot["position"], errors="coerce").fillna(0).astype(int).values
        display_df["PB"] = df_plot.get("is_pb", False)

        st.markdown(f"**{aname}**")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.markdown("")

render_analytics_charts(
    athletes=athletes,
    athlete_dfs=athlete_dfs,
    start_date=start_date,
    end_date=end_date,
    x_col=x_col,
    x_title=x_title,
    y_col=y_col,
    y_title=y_title,
)

st.markdown("---")
st.caption("Data from parkrun.org.uk. Use for personal, non-commercial use only.")
