import { useState, useEffect } from 'react'
import type { InstanceInfo } from '../electron.d'
import ProvisionPage from './ProvisionPage'
import { useAuth } from '../AuthContext'
import PricingLink from '../components/PricingLink'

type View = null | 'provision' | 'detail'

export default function DatacenterPage() {
  const { requireCreds, withAuth } = useAuth()
  const [view, setView] = useState<View>(null)
  const [info, setInfo] = useState<InstanceInfo | null>(null)

  useEffect(() => {
    if (view === null) loadStatus()
  }, [view])

  async function loadStatus() {
    setInfo(null)
    const result = await window.electronAPI.describeDatacenter()
    if (result.ok) {
      setInfo({ found: result.found, state: result.state, instanceId: result.instanceId, instanceType: result.instanceType, publicIp: result.publicIp, publicDns: result.publicDns, launchTime: result.launchTime })
    } else {
      setInfo({ found: false })
    }
  }

  if (view === 'provision') return <ProvisionPage onBack={() => setView(null)} />
  if (view === 'detail') return <DetailPage info={info ?? { found: false }} onBack={() => setView(null)} />

  return (
    <div className="max-w-4xl mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-zinc-100">My VMs</h1>
        <button
          onClick={loadStatus}
          disabled={info === null}
          className="px-4 py-2 text-sm border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {info === null ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Instance card */}
      {info === null ? (
        <div className="text-zinc-500 text-sm">Loading...</div>
      ) : !info.found ? (
        <div className="text-zinc-500 text-sm">No VMs found. Use the <span className="text-zinc-300">Create VM</span> tab to provision one.</div>
      ) : (
        <InstanceCard
          info={info}
          onProvision={() => requireCreds(() => withAuth(() => setView('provision')))}
          onDetail={() => requireCreds(() => withAuth(() => setView('detail')))}
          onRefresh={loadStatus}
        />
      )}

    </div>
  )
}

// ── InstanceCard ──────────────────────────────────────────────────────────────

interface InstanceCardProps {
  info:        InstanceInfo
  onProvision: () => void
  onDetail:    () => void
  onRefresh:   () => void
}

function InstanceCard({ info, onProvision, onDetail, onRefresh }: InstanceCardProps) {
  const { requireCreds, withAuth, withSession } = useAuth()
  const [busy,     setBusy]     = useState(false)
  const [starting, setStarting] = useState(false)
  const [stopping, setStopping] = useState(false)
  const [error,    setError]    = useState<string | null>(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showStopModal,   setShowStopModal]   = useState(false)

  const isRunning  = info.found && info.state === 'running'
  const isStopped  = info.found && info.state === 'stopped'
  const inTransit  = info.found && (info.state === 'pending' || info.state === 'stopping')

  async function handleStart() {
    if (!info.instanceId) return
    setBusy(true); setStarting(true); setError(null)
    try {
      const result = await window.electronAPI.startInstance(info.instanceId)
      if (!result.ok) setError(result.error ?? 'Failed to start instance')
    } finally {
      setBusy(false); setStarting(false); onRefresh()
    }
  }

  async function handleStop() {
    if (!info.instanceId) return
    setShowStopModal(false)
    setBusy(true); setStopping(true); setError(null)
    try {
      const result = await window.electronAPI.stopInstance(info.instanceId)
      if (!result.ok) setError(result.error ?? 'Failed to stop instance')
    } finally {
      setBusy(false); setStopping(false); onRefresh()
    }
  }

  return (
    <>
      {showStopModal && (
        <StopModal
          busy={busy}
          onConfirm={handleStop}
          onCancel={() => setShowStopModal(false)}
        />
      )}
      {showDeleteModal && (
        <DeleteModal
          onConfirm={() => { setShowDeleteModal(false); onRefresh() }}
          onCancel={() => setShowDeleteModal(false)}
        />
      )}

      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3 max-w-sm">

        {/* Name and status */}
        <div className="flex items-center justify-between">
          <span className="text-zinc-100 font-medium">dtc-box</span>
          <StateBadge
            state={info.found ? (info.state ?? 'unknown') : 'not created'}
            starting={starting}
            stopping={stopping}
          />
        </div>

        {/* Instance ID */}
        {info.found && info.instanceId && (
          <p className="text-zinc-500 text-xs font-mono truncate">{info.instanceId}</p>
        )}
        {!info.found && (
          <p className="text-zinc-600 text-xs">No instance found in eu-west-1</p>
        )}

        {/* Public IP */}
        {info.publicIp && (
          <p className="text-zinc-400 text-xs">{info.publicIp} · dtc.maxmin.it</p>
        )}

        {info.found && (
          <p className="text-zinc-600 text-xs">
            Billed while running · <PricingLink url="https://aws.amazon.com/ec2/pricing/" label="EC2 pricing ↗" />
          </p>
        )}

        {error && <p className="text-red-400 text-xs">{error}</p>}

        {/* Action buttons */}
        <div className="flex gap-2 mt-1 flex-wrap">

          {/* Start / Stop — mutually exclusive */}
          {isRunning || inTransit ? (
            <button
              onClick={() => requireCreds(() => withSession(() => setShowStopModal(true)))}
              disabled={busy || inTransit}
              className="px-3 py-1 text-sm bg-red-700 hover:bg-red-600 text-white font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {stopping ? 'Stopping...' : 'Stop'}
            </button>
          ) : (
            <button
              onClick={() => requireCreds(() => withSession(handleStart))}
              disabled={busy || !info.found || (!isStopped && !inTransit)}
              className="px-3 py-1 text-sm bg-blue-700 hover:bg-blue-600 text-white font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {starting ? 'Starting...' : 'Start'}
            </button>
          )}

          <button
            onClick={() => requireCreds(() => withAuth(() => setShowDeleteModal(true)))}
            disabled={busy || isRunning || inTransit}
            className="px-3 py-1 text-sm border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Delete
          </button>

          <button
            onClick={onProvision}
            disabled={busy}
            className="px-3 py-1 text-sm border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed ml-auto"
          >
            Provision
          </button>

          <button
            onClick={onDetail}
            disabled={busy}
            className="px-3 py-1 text-sm border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Detail
          </button>

        </div>
      </div>
    </>
  )
}

// ── StateBadge ────────────────────────────────────────────────────────────────

function StateBadge({ state, starting = false, stopping = false }: { state: string; starting?: boolean; stopping?: boolean }) {
  const label = starting ? 'starting…' : stopping ? 'stopping…' : state
  const styles: Record<string, string> = {
    running:       'bg-green-800 text-green-200',
    stopped:       'bg-zinc-700  text-zinc-300',
    pending:       'bg-blue-900  text-blue-200',
    stopping:      'bg-amber-900 text-amber-200',
    'not created': 'bg-zinc-700  text-zinc-400',
  }
  const cls = styles[state] ?? 'bg-zinc-700 text-zinc-400'
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium capitalize ${cls}`}>
      {label}
    </span>
  )
}

// ── StopModal ─────────────────────────────────────────────────────────────────

interface StopModalProps {
  busy:      boolean
  onConfirm: () => void
  onCancel:  () => void
}

function StopModal({ busy, onConfirm, onCancel }: StopModalProps) {
  useEffect(() => {
    function handleKey(e: KeyboardEvent) { if (e.key === 'Escape') onCancel() }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [onCancel])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={onCancel}
    >
      <div
        className="bg-zinc-800 border border-zinc-700 rounded-xl p-8 max-w-sm w-full mx-4 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="text-zinc-400 text-sm text-center mb-2">Stop this instance?</p>
        <p className="text-zinc-100 text-2xl font-bold text-center mb-6">dtc-box</p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={onCancel}
            disabled={busy}
            className="px-4 py-2 text-sm border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className="px-4 py-2 text-sm bg-red-700 hover:bg-red-600 text-white font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Stop instance
          </button>
        </div>
      </div>
    </div>
  )
}

// ── DetailPage ────────────────────────────────────────────────────────────────

interface DetailPageProps {
  info:   InstanceInfo
  onBack: () => void
}

function DetailPage({ info, onBack }: DetailPageProps) {
  const rows: [string, string][] = [
    ['Instance ID',   info.instanceId   ?? '—'],
    ['State',         info.state        ?? '—'],
    ['Type',          info.instanceType ?? '—'],
    ['Public IP',     info.publicIp     ?? '—'],
    ['Public DNS',    info.publicDns    ?? '—'],
    ['DNS record',    'dtc.maxmin.it'],
    ['Region',        'eu-west-1'],
    ['Launch time',   info.launchTime ? new Date(info.launchTime).toLocaleString() : '—'],
  ]

  return (
    <div className="max-w-2xl mx-auto">

      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={onBack}
          className="px-3 py-1 text-sm border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors"
        >
          ← Back
        </button>
        <h1 className="text-xl font-semibold text-zinc-100">Detail — dtc-box</h1>
      </div>

      <div className="bg-zinc-800 border border-zinc-700 rounded-lg overflow-hidden">
        <dl className="divide-y divide-zinc-700">
          {rows.map(([label, value]) => (
            <div key={label} className="px-4 py-3 flex justify-between gap-4">
              <dt className="text-zinc-500 text-sm shrink-0">{label}</dt>
              <dd className="text-zinc-200 text-sm font-mono text-right break-all">{value}</dd>
            </div>
          ))}
        </dl>
      </div>

      <p className="text-zinc-600 text-xs mt-3">
        Billed while running · <PricingLink url="https://aws.amazon.com/ec2/pricing/" label="EC2 pricing ↗" />
      </p>

    </div>
  )
}

// ── DeleteModal ───────────────────────────────────────────────────────────────

interface DeleteModalProps {
  onConfirm: () => void
  onCancel:  () => void
}

function DeleteModal({ onConfirm, onCancel }: DeleteModalProps) {
  const [confirmed, setConfirmed] = useState(false)

  useEffect(() => {
    function handleKey(e: KeyboardEvent) { if (e.key === 'Escape') onCancel() }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [onCancel])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={onCancel}
    >
      <div
        className="bg-zinc-800 border border-zinc-700 rounded-xl p-8 max-w-sm w-full mx-4 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="text-zinc-400 text-sm text-center mb-2">Permanently delete this datacenter?</p>
        <p className="text-zinc-100 text-2xl font-bold text-center mb-2">dtc-box</p>
        <p className="text-zinc-500 text-xs text-center mb-6">
          All AWS resources will be removed: DNS record, EC2 instance, security group, subnet, VPC.
        </p>
        <label className="flex items-center gap-2 text-sm text-zinc-400 cursor-pointer select-none mb-6">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
            className="accent-red-500"
          />
          I understand this cannot be undone
        </label>
        <div className="flex gap-3 justify-center">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={!confirmed}
            className="px-4 py-2 text-sm bg-red-700 hover:bg-red-600 text-white font-medium rounded transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Delete permanently
          </button>
        </div>
      </div>
    </div>
  )
}
