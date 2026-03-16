/**
 * hebrewToLambdin — convert pointed Biblical Hebrew (Unicode) to
 * Lambdin-style transliteration.
 *
 * Input: the raw Hebrew field from TAHOT, e.g. "בְּ/רֵאשִׁ֖ית"
 * Output: e.g. "bərēʾšît"
 *
 * Handles:
 *   • All 22 consonants (+ finals), with ḥ ṭ ṣ š ś ʾ ʿ
 *   • Begadkephat spirants (line below): ḇ ḡ ḏ ḵ p̄ ṯ when no dagesh
 *   • Full niqqud: qamets ā, tsere ē, holam ō, patah a, segol e,
 *     hireq i, qubbuts u, hatef ă ĕ ŏ, shewa ə
 *   • Mater lectiones: hireq-yod → î, tsere-yod → ē (skips yod),
 *     holam-waw → ō (skips waw), shureq (waw+dagesh) → û,
 *     holam-waw combining (U+05BA) → ō
 *   • Dagesh forte: doubles consonant when preceded by a vowel
 *   • Dagesh lene: begadkephat consonant is plosive (no doubling)
 *   • Patah furtive: under final ח or ע, emitted before the consonant
 *   • Shin / sin dot distinction
 *
 * Approximations:
 *   • Qamets hatuf (in closed unaccented syllable) not distinguished from
 *     qamets gadol — both rendered ā
 *   • Vocal vs silent shewa: shewa after a vowel is silent; otherwise vocal
 */

// ── Unicode code-point constants ─────────────────────────────────────────────

const SHEWA       = 0x05B0
const HATEF_SEGOL = 0x05B1
const HATEF_PATAH = 0x05B2
const HATEF_QAM   = 0x05B3
const HIREQ       = 0x05B4
const TSERE       = 0x05B5
const SEGOL       = 0x05B6
const PATAH       = 0x05B7
const QAMETS      = 0x05B8
const HOLAM       = 0x05B9
const HOLAM_WAW   = 0x05BA   // holam written on the waw itself
const QUBBUTS     = 0x05BB
const DAGESH      = 0x05BC
const SHIN_DOT    = 0x05C1
const SIN_DOT     = 0x05C2

const WAW   = 0x05D5
const HET   = 0x05D7
const YOD   = 0x05D9
const SHIN  = 0x05E9
const AYIN  = 0x05E2

const CONS_START = 0x05D0
const CONS_END   = 0x05EA

function isCons(cp: number): boolean { return cp >= CONS_START && cp <= CONS_END }
function isVow(cp: number): boolean  { return cp >= SHEWA && cp <= QUBBUTS }

// ── Mapping tables ────────────────────────────────────────────────────────────

// Plosive form (with dagesh lene or forte)
const CONS_MAP: Record<number, string> = {
  0x05D0: 'ʾ',  // aleph
  0x05D1: 'b',  // bet
  0x05D2: 'g',  // gimel
  0x05D3: 'd',  // dalet
  0x05D4: 'h',  // he
  0x05D5: 'w',  // waw
  0x05D6: 'z',  // zayin
  0x05D7: 'ḥ',  // het
  0x05D8: 'ṭ',  // tet
  0x05D9: 'y',  // yod
  0x05DA: 'k',  // final kaf
  0x05DB: 'k',  // kaf
  0x05DC: 'l',  // lamed
  0x05DD: 'm',  // final mem
  0x05DE: 'm',  // mem
  0x05DF: 'n',  // final nun
  0x05E0: 'n',  // nun
  0x05E1: 's',  // samek
  0x05E2: 'ʿ',  // ayin
  0x05E3: 'p',  // final pe
  0x05E4: 'p',  // pe
  0x05E5: 'ṣ',  // final tsadi
  0x05E6: 'ṣ',  // tsadi
  0x05E7: 'q',  // qof
  0x05E8: 'r',  // resh
  0x05E9: 'š',  // shin (overridden to ś for sin)
  0x05EA: 't',  // tav
}

// Spirant form (no dagesh) — Lambdin: line underneath the letter
// ḇ=U+1E07, ḡ=U+1E21, ḏ=U+1E0F, ḵ=U+1E35, ṯ=U+1E6F
// p̄: no precomposed form, use p + combining macron below (U+0331)
const BGDKPT_SPIRANT: Record<number, string> = {
  0x05D1: '\u1E07',        // ב → ḇ
  0x05D2: '\u1E21',        // ג → ḡ
  0x05D3: '\u1E0F',        // ד → ḏ
  0x05DA: '\u1E35',        // ך → ḵ
  0x05DB: '\u1E35',        // כ → ḵ
  0x05E3: 'p\u0332',        // ף → p̲ (p + line below)
  0x05E4: 'p\u0332',        // פ → p̲
  0x05EA: '\u1E6F',        // ת → ṯ
}

const VOW_MAP: Record<number, string> = {
  [SHEWA]:       'ə',
  [HATEF_SEGOL]: 'ĕ',
  [HATEF_PATAH]: 'ă',
  [HATEF_QAM]:   'ŏ',
  [HIREQ]:       'i',
  [TSERE]:       'ē',
  [SEGOL]:       'e',
  [PATAH]:       'a',
  [QAMETS]:      'ā',
  [HOLAM]:       'ō',
  [HOLAM_WAW]:   'ō',
  [QUBBUTS]:     'u',
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** True if the consonant at `pos` has no vowel and no dagesh (= unvoweled mater). */
function isMater(cps: number[], pos: number): boolean {
  for (let k = pos + 1; k < cps.length; k++) {
    if (isCons(cps[k])) break
    if (isVow(cps[k]) || cps[k] === DAGESH) return false
  }
  return true
}

/** Return index of first consonant at or after `pos` (skipping non-consonants). */
function skipToNextCons(cps: number[], pos: number): number {
  while (pos < cps.length && !isCons(cps[pos])) pos++
  return pos
}

// ── Main function ─────────────────────────────────────────────────────────────

export function hebrewToLambdin(input: string): string {
  if (!input) return ''

  // Keep only consonants, niqqud (U+05B0–U+05BB), dagesh (U+05BC),
  // shin/sin dots (U+05C1–U+05C2).  Everything else — cantillation,
  // meteg, maqaf, sof pasuq, solidus separators — is stripped.
  const cps = Array.from(input)
    .map(c => c.codePointAt(0)!)
    .filter(cp =>
      (cp >= SHEWA  && cp <= DAGESH)  ||  // niqqud + dagesh
      cp === SHIN_DOT || cp === SIN_DOT ||
      (cp >= CONS_START && cp <= CONS_END)
    )

  let out = ''
  let i = 0
  let afterVowel = false  // tracks whether previous output ended with a vowel

  while (i < cps.length) {
    const cp = cps[i]
    if (!isCons(cp)) { i++; continue }

    // ── Collect modifiers belonging to this consonant ──────────────────────
    let dagesh = false
    let vowel: number | null = null
    let sinDot = false
    let j = i + 1
    while (j < cps.length && !isCons(cps[j])) {
      const m = cps[j]
      if (m === DAGESH)   dagesh = true
      else if (m === SIN_DOT)  sinDot = true
      else if (m === SHIN_DOT) { /* shin is the default */ }
      else if (isVow(m)) vowel = m
      j++
    }
    // j now points to the next consonant (or end)

    // ── Special: waw ──────────────────────────────────────────────────────
    if (cp === WAW) {
      // Shureq: waw + dagesh, no other vowel
      if (dagesh && vowel === null) {
        out += 'û'; afterVowel = true; i = j; continue
      }
      // Holam-waw combining mark (U+05BA): waw is the vowel carrier, not a consonant
      if (vowel === HOLAM_WAW) {
        out += 'ō'; afterVowel = true; i = j; continue
      }
      // Waw + holam (U+05B9) when the preceding consonant was unvoweled:
      // the waw is a holam-waw mater (vowel carrier), not a consonant.
      // e.g. שָׁלוֹם: lamed (no vowel) + waw + holam → lōm, not lwōm
      if (vowel === HOLAM && !afterVowel) {
        out += 'ō'; afterVowel = true; i = j; continue
      }
    }

    // ── Consonant letter ──────────────────────────────────────────────────
    // Begadkephat: use spirant form when no dagesh, plosive when dagesh present.
    // Dagesh forte (after vowel) → doubled plosive.
    // Dagesh lene (not after vowel) → plosive, no doubling.
    const isBGDKPT = cp in BGDKPT_SPIRANT
    let letter: string
    if (cp === SHIN) {
      letter = sinDot ? 'ś' : 'š'
    } else if (isBGDKPT && !dagesh) {
      letter = BGDKPT_SPIRANT[cp]   // spirant: no dagesh
    } else {
      letter = CONS_MAP[cp] ?? '?'  // plosive: dagesh present, or non-bgdkpt
    }

    // ── Patah furtive ─────────────────────────────────────────────────────
    // Patah under the final ח or ע is pronounced before the consonant.
    if (vowel === PATAH && j >= cps.length && (cp === HET || cp === AYIN)) {
      // These are never bgdkpt, so no spirant/forte concern here
      out += 'a' + letter
      afterVowel = false; i = j; continue
    }

    // ── Dagesh forte: doubled plosive (only when dagesh follows a vowel) ──
    if (dagesh && afterVowel) out += letter + letter
    else out += letter

    // ── Vowel ─────────────────────────────────────────────────────────────
    // Save the pre-reset state: it tells us whether the shewa is vocal or silent.
    const prevAfterVowel = afterVowel
    afterVowel = false

    if (vowel !== null) {
      // Hireq + unvoweled yod → long î
      if (vowel === HIREQ && j < cps.length && cps[j] === YOD && isMater(cps, j)) {
        out += 'î'; afterVowel = true
        i = skipToNextCons(cps, j + 1); continue
      }
      // Tsere + unvoweled yod → ē (yod is just a mater confirming length)
      if (vowel === TSERE && j < cps.length && cps[j] === YOD && isMater(cps, j)) {
        out += 'ē'; afterVowel = true
        i = skipToNextCons(cps, j + 1); continue
      }
      // Holam + unvoweled waw → ō
      if (vowel === HOLAM && j < cps.length && cps[j] === WAW && isMater(cps, j)) {
        out += 'ō'; afterVowel = true
        i = skipToNextCons(cps, j + 1); continue
      }
      // Shewa: vocal when the preceding syllable was open (prevAfterVowel=false),
      // silent when it follows a vowel (prevAfterVowel=true).
      // When silent, afterVowel stays false so the next dagesh is treated as lene.
      if (vowel === SHEWA) {
        if (!prevAfterVowel) { out += 'ə'; afterVowel = true }
        // else: silent — afterVowel remains false
      } else {
        out += VOW_MAP[vowel] ?? ''
        afterVowel = true
      }
    }

    i = j
  }

  return out
}
