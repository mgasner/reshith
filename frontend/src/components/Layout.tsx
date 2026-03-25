import { useState, useEffect, useRef } from 'react'
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom'

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
    alphabetPath: '/hebrew/alphabet',
    vowelsPath: '/hebrew/vowels',
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
    alphabetPath: null,
    vowelsPath: null,
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
    alphabetPath: null,
    vowelsPath: null,
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
    alphabetPath: null,
    vowelsPath: null,
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
    alphabetPath: null,
    vowelsPath: null,
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
    alphabetPath: null,
    vowelsPath: null,
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
    alphabetPath: null,
    vowelsPath: null,
    exercisesPath: '/exercises/ecclesiastical-latin',
    resourcesPath: null,
    hasAlphabet: false,
    hasVowels: false,
  },
]

export function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [lessonsOpen, setLessonsOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const mobileMenuRef = useRef<HTMLDivElement>(null)

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
            <div className="hidden sm:flex sm:items-center sm:gap-6">
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
            </div>
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

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}
