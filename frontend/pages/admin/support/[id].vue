<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-6">
        <div class="flex items-center gap-4">
          <NuxtLink to="/admin/support" class="text-gray-500 hover:text-gray-700">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </NuxtLink>
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">Razgovor sa korisnikom</h1>
            <p v-if="userInfo" class="mt-1 text-sm text-gray-600">{{ userInfo.name || userInfo.email }}</p>
          </div>
        </div>
      </div>

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

      <div v-else>
        <!-- User Info Card -->
        <div v-if="userInfo" class="bg-white rounded-lg border border-gray-200 p-4 mb-4">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold text-xl">
              {{ (userInfo.name || userInfo.email || '?')[0].toUpperCase() }}
            </div>
            <div>
              <div class="font-semibold text-gray-900">{{ userInfo.name || userInfo.email }}</div>
              <div class="text-sm text-gray-500">{{ userInfo.email }}</div>
              <div class="text-xs text-gray-400 mt-1">Registrovan: {{ formatDate(userInfo.created_at) }}</div>
            </div>
          </div>
        </div>

        <!-- Chat Messages -->
        <div class="bg-white rounded-lg border border-gray-200 mb-4">
          <div class="p-4 border-b border-gray-200">
            <h2 class="font-semibold text-gray-900">Poruke</h2>
          </div>

          <div class="p-4 min-h-[300px] max-h-[500px] overflow-y-auto space-y-4" ref="messagesContainer">
            <div v-if="messages.length === 0" class="text-center text-gray-500 py-8">
              Nema poruka. Pošaljite prvu poruku korisniku.
            </div>

            <div
              v-for="msg in messages"
              :key="msg.id"
              :class="[
                'flex',
                msg.sender_type === 'admin' ? 'justify-end' : 'justify-start'
              ]"
            >
              <div
                :class="[
                  'max-w-[70%] rounded-lg px-4 py-2',
                  msg.sender_type === 'admin'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                ]"
              >
                <p class="text-sm whitespace-pre-wrap">{{ msg.message }}</p>
                <p
                  :class="[
                    'text-xs mt-1',
                    msg.sender_type === 'admin' ? 'text-indigo-200' : 'text-gray-500'
                  ]"
                >
                  {{ formatDateTime(msg.created_at) }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Message Input -->
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="flex gap-4">
            <textarea
              v-model="newMessage"
              placeholder="Napiši poruku..."
              rows="3"
              class="flex-1 resize-none border border-gray-300 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 placeholder-gray-400"
              @keydown.ctrl.enter="sendMessage"
            />
            <div class="flex flex-col gap-2">
              <button
                @click="sendMessage"
                :disabled="isSending || !newMessage.trim()"
                class="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {{ isSending ? 'Slanje...' : 'Pošalji' }}
              </button>
              <label class="flex items-center gap-2 text-xs text-gray-600">
                <input type="checkbox" v-model="sendEmailNotification" class="rounded">
                Pošalji email
              </label>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-2">Ctrl+Enter za brzo slanje</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth', 'admin']
})

const route = useRoute()
const { get, post } = useApi()

const userId = computed(() => route.params.id as string)

const isLoading = ref(true)
const isSending = ref(false)
const userInfo = ref<any>(null)
const messages = ref<any[]>([])
const newMessage = ref('')
const sendEmailNotification = ref(true)
const messagesContainer = ref<HTMLElement | null>(null)

onMounted(async () => {
  await loadData()
})

async function loadData() {
  isLoading.value = true
  try {
    const data = await get(`/api/support/admin/messages/${userId.value}`)
    userInfo.value = data.user
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
    const data = await post('/api/support/admin/send', {
      user_id: userId.value,
      message: newMessage.value.trim(),
      send_email: sendEmailNotification.value
    })

    if (data.success && data.message) {
      messages.value.push(data.message)
      newMessage.value = ''

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

function formatDate(dateString: string) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-RS', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

useSeoMeta({
  title: 'Razgovor - Podrška - Admin - Popust.ba',
})
</script>
