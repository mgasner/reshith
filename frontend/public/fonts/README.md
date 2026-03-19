# Fonts

## Gveret Levin (GveretLevinAlefAlefAlef-Regular.woff2 / .woff)

Hebrew handwritten script font by Alef Alef Alef. Described as "the new Guttman-Hand" — based on
the flowing handwriting of Gili Levin. Free for print, app, and web use.

Source: https://alefalefalef.co.il/en/resources/פונטים-בחינם/

Used for the handwriting toggle on alphabet flashcards (`font-hebrew-script` Tailwind class).

## SBL Hebrew (SBL_Hbrw.woff2 / .ttf)

Gold-standard font for Biblical Hebrew. Designed by John Hudson (Tiro Typeworks) for the Society
of Biblical Literature. Full support for Tiberian vowel signs (nikud) and cantillation marks
(te'amim/trope) with proper glyph positioning and stacking.

License: Free for non-commercial use. © John Hudson, Tiro Typeworks, 2003 & 2007.
Source: https://www.sbl-site.org/educational/biblicalfonts.aspx

Used as the primary `font-hebrew` and `.hebrew-text` font throughout the app, with Noto Serif
Hebrew (Google Fonts) as the web fallback.

## NachlieliCLM-Light.otf

OTF fallback from the [Culmus project](https://culmus.sourceforge.io/). Used if the woff2/woff
files above fail to load.
