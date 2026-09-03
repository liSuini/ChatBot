import { Typography, Tag } from 'antd'
import type { Conversation, Message } from '../../types'
import MessageList from './MessageList'
import InputArea from './InputArea'

interface Props {
  conversation: Conversation
  messages: Message[]
}

export default function ChatWindow({ conversation, messages }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* 标题栏 */}
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
      </div>

      {/* 消息列表 */}
      <MessageList messages={messages} />

      {/* 输入区 */}
      <InputArea conversationId={conversation.id} />
    </div>
  )
}
