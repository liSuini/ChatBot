import { useState } from 'react'
import { Input, Button } from 'antd'
import { EditOutlined, ReloadOutlined } from '@ant-design/icons'
import type { Message as MessageType } from '../../types'
import { useChatStore } from '../../stores/chatStore'
import MarkdownRenderer from './MarkdownRenderer'
import StreamingCursor from './StreamingCursor'

interface Props {
  message: MessageType
  conversationId: number
  streaming?: boolean
}

export default function MessageBubble({ message, conversationId, streaming }: Props) {
  const isUser = message.role === 'user'
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState(message.content)
  const isStreaming = useChatStore((s) => s.isStreaming)
  const regenerateMessage = useChatStore((s) => s.regenerateMessage)
  const editMessage = useChatStore((s) => s.editMessage)

  const submitEdit = () => {
    const trimmed = editValue.trim()
    if (trimmed && trimmed !== message.content) {
      editMessage(conversationId, message.id, trimmed)
    }
    setEditing(false)
  }

  if (editing) {
    return (
      <div style={{ margin: '8px 0', textAlign: 'right' }}>
        <div style={{ display: 'inline-block', maxWidth: '70%', textAlign: 'left' }}>
          <Input.TextArea
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            autoSize={{ minRows: 1, maxRows: 6 }}
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitEdit() }
              if (e.key === 'Escape') setEditing(false)
            }}
          />
          <div style={{ marginTop: 4, display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <Button size="small" onClick={() => setEditing(false)}>取消</Button>
            <Button size="small" type="primary" onClick={submitEdit}>发送</Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ margin: '8px 0', textAlign: isUser ? 'right' : 'left' }}>
      <div
        style={{
          background: isUser ? '#e6f4ff' : '#f5f5f5',
          padding: '8px 12px',
          borderRadius: 8,
          display: 'inline-block',
          maxWidth: '70%',
          textAlign: 'left',
          wordBreak: 'break-word',
          ...(isUser ? { whiteSpace: 'pre-wrap' } : {}),
        }}
      >
        {isUser ? (
          message.content
        ) : (
          <div className="markdown-body">
            <MarkdownRenderer content={message.content} />
            {streaming && <StreamingCursor />}
          </div>
        )}
      </div>
      {!streaming && !isStreaming && (
        <div style={{ marginTop: 2, display: 'flex', gap: 8, justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
          {isUser ? (
            <Button size="small" type="text" icon={<EditOutlined />} onClick={() => { setEditValue(message.content); setEditing(true) }}>
              编辑
            </Button>
          ) : (
            <Button size="small" type="text" icon={<ReloadOutlined />} onClick={() => regenerateMessage(conversationId, message.id)}>
              重新生成
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
