# openspec/core

- config: `openspec/config.yaml`（spec-driven, context に本番分離・ダミー制約）
- 初版 change: `openspec/changes/demo-kintai`（attendance-month / attendance-summary）
- Skills: `.cursor/skills/openspec-apply-change` / `openspec-propose` に Serena 接続ゲート
- Rule: `.cursor/rules/openspec-serena-workflow.mdc` alwaysApply
- apply 前: Serena `initial_instructions`。失敗したらコード編集しない
- 機能追加は change を分割（保存・バリデーション等を1 change に詰め込まない）
- archive はユーザー指示後。push も指示後
- 戻る: `mem:core`
