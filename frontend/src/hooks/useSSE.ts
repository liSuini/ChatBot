/**
 * useSSE: 基于 fetch + ReadableStream 的 SSE 流式接收 Hook
 * EventSource 不支持 POST + JWT，因此用 fetch 手动解析
 */

import { useRef, useCallback } from 'react'
import { streamSSE, type SSECallbacks } from '../utils/sse-stream'

export function useSSE() {
  const abortRef = useRef<AbortController | null>(null)

  const stream = useCallback(async (url: string, body: unknown, callbacks: SSECallbacks) => {
    const controller = new AbortController()
    abortRef.current = controller
    await streamSSE(url, body, callbacks, controller)
    abortRef.current = null
  }, [])

  const stop = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { stream, stop }
}
