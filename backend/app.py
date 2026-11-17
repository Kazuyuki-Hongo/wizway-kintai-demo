"""勤怠デモ読み取り API。計算は sql/ の SELECT。Python で同じ式を持ち直さない。"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
}

YM_RE = re.compile(r"^\d{4}-\d{2}$")
EMPLOYEES_PATH = re.compile(r"^/employees/?$")
# ym に 2026/11 のような不正値が来ても1セグメントとして扱う（summary を先に判定）
MONTH_PATH = re.compile(r"^/employees/([^/]+)/months/(.+?)/?$")
SUMMARY_PATH = re.compile(r"^/employees/([^/]+)/months/(.+?)/summary/?$")

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
DB_PATH = Path(__file__).resolve().parent / "data" / "attendance.db"


def _response(status_code: int, body: dict | list | None = None):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": "" if body is None else json.dumps(body, ensure_ascii=False),
    }


def _path(event) -> str:
    raw = event.get("rawPath") or event.get("path") or ""
    # HTTP API の stage 付き URL でも、ハンドラ側は /employees から始める
    if raw.startswith("/prod/"):
        raw = raw[len("/prod") :]
    elif raw == "/prod":
        raw = "/"
    return raw


def _method(event) -> str:
    rc = event.get("requestContext") or {}
    http = rc.get("http") or {}
    return (http.get("method") or event.get("httpMethod") or "GET").upper()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _load_sql(name: str) -> str:
    # Lambda 同梱時は backend/ 配下にもコピーする。無いときはリポジトリの sql/ を読む。
    local = Path(__file__).resolve().parent / "sql" / name
    path = local if local.exists() else SQL_DIR / name
    return path.read_text(encoding="utf-8")


def _parse_employee_id(raw: str) -> int | None:
    try:
        return int(raw)
    except ValueError:
        return None


def _employee_exists(conn: sqlite3.Connection, employee_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 AS ok FROM employees WHERE id = ?", (employee_id,)
    ).fetchone()
    return row is not None


def _list_employees(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, display_name FROM employees ORDER BY id"
    ).fetchall()
    return [{"id": r["id"], "display_name": r["display_name"]} for r in rows]


def _month_rows(conn: sqlite3.Connection, employee_id: int, ym: str) -> list[dict]:
    sql = _load_sql("month_rows.sql")
    rows = conn.execute(sql, {"employee_id": employee_id, "ym": ym}).fetchall()
    return [
        {
            "work_date": r["work_date"],
            "category": r["category"],
            "clock_in": r["clock_in"],
            "clock_out": r["clock_out"],
            "break_time": r["break_time"],
        }
        for r in rows
    ]


def _month_summary(conn: sqlite3.Connection, employee_id: int, ym: str) -> dict:
    sql = _load_sql("month_summary.sql")
    row = conn.execute(sql, {"employee_id": employee_id, "ym": ym}).fetchone()
    return {
        "workday_count": int(row["workday_count"]),
        "total_worked_hours": float(row["total_worked_hours"]),
        "overtime_hours": float(row["overtime_hours"]),
        "missing_clock_out_count": int(row["missing_clock_out_count"]),
    }


def _invalid_ym(ym: str) -> bool:
    return YM_RE.match(ym) is None


def lambda_handler(event, context):
    method = _method(event)
    path = _path(event)

    if method == "OPTIONS":
        return _response(204)

    if method != "GET":
        return _response(405, {"error": "method not allowed"})

    if EMPLOYEES_PATH.match(path):
        with _connect() as conn:
            return _response(200, {"employees": _list_employees(conn)})

    summary_match = SUMMARY_PATH.match(path)
    month_match = MONTH_PATH.match(path) if summary_match is None else None

    if summary_match or month_match:
        m = summary_match or month_match
        assert m is not None
        employee_id = _parse_employee_id(m.group(1))
        ym = m.group(2)

        if employee_id is None:
            return _response(404, {"error": "employee not found"})

        if _invalid_ym(ym):
            print(f"invalid ym={ym!r} reason=expected YYYY-MM")
            return _response(400, {"error": "invalid ym"})

        with _connect() as conn:
            if not _employee_exists(conn, employee_id):
                return _response(404, {"error": "employee not found"})
            if summary_match:
                return _response(
                    200,
                    {
                        "employee_id": employee_id,
                        "ym": ym,
                        "summary": _month_summary(conn, employee_id, ym),
                    },
                )
            return _response(
                200,
                {
                    "employee_id": employee_id,
                    "ym": ym,
                    "rows": _month_rows(conn, employee_id, ym),
                },
            )

    return _response(404, {"error": "not found", "path": path, "method": method})
