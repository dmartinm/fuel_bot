import os
import requests
import pdfplumber
import io
import re
import smtplib
from email.message import EmailMessage
from datetime import datetime

PDF_URL = "https://economie.fgov.be/sites/default/files/Files/Energy/prices/Tarifs-officiels-produits-petroliers.pdf"

EMAIL_SENDER = os.environ["EMAIL_SENDER"]
EMAIL_RECEIVER = os.environ["EMAIL_RECEIVER"]
EMAIL_TOKEN = os.environ["EMAIL_TOKEN"]

def parse_price_line(line):
    prices = re.findall(r"\d+,\d+", line)
    return float(prices[1].replace(",", ".")) if len(prices) >= 2 else None

def get_prices():
    r = requests.get(PDF_URL, timeout=15)
    r.raise_for_status()
    text = ""
    with pdfplumber.open(io.BytesIO(r.content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    date_match = re.search(r"valable à partir du\s*:\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
    date = datetime.strptime(date_match.group(1), "%d/%m/%Y").strftime("%Y-%m-%d") if date_match else "Unknown"

    e5 = e10 = None
    for line in text.split("\n"):
        if "Essence 95 RON E5" in line:
            e5 = parse_price_line(line)
        if "Essence 95 RON E10" in line:
            e10 = parse_price_line(line)
    return date, e5, e10

def send_email(date, e5, e10):
    msg = EmailMessage()
    msg["Subject"] = f"Fuel price update {date}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.set_content(f"""
Fuel price update

Date: {date}
Essence 95 RON E5: {e5} €/L
Essence 95 RON E10: {e10} €/L
""")
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_SENDER, EMAIL_TOKEN)
        smtp.send_message(msg)
        print("Email sent!")

if __name__ == "__main__":
    date, e5, e10 = get_prices()
    send_email(date, e5, e10)
