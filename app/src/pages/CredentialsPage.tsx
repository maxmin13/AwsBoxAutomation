import { useState, useEffect } from 'react'

export default function CredentialsPage() {
  const [accessKeyId,     setAccessKeyId]     = useState('')
  const [secretAccessKey, setSecretAccessKey] = useState('')
  const [region,          setRegion]          = useState('eu-west-1')
  const [saved,           setSaved]           = useState(false)
  const [loading,         setLoading]         = useState(true)

  useEffect(() => {
    window.electronAPI.loadCredentials().then((creds) => {
      if (creds.accessKeyId)     setAccessKeyId(creds.accessKeyId)
      if (creds.secretAccessKey) setSecretAccessKey(creds.secretAccessKey)
      if (creds.region)          setRegion(creds.region)
      setLoading(false)
    })
  }, [])

  async function handleSave() {
    await window.electronAPI.saveCredentials(accessKeyId.trim(), secretAccessKey.trim(), region.trim())
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  const ic = (val: string) =>
    'w-full px-2.5 py-1.5 bg-zinc-700 border rounded text-zinc-100 text-sm font-mono ' +
    'focus:outline-none focus:border-blue-500 ' +
    (val ? 'border-zinc-400' : 'border-zinc-600')

  if (loading) {
    return <div className="text-zinc-400 text-sm">Loading...</div>
  }

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-semibold text-zinc-100 mb-1">Credentials</h1>
      <p className="text-zinc-500 text-sm mb-6">
        AWS IAM credentials passed as environment variables to the scripts. Stored locally and never sent anywhere.
      </p>

      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-5 space-y-4">

        <div>
          <label className="block text-zinc-400 text-xs mb-1">AWS_ACCESS_KEY_ID</label>
          <input
            type="text"
            value={accessKeyId}
            onChange={(e) => { setAccessKeyId(e.target.value); setSaved(false) }}
            placeholder="AKIAIOSFODNN7EXAMPLE"
            autoComplete="off"
            className={ic(accessKeyId)}
          />
        </div>

        <div>
          <label className="block text-zinc-400 text-xs mb-1">AWS_SECRET_ACCESS_KEY</label>
          <input
            type="password"
            value={secretAccessKey}
            onChange={(e) => { setSecretAccessKey(e.target.value); setSaved(false) }}
            placeholder="••••••••••••••••••••••••••••••••"
            autoComplete="off"
            className={ic(secretAccessKey)}
          />
        </div>

        <div>
          <label className="block text-zinc-400 text-xs mb-1">AWS_DEFAULT_REGION</label>
          <input
            type="text"
            value={region}
            onChange={(e) => { setRegion(e.target.value); setSaved(false) }}
            placeholder="eu-west-1"
            autoComplete="off"
            className={ic(region)}
          />
        </div>

        <div className="flex items-center gap-3 pt-1">
          <button
            onClick={handleSave}
            disabled={!accessKeyId || !secretAccessKey || !region}
            className="px-4 py-2 text-sm bg-blue-700 hover:bg-blue-600 text-white font-medium rounded transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Save
          </button>
          {saved && (
            <span className="text-green-400 text-xs">Saved.</span>
          )}
        </div>
      </div>

      <div className="mt-4 bg-zinc-800 border border-zinc-700 rounded-lg p-4">
        <p className="text-zinc-500 text-xs leading-relaxed">
          Credentials are stored base64-encoded in <span className="text-zinc-400 font-mono">~/.config/AwsBoxAutomation/credentials.json</span>.<br />
          They are passed as <span className="text-zinc-400 font-mono">AWS_ACCESS_KEY_ID</span>, <span className="text-zinc-400 font-mono">AWS_SECRET_ACCESS_KEY</span>, and <span className="text-zinc-400 font-mono">AWS_DEFAULT_REGION</span> environment variables when a script runs.
        </p>
      </div>
    </div>
  )
}
