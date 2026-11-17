# wizway-kintai-demo

学習パック向けの勤怠デモ。  
ダミー社員の月次勤怠表と合計を返し、保存済みの日を更新できる。本番の勤怠（wizway_kintai）とは別リポジトリ。

**OpenSpec + Serena 導入済みの見本。** 仕様駆動の型は次のフォルダにある。

- `docs/rules/project-rules-serena.md` と `.serena/memories/` — Serena の約束と覚え書き
- `openspec/specs/` — いまの仕様
- `openspec/changes/` — 進行中の change
- `openspec/changes/archive/` — 完了して移した change
- `.cursor/skills/openspec-apply-change/` — 実装の前に Serena へ接続するゲート

**React + TypeScript + Python Lambda + API Gateway (HTTP API) + 同梱 SQLite**

| 経路 | 役割 |
|------|------|
| `GET /employees` | ダミー社員の識別子と表示名 |
| `GET /employees/{id}/months/{ym}` | 指定月の勤怠行（`ym` は `YYYY-MM`） |
| `GET /employees/{id}/months/{ym}/summary` | 出勤日数・総実働・8時間超過・退勤なし件数 |
| `PUT /employees/{id}/months/{ym}/days/{date}` | 保存済みの1日を更新する。行が無い日は作らない |

データは Lambda に同梱した SQLite が初期データ。更新は実行環境のコピーに書き、やり直すと初期データに戻る。DynamoDB と RDS は使わない。ログインは無い。

## 動いている画面（デプロイ済み）

- フロント: https://d266q7koncqwt6.cloudfront.net
- API: https://335nxj9000.execute-api.ap-northeast-1.amazonaws.com/prod

上の URL はダミー専用。本番の勤怠データは見えない。

## 構成

```
backend/          Python Lambda（API + 同梱 SQLite）
frontend/         React + TypeScript（Vite）
sql/              表定義・シード・合計 SELECT
template.yaml     SAM（HTTP API + Lambda + S3 + CloudFront）
docs/architecture.drawio  構成図
docs/rules/       Serena のプロジェクトルール
openspec/         仕様と change（進行中と archive）
backend/tests/    API の pytest
tests/e2e/        画面の受け入れ確認（Playwright）
```

### 構成図

ブラウザ → CloudFront → S3（画面）  
ブラウザ → HTTP API → Lambda → 同梱 SQLite

詳細: `docs/architecture.drawio`

## 前提

- AWS CLI / SAM CLI / Node.js
- 学習用 AWS アカウントの Deployer（本番勤怠のアカウントには載せない）

```powershell
aws sso login --profile <自分のプロファイル名>
aws sts get-caller-identity --profile <自分のプロファイル名>
```

Account が本番勤怠と同じ箱なら、ここで止める。

## デプロイ手順

### 1. SQLite を作り直す（任意）

```powershell
python sql/build_db.py
```

### 2. API + インフラ

Windows で SAM CLI が `botocore` で落ちるときは、同じシェルで `PYTHONNOUSERSITE=1` を付けてから実行する。

```powershell
$env:PYTHONNOUSERSITE='1'
sam build
sam deploy --profile <自分のプロファイル名>
```

Outputs: `ApiUrl` / `FrontendBucketName` / `FrontendUrl` / `CloudFrontDistributionId`

### 3. フロント

`frontend/.env.production`:

```env
VITE_API_URL=https://xxxx.execute-api.ap-northeast-1.amazonaws.com/prod
```

```powershell
cd frontend
npm ci
npm run build
aws s3 sync dist/ s3://<FrontendBucketName>/ --delete --profile <自分のプロファイル名>
aws cloudfront create-invalidation --distribution-id <CloudFrontDistributionId> --paths "/*" --profile <自分のプロファイル名>
```

## ローカル確認

```powershell
python sql/build_db.py
python backend/local_check.py
python backend/local_server.py
```

別ターミナル:

```powershell
cd frontend
$env:VITE_API_URL='http://127.0.0.1:8080'
npm run dev
```

## テスト

API の pytest は `backend/tests/`。画面の受け入れ確認は、リポジトリ直下の Playwright と `tests/e2e/`。詳細は [tests/e2e/README.md](tests/e2e/README.md)。

```powershell
python -m pip install --user -r backend/requirements-dev.txt
npm install
npm run pw:install
cd frontend
npm install
cd ..

npm run test:api
npm run pw:test:attendance
```
