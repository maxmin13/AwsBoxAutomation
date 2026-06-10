import { useEffect, useState } from 'react'

export default function AccountPage() {
  const [accessKeyId,     setAccessKeyId]     = useState('')
  const [secretAccessKey, setSecretAccessKey] = useState('')
  const [region,          setRegion]          = useState('eu-west-1')
  const [showSecret,      setShowSecret]      = useState(false)
  const [saving,          setSaving]          = useState(false)
  const [saved,           setSaved]           = useState(false)
  const [error,           setError]           = useState<string | null>(null)

  useEffect(() => {
    window.electronAPI.loadCredentials().then((creds) => {
      if (creds.accessKeyId)     setAccessKeyId(creds.accessKeyId)
      if (creds.secretAccessKey) setSecretAccessKey(creds.secretAccessKey)
      if (creds.region)          setRegion(creds.region)
    })
  }, [])

  async function handleSave() {
    if (!accessKeyId || !secretAccessKey || !region) return
    setSaving(true)
    setSaved(false)
    setError(null)
    try {
      await window.electronAPI.saveCredentials(accessKeyId, secretAccessKey, region)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  const canSave = !!accessKeyId && !!secretAccessKey && !!region && !saving

  const ic = (value: string) =>
    'w-full px-2.5 py-1.5 bg-zinc-700 border rounded text-zinc-100 text-sm ' +
    'focus:outline-none focus:border-blue-500 ' +
    (value ? 'border-zinc-400' : 'border-zinc-600')

  return (
    <div className="max-w-md mx-auto">

      <h1 className="text-2xl font-semibold text-zinc-100 mb-1">My Account</h1>
      <p className="text-zinc-400 text-sm mb-4">AWS credentials used to manage your instances.</p>

      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-5 space-y-3">

        <div>
          <label className="block text-zinc-400 text-xs mb-1">AWS Access Key ID</label>
          <input
            type="text"
            value={accessKeyId}
            onChange={(e) => setAccessKeyId(e.target.value)}
            placeholder="AKIAIOSFODNN7EXAMPLE"
            autoComplete="off"
            className={ic(accessKeyId)}
          />
        </div>

        <div>
          <label className="block text-zinc-400 text-xs mb-1">AWS Secret Access Key</label>
          <div className="relative">
            <input
              type={showSecret ? 'text' : 'password'}
              value={secretAccessKey}
              onChange={(e) => setSecretAccessKey(e.target.value)}
              placeholder="••••••••"
              autoComplete="off"
              className={ic(secretAccessKey) + ' pr-9'}
            />
            <button
              type="button"
              onClick={() => setShowSecret((v) => !v)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-200"
              tabIndex={-1}
            >
              {showSecret ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-5 0-9-4-9-7s4-7 9-7a10.05 10.05 0 011.875.175M15 12a3 3 0 11-6 0 3 3 0 016 0zm6 0c0 3-4 7-9 7M3 3l18 18" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              )}
            </button>
          </div>
        </div>

        <div>
          <label className="block text-zinc-400 text-xs mb-1">Region</label>
          <input
            type="text"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            placeholder="eu-west-1"
            className={ic(region)}
          />
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <button
          onClick={handleSave}
          disabled={!canSave}
          className="w-full px-4 py-2 text-sm bg-blue-700 hover:bg-blue-600 text-white font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : saved ? 'Saved' : 'Save'}
        </button>

      </div>
    </div>
  )
}
