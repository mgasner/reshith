const RTL_LANGUAGES = new Set(['hbo', 'arc', 'heb'])

const LANGUAGE_FONTS: Record<string, string> = {
  hbo: 'hebrew-text',
  arc: 'hebrew-text',
  heb: 'hebrew-text',
  grc: 'greek-text',
  san: 'sanskrit-text',
  pli: 'sanskrit-text',
  bhs: 'sanskrit-text',
}

export function useLanguage(languageCode: string) {
  const isRtl = RTL_LANGUAGES.has(languageCode)
  const fontClass = LANGUAGE_FONTS[languageCode] || ''

  return {
    isRtl,
    fontClass,
    directionClass: isRtl ? 'rtl' : 'ltr',
  }
}
