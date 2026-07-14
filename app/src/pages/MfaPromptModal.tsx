import { useEffect, useState } from 'react'

interface MfaPromptModalProps {
  onSubmit: (code: string) => Promise<{ ok: boolean; error?: string }>
  onCancel: () => void
}

export default function MfaPromptModal({ onSubmit, onCancel }: MfaPromptModalProps) {
  const [code,  setCode]  = useState('')
  const [busy,  setBusy]  = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    function handleKey(e: KeyboardEvent) { if (e.key === 'Escape' && !busy) onCancel() }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [busy, onCancel])

  async function handleSubmit() {
    if (code.trim().length < 6 || busy) return
    setBusy(true)
    setError(null)
    const res = await onSubmit(code.trim())
    setBusy(false)
    if (!res.ok) setError(res.error ?? 'Unknown error')
  }

  const ic = (value: string) =>
    'w-full px-2.5 py-1.5 bg-zinc-700 border rounded text-zinc-100 text-sm text-center tracking-widest ' +
    'focus:outline-none focus:border-blue-500 ' +
    (value ? 'border-zinc-400' : 'border-zinc-600')

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-zinc-800 border border-zinc-700 rounded-xl p-8 max-w-sm w-full mx-4 shadow-2xl">
        <p className="text-zinc-100 text-lg font-semibold text-center mb-1">Session expired</p>
        <p className="text-zinc-500 text-xs text-center mb-6">
          Enter a fresh MFA code to start a new session.
        </p>

        <input
          type="text"
          inputMode="numeric"
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
          onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit() }}
          placeholder="000000"
          autoFocus
          className={ic(code)}
        />

        {error && <p className="text-red-400 text-xs text-center mt-3">{error}</p>}

        <div className="flex gap-3 justify-center mt-6">
          <button
            onClick={onCancel}
            disabled={busy}
            className="px-4 py-2 text-sm border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={busy || code.length < 6}
            className="px-4 py-2 text-sm bg-blue-700 hover:bg-blue-600 text-white font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {busy ? 'Verifying...' : 'Continue'}
          </button>
        </div>
      </div>
    </div>
  )
}
