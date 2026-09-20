from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from src.sentiment_data import generate_market_snapshot

st.set_page_config(page_title="Retail Sentiment Monitor", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #0b1020 0%, #101827 100%);
        color: #e5edf8;
    }
    .stDataFrame {
        background: rgba(17, 24, 39, 0.9);
        border-radius: 12px;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc;
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }
    .signal-card {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

INSTRUMENTS = ["BTCUSD", "XAUUSD", "US30", "NAS100", "SPX500", "ETHUSD"]
TIMEFRAMES = {
    "1m": 60,
    "5m": 5 * 60,
    "15m": 15 * 60,
    "1h": 60 * 60,
    "4h": 4 * 60 * 60,
    "1D": 24 * 60 * 60,
}


def _ensure_history() -> None:
    if "history" not in st.session_state:
        st.session_state.history = defaultdict(list)


def _append_snapshot() -> pd.DataFrame:
    _ensure_history()
    snapshot = generate_market_snapshot()
    snapshot = snapshot[snapshot["symbol"].isin(INSTRUMENTS)].sort_values("symbol").reset_index(drop=True)
    for _, row in snapshot.iterrows():
        st.session_state.history[row["symbol"]].append(
            {
                "timestamp": row["timestamp"],
                "price": float(row["price"]),
                "price_change_pct": float(row["price_change_pct"]),
                "long_pct": float(row["long_pct"]),
                "short_pct": float(row["short_pct"]),
                "volume": int(row["volume"]),
                "position": int(row["position"]),
                "momentum": float(row["momentum"]),
                "market_structure": row["market_structure"],
            }
        )
    return snapshot


def _history_for_timeframe(symbol: str, seconds: int) -> pd.DataFrame:
    _ensure_history()
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    rows = [row for row in st.session_state.history.get(symbol, []) if row["timestamp"] >= cutoff]
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def render_header() -> None:
    st.title("Retail Trader Sentiment & Market Structure Monitor")
    st.caption("Real-time sentiment, volume, market structure, and price momentum across major instruments.")


def highlight_structure(value: str) -> str:
    if "Bullish" in value:
        return "🚀 Bullish"
    if "Bearish" in value:
        return "📉 Bearish"
    return "➡️ Neutral"


def render_cards(df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1.5, 1.4, 1.4, 1.6, 1.4])
            with col1:
                st.markdown(f"### {row['symbol']}")
                st.write(f"Price: ${row['price']:,.2f}")
                st.write(f"Change: {row['price_change_pct']:+.2f}%")
            with col2:
                st.metric("Long", f"{row['long_pct']:.1f}%")
                st.metric("Short", f"{row['short_pct']:.1f}%")
            with col3:
                st.metric("Volume", f"{row['volume']:,}")
                st.metric("Position", f"{row['position']:,}")
            with col4:
                st.write("Market Structure")
                st.write(highlight_structure(row["market_structure"]))
                st.write(f"Momentum: {row['momentum']:.3f}")
            with col5:
                sentiment_gap = row["long_pct"] - row["short_pct"]
                if sentiment_gap > 6:
                    st.success("Retail bias: Long-heavy")
                elif sentiment_gap < -6:
                    st.warning("Retail bias: Short-heavy")
                else:
                    st.info("Retail bias: Balanced")
                st.write(f"Net bias: {sentiment_gap:+.1f}%")

            st.markdown("---")


def render_table(df: pd.DataFrame) -> None:
    display = df[["symbol", "price", "price_change_pct", "long_pct", "short_pct", "volume", "position", "market_structure"]].copy()
    display.columns = ["Symbol", "Price", "Change %", "Long %", "Short %", "Volume", "Position", "Structure"]
    st.dataframe(display, use_container_width=True, hide_index=True)


def _signal_score(row: pd.Series) -> float:
    return float(row["long_pct"]) - float(row["short_pct"]) + (float(row["momentum"]) * 10.0)


def render_summary(df: pd.DataFrame) -> None:
    ranked = df.copy()
    ranked["signal_score"] = ranked.apply(_signal_score, axis=1)
    ranked = ranked.sort_values("signal_score", ascending=False).reset_index(drop=True)

    st.markdown("### Market Summary")
    strongest = ranked.iloc[0]
    weakest = ranked.iloc[-1]
    avg_momentum = ranked["momentum"].mean()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Strongest Bias", f"{strongest['symbol']} {strongest['signal_score']:+.1f}")
    with col2:
        st.metric("Weakest Bias", f"{weakest['symbol']} {weakest['signal_score']:+.1f}")
    with col3:
        st.metric("Avg Momentum", f"{avg_momentum:.3f}")


def render_signal_board(df: pd.DataFrame) -> None:
    ranked = df.copy()
    ranked["signal_score"] = ranked.apply(_signal_score, axis=1)
    ranked = ranked.sort_values("signal_score", ascending=False).reset_index(drop=True)

    st.markdown("### Signal Board")
    for _, row in ranked.iterrows():
        signal = "Bullish" if row["signal_score"] >= 0 else "Bearish"
        with st.container():
            st.markdown(
                f"""
                <div class="signal-card">
                    <b>{row['symbol']}</b> · {signal} · Score: {row['signal_score']:+.1f}<br>
                    Long: {row['long_pct']:.1f}% | Short: {row['short_pct']:.1f}% | Change: {row['price_change_pct']:+.2f}%
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_top_movers(df: pd.DataFrame) -> None:
    movers = df[["symbol", "price_change_pct", "signal_score"]].copy() if "signal_score" in df.columns else df[["symbol", "price_change_pct"]].copy()
    if "signal_score" not in movers.columns:
        movers["signal_score"] = movers["price_change_pct"]
    movers = movers.sort_values("signal_score", ascending=False).reset_index(drop=True)

    st.markdown("### Top Movers")
    top_cols = st.columns(min(3, len(movers)))
    for idx, (_, row) in enumerate(movers.head(3).iterrows()):
        with top_cols[idx]:
            label = "Strongest" if idx == 0 else "Active"
            st.metric(label, f"{row['symbol']}", f"{row['price_change_pct']:+.2f}%")


def render_alerts(df: pd.DataFrame, threshold: float) -> None:
    alert_rows = []
    for _, row in df.iterrows():
        sentiment_gap = float(row["long_pct"]) - float(row["short_pct"])
        if sentiment_gap > threshold:
            alert_rows.append(f"🚀 {row['symbol']}: strong long sentiment ({sentiment_gap:+.1f}%)")
        elif sentiment_gap < -threshold:
            alert_rows.append(f"📉 {row['symbol']}: strong short sentiment ({sentiment_gap:+.1f}%)")
        if row["market_structure"] == "Bullish Structure":
            alert_rows.append(f"📈 {row['symbol']}: bullish structure confirmed")
        elif row["market_structure"] == "Bearish Structure":
            alert_rows.append(f"📉 {row['symbol']}: bearish structure confirmed")

    st.markdown("### Alerts")
    if not alert_rows:
        st.info("No major alerts right now. Market is relatively balanced.")
        return

    for alert in alert_rows[:6]:
        st.warning(alert)


def render_rankings(df: pd.DataFrame) -> None:
    ranked = df.copy()
    ranked["signal_score"] = ranked.apply(_signal_score, axis=1)
    ranked = ranked.sort_values("signal_score", ascending=False).reset_index(drop=True)

    display = ranked[["symbol", "signal_score", "long_pct", "short_pct", "price_change_pct", "market_structure"]].copy()
    display.columns = ["Symbol", "Signal Score", "Long %", "Short %", "Change %", "Structure"]
    st.markdown("### Ranking")
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_heatmap(df: pd.DataFrame) -> None:
    heat = df[["symbol", "long_pct", "short_pct"]].copy()
    heat = heat.set_index("symbol")
    styled = heat.style.background_gradient(cmap="RdYlGn_r", subset=["long_pct", "short_pct"])
    st.markdown("### Sentiment Heatmap")
    st.dataframe(styled, use_container_width=True, hide_index=False)


def render_timeframe_charts(symbol: str, timeframe_seconds: int) -> None:
    history = _history_for_timeframe(symbol, timeframe_seconds)
    if history.empty:
        st.info(f"No history loaded yet for {symbol} within the selected timeframe.")
        return

    history = history.sort_values("timestamp").reset_index(drop=True)
    st.subheader(f"{symbol} · {timeframe_seconds // 60} min view")
    st.line_chart(history.set_index("timestamp")["price"], height=220)

    positive_positions = history.loc[history["position"] > 0, "position"]
    negative_positions = history.loc[history["position"] < 0, "position"]
    st.markdown("#### Position activity in selected timeframe")
    position_chart = history.set_index("timestamp")[["position"]]
    st.bar_chart(position_chart, height=180)

    cols = st.columns(5)
    with cols[0]:
        st.metric("Latest Price", f"${history['price'].iloc[-1]:,.2f}")
    with cols[1]:
        st.metric("Range", f"{history['price'].min():,.2f} → {history['price'].max():,.2f}")
    with cols[2]:
        st.metric("Avg Momentum", f"{history['momentum'].mean():.3f}")
    with cols[3]:
        st.metric("Positive Position", f"{len(positive_positions)} times", f"Total +{positive_positions.sum():,.0f}")
    with cols[4]:
        st.metric("Negative Position", f"{len(negative_positions)} times", f"Total {negative_positions.sum():,.0f}")


def main() -> None:
    render_header()

    st.sidebar.header("Controls")
    timeframe_label = st.sidebar.selectbox("Timeframe", list(TIMEFRAMES.keys()), index=2)
    refresh_seconds = st.sidebar.slider("Refresh every (seconds)", min_value=1, max_value=10, value=2)
    selected_symbol = st.sidebar.selectbox("Symbol", INSTRUMENTS, index=0)
    alert_threshold = st.sidebar.slider("Alert threshold (%)", min_value=3.0, max_value=20.0, value=6.0, step=0.5)
    st.sidebar.caption("Synthetic live data for dashboard prototyping and briefing workflows.")

    @st.fragment(run_every=refresh_seconds)
    def render_live_feed() -> None:
        snapshot = _append_snapshot()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        st.subheader(f"Live Feed · {now}")
        render_summary(snapshot)
        render_alerts(snapshot, alert_threshold)

        csv_data = snapshot.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download snapshot as CSV",
            data=csv_data,
            file_name=f"sentiment_snapshot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            width="stretch",
        )

        st.markdown("---")
        overview, table, analysis = st.tabs(["Overview", "Market Table", "Analysis"])

        with overview:
            render_signal_board(snapshot)
            render_top_movers(snapshot)
            render_cards(snapshot)

        with table:
            render_table(snapshot)
            render_heatmap(snapshot)
            render_rankings(snapshot)

        with analysis:
            st.subheader("Timeframe Analysis")
            timeframe_seconds = TIMEFRAMES[timeframe_label]
            render_timeframe_charts(selected_symbol, timeframe_seconds)

    render_live_feed()


if __name__ == "__main__":
    main()
