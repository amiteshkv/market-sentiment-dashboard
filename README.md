# Retail Sentiment & Market Structure Monitor

This project is a real-time Python dashboard for monitoring retail trader sentiment and market structure across:

- BTCUSD
- XAUUSD
- US30
- NAS100
- SPX500
- ETHUSD

It displays:

- Long vs Short retail sentiment percentages
- Trading volume
- Net positions
- Market structure state
- Live updates in a dashboard UI

## Tech stack

- Python 3.12
- Streamlit
- Pandas
- NumPy

## Run locally

1. Create a virtual environment
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Install requirements
   ```bash
   pip install -r requirements.txt
   ```

3. Start the dashboard
   ```bash
   streamlit run app.py
   ```

## Notes

This initial version uses a synthetic real-time feed to simulate live data. To connect a real source, replace the `generate_market_snapshot()` logic in `src/sentiment_data.py` with API calls or brokerage/market data integration.

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository and upload the project files. Keep `app.py`, `requirements.txt`, and the `src` folder in the repository root.
2. Open [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
3. Select **New app**, choose the repository and branch, and set the main file to `app.py`.
4. Select **Deploy**. Community Cloud installs the packages from `requirements.txt` automatically.

The dashboard uses simulated live data, so no secrets are required. The local Windows launcher files are not needed on Community Cloud.
