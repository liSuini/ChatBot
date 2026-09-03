import { create } from 'zustand'
import type { Provider } from '../types'
import { listProviders } from '../services/llmApi'

interface SettingsState {
  /** 当前选中的 provider，新建会话时绑定 */
  provider: string
  providers: Provider[]
  /** RAG 开关：发送消息时是否注入文档检索结果 */
  ragEnabled: boolean
  setProvider: (provider: string) => void
  setRagEnabled: (enabled: boolean) => void
  loadProviders: () => Promise<void>
}

export const useSettingsStore = create<SettingsState>()((set) => ({
  provider: 'mock',
  providers: [],
  ragEnabled: false,
  setProvider: (provider) => set({ provider }),
  setRagEnabled: (enabled) => set({ ragEnabled: enabled }),
  loadProviders: async () => {
    const providers = await listProviders()
    set((state) => ({
      providers,
      provider: providers.some((p) => p.name === state.provider)
        ? state.provider
        : (providers[0]?.name ?? 'mock'),
    }))
  },
}))
