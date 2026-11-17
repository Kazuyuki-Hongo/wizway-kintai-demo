# frontend/core

- 入口: `frontend/src/App.tsx` / `main.tsx`。API は `import.meta.env.VITE_API_URL`
- 1画面: 社員 select + month input → rows table + summary dl
- 保存ボタン無し。エラーは画面上部テキスト
- 本番ビルドは `.env.production`（gitignore）。環境変数 `VITE_API_URL` が残っていると `.env.production` より優先される
- E2E: `tests/e2e/attendance.spec.ts`。webServer が API:8080 + Vite:5173。`PLAYWRIGHT_BASE_URL` があると webServer オフ
- 詳細手順: `tests/e2e/README.md`。戻る: `mem:core`
