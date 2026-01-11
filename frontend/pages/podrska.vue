<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 flex-shrink-0">
      <div class="max-w-3xl mx-auto px-4 py-4">
        <div class="flex items-center gap-4">
          <NuxtLink to="/" class="text-gray-500 hover:text-gray-700">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </NuxtLink>
          <div>
            <h1 class="text-xl font-semibold text-gray-900">Podrška</h1>
            <p class="text-sm text-gray-500">Razgovor sa Popust.ba timom</p>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-3xl mx-auto px-4 py-6 flex-1 w-full flex flex-col pb-20 md:pb-6">
      <!-- Loading -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-indigo-600">
          <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Učitavanje...</span>
        </div>
      </div>

      <div v-else class="flex-1 flex flex-col">
        <!-- Info box for new users -->
        <div v-if="messages.length === 0" class="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-4">
          <div class="flex items-start gap-3">
            <svg class="w-6 h-6 text-indigo-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h3 class="font-medium text-indigo-900">Dobrodošli u Podršku</h3>
              <p class="text-sm text-indigo-700 mt-1">
                Ovdje možete direktno komunicirati sa našim timom. Bilo da imate pitanja, prijedloge ili trebate pomoć - tu smo za vas!
              </p>
            </div>
          </div>
        </div>

        <!-- Chat Messages -->
        <div class="bg-white rounded-lg border border-gray-200 mb-4 flex-1">
          <div class="p-4 min-h-[250px] md:min-h-[300px] max-h-[50vh] md:max-h-[500px] overflow-y-auto space-y-4" ref="messagesContainer">
            <div v-if="messages.length === 0" class="text-center text-gray-500 py-8">
              <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <p>Nemate poruka.</p>
              <p class="text-sm mt-1">Pošaljite nam poruku ispod!</p>
            </div>

            <div
              v-for="msg in messages"
              :key="msg.id"
              :class="[
                'flex',
                msg.sender_type === 'user' ? 'justify-end' : 'justify-start'
              ]"
            >
              <div
                :class="[
                  'max-w-[80%] rounded-lg px-4 py-2',
                  msg.sender_type === 'user'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                ]"
              >
                <div v-if="msg.sender_type === 'admin'" class="text-xs font-medium text-indigo-600 mb-1">
                  Popust.ba Podrška
                </div>
                <p class="text-sm whitespace-pre-wrap">{{ msg.message }}</p>
                <p
                  :class="[
                    'text-xs mt-1',
                    msg.sender_type === 'user' ? 'text-indigo-200' : 'text-gray-500'
                  ]"
                >
                  {{ formatDateTime(msg.created_at) }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Message Input -->
        <div class="bg-white rounded-lg border border-gray-200 p-3 flex-shrink-0">
          <div class="flex items-end gap-2">
            <textarea
              v-model="newMessage"
              placeholder="Napiši poruku..."
              rows="1"
              class="flex-1 resize-none border border-gray-300 rounded-full px-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 placeholder-gray-400 min-h-[42px] max-h-[120px]"
              @keydown.ctrl.enter="sendMessage"
              @keydown.meta.enter="sendMessage"
              @input="autoResize"
              ref="textareaRef"
            />
            <button
              @click="sendMessage"
              :disabled="isSending || !newMessage.trim()"
              class="bg-indigo-600 text-white w-10 h-10 rounded-full flex items-center justify-center hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex-shrink-0"
            >
              <svg v-if="!isSending" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
              <svg v-else class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth']
})

const { get, post } = useApi()

const isLoading = ref(true)
const isSending = ref(false)
const messages = ref<any[]>([])
const newMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

onMounted(async () => {
  await loadMessages()
})

async function loadMessages() {
  isLoading.value = true
  try {
    const data = await get('/api/support/messages')
    messages.value = data.messages || []

    nextTick(() => {
      scrollToBottom()
    })
  } catch (error) {
    console.error('Error loading messages:', error)
  } finally {
    isLoading.value = false
  }
}

async function sendMessage() {
  if (!newMessage.value.trim() || isSending.value) return

  isSending.value = true
  try {
    const data = await post('/api/support/send', {
      message: newMessage.value.trim()
    })

    if (data.success && data.message) {
      messages.value.push(data.message)
      newMessage.value = ''
      resetTextarea()

      nextTick(() => {
        scrollToBottom()
      })
    }
  } catch (error) {
    console.error('Error sending message:', error)
  } finally {
    isSending.value = false
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function autoResize() {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 120) + 'px'
  }
}

function resetTextarea() {
  if (textareaRef.value) {
    textareaRef.value.style.height = '42px'
  }
}

function formatDateTime(dateString: string) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('sr-RS', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

useSeoMeta({
  title: 'Podrška - Popust.ba',
  description: 'Kontaktirajte naš tim za pomoć',
})
</script>
