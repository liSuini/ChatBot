import type { Message as MessageType } from '../../types'

interface Props {
  message: MessageType
  streaming?: boolean
}

export default function MessageBubble({ message, streaming }: Props) {
  const isUser = message.role === 'user'

  return (
    <div style={{ margin: '8px 0', textAlign: isUser ? 'right' : 'left' }}>
      <span
        style={{
          background: isUser ? '#e6f4ff' : '#f5f5f5',
          padding: '8px 12px',
          borderRadius: 8,
          display: 'inline-block',
          maxWidth: '70%',
          whiteSpace: 'pre-wrap',
          textAlign: 'left',
          wordBreak: 'break-word',
        }}
      >
        {message.content}
        {streaming && (
          <span
            style={{
              display: 'inline-block',
              width: 6,
              height: 16,
              background: '#999',
              marginLeft: 2,
              animation: 'blink 1s step-end infinite',
              verticalAlign: 'text-bottom',
            }}
          />
        )}
      </span>
    </div>
  )
}
