from filing_event_study.events import cumulative_abnormal_return, map_to_session


def test_after_close_maps_to_next_observed_session():
    sessions = ["2024-01-05", "2024-01-08", "2024-01-09"]
    # 21:30 UTC is 16:30 Eastern in January.
    assert map_to_session("2024-01-05T21:30:00Z", sessions) == ("2024-01-08", "after close mapped to next observed session")


def test_intraday_filing_is_excluded_for_daily_bars():
    sessions = ["2024-01-08", "2024-01-09"]
    assert map_to_session("2024-01-08T15:00:00Z", sessions)[0] is None


def test_abnormal_window_is_market_adjusted():
    sessions = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]
    stock = dict(zip(sessions, [100, 101, 102.01, 103.0301]))
    market = dict(zip(sessions, [100, 101, 102.01, 103.0301]))
    result = cumulative_abnormal_return(stock, market, sessions, "2024-01-03", 0)
    assert abs(result) < 1e-10
