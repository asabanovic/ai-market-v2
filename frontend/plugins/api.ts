export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase

  const apiFetch = async (
    endpoint: string,
    options: RequestInit = {}
  ): Promise<any> => {
    // Ensure endpoint starts with /api
    const apiEndpoint = endpoint.startsWith('/api') ? endpoint : `/api${endpoint}`
    const url = `${baseURL}${apiEndpoint}`

    // Get auth token from localStorage (if exists)
    const token = process.client ? localStorage.getItem('token') : null

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const error: any = new Error(errorData.message || `API Error: ${response.statusText}`)
        error.statusCode = response.status
        error.status = response.status
        error.code = errorData.code
        error.data = errorData
        throw error
      }
      // ✅ 204 No Content → just return null
      if (response.status === 204) {
        return null
      }

      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  const api = {
    get: (endpoint: string, options?: RequestInit) =>
      apiFetch(endpoint, { ...options, method: 'GET' }),

    post: (endpoint: string, data?: any, options?: RequestInit) =>
      apiFetch(endpoint, {
        ...options,
        method: 'POST',
        body: JSON.stringify(data),
      }),

    put: (endpoint: string, data?: any, options?: RequestInit) =>
      apiFetch(endpoint, {
        ...options,
        method: 'PUT',
        body: JSON.stringify(data),
      }),

    patch: (endpoint: string, data?: any, options?: RequestInit) =>
      apiFetch(endpoint, {
        ...options,
        method: 'PATCH',
        body: JSON.stringify(data),
      }),

    delete: (endpoint: string, options?: RequestInit) =>
      apiFetch(endpoint, { ...options, method: 'DELETE' }),
  }

  return {
    provide: {
      api
    }
  }
})
