import { useState, useEffect, useRef } from 'react'
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useApolloClient, useQuery } from '@apollo/client'
import { useAuth } from '@/contexts/AuthContext'
import { GET_MY_PROGRESS } from '@/graphql/operations'

const LANGUAGES = [
  {
    code: 'hbo',
    label: 'א',
    name: 'Hebrew',
    lessons: [
      { num: '01', name: 'Lesson 1' },
      { num: '02', name: 'Lesson 2' },
      { num: '03', name: 'Lesson 3' },
      { num: '04', name: 'Lesson 4' },
      { num: '05', name: 'Lesson 5' },
    ],
    lessonPath: (num: string) => `/hebrew/lesson/${num}`,
    homePath: '/',
    studyPath: '/hebrew/study',
    alphabetPath: '/hebrew/alphabet',
    vowelsPath: '/hebrew/vowels',
    babylonianVowelsPath: '/hebrew/babylonian-vowels',
    exercisesPath: '/exercises/hebrew',
    resourcesPath: '/hebrew/tahot',
    hasAlphabet: true,
    hasVowels: true,
  },
  {
    code: 'lat',
    label: 'L',
    name: 'Latin',
    lessons: [
      { num: '01', name: 'Lesson 1' },
      { num: '02', name: 'Lesson 2' },
      { num: '03', name: 'Lesson 3' },
    ],
    lessonPath: (num: string) => `/latin/lesson/${num}`,
    homePath: '/latin',
    studyPath: '/latin/study',
    alphabetPath: null,
    vowelsPath: null,
    babylonianVowelsPath: null,
    exercisesPath: '/exercises/latin',
    resourcesPath: null,
    hasAlphabet: false,
    hasVowels: false,
  },
  {
    code: 'grc',
    label: 'ε',
    name: 'Ancient Greek',
    lessons: [
      { num: '1', name: 'Lesson 1' },
      { num: '2', name: 'Lesson 2' },
      { num: '3', name: 'Lesson 3' },
    ],
    lessonPath: (num: string) => `/greek/lesson/${num}`,
    homePath: '/greek',
    studyPath: '/greek/study',
    alphabetPath: null,
    vowelsPath: null,
    babylonianVowelsPath: null,
    exercisesPath: '/exercises/greek',
    resourcesPath: null,
    hasAlphabet: false,
    hasVowels: false,
  },
  {
    code: 'gnt',
    label: 'κ',
    name: 'NT Greek',
    lessons: [
      { num: '1', name: 'Lesson 1' },
      { num: '2', name: 'Lesson 2' },
      { num: '3', name: 'Lesson 3' },
    ],
    lessonPath: (num: string) => `/nt-greek/lesson/${num}`,
    homePath: '/nt-greek',
    studyPath: '/nt-greek/study',
    alphabetPath: null,
    vowelsPath: null,
    babylonianVowelsPath: null,
    exercisesPath: '/exercises/nt-greek',
    resourcesPath: null,
    hasAlphabet: false,
    hasVowels: false,
  },
  {
    code: 'san',
    label: 'अ',
    name: 'Sanskrit',
    lessons: [
      { num: '1', name: 'Lesson 1' },
      { num: '2', name: 'Lesson 2' },
      { num: '3', name: 'Lesson 3' },
    ],
    lessonPath: (num: string) => `/sanskrit/lesson/${num}`,
    homePath: '/sanskrit',
    studyPath: '/sanskrit/study',
    alphabetPath: null,
    vowelsPath: null,
    babylonianVowelsPath: null,
    exercisesPath: '/exercises/sanskrit',
    resourcesPath: null,
    hasAlphabet: false,
    hasVowels: false,
  },
  {
    code: 'ang',
    label: 'ƿ',
    name: 'Old English',
    lessons: [{ num: '1', name: 'Lesson 1' }],
    lessonPath: (num: string) => `/old-english/lesson/${num}`,
    homePath: '/old-english',
    studyPath: null,
    alphabetPath: null,
    vowelsPath: null,
    babylonianVowelsPath: null,
    exercisesPath: '/old-english',
    resourcesPath: '/old-english/beowulf',
    hasAlphabet: false,
    hasVowels: false,
  },
  {
    code: 'ecl',
    label: 'V',
    name: 'Eccl. Latin',
    lessons: [
      { num: '1', name: 'Lesson 1' },
      { num: '2', name: 'Lesson 2' },
      { num: '3', name: 'Lesson 3' },
    ],
    lessonPath: (num: string) => `/ecclesiastical-latin/lesson/${num}`,
    homePath: '/ecclesiastical-latin',
    studyPath: '/ecclesiastical-latin/study',
    alphabetPath: null,
    vowelsPath: null,
    babylonianVowelsPath: null,
    exercisesPath: '/exercises/ecclesiastical-latin',
    resourcesPath: null,
    hasAlphabet: false,
    hasVowels: false,
  },
]

// Map GraphQL LanguageCode enum values back to the navbar's lang codes so
// the per-language progress indicator can route into the right home page.
const GQL_TO_LANG_CODE: Record<string, string> = {
  BIBLICAL_HEBREW: 'hbo',
  LATIN: 'lat',
  ECCLESIASTICAL_LATIN: 'ecl',
  ANCIENT_GREEK: 'grc',
  NT_GREEK: 'gnt',
  SANSKRIT: 'san',
}

interface ProgressRow {
  language: string
  currentLesson: number
  totalLessons: number
  dueCount: number
  isReadyToAdvance: boolean
}

export function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const apollo = useApolloClient()
  const { user, logout } = useAuth()
  const [lessonsOpen, setLessonsOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const mobileMenuRef = useRef<HTMLDivElement>(null)
  const { data: progressData } = useQuery(GET_MY_PROGRESS, { skip: !user })
  const progressRows: ProgressRow[] = progressData?.myProgress ?? []

  useEffect(() => {
    setMobileMenuOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (!mobileMenuOpen) return
    const handleClickOutside = (e: MouseEvent) => {
      if (mobileMenuRef.current && !mobileMenuRef.current.contains(e.target as Node)) {
        setMobileMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [mobileMenuOpen])

  const handleLogout = async () => {
    logout()
    await apollo.resetStore()
    navigate('/login', { replace: true })
  }

  const getActiveLang = () => {
    if (
      location.pathname.startsWith('/latin') ||
      location.pathname.startsWith('/exercises/latin')
    ) {
      return LANGUAGES.find((l) => l.code === 'lat')!
    }
    if (
      location.pathname.startsWith('/greek') ||
      location.pathname.startsWith('/exercises/greek')
    ) {
      return LANGUAGES.find((l) => l.code === 'grc')!
    }
    if (
      location.pathname.startsWith('/nt-greek') ||
      location.pathname.startsWith('/exercises/nt-greek')
    ) {
      return LANGUAGES.find((l) => l.code === 'gnt')!
    }
    if (
      location.pathname.startsWith('/sanskrit') ||
      location.pathname.startsWith('/exercises/sanskrit')
    ) {
      return LANGUAGES.find((l) => l.code === 'san')!
    }
    if (
      location.pathname.startsWith('/ecclesiastical-latin') ||
      location.pathname.startsWith('/exercises/ecclesiastical-latin')
    ) {
      return LANGUAGES.find((l) => l.code === 'ecl')!
    }
    if (location.pathname.startsWith('/old-english')) {
      return LANGUAGES.find((l) => l.code === 'ang')!
    }
    return LANGUAGES.find((l) => l.code === 'hbo')!
  }
  const activeLang = getActiveLang()

  const handleLangSwitch = (lang: typeof LANGUAGES[0]) => {
    if (lang.code !== activeLang.code) {
      navigate(lang.homePath)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar: language picker */}
      <div className="bg-gray-900 text-gray-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-9 gap-1">
            <span className="text-xs uppercase tracking-widest text-gray-500 mr-2">Language</span>
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLangSwitch(lang)}
                className={`flex items-center gap-1.5 px-3 py-0.5 rounded text-sm font-medium transition-colors ${
                  activeLang.code === lang.code
                    ? 'bg-gray-700 text-white'
                    : 'hover:bg-gray-800 hover:text-white'
                }`}
              >
                <span className="text-base leading-none">{lang.label}</span>
                <span className="hidden sm:inline">{lang.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Second bar: main nav */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-8">
            <Link to={activeLang.homePath} className="flex-shrink-0">
              <span className="text-xl font-semibold text-gray-900">Reshith</span>
            </Link>
            <div className="hidden sm:flex sm:items-center sm:gap-6 flex-1">
              {activeLang.hasAlphabet && activeLang.alphabetPath && (
                <Link
                  to={activeLang.alphabetPath}
                  className="text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Alphabet
                </Link>
              )}
              {activeLang.hasVowels && activeLang.vowelsPath && (
                <Link
                  to={activeLang.vowelsPath}
                  className="text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Vowels
                </Link>
              )}
              {activeLang.babylonianVowelsPath && (
                <Link
                  to={activeLang.babylonianVowelsPath}
                  className="text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Babylonian Vowels
                </Link>
              )}
              {user && activeLang.studyPath && (
                <Link
                  to={activeLang.studyPath}
                  className="text-sm font-medium text-blue-700 hover:text-blue-900"
                >
                  Study
                </Link>
              )}
              <Link
                to={activeLang.exercisesPath}
                className="text-sm font-medium text-gray-500 hover:text-gray-900"
              >
                Exercises
              </Link>
              <div className="relative">
                <button
                  onClick={() => setLessonsOpen(!lessonsOpen)}
                  className="flex items-center gap-1 text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Lessons
                  <svg
                    className={`h-4 w-4 transition-transform ${lessonsOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {lessonsOpen && (
                  <div className="absolute left-0 mt-2 w-40 bg-white rounded-md shadow-lg py-1 z-10">
                    {activeLang.lessons.map((lesson) => (
                      <Link
                        key={lesson.num}
                        to={activeLang.lessonPath(lesson.num)}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        onClick={() => setLessonsOpen(false)}
                      >
                        {lesson.name}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
              {activeLang.resourcesPath && (
                <Link
                  to={activeLang.resourcesPath}
                  className="text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Resources
                </Link>
              )}
              <Link
                to="/decks"
                className="text-sm font-medium text-gray-500 hover:text-gray-900"
              >
                Decks
              </Link>
              {user && (
                <>
                  <Link
                    to="/study"
                    className="text-sm font-medium text-gray-500 hover:text-gray-900"
                  >
                    Study
                  </Link>
                  <Link
                    to="/settings"
                    className="text-sm font-medium text-gray-500 hover:text-gray-900"
                  >
                    Settings
                  </Link>
                </>
              )}
            </div>
            </div>
            <div className="hidden sm:flex sm:items-center sm:gap-3 ml-auto">
              {user ? (
                <>
                  <span className="text-sm text-gray-600">
                    {user.displayName || user.username}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="text-sm font-medium text-gray-500 hover:text-gray-900"
                  >
                    Log out
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="text-sm font-medium text-gray-500 hover:text-gray-900"
                  >
                    Log in
                  </Link>
                  <Link
                    to="/register"
                    className="text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded"
                  >
                    Sign up
                  </Link>
                </>
              )}
            </div>
            <button
              className="sm:hidden p-2 rounded-md text-gray-500 hover:text-gray-900 hover:bg-gray-100"
              onClick={() => setMobileMenuOpen((v) => !v)}
              aria-label="Toggle menu"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
        {mobileMenuOpen && (
          <div ref={mobileMenuRef} className="sm:hidden border-t bg-white px-4 py-3 space-y-2">
            {activeLang.hasAlphabet && activeLang.alphabetPath && (
              <Link to={activeLang.alphabetPath} className="block py-2 text-sm font-medium text-gray-700 hover:text-gray-900">Alphabet</Link>
            )}
            {activeLang.hasVowels && activeLang.vowelsPath && (
              <Link to={activeLang.vowelsPath} className="block py-2 text-sm font-medium text-gray-700 hover:text-gray-900">Vowels</Link>
            )}
            <Link to={activeLang.exercisesPath} className="block py-2 text-sm font-medium text-gray-700 hover:text-gray-900">Exercises</Link>
            <div className="py-2">
              <span className="text-sm font-medium text-gray-700">Lessons</span>
              <div className="mt-1 ml-3 space-y-1">
                {activeLang.lessons.map((lesson) => (
                  <Link key={lesson.num} to={activeLang.lessonPath(lesson.num)} className="block py-1 text-sm text-gray-500 hover:text-gray-900">{lesson.name}</Link>
                ))}
              </div>
            </div>
            {activeLang.resourcesPath && (
              <Link to={activeLang.resourcesPath} className="block py-2 text-sm font-medium text-gray-700 hover:text-gray-900">Resources</Link>
            )}
            <Link to="/decks" className="block py-2 text-sm font-medium text-gray-700 hover:text-gray-900">Decks</Link>
          </div>
        )}
      </nav>

      {user && progressRows.length > 0 && (
        <div className="bg-blue-50 border-b border-blue-100">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-1.5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-blue-900">
            {progressRows.map((row) => {
              const code = GQL_TO_LANG_CODE[row.language]
              const lang = LANGUAGES.find((l) => l.code === code)
              if (!lang) return null
              return (
                <Link
                  key={row.language}
                  to={lang.homePath}
                  className="inline-flex items-center gap-1 hover:underline"
                  title={`Lesson ${row.currentLesson} of ${row.totalLessons}`}
                >
                  <span className="font-medium">{lang.name}</span>
                  <span className="text-blue-700">· L{row.currentLesson}</span>
                  {row.dueCount > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 rounded-full bg-blue-600 text-white text-[10px] leading-none">
                      {row.dueCount} due
                    </span>
                  )}
                  {row.isReadyToAdvance && (
                    <span className="ml-1 text-green-700 font-semibold">↑ ready</span>
                  )}
                </Link>
              )
            })}
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}
