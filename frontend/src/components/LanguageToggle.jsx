/**
 * LanguageToggle.jsx — Switch between Hindi and English.
 *
 * Props:
 *   lang        : "en" | "hi"
 *   onLangChange: function(newLang)
 */
export default function LanguageToggle({ lang, onLangChange }) {
  return (
    <div
      className="language-toggle"
      role="group"
      aria-label={lang === 'hi' ? 'भाषा चुनें' : 'Choose language'}
    >
      <button
        type="button"
        onClick={() => onLangChange('en')}
        className={`language-option ${lang === 'en' ? 'language-option-active' : ''}`}
        aria-pressed={lang === 'en'}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => onLangChange('hi')}
        className={`language-option hindi-text ${lang === 'hi' ? 'language-option-active' : ''}`}
        aria-pressed={lang === 'hi'}
      >
        हिंदी
      </button>
    </div>
  )
}
