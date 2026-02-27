import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def _hover_template() -> str:
    return (
        "Time: %{customdata[0]}<br>"
        "Date: %{customdata[1]}<br>"
        "Run #: %{customdata[2]}<br>"
        "Age grade: %{customdata[3]:.1f}%<br>"
        "Position: %{customdata[4]}<br>"
        "Event: %{customdata[5]}<extra></extra>"
    )


def _make_customdata(df_plot: pd.DataFrame):
    date_str = df_plot["run_date"].dt.strftime("%d/%m/%y")
    event_col = (
        df_plot["event"].fillna("—").astype(str)
        if "event" in df_plot.columns
        else (["—"] * len(df_plot))
    )
    return list(
        zip(
            df_plot["time_str"].fillna("—").astype(str),
            date_str.astype(str),
            df_plot["run_index"].astype(int),
            df_plot["age_grade"].fillna(0).astype(float),
            df_plot["position"].fillna(0).astype(int),
            event_col,
        )
    )


def render_analytics_charts(
    athletes,
    athlete_dfs,
    start_date,
    end_date,
    x_col: str,
    x_title: str,
    y_col: str,
    y_title: str,
):
    """Render all analytics visuals (line chart, distributions, monthly charts)."""
    hover_template = _hover_template()

    # ----- Line chart -----
    st.markdown("#### Line chart")
    st.caption("Trend of the selected metric over time or run number for all selected runners.")
    fig_line = go.Figure()
    colors = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#3A7D44"]
    for idx, a in enumerate(athletes):
        aid, aname = a["id"], a["name"]
        if aid not in athlete_dfs:
            continue
        df_a = athlete_dfs[aid]
        mask = (df_a["run_date"].dt.date >= start_date) & (
            df_a["run_date"].dt.date <= end_date
        )
        df_plot = df_a.loc[mask].sort_values(x_col).reset_index(drop=True)
        if df_plot.empty or y_col not in df_plot.columns or x_col not in df_plot.columns:
            continue
        if x_col == "run_date":
            x_vals = df_plot["run_date"].tolist()
        else:
            x_vals = df_plot["run_index"].astype(int).tolist()
        y_series = df_plot[y_col]
        y_vals = [float(x) if pd.notna(x) and np.isfinite(x) else np.nan for x in y_series]
        fig_line.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines+markers",
                name=aname,
                line=dict(color=colors[idx % len(colors)], width=2),
                marker=dict(size=6),
                customdata=_make_customdata(df_plot),
                hovertemplate=hover_template,
            )
        )
    fig_line.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        margin=dict(b=60),
        height=450,
    )
    if y_col == "time_min":
        fig_line.update_yaxes(tickformat=".2f", title_text="Time (minutes)")
    elif y_col == "age_grade":
        fig_line.update_yaxes(
            tickformat=".1f", ticksuffix="%", title_text="Age grade (%)"
        )
    elif y_col == "position":
        fig_line.update_yaxes(tickformat="d", title_text="Position")
    else:
        fig_line.update_yaxes(tickformat="d", title_text="Run number")
    if x_col == "run_index":
        fig_line.update_xaxes(tickformat="d", title_text="Run number")
    st.plotly_chart(fig_line, use_container_width=True)

    # ----- Time distribution (strip plot) -----
    st.markdown("#### Time distribution (strip plot)")
    st.caption("Each point is a run, showing its finish time in minutes. PBs and the latest run are highlighted.")
    fig_strip = go.Figure()
    athlete_names_in_plot = [a["name"] for a in athletes if a["id"] in athlete_dfs]

    for idx, a in enumerate(athletes):
        aid, aname = a["id"], a["name"]
        if aid not in athlete_dfs:
            continue
        df_a = athlete_dfs[aid]
        mask = (df_a["run_date"].dt.date >= start_date) & (
            df_a["run_date"].dt.date <= end_date
        )
        df_plot = df_a.loc[mask].sort_values("run_date").reset_index(drop=True)
        if df_plot.empty:
            continue

        tmin = pd.to_numeric(df_plot["time_min"], errors="coerce")
        valid = tmin.notna()
        df_plot = df_plot.loc[valid].copy()
        tmin = tmin.loc[valid]
        if df_plot.empty:
            continue

        seed = int(aid) % 100000
        run_idx = df_plot["run_index"].astype(int).values
        jitter = (((run_idx * 1103515245 + seed) % 1000) / 1000.0 - 0.5) * 0.6
        y_vals = (idx + jitter).tolist()

        fig_strip.add_trace(
            go.Scatter(
                x=tmin.tolist(),
                y=y_vals,
                mode="markers",
                name=aname,
                marker=dict(size=6, opacity=0.35),
                customdata=_make_customdata(df_plot),
                hovertemplate=hover_template,
                showlegend=False,
            )
        )

        # PBs
        pb_mask = df_plot.get("is_pb", False)
        if hasattr(pb_mask, "fillna"):
            pb_mask = pb_mask.fillna(False)
        pb_mask = pb_mask.astype(bool) if hasattr(pb_mask, "astype") else pb_mask
        if getattr(pb_mask, "any", lambda: False)():
            df_pb = df_plot.loc[pb_mask]
            if not df_pb.empty:
                pb_tmin = pd.to_numeric(df_pb["time_min"], errors="coerce")
                pb_valid = pb_tmin.notna()
                df_pb = df_pb.loc[pb_valid]
                pb_tmin = pb_tmin.loc[pb_valid]
                pb_y = [idx] * len(df_pb)
                fig_strip.add_trace(
                    go.Scatter(
                        x=pb_tmin.tolist(),
                        y=pb_y,
                        mode="markers",
                        name="PB" if idx == 0 else None,
                        marker=dict(
                            symbol="diamond",
                            size=9,
                            line=dict(width=1),
                            opacity=0.9,
                        ),
                        customdata=_make_customdata(df_pb),
                        hovertemplate="PB<br>" + hover_template,
                        showlegend=(idx == 0),
                    )
                )

        # Latest run
        latest_idx = df_plot["run_date"].idxmax()
        df_latest = df_plot.loc[[latest_idx]]
        latest_tmin = pd.to_numeric(df_latest["time_min"], errors="coerce").iloc[0]
        if pd.notna(latest_tmin):
            fig_strip.add_trace(
                go.Scatter(
                    x=[float(latest_tmin)],
                    y=[idx],
                    mode="markers",
                    name="Latest run" if idx == 0 else None,
                    marker=dict(
                        symbol="x", size=10, line=dict(width=1), opacity=0.95
                    ),
                    customdata=_make_customdata(df_latest),
                    hovertemplate="Latest run<br>" + hover_template,
                    showlegend=(idx == 0),
                )
            )

    fig_strip.update_layout(
        xaxis_title="Time (minutes)",
        yaxis_title="Runner",
        height=max(250, 120 + 40 * len(athlete_names_in_plot)),
        margin=dict(b=40),
    )
    if athlete_names_in_plot:
        fig_strip.update_yaxes(
            tickmode="array",
            tickvals=list(range(len(athlete_names_in_plot))),
            ticktext=athlete_names_in_plot,
        )
    st.plotly_chart(fig_strip, use_container_width=True)

    # ----- Age grade distribution (strip plot) -----
    st.markdown("#### Age grade distribution (strip plot)")
    st.caption(
        "Each point is a run, showing its age grade percentage. PBs and the latest run are highlighted. "
        "Age grading takes your time and uses the world record time for your gender and age to produce a score "
        "(a percentage). See the [parkrun age grading help article]"
        "(https://support.parkrun.com/hc/en-us/articles/200565263-4-5-Age-grading) for more details."
    )
    fig_age = go.Figure()

    for idx, a in enumerate(athletes):
        aid, aname = a["id"], a["name"]
        if aid not in athlete_dfs:
            continue
        df_a = athlete_dfs[aid]
        mask = (df_a["run_date"].dt.date >= start_date) & (
            df_a["run_date"].dt.date <= end_date
        )
        df_plot = df_a.loc[mask].sort_values("run_date").reset_index(drop=True)
        if df_plot.empty:
            continue

        ag = pd.to_numeric(df_plot["age_grade"], errors="coerce")
        valid = ag.notna()
        df_plot = df_plot.loc[valid].copy()
        ag = ag.loc[valid]
        if df_plot.empty:
            continue

        seed = int(aid) % 100000
        run_idx = df_plot["run_index"].astype(int).values
        jitter = (((run_idx * 1103515245 + seed) % 1000) / 1000.0 - 0.5) * 0.6
        y_vals = (idx + jitter).tolist()

        fig_age.add_trace(
            go.Scatter(
                x=ag.tolist(),
                y=y_vals,
                mode="markers",
                name=aname,
                marker=dict(size=6, opacity=0.35),
                customdata=_make_customdata(df_plot),
                hovertemplate=hover_template,
                showlegend=False,
            )
        )

        # PBs (time PB flag) highlighted on age grade distribution
        pb_mask = df_plot.get("is_pb", False)
        if hasattr(pb_mask, "fillna"):
            pb_mask = pb_mask.fillna(False)
        pb_mask = pb_mask.astype(bool) if hasattr(pb_mask, "astype") else pb_mask
        if getattr(pb_mask, "any", lambda: False)():
            df_pb = df_plot.loc[pb_mask]
            if not df_pb.empty:
                pb_ag = pd.to_numeric(df_pb["age_grade"], errors="coerce")
                pb_valid = pb_ag.notna()
                df_pb = df_pb.loc[pb_valid]
                pb_ag = pb_ag.loc[pb_valid]
                pb_y = [idx] * len(df_pb)
                fig_age.add_trace(
                    go.Scatter(
                        x=pb_ag.tolist(),
                        y=pb_y,
                        mode="markers",
                        name="PB (time)" if idx == 0 else None,
                        marker=dict(
                            symbol="diamond",
                            size=9,
                            line=dict(width=1),
                            opacity=0.9,
                        ),
                        customdata=_make_customdata(df_pb),
                        hovertemplate="PB (time)<br>" + hover_template,
                        showlegend=(idx == 0),
                    )
                )

        # Latest run
        latest_idx = df_plot["run_date"].idxmax()
        df_latest = df_plot.loc[[latest_idx]]
        latest_ag = pd.to_numeric(df_latest["age_grade"], errors="coerce").iloc[0]
        if pd.notna(latest_ag):
            fig_age.add_trace(
                go.Scatter(
                    x=[float(latest_ag)],
                    y=[idx],
                    mode="markers",
                    name="Latest run" if idx == 0 else None,
                    marker=dict(
                        symbol="x", size=10, line=dict(width=1), opacity=0.95
                    ),
                    customdata=_make_customdata(df_latest),
                    hovertemplate="Latest run<br>" + hover_template,
                    showlegend=(idx == 0),
                )
            )

    fig_age.update_layout(
        xaxis_title="Age grade (%)",
        yaxis_title="Runner",
        height=max(250, 120 + 40 * len(athlete_names_in_plot)),
        margin=dict(b=40),
    )
    fig_age.update_xaxes(tickformat=".1f", ticksuffix="%")
    if athlete_names_in_plot:
        fig_age.update_yaxes(
            tickmode="array",
            tickvals=list(range(len(athlete_names_in_plot))),
            ticktext=athlete_names_in_plot,
        )
    st.plotly_chart(fig_age, use_container_width=True)

    # ----- Monthly runs per athlete (stacked) -----
    st.markdown("#### Monthly runs per athlete (stacked)")
    st.caption("Number of 5k parkruns completed in each calendar month, stacked by runner.")
    months = list(range(1, 13))
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    fig_month_counts = go.Figure()

    for a in athletes:
        aid, aname = a["id"], a["name"]
        if aid not in athlete_dfs:
            continue
        df_a = athlete_dfs[aid]
        mask = (df_a["run_date"].dt.date >= start_date) & (
            df_a["run_date"].dt.date <= end_date
        )
        df_plot = df_a.loc[mask].copy()
        if df_plot.empty:
            counts = pd.Series(0, index=months)
        else:
            month_series = df_plot["run_date"].dt.month
            counts = month_series.value_counts().reindex(months, fill_value=0)

        fig_month_counts.add_trace(
            go.Bar(
                x=month_labels,
                y=counts.values.tolist(),
                name=aname,
            )
        )

    fig_month_counts.update_layout(
        barmode="stack",
        yaxis_title="Number of runs",
        height=400,
    )
    st.plotly_chart(fig_month_counts, use_container_width=True)

    # ----- Monthly distance per athlete (stacked, km) -----
    st.markdown("#### Monthly distance per athlete (stacked, km)")
    st.caption("Total distance in kilometres (5 km per parkrun) completed in each month, stacked by runner.")
    fig_month_km = go.Figure()

    for a in athletes:
        aid, aname = a["id"], a["name"]
        if aid not in athlete_dfs:
            continue
        df_a = athlete_dfs[aid]
        mask = (df_a["run_date"].dt.date >= start_date) & (
            df_a["run_date"].dt.date <= end_date
        )
        df_plot = df_a.loc[mask].copy()
        if df_plot.empty:
            counts = pd.Series(0, index=months)
        else:
            month_series = df_plot["run_date"].dt.month
            counts = month_series.value_counts().reindex(months, fill_value=0)

        km_vals = (counts * 5).values

        fig_month_km.add_trace(
            go.Bar(
                x=month_labels,
                y=km_vals.tolist(),
                name=aname,
            )
        )

    fig_month_km.update_layout(
        barmode="stack",
        yaxis_title="Distance (km)",
        height=400,
    )
    st.plotly_chart(fig_month_km, use_container_width=True)

