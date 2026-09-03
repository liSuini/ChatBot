import type { AuthResponse, User } from '../types'
import { api } from './api'

export async function register(username: string, password: string): Promise<AuthResponse> {
  const resp = await api.post<AuthResponse>('/auth/register', { username, password })
  return resp.data
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const resp = await api.post<AuthResponse>('/auth/login', { username, password })
  return resp.data
}

export async function me(): Promise<User> {
  const resp = await api.get<User>('/auth/me')
  return resp.data
}
