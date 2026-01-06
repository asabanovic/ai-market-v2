/**
 * PWA Install Plugin
 * Initializes PWA install tracking on client side
 */

export default defineNuxtPlugin(() => {
  const { initialize } = usePwaInstall()

  // Initialize on mount
  onNuxtReady(() => {
    initialize()
  })
})
