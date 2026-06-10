import { useState, useEffect, useRef } from 'react'

interface LogsPageProps {
  isActive: boolean
}

export default function LogsPage({ isActive }: LogsPageProps) {
  const [content, setContent] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isActive) loadLog()
  }, [isActive])

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end' })
  }, [content])

  async function loadLog() {
    setLoading(true)
    setError(null)
    const result = await window.electronAPI.readLog()
    if (result.ok) {
      setContent(result.content ?? '')
    } else {
      setError('Could not read log file.')
    }
    setLoading(false)
  }

  return (
    <div className="h-full flex flex-col gap-4">

      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <h1 className="text-2xl font-semibold text-zinc-100">Console</h1>
        <div className="flex gap-2">
          <button
            onClick={loadLog}
            disabled={loading}
            className="px-4 py-2 text-sm border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
          <button
            onClick={() => window.electronAPI.openLogDir()}
            className="px-4 py-2 text-sm border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors"
          >
            Open folder
          </button>
        </div>
      </div>

      {/* Log content */}
      <div className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg overflow-y-auto p-4 font-mono text-xs text-zinc-400 leading-relaxed">
        {error && <p className="text-red-400">{error}</p>}
        {!error && !content && !loading && (
          <p className="text-zinc-600">No log entries yet. Run Make, Provision, or Delete to see output here.</p>
        )}
        {content && (
          <pre className="whitespace-pre-wrap break-words">{content}</pre>
        )}
        <div ref={endRef} />
      </div>

    </div>
  )
}
