"""共有 SQLite は、ETag が同じあいだ中身を取り直さない。"""

from __future__ import annotations

import hashlib
import io
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import app  # noqa: E402


class _ResponseError(Exception):
    def __init__(self, code: str, status: int):
        super().__init__(code)
        self.response = {
            "Error": {"Code": code},
            "ResponseMetadata": {"HTTPStatusCode": status},
        }


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[str, bytes]] = {}
        self.body_reads = 0
        self.conditional: list[str | None] = []
        self.fail_upload = False

    def get_object(self, Bucket: str, Key: str, IfNoneMatch: str | None = None):
        self.conditional.append(IfNoneMatch)
        if Key not in self.objects:
            raise _ResponseError("NoSuchKey", 404)
        etag, body = self.objects[Key]
        if IfNoneMatch is not None and IfNoneMatch == etag:
            raise _ResponseError("304", 304)
        self.body_reads += 1
        return {"ETag": etag, "Body": io.BytesIO(body)}

    def upload_file(self, filename: str, bucket: str, key: str) -> None:
        if self.fail_upload:
            raise RuntimeError("upload failed")
        data = Path(filename).read_bytes()
        etag = '"' + hashlib.md5(data).hexdigest() + '"'
        self.objects[key] = (etag, data)

    def head_object(self, Bucket: str, Key: str):
        etag, _body = self.objects[Key]
        return {"ETag": etag}


def _clock(path: Path) -> str | None:
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            """
            SELECT clock_out FROM attendance_rows
            WHERE employee_id = 1 AND work_date = '2026-11-02'
            """
        ).fetchone()
    return None if row is None else row[0]


def _write_clock(src: Path, dest: Path, clock: str) -> None:
    shutil.copyfile(src, dest)
    with sqlite3.connect(dest) as conn:
        conn.execute(
            """
            UPDATE attendance_rows
            SET clock_out = ?
            WHERE employee_id = 1 AND work_date = '2026-11-02'
            """,
            (clock,),
        )


@pytest.fixture
def shared(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FakeS3:
    monkeypatch.delenv("KINTAI_RUNTIME_DB", raising=False)
    monkeypatch.setenv("KINTAI_DB_BUCKET", "demo-bucket")
    monkeypatch.setenv("KINTAI_DB_KEY", "attendance.db")
    monkeypatch.setattr(app, "_SHARED_ETAG", None)
    monkeypatch.setattr(app, "_S3_CLIENT", None)
    monkeypatch.setattr(app, "_SHARED_DB_PATH", tmp_path / "attendance.db")
    fake = FakeS3()
    monkeypatch.setattr(app, "_s3", lambda: fake)
    return fake


def test_s3_client_is_reused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app, "_S3_CLIENT", None)
    calls: list[object] = []

    def factory() -> object:
        client = object()
        calls.append(client)
        return client

    monkeypatch.setattr(app, "_new_s3_client", factory)
    assert app._s3() is app._s3()
    assert len(calls) == 1


def test_same_etag_does_not_read_body(shared: FakeS3) -> None:
    shared.upload_file(str(app.SEED_PATH), "demo-bucket", "attendance.db")
    first = app._prepare_shared_db("demo-bucket", "attendance.db")
    second = app._prepare_shared_db("demo-bucket", "attendance.db")
    assert first == second
    assert shared.body_reads == 1
    assert shared.conditional[1] == app._SHARED_ETAG
    assert _clock(first) == "18:00"


def test_changed_etag_returns_new_row(shared: FakeS3, tmp_path: Path) -> None:
    shared.upload_file(str(app.SEED_PATH), "demo-bucket", "attendance.db")
    app._prepare_shared_db("demo-bucket", "attendance.db")
    changed = tmp_path / "changed.db"
    _write_clock(app.SEED_PATH, changed, "19:00")
    shared.upload_file(str(changed), "demo-bucket", "attendance.db")
    path = app._prepare_shared_db("demo-bucket", "attendance.db")
    assert shared.body_reads == 2
    assert _clock(path) == "19:00"


def test_failed_publish_reloads_s3(shared: FakeS3) -> None:
    shared.upload_file(str(app.SEED_PATH), "demo-bucket", "attendance.db")
    path = app._prepare_shared_db("demo-bucket", "attendance.db")
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            UPDATE attendance_rows
            SET clock_out = '19:00'
            WHERE employee_id = 1 AND work_date = '2026-11-02'
            """
        )
        conn.commit()
    finally:
        conn.close()
    shared.fail_upload = True
    with pytest.raises(RuntimeError, match="upload failed"):
        app._publish_shared_db()
    assert app._SHARED_ETAG is None
    reloaded = app._prepare_shared_db("demo-bucket", "attendance.db")
    assert shared.body_reads == 2
    assert _clock(reloaded) == "18:00"


def test_missing_object_uploads_seed(shared: FakeS3) -> None:
    path = app._prepare_shared_db("demo-bucket", "attendance.db")
    assert path.read_bytes() == app.SEED_PATH.read_bytes()
    assert "attendance.db" in shared.objects
    assert app._SHARED_ETAG == shared.objects["attendance.db"][0]
    app._prepare_shared_db("demo-bucket", "attendance.db")
    assert shared.body_reads == 0
