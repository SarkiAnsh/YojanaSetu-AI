/**
 * ConsentBanner.jsx — Privacy consent notice shown before the user starts.
 *
 * Key principle: Be transparent about what data is collected and why.
 * Users should understand before they share anything.
 *
 * Props:
 *   lang      : "en" | "hi"
 *   onAccept  : function — user clicked "I understand, let's start"
 */
export default function ConsentBanner({ lang, onAccept }) {
  const isHindi = lang === 'hi'

  return (
    <div className="consent-card">
      {/* Icon + Title */}
      <div className="consent-heading">
        <span className="consent-icon"><Icon name="lock" size={19} /></span>
        <h3 className={isHindi ? 'hindi-text' : ''}>
          {isHindi ? 'आपकी जानकारी की सुरक्षा' : 'Your Privacy Matters'}
        </h3>
      </div>

      {/* What we collect */}
      <ul className={`consent-list ${isHindi ? 'hindi-text' : ''}`}>
        <li><Icon name="check" size={15} /> {isHindi
          ? 'हम केवल पात्रता जाँचने के लिए सवाल पूछेंगे'
          : 'We only ask questions needed to check your eligibility'}</li>
        <li><Icon name="check" size={15} /> {isHindi
          ? 'कोई आधार, PAN, या बैंक नंबर नहीं माँगा जाएगा'
          : 'No Aadhaar, PAN, or bank number will be asked'}</li>
        <li><Icon name="check" size={15} /> {isHindi
          ? 'आपकी जानकारी बिना इजाजत सेव नहीं होगी'
          : 'Your data will not be saved without your permission'}</li>
        <li><Icon name="check" size={15} /> {isHindi
          ? 'यह डेमो डेटा है — कोई सरकारी डेटाबेस नहीं'
          : 'This uses demo data — no real government database'}</li>
      </ul>

      {/* Accept button */}
      <button
        type="button"
        onClick={onAccept}
        className={`consent-accept ${isHindi ? 'hindi-text' : ''}`}
      >
        {isHindi ? '✅ ठीक है, शुरू करें' : '✅ I understand, let\'s start'}
      </button>
    </div>
  )
}
import Icon from './Icon.jsx'

