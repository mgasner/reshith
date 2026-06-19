import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery } from '@apollo/client'
import { useAuth } from '@/contexts/AuthContext'
import {
  GET_DECK_SRS_SETTINGS,
  GET_EFFECTIVE_SRS_CONFIG,
  UPDATE_DECK_SRS_SETTINGS,
} from '@/graphql/operations'
import {
  SRS_SECTIONS,
  SRSFieldInput,
  SRSFieldKey,
  SRSFormValues,
} from '@/components/SRSSettingsForm'

export function DeckSettingsPage() {
  const { deckId } = useParams<{ deckId: string }>()
  const { user } = useAuth()

  const deckSettings = useQuery<{ deckSrsSettings: SRSFormValues }>(GET_DECK_SRS_SETTINGS, {
    variables: { deckId },
    skip: !user || !deckId,
    fetchPolicy: 'cache-and-network',
  })
  const effective = useQuery<{ effectiveSrsConfig: SRSFormValues }>(GET_EFFECTIVE_SRS_CONFIG, {
    variables: { deckId },
    skip: !user || !deckId,
    fetchPolicy: 'cache-and-network',
  })

  const [updateDeck, { loading: saving }] = useMutation(UPDATE_DECK_SRS_SETTINGS)

  const [overrides, setOverrides] = useState<SRSFormValues>({})
  const [status, setStatus] = useState<string | null>(null)

  useEffect(() => {
    if (deckSettings.data?.deckSrsSettings) {
      const next: SRSFormValues = {}
      for (const [k, v] of Object.entries(deckSettings.data.deckSrsSettings)) {
        if (k === 'deckId' || k === '__typename') continue
        next[k as SRSFieldKey] = v as number | null
      }
      setOverrides(next)
    }
  }, [deckSettings.data])

  if (!user) {
    return (
      <div className="px-4 text-center py-12 text-gray-600">
        <p>You need to log in to manage deck settings.</p>
      </div>
    )
  }
  if (!deckId) return <div className="px-4">Missing deck id.</div>

  if (deckSettings.loading && !deckSettings.data) {
    return <div className="px-4 text-gray-500">Loading…</div>
  }

  const effectiveValues = effective.data?.effectiveSrsConfig

  const handleSave = async () => {
    setStatus(null)
    await updateDeck({ variables: { input: { deckId, ...overrides } } })
    await Promise.all([deckSettings.refetch(), effective.refetch()])
    setStatus('Saved')
  }

  const isInheriting = (key: SRSFieldKey) => overrides[key] == null

  const toggleInherit = (key: SRSFieldKey) => {
    setOverrides((prev) => {
      const next = { ...prev }
      if (isInheriting(key)) {
        // Reveal: seed with current effective value.
        next[key] = effectiveValues?.[key] ?? null
      } else {
        next[key] = null
      }
      return next
    })
  }

  return (
    <div className="px-4 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Deck SRS Settings</h1>
        <Link to="/decks" className="text-sm text-blue-600 hover:underline">
          ← Back to decks
        </Link>
      </div>
      <p className="text-sm text-gray-600 mb-6">
        Uncheck "Inherit" to override a setting just for this deck. Inherited
        fields fall back to your global settings.
      </p>

      {SRS_SECTIONS.map((section) => (
        <section key={section.title} className="mb-8">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">{section.title}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {section.fields.map((spec) => {
              const key = spec.key as SRSFieldKey
              const inheriting = isInheriting(key)
              return (
                <SRSFieldInput
                  key={spec.key}
                  spec={spec}
                  value={inheriting ? effectiveValues?.[key] ?? null : overrides[key]}
                  disabled={inheriting}
                  onChange={(next) => setOverrides((prev) => ({ ...prev, [key]: next }))}
                  trailing={
                    <label className="text-xs text-gray-500 flex items-center gap-1 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={inheriting}
                        onChange={() => toggleInherit(key)}
                      />
                      Inherit
                    </label>
                  }
                />
              )
            })}
          </div>
        </section>
      ))}

      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save overrides'}
        </button>
        {status && <span className="text-sm text-green-700">{status}</span>}
      </div>
    </div>
  )
}
