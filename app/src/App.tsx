import { useState } from 'react'
import NavBar from './components/NavBar'
import DatacenterPage from './pages/DatacenterPage'
import CreateVmPage from './pages/CreateVmPage'
import LogsPage from './pages/LogsPage'
import AccountPage from './pages/AccountPage'
import CostsPage from './pages/CostsPage'
import DocsPage from './pages/DocsPage'
import ErrorBoundary from './ErrorBoundary'
import { AuthProvider } from './AuthContext'

export type Page = 'account' | 'costs' | 'vms' | 'create' | 'docs' | 'logs'

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('vms')

  // Re-clicking "My Account" while already on it wouldn't otherwise change
  // currentPage, so AccountPage would stay mounted in whatever pageMode it
  // was last in (e.g. mid-wizard) instead of returning to the dashboard.
  // Bumping this key forces a remount, which always lands back on 'detail'.
  const [accountNavKey, setAccountNavKey] = useState(0)

  function handleNavigate(page: Page) {
    if (page === 'account') setAccountNavKey(k => k + 1)
    setCurrentPage(page)
  }

  return (
    <div className="flex flex-col h-screen">
      <NavBar currentPage={currentPage} onNavigate={handleNavigate} />

      <main className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="h-full p-6">
          <ErrorBoundary>
            <AuthProvider>
              <div style={{ display: currentPage === 'vms' ? undefined : 'none' }} className="h-full overflow-hidden">
                <DatacenterPage />
              </div>
              {currentPage === 'account' && <AccountPage key={accountNavKey} />}
              {currentPage === 'costs' && <CostsPage />}
              {currentPage === 'create' && <CreateVmPage />}
              {currentPage === 'docs' && <DocsPage />}
              <div style={{ display: currentPage === 'logs' ? undefined : 'none' }} className="h-full overflow-hidden">
                <LogsPage isActive={currentPage === 'logs'} />
              </div>
            </AuthProvider>
          </ErrorBoundary>
        </div>
      </main>
    </div>
  )
}
