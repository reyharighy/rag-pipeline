import { ref } from 'vue'
import {
  fetchUploadJobs,
  flattenJobs,
  type PipelineJob,
  type PipelineJobStatus,
} from '../api/upload'
import { pushToast } from './toast'

export const documentsJobs = ref<PipelineJob[]>([])
export const documentsJobsError = ref<string | null>(null)

const jobsStatusSeedDone = ref(false)
const lastJobStatusById = new Map<string, PipelineJobStatus>()

function displayFileName(job: PipelineJob): string {
  const raw = job.file_metadata?.name
  const name = typeof raw === 'string' ? raw.trim() : ''
  return name || '(unnamed)'
}

function embeddingOutcomeMessage(job: PipelineJob): string {
  const m = job.job_result?.result?.message?.trim()
  if (m) return m

  const s = job.job_result?.result?.status
  if (s === 'error') return 'Embedding failed.'

  return 'Stored in vector database.'
}

export async function refreshDocumentsJobs(): Promise<void> {
  try {
    const data = await fetchUploadJobs()
    const next = flattenJobs(data)

    if (!jobsStatusSeedDone.value) {
      for (const job of next) {
        lastJobStatusById.set(job.job_metadata.id, job.job_metadata.status)
      }

      jobsStatusSeedDone.value = true
    } else {
      const nextIds = new Set<string>()

      for (const job of next) {
        const id = job.job_metadata.id
        nextIds.add(id)
        const prev = lastJobStatusById.get(id)
        const cur = job.job_metadata.status

        if (prev === 'enqueued' || prev === 'started') {
          if (cur === 'finished') {
            pushToast(`Ready: ${displayFileName(job)} — ${embeddingOutcomeMessage(job)}`, 'success')
          } else if (cur === 'failed') {
            pushToast(`Embedding failed: ${displayFileName(job)} — ${embeddingOutcomeMessage(job)}`, 'error')
          }
        }
        lastJobStatusById.set(id, cur)
      }

      for (const id of lastJobStatusById.keys()) {
        if (!nextIds.has(id)) lastJobStatusById.delete(id)
      }
    }

    documentsJobs.value = next
    documentsJobsError.value = null
  } catch (e) {
    documentsJobsError.value = e instanceof Error ? e.message : String(e)
  }
}

let pollTimer: ReturnType<typeof setInterval> | null = null

export function startDocumentsJobsPolling(): void {
  void refreshDocumentsJobs()

  if (pollTimer == null) {
    pollTimer = setInterval(() => void refreshDocumentsJobs(), 4000)
  }
}

export function stopDocumentsJobsPolling(): void {
  if (pollTimer != null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}
