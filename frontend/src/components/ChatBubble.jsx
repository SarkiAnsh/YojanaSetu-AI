import Icon from './Icon.jsx'

/**
 * ChatBubble.jsx — A single message bubble in the conversation.
 *
 * Props:
 *   role   : "bot" | "user"       — who sent the message
 *   text   : string               — the message content
 *   isHindi: boolean              — apply Hindi font styling
 */
export default function ChatBubble({ role, text, isHindi }) {
  const isBot = role === 'bot'

  return (
    <div className={`message-row ${isBot ? 'message-row-bot' : 'message-row-user'}`}>
      {isBot && (
        <div className="assistant-avatar message-avatar">
          <Icon name="assistant" size={17} />
        </div>
      )}
      <div
        className={`message-bubble ${isBot ? 'message-bubble-bot' : 'message-bubble-user'} ${isHindi ? 'hindi-text' : ''}`}
      >
        {text}
      </div>
    </div>
  )
}
