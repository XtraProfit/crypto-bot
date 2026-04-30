import requests
import schedule
import time
from datetime import datetime, timezone

# ============================================================
#   CONFIGURACIÓN — edita solo estas 2 líneas
# ============================================================
BOT_TOKEN = "8753633633:AAHkz8nlLV1cGu70K0b_piUJbjb_A5_GY2s"        # obtenlo de @BotFather
CHANNEL_ID = "@InvestmentM_Updates"      # ej: @MiCanalCrypto
# ============================================================

TOP_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "TRXUSDT", "LTCUSDT"
]

DISPLAY_NAMES = {
    "BTCUSDT": "BTC", "ETHUSDT": "ETH", "BNBUSDT": "BNB",
    "XRPUSDT": "XRP", "SOLUSDT": "SOL", "ADAUSDT": "ADA",
    "DOGEUSDT": "DOGE", "AVAXUSDT": "AVAX", "TRXUSDT": "TRX",
    "LTCUSDT": "LTC"
}

def get_prices():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10)
        data = r.json()
        prices = {}
        for item in data:
            if item["symbol"] in TOP_SYMBOLS:
                prices[item["symbol"]] = {
                    "price": float(item["lastPrice"]),
                    "change": float(item["priceChangePercent"])
                }
        return prices
    except Exception as e:
        print(f"Error prices: {e}")
        return {}

def get_gainers_losers():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10)
        data = r.json()
        usdt = [x for x in data if x["symbol"].endswith("USDT") and float(x["quoteVolume"]) > 1_000_000]
        sorted_data = sorted(usdt, key=lambda x: float(x["priceChangePercent"]), reverse=True)
        return sorted_data[:5], sorted_data[-5:][::-1]
    except:
        return [], []

def get_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        d = r.json()["data"][0]
        return d["value"], d["value_classification"]
    except:
        return "N/A", "N/A"

def get_news():
    try:
        url = "https://cryptopanic.com/api/v1/posts/?auth_token=public&kind=news&filter=hot&regions=en"
        r = requests.get(url, timeout=10)
        items = r.json().get("results", [])[:3]
        return [{"title": i["title"], "source": i.get("source", {}).get("title", ""), "url": i.get("url", "")} for i in items]
    except:
        return []

def format_price(p):
    return f"${p:,.2f}" if p >= 1000 else f"${p:.4f}" if p >= 1 else f"${p:.6f}"

def format_change(c):
    return f"{'▲' if c >= 0 else '▼'} {abs(c):.2f}%"

def build_message():
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%H:%M UTC · %b %d, %Y")
    prices = get_prices()
    gainers, losers = get_gainers_losers()
    fg_value, fg_label = get_fear_greed()
    news = get_news()

    lines = [
        "🌐 <b>Crypto Market Live Update</b>",
        f"🕐 Last Update: {timestamp}",
        "━━━━━━━━━━━━━━━━━━━━"
    ]

    if news:
        lines.append("📰 <b>Market News</b>")
        for n in news:
            lines.append(f'• {n["title"]} — <a href="{n["url"]}">{n["source"]}</a>')
        lines.append("━━━━━━━━━━━━━━━━━━━━")

    lines.append(f"😨 <b>Fear &amp; Greed:</b> {fg_value} ({fg_label})")

    if gainers:
        lines += ["", "🚀 <b>Top Gainers (Binance · 24h)</b>"]
        for g in gainers:
            lines.append(f'• {g["symbol"]}  +{float(g["priceChangePercent"]):.2f}%')

    if losers:
        lines += ["", "📉 <b>Top Losers (Binance · 24h)</b>"]
        for l in losers:
            lines.append(f'• {l["symbol"]}  {float(l["priceChangePercent"]):.2f}%')

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("💰 <b>Market Prices (Top 10)</b>")
    for symbol in TOP_SYMBOLS:
        if symbol in prices:
            name = DISPLAY_NAMES[symbol]
            lines.append(f"{name}  {format_price(prices[symbol]['price'])}  ({format_change(prices[symbol]['change'])})")

    lines += ["━━━━━━━━━━━━━━━━━━━━", "⏰ <i>Auto-updates every 12 HOURS</i>"]
    return "\n".join(lines)

def send_message():
    print(f"[{datetime.now()}] Sending...")
    msg = build_message()
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHANNEL_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True},
        timeout=15
    )
    print("✅ Sent!" if r.status_code == 200 else f"❌ Error: {r.text}")

if __name__ == "__main__":
    print("🤖 Bot started!")
    send_message()
    schedule.every(12).hours.do(send_message)
    while True:
        schedule.run_pending()
        time.sleep(60)