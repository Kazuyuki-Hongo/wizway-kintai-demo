"""ローカルで lambda_handler を叩いて 3.1 / 3.2 を確認する。"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

from app import lambda_handler


def call(path: str):
    event = {
        "rawPath": path,
        "requestContext": {"http": {"method": "GET"}},
    }
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = lambda_handler(event, None)
    return result, buf.getvalue()


def main() -> None:
    employees, _ = call("/employees")
    assert employees["statusCode"] == 200
    body = json.loads(employees["body"])
    assert len(body["employees"]) == 3
    print("employees ok", body["employees"])

    rows_res, _ = call("/employees/1/months/2026-11")
    assert rows_res["statusCode"] == 200
    rows = json.loads(rows_res["body"])["rows"]
    assert any(r["clock_out"] == "" for r in rows)
    assert any(r["category"] == "欠勤" for r in rows)
    print("rows ok", rows)

    summary_res, _ = call("/employees/1/months/2026-11/summary")
    assert summary_res["statusCode"] == 200
    summary = json.loads(summary_res["body"])["summary"]
    assert summary["workday_count"] == 14
    assert summary["total_worked_hours"] == 105.0
    assert summary["overtime_hours"] == 1.0
    assert summary["missing_clock_out_count"] == 1
    print("summary ok", summary)

    bad_ym, log = call("/employees/1/months/2026/11")
    assert bad_ym["statusCode"] == 400
    assert json.loads(bad_ym["body"]).get("rows") is None
    assert "invalid ym" in log
    print("400 log:", log.strip())

    bad_ym_s, _ = call("/employees/1/months/2026/11/summary")
    assert bad_ym_s["statusCode"] == 400

    missing, _ = call("/employees/999/months/2026-11")
    assert missing["statusCode"] == 404
    missing_s, _ = call("/employees/999/months/2026-11/summary")
    assert missing_s["statusCode"] == 404
    print("404 ok")
    print("all local checks passed")


if __name__ == "__main__":
    main()
