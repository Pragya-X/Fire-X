from datetime import datetime, timedelta, timezone

from app.services.temporal import analyze_detections

NOW = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)


def test_no_detections():
    res = analyze_detections([], now=NOW)
    assert res["pattern"] == "unknown"
    assert res["persistence_score"] == 0.0


def test_single_detection_is_sudden():
    res = analyze_detections([NOW - timedelta(hours=10)], now=NOW)
    assert res["pattern"] == "sudden"
    assert res["persistence_score"] == 0.0


def test_daily_detections_are_persistent():
    dets = [NOW - timedelta(days=d, hours=2) for d in range(10, 0, -1)]
    res = analyze_detections(dets, now=NOW)
    assert res["pattern"] == "persistent"
    assert res["persistence_score"] >= 50
    assert res["n_detections"] == 10


def test_clustered_detections_are_recurring():
    dets = [
        NOW - timedelta(days=13, hours=1), NOW - timedelta(days=12, hours=2),
        NOW - timedelta(days=8, hours=1), NOW - timedelta(days=7, hours=2),
        NOW - timedelta(days=3, hours=1), NOW - timedelta(days=2, hours=2),
    ]
    res = analyze_detections(dets, now=NOW)
    assert res["pattern"] in ("recurring", "persistent")


def test_timeline_covers_window():
    dets = [NOW - timedelta(days=2), NOW]
    res = analyze_detections(dets, window_days=14, now=NOW)
    assert len(res["timeline"]) >= 14
    assert any(d["detected"] for d in res["timeline"])