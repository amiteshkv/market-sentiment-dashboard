from __future__ import annotations

from datetime import datetime, timezone
import math
import random

import numpy as np
import pandas as pd

SYMBOLS = {
    "BTCUSD": {"base_price": 65000.0, "volatility": 1.40, "position_mult": 1.8},
    "ETHUSD": {"base_price": 3400.0, "volatility": 1.10, "position_mult": 1.6},
    "XAUUSD": {"base_price": 2320.0, "volatility": 0.82, "position_mult": 1.3},
    "US30": {"base_price": 42000.0, "volatility": 0.92, "position_mult": 1.1},
    "NAS100": {"base_price": 20000.0, "volatility": 1.05, "position_mult": 1.4},
    "SPX500": {"base_price": 5400.0, "volatility": 0.88, "position_mult": 1.2},
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _market_structure(long_pct: float, short_pct: float, momentum: float) -> str:
    score = long_pct - short_pct + momentum * 12
    if score > 8:
        return "Bullish Structure"
    if score < -8:
        return "Bearish Structure"
    return "Neutral Structure"


def generate_symbol_snapshot(symbol: str, timestamp: datetime, seed_offset: int = 0) -> dict:
    meta = SYMBOLS[symbol]
    rng = random.Random(f"{symbol}:{int(timestamp.timestamp())}:{seed_offset}")
    phase = (timestamp.timestamp() / 90.0) + seed_offset
    wave = math.sin(phase)
    momentum = math.sin(phase * 1.7 + 0.6)
    retail_bias = math.cos(phase * 0.9 + 0.5)

    long_pct = 50 + wave * 18 + retail_bias * 9
    short_pct = 100 - long_pct
    long_pct = _clamp(long_pct, 18, 82)
    short_pct = _clamp(short_pct, 18, 82)

    price_change = (momentum * 0.65 + wave * 0.35) * meta["volatility"]
    last_price = meta["base_price"] * (1 + price_change / 100.0)

    volume = int(
        (1800 + abs(wave) * 1400 + abs(momentum) * 2200 + rng.uniform(200, 800))
        * meta["volatility"]
        * 12
    )
    position = int((long_pct - short_pct) * 120 * meta["position_mult"])

    return {
        "symbol": symbol,
        "timestamp": timestamp,
        "price": round(last_price, 2),
        "price_change_pct": round(price_change, 2),
        "long_pct": round(long_pct, 2),
        "short_pct": round(short_pct, 2),
        "volume": volume,
        "position": position,
        "momentum": round(momentum, 3),
        "market_structure": _market_structure(long_pct, short_pct, momentum),
    }


def generate_market_snapshot() -> pd.DataFrame:
    timestamp = datetime.now(timezone.utc)
    rows = []
    for idx, symbol in enumerate(SYMBOLS.keys()):
        rows.append(generate_symbol_snapshot(symbol, timestamp, seed_offset=idx * 2))
    return pd.DataFrame(rows)


def main() -> None:
    snapshot = generate_market_snapshot()
    print(snapshot[['symbol', 'price', 'price_change_pct', 'long_pct', 'short_pct', 'market_structure']].to_string(index=False))


if __name__ == "__main__":
    main()
