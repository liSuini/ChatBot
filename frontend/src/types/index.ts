export interface User {
  id: number
  username: string
}

export interface AuthResponse {
  access_token: string
  // 注册接口不返回 refresh_token，登录接口返回
  refresh_token?: string
  token_type: string
  user: User
}

export interface Message {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  tokens: number
  parent_message_id: number | null
  created_at: string
}

export interface Conversation {
  id: number
  title: string
  model_provider: string
  system_prompt: string | null
  created_at: string
  updated_at: string
  messages?: Message[]
}

export interface DocumentItem {
  id: number
  filename: string
  file_type: string
  file_size: number
  status: 'processing' | 'ready' | 'failed'
  chunk_count: number
  created_at: string
}

export interface Provider {
  name: string
  display_name: string
  models: string[]
}
