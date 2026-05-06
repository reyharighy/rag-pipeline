import { API_BASE_URL } from '../config'

export type ComponentStatus = 'ok' | 'error'

export interface ModelHealthComponent {
  status: ComponentStatus
  detail: string | null
  name?: string
  probe?: 'live' | 'cached'
  last_live_probe_at?: string
}

export interface NamedHealthComponent {
  status: ComponentStatus
  detail: string | null
  name?: string
}

export interface StorageHealthComponent {
  status: ComponentStatus
  detail: string | null
  file_count: number | null
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy'
  model: {
    embedding: ModelHealthComponent
    llm: ModelHealthComponent
  }
  vector_db: NamedHealthComponent
  worker: NamedHealthComponent
  storage: StorageHealthComponent
}

function isHealthPayload(value: unknown): value is HealthResponse {
  if (value === null || typeof value !== 'object') {
    return false
  }

  const o = value as Record<string, unknown>

  if (o.status !== 'healthy' && o.status !== 'unhealthy') {
    return false
  }

  if (typeof o.model !== 'object' || o.model === null) {
    return false
  }

  const model = o.model as Record<string, unknown>

  if (typeof model.embedding !== 'object' || model.embedding === null) {
    return false
  }

  if (typeof model.llm !== 'object' || model.llm === null) {
    return false
  }

  if (typeof o.vector_db !== 'object' || o.vector_db === null) {
    return false
  }

  if (typeof o.worker !== 'object' || o.worker === null) {
    return false
  }

  if (typeof o.storage !== 'object' || o.storage === null) {
    return false
  }

  return true
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`)

  const text = await res.text()
  let parsed: unknown

  try {
    parsed = text ? JSON.parse(text) : null
  } catch {
    throw new Error('Health endpoint returned invalid JSON')
  }

  if (res.status !== 200 && res.status !== 503) {
    throw new Error(`Health check failed (${res.status})`)
  }

  if (!isHealthPayload(parsed)) {
    throw new Error('Health endpoint returned unexpected payload')
  }

  return parsed
}
