<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  uploadDocuments,
  VECTOR_EMBEDDING_DIMENSION,
  type PipelineJob,
  type PipelineJobStatus,
} from '../api/upload'
import { documentsJobs as jobs, documentsJobsError as loadError, refreshDocumentsJobs } from '../lib/documentsJobsStore'
import { pushToast } from '../lib/toast'

type SortKey = 'name' | 'date'
type SortDir = 'asc' | 'desc'

const uploading = ref(false)
const filterText = ref('')
const sortKey = ref<SortKey>('date')
const sortDir = ref<SortDir>('desc')
const pageSize = ref(5)
const currentPage = ref(1)
const expandedId = ref<string | null>(null)
const dragActive = ref(false)

async function loadJobs() {
  await refreshDocumentsJobs()
}

const filtered = computed(() => {
  const q = filterText.value.trim().toLowerCase()
  let list = jobs.value.slice()

  if (q) {
    list = list.filter((j) => displayFileName(j).toLowerCase().includes(q))
  }

  list.sort((a, b) => {
    if (sortKey.value === 'name') {
      const an = displayFileName(a).toLowerCase()
      const bn = displayFileName(b).toLowerCase()
      const c = an.localeCompare(bn)

      return sortDir.value === 'asc' ? c : -c
    }

    const ad = a.job_metadata.enqueued_at ? Date.parse(a.job_metadata.enqueued_at) : 0
    const bd = b.job_metadata.enqueued_at ? Date.parse(b.job_metadata.enqueued_at) : 0

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

  return `Showing ${start}–${end} of ${filtered.value.length} documents`
})

function toggleRow(jobId: string) {
  expandedId.value = expandedId.value === jobId ? null : jobId
}

function statusLabel(status: PipelineJobStatus): string {
  switch (status) {
    case 'enqueued':
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

function isProcessing(status: PipelineJobStatus): boolean {
  return status === 'enqueued' || status === 'started'
}

function statusChipClass(status: PipelineJobStatus): string {
  const base = 'relative inline-flex shrink-0 items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-semibold'

  const map: Record<PipelineJobStatus, string> = {
    enqueued: 'bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200',
    started: 'bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-200',
    finished: 'bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-200',
    failed: 'bg-red-100 text-red-900 dark:bg-red-950 dark:text-red-200',
  }

  return `${base} ${map[status]}`
}

async function onFilePick(files: FileList | null) {
  if (!files?.length) return

  const list = Array.from(files)
  uploading.value = true

  try {
    const { succeeded, failed } = await uploadDocuments(list)

    await loadJobs()

    const ok = succeeded.length

    if (failed.length === 0) {
      pushToast(list.length === 1 ? 'File uploaded successfully.' : `${ok} files uploaded successfully.`, 'success')
    } else if (ok === 0) {
      pushToast(failed.map((f) => `${f.file_name}: ${f.detail}`).join(' '), 'error')
    } else {
      pushToast(
        `${ok} of ${list.length} uploaded. ${failed.map((f) => `${f.file_name}: ${f.detail}`).join(' ')}`,
        'error',
      )
    }
  } catch (e) {
    pushToast(e instanceof Error ? e.message : String(e), 'error')
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
  void onFilePick(input.files).finally(() => {
    input.value = ''
  })
}

function goPage(p: number) {
  currentPage.value = Math.min(Math.max(1, p), totalPages.value)
}

function displayFileName(job: PipelineJob): string {
  const raw = job.file_metadata?.name
  const name = typeof raw === 'string' ? raw.trim() : ''
  return name || '(unnamed)'
}

function formatFileTypeLabel(job: PipelineJob): string {
  const mime = (job.file_metadata?.type ?? '').trim().toLowerCase()
  if (mime === 'application/pdf') return 'Portable Document Format'
  if (mime === 'text/plain') return 'Plain text'

  const name = displayFileName(job).toLowerCase()
  if (name.endsWith('.pdf')) return 'Portable Document Format'
  if (name.endsWith('.txt')) return 'Plain text'

  return '—'
}

function formatBytes(bytes: number | undefined): string {
  if (bytes == null || Number.isNaN(bytes) || bytes < 0) return '—'

  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let v = bytes

  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i += 1
  }

  return `${i === 0 ? v : v.toFixed(1)} ${units[i]}`
}

function displayOrDash(value: string | number | undefined | null): string {
  if (value === undefined || value === null || value === '') return '—'

  return String(value)
}

function formatJobTimestamp(iso: string | null | undefined): string {
  if (iso == null || String(iso).trim() === '') return '—'

  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'

  const datePart = new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(d)

  const timePart = new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(d)

  return `${datePart} at ${timePart}`
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col bg-zinc-100 dark:bg-zinc-950">
    <header class="shrink-0 border-b border-zinc-200 bg-white px-5 pb-3 pt-4 text-left dark:border-zinc-700 dark:bg-zinc-900">
      <h1 class="text-xl font-semibold text-zinc-900 dark:text-zinc-50">Documents</h1>
      <p class="mt-1.5 max-w-3xl text-sm text-zinc-600 dark:text-zinc-400">
        Upload one or more PDF or plain-text files.
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
          .pdf and .txt only — select multiple files if you need to.
        </p>
        <label class="relative inline-block cursor-pointer">
          <input
            type="file"
            multiple
            accept=".pdf,.txt,application/pdf,text/plain"
            class="absolute inset-0 cursor-pointer opacity-0"
            :disabled="uploading"
            @change="onBrowse"
          />
          <span class="inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white">Browse files</span>
        </label>
      </div>

      <p v-if="loadError" class="mx-auto mb-2 max-w-3xl text-sm text-red-700 dark:text-red-400">{{ loadError }}</p>

      <div class="mx-auto mb-3 flex justify-between max-w-3xl flex-row items-end gap-4">
        <div class="flex flex-row w-full items-center gap-2 h-14">
          <span class="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Filter</span>
          <input
            v-model="filterText"
            type="search"
            placeholder="Filter by file name…"
            class="min-w-48 w-full h-8 rounded-md border border-zinc-200 bg-white px-2.5 py-2 text-sm text-zinc-900 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100"
          />
        </div>

        <div class="flex flex-row items-center gap-2 h-14">
          <span class="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Sort</span>
          <select
            v-model="sortKey"
            class="min-w-28 h-8 rounded-md border border-zinc-200 bg-white px-2.5 py-2 text-sm text-zinc-900 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100"
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
        <li v-for="job in pageSlice" :key="job.job_metadata.id" class="m-0">
          <button
            type="button"
            class="flex w-full cursor-pointer items-center gap-3 rounded-lg border bg-white px-3.5 py-2 text-left [font:inherit] transition-shadow hover:border-blue-300 hover:shadow-sm dark:bg-zinc-900"
            :class="
              expandedId === job.job_metadata.id
                ? 'border-blue-600 dark:border-blue-500'
                : 'border-zinc-200 dark:border-zinc-600'
            "
            @click="toggleRow(job.job_metadata.id)"
          >
            <span class="min-w-0 flex-1 truncate font-medium text-zinc-900 dark:text-zinc-50">
              {{ displayFileName(job) }}
            </span>
            <span :class="statusChipClass(job.job_metadata.status)">
              {{ statusLabel(job.job_metadata.status) }}
              <span
                v-if="isProcessing(job.job_metadata.status)"
                class="h-1.5 w-1.5 shrink-0 rounded-full bg-current animate-pulse-dot"
                aria-hidden="true"
              />
            </span>
            <span
              class="shrink-0 text-[0.65rem] text-zinc-500 transition-transform dark:text-zinc-400"
              :class="expandedId === job.job_metadata.id ? '-rotate-180' : ''"
              aria-hidden="true"
              >▼</span
            >
          </button>

          <div
            v-if="expandedId === job.job_metadata.id"
            class="mt-1.5 rounded-lg border-2 border-dashed border-zinc-300 bg-zinc-50 px-4 py-4 text-left dark:border-zinc-600 dark:bg-zinc-800/50"
          >
            <section class="mb-4">
              <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                File
              </h3>
              <dl class="grid grid-cols-[minmax(7rem,10rem)_1fr] gap-x-4 gap-y-1.5 text-sm">
                <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">Name</dt>
                <dd class="m-0 text-zinc-600 dark:text-zinc-400">{{ displayFileName(job) }}</dd>
                <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">Type</dt>
                <dd class="m-0 text-zinc-600 dark:text-zinc-400">{{ formatFileTypeLabel(job) }}</dd>
                <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">Size</dt>
                <dd class="m-0 text-zinc-600 dark:text-zinc-400">{{ formatBytes(job.file_metadata?.size ?? undefined) }}</dd>
              </dl>
            </section>

            <section class="mb-4 border-t border-zinc-200 pt-4 dark:border-zinc-600">
              <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Vector store
              </h3>
              <dl class="grid grid-cols-[minmax(7rem,10rem)_1fr] gap-x-4 gap-y-1.5 text-sm">
                <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">Total chunks</dt>
                <dd class="m-0 text-zinc-600 dark:text-zinc-400">{{ displayOrDash(job.job_result?.chunks) }}</dd>
                <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">Embedding dimension</dt>
                <dd class="m-0 text-zinc-600 dark:text-zinc-400">{{ VECTOR_EMBEDDING_DIMENSION }}</dd>
              </dl>
            </section>

            <section class="border-t border-zinc-200 pt-4 dark:border-zinc-600">
              <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Job</h3>
              <dl class="grid grid-cols-[minmax(7rem,10rem)_1fr] gap-x-4 gap-y-1.5 text-sm">
                <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">Uploaded at</dt>
                <dd class="m-0 text-zinc-600 dark:text-zinc-400">{{ formatJobTimestamp(job.job_metadata.enqueued_at) }}</dd>
                <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">Stored at</dt>
                <dd class="m-0 text-zinc-600 dark:text-zinc-400">{{ formatJobTimestamp(job.job_metadata.ended_at) }}</dd>
                <dt class="m-0 font-semibold text-zinc-900 dark:text-zinc-100">Outcome</dt>
                <dd class="m-0 text-zinc-600 dark:text-zinc-400">
                  <template v-if="job.job_result?.result?.message">
                    {{ job.job_result.result.message }}
                  </template>
                  <template v-else-if="job.job_result?.result?.status">
                    {{ job.job_result.result.status }}
                  </template>
                  <template v-else>—</template>
                </dd>
              </dl>
            </section>
          </div>
        </li>
      </ul>

      <div v-if="!filtered.length && !loadError" class="mx-auto mt-4 max-w-3xl text-center text-sm text-zinc-500 dark:text-zinc-400">
        Upload documents to add them to the knowledge base.
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
