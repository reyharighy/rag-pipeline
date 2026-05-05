
function devApiOrigin(): string {
  if (typeof window === 'undefined') {
    return 'http://localhost:8000'
  }

  const host = window.location.hostname
  const hostPart = host.includes(':') ? `[${host}]` : host

  return `http://${hostPart}:8000`
}

function resolveApiBase(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL as string | undefined

  if (fromEnv != null && fromEnv !== '') {
    return fromEnv.replace(/\/$/, '')
  }

  if (import.meta.env.DEV) {
    return devApiOrigin()
  }

  return 'http://localhost:8000'
}

export const API_BASE_URL = resolveApiBase()
