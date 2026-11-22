import { useState, useRef, useEffect, useCallback } from 'react'
import ChatBubble from '../components/ChatBubble.jsx'
import VoiceButton from '../components/VoiceButton.jsx'
import EligibilityResult from '../components/EligibilityResult.jsx'
import LanguageToggle from '../components/LanguageToggle.jsx'
import Icon from '../components/Icon.jsx'
import { useSpeech } from '../hooks/useSpeech.js'
import { fetchNextQuestion, checkEligibility, clarifyQuestion, validateAnswer } from '../utils/api.js'

export default function Checker({
  lang,
  onLangChange,
  onBack,
  backendStatus,
  assistantStatus,
  onAssistantStatusChange,
  onRefreshBackendStatus,
}) {
  const isHindi = lang === 'hi'
  const [messages, setMessages] = useState([])
  const [profile, setProfile] = useState({})
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [voiceEnabled, setVoiceEnabled] = useState(false)
  const [isClarifying, setIsClarifying] = useState(false)

  const chatEndRef = useRef(null)
  const voiceEnabledRef = useRef(false)
  const startedRef = useRef(false)
  const langRef = useRef(lang)
  const currentQuestionRef = useRef(currentQuestion)
  const languageRequestRef = useRef(0)
  const conversationRequestRef = useRef(0)
  const clarificationRequestRef = useRef(0)
  const answerInFlightRef = useRef(false)
  const announcedMatchesRef = useRef(new Set())
  langRef.current = lang
  currentQuestionRef.current = currentQuestion
  const { isListening, startListening, stopListening, speak, cancelSpeech, supported } = useSpeech(lang)

  const speakAI = useCallback((text) => {
    if (voiceEnabledRef.current) speak(text)
  }, [speak])

  useEffect(() => () => cancelSpeech(), [cancelSpeech])

  const toggleVoiceOutput = () => {
    const nextEnabled = !voiceEnabledRef.current
    voiceEnabledRef.current = nextEnabled
    setVoiceEnabled(nextEnabled)
    if (!nextEnabled) cancelSpeech()
  }

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isLoading, isClarifying])

  const addMessage = (role, text) => {
    setMessages(prev => [...prev, { role, text, id: Date.now() + Math.random() }])
  }

  const handleLanguageChange = async (nextLang) => {
    if (nextLang === langRef.current) return
    langRef.current = nextLang
    onLangChange(nextLang)
    clarificationRequestRef.current += 1
    setIsClarifying(false)

    const requestId = ++languageRequestRef.current
    const conversationRequestId = conversationRequestRef.current
    if (results) {
      try {
        const data = await checkEligibility(profile, nextLang)
        if (requestId !== languageRequestRef.current) return
        if (conversationRequestId !== conversationRequestRef.current) return
        setResults(data)
      } catch {
        if (requestId !== languageRequestRef.current) return
        if (conversationRequestId !== conversationRequestRef.current) return
        setError(nextLang === 'hi'
          ? 'भाषा बदलते समय पात्रता परिणाम अपडेट नहीं हो सके।'
          : 'Could not refresh the eligibility results in the selected language.')
        onRefreshBackendStatus?.()
      }
      return
    }

    const activeQuestionId = currentQuestionRef.current?.id
    if (!activeQuestionId || isLoading) return

    try {
      const data = await fetchNextQuestion(profile, nextLang)
      if (requestId !== languageRequestRef.current) return
      if (conversationRequestId !== conversationRequestRef.current) return
      if (currentQuestionRef.current?.id !== activeQuestionId) return
      if (data.next_question?.id !== activeQuestionId) return

      setCurrentQuestion(data.next_question)
      addMessage('bot', data.next_question.text)
      speakAI(data.next_question.text)
    } catch {
      if (requestId !== languageRequestRef.current) return
      if (conversationRequestId !== conversationRequestRef.current) return
      setError(nextLang === 'hi'
        ? 'भाषा बदलते समय सर्वर से कनेक्ट नहीं हो सका।'
        : 'Could not refresh the question in the selected language.')
      onRefreshBackendStatus?.()
    }
  }

  const runEligibilityCheck = async (finalProfile, requestId) => {
    setIsLoading(true)
    try {
      addMessage('bot', isHindi
        ? 'आपकी जानकारी के आधार पर योजनाएँ जाँच रहा हूँ...'
        : 'Checking schemes based on your answers...')

      let requestLang = langRef.current
      let data = await checkEligibility(finalProfile, requestLang)
      if (requestLang !== langRef.current) {
        requestLang = langRef.current
        data = await checkEligibility(finalProfile, requestLang)
      }
      if (requestId !== conversationRequestRef.current) return
      setResults(data)
    } catch {
      if (requestId !== conversationRequestRef.current) return
      addMessage('bot', isHindi
        ? 'पात्रता जाँच में त्रुटि। कृपया बैकएंड कनेक्शन जाँचें और फिर प्रयास करें।'
        : 'Eligibility check failed. Please check the backend connection and try again.')
      onRefreshBackendStatus?.()
    } finally {
      if (requestId === conversationRequestRef.current) setIsLoading(false)
    }
  }

  const askNextQuestion = useCallback(async (updatedProfile) => {
    const requestId = conversationRequestRef.current
    setIsLoading(true)
    setError(null)
    try {
      const requestLang = langRef.current
      let data = await fetchNextQuestion(updatedProfile, requestLang)
      if (requestLang !== langRef.current) {
        data = await fetchNextQuestion(updatedProfile, langRef.current)
      }
      if (requestId !== conversationRequestRef.current) return

      if (data.contradictions?.length > 0) {
        for (const warning of data.contradictions) {
          addMessage('bot', warning)
          speakAI(warning)
        }
      }

      if (!data.done && !data.contradictions?.length && !data.next_question?.is_clarification) {
        const newMatches = (data.early_matches || []).filter(match => {
          if (announcedMatchesRef.current.has(match.scheme_id)) return false
          announcedMatchesRef.current.add(match.scheme_id)
          return true
        })
        if (newMatches.length > 0) {
          const names = newMatches.map(match => match.name).join(', ')
          const matchMessage = langRef.current === 'hi'
            ? `आपके जवाब इन योजनाओं के डेमो नियमों से मेल खाते हैं: ${names}। मैं बाकी योजनाओं की जाँच जारी रखूँगा।`
            : `Your answers meet the demo rules for: ${names}. I'll keep checking other schemes.`
          addMessage('bot', matchMessage)
          speakAI(matchMessage)
        }
      }

      if (data.done) {
        await runEligibilityCheck(updatedProfile, requestId)
      } else {
        const question = data.next_question
        setCurrentQuestion(question)
        addMessage('bot', question.text)
        speakAI(question.text)
      }
    } catch {
      if (requestId !== conversationRequestRef.current) return
      const message = isHindi
        ? 'सर्वर से कनेक्ट नहीं हो सका। कृपया बैकएंड चलने की जाँच करें।'
        : 'Could not connect to the server. Please check that the backend is running.'
      setError(message)
      addMessage('bot', message)
      onRefreshBackendStatus?.()
    } finally {
      if (requestId === conversationRequestRef.current) setIsLoading(false)
    }
  }, [lang, isHindi, speakAI, onRefreshBackendStatus])

  const handleAnswer = useCallback(async (rawAnswer) => {
    if (answerInFlightRef.current || isLoading || !currentQuestion || !rawAnswer.trim()) return

    answerInFlightRef.current = true
    setError(null)
    const question = currentQuestion
    const conversationRequestId = conversationRequestRef.current
    const answer = rawAnswer.trim()

    try {
      let requestLang = langRef.current
      let validation = await validateAnswer(question.id, answer, requestLang)
      if (requestLang !== langRef.current && !validation.valid) {
        requestLang = langRef.current
        validation = await validateAnswer(question.id, answer, requestLang)
      }
      if (conversationRequestId !== conversationRequestRef.current) return
      if (currentQuestionRef.current?.id !== question.id) return
      if (!validation.valid) {
        setError(validation.error)
        return
      }

      clarificationRequestRef.current += 1
      setIsClarifying(false)
      addMessage('user', answer)
      setInputText('')

      const updatedProfile = { ...profile, [question.id]: validation.value }
      if (question.is_clarification) {
        const clarifiedFields = new Set(
          Array.isArray(profile._clarified_fields) ? profile._clarified_fields : [],
        )
        clarifiedFields.add(question.id)
        updatedProfile._clarified_fields = [...clarifiedFields]
      }
      setProfile(updatedProfile)
      await askNextQuestion(updatedProfile)
    } catch (validationError) {
      if (conversationRequestId !== conversationRequestRef.current) return
      const detail = validationError instanceof Error
        ? validationError.message
        : 'Unknown answer validation error.'
      setError(isHindi
        ? `उत्तर की जाँच नहीं हो सकी: ${detail}`
        : `Could not validate your answer: ${detail}`)
      onRefreshBackendStatus?.()
    } finally {
      answerInFlightRef.current = false
    }
  }, [currentQuestion, isHindi, isLoading, profile, askNextQuestion, onRefreshBackendStatus])

  const handleVoiceInput = () => {
    if (isListening) {
      stopListening()
      return
    }
    setError(null)
    startListening(setInputText, setError)
  }

  const handleExplainQuestion = async () => {
    if (!currentQuestion || isClarifying) return

    const questionId = currentQuestion.id
    const requestLang = langRef.current
    const requestId = ++clarificationRequestRef.current
    setError(null)
    setIsClarifying(true)
    const message = isHindi
      ? 'कृपया इस प्रश्न को सरल शब्दों में समझाएं।'
      : 'Please explain this question in simpler words.'
    try {
      const data = await clarifyQuestion(questionId, message, requestLang)
      if (requestId !== clarificationRequestRef.current) return
      if (currentQuestionRef.current?.id !== questionId || langRef.current !== requestLang) return
      addMessage('bot', data.reply)
      onAssistantStatusChange('available')
      speakAI(data.reply)
    } catch (err) {
      if (requestId !== clarificationRequestRef.current) return
      const detail = err instanceof Error ? err.message : 'Unknown assistant error.'
      setError(isHindi
        ? `AI सहायता उपलब्ध नहीं है: ${detail}`
        : `AI clarification unavailable: ${detail}`)
      onAssistantStatusChange('unavailable')
      onRefreshBackendStatus?.()
    } finally {
      if (requestId === clarificationRequestRef.current) setIsClarifying(false)
    }
  }

  useEffect(() => {
    if (startedRef.current) return
    startedRef.current = true

    const greeting = isHindi
      ? 'नमस्ते! मैं योजना सेतु AI हूँ। मैं आपको सरकारी योजनाओं के बारे में बताऊँगा। बस कुछ सवालों के जवाब दीजिए।'
      : 'Hello! I am YojanaSetu AI. I will help you find government schemes you may qualify for. Just answer a few questions.'

    addMessage('bot', greeting)
    speakAI(greeting)
    askNextQuestion({})
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleRestart = () => {
    conversationRequestRef.current += 1
    clarificationRequestRef.current += 1
    languageRequestRef.current += 1
    answerInFlightRef.current = false
    announcedMatchesRef.current.clear()
    setMessages([])
    setProfile({})
    setResults(null)
    setCurrentQuestion(null)
    setError(null)
    setIsClarifying(false)

    const greeting = isHindi ? 'ठीक है, फिर से शुरू करते हैं!' : "Alright, let's start over!"
    addMessage('bot', greeting)
    setTimeout(() => askNextQuestion({}), 300)
  }

  return (
    <div className="chat-page">
      <header className="chat-header">
        <div className="chat-brand">
          <button
            type="button"
            className="icon-button back-button"
            onClick={onBack}
            aria-label={isHindi ? 'डैशबोर्ड पर वापस जाएँ' : 'Back to dashboard'}
            title={isHindi ? 'डैशबोर्ड' : 'Dashboard'}
          >
            <Icon name="home" size={19} />
          </button>
          <span className="brand-mark brand-mark-small" aria-hidden="true">य</span>
          <span>
            <strong>{isHindi ? 'योजना सेतु AI' : 'YojanaSetu AI'}</strong>
            <small className={isHindi ? 'hindi-text' : ''}>
              {isHindi ? 'योजना सेतु AI · डेमो' : 'YojanaSetu AI · Demo'}
            </small>
          </span>
        </div>
        <div className="chat-header-actions">
          <HeaderStatus status={backendStatus} lang={lang} kind="backend" />
          <LanguageToggle lang={lang} onLangChange={handleLanguageChange} />
          <button
            type="button"
            onClick={toggleVoiceOutput}
            className={`icon-button voice-toggle ${voiceEnabled ? 'voice-toggle-on' : ''}`}
            title={isHindi
              ? (voiceEnabled ? 'AI की आवाज़ बंद करें' : 'AI की आवाज़ चालू करें')
              : (voiceEnabled ? 'Turn AI voice off' : 'Turn AI voice on')}
            aria-label={isHindi
              ? (voiceEnabled ? 'AI की आवाज़ बंद करें' : 'AI की आवाज़ चालू करें')
              : (voiceEnabled ? 'Turn AI voice off' : 'Turn AI voice on')}
            aria-pressed={voiceEnabled}
          >
            <Icon name={voiceEnabled ? 'volume' : 'volumeOff'} size={19} />
          </button>
        </div>
      </header>

      <main className="chat-workspace page-enter">
        <aside className="chat-context-panel">
          <div className="context-welcome">
            <span className="context-lamp" aria-hidden="true">य</span>
            <p className="eyebrow">{isHindi ? 'आपकी सहायता के लिए' : 'HERE TO HELP'}</p>
            <h1 className={isHindi ? 'hindi-text' : ''}>
              {isHindi ? 'एक सवाल, एक कदम।' : 'One question at a time.'}
            </h1>
            <p className={isHindi ? 'hindi-text' : ''}>
              {isHindi
                ? 'सही जवाब देने में मदद चाहिए? किसी भी सवाल को सरल भाषा में समझने के लिए कहें।'
                : 'Need help answering? Ask for a simpler explanation whenever you need one.'}
            </p>
          </div>

          <div className="context-info-card">
            <div className="context-info-icon"><Icon name="lock" size={18} /></div>
            <div>
              <strong className={isHindi ? 'hindi-text' : ''}>{isHindi ? 'आपकी जानकारी निजी है' : 'Your answers stay private'}</strong>
              <p className={isHindi ? 'hindi-text' : ''}>
                {isHindi ? 'यह डेमो आपकी प्रोफ़ाइल सेव नहीं करता।' : 'This demo does not save your profile.'}
              </p>
            </div>
          </div>

          <div className="context-info-card">
            <div className="context-info-icon context-info-icon-green"><Icon name="schemes" size={18} /></div>
            <div>
              <strong className={isHindi ? 'hindi-text' : ''}>{isHindi ? 'नियम-आधारित जाँच' : 'Rule-based eligibility'}</strong>
              <p className={isHindi ? 'hindi-text' : ''}>
                {isHindi ? 'AI केवल सवाल समझाने में मदद करता है।' : 'AI only helps explain questions; rules decide results.'}
              </p>
            </div>
          </div>

          <div className="context-local-status">
            <span className="context-status-label">{isHindi ? 'Gemma की पिछली स्थिति' : 'Gemma last response'}</span>
            <HeaderStatus status={assistantStatus} lang={lang} kind="assistant" />
          </div>
        </aside>

        <section className="conversation-card" aria-label={isHindi ? 'चैट बातचीत' : 'Chat conversation'}>
          <div className="conversation-heading">
            <div>
              <span className="assistant-avatar"><Icon name="assistant" size={20} /></span>
              <span>
                <strong>{isHindi ? 'योजना सेतु AI' : 'YojanaSetu AI'}</strong>
                <small className={isHindi ? 'hindi-text' : ''}>
                  {isHindi ? 'सरकारी योजनाओं के लिए आपका सहायक' : 'Your guide to public-benefit schemes'}
                </small>
              </span>
            </div>
            <span className="rule-badge">
              <Icon name="schemes" size={14} />
              {isHindi ? 'नियम-आधारित' : 'Rule-based'}
            </span>
          </div>

          <div className="conversation-status-row" role="group" aria-live="polite" aria-label={isHindi ? 'कनेक्शन स्थिति' : 'Connection status'}>
            <HeaderStatus status={backendStatus} lang={lang} kind="backend" />
            <HeaderStatus status={assistantStatus} lang={lang} kind="assistant" />
          </div>

          <div className="chat-messages">
            {messages.map(message => (
              <ChatBubble
                key={message.id}
                role={message.role}
                text={message.text}
                isHindi={isHindi}
              />
            ))}

            {isLoading && (
              <TypingIndicator
                lang={lang}
                label={isHindi ? 'अगला सवाल तैयार हो रहा है' : 'Preparing the next question'}
              />
            )}
            {isClarifying && (
              <TypingIndicator
                lang={lang}
                label={isHindi ? 'Gemma सरल जवाब तैयार कर रहा है' : 'Gemma is preparing a simple explanation'}
              />
            )}

            {results && (
              <div className="results-enter">
                <EligibilityResult
                  results={results.results}
                  summary={results.summary}
                  disclaimer={results.disclaimer}
                  lang={lang}
                  onRestart={handleRestart}
                />
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {!results && (
            <div className="composer-wrap">
              {error && (
                <p role="alert" className={`chat-error ${isHindi ? 'hindi-text' : ''}`}>
                  <Icon name="info" size={16} />
                  {error}
                </p>
              )}
              {!supported && (
                <p role="status" className={`chat-hint ${isHindi ? 'hindi-text' : ''}`}>
                  {isHindi
                    ? 'इस ब्राउज़र में वॉइस इनपुट उपलब्ध नहीं है। आप टाइप करके जारी रख सकते हैं।'
                    : 'Voice input is not supported in this browser. You can continue by typing.'}
                </p>
              )}
              {currentQuestion && (
                <button
                  type="button"
                  onClick={handleExplainQuestion}
                  disabled={isLoading || isClarifying}
                  className={`explain-button ${isHindi ? 'hindi-text' : ''}`}
                >
                  <Icon name="assistant" size={17} />
                  {isClarifying
                    ? (isHindi ? 'Gemma समझा रहा है…' : 'Gemma is thinking…')
                    : (isHindi ? 'इस सवाल को सरल भाषा में समझाएँ' : 'Explain this question simply')}
                </button>
              )}
              <form
                className="chat-composer"
                onSubmit={event => {
                  event.preventDefault()
                  handleAnswer(inputText)
                }}
              >
                <label htmlFor="chat-answer" className="sr-only">
                  {isHindi ? 'आपका जवाब' : 'Your answer'}
                </label>
                <input
                  id="chat-answer"
                  type="text"
                  value={inputText}
                  onChange={event => setInputText(event.target.value)}
                  placeholder={isHindi ? 'यहाँ टाइप करें या बोलें…' : 'Type your answer or use the mic…'}
                  className={`chat-input ${isHindi ? 'hindi-text' : ''}`}
                  disabled={isLoading}
                  autoComplete="off"
                />
                <VoiceButton
                  isListening={isListening}
                  onPress={handleVoiceInput}
                  lang={lang}
                />
                <button
                  type="submit"
                  disabled={!inputText.trim() || isLoading}
                  className="send-button"
                  aria-label={isHindi ? 'जवाब भेजें' : 'Send answer'}
                  title={isHindi ? 'जवाब भेजें' : 'Send answer'}
                >
                  <Icon name="send" size={18} />
                </button>
              </form>
              <p className={`composer-note ${isHindi ? 'hindi-text' : ''}`}>
                {isHindi
                  ? 'AI आवाज़ अलग से चालू करें। माइक्रोफ़ोन इनपुट म्यूट से स्वतंत्र है।'
                  : 'AI voice is optional. Microphone input works independently of the mute setting.'}
              </p>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

function HeaderStatus({ status, lang, kind }) {
  const isHindi = lang === 'hi'
  const assistant = kind === 'assistant'
  const config = {
    connected: {
      dot: 'status-dot-connected',
      text: assistant
        ? (isHindi ? 'Gemma ने जवाब दिया' : 'Gemma responded')
        : (isHindi ? 'बैकएंड जुड़ा है' : 'Backend connected'),
    },
    available: {
      dot: 'status-dot-connected',
      text: assistant
        ? (isHindi ? 'Gemma ने जवाब दिया' : 'Gemma responded')
        : (isHindi ? 'बैकएंड जुड़ा है' : 'Backend connected'),
    },
    unavailable: {
      dot: 'status-dot-unavailable',
      text: assistant
        ? (isHindi ? 'जवाब उपलब्ध नहीं' : 'Response unavailable')
        : (isHindi ? 'बैकएंड उपलब्ध नहीं' : 'Backend unavailable'),
    },
    checking: {
      dot: 'status-dot-checking',
      text: isHindi ? 'जाँच हो रही है' : 'Checking…',
    },
    unknown: {
      dot: 'status-dot-unknown',
      text: assistant
        ? (isHindi ? 'अभी जाँच नहीं हुई' : 'Not checked yet')
        : (isHindi ? 'स्थिति अज्ञात' : 'Status unknown'),
    },
  }
  const current = config[status] || config.unknown

  return (
    <span className="status-pill compact-status">
      <span className={`status-dot ${current.dot}`} />
      {current.text}
    </span>
  )
}

function TypingIndicator({ lang, label }) {
  return (
    <div className="typing-row" role="status" aria-live="polite">
      <span className="assistant-avatar typing-avatar"><Icon name="assistant" size={17} /></span>
      <div className="typing-bubble">
        <span className="typing-dots" aria-hidden="true">
          <i /><i /><i />
        </span>
        <span className={lang === 'hi' ? 'hindi-text' : ''}>{label}</span>
      </div>
    </div>
  )
}
