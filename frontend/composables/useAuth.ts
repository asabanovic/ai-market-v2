interface User {
  id: string
  email: string
  name: string
  first_name?: string
  last_name?: string
  is_admin?: boolean
  phone?: string
  city?: string
  first_search_reward_claimed?: boolean
}

interface LoginCredentials {
  email: string
  password: string
}

interface AuthResponse {
  token: string
  user: User
}

export const useAuth = () => {
  const api = useApi()
  const user = useState<User | null>('user', () => null)
  const authReady = useState<boolean>('authReady', () => false)
  const isAuthenticated = computed(() => !!user.value)

  const login = async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password })

    if (process.client) {
      localStorage.setItem('token', response.token)
    }

    user.value = response.user
    return response
  }

  const logout = () => {
    if (process.client) {
      localStorage.removeItem('token')
    }
    user.value = null
    navigateTo('/prijava')
  }

  const checkAuth = async () => {
    if (process.client) {
      const token = localStorage.getItem('token')
      if (token) {
        try {
          const response = await api.get('/auth/verify')
          user.value = response.user
        } catch (error) {
          logout()
        }
      }
      authReady.value = true
    }
  }

  const refreshUser = async () => {
    if (process.client) {
      const token = localStorage.getItem('token')
      if (token) {
        try {
          const response = await api.get('/auth/verify')
          user.value = response.user
        } catch (error) {
          console.error('Failed to refresh user:', error)
        }
      }
    }
  }

  return {
    user,
    isAuthenticated,
    authReady,
    login,
    logout,
    checkAuth,
    refreshUser
  }
}
