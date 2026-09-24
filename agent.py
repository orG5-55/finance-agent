import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import feedparser
import yfinance as yf
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def get_market_data():
    """שאיבת נתוני שוק יומיים עבור מדדים ומניות מרכזיות"""
    tickers = {
        "S&P 500": "^GSPC",
        "Nasdaq 100": "^NDX",
        "Nvidia": "NVDA",
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "10Y Treasury": "^TNX"
    }
    
    summary = []
    for name, sym in tickers.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
                curr_close = hist['Close'].iloc[-1]
                pct_change = ((curr_close - prev_close) / prev_close) * 100
                summary.append(f"{name}: {curr_close:.2f} ({pct_change:+.2f}%)")
        except Exception:
            summary.append(f"{name}: נתונים לא זמינים זמנית")
            
    return "\n".join(summary)

def get_economic_news():
    """שאיבת כותרות וניתוחים מפידים כלכליים מרכזיים"""
    feeds = [
        "https://search.cnbc.com/rs/search/view.xml?partnerId=2000&keywords=markets&sort=date",
        "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines"
    ]
    
    news_items = []
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:5]:
                summary_text = getattr(entry, 'summary', '')
                news_items.append(f"- {entry.title}: {summary_text}")
        except Exception:
            pass
            
    return "\n".join(news_items[:10])

def generate_insights(market_data, news_data):
    """עיבוד הנתונים והפקת תחזית באמצעות מודל שפה"""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
אתה אנליסט מאקרו ושווקים פיננסיים בכיר.
נתח את נתוני השוק והחדשות הבאים והפק סקירת שוק תמציתית, מקצועית וממוקדת בעברית.

נתוני ביצועי שוק ומדדים:
{market_data}

חדשות וסקירות אנליסטים אחרונות:
{news_data}

מבנה התשובה הנדרש (עד 350 מילים, ברור וקריא):
1. **מצב השוק ומדדים מובילים:** תמצית של המגמה.
2. **אירועי מאקרו ומגזרים מרכזיים:** דגש על אינפלציה, ריבית, אג"ח ותחום הטכנולוגיה/שבבים.
3. **תחזיות קדימה וסנטימנט אנליסטים:** מה צופה הקונצנזוס קדימה, סיכונים ומנועי צמיחה פעילים.
"""
    response = client.models.generate_content(
       model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text

def send_email_report(content):
    """שליחת הדוח לתיבת הג'ימייל שלך"""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg['Subject'] = "📊 דוח שוק יומי ותחזיות להשקעה"
    
    msg.attach(MIMEText(content, 'plain', 'utf-8'))
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)

def main():
    market_data = get_market_data()
    news_data = get_economic_news()
    insights = generate_insights(market_data, news_data)
    
    report = f"דוח שוק ותחזיות השקעה יומי\n{'='*30}\n\n{insights}"
    send_email_report(report)

if __name__ == "__main__":
    main()
