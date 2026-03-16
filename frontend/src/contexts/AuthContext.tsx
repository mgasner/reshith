import { createContext, useContext, useState, useCallback, ReactNode } from 'react'

export interface AuthUser {
  id: string
  username: string
  email: string
  displayName: string
}

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  login: (user: AuthUser, token: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

const STORAGE_KEY = 'reshith_auth'

function loadFromStorage(): { user: AuthUser; token: string } | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<{ user: AuthUser; token: string } | null>(
    loadFromStorage
  )

  const login = useCallback((user: AuthUser, token: string) => {
    const next = { user, token }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    setState(next)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setState(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user: state?.user ?? null, token: state?.token ?? null, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
