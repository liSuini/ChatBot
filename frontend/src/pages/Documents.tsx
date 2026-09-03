import { useEffect, useState, useCallback } from 'react'
import { Table, Tag, Button, Popconfirm, message } from 'antd'
import { DeleteOutlined, ReloadOutlined } from '@ant-design/icons'
import type { DocumentItem } from '../types'
import * as docApi from '../services/documentApi'
import UploadButton from '../components/common/UploadButton'

const STATUS_COLOR: Record<string, string> = {
  ready: 'green',
  processing: 'orange',
  failed: 'red',
}

export default function Documents() {
  const [docs, setDocs] = useState<DocumentItem[]>([])
  const [loading, setLoading] = useState(false)

  const loadDocs = useCallback(async () => {
    setLoading(true)
    try {
      const list = await docApi.listDocuments()
      setDocs(list)
    } catch {
      message.error('加载文档列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDocs()
  }, [loadDocs])

  const handleDelete = async (id: number) => {
    try {
      await docApi.deleteDocument(id)
      setDocs((prev) => prev.filter((d) => d.id !== id))
      message.success('删除成功')
    } catch {
      message.error('删除失败')
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div style={{ maxWidth: 900 }}>
      <h2 style={{ marginBottom: 16 }}>文档管理</h2>
      <UploadButton onUploaded={() => loadDocs()} />
      <Table
        rowKey="id"
        loading={loading}
        dataSource={docs}
        pagination={{ pageSize: 10 }}
        locale={{ emptyText: '暂无文档，上传一个试试吧' }}
        columns={[
          { title: '文件名', dataIndex: 'filename', ellipsis: true },
          { title: '类型', dataIndex: 'file_type', width: 80 },
          {
            title: '大小',
            dataIndex: 'file_size',
            width: 100,
            render: (size: number) => formatSize(size),
          },
          {
            title: '状态',
            dataIndex: 'status',
            width: 100,
            render: (status: string) => (
              <Tag color={STATUS_COLOR[status] ?? 'default'}>
                {status === 'ready' ? '就绪' : status === 'processing' ? '处理中' : '失败'}
              </Tag>
            ),
          },
          { title: '分块', dataIndex: 'chunk_count', width: 70 },
          {
            title: '上传时间',
            dataIndex: 'created_at',
            width: 180,
            render: (t: string) => new Date(t).toLocaleString('zh-CN'),
          },
          {
            title: '操作',
            width: 80,
            render: (_: unknown, record: DocumentItem) => (
              <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
                <Button size="small" danger icon={<DeleteOutlined />}>
                  删除
                </Button>
              </Popconfirm>
            ),
          },
        ]}
      />
      <div style={{ marginTop: 8 }}>
        <Button size="small" type="text" icon={<ReloadOutlined />} onClick={loadDocs}>
          刷新
        </Button>
      </div>
    </div>
  )
}
