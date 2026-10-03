import json, sys, urllib.request, datetime

TICKERS = {
    "NVDA": "輝達 NVIDIA",
    "QQQ": "那斯達克100 ETF",
    "VT": "全球股票 ETF",
    "VOO": "標普500 ETF",
}

def fetch(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=6mo&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)["chart"]["result"][0]
    rows = [(t, c) for t, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]) if c is not None]
    return rows

def sma(v, n):
    return sum(v[-n:]) / n if len(v) >= n else None

def rsi(v, n=14):
    d = [b - a for a, b in zip(v[-n - 1:-1], v[-n:])]
    ag = sum(max(x, 0) for x in d) / n
    al = sum(max(-x, 0) for x in d) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)

def analyze(sym, name, rows):
    dates = [datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d") for t, _ in rows]
    v = [c for _, c in rows]
    close, prev = v[-1], v[-2]
    chg = (close / prev - 1) * 100
    ma20, ma50 = sma(v, 20), sma(v, 50)
    r = rsi(v)
    ret1m = (close / v[-22] - 1) * 100 if len(v) > 22 else None
    high = max(v)
    from_high = (close / high - 1) * 100

    if ma20 and ma50 and close > ma20 > ma50:
        trend = "偏多"
    elif ma20 and ma50 and close < ma20 < ma50:
        trend = "偏空"
    else:
        trend = "盤整"

    notes = []
    notes.append(f"今日{'上漲' if chg >= 0 else '下跌'} {abs(chg):.2f}%，收盤 {close:.2f}。")
    if ma20:
        notes.append(f"股價在 20 日均線（{ma20:.2f}）{'之上' if close > ma20 else '之下'}。")
    if ma50:
        notes.append(f"股價在 50 日均線（{ma50:.2f}）{'之上' if close > ma50 else '之下'}。")
    if r >= 70:
        notes.append(f"RSI {r:.0f}，進入超買區，短線容易震盪。")
    elif r <= 30:
        notes.append(f"RSI {r:.0f}，進入超賣區，可能出現反彈。")
    else:
        notes.append(f"RSI {r:.0f}，在中性區間。")
    if ret1m is not None:
        notes.append(f"近一個月 {ret1m:+.1f}%，距半年高點 {from_high:.1f}%。")

    return {
        "sym": sym, "name": name, "date": dates[-1],
        "close": round(close, 2), "change_pct": round(chg, 2),
        "ma20": round(ma20, 2) if ma20 else None,
        "ma50": round(ma50, 2) if ma50 else None,
        "rsi": round(r, 1), "trend": trend, "notes": notes,
        "series": [round(x, 2) for x in v[-60:]],
    }

def main():
    items = []
    for sym, name in TICKERS.items():
        try:
            items.append(analyze(sym, name, fetch(sym)))
        except Exception as e:
            print(f"{sym} failed: {e}", file=sys.stderr)
    if not items:
        sys.exit(1)
    out = {"updated": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "items": items}
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

main()
