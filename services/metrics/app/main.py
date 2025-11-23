from __future__ import annotations
import csv
import os
import time
from collections import defaultdict
from prometheus_client import start_http_server, Gauge


CSV_PATH = os.getenv("CSV_PATH", "/data/out/contacts.csv")
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "5"))

g_total_rows = Gauge("csv_contacts_total_rows", "Total rows in contacts.csv")
g_unique_contacts = Gauge("csv_contacts_unique_contacts", "Unique contacts by email+phone")
g_ooo_count = Gauge("csv_contacts_ooo_count", "Rows marked as OOO")


def compute_metrics(path: str):
    total = 0
    unique = set()
    ooo = 0
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total += 1
                key = (row.get("contact_email", ""), row.get("contact_phone_e164", ""))
                unique.add(key)
                if str(row.get("is_ooo", "")).lower() == "true":
                    ooo += 1
    except FileNotFoundError:
        total = 0
    return total, len(unique), ooo


def main():
    start_http_server(8000)
    while True:
        total, uniq, ooo = compute_metrics(CSV_PATH)
        g_total_rows.set(total)
        g_unique_contacts.set(uniq)
        g_ooo_count.set(ooo)
        time.sleep(SCRAPE_INTERVAL)


if __name__ == "__main__":
    main()
