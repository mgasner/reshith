import { useState } from 'react'
import { useMutation } from '@apollo/client'
import { LOGIN } from '@/graphql/operations'
import { useAuth } from '@/contexts/AuthContext'

interface LoginData {
  login: {
    token: string
    user: { id: string; username: string; email: string; displayName: string }
  } | null
}

export function DebugPanel() {
  const [open, setOpen] = useState(false)
  const { user, login, logout } = useAuth()
  const [loginMutation, { loading, error }] = useMutation<LoginData>(LOGIN)

  const handleAutoLogin = async () => {
    const result = await loginMutation({
      variables: { input: { username: 'dev', password: 'password' } },
    })
    const payload = result.data?.login
    if (payload) {
      login(
        {
          id: payload.user.id,
          username: payload.user.username,
          email: payload.user.email,
          displayName: payload.user.displayName,
        },
        payload.token
      )
    }
  }

  return (
    <div className="fixed bottom-4 left-4 z-50">
      {open ? (
        <div className="bg-gray-900 text-gray-100 rounded-lg shadow-xl p-4 w-64 text-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="font-mono font-bold text-yellow-400">DEBUG</span>
            <button
              onClick={() => setOpen(false)}
              className="text-gray-400 hover:text-white text-lg leading-none"
            >
              ×
            </button>
          </div>

          {user ? (
            <div className="space-y-2">
              <div className="text-green-400 font-mono text-xs">
                Logged in as <span className="font-bold">{user.username}</span>
              </div>
              <button
                onClick={logout}
                className="w-full bg-red-700 hover:bg-red-600 text-white rounded px-3 py-1.5 font-mono text-xs"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="text-gray-400 font-mono text-xs">Not logged in</div>
              <button
                onClick={handleAutoLogin}
                disabled={loading}
                className="w-full bg-blue-700 hover:bg-blue-600 disabled:opacity-50 text-white rounded px-3 py-1.5 font-mono text-xs"
              >
                {loading ? 'Logging in…' : 'Auto-login (dev/password)'}
              </button>
              {error && (
                <div className="text-red-400 font-mono text-xs">{error.message}</div>
              )}
            </div>
          )}
        </div>
      ) : (
        <button
          onClick={() => setOpen(true)}
          className="bg-gray-900 hover:bg-gray-800 text-yellow-400 font-mono text-xs font-bold rounded px-2 py-1 shadow-lg opacity-70 hover:opacity-100 transition-opacity"
          title="Debug panel"
        >
          DBG
        </button>
      )}
    </div>
  )
}
