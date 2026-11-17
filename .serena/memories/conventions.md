# conventions

- 実働・超過は `sql/month_summary.sql`。Lambda は SELECT 結果を返すだけ
- 区分: `通常出勤` / `欠勤`。欠勤は時刻 NULL。退勤なしは通常出勤+clock_out NULL
- API JSON: employees `{id,display_name}` / rows `{work_date,category,clock_in,clock_out,break_time}`（空は `""`）/ summary `{workday_count,total_worked_hours,overtime_hours,missing_clock_out_count}`
- ym は `YYYY-MM` のみ。`2026/11` は 400+ログ1行
- 画面は保存 UI を置かない（初版）。文言「ダミーデータのみ」
- ダミー表示名例: テスト青空 / サンプル海原 / 見本山辺（実在名と重ねない）
- OpenSpec artifacts は日本語。見出し構造と SHALL/MUST は英語のまま
- PHP / 開発 VM / `php -l` 手順をこのリポに持ち込まない
- Serena 行番号は 0-based
