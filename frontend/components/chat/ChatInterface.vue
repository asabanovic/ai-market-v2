<template>
  <div class="flex flex-col h-full">
    <!-- Chat messages -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6 space-y-6">
      <TransitionGroup name="message">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="[
            'flex',
            message.role === 'user' ? 'justify-end' : 'justify-start'
          ]"
        >
          <div
            :class="[
              'max-w-[80%] rounded-2xl px-6 py-4',
              message.role === 'user'
                ? 'bg-gradient-to-r from-primary-500 to-accent-500 text-white'
                : 'glass'
            ]"
          >
            <p class="text-sm leading-relaxed">{{ message.content }}</p>
            <span class="text-xs opacity-70 mt-2 block">
              {{ formatTime(message.timestamp) }}
            </span>
          </div>
        </div>
      </TransitionGroup>

      <!-- Loading indicator -->
      <div v-if="isLoading" class="flex justify-start">
        <div class="glass rounded-2xl px-6 py-4">
          <div class="flex space-x-2">
            <div class="w-2 h-2 bg-primary-500 rounded-full animate-bounce"></div>
            <div class="w-2 h-2 bg-primary-500 rounded-full animate-bounce animate-delay-100"></div>
            <div class="w-2 h-2 bg-primary-500 rounded-full animate-bounce animate-delay-200"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Input area -->
    <div class="border-t border-gray-200 dark:border-gray-800 p-6 glass">
      <form @submit.prevent="sendMessage" class="flex items-end space-x-4">
        <div class="flex-1">
          <textarea
            v-model="inputMessage"
            @keydown.enter.prevent="handleEnter"
            placeholder="Pitaj me o proizvodima..."
            rows="1"
            class="input resize-none"
          ></textarea>
        </div>
        <button
          type="submit"
          :disabled="!inputMessage.trim() || isLoading"
          class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Icon name="mdi:send" class="w-5 h-5" />
        </button>
      </form>
      <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
        Pritisni Enter za slanje, Shift + Enter za novi red
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const { sendChatMessage } = useChat()
const messagesContainer = ref<HTMLElement>()
const messages = ref<Message[]>([
  {
    id: '1',
    role: 'assistant',
    content: 'Zdravo! Ja sam AI asistent za AI Pijaca. Kako mogu da vam pomognem danas?',
    timestamp: new Date()
  }
])
const inputMessage = ref('')
const isLoading = ref(false)

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: inputMessage.value,
    timestamp: new Date()
  }

  messages.value.push(userMessage)
  inputMessage.value = ''
  isLoading.value = true

  try {
    const response = await sendChatMessage(userMessage.content)

    const aiMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response.reply,
      timestamp: new Date()
    }

    messages.value.push(aiMessage)
  } catch (error) {
    console.error('Error sending message:', error)
    // TODO: Show error toast
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const handleEnter = (event: KeyboardEvent) => {
  if (!event.shiftKey) {
    sendMessage()
  }
}

const formatTime = (date: Date) => {
  return new Intl.DateTimeFormat('bs-BA', {
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.message-enter-active {
  transition: all 0.3s ease;
}

.message-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.message-leave-active {
  transition: all 0.2s ease;
}

.message-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
