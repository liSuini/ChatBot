import { Button, Empty } from 'antd'
import { useEffect } from 'react'
import { useChatStore } from '../../stores/chatStore'
import { useSettingsStore } from '../../stores/settingsStore'
import ConversationItem from './ConversationItem'

export default function ConversationList() {
  const conversations = useChatStore((s) => s.conversations)
  const currentId = useChatStore((s) => s.currentId)
  const loadConversations = useChatStore((s) => s.loadConversations)
  const selectConversation = useChatStore((s) => s.selectConversation)
  const createConversation = useChatStore((s) => s.createConversation)
  const renameConversation = useChatStore((s) => s.renameConversation)
  const deleteConversation = useChatStore((s) => s.deleteConversation)
  const provider = useSettingsStore((s) => s.provider)

  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: '0 8px 8px' }}>
      <Button
        block
        type="primary"
        style={{ marginBottom: 8 }}
        onClick={() => createConversation(provider)}
      >
        新建对话
      </Button>
      {conversations.length === 0 ? (
        <Empty description="暂无会话" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        conversations.map((c) => (
          <ConversationItem
            key={c.id}
            title={c.title}
            active={c.id === currentId}
            onClick={() => selectConversation(c.id)}
            onRename={(title) => renameConversation(c.id, title)}
            onDelete={() => deleteConversation(c.id)}
          />
        ))
      )}
    </div>
  )
}
