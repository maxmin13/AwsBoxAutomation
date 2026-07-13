import { useEffect, useRef, useState } from 'react'

interface LogsPageProps {
  isActive: boolean
}

export default function LogsPage({ isActive }: LogsPageProps) {
  const [content,     setContent]     = useState('')
  const [error,       setError]       = useState<string | null>(null)
  const [loading,     setLoading]     = useState(false)
  const [syncEnabled, setSyncEnabled] = useState(true)
  const contentRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (isActive) loadLog()
  }, [isActive])

  // Poll every 2.5 s while sync is on
  useEffect(() => {
    if (!syncEnabled) return
    const id = setInterval(async () => {
      const result = await window.electronAPI.readLog()
      if (result.ok) setContent(result.content ?? '')
    }, 2500)
    return () => clearInterval(id)
  }, [syncEnabled])

  // Scroll to the bottom whenever content changes or the tab becomes active.
  // When hidden (display:none ancestor), scrollHeight is 0 so scrollTop is zeroed out;
  // re-running on isActive ensures we scroll once the element is visible again.
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight
    }
  }, [content, isActive])

  async function loadLog(silent = false) {
    if (!silent) {
      setLoading(true)
      setError(null)
    }
    const result = await window.electronAPI.readLog()
    if (result.ok) {
      setContent(result.content ?? '')
    } else if (!silent) {
      setError('Could not read log file.')
    }
    if (!silent) setLoading(false)
  }

  return (
    <div className="flex gap-6 h-full">

      {/* Sidebar */}
      <aside className="w-52 shrink-0">
        <p className="text-zinc-500 text-xs uppercase tracking-wider mb-3">Log file</p>
        <div className="w-full text-left px-3 py-2 rounded text-sm bg-zinc-700 text-zinc-100">
          <span className="block font-medium">GUI log</span>
          <span className="block text-xs text-zinc-500 mt-0.5">Electron main process — IPC calls, replies, errors</span>
        </div>

        <button
          onClick={() => loadLog()}
          disabled={loading || syncEnabled}
          className="mt-4 w-full px-3 py-2 rounded text-sm bg-zinc-700 text-zinc-100 hover:bg-zinc-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>

        <label className="mt-3 flex items-center gap-2 text-sm text-zinc-400 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={syncEnabled}
            onChange={e => setSyncEnabled(e.target.checked)}
            className="accent-indigo-500"
          />
          Sync
        </label>

        <p className="text-zinc-500 text-xs uppercase tracking-wider mt-6 mb-3">Open folder</p>
        <button
          onClick={() => window.electronAPI.openLogDir()}
          className="w-full text-left px-3 py-2 rounded text-sm text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
        >
          App logs
          <span className="block text-xs text-zinc-600 mt-0.5">gui.log</span>
        </button>
      </aside>

      {/* Log content */}
      <main ref={contentRef} className="flex-1 min-w-0 overflow-y-auto">
        {loading && (
          <p className="text-zinc-500 text-sm">Loading...</p>
        )}

        {error && (
          <div className="bg-red-900 border border-red-700 rounded p-4 text-red-300 text-sm">
            {error}
          </div>
        )}

        {!loading && !error && content === '' && (
          <p className="text-zinc-500 text-sm">Log file is empty.</p>
        )}

        {!loading && !error && content !== '' && (
          <pre className="text-zinc-300 text-xs font-mono whitespace-pre-wrap break-all leading-relaxed">
            {content}
          </pre>
        )}
      </main>
    </div>
  )
}
