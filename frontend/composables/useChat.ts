interface ChatResponse {
  reply: string
  products?: any[]
  timestamp: string
}

export const useChat = () => {
  const api = useApi()

  const sendChatMessage = async (message: string): Promise<ChatResponse> => {
    return await api.post('/api/chat', { message })
  }

  return {
    sendChatMessage
  }
}
