/**
 * PWA Install Composable
 * Handles PWA install prompt, tracking, and state
 */

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

interface PwaInstallState {
  canInstall: boolean
  isInstalled: boolean
  isIOS: boolean
  isStandalone: boolean
  platform: 'android' | 'ios' | 'desktop' | null
  browser: string | null
}

let deferredPrompt: BeforeInstallPromptEvent | null = null
const state = reactive<PwaInstallState>({
  canInstall: false,
  isInstalled: false,
  isIOS: false,
  isStandalone: false,
  platform: null,
  browser: null
})

export function usePwaInstall() {
  const config = useRuntimeConfig()

  // Generate or get session ID
  const getSessionId = () => {
    if (typeof window === 'undefined') return null
    let sessionId = sessionStorage.getItem('pwa_session_id')
    if (!sessionId) {
      sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36)
      sessionStorage.setItem('pwa_session_id', sessionId)
    }
    return sessionId
  }

  // Detect platform
  const detectPlatform = () => {
    if (typeof window === 'undefined') return null
    const ua = navigator.userAgent.toLowerCase()
    if (/iphone|ipad|ipod/.test(ua)) return 'ios'
    if (/android/.test(ua)) return 'android'
    return 'desktop'
  }

  // Detect browser
  const detectBrowser = () => {
    if (typeof window === 'undefined') return null
    const ua = navigator.userAgent
    if (ua.includes('Chrome') && !ua.includes('Edg')) return 'Chrome'
    if (ua.includes('Safari') && !ua.includes('Chrome')) return 'Safari'
    if (ua.includes('Firefox')) return 'Firefox'
    if (ua.includes('Edg')) return 'Edge'
    if (ua.includes('Opera') || ua.includes('OPR')) return 'Opera'
    return 'Other'
  }

  // Track event to backend
  const trackEvent = async (event: string) => {
    try {
      const apiBase = config.public.apiBase || 'http://localhost:5001'
      const token = localStorage.getItem('token')

      await fetch(`${apiBase}/api/track/pwa-install`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          event,
          session_id: getSessionId(),
          page_url: window.location.pathname,
          platform: state.platform,
          browser: state.browser
        })
      })
    } catch (e) {
      console.error('Failed to track PWA event:', e)
    }
  }

  // Initialize - detect state
  const initialize = () => {
    if (typeof window === 'undefined') return

    state.platform = detectPlatform()
    state.browser = detectBrowser()
    state.isIOS = state.platform === 'ios'

    // Check if running in standalone mode (already installed)
    state.isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
      (window.navigator as any).standalone === true

    if (state.isStandalone) {
      state.isInstalled = true
      trackEvent('standalone_launch')
    }

    // Listen for beforeinstallprompt
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault()
      deferredPrompt = e as BeforeInstallPromptEvent
      state.canInstall = true
      trackEvent('prompt_shown')
    })

    // Listen for app installed
    window.addEventListener('appinstalled', () => {
      state.isInstalled = true
      state.canInstall = false
      deferredPrompt = null
      trackEvent('installed')
    })
  }

  // Trigger install prompt
  const promptInstall = async (): Promise<boolean> => {
    if (!deferredPrompt) {
      console.log('No install prompt available')
      return false
    }

    try {
      await deferredPrompt.prompt()
      const { outcome } = await deferredPrompt.userChoice

      if (outcome === 'accepted') {
        trackEvent('prompt_accepted')
        return true
      } else {
        trackEvent('prompt_dismissed')
        return false
      }
    } catch (e) {
      console.error('Install prompt error:', e)
      return false
    } finally {
      deferredPrompt = null
      state.canInstall = false
    }
  }

  // Check if should show custom prompt (not recently dismissed)
  const shouldShowPrompt = () => {
    if (typeof window === 'undefined') return false
    if (state.isInstalled || state.isStandalone) return false

    const lastDismissed = localStorage.getItem('pwa_prompt_dismissed')
    if (lastDismissed) {
      const daysSinceDismissed = (Date.now() - parseInt(lastDismissed)) / (1000 * 60 * 60 * 24)
      // Show again after 7 days
      if (daysSinceDismissed < 7) return false
    }

    // For iOS, always allow showing instructions
    if (state.isIOS) return true

    // For others, only show if browser prompt is available
    return state.canInstall
  }

  // Mark prompt as dismissed (for cooldown)
  const dismissPrompt = () => {
    localStorage.setItem('pwa_prompt_dismissed', Date.now().toString())
    trackEvent('prompt_dismissed')
  }

  // Get iOS install instructions
  const getIOSInstructions = () => {
    return {
      title: 'Instalirajte Popust.ba',
      steps: [
        'Dodirnite ikonu za dijeljenje na dnu ekrana',
        'Skrolajte dolje i dodirnite "Dodaj na početni ekran"',
        'Dodirnite "Dodaj" u gornjem desnom uglu'
      ]
    }
  }

  return {
    state: readonly(state),
    initialize,
    promptInstall,
    shouldShowPrompt,
    dismissPrompt,
    getIOSInstructions,
    trackEvent
  }
}
