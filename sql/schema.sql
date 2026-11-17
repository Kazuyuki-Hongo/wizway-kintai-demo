-- ダミー勤怠デモ用。本番 MariaDB には繋がない。

CREATE TABLE employees (
  id INTEGER PRIMARY KEY,
  display_name TEXT NOT NULL
);

CREATE TABLE attendance_rows (
  id INTEGER PRIMARY KEY,
  employee_id INTEGER NOT NULL REFERENCES employees (id),
  work_date TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('通常出勤', '欠勤')),
  clock_in TEXT,
  clock_out TEXT,
  break_time TEXT,
  UNIQUE (employee_id, work_date)
);
