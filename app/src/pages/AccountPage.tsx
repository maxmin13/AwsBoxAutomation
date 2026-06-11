import { useState } from 'react'
import { useAuth } from '../AuthContext'

export default function AccountPage() {
  const { hasCredentials, setHasCredentials, requireCreds, withAuth } = useAuth()

  // ── Create IAM user ───────────────────────────────────────────────────────
  const [iamUsername,     setIamUsername]     = useState('')
  const [iamBusy,         setIamBusy]         = useState(false)
  const [iamError,        setIamError]        = useState<string | null>(null)
  const [iamResult,       setIamResult]       = useState<{ accessKeyId: string; secretAccessKey: string } | null>(null)
  const [iamKeyCopied,    setIamKeyCopied]    = useState(false)
  const [iamSecretCopied, setIamSecretCopied] = useState(false)
  const [iamSaved,        setIamSaved]        = useState(false)

  function handleCreateIamUser() {
    if (!iamUsername.trim()) return
    withAuth(async () => {
      setIamBusy(true); setIamError(null); setIamResult(null); setIamSaved(false)
      const res = await window.electronAPI.createIamUser(iamUsername.trim())
      if (res.ok && res.accessKeyId && res.secretAccessKey) {
        const { region } = await window.electronAPI.loadCredentials()
        await window.electronAPI.saveCredentials(res.accessKeyId, res.secretAccessKey, region || 'eu-west-1')
        setIamSaved(true)
        setHasCredentials(true)
        setIamResult({ accessKeyId: res.accessKeyId, secretAccessKey: res.secretAccessKey })
      } else {
        setIamError(res.error ?? 'Unknown error')
      }
      setIamBusy(false)
    })
  }

  function copy(text: string, setCopied: (v: boolean) => void) {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // ── Billing alert ─────────────────────────────────────────────────────────
  const [budgetAmount, setBudgetAmount] = useState('5')
  const [budgetEmail,  setBudgetEmail]  = useState('')
  const [budgetBusy,   setBudgetBusy]   = useState(false)
  const [budgetError,  setBudgetError]  = useState<string | null>(null)
  const [budgetDone,   setBudgetDone]   = useState(false)

  function handleCreateBillingAlert() {
    const amount = parseFloat(budgetAmount)
    if (!amount || !budgetEmail.trim()) return
    requireCreds(() => withAuth(async () => {
      setBudgetBusy(true); setBudgetError(null); setBudgetDone(false)
      const res = await window.electronAPI.createBillingAlert(amount, budgetEmail.trim())
      setBudgetBusy(false)
      res.ok ? setBudgetDone(true) : setBudgetError(res.error ?? 'Unknown error')
    }))
  }

  // ── Cost anomaly detection ─────────────────────────────────────────────────
  const [anomalyThreshold, setAnomalyThreshold] = useState('10')
  const [anomalyEmail,     setAnomalyEmail]     = useState('')
  const [anomalyBusy,      setAnomalyBusy]      = useState(false)
  const [anomalyError,     setAnomalyError]     = useState<string | null>(null)
  const [anomalyDone,      setAnomalyDone]      = useState(false)

  function handleCreateAnomalyDetection() {
    const threshold = parseFloat(anomalyThreshold)
    if (!threshold || !anomalyEmail.trim()) return
    requireCreds(() => withAuth(async () => {
      setAnomalyBusy(true); setAnomalyError(null); setAnomalyDone(false)
      const res = await window.electronAPI.createAnomalyDetection(threshold, anomalyEmail.trim())
      setAnomalyBusy(false)
      res.ok ? setAnomalyDone(true) : setAnomalyError(res.error ?? 'Unknown error')
    }))
  }

  // ── Security toggles ──────────────────────────────────────────────────────
  type S = { busy: boolean; done: boolean; error: string | null }
  const init: S = { busy: false, done: false, error: null }
  const [pwPolicy,  setPwPolicy]  = useState<S>(init)
  const [s3Block,   setS3Block]   = useState<S>(init)
  const [guardDuty, setGuardDuty] = useState<S>(init)
  const [accessAn,  setAccessAn]  = useState<S>(init)

  function runSecurity(fn: () => Promise<{ ok: boolean; error?: string }>, set: (s: S) => void) {
    requireCreds(() => withAuth(async () => {
      set({ busy: true, done: false, error: null })
      const res = await fn()
      set(res.ok ? { busy: false, done: true, error: null } : { busy: false, done: false, error: res.error ?? 'Unknown error' })
    }))
  }

  const isValidEmail = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim())

  const ic = (value: string) =>
    'w-full px-2 py-1 bg-zinc-700 border rounded text-zinc-100 text-xs ' +
    'focus:outline-none focus:border-blue-500 ' +
    (value ? 'border-zinc-400' : 'border-zinc-600')

  const primaryBtn = 'w-full px-3 py-1.5 text-xs bg-blue-700 hover:bg-blue-600 text-white font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
  const lockedBtn  = 'w-full px-3 py-1.5 text-xs bg-blue-700 text-white font-medium rounded opacity-50 cursor-not-allowed'

  const credGated = (extraDisabled: boolean) => ({
    className: hasCredentials ? primaryBtn : lockedBtn,
    disabled:  !!hasCredentials && extraDisabled,
  })

  return (
    <div className="flex flex-col gap-6">

      {/* ── Account Setup ── */}
      <section className="flex flex-col gap-3">
        <div>
          <h2 className="text-sm font-semibold text-zinc-100">Account Setup</h2>
          <p className="text-zinc-500 text-xs">One-time steps after opening a new AWS account.</p>
        </div>

        <div className="grid grid-cols-3 gap-3">

          {/* Create IAM user */}
          <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
            <div>
              <p className="text-zinc-200 text-xs font-semibold">Create IAM User</p>
              <p className="text-zinc-500 text-xs mt-0.5">Creates a user with AdministratorAccess and an access key. Use these instead of root.</p>
            </div>
            <div className="flex flex-col gap-1.5 flex-1">
              <label className="text-zinc-400 text-xs">Username</label>
              <input type="text" value={iamUsername} onChange={e => setIamUsername(e.target.value)}
                placeholder="e.g. admin" autoComplete="off" className={ic(iamUsername)} />
              {iamError && <p className="text-red-400 text-xs">{iamError}</p>}
              {iamResult && (
                <div className="bg-zinc-900 border border-zinc-600 rounded p-2 flex flex-col gap-1">
                  <div className="flex items-center gap-1.5">
                    {iamSaved
                      ? <p className="text-green-400 text-xs font-medium">Saved locally. Copy as backup — secret shown only once.</p>
                      : <p className="text-amber-400 text-xs font-medium">Save now — secret shown only once.</p>
                    }
                  </div>
                  {([['Key ID', iamResult.accessKeyId, iamKeyCopied, setIamKeyCopied], ['Secret', iamResult.secretAccessKey, iamSecretCopied, setIamSecretCopied]] as const).map(([label, val, copied, setCopied]) => (
                    <div key={label} className="flex items-center gap-2">
                      <span className="text-zinc-400 text-xs w-10 shrink-0">{label}</span>
                      <code className="flex-1 text-zinc-100 text-xs font-mono truncate">{val}</code>
                      <button onClick={() => copy(val, setCopied as (v: boolean) => void)} className="text-xs text-zinc-400 hover:text-zinc-200 shrink-0">
                        {copied ? 'Copied' : 'Copy'}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <button onClick={handleCreateIamUser} disabled={!iamUsername.trim() || iamBusy} className={primaryBtn}>
              {iamBusy ? 'Creating...' : 'Create IAM User'}
            </button>
          </div>

          {/* Billing alert */}
          <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
            <div>
              <p className="text-zinc-200 text-xs font-semibold">Set Billing Alert</p>
              <p className="text-zinc-500 text-xs mt-0.5">Creates a monthly budget — email alert when 80% is reached.</p>
            </div>
            <div className="flex flex-col gap-1.5 flex-1">
              <div className="flex gap-2">
                <div className="w-20 shrink-0">
                  <label className="text-zinc-400 text-xs">Limit (USD/mo)</label>
                  <input type="number" min="1" value={budgetAmount} onChange={e => setBudgetAmount(e.target.value)} className={ic(budgetAmount) + ' mt-1'} />
                </div>
                <div className="flex-1 min-w-0">
                  <label className="text-zinc-400 text-xs">Alert email</label>
                  <input type="email" value={budgetEmail} onChange={e => setBudgetEmail(e.target.value)} placeholder="you@example.com" className={ic(budgetEmail) + ' mt-1'} />
                </div>
              </div>
              {budgetError && <p className="text-red-400 text-xs">{budgetError}</p>}
              {budgetDone  && <p className="text-green-400 text-xs">Budget created — alert at 80% of ${budgetAmount}/month.</p>}
            </div>
            <button onClick={handleCreateBillingAlert} {...credGated(!budgetAmount || !isValidEmail(budgetEmail) || budgetBusy || budgetDone)}>
              {budgetBusy ? 'Creating...' : budgetDone ? 'Alert Created' : 'Set Billing Alert'}
            </button>
          </div>

          {/* Cost anomaly detection */}
          <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
            <div>
              <p className="text-zinc-200 text-xs font-semibold">Cost Anomaly Detection</p>
              <p className="text-zinc-500 text-xs mt-0.5">Immediate email alert when spending spikes unexpectedly, regardless of your monthly budget.</p>
            </div>
            <div className="flex flex-col gap-1.5 flex-1">
              <div className="flex gap-2">
                <div className="w-20 shrink-0">
                  <label className="text-zinc-400 text-xs">Threshold (USD)</label>
                  <input type="number" min="1" value={anomalyThreshold} onChange={e => setAnomalyThreshold(e.target.value)} className={ic(anomalyThreshold) + ' mt-1'} />
                </div>
                <div className="flex-1 min-w-0">
                  <label className="text-zinc-400 text-xs">Alert email</label>
                  <input type="email" value={anomalyEmail} onChange={e => setAnomalyEmail(e.target.value)} placeholder="you@example.com" className={ic(anomalyEmail) + ' mt-1'} />
                </div>
              </div>
              {anomalyError && <p className="text-red-400 text-xs">{anomalyError}</p>}
              {anomalyDone  && <p className="text-green-400 text-xs">Enabled — alerts on spikes above ${anomalyThreshold}.</p>}
            </div>
            <button onClick={handleCreateAnomalyDetection} {...credGated(!anomalyThreshold || !isValidEmail(anomalyEmail) || anomalyBusy || anomalyDone)}>
              {anomalyBusy ? 'Enabling...' : anomalyDone ? 'Enabled' : 'Enable Anomaly Detection'}
            </button>
          </div>

        </div>
      </section>

      {/* ── Security ── */}
      <section className="flex flex-col gap-3">
        <div>
          <h2 className="text-sm font-semibold text-zinc-100">Security</h2>
          <p className="text-zinc-500 text-xs">One-click hardening for a new AWS account.</p>
        </div>

        <div className="grid grid-cols-4 gap-3">
          {([
            ['IAM Password Policy',   'Enforces min 12 chars, uppercase, numbers, symbols, and 90-day rotation.',  pwPolicy,  setPwPolicy,  () => window.electronAPI.setIamPasswordPolicy(),  'Apply Policy',  'Applying...', 'Applied'],
            ['S3 Block Public Access', 'Prevents any S3 bucket from being made publicly accessible, account-wide.', s3Block,   setS3Block,   () => window.electronAPI.blockS3PublicAccess(),    'Block Access',  'Blocking...', 'Blocked'],
            ['GuardDuty',             'Monitors for suspicious API calls, unusual logins, and crypto mining.',      guardDuty, setGuardDuty, () => window.electronAPI.enableGuardDuty(),        'Enable',        'Enabling...', 'Enabled'],
            ['IAM Access Analyzer',   'Flags IAM policies and resources accessible from outside your account.',    accessAn,  setAccessAn,  () => window.electronAPI.enableAccessAnalyzer(),   'Enable',        'Enabling...', 'Enabled'],
          ] as const).map(([title, desc, state, setter, fn, label, busyLabel, doneLabel]) => (
            <div key={title} className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
              <div className="flex-1">
                <p className="text-zinc-200 text-xs font-semibold leading-snug">{title}</p>
                <p className="text-zinc-500 text-xs leading-snug mt-1">{desc}</p>
                {state.error && <p className="text-red-400 text-xs mt-1">{state.error}</p>}
                {state.done  && <p className="text-green-400 text-xs mt-1">Done.</p>}
              </div>
              <button
                onClick={() => runSecurity(fn, setter as (s: S) => void)}
                {...credGated(state.busy || state.done)}
              >
                {state.busy ? busyLabel : state.done ? doneLabel : label}
              </button>
            </div>
          ))}
        </div>
      </section>

    </div>
  )
}
