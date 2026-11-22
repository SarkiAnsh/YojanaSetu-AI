import Icon from './Icon.jsx'

/**
 * VoiceButton.jsx — Microphone button for voice input.
 *
 * Shows a pulsing animation while listening.
 * Falls back to text input if voice is not supported.
 *
 * Props:
 *   isListening : boolean   — is mic currently active?
 *   onPress     : function  — called when button is clicked
 *   lang        : "en"|"hi"
 */
export default function VoiceButton({ isListening, onPress, lang }) {
  const label = lang === 'hi'
    ? (isListening ? 'सुनना बंद करें' : 'बोलकर जवाब दें')
    : (isListening ? 'Stop listening' : 'Answer by voice')

  return (
    <button
      type="button"
      onClick={onPress}
      className={`voice-button ${isListening ? 'voice-button-listening mic-active' : ''}`}
      title={label}
      aria-label={label}
      aria-pressed={isListening}
    >
      <Icon name="mic" size={21} />
      <span className="sr-only">
        {lang === 'hi'
          ? (isListening ? 'माइक्रोफ़ोन चालू है' : 'माइक्रोफ़ोन बंद है')
          : (isListening ? 'Microphone is listening' : 'Microphone is stopped')}
      </span>
    </button>
  )
}
