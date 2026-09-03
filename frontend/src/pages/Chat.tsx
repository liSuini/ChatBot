import { Empty } from 'antd'
import { useChatStore } from '../stores/chatStore'
import ChatWindow from '../components/chat/ChatWindow'

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

  return <ChatWindow conversation={current} messages={messages} />
}
