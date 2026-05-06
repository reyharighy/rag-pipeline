<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import {
  streamChat,
  extractAssistantTextFromUpdateData,
  extractRationaleOrHint,
  getStoredChatSessionId,
  setStoredChatSessionId,
  fetchChatHistory,
} from '../lib/chatStream'

marked.setOptions({ gfm: true, breaks: false })

function renderAssistantMarkdown(text: string): string {
  const trimmed = text.trim()

  if (!trimmed) {
    return ''
  }

  const html = marked.parse(trimmed, { async: false }) as string

  return DOMPurify.sanitize(html)
}

interface ChatBubble {
  role: 'user' | 'assistant'
  text: string
}

const conversation = ref<ChatBubble[]>([])
const draft = ref('')
const streamingReply = ref('')
const thinkingText = ref<string | null>(null)
const isStreaming = ref(false)
const historyLoading = ref(true)
const errorMessage = ref<string | null>(null)
const scrollRoot = ref<HTMLElement | null>(null)
const sessionId = ref<string | null>(getStoredChatSessionId())

async function loadHistory() {
  historyLoading.value = true
  errorMessage.value = null

  try {
    sessionId.value = getStoredChatSessionId()
    const sid = sessionId.value

    if (!sid) {
      conversation.value = []

      return
    }

    const rows = await fetchChatHistory(sid)

    conversation.value = rows.map((r) => ({
      role: r.role,
      text: r.content,
    }))
  } catch (e) {
    conversation.value = []
    errorMessage.value = e instanceof Error ? e.message : String(e)
  } finally {
    historyLoading.value = false
    scrollToBottom()
  }
}

onMounted(() => {
  void loadHistory()
})

function scrollToBottom() {
  nextTick(() => {
    const el = scrollRoot.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

watch([conversation, streamingReply, thinkingText], () => scrollToBottom(), { deep: true })

async function send() {
  const text = draft.value.trim()
  if (!text || isStreaming.value) return

  errorMessage.value = null
  conversation.value = [...conversation.value, { role: 'user', text }]
  draft.value = ''
  streamingReply.value = ''
  thinkingText.value = 'Connecting…'
  isStreaming.value = true
  scrollToBottom()

  try {
    for await (const event of streamChat(text, sessionId.value)) {
      if (event.type === 'session') {
        const data = event.data as { session_id?: string } | undefined
        const sid = data?.session_id

        if (typeof sid === 'string' && sid) {
          sessionId.value = sid
          setStoredChatSessionId(sid)
        }

        continue
      }

      if (event.type === 'complete') {
        if (streamingReply.value.trim()) {
          conversation.value = [
            ...conversation.value,
            { role: 'assistant', text: streamingReply.value },
          ]
        }

        streamingReply.value = ''
        thinkingText.value = null
        isStreaming.value = false
        break
      }

      if (event.type === 'update') {
        const data = event.data

        if (typeof data === 'string') {
          errorMessage.value = data
          thinkingText.value = null
          isStreaming.value = false
          break
        }

        const hint = extractRationaleOrHint(data)

        if (hint) {
          thinkingText.value = hint
        }

        const assistant = extractAssistantTextFromUpdateData(data)

        if (assistant) {
          streamingReply.value = assistant
        }
      }
    }
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : String(e)
  } finally {
    thinkingText.value = null
    isStreaming.value = false
    streamingReply.value = ''
    scrollToBottom()
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    void send()
  }
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col bg-zinc-100 dark:bg-zinc-950">
    <header class="shrink-0 border-b border-zinc-200 bg-white px-5 pb-3 pt-4 text-left dark:border-zinc-700 dark:bg-zinc-900">
      <h1 class="text-xl font-semibold text-zinc-900 dark:text-zinc-50">Chat</h1>
      <p class="mt-1.5 max-w-2xl text-sm text-zinc-600 dark:text-zinc-400">
        Send a message to the agent. Replies stream in as the graph runs.
      </p>
    </header>

    <div ref="scrollRoot" class="min-h-0 flex-1 overflow-y-auto px-5 pb-6 pt-4">
      <div class="mx-auto flex max-w-3xl flex-col gap-4">
        <p
          v-if="historyLoading"
          class="m-0 text-center text-sm text-zinc-500 dark:text-zinc-400"
        >
          Loading conversation…
        </p>

        <template v-for="(m, i) in conversation" :key="i">
          <div v-if="m.role === 'user'" class="flex justify-end">
            <div
              class="max-w-[85%] whitespace-pre-wrap wrap-break-word rounded-2xl rounded-br-sm bg-green-500 px-4 py-2.5 text-left font-medium leading-snug text-green-950"
            >
              {{ m.text }}
            </div>
          </div>
          <div v-else class="flex justify-start">
            <div
              class="assistant-markdown max-w-[85%] wrap-break-word rounded-2xl rounded-bl-sm bg-zinc-200 px-4 py-2.5 text-left text-[0.95rem] leading-relaxed text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
              v-html="renderAssistantMarkdown(m.text)"
            ></div>
          </div>
        </template>

        <div
          v-if="isStreaming && thinkingText && !streamingReply"
          class="flex justify-start"
        >
          <p
            class="m-0 max-w-[85%] rounded-lg bg-zinc-200/80 px-3 py-2 text-sm text-zinc-600 italic dark:bg-zinc-800/80 dark:text-zinc-400"
          >
            {{ thinkingText }}
          </p>
        </div>

        <div v-if="isStreaming && streamingReply" class="flex justify-start">
          <div
            class="assistant-markdown max-w-[85%] wrap-break-word rounded-2xl rounded-bl-sm border border-zinc-300/80 bg-zinc-200/90 px-4 py-2.5 text-left text-[0.95rem] leading-relaxed text-zinc-900 dark:border-zinc-600 dark:bg-zinc-800/90 dark:text-zinc-100"
            v-html="renderAssistantMarkdown(streamingReply)"
          ></div>
        </div>

        <div
          v-if="errorMessage"
          class="rounded-xl border-2 border-dashed border-red-600 bg-red-50 px-4 py-3.5 text-left text-red-950 dark:border-red-500 dark:bg-red-950/40 dark:text-red-100"
        >
          <span class="mb-1.5 block text-[0.7rem] font-semibold uppercase tracking-wide opacity-85">Error</span>
          <p class="m-0 whitespace-pre-wrap wrap-break-word text-[0.95rem]">{{ errorMessage }}</p>
        </div>
      </div>
    </div>

    <div
      class="flex shrink-0 items-end gap-2 border-t border-zinc-200 bg-white px-4 py-3 shadow-[0_-4px_12px_rgba(0,0,0,0.04)] dark:border-zinc-700 dark:bg-zinc-900 dark:shadow-[0_-4px_12px_rgba(0,0,0,0.2)]"
    >
      <textarea
        v-model="draft"
        class="min-h-11 max-h-32 flex-1 resize-none rounded-lg border border-zinc-200 bg-white px-3.5 py-2.5 text-zinc-900 placeholder:text-zinc-400 focus:border-transparent focus:outline-2 focus:outline-offset-0 focus:outline-blue-600 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder:text-zinc-500"
        rows="1"
        placeholder="Type your message…"
        :disabled="isStreaming || historyLoading"
        @keydown="onKeydown"
      />
      <button
        type="button"
        class="shrink-0 cursor-pointer rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-45"
        :disabled="isStreaming || historyLoading || !draft.trim()"
        @click="send"
      >
        Send
      </button>
    </div>
  </div>
</template>

<style scoped>
.assistant-markdown :deep(p) {
  margin: 0.5em 0;
}

.assistant-markdown :deep(p:first-child) {
  margin-top: 0;
}

.assistant-markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.assistant-markdown :deep(ul),
.assistant-markdown :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.35em;
}

.assistant-markdown :deep(li) {
  margin: 0.2em 0;
}

.assistant-markdown :deep(h1),
.assistant-markdown :deep(h2),
.assistant-markdown :deep(h3),
.assistant-markdown :deep(h4) {
  margin: 0.65em 0 0.4em;
  font-weight: 700;
  line-height: 1.25;
}

.assistant-markdown :deep(h1) {
  font-size: 1.15em;
}

.assistant-markdown :deep(h2) {
  font-size: 1.08em;
}

.assistant-markdown :deep(h3),
.assistant-markdown :deep(h4) {
  font-size: 1em;
}

.assistant-markdown :deep(a) {
  color: #2563eb;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.dark .assistant-markdown :deep(a) {
  color: #93c5fd;
}

.assistant-markdown :deep(code) {
  font-size: 0.9em;
  padding: 0.1em 0.35em;
  border-radius: 0.25rem;
  background: rgb(24 24 27 / 0.12);
}

.dark .assistant-markdown :deep(code) {
  background: rgb(255 255 255 / 0.1);
}

.assistant-markdown :deep(pre) {
  margin: 0.6em 0;
  padding: 0.75em 1em;
  overflow-x: auto;
  border-radius: 0.5rem;
  font-size: 0.88em;
  line-height: 1.45;
  background: rgb(24 24 27 / 0.12);
}

.dark .assistant-markdown :deep(pre) {
  background: rgb(0 0 0 / 0.35);
}

.assistant-markdown :deep(pre code) {
  padding: 0;
  background: transparent;
  font-size: inherit;
}

.assistant-markdown :deep(blockquote) {
  margin: 0.5em 0;
  padding-left: 0.85em;
  border-left: 3px solid rgb(113 113 122 / 0.65);
  color: rgb(63 63 70);
}

.dark .assistant-markdown :deep(blockquote) {
  color: rgb(212 212 216);
}

.assistant-markdown :deep(hr) {
  margin: 0.85em 0;
  border: 0;
  border-top: 1px solid rgb(113 113 122 / 0.35);
}

.assistant-markdown :deep(table) {
  width: 100%;
  margin: 0.6em 0;
  border-collapse: collapse;
  font-size: 0.92em;
}

.assistant-markdown :deep(th),
.assistant-markdown :deep(td) {
  border: 1px solid rgb(113 113 122 / 0.45);
  padding: 0.35em 0.5em;
  text-align: left;
}

.assistant-markdown :deep(th) {
  background: rgb(24 24 27 / 0.08);
}

.dark .assistant-markdown :deep(th) {
  background: rgb(255 255 255 / 0.06);
}
</style>
