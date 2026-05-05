import { API_BASE_URL } from '../config'

export type PipelineJobStatus = 'queued' | 'started' | 'finished' | 'failed'

export interface PipelineJob {
  job_id: string
  status: PipelineJobStatus
  filename: string | null
  enqueued_at: string | null
  ended_at: string | null
  result: unknown
}

export interface JobsResponse {
  queued: PipelineJob[]
  started: PipelineJob[]
  finished: PipelineJob[]
  failed: PipelineJob[]
}

export async function fetchUploadJobs(): Promise<JobsResponse> {
  const res = await fetch(`${API_BASE_URL}/upload/jobs`)

  if (!res.ok) {
    throw new Error(await res.text().catch(() => res.statusText))
  }

  return res.json() as Promise<JobsResponse>
}

export async function uploadDocument(file: File): Promise<{ file_name: string; message: string }> {
  const fd = new FormData()
  fd.append('file', file)

  const res = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: fd,
  })

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(text || `Upload failed (${res.status})`)
  }

  return res.json() as Promise<{ file_name: string; message: string }>
}

export function flattenJobs(data: JobsResponse): PipelineJob[] {
  return [...data.queued, ...data.started, ...data.finished, ...data.failed]
}
