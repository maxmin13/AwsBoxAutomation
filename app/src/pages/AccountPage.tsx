import { Fragment, useEffect, useState } from 'react'
import { useAuth } from '../AuthContext'
import LoginPage from './LoginPage'
import PricingLink from '../components/PricingLink'

const WIZARD_STEPS = [
  { id: 1, title: 'Root MFA'  },
  { id: 2, title: 'IAM User'  },
  { id: 3, title: 'IAM MFA'   },
  { id: 4, title: 'Alerts'    },
  { id: 5, title: 'Security'  },
]

export default function AccountPage() {
  const { hasCredentials, setHasCredentials, requireCreds, withAuth, withSession } = useAuth()

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
  // AWS's IAM API has no way to activate a virtual MFA device for the root
  // user itself (EnableMFADevice requires a real IAM UserName — confirmed
  // against the SDK's own model and live testing; AssumeRoot's task-policy
  // list doesn't cover MFA either). Device creation works via API, but
  // activation only exists in the Console — so mfaStep 1 shows the QR code
  // plus instructions to finish there, and "Check Status" re-polls AWS
  // (ListMFADevices, via check-root-credentials) rather than activating.
  const [mfaEnabled, setMfaEnabled] = useState(false)
  const [mfaStep,    setMfaStep]    = useState(0) // 0=idle, 1=QR shown, awaiting console activation
  const [mfaSerial,  setMfaSerial]  = useState('')
  const [mfaQrCode,  setMfaQrCode]  = useState('')
  const [mfaSecret,  setMfaSecret]  = useState('')
  const [mfaBusy,    setMfaBusy]    = useState(false)
  const [mfaError,   setMfaError]   = useState<string | null>(null)
  const [mfaDone,    setMfaDone]    = useState(false)

  // ── Create IAM user ───────────────────────────────────────────────────────
  const IAM_POLICY_ARN = 'arn:aws:iam::aws:policy/AdministratorAccess'

  const [iamUsername,        setIamUsername]        = useState('')
  const [iamBusy,            setIamBusy]            = useState(false)
  const [iamError,           setIamError]           = useState<string | null>(null)
  const [iamResult,          setIamResult]          = useState<{ accessKeyId: string; secretAccessKey: string } | null>(null)
  const [iamKeyCopied,       setIamKeyCopied]       = useState(false)
  const [iamSecretCopied,    setIamSecretCopied]    = useState(false)
  const [iamSaved,           setIamSaved]           = useState(false)
  const [iamRootKeysDeleted, setIamRootKeysDeleted] = useState(false)
  const [iamResumed,         setIamResumed]         = useState(false)

  // ── Access key rotation ────────────────────────────────────────────────────
  const [rotateBusy,         setRotateBusy]         = useState(false)
  const [rotateError,        setRotateError]        = useState<string | null>(null)
  const [rotateResult,       setRotateResult]       = useState<{ accessKeyId: string; secretAccessKey: string } | null>(null)
  const [rotateKeyCopied,    setRotateKeyCopied]    = useState(false)
  const [rotateSecretCopied, setRotateSecretCopied] = useState(false)

  // ── IAM user MFA + first session ──────────────────────────────────────────
  const [iamMfaStep,   setIamMfaStep]   = useState(0) // 0=idle,1=QR,2=codes,3=mint first session
  const [iamMfaSerial, setIamMfaSerial] = useState('')
  const [iamMfaQrCode, setIamMfaQrCode] = useState('')
  const [iamMfaSecret, setIamMfaSecret] = useState('')
  const [iamMfaCode1,  setIamMfaCode1]  = useState('')
  const [iamMfaCode2,  setIamMfaCode2]  = useState('')
  const [iamMfaBusy,   setIamMfaBusy]   = useState(false)
  const [iamMfaError,  setIamMfaError]  = useState<string | null>(null)
  const [iamMfaDone,   setIamMfaDone]   = useState(false)
  const [sessionCode,     setSessionCode]     = useState('')
  const [sessionDuration, setSessionDuration] = useState(14400) // seconds; matches mfa-enforcement-policy.js's 4-hour cap
  const [sessionBusy,     setSessionBusy]     = useState(false)
  const [sessionError,    setSessionError]    = useState<string | null>(null)
  const [sessionMinted,   setSessionMinted]   = useState(false)

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
  // Clicking "My Account" always lands on the detail/landing page, regardless
  // of how far setup has progressed — the wizard is only entered explicitly,
  // via the "Continue setup →" button below.
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
          setIamMfaDone(res.iamMfaEnabled ?? false)
          if (res.iamUsername) { setIamUsername(res.iamUsername); setIamSaved(true) }
          if (res.iamMfaEnabled) {
            window.electronAPI.getSessionStatus().then(s => { if (s.ok && s.active) setSessionMinted(true) })
          }
        }
      }
      setPageMode('detail')
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

  function handleMfaCheckStatus() {
    requireCreds(() => withAuth(async () => {
      setMfaBusy(true); setMfaError(null)
      const res = await window.electronAPI.checkRootCredentials()
      setMfaBusy(false)
      if (res.ok && res.mfaEnabled) {
        setMfaDone(true); setMfaEnabled(true); setMfaStep(0)
      } else if (res.ok) {
        setMfaError('MFA not detected yet. Finish activating the device in the AWS Console, then check again.')
      } else {
        setMfaError(res.error ?? 'Unknown error')
      }
    }))
  }

  function handleCreateIamUser() {
    if (!iamUsername.trim()) return
    withAuth(async () => {
      setIamBusy(true); setIamError(null); setIamResult(null); setIamSaved(false); setIamRootKeysDeleted(false); setIamResumed(false)
      const res = await window.electronAPI.createIamUser(iamUsername.trim(), IAM_POLICY_ARN, true)
      if (res.ok && res.accessKeyId && res.secretAccessKey) {
        const { region } = await window.electronAPI.loadCredentials()
        await window.electronAPI.saveCredentials(res.accessKeyId, res.secretAccessKey, region || 'eu-west-1')
        setIamSaved(true); setHasCredentials(true); setIsRootCaller(false)
        setIamResult({ accessKeyId: res.accessKeyId, secretAccessKey: res.secretAccessKey })
        if (res.rootKeysDeleted) { setIamRootKeysDeleted(true); setKeysPresent(false) }
        if (res.resumed) setIamResumed(true)
      } else {
        setIamError(res.error ?? 'Unknown error')
      }
      setIamBusy(false)
    })
  }

  // iam:CreateAccessKey/DeleteAccessKey require an active MFA session (see
  // mfa-enforcement-policy.js), same gating as the security hardening cards.
  // The main process persists the new key to disk itself once it's verified,
  // so there's no separate saveCredentials call here.
  function handleRotateAccessKey() {
    requireCreds(() => withSession(async () => {
      setRotateBusy(true); setRotateError(null); setRotateResult(null)
      const res = await window.electronAPI.rotateAccessKey()
      if (res.ok && res.accessKeyId && res.secretAccessKey) {
        setRotateResult({ accessKeyId: res.accessKeyId, secretAccessKey: res.secretAccessKey })
      } else {
        setRotateError(res.error ?? 'Unknown error')
      }
      setRotateBusy(false)
    }))
  }

  function handleIamMfaStart() {
    withAuth(async () => {
      setIamMfaBusy(true); setIamMfaError(null)
      const res = await window.electronAPI.createVirtualMfaDevice(iamUsername)
      setIamMfaBusy(false)
      if (res.ok && res.serialNumber && res.qrCodePng) {
        setIamMfaSerial(res.serialNumber); setIamMfaQrCode(res.qrCodePng); setIamMfaSecret(res.base32Seed ?? '')
        setIamMfaStep(1)
      } else {
        setIamMfaError(res.error ?? 'Unknown error')
      }
    })
  }

  function handleIamMfaActivate() {
    if (iamMfaCode1.length < 6 || iamMfaCode2.length < 6) return
    withAuth(async () => {
      setIamMfaBusy(true); setIamMfaError(null)
      const res = await window.electronAPI.enableMfaDevice(iamMfaSerial, iamMfaCode1.trim(), iamMfaCode2.trim(), iamUsername)
      setIamMfaBusy(false)
      if (res.ok) {
        setIamMfaDone(true); setIamMfaStep(3)
      } else {
        setIamMfaError(res.error ?? 'Unknown error')
      }
    })
  }

  function handleMintFirstSession() {
    if (sessionCode.length < 6) return
    withAuth(async () => {
      setSessionBusy(true); setSessionError(null)
      const res = await window.electronAPI.getSessionToken(sessionCode.trim(), sessionDuration)
      setSessionBusy(false)
      if (res.ok) {
        setSessionMinted(true); setIamMfaStep(0)
      } else {
        setSessionError(res.error ?? 'Unknown error')
      }
    })
  }

  function handleCreateBillingAlert() {
    const amount = parseFloat(budgetAmount)
    if (!amount || !budgetEmail.trim()) return
    requireCreds(() => withSession(async () => {
      setBudgetBusy(true); setBudgetError(null); setBudgetDone(false)
      const res = await window.electronAPI.createBillingAlert(amount, budgetEmail.trim(), budgetPhone.trim() || undefined)
      setBudgetBusy(false)
      res.ok ? setBudgetDone(true) : setBudgetError(res.error ?? 'Unknown error')
    }))
  }

  function handleCreateAnomalyDetection() {
    const threshold = parseFloat(anomalyThreshold)
    if (!threshold || !anomalyEmail.trim()) return
    requireCreds(() => withSession(async () => {
      setAnomalyBusy(true); setAnomalyError(null); setAnomalyDone(false)
      const res = await window.electronAPI.createAnomalyDetection(threshold, anomalyEmail.trim(), anomalyPhone.trim() || undefined)
      setAnomalyBusy(false)
      res.ok ? setAnomalyDone(true) : setAnomalyError(res.error ?? 'Unknown error')
    }))
  }

  function handleCreateRootAlarm() {
    if (!alarmEmail.trim()) return
    requireCreds(() => withSession(async () => {
      setAlarmBusy(true); setAlarmError(null); setAlarmDone(false)
      const res = await window.electronAPI.createRootLoginAlarm(alarmEmail.trim(), alarmPhone.trim() || undefined)
      setAlarmBusy(false)
      res.ok ? setAlarmDone(true) : setAlarmError(res.error ?? 'Unknown error')
    }))
  }

  function handleEnableSmsAlert() {
    if (!smsPhone.trim()) return
    if (!guardDuty.done) { setSmsError('Enable GuardDuty first — SMS alerts require an active GuardDuty detector.'); return }
    requireCreds(() => withSession(async () => {
      setSmsBusy(true); setSmsError(null); setSmsDone(false)
      const res = await window.electronAPI.enableSmsSecurityAlert(smsPhone.trim())
      setSmsBusy(false)
      res.ok ? setSmsDone(true) : setSmsError(res.error ?? 'Unknown error')
    }))
  }

  function handleDisableSmsAlert() {
    requireCreds(() => withSession(async () => {
      setSmsBusy(true); setSmsError(null)
      const res = await window.electronAPI.disableSmsSecurityAlert()
      setSmsBusy(false)
      res.ok ? setSmsDone(false) : setSmsError(res.error ?? 'Unknown error')
    }))
  }

  function runSecurity(fn: () => Promise<{ ok: boolean; error?: string }>, set: (s: S) => void) {
    requireCreds(() => withSession(async () => {
      set({ busy: true, done: false, error: null })
      const res = await fn()
      set(res.ok ? { busy: false, done: true, error: null } : { busy: false, done: false, error: res.error ?? 'Unknown error' })
    }))
  }

  function runSecurityDisable(fn: () => Promise<{ ok: boolean; error?: string }>, set: (s: S) => void) {
    requireCreds(() => withSession(async () => {
      set({ busy: true, done: true, error: null })
      const res = await fn()
      set(res.ok ? { busy: false, done: false, error: null } : { busy: false, done: true, error: res.error ?? 'Unknown error' })
    }))
  }

  function copy(text: string, setCopied: (v: boolean) => void) {
    navigator.clipboard.writeText(text); setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  const formatDuration = (seconds: number) =>
    seconds < 3600 ? `${seconds / 60}-minute` : `${seconds / 3600}-hour`

  const isValidEmail  = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim())
  const isValidPhone  = (v: string) => /^\+\d{7,15}$/.test(v.trim())
  const pricingLink   = (url: string, label = 'AWS pricing ↗') => <PricingLink url={url} label={label} />

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
          <p className="text-amber-600 text-xs mt-0.5">Free · {pricingLink('https://aws.amazon.com/iam/pricing/')}</p>
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
            <p className="text-zinc-400 text-xs">Scan this QR code in your authenticator app.</p>
            <div className="flex justify-center bg-white rounded p-1.5">
              <img src={`data:image/png;base64,${mfaQrCode}`} alt="MFA QR code" className="w-28 h-28" />
            </div>
            {mfaSecret && (
              <details className="text-xs">
                <summary className="text-zinc-500 cursor-pointer select-none">Manual entry code</summary>
                <code className="block text-zinc-300 break-all mt-1 leading-relaxed">{mfaSecret}</code>
              </details>
            )}
            <p className="text-zinc-400 text-xs mt-1">
              AWS doesn't allow activating root's MFA device via API — finish it in the AWS Console: <span className="text-zinc-300">Security credentials</span> → <span className="text-zinc-300">Multi-factor authentication (MFA)</span>, find this device, and enter two codes there. Then check status below.
            </p>
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
      {mfaStep === 1 && (
        <div className="flex flex-col gap-1.5">
          <button
            onClick={() => window.electronAPI.openExternal('https://console.aws.amazon.com/iam/home#/security_credentials')}
            className={primaryBtn}
          >
            Open AWS Console ↗
          </button>
          <button
            onClick={handleMfaCheckStatus}
            disabled={mfaBusy}
            className="w-full px-3 py-1.5 text-xs border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mfaBusy ? 'Checking...' : 'Check Status'}
          </button>
        </div>
      )}
    </div>
  )

  const iamMfaCard = (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-zinc-200 text-xs font-semibold">IAM User MFA</p>
          <p className="text-zinc-500 text-xs mt-0.5">Virtual MFA device for {iamUsername || 'the IAM user'}. From now on, the permanent key alone won't be enough for privileged actions.</p>
          <p className="text-amber-600 text-xs mt-0.5">Free · {pricingLink('https://aws.amazon.com/iam/pricing/')}</p>
        </div>
        <span className={`shrink-0 flex items-center gap-1 text-xs px-1.5 py-0.5 rounded ${iamMfaDone ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${iamMfaDone ? 'bg-green-400' : 'bg-red-400'}`} />
          {iamMfaDone ? 'Enabled' : 'Disabled'}
        </span>
      </div>
      <div className="flex-1 flex flex-col gap-2">
        {iamMfaError && <p className="text-red-400 text-xs">{iamMfaError}</p>}
        {iamMfaStep === 0 && !iamMfaDone && (
          <p className="text-zinc-500 text-xs">Click below to generate a QR code, then scan it with your authenticator app.</p>
        )}
        {iamMfaStep === 1 && (
          <>
            <p className="text-zinc-400 text-xs">Scan this QR code in your authenticator app, then click Next.</p>
            <div className="flex justify-center bg-white rounded p-1.5">
              <img src={`data:image/png;base64,${iamMfaQrCode}`} alt="MFA QR code" className="w-28 h-28" />
            </div>
            {iamMfaSecret && (
              <details className="text-xs">
                <summary className="text-zinc-500 cursor-pointer select-none">Manual entry code</summary>
                <code className="block text-zinc-300 break-all mt-1 leading-relaxed">{iamMfaSecret}</code>
              </details>
            )}
          </>
        )}
        {iamMfaStep === 2 && (
          <>
            <p className="text-zinc-400 text-xs">Enter two consecutive 6-digit codes from your authenticator app.</p>
            <input type="text" inputMode="numeric" maxLength={6} value={iamMfaCode1}
              onChange={e => setIamMfaCode1(e.target.value.replace(/\D/g, ''))}
              placeholder="Code 1" className={ic(iamMfaCode1)} />
            <input type="text" inputMode="numeric" maxLength={6} value={iamMfaCode2}
              onChange={e => setIamMfaCode2(e.target.value.replace(/\D/g, ''))}
              placeholder="Code 2 (next 30s window)" className={ic(iamMfaCode2)} />
          </>
        )}
        {iamMfaStep === 3 && (
          <>
            <p className="text-zinc-400 text-xs">MFA activated. Enter a fresh code to start your first session.</p>
            <label className="text-zinc-400 text-xs">Session length</label>
            <select value={sessionDuration} onChange={e => setSessionDuration(Number(e.target.value))}
              className={ic(String(sessionDuration))}>
              <option value={3600}>1 hour</option>
              <option value={7200}>2 hours</option>
              <option value={10800}>3 hours</option>
              <option value={14400}>4 hours (default)</option>
            </select>
            <input type="text" inputMode="numeric" maxLength={6} value={sessionCode}
              onChange={e => setSessionCode(e.target.value.replace(/\D/g, ''))}
              placeholder="Code" className={ic(sessionCode)} />
            {sessionError && <p className="text-red-400 text-xs">{sessionError}</p>}
          </>
        )}
        {iamMfaDone && iamMfaStep === 0 && !sessionMinted && (
          <p className="text-zinc-500 text-xs">MFA is already enabled — start a fresh session to continue.</p>
        )}
        {iamMfaDone && iamMfaStep === 0 && sessionMinted && (
          <>
            <p className="text-green-400 text-xs">MFA activated — session started.</p>
            <p className="text-zinc-600 text-xs">
              Closing the app only clears this session locally — AWS has no way to revoke it early, so it stays valid for its full {formatDuration(sessionDuration)} window either way. You'll just be asked for a fresh code next time you open the app.
              If you ever need to cut it off early, deactivate or delete the IAM user's access key: {pricingLink(`https://console.aws.amazon.com/iam/home#/users/details/${encodeURIComponent(iamUsername)}?section=security_credentials`, 'IAM security credentials ↗')}
            </p>
          </>
        )}
      </div>
      {!iamMfaDone && iamMfaStep === 0 && (
        <button onClick={handleIamMfaStart} disabled={iamMfaBusy || !iamUsername.trim()} className={primaryBtn}>
          {iamMfaBusy ? 'Generating QR...' : 'Set Up IAM User MFA'}
        </button>
      )}
      {iamMfaDone && iamMfaStep === 0 && !sessionMinted && (
        <button onClick={() => setIamMfaStep(3)} className={primaryBtn}>Start Session →</button>
      )}
      {iamMfaStep === 1 && <button onClick={() => setIamMfaStep(2)} className={primaryBtn}>Next: Enter Codes →</button>}
      {iamMfaStep === 2 && (
        <div className="flex flex-col gap-1.5">
          <button onClick={handleIamMfaActivate} disabled={iamMfaBusy || iamMfaCode1.length < 6 || iamMfaCode2.length < 6} className={primaryBtn}>
            {iamMfaBusy ? 'Activating...' : 'Activate MFA'}
          </button>
          <button onClick={() => setIamMfaStep(1)} disabled={iamMfaBusy} className="text-xs text-zinc-500 hover:text-zinc-300 text-center py-0.5">← Back</button>
        </div>
      )}
      {iamMfaStep === 3 && (
        <button onClick={handleMintFirstSession} disabled={sessionBusy || sessionCode.length < 6} className={primaryBtn}>
          {sessionBusy ? 'Starting...' : 'Start Session'}
        </button>
      )}
    </div>
  )

  const iamCard = (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
      <div>
        <p className="text-zinc-200 text-xs font-semibold">Create IAM User</p>
        <p className="text-zinc-500 text-xs mt-0.5">Creates an administrator IAM user and access key, then switches the app to use them for every action instead of root.</p>
        <p className="text-amber-600 text-xs mt-0.5">Free · {pricingLink('https://aws.amazon.com/iam/pricing/')}</p>
      </div>
      <div className="flex flex-col gap-1.5 flex-1">
        <label className="text-zinc-400 text-xs">Username</label>
        <input type="text" value={iamUsername} disabled={iamSaved}
          onChange={e => setIamUsername(e.target.value)}
          placeholder="e.g. admin" autoComplete="off" className={ic(iamUsername) + ' disabled:opacity-60 disabled:cursor-not-allowed'} />
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
            {iamResumed && <p className="text-amber-400 text-xs mt-0.5">This IAM user already existed — reused it and issued a new access key.</p>}
          </div>
        )}
      </div>
      <div className="flex flex-col gap-1">
        <p className="text-zinc-400 text-xs">Root access keys will be deleted after creating this user.</p>
        <p className="text-zinc-600 text-xs">Only removes API access — you can still sign in to the AWS console as root with your email and password.</p>
      </div>
      {iamSaved ? (
        <p className="text-zinc-600 text-xs">IAM user created — click <span className="text-zinc-400">Next Step →</span> below to continue.</p>
      ) : (
        <button onClick={handleCreateIamUser} disabled={!iamUsername.trim() || iamBusy} className={primaryBtn}>
          {iamBusy ? 'Creating...' : 'Create IAM User'}
        </button>
      )}
    </div>
  )

  const billingCard = (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
      <div>
        <p className="text-zinc-200 text-xs font-semibold">Set Billing Alert</p>
        <p className="text-zinc-500 text-xs mt-0.5">Creates a monthly budget — email alert when 80% is reached.</p>
        <p className="text-amber-600 text-xs mt-0.5">Free (first 2 budgets/account) · {pricingLink('https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/')}</p>
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
        <p className="text-amber-600 text-xs mt-0.5">Free · {pricingLink('https://aws.amazon.com/aws-cost-management/aws-cost-anomaly-detection/pricing/')}</p>
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
        <p className="text-amber-600 text-xs mt-0.5">Free · {pricingLink('https://aws.amazon.com/sns/pricing/')}</p>
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

  const outlineBtn = 'w-full px-3 py-1.5 text-xs border border-red-800 hover:border-red-600 text-red-400 hover:text-red-300 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed'

  const securityToggleCards = (
    [
      ['IAM Password Policy',   'Enforces min 12 chars, uppercase, numbers, symbols, and 90-day rotation.',  pwPolicy,  setPwPolicy,  () => window.electronAPI.setIamPasswordPolicy(), 'Apply Policy', 'Applying...', 'Applied', undefined],
      ['S3 Block Public Access', 'Prevents any S3 bucket from being made publicly accessible, account-wide.', s3Block,   setS3Block,   () => window.electronAPI.blockS3PublicAccess(),   'Block Access',  'Blocking...', 'Blocked', undefined],
      ['GuardDuty',             'Monitors for suspicious API calls, unusual logins, and crypto mining.',      guardDuty, setGuardDuty, () => window.electronAPI.enableGuardDuty(),       'Enable',        'Enabling...', 'Enabled', () => window.electronAPI.disableGuardDuty()],
      ['IAM Access Analyzer',   'Flags IAM policies and resources accessible from outside your account.',    accessAn,  setAccessAn,  () => window.electronAPI.enableAccessAnalyzer(),  'Enable',        'Enabling...', 'Enabled', undefined],
    ] as const
  ).map(([title, desc, state, setter, fn, label, busyLabel, doneLabel, disableFn]) => {
    const freePricingUrl = title === 'S3 Block Public Access'
      ? 'https://aws.amazon.com/s3/pricing/'
      : 'https://aws.amazon.com/iam/pricing/'
    const costNode = title === 'GuardDuty'
      ? <p className="text-amber-600 text-xs mt-1">Paid after 30-day trial · {pricingLink('https://aws.amazon.com/guardduty/pricing/')}</p>
      : <p className="text-amber-600 text-xs mt-1">Free · {pricingLink(freePricingUrl)}</p>
    return (
      <div key={title} className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
        <div className="flex-1">
          <p className="text-zinc-200 text-xs font-semibold leading-snug">{title}</p>
          <p className="text-zinc-500 text-xs leading-snug mt-1">{desc}</p>
          {costNode}
          {state.error && <p className="text-red-400 text-xs mt-1">{state.error}</p>}
          {state.done  && <p className="text-green-400 text-xs mt-1">Done.</p>}
        </div>
        {state.done && disableFn ? (
          <button onClick={() => runSecurityDisable(disableFn, setter as (s: S) => void)} disabled={state.busy} className={outlineBtn}>
            {state.busy ? 'Disabling...' : 'Disable'}
          </button>
        ) : (
          <button onClick={() => runSecurity(fn, setter as (s: S) => void)} {...iamGated(state.busy || state.done)}>
            {state.busy ? busyLabel : state.done ? doneLabel : label}
          </button>
        )}
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
      {smsDone ? (
        <button onClick={handleDisableSmsAlert} disabled={smsBusy} className={outlineBtn}>
          {smsBusy ? 'Disabling...' : 'Disable SMS Alert'}
        </button>
      ) : (
        <button onClick={handleEnableSmsAlert} {...iamGated(!isValidPhone(smsPhone) || smsBusy || !guardDuty.done)}>
          {smsBusy ? 'Enabling...' : 'Enable SMS Alert'}
        </button>
      )}
    </div>
  )

  // ── Step indicator ────────────────────────────────────────────────────────
  // Mirrors FedoraBoxAutomation's CreateVmPage StepIndicator (numbered circles
  // joined by a connecting bar), adapted to keep click-to-jump-back on done steps.

  const stepIndicator = (
    <div className="flex items-center mb-4">
      {WIZARD_STEPS.map((step, i) => {
        const isActive = step.id === wizardStep
        const isDone   = step.id < wizardStep
        return (
          <Fragment key={step.id}>
            <div className="flex flex-col items-center">
              <button
                onClick={() => { if (isDone) setWizardStep(step.id) }}
                disabled={!isDone}
                className={
                  'w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ' +
                  (isDone
                    ? 'bg-blue-600 text-white hover:bg-blue-500 cursor-pointer'
                    : isActive
                    ? 'bg-blue-600 text-white ring-2 ring-blue-400 ring-offset-2 ring-offset-zinc-900 cursor-default'
                    : 'bg-zinc-700 text-zinc-400 cursor-default')
                }
              >
                {isDone ? '✓' : step.id}
              </button>
              <span className={
                'text-xs mt-1.5 ' +
                (isActive ? 'text-zinc-200' : isDone ? 'text-zinc-400' : 'text-zinc-500')
              }>
                {step.title}
              </span>
            </div>
            {i < WIZARD_STEPS.length - 1 && (
              <div className={'flex-1 h-px mx-2 mb-4 ' + (step.id < wizardStep ? 'bg-blue-600' : 'bg-zinc-700')} />
            )}
          </Fragment>
        )
      })}
    </div>
  )

  // ── Wizard navigation button ──────────────────────────────────────────────
  // Matches FedoraBoxAutomation's StepNav sizing (px-6/py-2, text-sm) and the
  // bordered Back button treatment.

  const navBtn = (label: string, onClick: () => void, disabled = false) => (
    <button onClick={onClick} disabled={disabled}
      className="px-6 py-2 text-sm bg-blue-700 hover:bg-blue-600 text-white font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
      {label}
    </button>
  )

  const backBtn = (
    <button onClick={() => setWizardStep(s => s - 1)}
      className="px-3 py-1 text-sm border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors shrink-0">
      ← Back
    </button>
  )

  // Short per-step note shown inline above the step content — everything else
  // about the header (title, subtitle, Back placement) is fixed, mirroring
  // FedoraBoxAutomation's CreateVmPage where "Create VM" / its subtitle never
  // change across steps and "← Back" sits on its own line above the title.
  const stepNote: Record<number, React.ReactNode> = {
    2: 'Create a dedicated IAM user for day-to-day work. The app switches to IAM credentials automatically.',
    3: <>Set up MFA for {iamUsername || 'the IAM user'}. From now on, you'll enter a fresh code to start a timed session before doing anything privileged.</>,
    4: 'Optional. Set up cost and security notifications. You can skip and configure these later.',
    5: 'Optional. One-click hardening steps. You can skip and apply these later.',
  }

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
    // Steps 1-3 show a single narrow card and read better in a tighter,
    // centered column; steps 4-5 are card grids that need the extra width.
    const wizardMaxW = wizardStep <= 3 ? 'max-w-3xl' : 'max-w-4xl'
    return (
      <div className={`${wizardMaxW} mx-auto w-full flex flex-col gap-6`}>

        {/* Header — fixed title/subtitle, mirrors FedoraBoxAutomation's CreateVmPage
            where "Create VM" and its subtitle never change across steps.
            Back sits inline with the title, not on its own row above it. */}
        <div>
          <div className="flex items-center gap-3">
            {wizardStep > 1 && backBtn}
            <h1 className="text-2xl font-semibold text-zinc-100">Account Setup</h1>
          </div>
          <p className="text-zinc-400 text-sm mt-0.5">Secure your AWS account, create an IAM user, and configure alerts.</p>
        </div>

        {/* Step indicator */}
        {stepIndicator}

        {/* ── Step 1: Root MFA ── */}
        {wizardStep === 1 && (
          <div className="flex flex-col gap-4">
            <div className="w-full">{mfaCard}</div>
            <div className="w-full flex justify-end">
              {navBtn('Next Step →', () => setWizardStep(2), !mfaDone)}
            </div>
          </div>
        )}

        {/* ── Step 2: Create IAM User ── */}
        {wizardStep === 2 && (
          <div className="flex flex-col gap-4">
            <p className="text-zinc-500 text-xs">{stepNote[2]}</p>
            <div className="w-full">{iamCard}</div>
            <div className="w-full flex justify-end">
              {navBtn('Next Step →', () => setWizardStep(3), !iamSaved && isRootCaller)}
            </div>
          </div>
        )}

        {/* ── Step 3: IAM User MFA ── */}
        {wizardStep === 3 && (
          <div className="flex flex-col gap-4">
            <p className="text-zinc-500 text-xs">{stepNote[3]}</p>
            <div className="w-full">{iamMfaCard}</div>
            <div className="w-full flex justify-end">
              {navBtn('Next Step →', () => setWizardStep(4), !(iamMfaDone && sessionMinted))}
            </div>
          </div>
        )}

        {/* ── Step 4: Alerts ── */}
        {wizardStep === 4 && (
          <div className="flex flex-col gap-4">
            <p className="text-zinc-500 text-xs">{stepNote[4]}</p>
            <div className="grid grid-cols-3 gap-3">
              {billingCard}
              {anomalyCard}
              {alarmCard}
            </div>
            <div className="flex justify-end">
              {navBtn('Next Step →', () => setWizardStep(5))}
            </div>
          </div>
        )}

        {/* ── Step 5: Security Hardening ── */}
        {wizardStep === 5 && (
          <div className="flex flex-col gap-4">
            <p className="text-zinc-500 text-xs">{stepNote[5]}</p>
            <div className="grid grid-cols-5 gap-3">
              {securityToggleCards}
              {smsCard}
            </div>
            <div className="flex justify-end">
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
      { label: 'IAM MFA',               detail: iamMfaDone && sessionMinted ? 'MFA activated, session started' : undefined, done: iamMfaDone && sessionMinted },
      { label: 'Billing alert',         detail: budgetDone ? `$${budgetAmount}/mo → ${budgetEmail}` : undefined, done: budgetDone },
      { label: 'Cost anomaly detection',detail: anomalyDone ? `$${anomalyThreshold} threshold → ${anomalyEmail}` : undefined, done: anomalyDone },
      { label: 'Root login alarm',      detail: alarmDone ? alarmEmail : undefined,         done: alarmDone },
      { label: 'IAM password policy',   detail: pwPolicy.done  ? 'Applied' : undefined,    done: pwPolicy.done },
      { label: 'S3 block public access',detail: s3Block.done   ? 'Applied' : undefined,    done: s3Block.done },
      { label: 'GuardDuty',            detail: guardDuty.done  ? 'Enabled' : undefined,    done: guardDuty.done },
      { label: 'IAM Access Analyzer',  detail: accessAn.done   ? 'Enabled' : undefined,    done: accessAn.done },
      { label: 'GuardDuty SMS alert',  detail: smsDone ? smsPhone : undefined,             done: smsDone },
    ]

    const groupCard = (title: string, groupRows: Row[]) => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg overflow-hidden">
        <div className="px-4 py-3">
          <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">{title}</p>
          <div className="divide-y divide-zinc-700/50">
            {groupRows.map(row => (
              <div key={row.label} className="flex items-center gap-3 py-2">
                <span className={`shrink-0 text-xs font-bold w-3 text-center ${row.done ? 'text-green-400' : 'text-zinc-600'}`}>
                  {row.done ? '✓' : '—'}
                </span>
                <span className={`text-xs flex-1 ${row.done ? 'text-zinc-200' : 'text-zinc-500'}`}>{row.label}</span>
                {row.detail && <span className="text-xs text-zinc-500 font-mono truncate max-w-[220px]">{row.detail}</span>}
                {!row.done && <span className="text-xs text-zinc-600">Skipped</span>}
              </div>
            ))}
          </div>
        </div>
      </div>
    )

    return (
      <div className="flex flex-col gap-6">

        <div>
          <p className="text-green-400 text-xs font-semibold uppercase tracking-wide">Setup complete</p>
          <h1 className="text-2xl font-semibold text-zinc-100 mt-0.5">Your account is configured</h1>
          <p className="text-zinc-400 text-sm mt-1">
            Here's a summary of what was applied. Skipped items can be configured any time from the dashboard.
          </p>
        </div>

        <div className="flex gap-4 items-start">
          <div className="flex-1 flex flex-col gap-4">
            {groupCard('Account', rows.slice(0, 4))}
            {groupCard('Alerts',  rows.slice(4, 7))}
          </div>
          <div className="flex-1">
            {groupCard('Security', rows.slice(7))}
          </div>
        </div>

        <div className="flex justify-end">
          <button onClick={() => setPageMode('detail')}
            className="px-6 py-2 text-sm bg-blue-700 hover:bg-blue-600 text-white font-medium rounded transition-colors">
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
            <span className={`text-xs shrink-0 ${row.ok === null ? 'text-zinc-500' : 'text-zinc-200'}`}>
              {row.label}
            </span>
            <span className={`text-xs font-mono flex-1 min-w-0 truncate text-right ${
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

  // Where "Continue setup →" should resume, and whether the mandatory part
  // of the wizard (root MFA → IAM user → IAM MFA) is still outstanding.
  const setupIncomplete = isRootCaller || !iamMfaDone
  const resumeStep = isRootCaller ? (mfaDone || mfaEnabled ? 2 : 1) : (!iamMfaDone ? 3 : 1)

  return (
    <div className="flex flex-col gap-5">

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold text-zinc-100">Account</h1>
          <div className="flex items-center gap-4 mt-1.5">
            {accountId && (
              <span className="flex items-center gap-1.5 text-xs whitespace-nowrap">
                <span className="text-zinc-500">ID</span>
                <span className="text-zinc-300 font-mono">{accountId}</span>
              </span>
            )}
            {region && (
              <span className="flex items-center gap-1.5 text-xs whitespace-nowrap">
                <span className="text-zinc-500">Region</span>
                <span className="text-zinc-300 font-mono">{region}</span>
              </span>
            )}
            <span className="flex items-center gap-1.5 text-xs whitespace-nowrap">
              <span className="text-zinc-500">Signed in as</span>
              <span className="text-zinc-300 font-mono">{isRootCaller ? 'Root' : (iamUsername || 'IAM user')}</span>
            </span>
          </div>
        </div>
        <button onClick={() => { setWizardStep(resumeStep); setPageMode('wizard') }}
          className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors shrink-0 whitespace-nowrap">
          {setupIncomplete ? 'Continue setup →' : 'Configure alerts & security →'}
        </button>
      </div>

      <div className="flex gap-5 items-start">
        <div className="flex-1 flex flex-col gap-5">
          {detailSection('Account', [
            { label: 'Root MFA',         value: mfaEnabled || mfaDone ? 'Enabled' : 'Disabled',       ok: mfaEnabled || mfaDone },
            { label: 'Root access keys', value: keysPresent ? 'Present' : iamRootKeysDeleted ? 'Deleted' : 'Not detected', ok: !keysPresent },
            { label: 'IAM user',         value: iamSaved ? iamUsername : 'Not created this session',   ok: iamSaved || null },
            { label: 'IAM MFA',          value: iamMfaDone ? 'Enabled' : 'Disabled',                    ok: iamMfaDone },
          ])}

          {!isRootCaller && iamUsername && (
            <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-2">
              <div>
                <p className="text-zinc-200 text-xs font-semibold">IAM User</p>
                <p className="text-zinc-500 text-xs mt-0.5">
                  Username <span className="text-zinc-300 font-mono">{iamUsername}</span>
                  {region && <> · Region <span className="text-zinc-300 font-mono">{region}</span></>}
                  {accountId && <> · Account <span className="text-zinc-300 font-mono">{accountId}</span></>}
                </p>
              </div>
              {rotateError && <p className="text-red-400 text-xs">{rotateError}</p>}
              {rotateResult ? (
                <div className="bg-zinc-900 border border-zinc-600 rounded p-2 flex flex-col gap-1">
                  <p className="text-amber-400 text-xs font-medium">New key created and saved — old key deleted. Copy the secret now, it's shown only once.</p>
                  {([['Key ID', rotateResult.accessKeyId, rotateKeyCopied, setRotateKeyCopied], ['Secret', rotateResult.secretAccessKey, rotateSecretCopied, setRotateSecretCopied]] as const).map(([label, val, copied, setCopied]) => (
                    <div key={label} className="flex items-center gap-2">
                      <span className="text-zinc-400 text-xs w-10 shrink-0">{label}</span>
                      <code className="flex-1 text-zinc-100 text-xs font-mono truncate">{val}</code>
                      <button onClick={() => copy(val, setCopied as (v: boolean) => void)} className="text-xs text-zinc-400 hover:text-zinc-200 shrink-0">
                        {copied ? 'Copied' : 'Copy'}
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <button onClick={handleRotateAccessKey} disabled={rotateBusy}
                  className="self-start px-3 py-1.5 text-xs border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                  {rotateBusy ? 'Rotating...' : 'Rotate Access Key'}
                </button>
              )}
            </div>
          )}

          {detailSection('Alerts', [
            { label: 'Billing alert',          value: budgetDone  ? `$${budgetAmount}/mo → ${budgetEmail}`        : 'Skipped', ok: budgetDone  || null },
            { label: 'Cost anomaly detection', value: anomalyDone ? `$${anomalyThreshold} threshold → ${anomalyEmail}` : 'Skipped', ok: anomalyDone || null },
            { label: 'Root login alarm',       value: alarmDone   ? alarmEmail                                    : 'Skipped', ok: alarmDone   || null },
          ])}
        </div>

        <div className="flex-1">
          {detailSection('Security hardening', [
            { label: 'IAM password policy',    value: pwPolicy.done  ? 'Applied' : 'Skipped', ok: pwPolicy.done  || null },
            { label: 'S3 block public access', value: s3Block.done   ? 'Applied' : 'Skipped', ok: s3Block.done   || null },
            { label: 'GuardDuty',             value: guardDuty.done  ? 'Enabled' : 'Skipped', ok: guardDuty.done || null },
            { label: 'IAM Access Analyzer',   value: accessAn.done   ? 'Enabled' : 'Skipped', ok: accessAn.done  || null },
            { label: 'GuardDuty SMS alert',   value: smsDone ? smsPhone                       : 'Skipped', ok: smsDone        || null },
          ])}
        </div>
      </div>

    </div>
  )
}
