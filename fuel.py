import requests
import pdfplumber
import io
import re
import json
from datetime import datetime

PDF_URL = "https://economie.fgov.be/sites/default/files/Files/Energy/prices/Tarifs-officiels-produits-petroliers.pdf"

def parse_price_line(line):
    # extract numbers like 1,684
    prices = re.findall(r"\d+,\d+", line)
    if len(prices) >= 2:
        return prices[1]  # second value = price with TVA
    return None


def get_prices():
    r = requests.get(PDF_URL)
    r.raise_for_status()

    text = ""

    with pdfplumber.open(io.BytesIO(r.content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    # Extract effective date
    date_match = re.search(r"valable à partir du\s*:\s*(\d{2}/\d{2}/\d{4})", text)
    effective_date = None

    if date_match:
        effective_date = datetime.strptime(
            date_match.group(1), "%d/%m/%Y"
        ).strftime("%Y-%m-%d")

    e5 = None
    e10 = None

    for line in text.split("\n"):
        if "Essence 95 RON E5" in line:
            e5 = parse_price_line(line)

        if "Essence 95 RON E10" in line:
            e10 = parse_price_line(line)

    # convert to float
    def convert(v):
        return float(v.replace(",", ".")) if v else None

    return {
        "date": effective_date,
        "E5_TVAC": convert(e5),
        "E10_TVAC": convert(e10)
    }


if __name__ == "__main__":
    print(json.dumps(get_prices(), indent=2))
