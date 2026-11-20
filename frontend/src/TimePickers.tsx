import { useEffect, useId, useRef, useState } from 'react'

/** 装飾用。意味は親ボタンの aria-label に任せる */
function ClockIcon() {
  return (
    <svg
      className="picker-icon"
      viewBox="0 0 16 16"
      width="16"
      height="16"
      aria-hidden="true"
      focusable="false"
    >
      <circle cx="8" cy="8" r="6.25" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M8 4.25V8l2.5 1.75"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

/** 装飾用。意味は親ボタンの aria-label に任せる */
function TimerIcon() {
  return (
    <svg
      className="picker-icon"
      viewBox="0 0 16 16"
      width="16"
      height="16"
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M5.5 2.25h5M8 2.25v1.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <circle cx="8" cy="9" r="5" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M8 6.5V9l1.75 1"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function parseHm(value: string): { h: number; m: number } | null {
  const match = /^(\d{2}):(\d{2})$/.exec(value)
  if (!match) return null
  const h = Number(match[1])
  const m = Number(match[2])
  if (h < 0 || h > 23 || m < 0 || m > 59) return null
  return { h, m }
}

function formatHm(h: number, m: number): string {
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

function wrapHour(h: number): number {
  return ((h % 24) + 24) % 24
}

function wrapMinute(m: number): number {
  return ((m % 60) + 60) % 60
}

type FieldProps = {
  ariaLabel: string
  value: string
  onChange: (next: string) => void
}

/** 出勤・退勤: カレンダー風の時・分ボタンで HH:MM を選ぶ */
export function TimeClockField({ ariaLabel, value, onChange }: FieldProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const panelId = useId()
  const parsed = parseHm(value)
  const [draftH, setDraftH] = useState(parsed?.h ?? 9)
  const [draftM, setDraftM] = useState(parsed?.m ?? 0)

  useEffect(() => {
    if (!open) return
    const current = parseHm(value)
    setDraftH(current?.h ?? 9)
    setDraftM(current?.m ?? 0)
  }, [open, value])

  useEffect(() => {
    if (!open) return
    function onDoc(ev: MouseEvent) {
      if (!rootRef.current?.contains(ev.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [open])

  function apply(h: number, m: number) {
    onChange(formatHm(h, m))
  }

  return (
    <div className="time-field" ref={rootRef}>
      <input
        aria-label={ariaLabel}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <button
        type="button"
        className="picker-toggle"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={`${ariaLabel}を時刻ボタンで選ぶ`}
        onClick={() => setOpen((v) => !v)}
      >
        <ClockIcon />
      </button>
      {open ? (
        <div className="picker-panel calendar-like" id={panelId} role="group" aria-label={`${ariaLabel}の時刻選択`}>
          <div className="picker-spinners">
            <div className="picker-col">
              <span className="picker-col-label">時</span>
              <button
                type="button"
                aria-label={`${ariaLabel} 時を1増やす`}
                onClick={() => {
                  const h = wrapHour(draftH + 1)
                  setDraftH(h)
                  apply(h, draftM)
                }}
              >
                ▲
              </button>
              <span className="picker-value">{String(draftH).padStart(2, '0')}</span>
              <button
                type="button"
                aria-label={`${ariaLabel} 時を1減らす`}
                onClick={() => {
                  const h = wrapHour(draftH - 1)
                  setDraftH(h)
                  apply(h, draftM)
                }}
              >
                ▼
              </button>
            </div>
            <span className="picker-colon">:</span>
            <div className="picker-col">
              <span className="picker-col-label">分</span>
              <button
                type="button"
                aria-label={`${ariaLabel} 分を1増やす`}
                onClick={() => {
                  const m = wrapMinute(draftM + 1)
                  setDraftM(m)
                  apply(draftH, m)
                }}
              >
                ▲
              </button>
              <span className="picker-value">{String(draftM).padStart(2, '0')}</span>
              <button
                type="button"
                aria-label={`${ariaLabel} 分を1減らす`}
                onClick={() => {
                  const m = wrapMinute(draftM - 1)
                  setDraftM(m)
                  apply(draftH, m)
                }}
              >
                ▼
              </button>
            </div>
          </div>
          <div className="picker-presets" role="group" aria-label={`${ariaLabel}の候補`}>
            {['08:00', '09:00', '10:00', '17:00', '18:00', '19:00'].map((preset) => (
              <button
                key={preset}
                type="button"
                aria-label={`${ariaLabel} ${preset}`}
                onClick={() => {
                  const next = parseHm(preset)
                  if (!next) return
                  setDraftH(next.h)
                  setDraftM(next.m)
                  apply(next.h, next.m)
                }}
              >
                {preset}
              </button>
            ))}
          </div>
          <div className="picker-actions">
            <button type="button" onClick={() => { onChange(''); setOpen(false) }}>
              空にする
            </button>
            <button type="button" onClick={() => setOpen(false)}>
              閉じる
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}

/** 休憩: タイマー風の長さボタン。空から開くと 01:00 から */
export function BreakDurationField({ ariaLabel, value, onChange }: FieldProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const panelId = useId()
  const parsed = parseHm(value)
  const [draftH, setDraftH] = useState(parsed?.h ?? 1)
  const [draftM, setDraftM] = useState(parsed?.m ?? 0)

  useEffect(() => {
    if (!open) return
    const current = parseHm(value)
    if (current) {
      setDraftH(current.h)
      setDraftM(current.m)
    } else {
      setDraftH(1)
      setDraftM(0)
      onChange('01:00')
    }
    // 開いた瞬間の既定適用のみ。onChange/value の再実行はしない
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  useEffect(() => {
    if (!open) return
    function onDoc(ev: MouseEvent) {
      if (!rootRef.current?.contains(ev.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [open])

  function setDuration(h: number, m: number) {
    setDraftH(h)
    setDraftM(m)
    onChange(formatHm(h, m))
  }

  function bumpMinute(delta: number) {
    const total = draftH * 60 + draftM + delta
    const clamped = Math.max(0, Math.min(23 * 60 + 59, total))
    setDuration(Math.floor(clamped / 60), clamped % 60)
  }

  return (
    <div className="time-field" ref={rootRef}>
      <input
        aria-label={ariaLabel}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <button
        type="button"
        className="picker-toggle"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={`${ariaLabel}をタイマーで選ぶ`}
        onClick={() => setOpen((v) => !v)}
      >
        <TimerIcon />
      </button>
      {open ? (
        <div className="picker-panel timer-like" id={panelId} role="group" aria-label={`${ariaLabel}の長さ選択`}>
          <p className="picker-hint">休憩は長さ（1時間なら 01:00）</p>
          <div className="picker-spinners">
            <div className="picker-col">
              <span className="picker-col-label">時</span>
              <button
                type="button"
                aria-label={`${ariaLabel} を1時間増やす`}
                onClick={() => bumpMinute(60)}
              >
                ▲
              </button>
              <span className="picker-value">{String(draftH).padStart(2, '0')}</span>
              <button
                type="button"
                aria-label={`${ariaLabel} を1時間減らす`}
                onClick={() => bumpMinute(-60)}
              >
                ▼
              </button>
            </div>
            <span className="picker-colon">:</span>
            <div className="picker-col">
              <span className="picker-col-label">分</span>
              <button
                type="button"
                aria-label={`${ariaLabel} を1分増やす`}
                onClick={() => bumpMinute(1)}
              >
                ▲
              </button>
              <span className="picker-value">{String(draftM).padStart(2, '0')}</span>
              <button
                type="button"
                aria-label={`${ariaLabel} を1分減らす`}
                onClick={() => bumpMinute(-1)}
              >
                ▼
              </button>
            </div>
          </div>
          <div className="picker-presets" role="group" aria-label={`${ariaLabel}の候補`}>
            {['00:00', '01:00', '01:15', '12:00'].map((preset) => (
              <button
                key={preset}
                type="button"
                aria-label={`${ariaLabel} ${preset}`}
                onClick={() => {
                  const next = parseHm(preset)
                  if (!next) return
                  setDuration(next.h, next.m)
                }}
              >
                {preset}
              </button>
            ))}
          </div>
          <div className="picker-actions">
            <button type="button" onClick={() => { onChange(''); setOpen(false) }}>
              空にする
            </button>
            <button type="button" onClick={() => setOpen(false)}>
              閉じる
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
