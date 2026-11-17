# task_completion

挙動変更タスクを完了とみなす前:

1. OpenSpec `tasks.md` の該当チェックを `- [x]`（指定どおり実装済みのときだけ）
2. `python sql/build_db.py`（schema/seed を変えたとき）
3. `npm run test:api`（PYTHONNOUSERSITE を外す）
4. 画面・API 契約を変えたら `npm run pw:test:attendance`
5. 学習用アカウントへ載せる変更なら identity 確認 → sam deploy → フロント sync → CloudFront でシード月 `2026-11` を目視/API確認
6. URL 変更時のみ README + 導入メモ（common/ウィズウェイ）。コース本文は触らない
7. 安定した規約が増えたら Serena memory を更新（`mem:core` から参照を辿る）

任意: プロジェクトルートで `serena memories check`
