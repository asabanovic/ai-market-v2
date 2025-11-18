/**
 * Credits Toast Composable
 * Handles 402 (Insufficient Credits) errors with user-friendly toasts
 */

export interface ToastMessage {
  id: number
  type: 'info' | 'success' | 'warning' | 'error'
  title?: string
  message: string
  action?: {
    label: string
    onClick: () => void
  }
  duration?: number
}

// Global toast state (shared across all components)
const toasts = ref<ToastMessage[]>([])
let toastIdCounter = 0

export function useCreditsToast() {
  function showToast(toast: Omit<ToastMessage, 'id'>) {
    const id = ++toastIdCounter

    const newToast: ToastMessage = {
      id,
      type: toast.type || 'info',
      title: toast.title,
      message: toast.message,
      action: toast.action,
      duration: toast.duration ?? 5000 // Default 5 seconds
    }

    toasts.value.push(newToast)

    // Auto-dismiss after duration
    if (newToast.duration > 0) {
      setTimeout(() => {
        dismissToast(id)
      }, newToast.duration)
    }

    return id
  }

  function dismissToast(id: number) {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }
  }

  function handleInsufficientCredits(error?: any) {
    const message = error?.message || 'Nemate dovoljno kredita za ovu akciju'

    return showToast({
      type: 'warning',
      title: 'Nedovoljno kredita',
      message,
      action: {
        label: 'Kupi kredite',
        onClick: () => {
          // Navigate to credits/pricing page
          navigateTo('/profile?tab=credits')
        }
      },
      duration: 7000 // 7 seconds for action toasts
    })
  }

  function handleListItemLimit() {
    return showToast({
      type: 'warning',
      title: 'Limit artikala dostignut',
      message: 'Dostigli ste limit od 10 artikala u listi. Povećajte količinu postojećih ili završite kupovinu.',
      duration: 7000
    })
  }

  function handleApiError(error: any) {
    // Check if it's a 402 Insufficient Credits error
    if (error?.status === 402 || error?.code === 'INSUFFICIENT_CREDITS') {
      return handleInsufficientCredits(error)
    }

    // Check if it's a list item limit error
    if (error?.code === 'LIST_ITEM_LIMIT') {
      return handleListItemLimit()
    }

    // Generic error
    const message = error?.message || error?.error || 'Došlo je do greške'

    return showToast({
      type: 'error',
      message,
      duration: 5000
    })
  }

  function showSuccess(message: string, title?: string) {
    return showToast({
      type: 'success',
      title,
      message,
      duration: 3000
    })
  }

  function showInfo(message: string, title?: string) {
    return showToast({
      type: 'info',
      title,
      message,
      duration: 4000
    })
  }

  function showWarning(message: string, title?: string) {
    return showToast({
      type: 'warning',
      title,
      message,
      duration: 5000
    })
  }

  function showError(message: string, title?: string) {
    return showToast({
      type: 'error',
      title,
      message,
      duration: 5000
    })
  }

  function clearAll() {
    toasts.value = []
  }

  return {
    // State
    toasts: readonly(toasts),

    // Methods
    showToast,
    dismissToast,
    handleInsufficientCredits,
    handleListItemLimit,
    handleApiError,
    showSuccess,
    showInfo,
    showWarning,
    showError,
    clearAll
  }
}
