import { useEffect, useRef } from 'react'
import { Empty } from 'antd'
import type { Message } from '../../types'
import { useChatStore } from '../../stores/chatStore'
import MessageBubble from './MessageBubble'

interface Props {
  messages: Message[]
  conversationId: number
}

export default function MessageList({ messages, conversationId }: Props) {
  const isStreaming = useChatStore((s) => s.isStreaming)
  const streamingContent = useChatStore((s) => s.streamingContent)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, streamingContent])

  if (messages.length === 0 && !isStreaming) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Empty description="暂无消息" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </div>
    )
  }

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} conversationId={conversationId} />
      ))}
      {isStreaming && streamingContent && (
        <MessageBubble
          message={{
            id: -1, role: 'assistant', content: streamingContent,
            tokens: 0, parent_message_id: null, created_at: new Date().toISOString(),
          }}
          conversationId={conversationId}
          streaming
        />
      )}
      <div ref={bottomRef} />
    </div>
  )
}
