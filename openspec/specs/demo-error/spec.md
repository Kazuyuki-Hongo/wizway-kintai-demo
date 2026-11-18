# demo-error Specification

## Purpose

学習パックのログ切り分け演習向けに、意図的に 500 と traceback を出す経路を提供する。本番勤怠や顧客データは対象にしない。

## Requirements

### Requirement: 意図的 ERROR 経路

システムは `GET /demo/error` を提供し、クエリ `marker`（省略可）を含む例外を送出して 500 を返す SHALL。利用者向けの通常画面からはリンクしない。

#### Scenario: marker 付きで 500

- **GIVEN** 学習用の ERROR 経路がある
- **WHEN** `GET /demo/error?marker=短い印` を呼ぶ
- **THEN** 応答は 500 である
- **AND** サーバログ（またはローカル実行の標準エラー）に、例外メッセージまたは traceback と marker の文字列が残る

#### Scenario: marker なしでも 500

- **GIVEN** 学習用の ERROR 経路がある
- **WHEN** `GET /demo/error` を呼ぶ
- **THEN** 応答は 500 である
