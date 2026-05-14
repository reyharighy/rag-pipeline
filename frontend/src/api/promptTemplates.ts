import { API_BASE_URL } from '../config'

export type PromptTemplateRow = {
  key: string
  body: string
  updated_at: string
}

export type PromptTemplatesResponse = {
  templates: PromptTemplateRow[]
}

export async function fetchPromptTemplates(): Promise<PromptTemplateRow[]> {
  const res = await fetch(`${API_BASE_URL}/prompt-templates`)

  if (!res.ok) {
    throw new Error(`Failed to load prompt templates (${res.status})`)
  }

  const data = (await res.json()) as PromptTemplatesResponse

  return data.templates
}

export async function updatePromptTemplate(key: string, body: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/prompt-templates/${encodeURIComponent(key)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ body }),
  })

  if (!res.ok) {
    let detail = res.statusText

    try {
      const err = (await res.json()) as { detail?: string | string[] }

      if (typeof err.detail === 'string') {
        detail = err.detail
      } else if (Array.isArray(err.detail)) {
        detail = err.detail.map((x) => String(x)).join('; ')
      }
    } catch {
      /* ignore */
    }

    throw new Error(detail || `Update failed (${res.status})`)
  }
}
