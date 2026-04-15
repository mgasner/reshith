import { useState } from 'react'
import { useQuery, useMutation } from '@apollo/client'
import { GET_QAL_PARADIGM, GET_QAL_WORKSHEET, GRADE_QAL_WORKSHEET } from '@/graphql/operations'

interface ParadigmForm {
  conjugation: string
  person: string
  number: string
  gender: string
  label: string
  hebrew: string
  transliteration: string
}

interface Paradigm {
  root: string
  rootTransliteration: string
  citation: string
  citationTransliteration: string
  definition: string
  availableRoots: string[]
  forms: ParadigmForm[]
}

interface WorksheetForm extends ParadigmForm {
  answerHebrew: string
  answerTransliteration: string
  isBlank: boolean
}

interface Worksheet {
  root: string
  rootTransliteration: string
  citation: string
  citationTransliteration: string
  definition: string
  numBlanks: number
  forms: WorksheetForm[]
}

interface GradeItem {
  index: number
  label: string
  correct: boolean
  expected: string
  submitted: string
  feedback: string
}

const CONJUGATION_SECTIONS = [
  { key: 'perfect', label: 'Perfect (Suffix Conjugation)' },
  { key: 'imperfect', label: 'Imperfect (Prefix Conjugation)' },
  { key: 'imperative', label: 'Imperative' },
  { key: 'inf_construct', label: 'Infinitive Construct' },
  { key: 'inf_absolute', label: 'Infinitive Absolute' },
  { key: 'ptc_active', label: 'Active Participle' },
  { key: 'ptc_passive', label: 'Passive Participle' },
]

function ParadigmTable({ forms }: { forms: ParadigmForm[] }) {
  return (
    <div className="space-y-6">
      {CONJUGATION_SECTIONS.map(({ key, label }) => {
        const sectionForms = forms.filter((f) => f.conjugation === key)
        if (sectionForms.length === 0) return null
        return (
          <div key={key}>
            <h3 className="text-lg font-semibold text-gray-800 mb-2 border-b pb-1">{label}</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500">
                  <th className="py-1 pr-4 w-1/4">Form</th>
                  <th className="py-1 pr-4 w-1/3 text-right" dir="rtl">Hebrew</th>
                  <th className="py-1 w-1/3">Transliteration</th>
                </tr>
              </thead>
              <tbody>
                {sectionForms.map((form, i) => (
                  <tr key={i} className="border-t border-gray-100">
                    <td className="py-2 pr-4 text-gray-600">{form.label}</td>
                    <td className="py-2 pr-4 text-right text-xl font-serif" dir="rtl">
                      {form.hebrew}
                    </td>
                    <td className="py-2 text-gray-700 italic">{form.transliteration}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      })}
    </div>
  )
}

function WorksheetTable({
  forms,
  answers,
  setAnswer,
  gradeResults,
  submitted,
}: {
  forms: WorksheetForm[]
  answers: Record<number, string>
  setAnswer: (index: number, value: string) => void
  gradeResults: GradeItem[] | null
  submitted: boolean
}) {
  const gradeMap = new Map<number, GradeItem>()
  if (gradeResults) {
    for (const item of gradeResults) {
      gradeMap.set(item.index, item)
    }
  }

  return (
    <div className="space-y-6">
      {CONJUGATION_SECTIONS.map(({ key, label }) => {
        const sectionForms: { form: WorksheetForm; idx: number }[] = []
        // We need the global index, so iterate all forms to track it
        let tempIdx = -1
        for (const form of forms) {
          tempIdx++
          if (form.conjugation === key) {
            sectionForms.push({ form, idx: tempIdx })
          }
        }
        if (sectionForms.length === 0) return null

        return (
          <div key={key}>
            <h3 className="text-lg font-semibold text-gray-800 mb-2 border-b pb-1">{label}</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500">
                  <th className="py-1 pr-4 w-1/4">Form</th>
                  <th className="py-1 pr-4 w-1/3 text-right">Hebrew</th>
                  <th className="py-1 w-1/3">Transliteration</th>
                </tr>
              </thead>
              <tbody>
                {sectionForms.map(({ form, idx }) => {
                  const grade = gradeMap.get(idx)
                  return (
                    <tr key={idx} className="border-t border-gray-100">
                      <td className="py-2 pr-4 text-gray-600">{form.label}</td>
                      <td className="py-2 pr-4 text-right" dir="rtl">
                        {form.isBlank ? (
                          <div className="relative">
                            <input
                              type="text"
                              dir="rtl"
                              value={answers[idx] || ''}
                              onChange={(e) => setAnswer(idx, e.target.value)}
                              disabled={submitted}
                              className={`w-full p-1.5 text-xl font-serif border rounded text-right ${
                                grade
                                  ? grade.correct
                                    ? 'border-green-500 bg-green-50'
                                    : 'border-red-500 bg-red-50'
                                  : 'border-gray-300 focus:border-blue-500'
                              } focus:outline-none`}
                              placeholder="..."
                            />
                            {grade && !grade.correct && (
                              <p className="text-xs text-red-600 mt-0.5 text-left">
                                {grade.expected} ({form.answerTransliteration})
                              </p>
                            )}
                          </div>
                        ) : (
                          <span className="text-xl font-serif">{form.hebrew}</span>
                        )}
                      </td>
                      <td className="py-2 text-gray-700 italic">
                        {form.isBlank ? (
                          submitted && grade ? (
                            <span
                              className={grade.correct ? 'text-green-700' : 'text-red-500 line-through'}
                            >
                              {form.answerTransliteration}
                            </span>
                          ) : (
                            <span className="text-gray-300">?</span>
                          )
                        ) : (
                          form.transliteration
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )
      })}
    </div>
  )
}

export function QalParadigmPage() {
  const [mode, setMode] = useState<'paradigm' | 'worksheet'>('paradigm')
  const [selectedRoot, setSelectedRoot] = useState<string | undefined>(undefined)
  const [numBlanks, setNumBlanks] = useState(10)
  const [worksheetAnswers, setWorksheetAnswers] = useState<Record<number, string>>({})
  const [worksheetSubmitted, setWorksheetSubmitted] = useState(false)
  const [gradeResults, setGradeResults] = useState<GradeItem[] | null>(null)
  const [conjugationFilter, setConjugationFilter] = useState<string[]>([])

  const {
    data: paradigmData,
    loading: paradigmLoading,
  } = useQuery(GET_QAL_PARADIGM, {
    variables: { root: selectedRoot || null },
    skip: mode !== 'paradigm',
    fetchPolicy: 'network-only',
  })

  const {
    data: worksheetData,
    loading: worksheetLoading,
    refetch: refetchWorksheet,
  } = useQuery(GET_QAL_WORKSHEET, {
    variables: {
      numBlanks,
      root: selectedRoot || null,
      conjugations: conjugationFilter.length > 0 ? conjugationFilter : null,
    },
    skip: mode !== 'worksheet',
    fetchPolicy: 'network-only',
  })

  const [gradeWorksheet] = useMutation(GRADE_QAL_WORKSHEET)

  const paradigm: Paradigm | null = paradigmData?.qalParadigm || null
  const worksheet: Worksheet | null = worksheetData?.qalWorksheet || null

  // Get available roots from whichever query has loaded
  const rootOptions = paradigm?.availableRoots || []

  const handleNewWorksheet = () => {
    setWorksheetAnswers({})
    setWorksheetSubmitted(false)
    setGradeResults(null)
    refetchWorksheet()
  }

  const handleSubmitWorksheet = async () => {
    if (!worksheet) return
    const answers = Object.entries(worksheetAnswers)
      .filter(([_, v]) => v.trim() !== '')
      .map(([idx, submitted]) => ({ index: parseInt(idx), submitted }))

    try {
      const result = await gradeWorksheet({
        variables: {
          input: {
            root: worksheet.root,
            answers,
          },
        },
      })
      const gradeResult = result.data?.gradeQalWorksheet
      if (gradeResult) {
        setGradeResults(gradeResult.items)
        setWorksheetSubmitted(true)
      }
    } catch (error) {
      console.error('Failed to grade worksheet:', error)
    }
  }

  const loading = mode === 'paradigm' ? paradigmLoading : worksheetLoading
  const activeData = mode === 'paradigm' ? paradigm : worksheet

  return (
    <div className="px-4 max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Qal Verb Paradigms</h1>
        <p className="text-gray-600">
          Study complete Qal paradigm tables or test yourself with fill-in worksheets.
        </p>
      </div>

      {/* Controls */}
      <div className="mb-6 flex flex-wrap gap-4 items-end">
        {/* Mode toggle */}
        <div>
          <label className="block text-sm text-gray-600 mb-1">Mode</label>
          <div className="flex rounded-lg overflow-hidden border border-gray-300">
            <button
              onClick={() => setMode('paradigm')}
              className={`px-4 py-2 text-sm font-medium ${
                mode === 'paradigm'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              Full Paradigm
            </button>
            <button
              onClick={() => {
                setMode('worksheet')
                setWorksheetAnswers({})
                setWorksheetSubmitted(false)
                setGradeResults(null)
              }}
              className={`px-4 py-2 text-sm font-medium border-l ${
                mode === 'worksheet'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              Worksheet
            </button>
          </div>
        </div>

        {/* Verb selector */}
        {rootOptions.length > 0 && (
          <div>
            <label className="block text-sm text-gray-600 mb-1">Verb Root</label>
            <select
              value={selectedRoot || ''}
              onChange={(e) => {
                setSelectedRoot(e.target.value || undefined)
                setWorksheetAnswers({})
                setWorksheetSubmitted(false)
                setGradeResults(null)
              }}
              className="px-3 py-2 border rounded-lg"
            >
              <option value="">Random</option>
              {rootOptions.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Worksheet-specific controls */}
        {mode === 'worksheet' && (
          <>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Blanks</label>
              <select
                value={numBlanks}
                onChange={(e) => {
                  setNumBlanks(Number(e.target.value))
                  setWorksheetAnswers({})
                  setWorksheetSubmitted(false)
                  setGradeResults(null)
                }}
                className="px-3 py-2 border rounded-lg"
              >
                {[5, 10, 15, 20, 30].map((n) => (
                  <option key={n} value={n}>
                    {n} blanks
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">Focus</label>
              <select
                value={conjugationFilter.length === 0 ? 'all' : conjugationFilter.join(',')}
                onChange={(e) => {
                  const val = e.target.value
                  setConjugationFilter(val === 'all' ? [] : val.split(','))
                  setWorksheetAnswers({})
                  setWorksheetSubmitted(false)
                  setGradeResults(null)
                }}
                className="px-3 py-2 border rounded-lg"
              >
                <option value="all">All conjugations</option>
                <option value="perfect">Perfect only</option>
                <option value="imperfect">Imperfect only</option>
                <option value="perfect,imperfect">Perfect + Imperfect</option>
                <option value="imperative">Imperative only</option>
                <option value="ptc_active,ptc_passive">Participles only</option>
              </select>
            </div>

            <button
              onClick={handleNewWorksheet}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              New Worksheet
            </button>
          </>
        )}
      </div>

      {loading && (
        <div className="text-center py-12">
          <p className="text-gray-500">Loading...</p>
        </div>
      )}

      {!loading && !activeData && (
        <div className="text-center py-12">
          <p className="text-gray-500">No paradigm data available.</p>
        </div>
      )}

      {/* Paradigm view */}
      {!loading && mode === 'paradigm' && paradigm && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="text-center mb-6">
            <p className="text-3xl font-serif" dir="rtl">
              {paradigm.citation}
            </p>
            <p className="text-lg text-gray-600 italic mt-1">
              {paradigm.citationTransliteration}
            </p>
            <p className="text-gray-500 mt-1">{paradigm.definition}</p>
            <p className="text-sm text-gray-400 mt-1">
              Root: {paradigm.rootTransliteration}
            </p>
          </div>
          <ParadigmTable forms={paradigm.forms} />
        </div>
      )}

      {/* Worksheet view */}
      {!loading && mode === 'worksheet' && worksheet && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="text-center mb-6">
            <p className="text-3xl font-serif" dir="rtl">
              {worksheet.citation}
            </p>
            <p className="text-lg text-gray-600 italic mt-1">
              {worksheet.citationTransliteration}
            </p>
            <p className="text-gray-500 mt-1">{worksheet.definition}</p>
            <p className="text-sm text-gray-400 mt-1">
              Fill in the {worksheet.numBlanks} missing forms
            </p>
          </div>

          <WorksheetTable
            forms={worksheet.forms}
            answers={worksheetAnswers}
            setAnswer={(idx, val) =>
              setWorksheetAnswers((prev) => ({ ...prev, [idx]: val }))
            }
            gradeResults={gradeResults}
            submitted={worksheetSubmitted}
          />

          <div className="mt-6 flex justify-center gap-4">
            {!worksheetSubmitted ? (
              <button
                onClick={handleSubmitWorksheet}
                disabled={Object.keys(worksheetAnswers).length === 0}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Check Answers
              </button>
            ) : (
              <>
                {gradeResults && (
                  <div className="text-center">
                    <p className="text-lg font-medium mb-3">
                      {gradeResults.filter((g) => g.correct).length} / {gradeResults.length} correct
                      {' '}
                      ({gradeResults.length > 0
                        ? Math.round(
                            (gradeResults.filter((g) => g.correct).length / gradeResults.length) *
                              100
                          )
                        : 0}
                      %)
                    </p>
                  </div>
                )}
                <button
                  onClick={handleNewWorksheet}
                  className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  New Worksheet
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
