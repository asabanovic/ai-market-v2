export const useColorMode = () => {
  const preference = useState<'light' | 'dark'>('color-mode', () => 'light')

  const setColorMode = (mode: 'light' | 'dark') => {
    preference.value = mode
    if (process.client) {
      if (mode === 'dark') {
        document.documentElement.classList.add('dark')
        localStorage.setItem('color-mode', 'dark')
      } else {
        document.documentElement.classList.remove('dark')
        localStorage.setItem('color-mode', 'light')
      }
    }
  }

  // Initialize on client
  if (process.client) {
    const stored = localStorage.getItem('color-mode')
    if (stored === 'dark' || stored === 'light') {
      preference.value = stored
      if (stored === 'dark') {
        document.documentElement.classList.add('dark')
      }
    } else {
      // Check system preference
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        setColorMode('dark')
      }
    }
  }

  return {
    preference,
    value: preference,
    setColorMode
  }
}
