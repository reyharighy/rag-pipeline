import { ref, type Ref } from 'vue'

export type ToastVariant = 'success' | 'error'

export interface ToastPayload {
  id: number
  message: string
  variant: ToastVariant
}

const AUTO_DISMISS_MS = 5000

let toastSeq = 0

export const toastCurrent: Ref<ToastPayload | null> = ref(null)

let hideTimer: ReturnType<typeof setTimeout> | null = null

export function dismissToast(): void {
  if (hideTimer != null) {
    clearTimeout(hideTimer)
    hideTimer = null
  }

  toastCurrent.value = null
}

export function pushToast(message: string, variant: ToastVariant): void {
  if (hideTimer != null) {
    clearTimeout(hideTimer)
    hideTimer = null
  }

  toastCurrent.value = { id: ++toastSeq, message, variant }

  hideTimer = setTimeout(() => {
    hideTimer = null
    toastCurrent.value = null
  }, AUTO_DISMISS_MS)
}
