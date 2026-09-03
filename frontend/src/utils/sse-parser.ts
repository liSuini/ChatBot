/**
 * SSE 协议解析器：从 ReadableStream 的 chunk 中解析出完整事件
 *
 * SSE 格式：
 * event: start
 * data: {"message_id": 123}
 *
 * event: token
 * data: {"content": "你"}
 * ...
 */

export interface SSEEvent {
  event: string
  data: string
}

export class SSEParser {
  private buffer = ''

  /** 喂入一个 chunk，返回已完成的事件列表 */
  feed(chunk: string): SSEEvent[] {
    this.buffer += chunk
    const events: SSEEvent[] = []

    while (true) {
      const idx = this.buffer.indexOf('\n\n')
      if (idx === -1) break

      const block = this.buffer.slice(0, idx)
      this.buffer = this.buffer.slice(idx + 2)

      let event = ''
      let data = ''
      for (const line of block.split('\n')) {
        if (line.startsWith('event:')) {
          event = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          data = line.slice(5).trim()
        }
      }
      if (event) {
        events.push({ event, data })
      }
    }

    return events
  }

  reset() {
    this.buffer = ''
  }
}
