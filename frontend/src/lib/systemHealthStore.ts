import { ref } from 'vue'
import { fetchHealth, type HealthResponse } from '../api/health'

export const systemHealth = ref<HealthResponse | null>(null)
export const systemHealthUnreachable = ref(false)

export async function refreshSystemHealth(): Promise<void> {
  try {
    systemHealth.value = await fetchHealth()
    systemHealthUnreachable.value = false
  } catch {
    systemHealthUnreachable.value = true
  }
}

let pollTimer: ReturnType<typeof setInterval> | null = null

export function startSystemHealthPolling(): void {
  void refreshSystemHealth()

  if (pollTimer == null) {
    pollTimer = setInterval(() => void refreshSystemHealth(), 4000)
  }
}

export function stopSystemHealthPolling(): void {
  if (pollTimer != null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}
