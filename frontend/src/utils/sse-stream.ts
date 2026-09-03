/**
 * SSE 流式请求工具函数：fetch + ReadableStream + SSE 解析
 * 供 useSSE hook 和 chatStore 共用
 */

import { SSEParser } from './sse-parser'
import { useAuthStore } from '../stores/authStore'

export interface SSECallbacks {
  onStart?: (data: { message_id: number }) => void
  onToken?: (content: string) => void
  onDone?: (data: { message_id: number; content: string; tokens: number }) => void
  onError?: (message: string) => void
}

export async function streamSSE(
  url: string,
  body: unknown,
  callbacks: SSECallbacks,
  controller?: AbortController,
): Promise<void> {
  const token = useAuthStore.getState().token
  const parser = new SSEParser()

  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
      signal: controller?.signal,
    })

    if (!resp.ok) {
      callbacks.onError?.(`HTTP ${resp.status}`)
      return
    }

    const reader = resp.body!.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const events = parser.feed(chunk)

      for (const evt of events) {
        const data = evt.data ? JSON.parse(evt.data) : {}
        switch (evt.event) {
          case 'start':
            callbacks.onStart?.(data)
            break
          case 'token':
            callbacks.onToken?.(data.content)
            break
          case 'done':
            callbacks.onDone?.(data)
            break
          case 'error':
            callbacks.onError?.(data.message)
            break
        }
      }
    }
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') return
    callbacks.onError?.(err instanceof Error ? err.message : '未知错误')
  }
}
