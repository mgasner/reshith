import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@apollo/client'
import { useAuth } from '@/contexts/AuthContext'
import {
  GET_USER_SRS_SETTINGS,
  UPDATE_USER_SRS_SETTINGS,
} from '@/graphql/operations'
import {
  SRS_DEFAULTS,
  SRS_SECTIONS,
  SRSFieldInput,
  SRSFieldKey,
  SRSFormValues,
} from '@/components/SRSSettingsForm'
import { APIKeysSection } from '@/components/APIKeysSection'

export function SettingsPage() {
  const { user } = useAuth()
  const { data, loading, error, refetch } = useQuery<{ userSrsSettings: SRSFormValues }>(
    GET_USER_SRS_SETTINGS,
    { skip: !user, fetchPolicy: 'cache-and-network' }
  )
  const [updateSettings, { loading: saving }] = useMutation(UPDATE_USER_SRS_SETTINGS)
  const [form, setForm] = useState<SRSFormValues>({})
  const [status, setStatus] = useState<string | null>(null)

  useEffect(() => {
    if (data?.userSrsSettings) {
      // Apollo adds `__typename` to query results; Strawberry rejects it as
      // an unknown field on the input type, so strip it here before it ever
      // hits `form` state.
      const next: SRSFormValues = {}
      for (const [k, v] of Object.entries(data.userSrsSettings)) {
        if (k === '__typename') continue
        next[k as SRSFieldKey] = v as number | null
      }
      setForm(next)
    }
  }, [data])

  if (!user) {
    return (
      <div className="px-4 text-center py-12 text-gray-600">
        <p>You need to log in to view your settings.</p>
      </div>
    )
  }

  if (loading && !data) return <div className="px-4 text-gray-500">Loading settings…</div>
  if (error) return <div className="px-4 text-red-600">Failed to load: {error.message}</div>

  const handleSave = async () => {
    setStatus(null)
    await updateSettings({ variables: { input: form } })
    await refetch()
    setStatus('Saved')
  }

  const handleReset = async () => {
    setStatus(null)
    await updateSettings({ variables: { input: SRS_DEFAULTS } })
    await refetch()
    setStatus('Reset to defaults')
  }

  return (
    <div className="px-4 max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      <APIKeysSection />

      <h2 className="text-2xl font-bold text-gray-900 mb-2 mt-10">SRS</h2>
      <p className="text-sm text-gray-600 mb-6">
        Anki-style parameters applied to every deck that doesn't override them.
        Daily caps reset at <strong>UTC midnight</strong>.
      </p>

      {SRS_SECTIONS.map((section) => (
        <section key={section.title} className="mb-8">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">{section.title}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {section.fields.map((spec) => (
              <SRSFieldInput
                key={spec.key}
                spec={spec}
                value={form[spec.key as SRSFieldKey]}
                onChange={(next) => setForm((prev) => ({ ...prev, [spec.key]: next }))}
              />
            ))}
          </div>
        </section>
      ))}

      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save'}
        </button>
        <button
          onClick={handleReset}
          disabled={saving}
          className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 disabled:opacity-50"
        >
          Reset to defaults
        </button>
        {status && <span className="text-sm text-green-700">{status}</span>}
      </div>
    </div>
  )
}
