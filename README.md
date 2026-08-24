# 🌱 Eco-Intelligent AI

**Hackathon Track:** SW-05 — Eco-Intelligent AI & Sustainable Tech

An AI-powered dashboard that monitors campus building energy usage, forecasts
future consumption, automatically flags anomalies (e.g. equipment left
running after hours), and generates plain-English, actionable recommendations
for facilities staff — turning raw sensor data into immediate steps toward
lower campus energy waste and carbon emissions.

Validated on **real hourly electricity data** from actual university
buildings via the [Building Data Genome Project 2](https://doi.org/10.1038/s41597-020-00712-x)
(Miller et al., _Scientific Data_, 2020) — the peer-reviewed dataset used in
ASHRAE's Great Energy Predictor competition. Not a toy demo.

## Live demo

🔗 **[Add your Streamlit Community Cloud URL here once deployed]**

## How it works

1. **Data layer** — real hourly energy usage per building from BDG2 (with a
   synthetic data generator as a fallback/offline option).
2. **Forecasting** — Holt-Winters exponential smoothing predicts the next
   72 hours of usage per building.
3. **Anomaly detection** — compares each hour against that same building's
   typical usage at that same hour-of-day and day-type (weekday vs weekend),
   so normal daily/weekly rhythms aren't mistaken for anomalies.
4. **AI insight layer** — each detected anomaly is sent to a free LLM API
   (Groq) which explains the likely cause and suggests one concrete action.
   Works without any API key too (falls back to a template-based insight).
5. **Dashboard** — Streamlit + Plotly, with an impact estimate showing
   potential kWh / CO₂ savings if flagged anomalies are addressed.

## Tech stack

| Layer                 | Tools                                                   |
| --------------------- | ------------------------------------------------------- |
| Dashboard / UI        | Streamlit, Plotly                                       |
| Data processing       | pandas, NumPy                                           |
| Forecasting           | statsmodels (Holt-Winters Exponential Smoothing)        |
| Anomaly detection     | Custom same-hour / day-type statistical deviation model |
| AI insight generation | Groq API (`openai/gpt-oss-20b`), free tier              |
| Real-world data       | Building Data Genome Project 2 (via Kaggle)             |
| Hosting               | Streamlit Community Cloud (free)                        |
| Version control       | Git + GitHub                                            |

Every component runs on **free tiers only** — no paid subscriptions
anywhere in the stack, so this is realistically deployable by any campus
with zero AI/infrastructure budget.

## Quickstart (local)

```bash
# 1. Clone and enter the repo
git clone https://github.com/Arroh-Yadav/eco-intelligent-AI.git
cd eco-intelligent-AI

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies (uses only prebuilt wheels, no compiler needed)
python -m pip install --only-binary :all: -r requirements.txt

# 4. (Optional but recommended) enable live AI insights
cp .env.example .env
# then paste a free key from https://console.groq.com into .env

# 5. Generate demo data — pick ONE:
python data_generator.py        # synthetic data, works instantly, no setup
# OR, for real campus data (see "Using real data" below):
python real_data_loader.py

# 6. Run the app
python -m streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Using real campus data (BDG2)

By default, `data_generator.py` creates realistic **synthetic** data so the
app works instantly with zero setup. To run on **real** university building
data instead:

1. Create a free Kaggle account and generate an API token at
   [kaggle.com/settings](https://www.kaggle.com/settings) → API → Create New Token
2. Install kagglehub: `python -m pip install --user kagglehub`
3. Download the dataset:
   ```bash
   python -c "import kagglehub; print(kagglehub.dataset_download('claytonmiller/buildingdatagenomeproject2'))"
   ```
4. Copy `metadata.csv` and `electricity_cleaned.csv` from the printed path
   into a `bdg2_raw/` folder at the project root
5. Run `python real_data_loader.py` — this filters to real education-sector
   buildings and writes `data/energy_usage.csv` in the same schema the app
   expects, so no other code changes are needed

## Getting a free AI API key (no subscription, no credit card)

This project uses **Groq** because it's free, fast, and requires no
payment method:

1. Go to https://console.groq.com
2. Sign up / log in
3. Create an API key
4. Put it in your `.env` file as `GROQ_API_KEY=your_key_here`

No key? The app still runs fully — `ai_insights.py` automatically falls
back to a rule-based insight so the dashboard is never broken during a demo.

## Deploying (Streamlit Community Cloud, free)

1. Push this repo to your own GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub
3. Click **New app**, select this repo, branch `main`, main file `app.py`
4. In **Advanced settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "your_key_here"
   ```
5. Deploy. If you want the app to serve real BDG2 data instead of
   synthetic, force-add the generated data file before pushing:
   ```bash
   git add -f data/energy_usage.csv
   git commit -m "Add real BDG2 campus data for deployment"
   git push origin main
   ```

## Project structure

```
eco-intelligent-AI/
├── app.py               # Streamlit dashboard (entry point)
├── data_generator.py    # Synthetic campus energy data generator
├── real_data_loader.py  # Loads + reshapes real BDG2 data into the app's schema
├── forecast.py          # Forecasting + anomaly detection
├── ai_insights.py        # AI-generated recommendations (Groq API)
├── requirements.txt
├── .env.example
├── .gitignore
└── data/                 # generated CSV data (gitignored)
```

## Roadmap / how this scales beyond the hackathon

- Real-time ingestion from campus BMS/IoT smart meters (BACnet/Modbus/MQTT)
  instead of a static CSV
- Multi-tenant workspace model: campus admins sign up, connect their own
  buildings, isolated per-organization data
- Extend the same forecast → anomaly → AI-insight pipeline to water usage
  and e-waste tracking
- Multi-campus benchmarking and comparison dashboards
- Optional RAG layer to ground AI recommendations in an institution's own
  policy documents, maintenance logs, or ISO 50001 guidelines

## Problem statement

> Global sustainability goals can feel massive and out of reach, but real,
> measurable change starts locally. College campuses and surrounding
> communities generate significant energy, water, and e-waste footprints
> that often remain unmonitored or poorly optimized. This project builds a
> data-driven, AI-powered solution that empowers administrators to take
> immediate, meaningful action to reduce waste and lower carbon emissions.
