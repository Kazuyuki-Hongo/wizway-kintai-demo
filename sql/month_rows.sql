-- 指定社員・月の勤怠行。:employee_id と :ym（YYYY-MM）をバインドする。

SELECT
  work_date,
  category,
  COALESCE(clock_in, '') AS clock_in,
  COALESCE(clock_out, '') AS clock_out,
  COALESCE(break_time, '') AS break_time
FROM attendance_rows
WHERE employee_id = :employee_id
  AND substr(work_date, 1, 7) = :ym
ORDER BY work_date;
