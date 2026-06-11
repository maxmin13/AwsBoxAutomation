import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import LoginPage from './pages/LoginPage'

interface AuthContextValue {
  hasCredentials:    boolean | null
  setHasCredentials: (v: boolean) => void
  requireCreds:      (action: () => void) => void
  withAuth:          (action: () => void) => void
}

const AuthContext = createContext<AuthContextValue>({
  hasCredentials:    null,
  setHasCredentials: () => {},
  requireCreds:      (f) => f(),
  withAuth:          (f) => f(),
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [showLogin,      setShowLogin]      = useState(false)
  const [hasCredentials, setHasCredentials] = useState<boolean | null>(null)
  const [credError,      setCredError]      = useState<string | null>(null)
  const pendingAction = useRef<(() => void) | null>(null)

  useEffect(() => {
    window.electronAPI.loadCredentials().then(({ accessKeyId }) => {
      setHasCredentials(!!accessKeyId)
    })
  }, [])

  function requireCreds(action: () => void) {
    if (!hasCredentials) {
      setCredError('IAM credentials required. Create an IAM user first.')
      setTimeout(() => setCredError(null), 4000)
      return
    }
    action()
  }

  async function withAuth(action: () => void) {
    const result = await window.electronAPI.validateCredentials()
    if (result.ok) {
      action()
    } else {
      pendingAction.current = action
      setShowLogin(true)
    }
  }

  function handleLoginSuccess() {
    setShowLogin(false)
    setHasCredentials(true)
    const action = pendingAction.current
    pendingAction.current = null
    if (action) action()
  }

  function handleLoginBack() {
    setShowLogin(false)
    pendingAction.current = null
  }

  return (
    <AuthContext.Provider value={{ hasCredentials, setHasCredentials, requireCreds, withAuth }}>
      {children}
      {credError && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[60] px-4 py-2 bg-red-900/90 border border-red-700 rounded text-red-200 text-xs shadow-lg whitespace-nowrap">
          {credError}
        </div>
      )}
      {showLogin && (
        <div className="fixed inset-0 z-50 bg-zinc-900 overflow-y-auto p-6">
          <LoginPage onNext={handleLoginSuccess} onBack={handleLoginBack} />
        </div>
      )}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
