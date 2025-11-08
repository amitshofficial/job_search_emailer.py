#!/usr/bin/env python3
"""
Daily job search script.
Requires environment variables:
  - SERPAPI_KEY (optional; recommended)
  - SMTP_HOST
  - SMTP_PORT
  - SMTP_USER
  - SMTP_PASS
  - RECIPIENT_EMAIL
  - SENDER_EMAIL
"""
import os
import smtplib
import datetime
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests

# ---------- Configuration ----------
RECIPIENT = os.environ.get("RECIPIENT_EMAIL")
SENDER = os.environ.get("SENDER_EMAIL")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")  # optional, for Google search via SerpAPI
MAX_RESULTS = 20

# Example search queries (customize)
SEARCH_QUERIES = [
    'site:linkedin.com "entry level" "machine learning engineer" OR "AI engineer"',
    'site:indeed.com "entry level" "machine learning" "engineer"',
    'site:angel.co "machine learning engineer" "junior"',
    '"entry level" "AI Engineer" "new grad"'
]

# ---------- Helpers ----------
def search_with_serpapi(query, serpapi_key, num=10):
    params = {
        "engine": "google",
        "q": query,
        "num": num,
        "google_domain": "google.com",
        "gl": "in",
        "hl": "en",
        "api_key": serpapi_key
    }
    r = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def extract_links_from_serpapi_json(js):
    results = []
    for e in js.get("organic_results", []):
        title = e.get("title")
        link = e.get("link")
        snippet = e.get("snippet")
        results.append({"title": title, "link": link, "snippet": snippet})
    return results

def format_email_html(results):
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M IST")
    html = f"<h2>Daily Jobs — Entry-level AI (Collected {dt})</h2>"
    if not results:
        html += "<p>No results found.</p>"
    else:
        html += "<table border='0' cellpadding='6' cellspacing='0'>"
        html += "<tr><th align='left'>Title</th><th align='left'>Company / Snippet</th><th align='left'>Link</th></tr>"
        for r in results:
            title = r.get("title") or "No title"
            snippet = r.get("snippet") or ""
            link = r.get("link") or ""
            html += f"<tr><td>{title}</td><td>{snippet}</td><td><a href='{link}'>link</a></td></tr>"
        html += "</table>"
    return html

def send_email_html(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SENDER, RECIPIENT, msg.as_string())

# ---------- Main ----------
def main():
    aggregated = []
    if SERPAPI_KEY:
        for q in SEARCH_QUERIES:
            try:
                js = search_with_serpapi(q, SERPAPI_KEY, num=10)
                rs = extract_links_from_serpapi_json(js)
                aggregated.extend(rs)
            except Exception as e:
                print("SerpAPI error for query:", q, "=>", e)
    else:
        # Fallback: use simple Google Search via unofficial endpoints is not recommended.
        print("No SERPAPI_KEY provided; please provide one or configure RSS sources.")
    # Deduplicate by link
    seen = set()
    dedup = []
    for item in aggregated:
        link = item.get("link")
        if link and link not in seen:
            seen.add(link)
            dedup.append(item)
        if len(dedup) >= MAX_RESULTS:
            break
    html = format_email_html(dedup)
    subject = f"[Daily] Entry-level AI Jobs — {datetime.date.today().isoformat()}"
    try:
        send_email_html(subject, html)
        print("Email sent, items:", len(dedup))
    except Exception as e:
        print("Failed to send email:", e)

if __name__ == "__main__":
    main()
