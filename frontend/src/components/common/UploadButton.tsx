import { useState } from 'react'
import { Upload, message } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import { uploadDocument } from '../../services/documentApi'

const { Dragger } = Upload

const ACCEPT = '.pdf,.docx,.txt,.md'
const MAX_SIZE = 10 * 1024 * 1024 // 10MB

interface Props {
  onUploaded: () => void
}

/** 拖拽上传按钮：文件校验 + 调用上传 API */
export default function UploadButton({ onUploaded }: Props) {
  const [loading, setLoading] = useState(false)

  const handleUpload = async (file: File) => {
    // 文件校验
    const ext = file.name.toLowerCase().match(/\.[^.]+$/)?.[0] ?? ''
    if (!['.pdf', '.docx', '.txt', '.md'].includes(ext)) {
      message.error('不支持的文件类型，仅支持 PDF/DOCX/TXT/MD')
      return Upload.LIST_IGNORE
    }
    if (file.size > MAX_SIZE) {
      message.error('文件超过 10MB 限制')
      return Upload.LIST_IGNORE
    }

    setLoading(true)
    try {
      await uploadDocument(file)
      message.success(`${file.name} 上传成功`)
      onUploaded()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '上传失败'
      message.error(msg)
    } finally {
      setLoading(false)
    }
    return false // 阻止默认上传行为
  }

  return (
    <Dragger
      accept={ACCEPT}
      multiple={false}
      showUploadList={false}
      beforeUpload={handleUpload}
      disabled={loading}
      style={{ marginBottom: 16 }}
    >
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">{loading ? '上传中...' : '点击或拖拽文件上传'}</p>
      <p className="ant-upload-hint">支持 PDF / DOCX / TXT / MD，单文件不超过 10MB</p>
    </Dragger>
  )
}
