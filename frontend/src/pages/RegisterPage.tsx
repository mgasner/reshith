import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation } from '@apollo/client'
import { REGISTER } from '@/graphql/operations'
import { useAuth } from '@/contexts/AuthContext'

export function RegisterPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [registerMutation, { loading }] = useMutation(REGISTER)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const { data } = await registerMutation({
        variables: {
          input: {
            username,
            email,
            password,
            displayName: displayName.trim() || null,
          },
        },
      })
      const payload = data?.register
      if (!payload) {
        setError('Registration failed.')
        return
      }
      login(payload.user, payload.token)
      navigate('/decks', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed.')
    }
  }

  return (
    <div className="max-w-md mx-auto px-4">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Create account</h1>
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
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              className="w-full border rounded px-3 py-2"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="displayName">
              Display name <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              id="displayName"
              className="w-full border rounded px-3 py-2"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
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
              autoComplete="new-password"
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <p className="text-xs text-gray-500 mt-1">At least 8 characters.</p>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>
        <p className="text-sm text-gray-600 mt-4">
          Already have an account?{' '}
          <Link className="text-blue-600 hover:underline" to="/login">
            Log in
          </Link>
        </p>
      </div>
    </div>
  )
}
