import { create } from 'zustand'
import type { Conversation, Message } from '../types'
import * as chatApi from '../services/chatApi'

interface ChatState {
  conversations: Conversation[]
  currentId: number | null
  messagesMap: Record<number, Message[]>
  loadConversations: () => Promise<void>
  selectConversation: (id: number) => Promise<void>
  createConversation: (modelProvider: string) => Promise<void>
  renameConversation: (id: number, title: string) => Promise<void>
  deleteConversation: (id: number) => Promise<void>
  setMessages: (conversationId: number, messages: Message[]) => void
}

export const useChatStore = create<ChatState>()((set, get) => ({
  conversations: [],
  currentId: null,
  messagesMap: {},

  loadConversations: async () => {
    const conversations = await chatApi.listConversations()
    set({ conversations })
  },

  selectConversation: async (id) => {
    set({ currentId: id })
    // 首次选中时拉取会话详情（含消息历史）
    if (get().messagesMap[id] === undefined) {
      const detail = await chatApi.getConversation(id)
      set((s) => ({ messagesMap: { ...s.messagesMap, [id]: detail.messages ?? [] } }))
    }
  },

  createConversation: async (modelProvider) => {
    const conv = await chatApi.createConversation(modelProvider)
    set((s) => ({
      conversations: [conv, ...s.conversations],
      currentId: conv.id,
      messagesMap: { ...s.messagesMap, [conv.id]: [] },
    }))
  },

  renameConversation: async (id, title) => {
    const updated = await chatApi.renameConversation(id, title)
    set((s) => ({
      conversations: s.conversations
        .map((c) => (c.id === id ? { ...c, ...updated } : c))
        .sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1)),
    }))
  },

  deleteConversation: async (id) => {
    await chatApi.deleteConversation(id)
    set((s) => {
      const conversations = s.conversations.filter((c) => c.id !== id)
      const messagesMap = { ...s.messagesMap }
      delete messagesMap[id]
      // 删除当前会话时自动选中列表第一个
      const currentId = s.currentId === id ? (conversations[0]?.id ?? null) : s.currentId
      return { conversations, messagesMap, currentId }
    })
  },

  setMessages: (conversationId, messages) =>
    set((s) => ({ messagesMap: { ...s.messagesMap, [conversationId]: messages } })),
}))
