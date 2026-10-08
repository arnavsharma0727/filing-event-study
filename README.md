# After-hours SEC filing event study

Build a reproducible daily event study around SEC 8-K filing acceptance times. The event mapper converts the SEC's UTC acceptance timestamp to US/Eastern, maps pre-open and after-close filings to the next observed price session, and excludes filings accepted during regular trading hours because daily bars cannot isolate their market reaction. The estimator uses a user-supplied issuer price series and benchmark price series.

## Skill demonstrated

- Timestamp-aware event construction using SEC filing acceptance time and the actual observed trading calendar.
- Market-adjusted event-return estimation with explicit daily-bar limitations.

## Run

```bash
pip install -e '.[test]'
export SEC_USER_AGENT='Arnav Sharma arnavsharma0727@gmail.com'
filing-events --cik 0000320193 --prices issuer_daily.csv --benchmark benchmark_daily.csv --window 1 --out output
```

The price files must have `date,close` columns and must come from an identified public source whose coverage you record in the run manifest. Output includes the SEC accession, acceptance timestamp, mapped event session, exclusion reason (if any), and cumulative abnormal return. The SEC's public submissions JSON is the filing-metadata source; no proprietary transcript or price data is included.

## Limits

Daily prices cannot measure intraday announcement effects. The pre/post-market rule is a defensible calendar alignment, not a substitute for intraday quotes. Overlapping events, earnings dates, and corporate actions need review before interpreting the event mean. Results are descriptive unless the design supports a causal interpretation.

## Validation

```bash
pytest
```
