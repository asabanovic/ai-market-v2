export const useApi = () => {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase

  const apiFetch = async (
    endpoint: string,
    options: RequestInit = {}
  ): Promise<any> => {
    const url = `${baseURL}${endpoint}`

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
        const errorData = await response.json().catch(() => ({ error: response.statusText }))
        console.error('API Error:', errorData)
        throw new Error(errorData.error || `API Error: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  return {
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
}
