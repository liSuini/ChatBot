import { useState, useCallback } from 'react'
import { Input, Button } from 'antd'
import { SendOutlined, StopOutlined } from '@ant-design/icons'
import { useChatStore } from '../../stores/chatStore'
import { useSSE } from '../../hooks/useSSE'
import * as chatApi from '../../services/chatApi'
import type { Message } from '../../types'

export default function InputArea({ conversationId }: { conversationId: number }) {
  const [value, setValue] = useState('')

  const isStreaming = useChatStore((s) => s.isStreaming)
  const startStreaming = useChatStore((s) => s.startStreaming)
  const appendToken = useChatStore((s) => s.appendToken)
  const finishStreaming = useChatStore((s) => s.finishStreaming)
  const stopStreaming = useChatStore((s) => s.stopStreaming)

  const { stream, stop } = useSSE()

  const handleSend = useCallback(async () => {
    const content = value.trim()
    if (!content || isStreaming) return

    setValue('')

    // 乐观添加用户消息
    const userMsg: Message = {
      id: Date.now(),
      role: 'user',
      content,
      tokens: 0,
      parent_message_id: null,
      created_at: new Date().toISOString(),
    }
    startStreaming(conversationId, userMsg)

    await stream(
      `/api/v1/conversations/${conversationId}/messages`,
      { content },
      {
        onToken: (token) => appendToken(token),
        onDone: (data) => {
          finishStreaming(conversationId, {
            id: data.message_id,
            role: 'assistant',
            content: data.content,
            tokens: data.tokens,
            parent_message_id: null,
            created_at: new Date().toISOString(),
          })
        },
        onError: () => {
          stopStreaming()
        },
      },
    )
  }, [value, isStreaming, conversationId, startStreaming, appendToken, finishStreaming, stopStreaming, stream])

  const handleStop = useCallback(async () => {
    stop()
    await chatApi.stopGeneration(conversationId)
  }, [stop, conversationId])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{ display: 'flex', gap: 8, padding: '12px 0', borderTop: '1px solid #f0f0f0' }}>
      <Input.TextArea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
        autoSize={{ minRows: 1, maxRows: 6 }}
        disabled={isStreaming}
        style={{ flex: 1 }}
      />
      {isStreaming ? (
        <Button
          danger
          icon={<StopOutlined />}
          onClick={handleStop}
          style={{ alignSelf: 'flex-end' }}
        >
          停止
        </Button>
      ) : (
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          disabled={!value.trim()}
          style={{ alignSelf: 'flex-end' }}
        >
          发送
        </Button>
      )}
    </div>
  )
}
