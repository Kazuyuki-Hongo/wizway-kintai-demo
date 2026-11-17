"""読み取り API のユニットテスト（lambda_handler を直接呼ぶ）。"""

from __future__ import annotations

import io
import json
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app import lambda_handler  # noqa: E402


def _ensure_db() -> None:
    db = BACKEND / "data" / "attendance.db"
    if not db.exists():
        sys.path.insert(0, str(ROOT / "sql"))
        from build_db import main as build_db

        build_db()


@pytest.fixture(autouse=True)
def runtime_db(tmp_path, monkeypatch):
    _ensure_db()
    seed = BACKEND / "data" / "attendance.db"
    before = seed.read_bytes()
    runtime = tmp_path / "attendance.db"
    shutil.copyfile(seed, runtime)
    monkeypatch.setenv("KINTAI_RUNTIME_DB", str(runtime))
    yield runtime
    assert seed.read_bytes() == before


def call(path: str, method: str = "GET", payload: dict | None = None):
    event = {
        "rawPath": path,
        "requestContext": {"http": {"method": method}},
    }
    if payload is not None:
        event["body"] = json.dumps(payload)
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = lambda_handler(event, None)
    return result, buf.getvalue()


def body(result) -> dict:
    return json.loads(result["body"] or "{}")


def test_list_employees_returns_three_dummy_names():
    result, _ = call("/employees")
    assert result["statusCode"] == 200
    employees = body(result)["employees"]
    assert len(employees) == 3
    assert {e["display_name"] for e in employees} == {
        "テスト青空",
        "サンプル海原",
        "見本山辺",
    }
    for emp in employees:
        assert set(emp.keys()) == {"id", "display_name"}


def test_month_rows_include_missing_clock_out_and_absence():
    result, _ = call("/employees/1/months/2026-11")
    assert result["statusCode"] == 200
    rows = body(result)["rows"]
    assert any(r["clock_out"] == "" and r["category"] == "通常出勤" for r in rows)
    assert any(r["category"] == "欠勤" for r in rows)
    normal = next(
        r
        for r in rows
        if r["work_date"] == "2026-11-02"
    )
    assert normal["clock_in"] == "09:00"
    assert normal["clock_out"] == "18:00"
    assert normal["break_time"] == "01:00"
    assert normal["stored"] is True
    assert len(rows) == 30
    assert [r["work_date"] for r in rows] == [
        f"2026-11-{day:02d}" for day in range(1, 31)
    ]
    empty = next(r for r in rows if r["work_date"] == "2026-11-01")
    assert empty["stored"] is False
    assert empty["category"] == ""
    absent = next(r for r in rows if r["work_date"] == "2026-11-05")
    assert absent["stored"] is True
    assert absent["category"] == "欠勤"


def test_month_summary_matches_seed_scenarios():
    result, _ = call("/employees/1/months/2026-11/summary")
    assert result["statusCode"] == 200
    summary = body(result)["summary"]
    assert summary["workday_count"] == 3
    assert summary["total_worked_hours"] == 17.0
    assert summary["overtime_hours"] == 1.0
    assert summary["missing_clock_out_count"] == 1


def test_invalid_ym_returns_400_and_logs_reason():
    result, log = call("/employees/1/months/2026/11")
    assert result["statusCode"] == 400
    payload = body(result)
    assert "rows" not in payload
    assert "summary" not in payload
    assert "invalid ym" in log

    summary_result, _ = call("/employees/1/months/2026/11/summary")
    assert summary_result["statusCode"] == 400
    assert "summary" not in body(summary_result)


def test_unknown_employee_returns_404_without_rows_or_summary():
    result, _ = call("/employees/999/months/2026-11")
    assert result["statusCode"] == 404
    assert "rows" not in body(result)

    summary_result, _ = call("/employees/999/months/2026-11/summary")
    assert summary_result["statusCode"] == 404
    assert "summary" not in body(summary_result)


def test_february_is_all_unstored_and_summary_is_zero():
    result, _ = call("/employees/1/months/2026-02")
    assert result["statusCode"] == 200
    rows = body(result)["rows"]
    assert len(rows) == 28
    assert all(r["stored"] is False for r in rows)

    summary_result, _ = call("/employees/1/months/2026-02/summary")
    summary = body(summary_result)["summary"]
    assert summary["workday_count"] == 0
    assert summary["total_worked_hours"] == 0.0
    assert summary["overtime_hours"] == 0.0
    assert summary["missing_clock_out_count"] == 0


def test_month_13_returns_400_for_rows_and_summary():
    result, log = call("/employees/1/months/2026-13")
    assert result["statusCode"] == 400
    assert "rows" not in body(result)
    assert "invalid ym" in log

    summary_result, summary_log = call("/employees/1/months/2026-13/summary")
    assert summary_result["statusCode"] == 400
    assert "summary" not in body(summary_result)
    assert "invalid ym" in summary_log


def day_payload(**overrides):
    payload = {
        "category": "通常出勤",
        "clock_in": "09:00",
        "clock_out": "18:00",
        "break_time": "01:00",
    }
    payload.update(overrides)
    return payload


def nov2(path_suffix: str = ""):
    return f"/employees/1/months/2026-11/days/2026-11-02{path_suffix}"


def row_on(date: str):
    result, _ = call("/employees/1/months/2026-11")
    return next(r for r in body(result)["rows"] if r["work_date"] == date)


def test_put_updates_clocks_and_summary_uses_sql():
    result, _ = call(
        nov2(),
        "PUT",
        day_payload(clock_in="10:00", clock_out="19:00", break_time="01:00"),
    )
    assert result["statusCode"] == 200
    saved = body(result)
    assert saved["stored"] is True
    assert saved["clock_in"] == "10:00"
    assert saved["clock_out"] == "19:00"
    updated = row_on("2026-11-02")
    assert updated["clock_in"] == "10:00"
    assert updated["clock_out"] == "19:00"

    # 09:00–19:00 休憩 1 時間は実働 9 時間。11-03 の 9 時間と合わせて総実働 18、超過 2。
    result, _ = call(
        nov2(),
        "PUT",
        day_payload(clock_in="09:00", clock_out="19:00", break_time="01:00"),
    )
    assert result["statusCode"] == 200
    summary = body(call("/employees/1/months/2026-11/summary")[0])["summary"]
    assert summary["workday_count"] == 3
    assert summary["total_worked_hours"] == 18.0
    assert summary["overtime_hours"] == 2.0


def test_put_can_clear_clock_out_and_switch_to_absence():
    result, _ = call(
        nov2(),
        "PUT",
        day_payload(clock_in="09:00", clock_out="", break_time=""),
    )
    assert result["statusCode"] == 200
    assert row_on("2026-11-02")["clock_out"] == ""

    result, _ = call(
        nov2(),
        "PUT",
        day_payload(category="欠勤", clock_in="", clock_out="", break_time=""),
    )
    assert result["statusCode"] == 200
    row = row_on("2026-11-02")
    assert row["category"] == "欠勤"
    assert row["clock_in"] == ""
    assert row["clock_out"] == ""
    assert row["break_time"] == ""


def test_put_allows_equal_clocks_and_break_equal_to_span():
    result, _ = call(
        nov2(),
        "PUT",
        day_payload(clock_in="09:00", clock_out="09:00", break_time="00:00"),
    )
    assert result["statusCode"] == 200
    result, _ = call(
        nov2(),
        "PUT",
        day_payload(clock_in="09:00", clock_out="18:00", break_time="09:00"),
    )
    assert result["statusCode"] == 200
    assert row_on("2026-11-02")["break_time"] == "09:00"


@pytest.mark.parametrize(
    "payload",
    [
        day_payload(clock_in="18:00", clock_out="09:00", break_time="00:00"),
        day_payload(clock_in="09:00", clock_out="18:00", break_time="10:00"),
        day_payload(clock_in="", clock_out="18:00", break_time="01:00"),
        day_payload(category="欠勤", clock_in="09:00", clock_out="", break_time=""),
        day_payload(category="有休"),
        day_payload(clock_in="9:00"),
        day_payload(clock_out="25:00"),
        day_payload(clock_out="18:60"),
    ],
)
def test_put_rejects_invalid_day_without_changing_seed_row(payload):
    result, log = call(nov2(), "PUT", payload)
    assert result["statusCode"] == 400
    assert "reason=" in log
    row = row_on("2026-11-02")
    assert row["clock_in"] == "09:00"
    assert row["clock_out"] == "18:00"
    assert row["category"] == "通常出勤"


def test_put_rejects_missing_field_without_change():
    payload = day_payload()
    del payload["clock_out"]
    result, _ = call(nov2(), "PUT", payload)
    assert result["statusCode"] == 400
    assert row_on("2026-11-02")["clock_out"] == "18:00"


def test_put_rejects_bad_target_without_creating_a_row(runtime_db):
    before = sqlite_count(runtime_db)
    result, log = call(
        "/employees/1/months/2026/11/days/2026-11-02",
        "PUT",
        day_payload(),
    )
    assert result["statusCode"] == 400
    assert "invalid ym" in log

    result, log = call(
        "/employees/1/months/2026-13/days/2026-13-01",
        "PUT",
        day_payload(),
    )
    assert result["statusCode"] == 400
    assert "invalid ym" in log

    result, _ = call("/employees/999/months/2026-11/days/2026-11-02", "PUT", day_payload())
    assert result["statusCode"] == 404

    result, _ = call("/employees/1/months/2026-11/days/2026-11-31", "PUT", day_payload())
    assert result["statusCode"] == 400

    result, _ = call("/employees/1/months/2026-11/days/2026-11-01", "PUT", day_payload())
    assert result["statusCode"] == 404
    assert row_on("2026-11-01")["stored"] is False
    assert sqlite_count(runtime_db) == before


def test_fresh_runtime_db_drops_updates(runtime_db, tmp_path, monkeypatch):
    call(nov2(), "PUT", day_payload(clock_in="10:00"))
    assert row_on("2026-11-02")["clock_in"] == "10:00"
    fresh = tmp_path / "fresh.db"
    shutil.copyfile(BACKEND / "data" / "attendance.db", fresh)
    monkeypatch.setenv("KINTAI_RUNTIME_DB", str(fresh))
    assert row_on("2026-11-02")["clock_in"] == "09:00"
    assert runtime_db.exists()


def sqlite_count(db: Path) -> int:
    import sqlite3

    conn = sqlite3.connect(db)
    try:
        return conn.execute("SELECT COUNT(*) FROM attendance_rows").fetchone()[0]
    finally:
        conn.close()


def test_prod_prefix_path_is_accepted():
    result, _ = call("/prod/employees")
    assert result["statusCode"] == 200
    assert len(body(result)["employees"]) == 3
