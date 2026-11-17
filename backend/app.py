"""勤怠デモ API。実働の合計は sql/ の SELECT。Python で同じ式を持ち直さない。"""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,PUT,OPTIONS",
}

YM_RE = re.compile(r"^\d{4}-\d{2}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^(\d{2}):(\d{2})$")
EMPLOYEES_PATH = re.compile(r"^/employees/?$")
DAY_PATH = re.compile(r"^/employees/([^/]+)/months/(.+?)/days/([^/]+)/?$")
# ym に 2026/11 のような不正値が来ても1セグメントとして扱う（summary を先に判定）
MONTH_PATH = re.compile(r"^/employees/([^/]+)/months/(.+?)/?$")
SUMMARY_PATH = re.compile(r"^/employees/([^/]+)/months/(.+?)/summary/?$")

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
SEED_PATH = Path(__file__).resolve().parent / "data" / "attendance.db"
_LOCAL_RUNTIME: Path | None = None

UPDATE_FIELDS = ("category", "clock_in", "clock_out", "break_time")


def _response(status_code: int, body: dict | list | None = None):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": "" if body is None else json.dumps(body, ensure_ascii=False),
    }


def _path(event) -> str:
    raw = event.get("rawPath") or event.get("path") or ""
    if raw.startswith("/prod/"):
        raw = raw[len("/prod") :]
    elif raw == "/prod":
        raw = "/"
    return raw


def _method(event) -> str:
    rc = event.get("requestContext") or {}
    http = rc.get("http") or {}
    return (http.get("method") or event.get("httpMethod") or "GET").upper()


def _runtime_db_path() -> Path:
    """初期データは開かない。実行環境のコピーを返す。"""
    override = os.environ.get("KINTAI_RUNTIME_DB")
    if override:
        path = Path(override)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SEED_PATH, path)
        return path

    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        path = Path("/tmp/attendance.db")
        if not path.exists():
            shutil.copyfile(SEED_PATH, path)
        return path

    global _LOCAL_RUNTIME
    if _LOCAL_RUNTIME is None:
        fd, name = tempfile.mkstemp(prefix="kintai-", suffix=".db")
        os.close(fd)
        shutil.copyfile(SEED_PATH, name)
        _LOCAL_RUNTIME = Path(name)
    return _LOCAL_RUNTIME


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_runtime_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _load_sql(name: str) -> str:
    local = Path(__file__).resolve().parent / "sql" / name
    path = local if local.exists() else SQL_DIR / name
    return path.read_text(encoding="utf-8")


def _parse_employee_id(raw: str) -> int | None:
    try:
        return int(raw)
    except ValueError:
        return None


def _invalid_ym(ym: str) -> bool:
    if YM_RE.match(ym) is None:
        return True
    month = int(ym[5:7])
    return month < 1 or month > 12


def _log_invalid_ym(ym: str) -> None:
    print(f"invalid ym={ym!r} reason=expected YYYY-MM with month 01-12")


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
            "stored": bool(r["stored"]),
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


def _read_month(employee_id: int | None, ym: str, summary: bool):
    if employee_id is None:
        return _response(404, {"error": "employee not found"})
    if _invalid_ym(ym):
        _log_invalid_ym(ym)
        return _response(400, {"error": "invalid ym"})
    with _connect() as conn:
        if not _employee_exists(conn, employee_id):
            return _response(404, {"error": "employee not found"})
        if summary:
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


def _event_body(event) -> dict | None:
    raw = event.get("body") or ""
    if event.get("isBase64Encoded") and raw:
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _minutes(value: str) -> int | None:
    match = TIME_RE.fullmatch(value)
    if match is None:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2))
    if hour > 23 or minute > 59:
        return None
    return hour * 60 + minute


def _reject(reason: str):
    print(f"reject update reason={reason}")
    return _response(400, {"error": "rejected", "reason": reason})


def _validate_fields(fields: dict[str, str]) -> str | None:
    category = fields["category"]
    clock_in = fields["clock_in"]
    clock_out = fields["clock_out"]
    break_time = fields["break_time"]
    if category not in ("通常出勤", "欠勤"):
        return "category not allowed"
    if category == "欠勤":
        if clock_in or clock_out or break_time:
            return "absence must have empty times"
        return None
    if not clock_in:
        return "clock_in required"
    in_minutes = _minutes(clock_in)
    if in_minutes is None:
        return "invalid time"
    if clock_out == "":
        if break_time and _minutes(break_time) is None:
            return "invalid time"
        return None
    out_minutes = _minutes(clock_out)
    if out_minutes is None:
        return "invalid time"
    if out_minutes < in_minutes:
        return "clock_out before clock_in"
    if break_time == "":
        return "break required when clock_out is set"
    break_minutes = _minutes(break_time)
    if break_minutes is None:
        return "invalid time"
    if break_minutes > out_minutes - in_minutes:
        return "break too long"
    return None


def _blank_to_null(value: str) -> str | None:
    return value if value else None


def _date_in_month(ym: str, work_date: str) -> bool:
    if DATE_RE.fullmatch(work_date) is None or not work_date.startswith(ym + "-"):
        return False
    try:
        datetime.strptime(work_date, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _row_exists(conn: sqlite3.Connection, employee_id: int, work_date: str) -> bool:
    row = conn.execute(
        """
        SELECT 1 AS ok
        FROM attendance_rows
        WHERE employee_id = ? AND work_date = ?
        """,
        (employee_id, work_date),
    ).fetchone()
    return row is not None


def _update_day(employee_raw: str, ym: str, work_date: str, event):
    if _invalid_ym(ym):
        _log_invalid_ym(ym)
        return _response(400, {"error": "invalid ym", "reason": "invalid ym"})
    if not _date_in_month(ym, work_date):
        return _reject("date not in month")
    employee_id = _parse_employee_id(employee_raw)
    if employee_id is None:
        return _response(404, {"error": "employee not found"})

    with _connect() as conn:
        if not _employee_exists(conn, employee_id):
            return _response(404, {"error": "employee not found"})
        if not _row_exists(conn, employee_id, work_date):
            return _response(404, {"error": "day not stored"})

        data = _event_body(event)
        if data is None:
            return _reject("invalid json")
        if any(key not in data for key in UPDATE_FIELDS):
            return _reject("missing field")
        fields: dict[str, str] = {}
        for key in UPDATE_FIELDS:
            value = data[key]
            if value is None:
                value = ""
            if not isinstance(value, str):
                return _reject("invalid field")
            fields[key] = value
        reason = _validate_fields(fields)
        if reason:
            return _reject(reason)

        conn.execute(
            """
            UPDATE attendance_rows
            SET category = ?, clock_in = ?, clock_out = ?, break_time = ?
            WHERE employee_id = ? AND work_date = ?
            """,
            (
                fields["category"],
                _blank_to_null(fields["clock_in"]),
                _blank_to_null(fields["clock_out"]),
                _blank_to_null(fields["break_time"]),
                employee_id,
                work_date,
            ),
        )
        conn.commit()
    return _response(
        200,
        {
            "employee_id": employee_id,
            "ym": ym,
            "work_date": work_date,
            "category": fields["category"],
            "clock_in": fields["clock_in"],
            "clock_out": fields["clock_out"],
            "break_time": fields["break_time"],
            "stored": True,
        },
    )


def lambda_handler(event, context):
    method = _method(event)
    path = _path(event)

    if method == "OPTIONS":
        return _response(204)

    day_match = DAY_PATH.match(path)
    if day_match:
        if method != "PUT":
            return _response(405, {"error": "method not allowed"})
        return _update_day(
            day_match.group(1), day_match.group(2), day_match.group(3), event
        )

    if method != "GET":
        return _response(405, {"error": "method not allowed"})

    if EMPLOYEES_PATH.match(path):
        with _connect() as conn:
            return _response(200, {"employees": _list_employees(conn)})

    summary_match = SUMMARY_PATH.match(path)
    month_match = MONTH_PATH.match(path) if summary_match is None else None

    if summary_match or month_match:
        matched = summary_match or month_match
        assert matched is not None
        return _read_month(
            _parse_employee_id(matched.group(1)),
            matched.group(2),
            summary_match is not None,
        )

    return _response(404, {"error": "not found", "path": path, "method": method})
