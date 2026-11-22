import { useEffect, useState } from 'react'
import ConsentBanner from '../components/ConsentBanner.jsx'
import Icon from '../components/Icon.jsx'
import LanguageToggle from '../components/LanguageToggle.jsx'
import { fetchSchemes } from '../utils/api.js'

const sections = [
  { id: 'assistant', icon: 'assistant', en: 'AI Scheme Assistant', hi: 'योजना सहायक' },
  { id: 'schemes', icon: 'schemes', en: 'Eligible Schemes', hi: 'योजनाएँ' },
  { id: 'applications', icon: 'applications', en: 'My Applications', hi: 'मेरे आवेदन' },
  { id: 'notifications', icon: 'notifications', en: 'Notifications', hi: 'सूचनाएँ' },
  { id: 'grievance', icon: 'grievance', en: 'Grievance Assistant', hi: 'शिकायत सहायता' },
  { id: 'profile', icon: 'profile', en: 'My Profile', hi: 'मेरी प्रोफ़ाइल' },
]

const sectionTitles = {
  assistant: ['Your benefits, made clearer', 'आपके लाभ, अब और आसान'],
  schemes: ['Scheme directory', 'योजना सूची'],
  applications: ['Application tracker', 'आवेदन स्थिति'],
  notifications: ['Updates and reminders', 'अपडेट और याद दिलाने वाली सूचनाएँ'],
  grievance: ['Grievance support', 'शिकायत सहायता'],
  profile: ['Your privacy-first profile', 'आपकी गोपनीयता-सुरक्षित प्रोफ़ाइल'],
}

function StatusIndicator({ status, lang, label }) {
  const isHindi = lang === 'hi'
  const config = {
    checking: {
      dot: 'status-dot-checking',
      text: isHindi ? 'जाँच हो रही है' : 'Checking connection',
    },
    connected: {
      dot: 'status-dot-connected',
      text: isHindi ? 'बैकएंड जुड़ा है' : 'Backend connected',
    },
    unavailable: {
      dot: 'status-dot-unavailable',
      text: isHindi ? 'बैकएंड उपलब्ध नहीं' : 'Backend unavailable',
    },
    unknown: {
      dot: 'status-dot-unknown',
      text: isHindi ? 'अभी जाँच नहीं हुई' : 'Not checked yet',
    },
    available: {
      dot: 'status-dot-connected',
      text: isHindi ? 'Gemma ने जवाब दिया' : 'Gemma responded',
    },
  }
  const current = config[status] || config.unknown

  return (
    <span className="status-pill" title={label}>
      <span className={`status-dot ${current.dot}`} />
      {current.text}
    </span>
  )
}

export default function Home({
  lang,
  onStart,
  onLangChange,
  activeSection,
  onSectionChange,
  backendStatus,
  assistantStatus,
}) {
  const isHindi = lang === 'hi'
  const [showConsent, setShowConsent] = useState(false)
  const [schemes, setSchemes] = useState([])
  const [schemesState, setSchemesState] = useState('idle')

  useEffect(() => {
    if (activeSection !== 'schemes') return undefined

    let active = true
    setSchemesState('loading')
    fetchSchemes(lang)
      .then(data => {
        if (!active) return
        setSchemes(data.schemes || [])
        setSchemesState('ready')
      })
      .catch(() => {
        if (active) setSchemesState('error')
      })

    return () => {
      active = false
    }
  }, [activeSection, lang])

  const heading = sectionTitles[activeSection] || sectionTitles.assistant
  const assistantStatusLabel = assistantStatus === 'available'
    ? (isHindi ? 'Gemma के पिछले जवाब की स्थिति' : 'Status of Gemma’s last reply')
    : assistantStatus === 'unavailable'
      ? (isHindi ? 'Gemma का पिछला अनुरोध विफल हुआ' : 'Gemma’s last request failed')
      : (isHindi ? 'स्थानीय AI सहायक की स्थिति अभी जाँची नहीं गई' : 'Local AI assistant has not been checked yet')
  const backendStatusLabel = isHindi
    ? 'बैकएंड स्थिति: स्वास्थ्य जाँच'
    : 'Backend status: live health check'

  return (
    <div className="dashboard-shell">
      <aside className="dashboard-sidebar">
        <a
          href="#main-content"
          className="skip-link"
        >
          {isHindi ? 'मुख्य सामग्री पर जाएँ' : 'Skip to main content'}
        </a>
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">य</span>
          <span>
            <strong>YojanaSetu AI</strong>
            <small className="hindi-text">योजना सेतु AI</small>
          </span>
        </div>

        <p className="nav-heading">{isHindi ? 'मुख्य मेन्यू' : 'MENU'}</p>
        <nav className="sidebar-nav" aria-label={isHindi ? 'मुख्य नेविगेशन' : 'Main navigation'}>
          {sections.map(item => (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                setShowConsent(false)
                onSectionChange(item.id)
              }}
              className={`nav-item ${activeSection === item.id ? 'nav-item-active' : ''}`}
              aria-current={activeSection === item.id ? 'page' : undefined}
            >
              <Icon name={item.icon} size={19} />
              <span className={isHindi ? 'hindi-text' : ''}>{isHindi ? item.hi : item.en}</span>
              {activeSection === item.id && <Icon name="chevron" size={16} className="nav-chevron" />}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-privacy">
            <Icon name="lock" size={18} />
            <p className={isHindi ? 'hindi-text' : ''}>
              {isHindi
                ? 'आपकी जानकारी इस डेमो में सेव नहीं होती।'
                : 'Your answers are not saved in this demo.'}
            </p>
          </div>
          <span className="demo-caption">DEMO · NOT A GOVERNMENT WEBSITE</span>
        </div>
      </aside>

      <div className="dashboard-main">
        <header className="dashboard-topbar">
          <div className="mobile-brand">
            <span className="brand-mark brand-mark-small" aria-hidden="true">य</span>
            <strong>{isHindi ? 'योजना सेतु AI' : 'YojanaSetu AI'}</strong>
          </div>
          <div className="topbar-spacer" />
          <StatusIndicator
            status={backendStatus}
            lang={lang}
            label={backendStatusLabel}
          />
          <LanguageToggle lang={lang} onLangChange={onLangChange} />
          <button
            type="button"
            className="profile-shortcut"
            onClick={() => onSectionChange('profile')}
            aria-label={isHindi ? 'मेरी प्रोफ़ाइल खोलें' : 'Open My Profile'}
            title={isHindi ? 'मेरी प्रोफ़ाइल' : 'My Profile'}
          >
            <Icon name="profile" size={19} />
          </button>
        </header>

        <nav className="mobile-nav" aria-label={isHindi ? 'मुख्य नेविगेशन' : 'Main navigation'}>
          {sections.map(item => (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                setShowConsent(false)
                onSectionChange(item.id)
              }}
              className={`mobile-nav-item ${activeSection === item.id ? 'mobile-nav-item-active' : ''}`}
              aria-current={activeSection === item.id ? 'page' : undefined}
            >
              <Icon name={item.icon} size={18} />
              <span className={isHindi ? 'hindi-text' : ''}>{isHindi ? item.hi : item.en}</span>
            </button>
          ))}
        </nav>

        <main id="main-content" className="dashboard-content">
          <div className="page-heading-row">
            <div>
              <p className="eyebrow">
                {isHindi ? 'नमस्ते · योजना सेतु AI में आपका स्वागत है' : 'NAMASTE · WELCOME TO YOJANASETU AI'}
              </p>
              <h1 className={isHindi ? 'hindi-text' : ''}>{heading[isHindi ? 1 : 0]}</h1>
              <p className="page-subtitle">
                {isHindi
                  ? 'सरकारी योजनाओं की जानकारी और पात्रता जाँच — एक सरल जगह पर।'
                  : 'Understand public-benefit schemes and check your eligibility in one simple place.'}
              </p>
            </div>
            <span className="demo-tag">
              <Icon name="info" size={15} />
              {isHindi ? 'डेमो डेटा' : 'DEMO DATA'}
            </span>
          </div>

          <div key={activeSection} className="section-view page-enter">
            {activeSection === 'assistant' && (
              <AssistantDashboard
                lang={lang}
                onStart={() => setShowConsent(true)}
                showConsent={showConsent}
                onAccept={onStart}
                backendStatus={backendStatus}
                assistantStatus={assistantStatus}
                assistantStatusLabel={assistantStatusLabel}
              />
            )}

            {activeSection === 'schemes' && (
              <SchemesPanel
                lang={lang}
                schemes={schemes}
                state={schemesState}
                onStart={() => {
                  setShowConsent(true)
                  onSectionChange('assistant')
                }}
              />
            )}

            {activeSection === 'applications' && <ApplicationsPanel lang={lang} />}
            {activeSection === 'notifications' && <NotificationsPanel lang={lang} />}
            {activeSection === 'grievance' && (
              <GrievancePanel
                lang={lang}
                onStart={() => onSectionChange('assistant')}
              />
            )}
            {activeSection === 'profile' && (
              <ProfilePanel
                lang={lang}
                backendStatus={backendStatus}
                assistantStatus={assistantStatus}
                assistantStatusLabel={assistantStatusLabel}
              />
            )}
          </div>

          <footer className="dashboard-footer">
            <span>{isHindi ? 'यह सरकारी वेबसाइट नहीं है।' : 'This is not an official government website.'}</span>
            <span>{isHindi ? 'अंतिम जाँचें आधिकारिक स्रोतों पर करें।' : 'Always verify details with official sources.'}</span>
          </footer>
        </main>
      </div>
    </div>
  )
}

function AssistantDashboard({
  lang,
  onStart,
  showConsent,
  onAccept,
  backendStatus,
  assistantStatus,
  assistantStatusLabel,
}) {
  const isHindi = lang === 'hi'

  return (
    <>
      <section className="assistant-hero">
        <div className="hero-copy">
          <span className="hero-kicker">
            <Icon name="assistant" size={15} />
            {isHindi ? 'सरल, सुरक्षित और द्विभाषी' : 'SIMPLE · PRIVATE · BILINGUAL'}
          </span>
          <h2 className={isHindi ? 'hindi-text' : ''}>
            {isHindi
              ? 'आपके लिए सही योजनाएँ खोजें।'
              : 'Find support that fits your life.'}
          </h2>
          <p className={isHindi ? 'hindi-text' : ''}>
            {isHindi
              ? 'कुछ आसान सवालों के जवाब दें। हमारा नियम-आधारित सहायक आपके लिए उपलब्ध योजनाएँ समझने में मदद करेगा।'
              : 'Answer a few simple questions. Our rule-based assistant helps you understand the schemes that may fit your situation.'}
          </p>
          {!showConsent ? (
            <button type="button" className="primary-button" onClick={onStart}>
              <span>{isHindi ? 'पात्रता जाँच शुरू करें' : 'Start eligibility check'}</span>
              <Icon name="arrow" size={18} />
            </button>
          ) : (
            <ConsentBanner lang={lang} onAccept={onAccept} />
          )}
          <div className="hero-reassurance">
            <Icon name="lock" size={15} />
            <span className={isHindi ? 'hindi-text' : ''}>
              {isHindi ? 'आपकी जानकारी सेव नहीं होती' : 'Your answers are not saved'}
            </span>
            <span className="reassurance-divider" />
            <span className={isHindi ? 'hindi-text' : ''}>
              {isHindi ? 'कोई आधार या बैंक जानकारी नहीं' : 'No Aadhaar or bank details'}
            </span>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="hero-orbit orbit-one" />
          <div className="hero-orbit orbit-two" />
          <div className="hero-art-center">
            <span className="hero-lamp">य</span>
            <span className="hero-art-spark spark-one">✦</span>
            <span className="hero-art-spark spark-two">✦</span>
          </div>
          <div className="floating-note note-scheme">
            <span className="note-icon note-icon-green"><Icon name="schemes" size={18} /></span>
            <span><strong>{isHindi ? 'योजना सहायता' : 'Scheme support'}</strong><small>{isHindi ? 'आपके लिए' : 'Made for you'}</small></span>
          </div>
          <div className="floating-note note-language">
            <Icon name="globe" size={16} />
            <span>हिंदी · English</span>
          </div>
        </div>
      </section>

      <div className="overview-grid">
        <OverviewCard
          icon="schemes"
          tone="blue"
          value="5"
          title={isHindi ? 'डेमो योजनाएँ' : 'Demo schemes'}
          description={isHindi ? 'जाँच के लिए उपलब्ध' : 'Available to explore'}
        />
        <OverviewCard
          icon="globe"
          tone="saffron"
          value="2"
          title={isHindi ? 'भाषाएँ' : 'Languages'}
          description={isHindi ? 'हिंदी और अंग्रेज़ी' : 'Hindi and English'}
        />
        <OverviewCard
          icon="lock"
          tone="green"
          value={isHindi ? 'नहीं' : 'No'}
          title={isHindi ? 'डेटा सेव' : 'Data saved'}
          description={isHindi ? 'यह डेमो जानकारी सेव नहीं करता' : 'This demo does not save answers'}
        />
      </div>

      <section className="dashboard-section">
        <div className="section-title-row">
          <div>
            <p className="eyebrow">{isHindi ? 'यह कैसे काम करता है' : 'A CLEARER WAY FORWARD'}</p>
            <h2 className={isHindi ? 'hindi-text' : ''}>
              {isHindi ? 'तीन आसान कदम' : 'Three simple steps'}
            </h2>
          </div>
          <StatusIndicator
            status={backendStatus}
            lang={lang}
            label={isHindi ? 'बैकएंड की लाइव स्थिति' : 'Live backend health status'}
          />
        </div>
        <div className="steps-grid">
          <StepCard number="01" title={isHindi ? 'अपनी भाषा चुनें' : 'Choose your language'} text={isHindi ? 'हिंदी या अंग्रेज़ी में आगे बढ़ें।' : 'Continue in Hindi or English.'} />
          <StepCard number="02" title={isHindi ? 'कुछ सवालों के जवाब दें' : 'Answer a few questions'} text={isHindi ? 'टाइप करें या समर्थित ब्राउज़र में बोलें।' : 'Type, or speak in a supported browser.'} />
          <StepCard number="03" title={isHindi ? 'नतीजे समझें' : 'Understand your results'} text={isHindi ? 'पात्रता के कारण और अगले कदम देखें।' : 'Review eligibility reasons and next steps.'} />
        </div>
      </section>

      <section className="connection-card">
        <div className="connection-copy">
          <span className="connection-icon"><Icon name="server" size={20} /></span>
          <div>
            <h3 className={isHindi ? 'hindi-text' : ''}>
              {isHindi ? 'स्थानीय AI सहायक' : 'Local AI assistant'}
            </h3>
            <p className={isHindi ? 'hindi-text' : ''}>
              {assistantStatus === 'available'
                ? (isHindi ? 'पिछले स्पष्टीकरण में Gemma ने जवाब दिया।' : 'Gemma responded to the last clarification.')
                : assistantStatus === 'unavailable'
                  ? (isHindi ? 'पिछला स्पष्टीकरण पूरा नहीं हुआ। कनेक्शन जाँचें।' : 'The last clarification failed. Check the local connection.')
                  : (isHindi ? 'कनेक्शन की पुष्टि सरल स्पष्टीकरण माँगने पर होगी।' : 'Connection is verified when you request a simple explanation.')}
            </p>
          </div>
        </div>
        <StatusIndicator
          status={assistantStatus}
          lang={lang}
          label={assistantStatusLabel}
        />
      </section>
    </>
  )
}

function OverviewCard({ icon, tone, value, title, description }) {
  return (
    <article className="overview-card">
      <span className={`overview-icon overview-icon-${tone}`}><Icon name={icon} size={19} /></span>
      <span className="overview-value">{value}</span>
      <strong>{title}</strong>
      <small>{description}</small>
    </article>
  )
}

function StepCard({ number, title, text }) {
  return (
    <article className="step-card">
      <span>{number}</span>
      <h3>{title}</h3>
      <p>{text}</p>
    </article>
  )
}

function SchemesPanel({ lang, schemes, state, onStart }) {
  const isHindi = lang === 'hi'

  return (
    <section className="content-panel">
      <div className="panel-intro">
        <span className="panel-icon panel-icon-blue"><Icon name="schemes" size={22} /></span>
        <div>
          <h2 className={isHindi ? 'hindi-text' : ''}>{isHindi ? 'योजना निर्देशिका' : 'Explore demo schemes'}</h2>
          <p className={isHindi ? 'hindi-text' : ''}>
            {isHindi
              ? 'यह सूची केवल जानकारी के लिए है। व्यक्तिगत पात्रता जानने के लिए जाँच शुरू करें।'
              : 'Browse the sample catalog. Start a check to see which schemes may fit your answers.'}
          </p>
        </div>
      </div>
      {state === 'loading' && <p className="inline-status">{isHindi ? 'योजनाएँ लोड हो रही हैं…' : 'Loading schemes…'}</p>}
      {state === 'error' && (
        <p role="alert" className="inline-error">
          {isHindi ? 'योजना सूची लोड नहीं हुई। बैकएंड कनेक्शन जाँचें।' : 'The scheme list could not be loaded. Check the backend connection.'}
        </p>
      )}
      {state === 'ready' && (
        <div className="scheme-grid">
          {schemes.map(scheme => (
            <article key={scheme.id} className="scheme-tile">
              <div className="scheme-tile-heading">
                <span className="scheme-tile-icon"><Icon name="schemes" size={18} /></span>
                <span className="sample-label">{isHindi ? 'डेमो योजना' : 'DEMO SCHEME'}</span>
              </div>
              <h3 className={isHindi ? 'hindi-text' : ''}>{scheme.name}</h3>
              <p className={isHindi ? 'hindi-text' : ''}>{scheme.description}</p>
              <div className="scheme-tile-meta">
                <span><strong>{isHindi ? 'लाभ' : 'Benefit'}:</strong> {scheme.benefit}</span>
                <span><strong>{isHindi ? 'आवेदन' : 'Apply'}:</strong> {scheme.apply_at}</span>
              </div>
            </article>
          ))}
        </div>
      )}
      <div className="panel-demo-note">
        <Icon name="info" size={17} />
        <span className={isHindi ? 'hindi-text' : ''}>
          {isHindi
            ? 'पात्रता के नतीजे केवल इस डेमो के नियमों पर आधारित हैं। आधिकारिक पोर्टल पर पुष्टि करें।'
            : 'Eligibility results use demo rules only. Confirm all details with official portals.'}
        </span>
      </div>
      <button type="button" className="primary-button" onClick={onStart}>
        <span>{isHindi ? 'मेरी पात्रता जाँचें' : 'Check my eligibility'}</span>
        <Icon name="arrow" size={18} />
      </button>
    </section>
  )
}

function ApplicationsPanel({ lang }) {
  const isHindi = lang === 'hi'
  const examples = isHindi
    ? [
        ['तैयारी में', 'ड्राफ़्ट', 'आवेदन जमा नहीं हुआ'],
        ['जमा किया गया', 'जाँच का इंतज़ार', 'केवल स्थिति का उदाहरण'],
        ['निर्णय जारी', 'स्थिति देखें', 'कोई वास्तविक आवेदन जुड़ा नहीं'],
      ]
    : [
        ['In preparation', 'Draft', 'Application not submitted'],
        ['Submitted', 'Awaiting review', 'Example status only'],
        ['Decision issued', 'View status', 'No real application is connected'],
      ]

  return (
    <section className="content-panel">
      <div className="panel-intro">
        <span className="panel-icon panel-icon-saffron"><Icon name="applications" size={22} /></span>
        <div>
          <h2 className={isHindi ? 'hindi-text' : ''}>{isHindi ? 'आवेदन स्थिति के उदाहरण' : 'Application status examples'}</h2>
          <p className={isHindi ? 'hindi-text' : ''}>
            {isHindi
              ? 'यह डेमो किसी सरकारी आवेदन पोर्टल से जुड़ा नहीं है।'
              : 'This demo is not connected to a government application portal.'}
          </p>
        </div>
      </div>
      <div className="status-example-grid">
        {examples.map(([title, status, description]) => (
          <article className="status-example-card" key={title}>
            <span className="sample-label">{isHindi ? 'केवल उदाहरण' : 'EXAMPLE ONLY'}</span>
            <h3 className={isHindi ? 'hindi-text' : ''}>{title}</h3>
            <span className="application-status">{status}</span>
            <p className={isHindi ? 'hindi-text' : ''}>{description}</p>
          </article>
        ))}
      </div>
      <div className="panel-demo-note">
        <Icon name="info" size={17} />
        <span className={isHindi ? 'hindi-text' : ''}>
          {isHindi
            ? 'यहाँ कोई आवेदन जमा, सेव या ट्रैक नहीं किया जाता।'
            : 'No applications are submitted, saved, or tracked here.'}
        </span>
      </div>
    </section>
  )
}

function NotificationsPanel({ lang }) {
  const isHindi = lang === 'hi'
  const notices = isHindi
    ? [
        ['दस्तावेज़ तैयार रखें', 'आवेदन से पहले आधिकारिक योजना पोर्टल पर आवश्यक दस्तावेज़ जाँचें।'],
        ['पात्रता की पुष्टि करें', 'नियम और समय-सीमा बदल सकती है। सरकारी स्रोत से नवीनतम जानकारी लें।'],
      ]
    : [
        ['Keep documents ready', 'Check the official scheme portal for required documents before applying.'],
        ['Confirm eligibility', 'Rules and deadlines may change. Verify current details with an official source.'],
      ]

  return (
    <section className="content-panel">
      <div className="panel-intro">
        <span className="panel-icon panel-icon-green"><Icon name="notifications" size={22} /></span>
        <div>
          <h2 className={isHindi ? 'hindi-text' : ''}>{isHindi ? 'सूचना उदाहरण' : 'Illustrative reminders'}</h2>
          <p className={isHindi ? 'hindi-text' : ''}>
            {isHindi ? 'यह डेमो वास्तविक सूचनाएँ नहीं भेजता।' : 'This demo does not send real notifications.'}
          </p>
        </div>
      </div>
      <div className="notification-list">
        {notices.map(([title, body]) => (
          <article className="notification-card" key={title}>
            <span className="notification-mark"><Icon name="info" size={18} /></span>
            <div>
              <span className="sample-label">{isHindi ? 'डेमो सूचना' : 'DEMO NOTICE'}</span>
              <h3 className={isHindi ? 'hindi-text' : ''}>{title}</h3>
              <p className={isHindi ? 'hindi-text' : ''}>{body}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

function GrievancePanel({ lang, onStart }) {
  const isHindi = lang === 'hi'

  return (
    <section className="content-panel">
      <div className="panel-intro">
        <span className="panel-icon panel-icon-blue"><Icon name="grievance" size={22} /></span>
        <div>
          <h2 className={isHindi ? 'hindi-text' : ''}>{isHindi ? 'शिकायत सहायता का पूर्वावलोकन' : 'Grievance support preview'}</h2>
          <p className={isHindi ? 'hindi-text' : ''}>
            {isHindi
              ? 'यह सुविधा अभी किसी सरकारी शिकायत सेवा से जुड़ी नहीं है।'
              : 'This feature is not connected to a government grievance service.'}
          </p>
        </div>
      </div>
      <div className="grievance-callout">
        <Icon name="info" size={21} />
        <div>
          <h3 className={isHindi ? 'hindi-text' : ''}>{isHindi ? 'सुरक्षित रूप से आगे बढ़ें' : 'Next steps, safely'}</h3>
          <p className={isHindi ? 'hindi-text' : ''}>
            {isHindi
              ? 'अपनी योजना के आधिकारिक पोर्टल या संबंधित विभाग से संपर्क करें। अपनी शिकायत संख्या और जरूरी दस्तावेज़ अपने पास रखें।'
              : 'Contact the official scheme portal or department. Keep your reference number and relevant documents with you.'}
          </p>
        </div>
      </div>
      <button type="button" className="secondary-button" onClick={onStart}>
        {isHindi ? 'योजना सहायक पर वापस जाएँ' : 'Return to Scheme Assistant'}
        <Icon name="arrow" size={17} />
      </button>
    </section>
  )
}

function ProfilePanel({ lang, backendStatus, assistantStatus, assistantStatusLabel }) {
  const isHindi = lang === 'hi'

  return (
    <section className="content-panel">
      <div className="panel-intro">
        <span className="panel-icon panel-icon-green"><Icon name="profile" size={22} /></span>
        <div>
          <h2 className={isHindi ? 'hindi-text' : ''}>{isHindi ? 'कोई प्रोफ़ाइल सेव नहीं' : 'No saved profile'}</h2>
          <p className={isHindi ? 'hindi-text' : ''}>
            {isHindi
              ? 'यह डेमो आपकी पहचान या उत्तरों को सेव नहीं करता।'
              : 'This demo does not save your identity or answers.'}
          </p>
        </div>
      </div>
      <div className="profile-status-list">
        <div><Icon name="lock" size={19} /><span>{isHindi ? 'उत्तर केवल वर्तमान जाँच के लिए उपयोग होते हैं।' : 'Answers are used for the current eligibility check only.'}</span></div>
        <div><Icon name="server" size={19} /><span>{isHindi ? 'बैकएंड की लाइव स्थिति:' : 'Live backend status:'}<StatusIndicator status={backendStatus} lang={lang} /></span></div>
        <div><Icon name="assistant" size={19} /><span>{isHindi ? 'AI की पिछली स्थिति:' : 'AI last response:'}<StatusIndicator status={assistantStatus} lang={lang} label={assistantStatusLabel} /></span></div>
      </div>
      <div className="panel-demo-note">
        <Icon name="info" size={17} />
        <span className={isHindi ? 'hindi-text' : ''}>
          {isHindi
            ? 'वास्तविक सरकारी प्रोफ़ाइल या आवेदन जानकारी यहाँ उपलब्ध नहीं है।'
            : 'Government profile or application records are not available here.'}
        </span>
      </div>
    </section>
  )
}
