"""schema.sql + seed.sql から backend/data/attendance.db を作る。"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "backend" / "data" / "attendance.db"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()

    sys.path.insert(0, str(ROOT.parent / "backend"))
    from app import _ensure_admin

    conn = sqlite3.connect(OUT)
    try:
        conn.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
        conn.executescript((ROOT / "seed.sql").read_text(encoding="utf-8"))
        _ensure_admin(conn)
        conn.commit()
    finally:
        conn.close()
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
