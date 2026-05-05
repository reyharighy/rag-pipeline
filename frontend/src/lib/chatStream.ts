import { API_BASE_URL } from '../config'

export type StreamEventType = 'update' | 'complete' | string

export interface StreamEnvelope {
  type: StreamEventType
  data: unknown
}

function findStringField(obj: unknown, key: string): string | null {
  if (obj === null || obj === undefined) return null

  if (typeof obj === 'object' && key in (obj as Record<string, unknown>)) {
    const v = (obj as Record<string, unknown>)[key]
    if (typeof v === 'string' && v.trim()) return v
  }

  if (typeof obj === 'object' && obj !== null) {
    for (const k of Object.keys(obj as object)) {
      const found = findStringField((obj as Record<string, unknown>)[k], key)
      if (found) return found
    }
  }

  return null
}

/** Prefer backend-provided rationale; otherwise a short human hint from graph updates. */
export function extractRationaleOrHint(data: unknown): string | null {
  const rationale = findStringField(data, 'rationale')
  if (rationale) return rationale

  if (data !== null && typeof data === 'object' && !Array.isArray(data)) {
    const keys = Object.keys(data as object)
    if (keys.includes('get_relevant_docs')) {
      return 'Retrieving relevant documents from the knowledge base…'
    }
    if (keys.includes('response')) {
      return 'Generating the assistant reply…'
    }
  }
  return null
}

function messageContent(msg: unknown): string | null {
  if (msg === null || msg === undefined) return null
  if (typeof msg === 'string') return msg
  if (typeof msg === 'object' && 'content' in (msg as object)) {
    const c = (msg as { content: unknown }).content
    if (typeof c === 'string') return c
    if (Array.isArray(c)) {
      const parts = c
        .map((p) => {
          if (typeof p === 'string') return p
          if (p && typeof p === 'object' && 'text' in p) {
            const t = (p as { text?: unknown }).text
            return typeof t === 'string' ? t : ''
          }
          return ''
        })
        .filter(Boolean)
      return parts.join('') || null
    }
  }
  return null
}

/** Best-effort assistant text from LangGraph "updates" payloads. */
export function extractAssistantTextFromUpdateData(data: unknown): string | null {
  if (data !== null && typeof data === 'object' && 'response' in (data as object)) {
    const resp = (data as { response?: unknown }).response
    if (resp && typeof resp === 'object' && 'messages' in (resp as object)) {
      const messages = (resp as { messages: unknown }).messages
      const list = Array.isArray(messages) ? messages : [messages]
      for (let i = list.length - 1; i >= 0; i--) {
        const m = list[i]
        if (
          m &&
          typeof m === 'object' &&
          ((m as { type?: string }).type === 'ai' || (m as { role?: string }).role === 'assistant')
        ) {
          const text = messageContent(m)
          if (text) return text
        }
      }
      const last = list[list.length - 1]
      const text = messageContent(last)
      if (text) return text
    }
  }
  return null
}

export async function* streamChat(chatInput: string): AsyncGenerator<StreamEnvelope, void, void> {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ chat_input: chatInput }),
  })

  if (!res.ok || !res.body) {
    const errText = await res.text().catch(() => res.statusText)
    throw new Error(errText || `Chat request failed (${res.status})`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''

    for (const raw of parts) {
      const line = raw.trim()
      if (!line) continue
      let parsed: StreamEnvelope
      try {
        parsed = JSON.parse(line) as StreamEnvelope
      } catch {
        continue
      }
      if (parsed && typeof parsed === 'object' && 'type' in parsed) {
        yield parsed
      }
    }
  }

  const tail = buffer.trim()
  if (tail) {
    try {
      const parsed = JSON.parse(tail) as StreamEnvelope
      if (parsed && typeof parsed === 'object' && 'type' in parsed) {
        yield parsed
      }
    } catch {
      /* ignore trailing garbage */
    }
  }
}
