import { FormEvent, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useMutation } from '@apollo/client'
import { LOGIN } from '@/graphql/operations'
import { useAuth } from '@/contexts/AuthContext'

interface LocationState {
  from?: string
}

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loginMutation, { loading }] = useMutation(LOGIN)

  const redirectTo = (location.state as LocationState | null)?.from ?? '/decks'

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const { data } = await loginMutation({
        variables: { input: { username, password } },
      })
      const payload = data?.login
      if (!payload) {
        setError('Invalid username or password.')
        return
      }
      login(payload.user, payload.token)
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed.')
    }
  }

  return (
    <div className="max-w-md mx-auto px-4">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Log in</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              className="w-full border rounded px-3 py-2"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              className="w-full border rounded px-3 py-2"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Logging in…' : 'Log in'}
          </button>
        </form>
        <p className="text-sm text-gray-600 mt-4">
          No account?{' '}
          <Link className="text-blue-600 hover:underline" to="/register">
            Create one
          </Link>
        </p>
      </div>
    </div>
  )
}
