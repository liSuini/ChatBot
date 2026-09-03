import type { Conversation } from '../types'
import { api } from './api'

export async function listConversations(): Promise<Conversation[]> {
  const resp = await api.get<Conversation[]>('/conversations')
  return resp.data
}

export async function createConversation(modelProvider: string): Promise<Conversation> {
  const resp = await api.post<Conversation>('/conversations', { model_provider: modelProvider })
  return resp.data
}

export async function getConversation(id: number): Promise<Conversation> {
  const resp = await api.get<Conversation>(`/conversations/${id}`)
  return resp.data
}

export async function renameConversation(id: number, title: string): Promise<Conversation> {
  const resp = await api.patch<Conversation>(`/conversations/${id}`, { title })
  return resp.data
}

export async function deleteConversation(id: number): Promise<void> {
  await api.delete(`/conversations/${id}`)
}
