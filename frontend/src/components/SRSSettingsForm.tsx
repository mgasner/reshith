import { ReactNode } from 'react'

export const SRS_DEFAULTS = {
  initialEf: 2.5,
  minimumEf: 1.3,
  graduatingIntervalDays: 1,
  easyIntervalDays: 4,
  hardMultiplier: 1.2,
  easyBonus: 1.3,
  intervalModifier: 1.0,
  maximumIntervalDays: 36500,
  lapseMultiplier: 0.0,
  lapseMinimumIntervalDays: 1,
  newCardsPerDay: 20,
  reviewsPerDay: 200,
}

export type SRSFieldKey = keyof typeof SRS_DEFAULTS

type FieldKind = 'float' | 'int'

interface FieldSpec {
  key: SRSFieldKey
  label: string
  hint?: string
  kind: FieldKind
  min?: number
  max?: number
  step?: number
}

interface Section {
  title: string
  fields: FieldSpec[]
}

export const SRS_SECTIONS: Section[] = [
  {
    title: 'Learning',
    fields: [
      { key: 'initialEf', label: 'Initial ease factor', kind: 'float', step: 0.05 },
      { key: 'minimumEf', label: 'Minimum ease factor', kind: 'float', step: 0.05, min: 1.0 },
      { key: 'graduatingIntervalDays', label: 'Graduating interval (days)', kind: 'int', min: 1 },
      { key: 'easyIntervalDays', label: 'Easy interval (days)', kind: 'int', min: 1 },
    ],
  },
  {
    title: 'Reviews',
    fields: [
      { key: 'hardMultiplier', label: 'Hard multiplier', kind: 'float', step: 0.05 },
      { key: 'easyBonus', label: 'Easy bonus', kind: 'float', step: 0.05 },
      {
        key: 'intervalModifier',
        label: 'Interval modifier',
        kind: 'float',
        step: 0.05,
        hint: 'Global speed knob (1.0 = SM-2 defaults)',
      },
      { key: 'maximumIntervalDays', label: 'Maximum interval (days)', kind: 'int', min: 1 },
    ],
  },
  {
    title: 'Lapses',
    fields: [
      {
        key: 'lapseMultiplier',
        label: 'Lapse multiplier',
        kind: 'float',
        step: 0.05,
        hint: '0 = reset interval to the minimum below',
      },
      { key: 'lapseMinimumIntervalDays', label: 'Lapse minimum interval (days)', kind: 'int', min: 1 },
    ],
  },
  {
    title: 'Daily caps',
    fields: [
      { key: 'newCardsPerDay', label: 'New cards per day', kind: 'int', min: 0 },
      { key: 'reviewsPerDay', label: 'Reviews per day', kind: 'int', min: 0 },
    ],
  },
]

export type SRSFormValues = Partial<Record<SRSFieldKey, number | null>>

export function formatValue(value: number | null | undefined): string {
  return value == null ? '' : String(value)
}

export function parseValue(spec: FieldSpec, raw: string): number | null {
  const trimmed = raw.trim()
  if (trimmed === '') return null
  const num = spec.kind === 'int' ? Number.parseInt(trimmed, 10) : Number.parseFloat(trimmed)
  return Number.isFinite(num) ? num : null
}

interface SRSFieldInputProps {
  spec: FieldSpec
  value: number | null | undefined
  disabled?: boolean
  onChange: (next: number | null) => void
  trailing?: ReactNode
}

export function SRSFieldInput({ spec, value, disabled, onChange, trailing }: SRSFieldInputProps) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-medium text-gray-700">{spec.label}</span>
      <div className="flex items-center gap-2">
        <input
          type="number"
          step={spec.kind === 'float' ? spec.step ?? 0.1 : spec.step}
          min={spec.min}
          max={spec.max}
          value={formatValue(value)}
          disabled={disabled}
          onChange={(e) => onChange(parseValue(spec, e.target.value))}
          className="border rounded px-2 py-1 w-full disabled:bg-gray-100 disabled:text-gray-500"
        />
        {trailing}
      </div>
      {spec.hint && <span className="text-xs text-gray-500">{spec.hint}</span>}
    </label>
  )
}
