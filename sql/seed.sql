-- 表示名は架空。実在社員名は使わない。
-- 対象月: 2026-11。社員1に仕様シナリオをすべて載せる。

INSERT INTO employees (id, display_name) VALUES
  (1, 'テスト青空'),
  (2, 'サンプル海原'),
  (3, '見本山辺');

-- 社員1: 通常出勤 8h / 超過1h / 退勤なし / 欠勤
INSERT INTO attendance_rows (id, employee_id, work_date, category, clock_in, clock_out, break_time) VALUES
  (1, 1, '2026-11-02', '通常出勤', '09:00', '18:00', '01:00'),
  (2, 1, '2026-11-03', '通常出勤', '09:00', '19:00', '01:00'),
  (3, 1, '2026-11-04', '通常出勤', '09:00', NULL, '01:00'),
  (4, 1, '2026-11-05', '欠勤', NULL, NULL, NULL);

-- 社員2: 通常出勤のみ
INSERT INTO attendance_rows (id, employee_id, work_date, category, clock_in, clock_out, break_time) VALUES
  (5, 2, '2026-11-02', '通常出勤', '09:00', '18:00', '01:00'),
  (6, 2, '2026-11-03', '通常出勤', '09:00', '18:00', '01:00');

-- 社員3: 通常出勤 + 退勤なし
INSERT INTO attendance_rows (id, employee_id, work_date, category, clock_in, clock_out, break_time) VALUES
  (7, 3, '2026-11-02', '通常出勤', '10:00', '19:00', '01:00'),
  (8, 3, '2026-11-04', '通常出勤', '09:00', NULL, '01:00');
