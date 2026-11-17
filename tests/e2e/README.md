# 勤怠デモ Playwright E2E

案件管理（`wizway_anken`）の Playwright 配置に合わせ、`tests/e2e/` とルートの `playwright.config.ts` で動かす。  
このデモはログインが無いので、`storageState` と auth-setup は使わない。

## 前提

1. `python sql/build_db.py` 済み（`backend/data/attendance.db` がある）
2. フロント依存: `cd frontend && npm ci`（初回）
3. ルート依存: `npm ci` と `npm run pw:install`

## セットアップ

```powershell
cp env.sample .env
# ローカル既定のままなら編集不要

npm install
npm run pw:install
cd frontend
npm install
cd ..
python sql/build_db.py
python -m pip install --user -r backend/requirements-dev.txt
```

## 実行

```powershell
# API ユニット
npm run test:api

# E2E（ローカル: API + Vite を webServer が起動）
npm run pw:test:attendance

# デプロイ済み画面を見るとき
# .env の PLAYWRIGHT_BASE_URL を CloudFront URL にする
# （設定すると webServer は起動しない）
$env:PLAYWRIGHT_BASE_URL='https://d266q7koncqwt6.cloudfront.net'
npm run pw:test:attendance
```

UI デバッグ:

```powershell
npx playwright test tests/e2e/attendance.spec.ts --ui
```

## 注意

- `PLAYWRIGHT_BASE_URL` は画面のドキュメントルート（末尾スラッシュなし）
- ローカル実行時の API は `http://127.0.0.1:8080`（`backend/local_server.py`）
- `playwright-report/` と `junit.xml` は git 管理外
- SAM デプロイ用に `PYTHONNOUSERSITE=1` を付けたシェルでは、`pytest` が user インストールを見ないことがある。そのときは環境変数を外してから `npm run test:api` する
- ログイン・`storageState` は無い（案件管理の auth-setup は不要）
