/**
 * EligibilityResult.jsx — Displays the final eligibility results.
 *
 * Props:
 *   results    : array of scheme result objects from the API
 *   summary    : { eligible_count, eligible_schemes, ... }
 *   disclaimer : string — the data disclaimer text
 *   lang       : "en" | "hi"
 *   onRestart  : function — called to start a new session
 */
export default function EligibilityResult({ results, summary, disclaimer, lang, onRestart }) {
  const isHindi = lang === 'hi'

  const eligibleResults    = results.filter(r => r.eligible === true)
  const notEligibleResults = results.filter(r => r.eligible === false)
  const unclearResults     = results.filter(r => r.eligible === null)

  return (
    <div className="eligibility-results">
      {/* Summary banner */}
      <div className={`summary-banner ${summary.eligible_count > 0 ? 'summary-banner-positive' : 'summary-banner-neutral'}`}>
        <span className="summary-icon"><Icon name={summary.eligible_count > 0 ? 'check' : 'info'} size={21} /></span>
        <p className={`text-lg font-bold ${isHindi ? 'hindi-text' : ''}`}>
          {summary.eligible_count > 0
            ? (isHindi
                ? `आप ${summary.eligible_count} योजना के लिए पात्र हो सकते हैं।`
                : `You may qualify for ${summary.eligible_count} scheme(s).`)
            : (isHindi
                ? 'अभी कोई योजना मेल नहीं खाती। नीचे विवरण देखें।'
                : 'No matching schemes found right now. See details below.')}
        </p>
      </div>

      {/* Eligible schemes */}
      {eligibleResults.map(result => (
        <SchemeCard key={result.scheme_id} result={result} status="eligible" lang={lang} />
      ))}

      {/* Not eligible */}
      {notEligibleResults.map(result => (
        <SchemeCard key={result.scheme_id} result={result} status="not_eligible" lang={lang} />
      ))}

      {/* Unclear */}
      {unclearResults.map(result => (
        <SchemeCard key={result.scheme_id} result={result} status="unclear" lang={lang} />
      ))}

      {/* Demo data disclaimer — always shown */}
      <div className="results-disclaimer">
        <Icon name="info" size={16} />
        <span>{disclaimer}</span>
      </div>

      {/* Restart button */}
      <button
        type="button"
        onClick={onRestart}
        className="secondary-button results-restart"
      >
        {isHindi ? '🔄 फिर से जाँचें' : '🔄 Check Again'}
      </button>
    </div>
  )
}

/**
 * Individual scheme result card.
 */
function SchemeCard({ result, status, lang }) {
  const isHindi = lang === 'hi'

  const statusConfig = {
    eligible:     { className: 'scheme-result-eligible', icon: 'check', label: isHindi ? 'पात्र' : 'Eligible' },
    not_eligible: { className: 'scheme-result-not-eligible', icon: 'close', label: isHindi ? 'अपात्र' : 'Not eligible' },
    unclear:      { className: 'scheme-result-unclear', icon: 'info', label: isHindi ? 'अधिक जानकारी चाहिए' : 'Need more info' },
  }

  const cfg = statusConfig[status]

  return (
    <article className={`scheme-result-card ${cfg.className}`}>
      {/* Header */}
      <div className="scheme-result-heading">
        <h3 className={isHindi ? 'hindi-text' : ''}>
          <Icon name={cfg.icon} size={17} /> {result.name}
        </h3>
        <span className="scheme-status-badge">
          {cfg.label}
        </span>
      </div>

      {/* Benefit */}
      {status === 'eligible' && (
        <p className={`scheme-benefit ${isHindi ? 'hindi-text' : ''}`}>
          {result.benefit}
        </p>
      )}

      {/* Reasons */}
      <ul className="scheme-reasons">
        {result.reasons.slice(0, 3).map((reason, i) => (
          <li key={i} className={isHindi ? 'hindi-text' : ''}>
            <span aria-hidden="true">•</span> {reason}
          </li>
        ))}
      </ul>

      {/* Where to apply */}
      {status === 'eligible' && (
        <p className={`scheme-apply ${isHindi ? 'hindi-text' : ''}`}>
          {isHindi ? 'आवेदन करें: ' : 'Apply at: '}{result.apply_at}
        </p>
      )}
    </article>
  )
}
import Icon from './Icon.jsx'

