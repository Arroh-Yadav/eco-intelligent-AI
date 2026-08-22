# 🌱 Eco-Intelligent AI

**Hackathon Track:** SW-05 — Eco-Intelligent AI & Sustainable Tech

An AI-powered dashboard that monitors campus building energy usage, forecasts
future consumption, automatically flags anomalies (e.g. equipment left
running after hours), and generates plain-English recommendations for
facilities staff — turning raw sensor data into immediate, actionable steps
toward lower campus energy waste and carbon emissions.

## How it works

1. **Data layer** — hourly energy usage per building (synthetic data with
   realistic daily/weekly seasonality; swap in real sensor data later).
2. **Forecasting** — Holt-Winters exponential smoothing predicts the next
   72 hours of usage per building.
3. **Anomaly detection** — a rolling mean/std model flags usage spikes that
   deviate significantly from a building's normal pattern.
4. **AI insight layer** — each detected anomaly is sent to a free LLM API
   (Groq) which explains the likely cause and suggests one concrete action.
   Works without any API key too (falls back to a template-based insight).
5. **Dashboard** — Streamlit + Plotly, with an impact estimate showing
   potential kWh / CO₂ savings if flagged anomalies are addressed.

## Quickstart

```bash
# 1. Clone and enter the repo
git clone https://github.com/Arroh-Yadav/eco-intelligent-AI.git
cd eco-intelligent-AI

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional but recommended) enable live AI insights
cp .env.example .env
# then paste a free key from https://console.groq.com into .env

# 5. Generate the demo dataset
python data_generator.py

# 6. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Getting a free AI API key (no subscription, no credit card)

This project defaults to **Groq** because it's free, fast, and requires no
payment method:

1. Go to https://console.groq.com
2. Sign up / log in
3. Create an API key
4. Put it in your `.env` file as `GROQ_API_KEY=your_key_here`

No key? The app still runs fully — `ai_insights.py` automatically falls
back to a rule-based insight so the dashboard is never broken during a demo.

## Project structure

```
eco-intelligent-AI/
├── app.py              # Streamlit dashboard (entry point)
├── data_generator.py   # Synthetic campus energy data generator
├── forecast.py         # Forecasting + anomaly detection
├── ai_insights.py       # AI-generated recommendations (Groq API)
├── requirements.txt
├── .env.example
└── data/                # generated CSV data (gitignored)
```

## Roadmap / how this scales beyond the hackathon

- Swap synthetic data for real building IoT/smart-meter feeds
- Extend to water usage and e-waste tracking (same architecture,
  new data pipelines)
- Add per-building automated alerts (email/Slack) when anomalies are detected
- Multi-campus comparison view
- Student-facing leaderboard/gamification for sustainability behavior

## Problem statement

> Global sustainability goals can feel massive and out of reach, but real,
> measurable change starts locally. College campuses and surrounding
> communities generate significant energy, water, and e-waste footprints
> that often remain unmonitored or poorly optimized. This project builds a
> data-driven, AI-powered solution that empowers administrators to take
> immediate, meaningful action to reduce waste and lower carbon emissions.
