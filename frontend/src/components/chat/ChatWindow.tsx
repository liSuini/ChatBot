import { Typography, Tag, Switch } from 'antd'
import type { Conversation, Message } from '../../types'
import { useSettingsStore } from '../../stores/settingsStore'
import MessageList from './MessageList'
import InputArea from './InputArea'

interface Props {
  conversation: Conversation
  messages: Message[]
}

export default function ChatWindow({ conversation, messages }: Props) {
  const ragEnabled = useSettingsStore((s) => s.ragEnabled)
  const setRagEnabled = useSettingsStore((s) => s.setRagEnabled)

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
        <Typography.Text strong>{conversation.title}</Typography.Text>
        <Tag color="blue">{conversation.model_provider}</Tag>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Typography.Text style={{ fontSize: 13, color: '#666' }}>RAG</Typography.Text>
          <Switch size="small" checked={ragEnabled} onChange={setRagEnabled} />
        </div>
      </div>

      <MessageList messages={messages} conversationId={conversation.id} />

      <InputArea conversationId={conversation.id} />
    </div>
  )
}
