"""ローカル SQLite でシードと合計を確認する。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT.parent / "backend" / "data" / "attendance.db"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    names = [r["display_name"] for r in conn.execute("SELECT display_name FROM employees")]
    print("employees:", names)

    rows = list(
        conn.execute(
            """
            SELECT work_date, category, clock_in, clock_out, break_time
            FROM attendance_rows
            WHERE employee_id = 1
            ORDER BY work_date
            """
        )
    )
    print("emp1 rows:")
    for r in rows:
        print(" ", dict(r))

    cats = {r["category"] for r in rows}
    has_missing = any(r["category"] == "通常出勤" and r["clock_out"] is None for r in rows)
    has_over = any(
        r["category"] == "通常出勤"
        and r["clock_in"] == "09:00"
        and r["clock_out"] == "19:00"
        and r["break_time"] == "01:00"
        for r in rows
    )
    has_normal = any(
        r["clock_in"] == "09:00" and r["clock_out"] == "18:00" and r["break_time"] == "01:00"
        for r in rows
    )
    assert "通常出勤" in cats and "欠勤" in cats
    assert has_missing and has_over and has_normal

    month_sql = (ROOT / "month_rows.sql").read_text(encoding="utf-8")
    nov = list(conn.execute(month_sql, {"employee_id": 1, "ym": "2026-11"}))
    assert [r["work_date"] for r in nov] == [
        f"2026-11-{day:02d}" for day in range(1, 31)
    ]
    empty = next(r for r in nov if r["work_date"] == "2026-11-01")
    assert empty["stored"] == 0
    assert empty["category"] == ""
    assert empty["clock_in"] == ""
    assert empty["clock_out"] == ""
    assert empty["break_time"] == ""
    absent = next(r for r in nov if r["work_date"] == "2026-11-05")
    assert absent["stored"] == 1
    assert absent["category"] == "欠勤"
    feb = list(conn.execute(month_sql, {"employee_id": 1, "ym": "2026-02"}))
    assert [r["work_date"] for r in feb] == [
        f"2026-02-{day:02d}" for day in range(1, 29)
    ]
    assert all(r["stored"] == 0 for r in feb)
    print("calendar ok")

    summary_sql = (ROOT / "month_summary.sql").read_text(encoding="utf-8")
    s = dict(conn.execute(summary_sql, {"employee_id": 1, "ym": "2026-11"}).fetchone())
    print("emp1 summary:", s)
    assert s["workday_count"] == 14  # 11/2-20 の平日から欠勤1日を除く。退勤なしは出勤扱い
    assert float(s["total_worked_hours"]) == 105.0
    assert float(s["overtime_hours"]) == 1.0
    assert s["missing_clock_out_count"] == 1

    feb_s = dict(
        conn.execute(summary_sql, {"employee_id": 1, "ym": "2026-02"}).fetchone()
    )
    assert feb_s["workday_count"] == 0
    assert float(feb_s["total_worked_hours"]) == 0.0
    assert float(feb_s["overtime_hours"]) == 0.0
    assert feb_s["missing_clock_out_count"] == 0
    print("summary ok")
    print("ok")


if __name__ == "__main__":
    main()
