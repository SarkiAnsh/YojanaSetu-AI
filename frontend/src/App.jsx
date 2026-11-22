import { useCallback, useEffect, useState } from 'react'
import Checker from './pages/Checker.jsx'
import Home from './pages/Home.jsx'
import { checkBackendHealth } from './utils/api.js'

/**
 * App.jsx — Root component
 * Manages which page to show: Home (landing) or Checker (eligibility chat)
 */
export default function App() {
  const [page, setPage] = useState('home')   // 'home' | 'checker'
  const [section, setSection] = useState('assistant')
  const [lang, setLang] = useState('en')     // 'en' | 'hi'
  const [backendStatus, setBackendStatus] = useState('checking')
  const [assistantStatus, setAssistantStatus] = useState('unknown')

  const refreshBackendStatus = useCallback(async () => {
    try {
      await checkBackendHealth()
      setBackendStatus('connected')
    } catch {
      setBackendStatus('unavailable')
    }
  }, [])

  useEffect(() => {
    document.documentElement.lang = lang === 'hi' ? 'hi' : 'en'
  }, [lang])

  useEffect(() => {
    refreshBackendStatus()
    const intervalId = window.setInterval(refreshBackendStatus, 30000)
    return () => window.clearInterval(intervalId)
  }, [refreshBackendStatus])

  return (
    <div className="min-h-screen">
      {page === 'home' ? (
        <Home
          lang={lang}
          onStart={() => setPage('checker')}
          onLangChange={setLang}
          activeSection={section}
          onSectionChange={setSection}
          backendStatus={backendStatus}
          assistantStatus={assistantStatus}
        />
      ) : (
        <Checker
          lang={lang}
          onLangChange={setLang}
          onBack={() => setPage('home')}
          backendStatus={backendStatus}
          assistantStatus={assistantStatus}
          onAssistantStatusChange={setAssistantStatus}
          onRefreshBackendStatus={refreshBackendStatus}
        />
      )}
    </div>
  )
}
