"""
Eco-Intelligent AI - Campus Energy Dashboard
Hackathon build: SW-05 - Eco-Intelligent AI & Sustainable Tech

Run:
    streamlit run app.py
"""

import os
import subprocess

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from ai_insights import get_insight
from forecast import get_building_analysis, load_data

load_dotenv()

st.set_page_config(page_title="Eco-Intelligent AI", page_icon="🌱", layout="wide")

DATA_PATH = "data/energy_usage.csv"
CO2_KG_PER_KWH = 0.71  # approx grid emission factor, adjust for your region


@st.cache_data
def ensure_data():
    if not os.path.exists(DATA_PATH):
        subprocess.run(["python", "data_generator.py"], check=True)
    return load_data(DATA_PATH)


def render_header():
    st.title("🌱 Eco-Intelligent AI")
    st.caption(
        "AI-powered energy monitoring for campuses — Problem Statement SW-05: "
        "Eco-Intelligent AI & Sustainable Tech"
    )


def render_sidebar(buildings):
    st.sidebar.header("Controls")
    building = st.sidebar.selectbox("Select Building", buildings)
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**AI Insights**: powered by Groq's free API. "
        "Set `GROQ_API_KEY` in a `.env` file to enable live AI explanations "
        "(works with a template fallback otherwise)."
    )
    return building


def render_chart(historical: pd.DataFrame, forecast: pd.DataFrame):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=historical["timestamp"], y=historical["usage_kwh"],
        mode="lines", name="Actual Usage", line=dict(color="#2E8B57"),
    ))

    anomalies = historical[historical["is_anomaly"]]
    fig.add_trace(go.Scatter(
        x=anomalies["timestamp"], y=anomalies["usage_kwh"],
        mode="markers", name="Anomaly", marker=dict(color="red", size=10, symbol="x"),
    ))

    fig.add_trace(go.Scatter(
        x=forecast["timestamp"], y=forecast["predicted_kwh"],
        mode="lines", name="Forecast (next 72h)", line=dict(color="#1f77b4", dash="dash"),
    ))

    fig.update_layout(
        height=450,
        xaxis_title="Time",
        yaxis_title="Usage (kWh)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_metrics(historical, forecast, anomaly_count):
    total_recent = historical["usage_kwh"].tail(24).sum()
    forecast_total = forecast["predicted_kwh"].head(24).sum()
    potential_savings_kwh = anomaly_count * historical["usage_kwh"].mean() * 0.3
    co2_saved = potential_savings_kwh * CO2_KG_PER_KWH

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Last 24h Usage", f"{total_recent:.0f} kWh")
    c2.metric("Next 24h (Predicted)", f"{forecast_total:.0f} kWh")
    c3.metric("Anomalies Detected", anomaly_count)
    c4.metric("Potential CO₂ Savings", f"{co2_saved:.1f} kg", help="If flagged anomalies were addressed")


def render_ai_insights(historical, building):
    anomalies = historical[historical["is_anomaly"]].tail(5)

    if anomalies.empty:
        st.success("No anomalies detected in the recent window for this building.")
        return

    st.subheader("🤖 AI-Generated Insights")
    for _, row in anomalies.iterrows():
        with st.expander(f"Anomaly at {row['timestamp']} — {row['usage_kwh']:.1f} kWh"):
            if st.button("Generate AI Insight", key=f"btn_{row['timestamp']}"):
                with st.spinner("Analyzing pattern..."):
                    insight = get_insight(
                        building=building,
                        usage=row["usage_kwh"],
                        baseline=row["rolling_mean"] if pd.notna(row["rolling_mean"]) else row["usage_kwh"] / 2,
                        timestamp=str(row["timestamp"]),
                    )
                st.info(insight)


def main():
    render_header()
    df = ensure_data()
    buildings = sorted(df["building"].unique())
    building = render_sidebar(buildings)

    analysis = get_building_analysis(df, building)
    historical, forecast, anomaly_count = (
        analysis["historical"], analysis["forecast"], analysis["anomaly_count"]
    )

    render_metrics(historical, forecast, anomaly_count)
    st.markdown("---")
    render_chart(historical, forecast)
    st.markdown("---")
    render_ai_insights(historical, building)


if __name__ == "__main__":
    main()
