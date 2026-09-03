import type { DocumentItem } from '../types'
import { api } from './api'

export async function listDocuments(): Promise<DocumentItem[]> {
  const resp = await api.get<DocumentItem[]>('/documents')
  return resp.data
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData()
  formData.append('file', file)
  const resp = await api.post<DocumentItem>('/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return resp.data
}

export async function getDocumentStatus(id: number): Promise<DocumentItem> {
  const resp = await api.get<DocumentItem>(`/documents/${id}/status`)
  return resp.data
}

export async function deleteDocument(id: number): Promise<void> {
  await api.delete(`/documents/${id}`)
}
