<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  fetchUploadJobs,
  uploadDocument,
  flattenJobs,
  type PipelineJob,
} from '../api/upload'

type SortKey = 'name' | 'date'
type SortDir = 'asc' | 'desc'

const jobs = ref<PipelineJob[]>([])
const loadError = ref<string | null>(null)
const uploading = ref(false)
const uploadMessage = ref<string | null>(null)
const filterText = ref('')
const sortKey = ref<SortKey>('date')
const sortDir = ref<SortDir>('desc')
const pageSize = ref(5)
const currentPage = ref(1)
const expandedId = ref<string | null>(null)
const dragActive = ref(false)

let pollTimer: ReturnType<typeof setInterval> | null = null

async function loadJobs() {
  try {
    const data = await fetchUploadJobs()
    jobs.value = flattenJobs(data)
    loadError.value = null
  } catch (e) {
    loadError.value = e instanceof Error ? e.message : String(e)
  }
}

onMounted(() => {
  void loadJobs()
  pollTimer = setInterval(() => void loadJobs(), 4000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

const filtered = computed(() => {
  const q = filterText.value.trim().toLowerCase()
  let list = jobs.value.slice()

  if (q) {
    list = list.filter((j) => (j.filename ?? '').toLowerCase().includes(q))
  }

  list.sort((a, b) => {
    if (sortKey.value === 'name') {
      const an = (a.filename ?? '').toLowerCase()
      const bn = (b.filename ?? '').toLowerCase()
      const c = an.localeCompare(bn)
      return sortDir.value === 'asc' ? c : -c
    }

    const ad = a.enqueued_at ? Date.parse(a.enqueued_at) : 0
    const bd = b.enqueued_at ? Date.parse(b.enqueued_at) : 0

    return sortDir.value === 'asc' ? ad - bd : bd - ad
  })

  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize.value)))

watch([filtered, pageSize], () => {
  if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
})

const pageSlice = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value

  return filtered.value.slice(start, start + pageSize.value)
})

const rangeLabel = computed(() => {
  if (!filtered.value.length) return 'No documents to show'
  const start = (currentPage.value - 1) * pageSize.value + 1
  const end = Math.min(currentPage.value * pageSize.value, filtered.value.length)

  return `Showing ${start}–${end} of ${filtered.value.length} pipeline jobs`
})

function toggleRow(jobId: string) {
  expandedId.value = expandedId.value === jobId ? null : jobId
}

function statusLabel(status: PipelineJob['status']): string {
  switch (status) {
    case 'queued':
      return 'Queued'
    case 'started':
      return 'Processing'
    case 'finished':
      return 'Ready'
    case 'failed':
      return 'Failed'
    default:
      return status
  }
}

function isProcessing(status: PipelineJob['status']): boolean {
  return status === 'queued' || status === 'started'
}

function statusChipClass(status: PipelineJob['status']): string {
  const base = 'relative inline-flex shrink-0 items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-semibold'

  const map: Record<PipelineJob['status'], string> = {
    queued: 'bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200',
    started: 'bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-200',
    finished: 'bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-200',
    failed: 'bg-red-100 text-red-900 dark:bg-red-950 dark:text-red-200',
  }

  return `${base} ${map[status]}`
}

async function onFilePick(files: FileList | null) {
  if (!files?.length) return
  const file = files[0]
  uploading.value = true
  uploadMessage.value = null

  try {
    const r = await uploadDocument(file)
    uploadMessage.value = r.message

    await loadJobs()
  } catch (e) {
    uploadMessage.value = e instanceof Error ? e.message : String(e)
  } finally {
    uploading.value = false
  }
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  dragActive.value = false
  void onFilePick(e.dataTransfer?.files ?? null)
}

function onBrowse(e: Event) {
  const input = e.target as HTMLInputElement
  void onFilePick(input.files)
}

function goPage(p: number) {
  currentPage.value = Math.min(Math.max(1, p), totalPages.value)
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col bg-zinc-100 dark:bg-zinc-950">
    <header class="shrink-0 border-b border-zinc-200 bg-white px-5 pb-3 pt-4 text-left dark:border-zinc-700 dark:bg-zinc-900">
      <h1 class="text-xl font-semibold text-zinc-900 dark:text-zinc-50">Documents</h1>
      <p class="mt-1.5 max-w-3xl text-sm text-zinc-600 dark:text-zinc-400">
        Upload PDF or plain-text files. Cards reflect embedding jobs; details below are a UI placeholder until a
        document-metadata API exists.
      </p>
    </header>

    <div class="min-h-0 flex-1 overflow-y-auto px-5 pb-4 pt-4">
      <div
        class="mx-auto mb-4 max-w-3xl rounded-xl border-2 border-dashed border-zinc-300 bg-white p-6 text-center transition-colors dark:border-zinc-600 dark:bg-zinc-900"
        :class="{
          'border-blue-600 bg-blue-50/80 dark:border-blue-500 dark:bg-blue-950/30': dragActive,
          'pointer-events-none opacity-70': uploading,
        }"
        @dragenter.prevent="dragActive = true"
        @dragover.prevent="dragActive = true"
        @dragleave.prevent="dragActive = false"
        @drop="onDrop"
      >
        <p class="mb-1.5 font-semibold text-zinc-900 dark:text-zinc-50">Upload documents here</p>
        <p class="mb-4 text-sm text-zinc-600 dark:text-zinc-400">
          .pdf and .txt only — files are sent to
          <code class="rounded bg-zinc-100 px-1 py-0.5 font-mono text-xs text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200"
            >/upload</code
          >
        </p>
        <label class="relative inline-block cursor-pointer">
          <input
            type="file"
            accept=".pdf,.txt,application/pdf,text/plain"
            class="absolute inset-0 cursor-pointer opacity-0"
            :disabled="uploading"
            @change="onBrowse"
          />
          <span class="inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white">Browse files</span>
        </label>
      </div>

      <p v-if="uploadMessage" class="mx-auto mb-2 max-w-3xl text-sm text-zinc-900 dark:text-zinc-200">{{ uploadMessage }}</p>
      <p v-if="loadError" class="mx-auto mb-2 max-w-3xl text-sm text-red-700 dark:text-red-400">{{ loadError }}</p>

      <div class="mx-auto mb-3 flex max-w-3xl flex-wrap items-end gap-4">
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Filter</span>
          <input
            v-model="filterText"
            type="search"
            placeholder="Filter by file name…"
            class="min-w-48 rounded-md border border-zinc-200 bg-white px-2.5 py-2 text-sm text-zinc-900 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100"
          />
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Sort</span>
          <select
            v-model="sortKey"
            class="min-w-28 rounded-md border border-zinc-200 bg-white px-2.5 py-2 text-sm text-zinc-900 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100"
          >
            <option value="name">Name</option>
            <option value="date">Date queued</option>
          </select>
          <select
            v-model="sortDir"
            class="min-w-28 rounded-md border border-zinc-200 bg-white px-2.5 py-2 text-sm text-zinc-900 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100"
          >
            <option value="asc">Ascending</option>
            <option value="desc">Descending</option>
          </select>
        </div>
      </div>

      <p class="mx-auto mb-3 max-w-3xl text-left text-xs text-zinc-500 dark:text-zinc-400">{{ rangeLabel }}</p>

      <ul class="mx-auto flex max-w-3xl list-none flex-col gap-2 p-0">
        <li v-for="job in pageSlice" :key="job.job_id" class="m-0">
          <button
            type="button"
            class="flex w-full cursor-pointer items-center gap-3 rounded-lg border bg-white px-3.5 py-2 text-left [font:inherit] transition-shadow hover:border-blue-300 hover:shadow-sm dark:bg-zinc-900"
            :class="
              expandedId === job.job_id
                ? 'border-blue-600 dark:border-blue-500'
                : 'border-zinc-200 dark:border-zinc-600'
            "
            @click="toggleRow(job.job_id)"
          >
            <span class="min-w-0 flex-1 truncate font-medium text-zinc-900 dark:text-zinc-50">
              {{ job.filename ?? '(unnamed)' }}
            </span>
            <span :class="statusChipClass(job.status)">
              {{ statusLabel(job.status) }}
              <span
                v-if="isProcessing(job.status)"
                class="h-1.5 w-1.5 shrink-0 rounded-full bg-current animate-pulse-dot"
                aria-hidden="true"
              />
            </span>
            <span
              class="shrink-0 text-[0.65rem] text-zinc-500 transition-transform dark:text-zinc-400"
              :class="expandedId === job.job_id ? '-rotate-180' : ''"
              aria-hidden="true"
              >▼</span
            >
          </button>

          <div
            v-if="expandedId === job.job_id"
            class="mt-1.5 rounded-lg border-2 border-dashed border-zinc-300 bg-zinc-50 px-4 py-4 text-left dark:border-zinc-600 dark:bg-zinc-800/50"
          >
            <h2 class="mb-1 text-base font-semibold text-zinc-900 dark:text-zinc-50">Document details (mock)</h2>
            <p class="mb-4 text-sm leading-snug text-zinc-600 dark:text-zinc-400">
              This block previews how rich document metadata could look once the backend exposes it. It is not tied to
              job internals beyond the file name and pipeline state shown here.
            </p>
            <dl class="mb-4 grid grid-cols-[minmax(7rem,10rem)_1fr] gap-x-4 gap-y-1.5 text-sm">
              <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">File name</dt>
              <dd class="m-0 text-zinc-600 dark:text-zinc-400">{{ job.filename ?? '—' }}</dd>
              <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">Document type</dt>
              <dd class="m-0 text-zinc-600 dark:text-zinc-400">Inferred from extension (e.g. PDF report, TXT notes)</dd>
              <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">Page / size summary</dt>
              <dd class="m-0 text-zinc-600 dark:text-zinc-400">— pending catalog service</dd>
              <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">Indexed chunks</dt>
              <dd class="m-0 text-zinc-600 dark:text-zinc-400">— pending catalog service</dd>
              <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">Owner / project</dt>
              <dd class="m-0 text-zinc-600 dark:text-zinc-400">— optional future field</dd>
              <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">Last content preview</dt>
              <dd class="m-0 italic leading-snug text-zinc-600 dark:text-zinc-400">
                “Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer posuere erat a ante venenatis dapibus
                posuere velit aliquet…”
              </dd>
            </dl>
            <aside class="mt-1 border-t border-zinc-200 pt-3 dark:border-zinc-600">
              <h3 class="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Pipeline (from jobs API)
              </h3>
              <ul class="m-0 list-disc pl-[1.1rem] text-xs text-zinc-600 dark:text-zinc-400">
                <li class="mb-0.5"><strong>Job id</strong> {{ job.job_id }}</li>
                <li class="mb-0.5"><strong>Status</strong> {{ job.status }}</li>
                <li class="mb-0.5"><strong>Queued at</strong> {{ job.enqueued_at ?? '—' }}</li>
                <li class="mb-0.5"><strong>Ended at</strong> {{ job.ended_at ?? '—' }}</li>
              </ul>
            </aside>
          </div>
        </li>
      </ul>

      <div v-if="!filtered.length && !loadError" class="mx-auto mt-4 max-w-3xl text-center text-sm text-zinc-500 dark:text-zinc-400">
        No jobs yet. Upload a document to enqueue processing.
      </div>
    </div>

    <nav
      class="flex shrink-0 items-center justify-center gap-4 border-t border-zinc-200 bg-white px-4 py-3 shadow-[0_-4px_12px_rgba(0,0,0,0.04)] dark:border-zinc-700 dark:bg-zinc-900 dark:shadow-[0_-4px_12px_rgba(0,0,0,0.2)]"
      aria-label="Pagination"
    >
      <button
        type="button"
        class="cursor-pointer rounded-md border border-zinc-200 bg-white px-3.5 py-2 text-sm text-zinc-900 hover:border-blue-600 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-45 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100 dark:hover:border-blue-500 dark:hover:text-blue-300"
        :disabled="currentPage <= 1"
        @click="goPage(currentPage - 1)"
      >
        Previous
      </button>
      <span class="text-sm text-zinc-500 dark:text-zinc-400">Page {{ currentPage }} / {{ totalPages }}</span>
      <button
        type="button"
        class="cursor-pointer rounded-md border border-zinc-200 bg-white px-3.5 py-2 text-sm text-zinc-900 hover:border-blue-600 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-45 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100 dark:hover:border-blue-500 dark:hover:text-blue-300"
        :disabled="currentPage >= totalPages"
        @click="goPage(currentPage + 1)"
      >
        Next
      </button>
    </nav>
  </div>
</template>
