<script setup lang="ts">
import { ref } from 'vue'
import ChatPage from './components/ChatPage.vue'
import DocumentsPage from './components/DocumentsPage.vue'

type NavKey = 'chat' | 'documents'
const active = ref<NavKey>('chat')
</script>

<template>
  <div class="flex h-full min-h-0 w-full">
    <aside
      class="flex w-22 shrink-0 flex-col gap-2 border-r border-zinc-200 bg-white p-2 pt-3 dark:border-zinc-700 dark:bg-zinc-900"
      aria-label="Primary"
    >
      <button
        type="button"
        class="rounded-md px-1.5 py-2 text-center text-xs font-semibold text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
        :class="
          active === 'chat'
            ? 'border border-blue-600 bg-blue-100 text-blue-800 dark:border-blue-500 dark:bg-blue-950 dark:text-blue-200'
            : 'border border-transparent bg-transparent'
        "
        @click="active = 'chat'"
      >
        Chat
      </button>

      <button
        type="button"
        class="rounded-md px-1.5 py-2 text-center text-xs font-semibold text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
        :class="
          active === 'documents'
            ? 'border border-blue-600 bg-blue-100 text-blue-800 dark:border-blue-500 dark:bg-blue-950 dark:text-blue-200'
            : 'border border-transparent bg-transparent'
        "
        @click="active = 'documents'"
      >
        Documents
      </button>
    </aside>

    <main class="flex min-h-0 min-w-0 flex-1 flex-col">
      <ChatPage v-if="active === 'chat'" />
      <DocumentsPage v-else />
    </main>
  </div>
</template>
