<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-6">
        <div class="flex items-center gap-4">
          <NuxtLink to="/admin/feedback" class="text-gray-500 hover:text-gray-700">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </NuxtLink>
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">Odgovori na povratnu informaciju</h1>
            <p v-if="userInfo" class="mt-1 text-sm text-gray-600" data-pii>{{ userInfo.name || userInfo.email }}</p>
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
        <!-- Original Feedback Card -->
        <div v-if="feedback" class="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-gray-900">Originalna povratna informacija</h2>
            <div v-if="feedback.rating" class="flex items-center gap-1">
              <template v-for="star in 5" :key="star">
                <svg
                  class="w-5 h-5"
                  :class="star <= feedback.rating ? 'text-yellow-400' : 'text-gray-300'"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </template>
            </div>
          </div>

          <div class="text-xs text-gray-500 mb-4">
            {{ formatDateTime(feedback.created_at) }}
            <span v-if="feedback.trigger_type" class="ml-2 px-1.5 py-0.5 bg-gray-100 rounded">{{ feedback.trigger_type }}</span>
            <span v-if="feedback.device_type" class="ml-1 px-1.5 py-0.5 bg-gray-100 rounded">{{ feedback.device_type }}</span>
          </div>

          <div class="space-y-3">
            <div v-if="feedback.what_to_improve" class="bg-gray-50 rounded-lg p-3">
              <div class="text-xs font-medium text-gray-500 mb-1">Šta biste poboljšali?</div>
              <p class="text-sm text-gray-900">{{ feedback.what_to_improve }}</p>
            </div>
            <div v-if="feedback.how_to_help" class="bg-gray-50 rounded-lg p-3">
              <div class="text-xs font-medium text-gray-500 mb-1">Kako možemo pomoći?</div>
              <p class="text-sm text-gray-900">{{ feedback.how_to_help }}</p>
            </div>
            <div v-if="feedback.what_would_make_you_use" class="bg-gray-50 rounded-lg p-3">
              <div class="text-xs font-medium text-gray-500 mb-1">Šta bi vas natjeralo da koristite aplikaciju svaki put?</div>
              <p class="text-sm text-gray-900">{{ feedback.what_would_make_you_use }}</p>
            </div>
            <div v-if="feedback.comments" class="bg-blue-50 rounded-lg p-3">
              <div class="text-xs font-medium text-blue-600 mb-1">Dodatni komentari</div>
              <p class="text-sm text-gray-900">{{ feedback.comments }}</p>
            </div>
          </div>
        </div>

        <!-- Anonymous feedback warning -->
        <div v-if="!userInfo" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div class="flex items-center">
            <svg class="w-5 h-5 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span class="text-sm text-yellow-700">Ova povratna informacija je od anonimnog korisnika. Ne možete odgovoriti.</span>
          </div>
        </div>

        <!-- Chat Messages -->
        <div v-if="userInfo" class="bg-white rounded-lg border border-gray-200 mb-4">
          <div class="p-4 border-b border-gray-200">
            <h2 class="font-semibold text-gray-900">Razgovor</h2>
          </div>

          <div class="p-4 min-h-[200px] max-h-[400px] overflow-y-auto space-y-4" ref="messagesContainer">
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
        <div v-if="userInfo" class="bg-white rounded-lg border border-gray-200 p-4">
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

const feedbackId = computed(() => route.params.id as string)

const isLoading = ref(true)
const isSending = ref(false)
const feedback = ref<any>(null)
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
    const data = await get(`/api/support/admin/feedback/${feedbackId.value}`)
    feedback.value = data.feedback
    userInfo.value = data.user
    messages.value = data.messages || []

    // Scroll to bottom after messages load
    nextTick(() => {
      scrollToBottom()
    })
  } catch (error) {
    console.error('Error loading feedback:', error)
  } finally {
    isLoading.value = false
  }
}

async function sendMessage() {
  if (!newMessage.value.trim() || isSending.value) return

  isSending.value = true
  try {
    const data = await post(`/api/support/admin/feedback/${feedbackId.value}/reply`, {
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

useSeoMeta({
  title: 'Odgovori na povratnu informaciju - Admin - Popust.ba',
})
</script>
