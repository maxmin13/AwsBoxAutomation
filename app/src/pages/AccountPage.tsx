import { Fragment, useEffect, useState } from 'react'
import { useAuth } from '../AuthContext'
import LoginPage from './LoginPage'

const WIZARD_STEPS = [
  { id: 1, title: 'Root MFA'  },
  { id: 2, title: 'IAM User'  },
  { id: 3, title: 'Alerts'    },
  { id: 4, title: 'Security'  },
]

export default function AccountPage() {
  const { hasCredentials, setHasCredentials, requireCreds, withAuth } = useAuth()

  const [region, setRegion] = useState<string | null>(null)
  useEffect(() => {
    window.electronAPI.loadCredentials().then(c => { if (c.region) setRegion(c.region) })
  }, [])

  // ── Page mode ─────────────────────────────────────────────────────────────
  const [pageMode,     setPageMode]     = useState<'loading' | 'login' | 'wizard' | 'summary' | 'detail'>('loading')
  const [wizardStep,   setWizardStep]   = useState(1)
  const [isRootCaller, setIsRootCaller] = useState(false)
  const [accountId,    setAccountId]    = useState<string | null>(null)
  const [keysPresent,  setKeysPresent]  = useState(false)

  // ── Root MFA ──────────────────────────────────────────────────────────────
  const [mfaEnabled, setMfaEnabled] = useState(false)
  const [mfaStep,    setMfaStep]    = useState(0) // 0=idle, 1=QR shown, 2=code entry
  const [mfaSerial,  setMfaSerial]  = useState('')
  const [mfaQrCode,  setMfaQrCode]  = useState('')
  const [mfaSecret,  setMfaSecret]  = useState('')
  const [mfaCode1,   setMfaCode1]   = useState('')
  const [mfaCode2,   setMfaCode2]   = useState('')
  const [mfaBusy,    setMfaBusy]    = useState(false)
  const [mfaError,   setMfaError]   = useState<string | null>(null)
  const [mfaDone,    setMfaDone]    = useState(false)

  // ── Create IAM user ───────────────────────────────────────────────────────
  const IAM_POLICY_ARN = 'arn:aws:iam::aws:policy/AdministratorAccess'

  const [iamUsername,        setIamUsername]        = useState('')
  const [iamDeleteRootKeys,  setIamDeleteRootKeys]  = useState(true)
  const [iamBusy,            setIamBusy]            = useState(false)
  const [iamError,           setIamError]           = useState<string | null>(null)
  const [iamResult,          setIamResult]          = useState<{ accessKeyId: string; secretAccessKey: string } | null>(null)
  const [iamKeyCopied,       setIamKeyCopied]       = useState(false)
  const [iamSecretCopied,    setIamSecretCopied]    = useState(false)
  const [iamSaved,           setIamSaved]           = useState(false)
  const [iamRootKeysDeleted, setIamRootKeysDeleted] = useState(false)

  // ── Billing alert ─────────────────────────────────────────────────────────
  const [budgetAmount, setBudgetAmount] = useState('5')
  const [budgetEmail,  setBudgetEmail]  = useState('')
  const [budgetPhone,  setBudgetPhone]  = useState('')
  const [budgetBusy,   setBudgetBusy]   = useState(false)
  const [budgetError,  setBudgetError]  = useState<string | null>(null)
  const [budgetDone,   setBudgetDone]   = useState(false)

  // ── Cost anomaly detection ────────────────────────────────────────────────
  const [anomalyThreshold, setAnomalyThreshold] = useState('10')
  const [anomalyEmail,     setAnomalyEmail]     = useState('')
  const [anomalyPhone,     setAnomalyPhone]     = useState('')
  const [anomalyBusy,      setAnomalyBusy]      = useState(false)
  const [anomalyError,     setAnomalyError]     = useState<string | null>(null)
  const [anomalyDone,      setAnomalyDone]      = useState(false)

  // ── Root login alarm ──────────────────────────────────────────────────────
  const [alarmEmail, setAlarmEmail] = useState('')
  const [alarmPhone, setAlarmPhone] = useState('')
  const [alarmBusy,  setAlarmBusy]  = useState(false)
  const [alarmError, setAlarmError] = useState<string | null>(null)
  const [alarmDone,  setAlarmDone]  = useState(false)

  // ── Security toggles ──────────────────────────────────────────────────────
  type S = { busy: boolean; done: boolean; error: string | null }
  const init: S = { busy: false, done: false, error: null }
  const [pwPolicy,  setPwPolicy]  = useState<S>(init)
  const [s3Block,   setS3Block]   = useState<S>(init)
  const [guardDuty, setGuardDuty] = useState<S>(init)
  const [accessAn,  setAccessAn]  = useState<S>(init)

  // ── SMS security alert ────────────────────────────────────────────────────
  const [smsPhone, setSmsPhone] = useState('')
  const [smsBusy,  setSmsBusy]  = useState(false)
  const [smsError, setSmsError] = useState<string | null>(null)
  const [smsDone,  setSmsDone]  = useState(false)

  // ── Page mode detection on load ───────────────────────────────────────────
  useEffect(() => {
    if (hasCredentials === null) return
    if (!hasCredentials) { setPageMode('login'); return }
    window.electronAPI.checkRootCredentials().then(res => {
      if (res.ok) {
        setMfaEnabled(res.mfaEnabled ?? false)
        setIsRootCaller(res.isRoot ?? false)
        setAccountId(res.accountId ?? null)
        setKeysPresent(res.keysPresent ?? false)
        if (res.mfaEnabled) setMfaDone(true)
        if (!res.isRoot) {
          setPageMode('detail')
        } else if (!res.mfaEnabled) {
          setWizardStep(1); setPageMode('wizard')
        } else {
          setWizardStep(2); setPageMode('wizard')
        }
      } else {
        setPageMode('detail')
      }
    })
  }, [hasCredentials])

  // ── Handlers ──────────────────────────────────────────────────────────────

  function handleMfaStart() {
    if (!isRootCaller) { setMfaError('Root credentials required — you are currently signed in as an IAM user.'); return }
    requireCreds(() => withAuth(async () => {
      setMfaBusy(true); setMfaError(null)
      const res = await window.electronAPI.createVirtualMfaDevice()
      setMfaBusy(false)
      if (res.ok && res.serialNumber && res.qrCodePng) {
        setMfaSerial(res.serialNumber); setMfaQrCode(res.qrCodePng); setMfaSecret(res.base32Seed ?? '')
        setMfaStep(1)
      } else {
        setMfaError(res.error ?? 'Unknown error')
      }
    }))
  }

  function handleMfaActivate() {
    if (mfaCode1.length < 6 || mfaCode2.length < 6) return
    if (!isRootCaller) { setMfaError('Root credentials required — you are currently signed in as an IAM user.'); return }
    requireCreds(() => withAuth(async () => {
      setMfaBusy(true); setMfaError(null)
      const res = await window.electronAPI.enableMfaDevice(mfaSerial, mfaCode1.trim(), mfaCode2.trim())
      setMfaBusy(false)
      if (res.ok) {
        setMfaDone(true); setMfaEnabled(true); setMfaStep(0)
      } else {
        setMfaError(res.error ?? 'Unknown error')
      }
    }))
  }

  function handleCreateIamUser() {
    if (!iamUsername.trim()) return
    withAuth(async () => {
      setIamBusy(true); setIamError(null); setIamResult(null); setIamSaved(false); setIamRootKeysDeleted(false)
      const res = await window.electronAPI.createIamUser(iamUsername.trim(), IAM_POLICY_ARN, iamDeleteRootKeys)
      if (res.ok && res.accessKeyId && res.secretAccessKey) {
        const { region } = await window.electronAPI.loadCredentials()
        await window.electronAPI.saveCredentials(res.accessKeyId, res.secretAccessKey, region || 'eu-west-1')
        setIamSaved(true); setHasCredentials(true); setIsRootCaller(false)
        setIamResult({ accessKeyId: res.accessKeyId, secretAccessKey: res.secretAccessKey })
        if (res.rootKeysDeleted) { setIamRootKeysDeleted(true); setKeysPresent(false) }
      } else {
        setIamError(res.error ?? 'Unknown error')
      }
      setIamBusy(false)
    })
  }

  function handleCreateBillingAlert() {
    const amount = parseFloat(budgetAmount)
    if (!amount || !budgetEmail.trim()) return
    requireCreds(() => withAuth(async () => {
      setBudgetBusy(true); setBudgetError(null); setBudgetDone(false)
      const res = await window.electronAPI.createBillingAlert(amount, budgetEmail.trim(), budgetPhone.trim() || undefined)
      setBudgetBusy(false)
      res.ok ? setBudgetDone(true) : setBudgetError(res.error ?? 'Unknown error')
    }))
  }

  function handleCreateAnomalyDetection() {
    const threshold = parseFloat(anomalyThreshold)
    if (!threshold || !anomalyEmail.trim()) return
    requireCreds(() => withAuth(async () => {
      setAnomalyBusy(true); setAnomalyError(null); setAnomalyDone(false)
      const res = await window.electronAPI.createAnomalyDetection(threshold, anomalyEmail.trim(), anomalyPhone.trim() || undefined)
      setAnomalyBusy(false)
      res.ok ? setAnomalyDone(true) : setAnomalyError(res.error ?? 'Unknown error')
    }))
  }

  function handleCreateRootAlarm() {
    if (!alarmEmail.trim()) return
    requireCreds(() => withAuth(async () => {
      setAlarmBusy(true); setAlarmError(null); setAlarmDone(false)
      const res = await window.electronAPI.createRootLoginAlarm(alarmEmail.trim(), alarmPhone.trim() || undefined)
      setAlarmBusy(false)
      res.ok ? setAlarmDone(true) : setAlarmError(res.error ?? 'Unknown error')
    }))
  }

  function handleEnableSmsAlert() {
    if (!smsPhone.trim()) return
    if (!guardDuty.done) { setSmsError('Enable GuardDuty first — SMS alerts require an active GuardDuty detector.'); return }
    requireCreds(() => withAuth(async () => {
      setSmsBusy(true); setSmsError(null); setSmsDone(false)
      const res = await window.electronAPI.enableSmsSecurityAlert(smsPhone.trim())
      setSmsBusy(false)
      res.ok ? setSmsDone(true) : setSmsError(res.error ?? 'Unknown error')
    }))
  }

  function runSecurity(fn: () => Promise<{ ok: boolean; error?: string }>, set: (s: S) => void) {
    requireCreds(() => withAuth(async () => {
      set({ busy: true, done: false, error: null })
      const res = await fn()
      set(res.ok ? { busy: false, done: true, error: null } : { busy: false, done: false, error: res.error ?? 'Unknown error' })
    }))
  }

  function copy(text: string, setCopied: (v: boolean) => void) {
    navigator.clipboard.writeText(text); setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  const isValidEmail  = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim())
  const isValidPhone  = (v: string) => /^\+\d{7,15}$/.test(v.trim())
  const pricingLink   = (url: string, label = 'AWS pricing ↗') => (
    <button onClick={() => window.electronAPI.openExternal(url)}
      className="underline text-zinc-500 hover:text-zinc-300 transition-colors">{label}</button>
  )

  const ic = (value: string) =>
    'w-full px-2 py-1 bg-zinc-700 border rounded text-zinc-100 text-xs ' +
    'focus:outline-none focus:border-blue-500 ' +
    (value ? 'border-zinc-400' : 'border-zinc-600')

  const primaryBtn = 'w-full px-3 py-1.5 text-xs bg-blue-700 hover:bg-blue-600 text-white font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
  const lockedBtn  = 'w-full px-3 py-1.5 text-xs bg-blue-700 text-white font-medium rounded opacity-50 cursor-not-allowed'

  // Gate for steps 3-4 and grid mode — requires non-root credentials
  const iamReady = iamSaved || !isRootCaller
  const iamGated = (extraDisabled: boolean) => ({
    className: iamReady ? primaryBtn : lockedBtn,
    disabled:  iamReady && extraDisabled,
  })

  // ── Card fragments (shared between wizard and grid) ───────────────────────

  const mfaCard = (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-zinc-200 text-xs font-semibold">Root MFA</p>
          <p className="text-zinc-500 text-xs mt-0.5">Virtual MFA device for root. Requires Google Authenticator, Authy, or any TOTP app.</p>
          <p className="text-zinc-600 text-xs mt-0.5">Free</p>
        </div>
        <span className={`shrink-0 flex items-center gap-1 text-xs px-1.5 py-0.5 rounded ${mfaEnabled || mfaDone ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${mfaEnabled || mfaDone ? 'bg-green-400' : 'bg-red-400'}`} />
          {mfaEnabled || mfaDone ? 'Enabled' : 'Disabled'}
        </span>
      </div>
      <div className="flex-1 flex flex-col gap-2">
        {mfaError && <p className="text-red-400 text-xs">{mfaError}</p>}
        {mfaStep === 0 && !mfaDone && (
          <p className="text-zinc-500 text-xs">Click below to generate a QR code, then scan it with your authenticator app.</p>
        )}
        {mfaStep === 1 && (
          <>
            <p className="text-zinc-400 text-xs">Scan this QR code in your authenticator app, then click Next.</p>
            <div className="flex justify-center bg-white rounded p-1.5">
              <img src={`data:image/png;base64,${mfaQrCode}`} alt="MFA QR code" className="w-28 h-28" />
            </div>
            {mfaSecret && (
              <details className="text-xs">
                <summary className="text-zinc-500 cursor-pointer select-none">Manual entry code</summary>
                <code className="block text-zinc-300 break-all mt-1 leading-relaxed">{mfaSecret}</code>
              </details>
            )}
          </>
        )}
        {mfaStep === 2 && (
          <>
            <p className="text-zinc-400 text-xs">Enter two consecutive 6-digit codes from your authenticator app.</p>
            <input type="text" inputMode="numeric" maxLength={6} value={mfaCode1}
              onChange={e => setMfaCode1(e.target.value.replace(/\D/g, ''))}
              placeholder="Code 1" className={ic(mfaCode1)} />
            <input type="text" inputMode="numeric" maxLength={6} value={mfaCode2}
              onChange={e => setMfaCode2(e.target.value.replace(/\D/g, ''))}
              placeholder="Code 2 (next 30s window)" className={ic(mfaCode2)} />
          </>
        )}
        {mfaDone && <p className="text-green-400 text-xs">MFA activated — root is now protected.</p>}
      </div>
      {!mfaDone && !mfaEnabled && mfaStep === 0 && (
        <button onClick={handleMfaStart} disabled={mfaBusy} className={primaryBtn}>
          {mfaBusy ? 'Generating QR...' : 'Set Up Root MFA'}
        </button>
      )}
      {(mfaDone || mfaEnabled) && mfaStep === 0 && (
        <p className="text-zinc-600 text-xs">MFA is permanent and cannot be removed from this app.</p>
      )}
      {mfaStep === 1 && <button onClick={() => setMfaStep(2)} className={primaryBtn}>Next: Enter Codes →</button>}
      {mfaStep === 2 && (
        <div className="flex flex-col gap-1.5">
          <button onClick={handleMfaActivate} disabled={mfaBusy || mfaCode1.length < 6 || mfaCode2.length < 6} className={primaryBtn}>
            {mfaBusy ? 'Activating...' : 'Activate MFA'}
          </button>
          <button onClick={() => setMfaStep(1)} disabled={mfaBusy} className="text-xs text-zinc-500 hover:text-zinc-300 text-center py-0.5">← Back</button>
        </div>
      )}
    </div>
  )

  const iamCard = (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
      <div>
        <p className="text-zinc-200 text-xs font-semibold">Create IAM User</p>
        <p className="text-zinc-500 text-xs mt-0.5">Creates an administrator user and an access key. Credentials switch to IAM automatically.</p>
        <p className="text-zinc-600 text-xs mt-0.5">Free</p>
      </div>
      <div className="flex flex-col gap-1.5 flex-1">
        <label className="text-zinc-400 text-xs">Username</label>
        <input type="text" value={iamUsername}
          onChange={e => { setIamUsername(e.target.value); setIamResult(null); setIamSaved(false) }}
          placeholder="e.g. admin" autoComplete="off" className={ic(iamUsername)} />
        {iamError && <p className="text-red-400 text-xs">{iamError}</p>}
        {iamResult && (
          <div className="bg-zinc-900 border border-zinc-600 rounded p-2 flex flex-col gap-1">
            {iamSaved
              ? <p className="text-green-400 text-xs font-medium">Saved locally. Copy as backup — secret shown only once.</p>
              : <p className="text-amber-400 text-xs font-medium">Save now — secret shown only once.</p>
            }
            {([['Key ID', iamResult.accessKeyId, iamKeyCopied, setIamKeyCopied], ['Secret', iamResult.secretAccessKey, iamSecretCopied, setIamSecretCopied]] as const).map(([label, val, copied, setCopied]) => (
              <div key={label} className="flex items-center gap-2">
                <span className="text-zinc-400 text-xs w-10 shrink-0">{label}</span>
                <code className="flex-1 text-zinc-100 text-xs font-mono truncate">{val}</code>
                <button onClick={() => copy(val, setCopied as (v: boolean) => void)} className="text-xs text-zinc-400 hover:text-zinc-200 shrink-0">
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
            ))}
            {iamRootKeysDeleted && <p className="text-green-400 text-xs mt-0.5">Root access keys deleted.</p>}
          </div>
        )}
      </div>
      <div className="flex flex-col gap-1">
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input type="checkbox" checked={iamDeleteRootKeys} onChange={e => setIamDeleteRootKeys(e.target.checked)} className="accent-blue-500" />
          <span className="text-zinc-400 text-xs">Delete root access keys after creating</span>
        </label>
        <p className="text-zinc-600 text-xs pl-5">Only removes API access — you can still sign in to the AWS console as root with your email and password.</p>
      </div>
      <button onClick={handleCreateIamUser} disabled={!iamUsername.trim() || iamBusy} className={primaryBtn}>
        {iamBusy ? 'Creating...' : 'Create IAM User'}
      </button>
    </div>
  )

  const billingCard = (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
      <div>
        <p className="text-zinc-200 text-xs font-semibold">Set Billing Alert</p>
        <p className="text-zinc-500 text-xs mt-0.5">Creates a monthly budget — email alert when 80% is reached.</p>
        <p className="text-zinc-600 text-xs mt-0.5">Free (first 2 budgets/account) · {pricingLink('https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/')}</p>
      </div>
      <div className="flex flex-col gap-1.5 flex-1">
        <div className="flex gap-2">
          <div className="w-20 shrink-0">
            <label className="text-zinc-400 text-xs">Limit (USD/mo)</label>
            <input type="number" min="1" value={budgetAmount} onChange={e => setBudgetAmount(e.target.value)} onWheel={e => e.currentTarget.blur()} className={ic(budgetAmount) + ' mt-1'} />
          </div>
          <div className="flex-1 min-w-0">
            <label className="text-zinc-400 text-xs">Alert email</label>
            <input type="email" value={budgetEmail} onChange={e => setBudgetEmail(e.target.value)} placeholder="you@example.com" className={ic(budgetEmail) + ' mt-1'} />
          </div>
        </div>
        <label className="text-zinc-400 text-xs">SMS phone <span className="text-zinc-600">(optional)</span></label>
        <input type="tel" value={budgetPhone} onChange={e => setBudgetPhone(e.target.value)} placeholder="+353871234567" className={ic(budgetPhone)} />
        {budgetError && <p className="text-red-400 text-xs">{budgetError}</p>}
        {budgetDone  && <p className="text-green-400 text-xs">Budget created — alert at 80% of ${budgetAmount}/month.</p>}
      </div>
      <button onClick={handleCreateBillingAlert} {...iamGated(!budgetAmount || !isValidEmail(budgetEmail) || (!!budgetPhone && !isValidPhone(budgetPhone)) || budgetBusy || budgetDone)}>
        {budgetBusy ? 'Creating...' : budgetDone ? 'Alert Created' : 'Set Billing Alert'}
      </button>
    </div>
  )

  const anomalyCard = (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
      <div>
        <p className="text-zinc-200 text-xs font-semibold">Cost Anomaly Detection</p>
        <p className="text-zinc-500 text-xs mt-0.5">Immediate email alert when spending spikes unexpectedly, regardless of your monthly budget.</p>
        <p className="text-zinc-600 text-xs mt-0.5">Free · {pricingLink('https://aws.amazon.com/aws-cost-management/aws-cost-anomaly-detection/pricing/')}</p>
      </div>
      <div className="flex flex-col gap-1.5 flex-1">
        <div className="flex gap-2">
          <div className="w-20 shrink-0">
            <label className="text-zinc-400 text-xs">Threshold (USD)</label>
            <input type="number" min="1" value={anomalyThreshold} onChange={e => setAnomalyThreshold(e.target.value)} onWheel={e => e.currentTarget.blur()} className={ic(anomalyThreshold) + ' mt-1'} />
          </div>
          <div className="flex-1 min-w-0">
            <label className="text-zinc-400 text-xs">Alert email</label>
            <input type="email" value={anomalyEmail} onChange={e => setAnomalyEmail(e.target.value)} placeholder="you@example.com" className={ic(anomalyEmail) + ' mt-1'} />
          </div>
        </div>
        <label className="text-zinc-400 text-xs">SMS phone <span className="text-zinc-600">(optional)</span></label>
        <input type="tel" value={anomalyPhone} onChange={e => setAnomalyPhone(e.target.value)} placeholder="+353871234567" className={ic(anomalyPhone)} />
        {anomalyError && <p className="text-red-400 text-xs">{anomalyError}</p>}
        {anomalyDone  && <p className="text-green-400 text-xs">Enabled — alerts on spikes above ${anomalyThreshold}.</p>}
      </div>
      <button onClick={handleCreateAnomalyDetection} {...iamGated(!anomalyThreshold || !isValidEmail(anomalyEmail) || (!!anomalyPhone && !isValidPhone(anomalyPhone)) || anomalyBusy || anomalyDone)}>
        {anomalyBusy ? 'Enabling...' : anomalyDone ? 'Enabled' : 'Enable Anomaly Detection'}
      </button>
    </div>
  )

  const alarmCard = (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
      <div>
        <p className="text-zinc-200 text-xs font-semibold">Root Login Alarm</p>
        <p className="text-zinc-500 text-xs mt-0.5">Email alert on every root console sign-in via EventBridge + SNS.</p>
        <p className="text-zinc-600 text-xs mt-0.5">Free · {pricingLink('https://aws.amazon.com/sns/pricing/')}</p>
      </div>
      <div className="flex flex-col gap-1.5 flex-1">
        <label className="text-zinc-400 text-xs">Alert email</label>
        <input type="email" value={alarmEmail} onChange={e => setAlarmEmail(e.target.value)} placeholder="you@example.com" className={ic(alarmEmail)} />
        <label className="text-zinc-400 text-xs">SMS phone <span className="text-zinc-600">(optional)</span></label>
        <input type="tel" value={alarmPhone} onChange={e => setAlarmPhone(e.target.value)} placeholder="+353871234567" className={ic(alarmPhone)} />
        {alarmError && <p className="text-red-400 text-xs">{alarmError}</p>}
        {alarmDone  && <p className="text-green-400 text-xs">Alarm created — confirm the subscription email from AWS.</p>}
      </div>
      <button onClick={handleCreateRootAlarm} {...iamGated(!isValidEmail(alarmEmail) || (!!alarmPhone && !isValidPhone(alarmPhone)) || alarmBusy || alarmDone)}>
        {alarmBusy ? 'Creating...' : alarmDone ? 'Alarm Created' : 'Create Root Login Alarm'}
      </button>
    </div>
  )

  const securityToggleCards = (
    [
      ['IAM Password Policy',   'Enforces min 12 chars, uppercase, numbers, symbols, and 90-day rotation.',  pwPolicy,  setPwPolicy,  () => window.electronAPI.setIamPasswordPolicy(), 'Apply Policy', 'Applying...', 'Applied'],
      ['S3 Block Public Access', 'Prevents any S3 bucket from being made publicly accessible, account-wide.', s3Block,   setS3Block,   () => window.electronAPI.blockS3PublicAccess(),   'Block Access',  'Blocking...', 'Blocked'],
      ['GuardDuty',             'Monitors for suspicious API calls, unusual logins, and crypto mining.',      guardDuty, setGuardDuty, () => window.electronAPI.enableGuardDuty(),       'Enable',        'Enabling...', 'Enabled'],
      ['IAM Access Analyzer',   'Flags IAM policies and resources accessible from outside your account.',    accessAn,  setAccessAn,  () => window.electronAPI.enableAccessAnalyzer(),  'Enable',        'Enabling...', 'Enabled'],
    ] as const
  ).map(([title, desc, state, setter, fn, label, busyLabel, doneLabel]) => {
    const costNode = title === 'GuardDuty'
      ? <p className="text-amber-600 text-xs mt-1">Paid after 30-day trial · {pricingLink('https://aws.amazon.com/guardduty/pricing/')}</p>
      : <p className="text-zinc-600 text-xs mt-1">Free</p>
    return (
      <div key={title} className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
        <div className="flex-1">
          <p className="text-zinc-200 text-xs font-semibold leading-snug">{title}</p>
          <p className="text-zinc-500 text-xs leading-snug mt-1">{desc}</p>
          {costNode}
          {state.error && <p className="text-red-400 text-xs mt-1">{state.error}</p>}
          {state.done  && <p className="text-green-400 text-xs mt-1">Done.</p>}
        </div>
        <button onClick={() => runSecurity(fn, setter as (s: S) => void)} {...iamGated(state.busy || state.done)}>
          {state.busy ? busyLabel : state.done ? doneLabel : label}
        </button>
      </div>
    )
  })

  const smsCard = (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
      <div>
        <p className="text-zinc-200 text-xs font-semibold leading-snug">GuardDuty SMS Alert</p>
        <p className="text-zinc-500 text-xs leading-snug mt-1">Text alert on HIGH-severity findings. Requires GuardDuty enabled. Use E.164 format, e.g. +353871234567.</p>
        <p className="text-amber-600 text-xs mt-1">Paid after 30-day trial · {pricingLink('https://aws.amazon.com/sns/pricing/', 'SNS pricing ↗')} · {pricingLink('https://aws.amazon.com/guardduty/pricing/', 'GuardDuty pricing ↗')}</p>
      </div>
      <div className="flex flex-col gap-1.5 flex-1">
        <label className="text-zinc-400 text-xs">Phone number</label>
        <input type="tel" value={smsPhone} onChange={e => setSmsPhone(e.target.value)} placeholder="+353871234567" className={ic(smsPhone)} />
        {!guardDuty.done && <p className="text-amber-400 text-xs">Enable GuardDuty first.</p>}
        {smsError && <p className="text-red-400 text-xs">{smsError}</p>}
        {smsDone  && <p className="text-green-400 text-xs">Done — you'll receive a text on HIGH findings.</p>}
      </div>
      <button onClick={handleEnableSmsAlert} {...iamGated(!isValidPhone(smsPhone) || smsBusy || smsDone || !guardDuty.done)}>
        {smsBusy ? 'Enabling...' : smsDone ? 'Enabled' : 'Enable SMS Alert'}
      </button>
    </div>
  )

  // ── Step indicator ────────────────────────────────────────────────────────

  const stepIndicator = (
    <div className="flex items-center gap-1 text-xs">
      {WIZARD_STEPS.map((step, i) => (
        <Fragment key={step.id}>
          {i > 0 && <span className="text-zinc-700 mx-0.5">›</span>}
          <button
            onClick={() => { if (step.id < wizardStep) setWizardStep(step.id) }}
            className={`flex items-center gap-1.5 px-1.5 py-0.5 rounded transition-colors ${
              step.id < wizardStep  ? 'text-green-400 hover:text-green-300 cursor-pointer' :
              step.id === wizardStep ? 'text-zinc-100 font-medium cursor-default' :
              'text-zinc-600 cursor-default'
            }`}
          >
            <span className={`text-[10px] font-bold w-3 text-center ${
              step.id < wizardStep  ? 'text-green-400' :
              step.id === wizardStep ? 'text-blue-400' : 'text-zinc-600'
            }`}>
              {step.id < wizardStep ? '✓' : step.id}
            </span>
            {step.title}
          </button>
        </Fragment>
      ))}
    </div>
  )

  // ── Wizard navigation button ──────────────────────────────────────────────

  const navBtn = (label: string, onClick: () => void, disabled = false) => (
    <button onClick={onClick} disabled={disabled}
      className="px-4 py-1.5 text-xs bg-blue-700 hover:bg-blue-600 text-white font-medium rounded transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
      {label}
    </button>
  )

  const backBtn = (
    <button onClick={() => setWizardStep(s => s - 1)}
      className="px-4 py-1.5 text-xs text-zinc-400 hover:text-zinc-200 transition-colors">
      ← Back
    </button>
  )

  // ── Render ────────────────────────────────────────────────────────────────

  if (pageMode === 'loading') {
    return (
      <div className="flex items-center gap-2 text-zinc-500 text-xs">
        <span className="w-3 h-3 rounded-full border-2 border-zinc-600 border-t-zinc-300 animate-spin" />
        Checking account status…
      </div>
    )
  }

  if (pageMode === 'login') {
    return <LoginPage onNext={() => setHasCredentials(true)} />
  }

  if (pageMode === 'wizard') {
    return (
      <div className="flex flex-col gap-6">

        {/* Step indicator */}
        <div className="flex items-center justify-between">
          {stepIndicator}
          <span className="text-zinc-600 text-xs">Step {wizardStep} of {WIZARD_STEPS.length}</span>
        </div>

        {/* ── Step 1: Root MFA ── */}
        {wizardStep === 1 && (
          <div className="flex flex-col gap-4">
            <div>
              <h2 className="text-sm font-semibold text-zinc-100">Secure your root account</h2>
              <p className="text-zinc-500 text-xs mt-0.5">Set up MFA on the root account before creating any IAM users. You cannot skip this step.</p>
            </div>
            <div className="max-w-sm">{mfaCard}</div>
            <div className="flex justify-end">
              {navBtn('Next Step →', () => setWizardStep(2), !mfaDone)}
            </div>
          </div>
        )}

        {/* ── Step 2: Create IAM User ── */}
        {wizardStep === 2 && (
          <div className="flex flex-col gap-4">
            <div>
              <h2 className="text-sm font-semibold text-zinc-100">Create an IAM user</h2>
              <p className="text-zinc-500 text-xs mt-0.5">Create a dedicated IAM user for day-to-day work. The app switches to IAM credentials automatically.</p>
            </div>
            <div className="max-w-sm">{iamCard}</div>
            <div className="flex items-center justify-between">
              {backBtn}
              {navBtn('Next Step →', () => setWizardStep(3), !iamSaved && isRootCaller)}
            </div>
          </div>
        )}

        {/* ── Step 3: Alerts ── */}
        {wizardStep === 3 && (
          <div className="flex flex-col gap-4">
            <div>
              <h2 className="text-sm font-semibold text-zinc-100">Configure alerts</h2>
              <p className="text-zinc-500 text-xs mt-0.5">Optional. Set up cost and security notifications. You can skip and configure these later.</p>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {billingCard}
              {anomalyCard}
              {alarmCard}
            </div>
            <div className="flex items-center justify-between">
              {backBtn}
              {navBtn('Next Step →', () => setWizardStep(4))}
            </div>
          </div>
        )}

        {/* ── Step 4: Security Hardening ── */}
        {wizardStep === 4 && (
          <div className="flex flex-col gap-4">
            <div>
              <h2 className="text-sm font-semibold text-zinc-100">Security hardening</h2>
              <p className="text-zinc-500 text-xs mt-0.5">Optional. One-click hardening steps. You can skip and apply these later.</p>
            </div>
            <div className="grid grid-cols-5 gap-3">
              {securityToggleCards}
              {smsCard}
            </div>
            <div className="flex items-center justify-between">
              {backBtn}
              {navBtn('Complete Setup', () => setPageMode('summary'))}
            </div>
          </div>
        )}

      </div>
    )
  }

  // ── Summary (end of first-time wizard) ───────────────────────────────────

  if (pageMode === 'summary') {
    type Row = { label: string; detail?: string; done: boolean }
    const rows: Row[] = [
      { label: 'Root MFA',              detail: 'Virtual MFA device activated',            done: mfaDone },
      { label: 'IAM User',              detail: iamUsername || undefined,                   done: iamSaved },
      { label: 'Root access keys',      detail: iamRootKeysDeleted ? 'Deleted' : 'Kept',   done: iamRootKeysDeleted },
      { label: 'Billing alert',         detail: budgetDone ? `$${budgetAmount}/mo → ${budgetEmail}` : undefined, done: budgetDone },
      { label: 'Cost anomaly detection',detail: anomalyDone ? `$${anomalyThreshold} threshold → ${anomalyEmail}` : undefined, done: anomalyDone },
      { label: 'Root login alarm',      detail: alarmDone ? alarmEmail : undefined,         done: alarmDone },
      { label: 'IAM password policy',   detail: pwPolicy.done  ? 'Applied' : undefined,    done: pwPolicy.done },
      { label: 'S3 block public access',detail: s3Block.done   ? 'Applied' : undefined,    done: s3Block.done },
      { label: 'GuardDuty',            detail: guardDuty.done  ? 'Enabled' : undefined,    done: guardDuty.done },
      { label: 'IAM Access Analyzer',  detail: accessAn.done   ? 'Enabled' : undefined,    done: accessAn.done },
      { label: 'GuardDuty SMS alert',  detail: smsDone ? smsPhone : undefined,             done: smsDone },
    ]

    const groups = [
      { title: 'Account',   rows: rows.slice(0, 3) },
      { title: 'Alerts',    rows: rows.slice(3, 6) },
      { title: 'Security',  rows: rows.slice(6)    },
    ]

    return (
      <div className="flex flex-col gap-6 max-w-lg">

        <div>
          <p className="text-green-400 text-xs font-semibold uppercase tracking-wide">Setup complete</p>
          <h2 className="text-sm font-semibold text-zinc-100 mt-0.5">Your account is configured</h2>
          <p className="text-zinc-500 text-xs mt-1">
            Here's a summary of what was applied. Skipped items can be configured any time from the dashboard.
          </p>
        </div>

        <div className="flex flex-col gap-4">
          {groups.map(group => (
            <div key={group.title} className="bg-zinc-800 border border-zinc-700 rounded-lg overflow-hidden">
              <div className="px-4 py-2 border-b border-zinc-700">
                <p className="text-zinc-400 text-xs font-semibold">{group.title}</p>
              </div>
              <div className="divide-y divide-zinc-700/50">
                {group.rows.map(row => (
                  <div key={row.label} className="flex items-center gap-3 px-4 py-2.5">
                    <span className={`shrink-0 text-xs font-bold w-3 text-center ${row.done ? 'text-green-400' : 'text-zinc-600'}`}>
                      {row.done ? '✓' : '—'}
                    </span>
                    <span className={`text-xs flex-1 ${row.done ? 'text-zinc-200' : 'text-zinc-500'}`}>{row.label}</span>
                    {row.detail && <span className="text-xs text-zinc-500 font-mono truncate max-w-[180px]">{row.detail}</span>}
                    {!row.done && <span className="text-xs text-zinc-600">Skipped</span>}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end">
          <button onClick={() => setPageMode('detail')}
            className="px-5 py-2 text-xs bg-blue-700 hover:bg-blue-600 text-white font-medium rounded transition-colors">
            Open Dashboard →
          </button>
        </div>

      </div>
    )
  }

  // ── Detail page (returning users / post-wizard) ───────────────────────────

  type DetailRow = { label: string; value: string; ok: boolean | null }

  const detailSection = (title: string, rows: DetailRow[]) => (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg overflow-hidden">
      <div className="px-4 py-2.5 border-b border-zinc-700">
        <p className="text-zinc-300 text-xs font-semibold">{title}</p>
      </div>
      <div className="divide-y divide-zinc-700/50">
        {rows.map(row => (
          <div key={row.label} className="flex items-center gap-3 px-4 py-2.5">
            <span className={`shrink-0 text-xs font-bold w-3 text-center ${
              row.ok === true  ? 'text-green-400' :
              row.ok === false ? 'text-red-400'   : 'text-zinc-600'
            }`}>
              {row.ok === true ? '✓' : row.ok === false ? '✗' : '—'}
            </span>
            <span className={`text-xs flex-1 ${row.ok === null ? 'text-zinc-500' : 'text-zinc-200'}`}>
              {row.label}
            </span>
            <span className={`text-xs font-mono ${
              row.ok === true  ? 'text-zinc-400' :
              row.ok === false ? 'text-red-400'  : 'text-zinc-600'
            }`}>
              {row.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )

  return (
    <div className="flex flex-col gap-5 max-w-lg">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-sm font-semibold text-zinc-100">Account</h2>
          <div className="flex items-center gap-3 mt-1.5">
            {accountId && (
              <span className="flex items-center gap-1.5 text-xs">
                <span className="text-zinc-500">ID</span>
                <span className="text-zinc-300 font-mono">{accountId}</span>
              </span>
            )}
            {region && (
              <span className="flex items-center gap-1.5 text-xs">
                <span className="text-zinc-500">Region</span>
                <span className="text-zinc-300 font-mono">{region}</span>
              </span>
            )}
            <span className="flex items-center gap-1.5 text-xs">
              <span className="text-zinc-500">Caller</span>
              <span className="text-zinc-300 font-mono">{isRootCaller ? 'root' : 'IAM'}</span>
            </span>
          </div>
        </div>
        <button onClick={() => { setWizardStep(isRootCaller ? 1 : 3); setPageMode('wizard') }}
          className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors shrink-0">
          {isRootCaller ? 'Re-run setup →' : 'Configure alerts & security →'}
        </button>
      </div>

      {detailSection('Account', [
        { label: 'Root MFA',         value: mfaEnabled || mfaDone ? 'Enabled' : 'Disabled',       ok: mfaEnabled || mfaDone },
        { label: 'Root access keys', value: keysPresent ? 'Present' : iamRootKeysDeleted ? 'Deleted' : 'Not detected', ok: !keysPresent },
        { label: 'IAM user',         value: iamSaved ? iamUsername : 'Not created this session',   ok: iamSaved || null },
      ])}

      {detailSection('Alerts', [
        { label: 'Billing alert',          value: budgetDone  ? `$${budgetAmount}/mo → ${budgetEmail}`        : 'Skipped', ok: budgetDone  || null },
        { label: 'Cost anomaly detection', value: anomalyDone ? `$${anomalyThreshold} threshold → ${anomalyEmail}` : 'Skipped', ok: anomalyDone || null },
        { label: 'Root login alarm',       value: alarmDone   ? alarmEmail                                    : 'Skipped', ok: alarmDone   || null },
      ])}

      {detailSection('Security hardening', [
        { label: 'IAM password policy',    value: pwPolicy.done  ? 'Applied' : 'Skipped', ok: pwPolicy.done  || null },
        { label: 'S3 block public access', value: s3Block.done   ? 'Applied' : 'Skipped', ok: s3Block.done   || null },
        { label: 'GuardDuty',             value: guardDuty.done  ? 'Enabled' : 'Skipped', ok: guardDuty.done || null },
        { label: 'IAM Access Analyzer',   value: accessAn.done   ? 'Enabled' : 'Skipped', ok: accessAn.done  || null },
        { label: 'GuardDuty SMS alert',   value: smsDone ? smsPhone                       : 'Skipped', ok: smsDone        || null },
      ])}

    </div>
  )
}
