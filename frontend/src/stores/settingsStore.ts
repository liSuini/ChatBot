import { create } from 'zustand'
import type { Provider } from '../types'
import { listProviders } from '../services/llmApi'

interface SettingsState {
  /** 当前选中的 provider，新建会话时绑定 */
  provider: string
  providers: Provider[]
  setProvider: (provider: string) => void
  loadProviders: () => Promise<void>
}

export const useSettingsStore = create<SettingsState>()((set) => ({
  provider: 'mock',
  providers: [],
  setProvider: (provider) => set({ provider }),
  loadProviders: async () => {
    const providers = await listProviders()
    set((state) => ({
      providers,
      // 当前选择的 provider 不可用时重置为列表第一个
      provider: providers.some((p) => p.name === state.provider)
        ? state.provider
        : (providers[0]?.name ?? 'mock'),
    }))
  },
}))
