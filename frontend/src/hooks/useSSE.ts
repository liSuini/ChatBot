/**
 * useSSE: 基于 fetch + ReadableStream 的 SSE 流式接收 Hook
 * EventSource 不支持 POST + JWT，因此用 fetch 手动解析
 */

import { useRef, useCallback } from 'react'
import { SSEParser } from '../utils/sse-parser'
import { useAuthStore } from '../stores/authStore'

interface SSECallbacks {
  onStart?: (data: { message_id: number }) => void
  onToken?: (content: string) => void
  onDone?: (data: { message_id: number; content: string; tokens: number }) => void
  onError?: (message: string) => void
}

export function useSSE() {
  const abortRef = useRef<AbortController | null>(null)

  const stream = useCallback(
    async (url: string, body: unknown, callbacks: SSECallbacks) => {
      const token = useAuthStore.getState().token
      const parser = new SSEParser()
      const controller = new AbortController()
      abortRef.current = controller

      try {
        const resp = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(body),
          signal: controller.signal,
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
        if (err instanceof DOMException && err.name === 'AbortError') {
          return // 用户主动取消，不算错误
        }
        callbacks.onError?.(err instanceof Error ? err.message : '未知错误')
      } finally {
        abortRef.current = null
      }
    },
    [],
  )

  const stop = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { stream, stop }
}
