"""読み取り API のユニットテスト（lambda_handler を直接呼ぶ）。"""

from __future__ import annotations

import io
import json
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


@pytest.fixture(scope="session", autouse=True)
def _db() -> None:
    _ensure_db()


def call(path: str, method: str = "GET"):
    event = {
        "rawPath": path,
        "requestContext": {"http": {"method": method}},
    }
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


def test_prod_prefix_path_is_accepted():
    result, _ = call("/prod/employees")
    assert result["statusCode"] == 200
    assert len(body(result)["employees"]) == 3
