# backend/core

- Handler: `backend/app.py` `lambda_handler`
- Routes: GET `/employees`, `/employees/{id}/months/{ym}`, `.../summary`
- DB: `file:{DB_PATH}?mode=ro`（初版読み取り専用）。書き込みを足すなら OpenSpec design で /tmp コピー等を先に決める。接続先を MariaDB に差し替えない
- SQL ファイル: 実行時は `backend/sql/` 優先、無ければリポ `sql/`
- ローカル: `local_server.py`（8080）、`local_check.py`、pytest `backend/tests/test_api.py`
- パッケージ: SAM `CodeUri: backend/`（db + sql 同梱）。`__pycache__` は無視
- 戻る: `mem:core`。コマンド: `mem:suggested_commands`
