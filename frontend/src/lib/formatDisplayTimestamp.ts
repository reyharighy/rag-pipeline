export function formatDisplayTimestamp(iso: string | null | undefined): string {
  if (iso == null || String(iso).trim() === '') {
    return '—'
  }

  const raw = String(iso).trim()
  let d = new Date(raw)

  if (Number.isNaN(d.getTime())) {
    const normalized = raw.includes('T') ? raw : raw.replace(/^(\d{4}-\d{2}-\d{2})\s+/, '$1T')
    d = new Date(normalized)
  }

  if (Number.isNaN(d.getTime())) {
    return '—'
  }

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
