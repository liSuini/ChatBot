import { Button, Dropdown, Input, Modal } from 'antd'
import { useState } from 'react'

interface Props {
  title: string
  active: boolean
  onClick: () => void
  onRename: (title: string) => void
  onDelete: () => void
}

export default function ConversationItem({ title, active, onClick, onRename, onDelete }: Props) {
  const [renaming, setRenaming] = useState(false)
  const [renameValue, setRenameValue] = useState(title)

  const startRename = () => {
    setRenameValue(title)
    setRenaming(true)
  }

  const submitRename = () => {
    const trimmed = renameValue.trim()
    if (trimmed && trimmed !== title) onRename(trimmed)
    setRenaming(false)
  }

  const confirmDelete = () => {
    Modal.confirm({
      title: `删除「${title}」？`,
      content: '该会话的全部消息将被删除',
      okText: '删除',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: () => onDelete(),
    })
  }

  if (renaming) {
    return (
      <div style={{ padding: '4px 8px' }} onClick={(e) => e.stopPropagation()}>
        <Input
          size="small"
          value={renameValue}
          autoFocus
          onChange={(e) => setRenameValue(e.target.value)}
          onPressEnter={submitRename}
          onBlur={submitRename}
        />
      </div>
    )
  }

  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 4,
        padding: '8px 8px 8px 12px',
        margin: '2px 0',
        borderRadius: 8,
        cursor: 'pointer',
        background: active ? '#e6f4ff' : 'transparent',
      }}
    >
      <span
        style={{
          flex: 1,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          fontSize: 13,
        }}
      >
        {title}
      </span>
      <Dropdown
        menu={{
          items: [
            { key: 'rename', label: '重命名' },
            { key: 'delete', label: '删除', danger: true },
          ],
          onClick: ({ key, domEvent }) => {
            domEvent.stopPropagation()
            if (key === 'rename') startRename()
            else if (key === 'delete') confirmDelete()
          },
        }}
        trigger={['click']}
      >
        <Button
          type="text"
          size="small"
          onClick={(e) => e.stopPropagation()}
          style={{ minWidth: 24, color: '#999' }}
        >
          ···
        </Button>
      </Dropdown>
    </div>
  )
}
