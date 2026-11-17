# wizway-kintai-demo

学習パック向けの勤怠デモ（読み取り専用）。  
ダミー社員の月次勤怠表と合計だけを返す。本番の勤怠（wizway_kintai）とは別リポジトリ。

**OpenSpec + Serena 導入済みの見本リポジトリ。** 仕様駆動の change（`demo-kintai`）、Serena ルール／メモリ、apply の接続ゲートまで入っている。

**React + TypeScript + Python Lambda + API Gateway (HTTP API) + 同梱 SQLite**

| 経路 | 役割 |
|------|------|
| `GET /employees` | ダミー社員の識別子と表示名 |
| `GET /employees/{id}/months/{ym}` | 指定月の勤怠行（`ym` は `YYYY-MM`） |
| `GET /employees/{id}/months/{ym}/summary` | 出勤日数・総実働・8時間超過・退勤なし件数 |

データは Lambda に同梱した SQLite のみ。DynamoDB と RDS は使わない。ログインは無い。保存はしない。

## 動いている画面（デプロイ済み）

- フロント: https://d266q7koncqwt6.cloudfront.net
- API: https://335nxj9000.execute-api.ap-northeast-1.amazonaws.com/prod

上の URL はダミー専用。本番の勤怠データは見えない。

## 構成

```
backend/          Python Lambda（読み取り API + 同梱 SQLite）
frontend/         React + TypeScript（Vite）
sql/              表定義・シード・合計 SELECT
template.yaml     SAM（HTTP API + Lambda + S3 + CloudFront）
docs/architecture.drawio  構成図
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

案件管理と同様に、ルートの Playwright と `tests/e2e/` を使う。詳細は [tests/e2e/README.md](tests/e2e/README.md)。

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
