# parkrun Analytics

A multi-page Streamlit app that fetches your parkrun results from [parkrun UK](https://www.parkrun.org.uk) and lets you explore runs over time and compare with friends or family.

## Setup

```bash
cd "parkrun app"
pip install -r requirements.txt
```

## Run

```bash
streamlit run Home.py
```

Then open the URL shown in the terminal (usually http://localhost:8501).

## Pages

- **Home** — Welcome and short guide; enter your parkrun athlete number (from your results URL, e.g. `.../parkrunner/2099834/all/` → `2099834`) and click **View my analytics**.
- **Analytics** — Summary stats, a configurable line chart (time, position, age grade, run number), date range filter, and the option to add other athlete numbers to compare on the same chart.

## Data & privacy

- Results are scraped from **public** `parkrun.org.uk` pages when you load or refresh the Analytics page.  
- The only input you provide is the **athlete number** (e.g. `2099834`), which is used to construct the public results URL.  
- All processing happens in memory inside the running Streamlit app – **no result data is stored to disk or sent to any external service** by this code.  
- You can close the app at any time to clear the current analysis.

Use this project for personal, non-commercial use only. parkrun’s data use policy applies.
