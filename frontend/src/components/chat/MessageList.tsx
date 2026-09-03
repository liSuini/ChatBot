import { useEffect, useRef } from 'react'
import { Empty, Skeleton } from 'antd'
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
  const loadingMessages = useChatStore((s) => s.loadingMessages)
  const bottomRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const userScrolledRef = useRef(false)

  // 检测用户手动滚动
  const handleScroll = () => {
    const el = containerRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80
    userScrolledRef.current = !atBottom
  }

  useEffect(() => {
    // 只在用户未手动上滚时自动滚动
    if (!userScrolledRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages.length, streamingContent])

  if (loadingMessages) {
    return (
      <div style={{ flex: 1, padding: '12px 0' }}>
        <Skeleton active avatar paragraph={{ rows: 2 }} />
        <Skeleton active avatar={{ size: 'small' }} paragraph={{ rows: 2 }} style={{ marginTop: 16 }} />
      </div>
    )
  }

  if (messages.length === 0 && !isStreaming) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Empty description="暂无消息" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </div>
    )
  }

  return (
    <div ref={containerRef} onScroll={handleScroll} style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
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
