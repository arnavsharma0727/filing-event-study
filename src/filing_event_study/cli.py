from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

import requests

from .events import cumulative_abnormal_return, map_to_session


def read_prices(path: Path) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or not {"date", "close"}.issubset(reader.fieldnames):
            raise ValueError(f"{path} must contain date,close columns")
        return {row["date"][:10]: float(row["close"]) for row in reader if row.get("date") and row.get("close")}


def main() -> None:
    parser = argparse.ArgumentParser(description="Map SEC 8-K filing times to sessions and calculate market-adjusted event returns.")
    parser.add_argument("--cik", required=True)
    parser.add_argument("--prices", required=True, type=Path)
    parser.add_argument("--benchmark", required=True, type=Path)
    parser.add_argument("--window", type=int, default=1, help="Symmetric trading sessions around event, e.g. 1 means [-1,+1]")
    parser.add_argument("--out", type=Path, default=Path("output"))
    args = parser.parse_args()
    user_agent = os.environ.get("SEC_USER_AGENT")
    if not user_agent:
        parser.error("Set SEC_USER_AGENT to a real name and contact email")
    cik = args.cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(url, headers={"User-Agent": user_agent}, timeout=30)
    response.raise_for_status()
    data = response.json()
    recent = data.get("filings", {}).get("recent", {})
    accepted = recent.get("acceptanceDateTime", [])
    events = [
        {"form": form, "filing_date": filing_date, "accession": accession, "accepted_utc": accepted[i]}
        for i, (form, filing_date, accession) in enumerate(zip(recent.get("form", []), recent.get("filingDate", []), recent.get("accessionNumber", [])))
        if form in {"8-K", "8-K/A"} and i < len(accepted) and accepted[i]
    ]
    issuer = read_prices(args.prices)
    benchmark = read_prices(args.benchmark)
    sessions = sorted(set(issuer) & set(benchmark))
    if len(sessions) < 5:
        parser.error("issuer and benchmark price files need at least five common trading sessions")
    results = []
    for event in events:
        session, note = map_to_session(event["accepted_utc"], sessions)
        car = None
        exclusion = ""
        if session:
            try:
                car = cumulative_abnormal_return(issuer, benchmark, sessions, session, args.window)
            except (ValueError, KeyError):
                exclusion = "incomplete price window or invalid input prices"
        else:
            exclusion = note
        results.append({**event, "event_session": session or "", "mapping_note": note, "car_log_return": car if car is not None else "", "exclusion": exclusion})
    args.out.mkdir(parents=True, exist_ok=True)
    fields = ["form", "filing_date", "accession", "accepted_utc", "event_session", "mapping_note", "car_log_return", "exclusion"]
    with (args.out / "event_returns.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    manifest = {"cik": cik, "entity": data.get("name"), "submissions_url": url, "issuer_price_file": args.prices.name, "benchmark_price_file": args.benchmark.name, "issuer_price_source": "user-supplied; document public vendor/source before interpreting", "benchmark_price_source": "user-supplied; document public vendor/source before interpreting", "window": [-args.window, args.window], "filing_count": len(events), "mapped_count": sum(bool(r["event_session"]) for r in results)}
    (args.out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(results)} filing events to {args.out / 'event_returns.csv'}")
