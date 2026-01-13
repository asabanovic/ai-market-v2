interface User {
  id: string
  email: string
  name: string
  first_name?: string
  last_name?: string
  is_admin?: boolean
  is_verified?: boolean
  phone?: string
  city?: string
  city_id?: number | null
  first_search_reward_claimed?: boolean
  onboarding_completed?: boolean
  welcome_guide_seen?: boolean
  preferences?: Record<string, any>
  // Streak info
  current_streak?: number
  longest_streak?: number
  next_milestone?: number | null
  next_milestone_bonus?: number | null
  milestones?: Record<number, number>
}

interface BonusAwarded {
  daily_bonus: number
  streak_bonus: number
  current_streak: number
  milestone_reached: number | null
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
  const lastBonusAwarded = useState<BonusAwarded | null>('lastBonusAwarded', () => null)
  const isAuthenticated = computed(() => !!user.value)

  // Token accessor for components that need direct access
  const token = computed(() => {
    if (process.client) {
      return localStorage.getItem('token')
    }
    return null
  })

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
    lastBonusAwarded.value = null
    navigateTo('/prijava')
  }

  const checkAuth = async () => {
    if (process.client) {
      const token = localStorage.getItem('token')
      if (token) {
        try {
          const response = await api.get('/auth/verify')
          user.value = response.user
          // Store bonus info if credits were awarded
          if (response.bonus_awarded) {
            lastBonusAwarded.value = response.bonus_awarded
          }
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
          // Store bonus info if credits were awarded
          if (response.bonus_awarded) {
            lastBonusAwarded.value = response.bonus_awarded
          }
        } catch (error) {
          console.error('Failed to refresh user:', error)
        }
      }
    }
  }

  const clearBonusNotification = () => {
    lastBonusAwarded.value = null
  }

  const resendVerificationEmail = async () => {
    if (!user.value?.email) {
      throw new Error('Niste prijavljeni')
    }
    const response = await api.post('/auth/resend-verification', { email: user.value.email })
    return response
  }

  const isVerified = computed(() => user.value?.is_verified !== false)

  return {
    user,
    token,
    isAuthenticated,
    isVerified,
    authReady,
    lastBonusAwarded,
    login,
    logout,
    checkAuth,
    refreshUser,
    clearBonusNotification,
    resendVerificationEmail
  }
}
