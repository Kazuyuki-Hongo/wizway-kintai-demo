# 設計

## 前提

動機は proposal.md の「なぜ」。いま日ごと表の出勤・退勤・休憩は `frontend/src/App.tsx` の素の `input`（`aria-label` は `YYYY-MM-DD 出勤` など）。API（`backend/app.py`）は `HH:MM` の検証と、退勤前後・休憩長さ・欠勤時は空、をすでに持つ。曜日表示と `.row-saturday` / `.row-holiday` は完了済み。挙動変更の実装は OpenSpec apply と Serena（`.cursor/skills/openspec-apply-change/SKILL.md`、セッション初回 `initial_instructions`）を必須とする。

## 目標 / 対象外

**目標:**
- 出勤・退勤用の時刻 picker（カレンダー風のボタン UI）を日ごと表に載せる
- 休憩用の長さ picker（タイマー風、既定 `01:00`、1分刻み）を載せる
- 既存の `aria-label` と保存ペイロード（`clock_in` / `clock_out` / `break_time`）を維持し、E2E を新 UI に追従させる

**対象外:**
- API・SQLite・SAM テンプレートの変更
- 曜日・土日祝色の再実装
- 研修用リポへの先行実装
- この change 内での学習用 AWS 載せ直し（指示が出てから別タスク）

## 決定事項

### 1. API は触らず、画面の draft だけを picker で更新する

保存契約は `attendance-day-update` の既存 Requirement のまま。picker は `updateDraft` に `HH:MM` を渡すだけにする。

代替として API にプリセット一覧を足す案は取らない。デモ範囲が画面に閉じるし、研修題材が UI＋OpenSpec に寄る。

### 2. 出勤／退勤は「時刻」、休憩は「長さ」でコンポーネントを分ける

見た目はどちらもボタンで数値を選ぶが、ラベルと操作意味を分ける。

- 出勤・退勤: 時・分を選ぶカレンダー風パネル（日付カレンダーではない。その日の時刻だけ）
- 休憩: 長さの増減（＋/− や時・分スピナー）。空から始めるときは `01:00` を初期値にする
- 欠勤・有休に切り替えたときの空クリアは、いまの `updateDraft` ロジックを維持する

代替として `input type="time"` 一本化は取らない。休憩が「時刻」に見えてしまい、既存の長さ説明とぶつかる。

### 3. アクセシビリティの錨は既存ラベルを残す

E2E は `getByLabel('2026-11-02 出勤')` などで値を見ている。表示用の読み取り可能なコントロール（または同じ `aria-label` を持つ入力）を残し、picker 操作後も `.toHaveValue('HH:MM')` が通るようにする。拒否ケースは、picker または同等操作で値を載せてから保存する。

### 4. 曜日・行色のコードパスには手を入れない

`formatWorkDateLabel` と `rowClassName`、関連 CSS は変更しない。触るなら回帰確認だけ（E2E の曜日・色ケース）。

### 5. Serena と編集範囲

実装開始前に Serena `initial_instructions`。編集対象は主に `frontend/` と `tests/e2e/`。`backend/` は仕様どおり不要なら触らない。スキル正本は `.cursor/skills/openspec-apply-change/SKILL.md`。

### 6. デプロイ

学習用アカウント、プロファイル `deploy-jisseki`（`deploy` と取り違えない）。見本スタック `wizway-kintai-demo`。この change の完了条件に載せ直しを含めない。指示が出てから画面（必要なら API）を出す。本番勤怠アカウントへは出さない。

## リスク / トレードオフ

- [E2E の `.fill()` が効かなくなる] → 値をセットするテスト用の操作（ラベル付きコントロールへの fill、または picker の role/name）を設計し、spec のシナリオに合わせる
- [テーブル行が横に広がる] → コンパクトなポップオーバー／インラインスピナーにし、列幅の破綻を目視と E2E で確認する
- [空の休憩を `01:00` にしすぎると退勤なし日の保存意味が変わる] → 退勤が空の日は休憩を空のままにできる契約を守り、既定 `01:00` は「休憩を選ぶ操作を始めたとき」に適用する

## 移行手順

1. `/opsx-apply` で tasks を実装し、ローカル API テスト（変更がなければスキップ可）とローカル E2E（意図的失敗の「わざと」は除いてよい）を緑にする
2. 曜日・土日祝の E2E が赤になっていないことを確認する
3. 学習用 AWS への載せ直しは、別指示のあと `deploy-jisseki` で見本スタックのみ

## 未決事項

なし（既定の適用タイミングは上記 Decision 3 のリスク緩和どおり「休憩選択を始めたとき」とする）
