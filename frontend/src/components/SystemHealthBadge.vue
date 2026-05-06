<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { systemHealth, systemHealthUnreachable } from '../lib/systemHealthStore'

const open = ref(false)
const rootRef = ref<HTMLElement | null>(null)

const dotClass = computed(() => {
  if (systemHealthUnreachable.value) {
    return 'bg-red-500'
  }

  const h = systemHealth.value

  if (!h) {
    return 'bg-zinc-400'
  }

  return h.status === 'healthy' ? 'bg-emerald-500' : 'bg-amber-500'
})

function toggle(): void {
  open.value = !open.value
}

function relativeProbeTime(iso: string | undefined): string {
  if (!iso) {
    return ''
  }

  const d = new Date(iso)

  if (Number.isNaN(d.getTime())) {
    return ''
  }

  let sec = Math.floor((Date.now() - d.getTime()) / 1000)

  if (sec < 0) {
    sec = 0
  }

  if (sec < 60) {
    return 'less than a minute ago'
  }

  const min = Math.floor(sec / 60)

  if (min === 1) {
    return '1 minute ago'
  }

  if (min < 60) {
    return `${min} minutes ago`
  }

  const hrs = Math.floor(min / 60)

  if (hrs === 1) {
    return '1 hour ago'
  }

  if (hrs < 24) {
    return `${hrs} hours ago`
  }

  const days = Math.floor(hrs / 24)

  return days === 1 ? '1 day ago' : `${days} days ago`
}

function truncate(s: string, max = 96): string {
  const t = s.trim()

  return t.length <= max ? t : `${t.slice(0, max - 3)}...`
}

function onDocMouseDown(e: MouseEvent): void {
  if (!open.value) {
    return
  }

  const root = rootRef.value

  if (root && e.target instanceof Node && root.contains(e.target)) {
    return
  }

  open.value = false
}

function onDocKeydown(e: KeyboardEvent): void {
  if (e.key === 'Escape') {
    open.value = false
  }
}

onMounted(() => {
  document.addEventListener('mousedown', onDocMouseDown)
  document.addEventListener('keydown', onDocKeydown)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', onDocMouseDown)
  document.removeEventListener('keydown', onDocKeydown)
})

function onBadgeKeydown(e: KeyboardEvent): void {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    toggle()
  }
}

function rowDot(ok: boolean): string {
  return ok ? 'bg-emerald-500' : 'bg-red-500'
}
</script>

<template>
  <Teleport to="body">
    <div class="pointer-events-none fixed top-5 right-5 z-99">
      <div ref="rootRef" class="pointer-events-auto relative">
        <div
          class="flex h-10 w-10 cursor-pointer items-center justify-center rounded-lg border border-zinc-200 bg-white shadow-md transition-opacity hover:opacity-95 dark:border-zinc-700 dark:bg-zinc-900"
          role="button"
          tabindex="0"
          :aria-expanded="open"
          aria-label="System health"
          @click.stop="toggle"
          @keydown="onBadgeKeydown"
        >
          <span
            class="health-dot-dim size-3 shrink-0 rounded-full shadow-sm"
            :class="dotClass"
            aria-hidden="true"
          />
        </div>

        <div
          v-if="open"
          class="absolute top-full right-full z-100 mt-1 mr-1 min-w-[220px] max-w-sm rounded-lg border border-zinc-200 bg-white px-3 py-2.5 text-xs shadow-lg dark:border-zinc-700 dark:bg-zinc-900"
          role="region"
          aria-label="Service status"
          @click.stop
        >
          <p
            v-if="systemHealthUnreachable"
            class="m-0 font-medium text-red-700 dark:text-red-300"
          >
            Application is unreachable
          </p>

          <template v-else-if="systemHealth">
            <ul class="m-0 list-none space-y-2 p-0">
              <li class="flex flex-col gap-0.5 border-b border-zinc-100 pb-2 dark:border-zinc-800">
                <div class="flex items-center gap-2">
                  <span
                    class="size-2 shrink-0 rounded-full"
                    :class="rowDot(systemHealth.model.embedding.status === 'ok')"
                  />
                  <span class="font-medium text-zinc-800 dark:text-zinc-100">Embedding</span>
                </div>
                <p class="m-0 pl-4 text-[11px] leading-snug text-zinc-500 dark:text-zinc-400">
                  Last checked {{ relativeProbeTime(systemHealth.model.embedding.last_live_probe_at) || '—' }}
                </p>
              </li>

              <li class="flex flex-col gap-0.5 border-b border-zinc-100 pb-2 dark:border-zinc-800">
                <div class="flex items-center gap-2">
                  <span
                    class="size-2 shrink-0 rounded-full"
                    :class="rowDot(systemHealth.model.llm.status === 'ok')"
                  />
                  <span class="font-medium text-zinc-800 dark:text-zinc-100">LLM</span>
                </div>
                <p class="m-0 pl-4 text-[11px] leading-snug text-zinc-500 dark:text-zinc-400">
                  Last checked {{ relativeProbeTime(systemHealth.model.llm.last_live_probe_at) || '—' }}
                </p>
              </li>

              <li class="flex items-center gap-2">
                <span
                  class="size-2 shrink-0 rounded-full"
                  :class="rowDot(systemHealth.vector_db.status === 'ok')"
                />
                <span class="font-medium text-zinc-800 dark:text-zinc-100">Vector DB</span>
              </li>

              <li class="flex items-center gap-2">
                <span
                  class="size-2 shrink-0 rounded-full"
                  :class="rowDot(systemHealth.worker.status === 'ok')"
                />
                <span class="font-medium text-zinc-800 dark:text-zinc-100">Worker queue</span>
              </li>

              <li class="flex items-center gap-2">
                <span
                  class="size-2 shrink-0 rounded-full"
                  :class="rowDot(systemHealth.storage.status === 'ok')"
                />
                <span class="font-medium text-zinc-800 dark:text-zinc-100">Storage</span>
              </li>
            </ul>

            <p
              v-if="
                systemHealth.model.embedding.detail ||
                systemHealth.model.llm.detail ||
                systemHealth.vector_db.detail ||
                systemHealth.worker.detail ||
                systemHealth.storage.detail
              "
              class="mt-2 border-t border-zinc-100 pt-2 text-[11px] leading-snug text-zinc-500 dark:border-zinc-800 dark:text-zinc-400"
            >
              <span v-if="systemHealth.model.embedding.detail" class="block">
                Embedding: {{ truncate(systemHealth.model.embedding.detail) }}
              </span>
              <span v-if="systemHealth.model.llm.detail" class="block">
                LLM: {{ truncate(systemHealth.model.llm.detail) }}
              </span>
              <span v-if="systemHealth.vector_db.detail" class="block">
                Vector DB: {{ truncate(systemHealth.vector_db.detail) }}
              </span>
              <span v-if="systemHealth.worker.detail" class="block">
                Worker: {{ truncate(systemHealth.worker.detail) }}
              </span>
              <span v-if="systemHealth.storage.detail" class="block">
                Storage: {{ truncate(systemHealth.storage.detail) }}
              </span>
            </p>
          </template>

          <p v-else class="m-0 text-zinc-500 dark:text-zinc-400">Loading health…</p>
        </div>
      </div>
    </div>
  </Teleport>
</template>
