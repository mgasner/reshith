# Reshith Project Guidelines

## Transliteration Conventions

Use Lambdin's transliteration conventions throughout the project (from *Introduction to Biblical Hebrew*):

### Consonants
- א = ʾ (aleph)
- ב = b / ḇ (bet with/without dagesh)
- ג = g / ḡ (gimel with/without dagesh)
- ד = d / ḏ (dalet with/without dagesh)
- ה = h
- ו = w
- ז = z
- ח = ḥ (het)
- ט = ṭ (tet)
- י = y
- כ/ך = k / ḵ (kap with/without dagesh)
- ל = l
- מ/ם = m
- נ/ן = n
- ס = s (samek)
- ע = ʿ (ayin)
- פ/ף = p / p̄ (peh with/without dagesh)
- צ/ץ = ṣ (tsade)
- ק = q (qoph)
- ר = r
- שׁ = š (shin)
- שׂ = ś (sin)
- ת = t / ṯ (taw with/without dagesh)

### Vowels
- patah = a
- qamets = ā (or o when qamets hatuf)
- hireq = i
- tsere = ē (or ê with mater)
- segol = e
- holem = ō (or ô with mater)
- qibbuts = u
- shureq = û
- shewa = ə (vocal) or omitted (silent)
- hatef patah = ă
- hatef segol = ĕ
- hatef qamets = ŏ

### Letter Names
Use Lambdin's transliterated names:
- ʾalep, bêt, gîmel, dālet, hê, wāw, zayin, ḥêt, ṭêt, yôd, kap, lāmed, mêm, nûn, sāmek, ʿayin, peh, ṣādēh, qôp, rêš, śîn, šîn, tāw

## Frontend Guidelines

- Use Apollo Client with hooks (`useQuery`, `useMutation`) for all GraphQL operations
- Do not use raw `fetch` calls for GraphQL - always use Apollo hooks
- GraphQL operations should be defined in `src/graphql/operations.ts`

## Hebrew Text Display

- Always use `rtl` class and `font-hebrew` for Hebrew text
- Use the HebrewKeyboard component for Hebrew input (no modifier keys required)
