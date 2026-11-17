# tech_stack

- Frontend: React 19, TypeScript, Vite 6（`frontend/`）。`VITE_API_URL`
- Backend: Python 3.13 Lambda, stdlib sqlite3 only（boto3/Dynamo なし）
- Data: SQLite 同梱。`python sql/build_db.py` → `backend/data/attendance.db`
- IaC: AWS SAM (`template.yaml`), HTTP API stage `prod`, S3+CloudFront OAC
- OpenSpec CLI, schema `spec-driven`, artifacts ja（SHALL/MUST は英語）
- Tests: pytest（`backend/requirements-dev.txt`）, Playwright `@playwright/test`（ルート `package.json`）
- Node: frontend とルートで別 `package.json`（E2E はルート）
