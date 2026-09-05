import { Button, Empty, Skeleton } from 'antd'
import { useEffect, useState } from 'react'
import { ReloadOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useChatStore } from '../../stores/chatStore'
import { useSettingsStore } from '../../stores/settingsStore'
import ConversationItem from './ConversationItem'

export default function ConversationList() {
  const navigate = useNavigate()
  const conversations = useChatStore((s) => s.conversations)
  const currentId = useChatStore((s) => s.currentId)
  const loadConversations = useChatStore((s) => s.loadConversations)
  const selectConversation = useChatStore((s) => s.selectConversation)
  const createConversation = useChatStore((s) => s.createConversation)
  const renameConversation = useChatStore((s) => s.renameConversation)
  const deleteConversation = useChatStore((s) => s.deleteConversation)
  const provider = useSettingsStore((s) => s.provider)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const load = async () => {
    setLoading(true)
    setError(false)
    try {
      await loadConversations()
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [loadConversations])

  const handleSelect = async (id: number) => {
    await selectConversation(id)
    navigate('/chat')
  }

  const handleCreate = async () => {
    await createConversation(provider)
    navigate('/chat')
  }

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: '0 8px 8px' }}>
      <Button
        block
        type="primary"
        style={{ marginBottom: 8 }}
        onClick={handleCreate}
      >
        新建对话
      </Button>
      {loading ? (
        <Skeleton active paragraph={{ rows: 4 }} />
      ) : error ? (
        <div style={{ textAlign: 'center', padding: 16 }}>
          <Empty description="加载失败" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          <Button size="small" icon={<ReloadOutlined />} onClick={load} style={{ marginTop: 8 }}>
            重试
          </Button>
        </div>
      ) : conversations.length === 0 ? (
        <Empty description="暂无会话" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        conversations.map((c) => (
          <ConversationItem
            key={c.id}
            title={c.title}
            active={c.id === currentId}
            onClick={() => handleSelect(c.id)}
            onRename={(title) => renameConversation(c.id, title)}
            onDelete={() => deleteConversation(c.id)}
          />
        ))
      )}
    </div>
  )
}
