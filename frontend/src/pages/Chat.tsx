import { Empty, Tag, Typography } from 'antd'
import { useChatStore } from '../stores/chatStore'

export default function Chat() {
  const conversations = useChatStore((s) => s.conversations)
  const currentId = useChatStore((s) => s.currentId)
  const messagesMap = useChatStore((s) => s.messagesMap)

  const current = conversations.find((c) => c.id === currentId)
  const messages = currentId ? (messagesMap[currentId] ?? []) : []

  if (!current) {
    return (
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Empty description="选择或新建一个对话开始" />
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div
        style={{
          padding: '8px 0 12px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <Typography.Text strong>{current.title}</Typography.Text>
        <Tag color="blue">{current.model_provider}</Tag>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        {messages.length === 0 ? (
          <Empty description="暂无消息" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          messages.map((m) => (
            <div
              key={m.id}
              style={{
                margin: '8px 0',
                textAlign: m.role === 'user' ? 'right' : 'left',
              }}
            >
              <span
                style={{
                  background: m.role === 'user' ? '#e6f4ff' : '#f5f5f5',
                  padding: '6px 10px',
                  borderRadius: 8,
                  display: 'inline-block',
                  maxWidth: '70%',
                  whiteSpace: 'pre-wrap',
                  textAlign: 'left',
                }}
              >
                {m.content}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
