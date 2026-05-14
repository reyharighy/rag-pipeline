import { API_BASE_URL } from '../config'

export type StreamEventType = 'update' | 'complete' | 'session' | string

export interface StreamEnvelope {
  type: StreamEventType
  data: unknown
}

function findStringField(obj: unknown, key: string): string | null {
  if (obj === null || obj === undefined) {
    return null
  }

  if (typeof obj === 'object' && key in (obj as Record<string, unknown>)) {
    const v = (obj as Record<string, unknown>)[key]

    if (typeof v === 'string' && v.trim()) {
      return v
    }
  }

  if (typeof obj === 'object' && obj !== null) {
    const keys = Object.keys(obj as object)

    for (const k of keys) {
      const found = findStringField((obj as Record<string, unknown>)[k], key)

      if (found) {
        return found
      }
    }
  }

  return null
}

export function extractRationaleOrHint(data: unknown): string | null {
  const rationale = findStringField(data, 'rationale')

  if (rationale) {
    return rationale
  }

  if (data !== null && typeof data === 'object' && !Array.isArray(data)) {
    const keys = Object.keys(data as object)

    if (keys.includes('refine_query')) {
      return 'Refining the search query for retrieval…'
    }

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
  if (msg === null || msg === undefined) {
    return null
  }

  if (typeof msg === 'string') {
    return msg
  }

  if (typeof msg === 'object' && 'content' in (msg as object)) {
    const c = (msg as { content: unknown }).content

    if (typeof c === 'string') {
      return c
    }

    if (Array.isArray(c)) {
      const parts = c
        .map((p) => {
          if (typeof p === 'string') {
            return p
          }

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

          if (text) {
            return text
          }
        }
      }

      const last = list[list.length - 1]
      const text = messageContent(last)

      if (text) {
        return text
      }
    }
  }

  return null
}

const CHAT_SESSION_STORAGE_KEY = 'chat-session-id'

export function getStoredChatSessionId(): string | null {
  if (typeof localStorage === 'undefined') {
    return null
  }

  return localStorage.getItem(CHAT_SESSION_STORAGE_KEY)
}

export function setStoredChatSessionId(sessionId: string): void {
  if (typeof localStorage === 'undefined') {
    return
  }

  localStorage.setItem(CHAT_SESSION_STORAGE_KEY, sessionId)
}

export interface ChatHistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export async function fetchChatHistory(sessionId: string): Promise<ChatHistoryMessage[]> {
  const url = new URL(`${API_BASE_URL}/chat/history`)
  url.searchParams.set('session_id', sessionId.trim())

  const res = await fetch(url.toString())

  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText)

    throw new Error(errText || `Failed to load chat history (${res.status})`)
  }

  const data = (await res.json()) as { messages?: ChatHistoryMessage[] }

  return Array.isArray(data.messages) ? data.messages : []
}

export async function* streamChat(
  chatInput: string,
  sessionId?: string | null,
): AsyncGenerator<StreamEnvelope, void, void> {
  const body: { chat_input: string; session_id?: string } = { chat_input: chatInput }

  if (sessionId?.trim()) {
    body.session_id = sessionId.trim()
  }

  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify(body),
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

    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })

    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''

    for (const raw of parts) {
      const line = raw.trim()

      if (!line) {
        continue
      }

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
      console.error('Failed to parse trailing garbage:', tail)
    }
  }
}
