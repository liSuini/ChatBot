import type { Provider } from '../types'
import { api } from './api'

export async function listProviders(): Promise<Provider[]> {
  const resp = await api.get<Provider[]>('/llm/providers')
  return resp.data
}
