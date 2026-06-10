import { useState } from 'react'
import NavBar from './components/NavBar'
import DatacenterPage from './pages/DatacenterPage'
import CreateVmPage from './pages/CreateVmPage'
import LogsPage from './pages/LogsPage'
import AccountPage from './pages/AccountPage'
import DocsPage from './pages/DocsPage'
import ErrorBoundary from './ErrorBoundary'

export type Page = 'account' | 'vms' | 'create' | 'docs' | 'logs'

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('vms')

  return (
    <div className="flex flex-col h-screen">
      <NavBar currentPage={currentPage} onNavigate={setCurrentPage} />

      <main className="flex-1 overflow-y-auto p-6">
        <ErrorBoundary>
          <div style={{ display: currentPage === 'vms' ? undefined : 'none' }} className="h-full overflow-hidden">
            <DatacenterPage />
          </div>
          {currentPage === 'account' && <AccountPage />}
          {currentPage === 'create' && <CreateVmPage />}
          {currentPage === 'docs' && <DocsPage />}
          <div style={{ display: currentPage === 'logs' ? undefined : 'none' }} className="h-full overflow-hidden">
            <LogsPage isActive={currentPage === 'logs'} />
          </div>
        </ErrorBoundary>
      </main>
    </div>
  )
}
