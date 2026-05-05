<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import {
  streamChat,
  extractAssistantTextFromUpdateData,
  extractRationaleOrHint,
} from '../lib/chatStream'

interface ChatBubble {
  role: 'user'
  text: string
}

const messages = ref<ChatBubble[]>([])
const draft = ref('')
const agentReply = ref('')
const thinkingText = ref<string | null>(null)
const isStreaming = ref(false)
const errorMessage = ref<string | null>(null)
const scrollRoot = ref<HTMLElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    const el = scrollRoot.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

watch([messages, agentReply, thinkingText], () => scrollToBottom(), { deep: true })

async function send() {
  const text = draft.value.trim()
  if (!text || isStreaming.value) return

  errorMessage.value = null
  messages.value = [...messages.value, { role: 'user', text }]
  draft.value = ''
  agentReply.value = ''
  thinkingText.value = 'Connecting…'
  isStreaming.value = true
  scrollToBottom()

  try {
    for await (const event of streamChat(text)) {
      if (event.type === 'complete') {
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
        if (hint) thinkingText.value = hint
        const assistant = extractAssistantTextFromUpdateData(data)
        if (assistant) agentReply.value = assistant
      }
    }
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : String(e)
  } finally {
    thinkingText.value = null
    isStreaming.value = false
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
        <template v-for="(m, i) in messages" :key="i">
          <div v-if="m.role === 'user'" class="flex justify-end">
            <div
              class="max-w-[85%] whitespace-pre-wrap wrap-break-word rounded-2xl rounded-br-sm bg-green-500 px-4 py-2.5 text-left font-medium leading-snug text-green-950"
            >
              {{ m.text }}
            </div>
          </div>
        </template>

        <div
          v-if="thinkingText"
          class="rounded-xl border-2 border-dashed border-amber-600 bg-amber-50 px-4 py-3.5 text-left text-amber-950 dark:border-amber-500 dark:bg-amber-950/40 dark:text-amber-100"
        >
          <span class="mb-1.5 block text-[0.7rem] font-semibold uppercase tracking-wide opacity-85">
            Agent internal thinking
          </span>
          <p class="m-0 whitespace-pre-wrap wrap-break-word text-[0.95rem]">{{ thinkingText }}</p>
        </div>

        <div
          v-if="agentReply"
          class="rounded-xl border-2 border-dashed border-pink-600 bg-pink-50 px-4 py-3.5 text-left text-pink-950 dark:border-pink-500 dark:bg-pink-950/40 dark:text-pink-100"
        >
          <span class="mb-1.5 block text-[0.7rem] font-semibold uppercase tracking-wide opacity-85">
            Agent response
          </span>
          <p class="m-0 whitespace-pre-wrap wrap-break-word text-[0.95rem]">{{ agentReply }}</p>
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
        :disabled="isStreaming"
        @keydown="onKeydown"
      />
      <button
        type="button"
        class="shrink-0 cursor-pointer rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-45"
        :disabled="isStreaming || !draft.trim()"
        @click="send"
      >
        Send
      </button>
    </div>
  </div>
</template>
