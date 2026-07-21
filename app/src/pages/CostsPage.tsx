import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import PricingLink from '../components/PricingLink'
import type { CostSummary, CostServiceAmount } from '../electron.d'

export default function CostsPage() {
  const { withAuth } = useAuth()

  const [summary,      setSummary]      = useState<CostSummary | null>(null)
  const [summaryError, setSummaryError] = useState<string | null>(null)
  const [loadingSummary, setLoadingSummary] = useState(true)

  const [breakdown,      setBreakdown]      = useState<CostServiceAmount[] | null>(null)
  const [breakdownError, setBreakdownError] = useState<string | null>(null)
  const [loadingBreakdown, setLoadingBreakdown] = useState(false)

  useEffect(() => { loadSummary() }, [])

  async function loadSummary() {
    setLoadingSummary(true)
    setSummaryError(null)
    const result = await window.electronAPI.getCostSummary()
    if (result.ok) {
      setSummary({
        configured:      !!result.configured,
        limit:           result.limit,
        unit:            result.unit,
        actualSpend:     result.actualSpend,
        forecastedSpend: result.forecastedSpend,
        periodEnd:       result.periodEnd,
      })
    } else {
      setSummaryError(result.error ?? 'Failed to load cost summary.')
    }
    setLoadingSummary(false)
  }

  async function loadBreakdown() {
    setLoadingBreakdown(true)
    setBreakdownError(null)
    const result = await window.electronAPI.getCostBreakdown()
    if (result.ok) {
      setBreakdown(result.services ?? [])
    } else {
      setBreakdownError(result.error ?? 'Failed to load cost breakdown.')
    }
    setLoadingBreakdown(false)
  }

  function fmt(amount?: string | null, unit?: string) {
    return amount == null ? '—' : `${parseFloat(amount).toFixed(2)} ${unit ?? 'USD'}`
  }

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-100">Costs</h1>
        <button
          onClick={() => withAuth(loadSummary)}
          disabled={loadingSummary}
          className="px-4 py-2 text-sm border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loadingSummary ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Free month-to-date / forecast summary, sourced from the account's AWS Budget */}
      {loadingSummary ? (
        <div className="text-zinc-500 text-sm">Loading...</div>
      ) : summaryError ? (
        <div className="text-red-400 text-xs">{summaryError}</div>
      ) : !summary?.configured ? (
        <div className="text-zinc-500 text-sm">
          No budget configured yet. Set one up on the <span className="text-zinc-300">My Account</span> page's Alerts step to see month-to-date and forecasted spend here.
        </div>
      ) : (
        <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-zinc-100">Month to date</h2>
          <div className="grid grid-cols-3 gap-3">
            <Stat label="Accumulated"               value={fmt(summary.actualSpend, summary.unit)} />
            <Stat label="Forecasted (end of month)"  value={fmt(summary.forecastedSpend, summary.unit)} />
            <Stat label="Budget limit"               value={fmt(summary.limit, summary.unit)} />
          </div>
          {summary.periodEnd && (
            <p className="text-zinc-500 text-xs">Budget period ends {summary.periodEnd}.</p>
          )}
        </div>
      )}

      {/* Paid, opt-in per-service breakdown via Cost Explorer */}
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-zinc-100">Breakdown by service</h2>
          <button
            onClick={() => withAuth(loadBreakdown)}
            disabled={loadingBreakdown}
            className="px-3 py-1.5 text-xs bg-blue-700 hover:bg-blue-600 text-white font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loadingBreakdown ? 'Loading...' : breakdown ? 'Refresh breakdown' : 'Show breakdown by service'}
          </button>
        </div>

        <p className="text-zinc-500 text-xs">
          Each click here calls AWS Cost Explorer, which bills per API request — unlike the free totals above. See <PricingLink url="https://aws.amazon.com/aws-cost-management/pricing/" /> for current rates.
        </p>

        {breakdownError && <div className="text-red-400 text-xs">{breakdownError}</div>}

        {breakdown && (
          breakdown.length === 0 ? (
            <div className="text-zinc-500 text-sm">No billable services yet this month.</div>
          ) : (
            <dl className="divide-y divide-zinc-700">
              {breakdown.map(s => (
                <div key={s.service} className="flex justify-between py-1.5 text-sm">
                  <dt className="text-zinc-400">{s.service}</dt>
                  <dd className="text-zinc-100">{fmt(s.amount, s.unit)}</dd>
                </div>
              ))}
            </dl>
          )
        )}
      </div>

    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-zinc-900 border border-zinc-600 rounded p-2 flex flex-col gap-1">
      <span className="text-zinc-500 text-xs">{label}</span>
      <span className="text-zinc-100 text-sm font-medium">{value}</span>
    </div>
  )
}
