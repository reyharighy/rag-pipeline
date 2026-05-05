import { API_BASE_URL, VECTOR_EMBEDDING_DIMENSION } from '../config'

export { VECTOR_EMBEDDING_DIMENSION }

export type PipelineJobStatus = 'enqueued' | 'started' | 'finished' | 'failed'

export interface FileMetadata {
  name?: string | null
  size?: number | null
  type?: string | null
}

export interface JobMetadata {
  id: string
  status: PipelineJobStatus
  enqueued_at: string | null
  started_at: string | null
  ended_at: string | null
}

export interface JobResultPayload {
  chunks?: number | null
  result?: {
    status?: 'success' | 'error' | null
    message?: string | null
  }
}

export interface PipelineJob {
  file_metadata: FileMetadata
  job_metadata: JobMetadata
  job_result?: JobResultPayload
}

export interface JobsResponse {
  enqueued: PipelineJob[]
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

export interface BatchUploadResponse {
  succeeded: { file_name: string; message: string }[]
  failed: { file_name: string; detail: string }[]
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

/** One or more files in a single request (`POST /upload/batch`). */
export async function uploadDocuments(files: File[]): Promise<BatchUploadResponse> {
  if (!files.length) {
    throw new Error('No files selected')
  }

  const fd = new FormData()
  for (const f of files) {
    fd.append('files', f)
  }

  const res = await fetch(`${API_BASE_URL}/upload/batch`, {
    method: 'POST',
    body: fd,
  })

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(text || `Upload failed (${res.status})`)
  }

  return res.json() as Promise<BatchUploadResponse>
}

export function flattenJobs(data: JobsResponse): PipelineJob[] {
  return [...data.enqueued, ...data.started, ...data.finished, ...data.failed]
}
