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
  stored: boolean
}

type Summary = {
  workday_count: number
  total_worked_hours: number
  overtime_hours: number
  missing_clock_out_count: number
}

type Draft = {
  category: string
  clock_in: string
  clock_out: string
  break_time: string
}

function draftsFrom(rows: AttendanceRow[]): Record<string, Draft> {
  const next: Record<string, Draft> = {}
  for (const row of rows) {
    if (!row.stored) continue
    next[row.work_date] = {
      category: row.category,
      clock_in: row.clock_in,
      clock_out: row.clock_out,
      break_time: row.break_time,
    }
  }
  return next
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
  const [drafts, setDrafts] = useState<Record<string, Draft>>({})
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
      const nextRows = rowsBody.rows || []
      setRows(nextRows)
      setDrafts(draftsFrom(nextRows))
      setSummary(summaryBody.summary)
    } catch (err: unknown) {
      setRows([])
      setDrafts({})
      setSummary(null)
      setError(String(err))
    }
  }, [employeeId, ym])

  useEffect(() => {
    loadMonth()
  }, [loadMonth])

  function updateDraft(workDate: string, patch: Partial<Draft>) {
    setDrafts((current) => {
      const prev = current[workDate]
      if (!prev) return current
      const next = { ...prev, ...patch }
      if (patch.category === '欠勤') {
        next.clock_in = ''
        next.clock_out = ''
        next.break_time = ''
      }
      return { ...current, [workDate]: next }
    })
  }

  async function saveDay(workDate: string) {
    const draft = drafts[workDate]
    if (!API_URL || employeeId === '' || !draft) return
    setError('')
    try {
      const res = await fetch(
        `${API_URL}/employees/${employeeId}/months/${ym}/days/${workDate}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(draft),
        },
      )
      const payload = (await res.json().catch(() => ({}))) as { reason?: string }
      if (!res.ok) {
        setError(payload.reason || `保存 HTTP ${res.status}`)
        return
      }
      await loadMonth()
    } catch (err: unknown) {
      setError(String(err))
    }
  }

  return (
    <main>
      <h1>勤怠デモ</h1>
      <p className="note">
        保存済みの日は、この実行環境に保存できます。やり直すと初期データに戻ります。
      </p>

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
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const draft = drafts[row.work_date]
            if (!row.stored || !draft) {
              return (
                <tr key={row.work_date}>
                  <td>{row.work_date}</td>
                  <td>{cell(row.category)}</td>
                  <td>{cell(row.clock_in)}</td>
                  <td>{cell(row.clock_out)}</td>
                  <td>{cell(row.break_time)}</td>
                  <td />
                </tr>
              )
            }
            return (
              <tr key={row.work_date}>
                <td>{row.work_date}</td>
                <td>
                  <select
                    aria-label={`${row.work_date} 区分`}
                    value={draft.category}
                    onChange={(e) =>
                      updateDraft(row.work_date, { category: e.target.value })
                    }
                  >
                    <option value="通常出勤">通常出勤</option>
                    <option value="欠勤">欠勤</option>
                  </select>
                </td>
                <td>
                  <input
                    aria-label={`${row.work_date} 出勤`}
                    value={draft.clock_in}
                    onChange={(e) =>
                      updateDraft(row.work_date, { clock_in: e.target.value })
                    }
                  />
                </td>
                <td>
                  <input
                    aria-label={`${row.work_date} 退勤`}
                    value={draft.clock_out}
                    onChange={(e) =>
                      updateDraft(row.work_date, { clock_out: e.target.value })
                    }
                  />
                </td>
                <td>
                  <input
                    aria-label={`${row.work_date} 休憩`}
                    value={draft.break_time}
                    onChange={(e) =>
                      updateDraft(row.work_date, { break_time: e.target.value })
                    }
                  />
                </td>
                <td>
                  <button type="button" onClick={() => saveDay(row.work_date)}>
                    {row.work_date} を保存
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </main>
  )
}
