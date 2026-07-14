interface PricingLinkProps {
  url:   string
  label?: string
}

export default function PricingLink({ url, label = 'AWS pricing ↗' }: PricingLinkProps) {
  return (
    <button onClick={() => window.electronAPI.openExternal(url)}
      className="underline text-zinc-500 hover:text-zinc-300 transition-colors">{label}</button>
  )
}
