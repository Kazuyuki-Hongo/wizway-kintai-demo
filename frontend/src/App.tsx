import { useCallback, useEffect, useState } from 'react'

const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

type Employee = {
  id: number
  display_name: string
}

type AttendanceRow = {
  work_date: string
  category: string
  clock_in: string
  clock_out: string
  break_time: string
}

type Summary = {
  workday_count: number
  total_worked_hours: number
  overtime_hours: number
  missing_clock_out_count: number
}

function cell(value: string) {
  if (!value) return <span className="empty">（空）</span>
  return value
}

export default function App() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [employeeId, setEmployeeId] = useState<number | ''>('')
  const [ym, setYm] = useState('2026-11')
  const [rows, setRows] = useState<AttendanceRow[]>([])
  const [summary, setSummary] = useState<Summary | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!API_URL) {
      setError('VITE_API_URL が未設定です')
      return
    }
    fetch(`${API_URL}/employees`)
      .then(async (res) => {
        if (!res.ok) throw new Error(`社員一覧 HTTP ${res.status}`)
        return res.json() as Promise<{ employees: Employee[] }>
      })
      .then((data) => {
        setEmployees(data.employees || [])
        if (data.employees?.length) {
          setEmployeeId(data.employees[0].id)
        }
      })
      .catch((err: unknown) => setError(String(err)))
  }, [])

  const loadMonth = useCallback(async () => {
    if (!API_URL || employeeId === '') return
    setError('')
    try {
      const [rowsRes, summaryRes] = await Promise.all([
        fetch(`${API_URL}/employees/${employeeId}/months/${ym}`),
        fetch(`${API_URL}/employees/${employeeId}/months/${ym}/summary`),
      ])
      if (!rowsRes.ok) throw new Error(`勤怠行 HTTP ${rowsRes.status}`)
      if (!summaryRes.ok) throw new Error(`合計 HTTP ${summaryRes.status}`)
      const rowsBody = (await rowsRes.json()) as { rows: AttendanceRow[] }
      const summaryBody = (await summaryRes.json()) as { summary: Summary }
      setRows(rowsBody.rows || [])
      setSummary(summaryBody.summary)
    } catch (err: unknown) {
      setRows([])
      setSummary(null)
      setError(String(err))
    }
  }, [employeeId, ym])

  useEffect(() => {
    loadMonth()
  }, [loadMonth])

  return (
    <main>
      <h1>勤怠デモ（読み取り専用）</h1>
      <p className="note">ダミーデータのみ。保存操作はありません。</p>

      <div className="controls">
        <label>
          社員
          <select
            value={employeeId === '' ? '' : String(employeeId)}
            onChange={(e) =>
              setEmployeeId(e.target.value ? Number(e.target.value) : '')
            }
          >
            {employees.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.display_name}
              </option>
            ))}
          </select>
        </label>
        <label>
          月
          <input
            type="month"
            value={ym}
            onChange={(e) => setYm(e.target.value)}
          />
        </label>
      </div>

      {error ? <p className="error">{error}</p> : null}

      {summary ? (
        <dl className="summary">
          <div>
            <dt>出勤日数</dt>
            <dd>{summary.workday_count}</dd>
          </div>
          <div>
            <dt>総実働（時間）</dt>
            <dd>{summary.total_worked_hours}</dd>
          </div>
          <div>
            <dt>8時間超過（時間）</dt>
            <dd>{summary.overtime_hours}</dd>
          </div>
          <div>
            <dt>退勤なし件数</dt>
            <dd>{summary.missing_clock_out_count}</dd>
          </div>
        </dl>
      ) : null}

      <table>
        <thead>
          <tr>
            <th>日付</th>
            <th>区分</th>
            <th>出勤</th>
            <th>退勤</th>
            <th>休憩</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.work_date}>
              <td>{row.work_date}</td>
              <td>{row.category}</td>
              <td>{cell(row.clock_in)}</td>
              <td>{cell(row.clock_out)}</td>
              <td>{cell(row.break_time)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  )
}
