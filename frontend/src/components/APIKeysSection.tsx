import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@apollo/client'
import { GET_USER_API_KEYS, UPDATE_USER_API_KEYS } from '@/graphql/operations'

type LLMProvider = 'OPENAI' | 'ANTHROPIC'

interface UserAPIKeys {
  preferredProvider: LLMProvider | null
  hasOpenaiKey: boolean
  hasAnthropicKey: boolean
  openaiKeyLast4: string | null
  anthropicKeyLast4: string | null
  encryptionConfigured: boolean
}

/**
 * "LLM API Keys" section of the Settings page.
 *
 * Lets a logged-in user store their own OpenAI / Anthropic key (encrypted
 * at rest server-side) and pick which provider should be used for LLM-powered
 * features (translation help, drill generation, dynamic exercise mappings).
 * The user's key takes precedence over the server's env-configured key; if
 * neither is present the features degrade gracefully.
 *
 * Keys are never echoed back from the server — we only show the last 4
 * characters as a "this is the one you saved" confirmation.
 */
export function APIKeysSection() {
  const { data, loading, error, refetch } = useQuery<{ userApiKeys: UserAPIKeys }>(
    GET_USER_API_KEYS,
    { fetchPolicy: 'cache-and-network' },
  )
  const [updateKeys, { loading: saving }] = useMutation(UPDATE_USER_API_KEYS)

  const [openaiInput, setOpenaiInput] = useState('')
  const [anthropicInput, setAnthropicInput] = useState('')
  const [preferred, setPreferred] = useState<LLMProvider | ''>('')
  const [status, setStatus] = useState<string | null>(null)
  const [errMsg, setErrMsg] = useState<string | null>(null)

  const current = data?.userApiKeys

  useEffect(() => {
    if (current?.preferredProvider) {
      setPreferred(current.preferredProvider)
    }
  }, [current?.preferredProvider])

  if (loading && !data) {
    return <div className="text-gray-500">Loading API keys…</div>
  }
  if (error) {
    return <div className="text-red-600">Failed to load: {error.message}</div>
  }
  if (!current) return null

  const handleSave = async () => {
    setStatus(null)
    setErrMsg(null)
    try {
      // Detect when the user explicitly picked "Server default" and the
      // backend currently has a stored preference, so we send the explicit
      // clear flag instead of null (which means "leave unchanged").
      const clearPreferred = preferred === '' && current?.preferredProvider != null
      await updateKeys({
        variables: {
          input: {
            openaiApiKey: openaiInput || null,
            anthropicApiKey: anthropicInput || null,
            preferredProvider: preferred || null,
            clearPreferredProvider: clearPreferred,
          },
        },
      })
      setOpenaiInput('')
      setAnthropicInput('')
      await refetch()
      setStatus('Saved')
    } catch (e) {
      setErrMsg(e instanceof Error ? e.message : String(e))
    }
  }

  const handleClear = async (provider: LLMProvider) => {
    setStatus(null)
    setErrMsg(null)
    try {
      await updateKeys({
        variables: {
          input:
            provider === 'OPENAI'
              ? { clearOpenai: true }
              : { clearAnthropic: true },
        },
      })
      await refetch()
      setStatus(`Cleared ${provider === 'OPENAI' ? 'OpenAI' : 'Anthropic'} key`)
    } catch (e) {
      setErrMsg(e instanceof Error ? e.message : String(e))
    }
  }

  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold text-gray-800 mb-1">LLM API Keys</h2>
      <p className="text-sm text-gray-600 mb-4">
        Use your own OpenAI or Anthropic key for translation help, drills, and
        exercise generation. Keys are encrypted at rest on the server and only
        used for your own requests. Without a personal key, LLM features fall
        back to the server's default key (if configured).
      </p>

      {!current.encryptionConfigured && (
        <div className="mb-4 p-3 rounded-lg border border-amber-300 bg-amber-50 text-sm text-amber-900">
          The server isn't configured to encrypt secrets, so saving API keys is
          disabled. Ask an administrator to set <code>SECRETS_ENCRYPTION_KEY</code> in
          the backend environment.
        </div>
      )}

      <div className="grid grid-cols-1 gap-5">
        <KeyRow
          label="OpenAI API key"
          placeholder="sk-…"
          inputValue={openaiInput}
          onInputChange={setOpenaiInput}
          stored={current.hasOpenaiKey}
          last4={current.openaiKeyLast4}
          onClear={() => handleClear('OPENAI')}
          disabled={!current.encryptionConfigured || saving}
        />
        <KeyRow
          label="Anthropic API key"
          placeholder="sk-ant-…"
          inputValue={anthropicInput}
          onInputChange={setAnthropicInput}
          stored={current.hasAnthropicKey}
          last4={current.anthropicKeyLast4}
          onClear={() => handleClear('ANTHROPIC')}
          disabled={!current.encryptionConfigured || saving}
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Preferred provider
          </label>
          <select
            value={preferred}
            onChange={(e) => setPreferred(e.target.value as LLMProvider | '')}
            className="px-3 py-2 border border-gray-300 rounded-lg w-full sm:w-auto"
            disabled={saving}
          >
            <option value="">Server default</option>
            <option value="OPENAI">OpenAI</option>
            <option value="ANTHROPIC">Anthropic</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Determines which provider is used when both keys are configured.
            Note: Hebrew Gesenius (GKC) semantic search always uses OpenAI
            embeddings.
          </p>
        </div>
      </div>

      <div className="mt-5 flex items-center gap-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving || !current.encryptionConfigured}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save'}
        </button>
        {status && <span className="text-sm text-green-700">{status}</span>}
        {errMsg && <span className="text-sm text-red-700">{errMsg}</span>}
      </div>
    </section>
  )
}

interface KeyRowProps {
  label: string
  placeholder: string
  inputValue: string
  onInputChange: (value: string) => void
  stored: boolean
  last4: string | null
  onClear: () => void
  disabled: boolean
}

function KeyRow({
  label,
  placeholder,
  inputValue,
  onInputChange,
  stored,
  last4,
  onClear,
  disabled,
}: KeyRowProps) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <label className="block text-sm font-medium text-gray-700">{label}</label>
        {stored && (
          <span className="text-xs text-gray-500">
            Stored: <code>••••{last4 ?? ''}</code>
            <button
              type="button"
              onClick={onClear}
              disabled={disabled}
              className="ml-3 text-red-600 hover:underline disabled:opacity-50"
            >
              Remove
            </button>
          </span>
        )}
      </div>
      <input
        type="password"
        autoComplete="off"
        spellCheck={false}
        placeholder={stored ? 'Enter a new key to replace the stored one' : placeholder}
        value={inputValue}
        onChange={(e) => onInputChange(e.target.value)}
        disabled={disabled}
        className="px-3 py-2 border border-gray-300 rounded-lg w-full font-mono text-sm disabled:bg-gray-100"
      />
    </div>
  )
}
