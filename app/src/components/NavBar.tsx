import type { Page } from '../App'

interface NavBarProps {
  currentPage: Page
  onNavigate: (page: Page) => void
}

const NAV_ITEMS: { page: Page; label: string }[] = [
  { page: 'account',     label: 'My Account' },
  { page: 'vms',         label: 'My VMs'     },
  { page: 'create',      label: 'Create VM'  },
  { page: 'logs',        label: 'Console'    },
  { page: 'docs',        label: 'Docs'       },
]

export default function NavBar({ currentPage, onNavigate }: NavBarProps) {
  return (
    <nav className="bg-zinc-800 border-b border-zinc-700 px-6 py-3 flex items-center gap-6">
      <span className="text-zinc-100 font-semibold tracking-wide mr-4">
        AwsBox Automation
      </span>

      {NAV_ITEMS.map((item) => {
        const isActive = item.page === currentPage
        return (
          <button
            key={item.page}
            onClick={() => onNavigate(item.page)}
            className={
              isActive
                ? 'px-3 py-1 rounded text-sm font-medium bg-zinc-600 text-white'
                : 'px-3 py-1 rounded text-sm font-medium text-zinc-400 hover:text-zinc-100 hover:bg-zinc-700 transition-colors'
            }
          >
            {item.label}
          </button>
        )
      })}
    </nav>
  )
}
