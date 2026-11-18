# attendance-sql-practice Specification

## Purpose

学習パックの SQL 演習向けに、ローカル SQLite へ勤怠管理らしい表とデモデータを置く。画面と既存 API からは公開しない。

## Requirements

### Requirement: 演習用の部署と社員紐付け

システムは、ローカル SQLite に部署表を持ち、各ダミー社員を部署へ紐付け MUST する。部署には親子が分かる行を含む SHALL。

#### Scenario: 部署と社員が揃う

- **GIVEN** 演習用スキーマを含む `sql/schema.sql` がある
- **WHEN** `sql/build_db.py` で DB を作り直す
- **THEN** 部署が 2 件以上あり、親が NULL の部署と親を指す部署の両方がある
- **AND** 各ダミー社員に部署が付いている

### Requirement: 演習用の休暇申請と承認履歴

システムは、ローカル SQLite に休暇申請と承認履歴の表を持ち、複数ステータスと承認の有無が分かるデモ行を入れる SHALL。

#### Scenario: 申請の境界ケースが入る

- **GIVEN** 演習用の seed が適用される
- **WHEN** seed を適用したローカル DB を開く
- **THEN** status が submitted / approved / rejected / draft の申請がそれぞれ 1 件以上ある
- **AND** 承認履歴が付く申請と、付かない submitted 申請の両方がある
- **AND** 同一申請に承認履歴が 2 行以上あるケースが 1 件以上ある
- **AND** 対象月の勤怠行と期間が重なる承認済み申請と、重ならない承認済み申請の両方がある

### Requirement: 既存勤怠表との共存

演習用の表を足しても、既存の `employees` / `attendance_rows` / `attendance_edits` / `sessions` と既存 API・画面の要件は変えない SHALL。

#### Scenario: 既存の月次データが残る

- **GIVEN** 演習用の表を含む DB を作り直した
- **WHEN** 既存の月次 API を呼ぶ
- **THEN** 従来どおりダミー社員の 2026-11 勤怠行が返る
