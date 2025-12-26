<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Header with Back Button -->
      <div class="mb-8">
        <NuxtLink
          to="/admin"
          class="inline-flex items-center text-sm text-gray-500 hover:text-purple-600 mb-4 transition-colors"
        >
          <Icon name="mdi:arrow-left" class="w-4 h-4 mr-1" />
          Nazad na Dashboard
        </NuxtLink>
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-gray-900 mb-2">Social Media</h1>
            <p class="text-gray-600">Automatsko objavljivanje na Facebook stranici</p>
          </div>
          <button
            @click="generatePosts"
            :disabled="generating"
            class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
          >
            <Icon v-if="generating" name="mdi:loading" class="w-5 h-5 animate-spin" />
            <Icon v-else name="mdi:refresh" class="w-5 h-5" />
            Generiši postove
          </button>
        </div>
      </div>

      <!-- Config Status -->
      <div class="bg-white rounded-lg shadow p-4 mb-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
              <Icon name="mdi:facebook" class="w-6 h-6 text-blue-600" />
              <span class="font-medium">Facebook</span>
            </div>
            <span
              :class="[
                'px-2 py-1 rounded-full text-xs font-medium',
                config.facebook?.enabled
                  ? 'bg-green-100 text-green-700'
                  : 'bg-yellow-100 text-yellow-700'
              ]"
            >
              {{ config.facebook?.enabled ? 'Aktivno' : 'DEV MODE' }}
            </span>
          </div>
          <div class="text-sm text-gray-500">
            Postovi: {{ config.posting_times?.join(', ') || '09:00, 12:00, 15:00, 18:00' }}
          </div>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Zakazano</p>
              <p class="text-3xl font-bold text-blue-600">{{ stats.scheduled }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
              <Icon name="mdi:clock-outline" class="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Objavljeno</p>
              <p class="text-3xl font-bold text-green-600">{{ stats.published }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
              <Icon name="mdi:check-circle" class="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Neuspjelo</p>
              <p class="text-3xl font-bold text-red-600">{{ stats.failed }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
              <Icon name="mdi:alert-circle" class="w-6 h-6 text-red-600" />
            </div>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-12">
        <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
      </div>

      <!-- Schedule View -->
      <div v-else class="space-y-6">
        <div v-for="day in days" :key="day.date" class="bg-white rounded-lg shadow overflow-hidden">
          <!-- Day Header -->
          <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-gray-900">
                  {{ formatDayName(day.day_name) }}
                </h3>
                <p class="text-sm text-gray-500">{{ formatDate(day.date) }}</p>
              </div>
              <span class="text-sm text-gray-500">
                {{ day.posts.length }} post{{ day.posts.length !== 1 ? 'a' : '' }}
              </span>
            </div>
          </div>

          <!-- Posts Grid -->
          <div v-if="day.posts.length > 0" class="p-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div
              v-for="post in day.posts"
              :key="post.id"
              class="border rounded-lg p-4 relative"
              :class="{
                'border-blue-200 bg-blue-50': post.status === 'scheduled',
                'border-green-200 bg-green-50': post.status === 'published',
                'border-red-200 bg-red-50': post.status === 'failed',
                'border-gray-200 bg-gray-50': post.status === 'cancelled'
              }"
            >
              <!-- Time & Status -->
              <div class="flex items-center justify-between mb-3">
                <span class="font-medium text-gray-900">
                  {{ formatTime(post.scheduled_time) }}
                </span>
                <span
                  :class="[
                    'px-2 py-0.5 rounded text-xs font-medium',
                    {
                      'bg-blue-100 text-blue-700': post.status === 'scheduled',
                      'bg-green-100 text-green-700': post.status === 'published',
                      'bg-red-100 text-red-700': post.status === 'failed',
                      'bg-gray-100 text-gray-700': post.status === 'cancelled'
                    }
                  ]"
                >
                  {{ statusLabel(post.status) }}
                </span>
              </div>

              <!-- Products List -->
              <div class="space-y-2 mb-4">
                <div
                  v-for="(product, idx) in post.products?.slice(0, 3)"
                  :key="idx"
                  class="text-xs"
                >
                  <div class="font-medium text-gray-800 truncate">{{ product.title }}</div>
                  <div class="text-gray-500 flex items-center gap-1">
                    <span class="text-green-600 font-medium">{{ product.discount_price?.toFixed(2) }} KM</span>
                    <span class="line-through">{{ product.base_price?.toFixed(2) }}</span>
                    <span class="text-red-500">-{{ product.discount_pct }}%</span>
                  </div>
                </div>
                <div v-if="post.products?.length > 3" class="text-xs text-gray-400">
                  +{{ post.products.length - 3 }} više...
                </div>
              </div>

              <!-- Actions -->
              <div v-if="post.status === 'scheduled'" class="flex gap-2">
                <button
                  @click="regeneratePost(post.id)"
                  class="flex-1 px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50"
                  title="Regeneriši"
                >
                  <Icon name="mdi:refresh" class="w-4 h-4" />
                </button>
                <button
                  @click="publishPost(post.id)"
                  class="flex-1 px-2 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700"
                  title="Objavi sad"
                >
                  <Icon name="mdi:send" class="w-4 h-4" />
                </button>
                <button
                  @click="deletePost(post.id)"
                  class="px-2 py-1 text-xs bg-red-100 text-red-600 rounded hover:bg-red-200"
                  title="Obriši"
                >
                  <Icon name="mdi:delete" class="w-4 h-4" />
                </button>
              </div>

              <!-- Error message -->
              <div v-if="post.status === 'failed' && post.error_message" class="mt-2 text-xs text-red-600">
                {{ post.error_message }}
              </div>
            </div>
          </div>

          <!-- Empty state -->
          <div v-else class="p-6 text-center text-gray-500">
            <Icon name="mdi:calendar-blank" class="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p>Nema zakazanih postova</p>
          </div>
        </div>
      </div>

      <!-- Post Preview Modal -->
      <div
        v-if="selectedPost"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        @click.self="selectedPost = null"
      >
        <div class="bg-white rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
          <div class="p-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold">Pregled posta</h3>
              <button @click="selectedPost = null" class="text-gray-400 hover:text-gray-600">
                <Icon name="mdi:close" class="w-6 h-6" />
              </button>
            </div>
            <pre class="whitespace-pre-wrap text-sm bg-gray-50 p-4 rounded">{{ selectedPost.content }}</pre>
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

const { $api } = useNuxtApp()

const loading = ref(true)
const generating = ref(false)
const days = ref<any[]>([])
const stats = ref({
  scheduled: 0,
  published: 0,
  failed: 0
})
const config = ref<any>({})
const selectedPost = ref<any>(null)

// Day name translations
const dayNames: Record<string, string> = {
  'Monday': 'Ponedjeljak',
  'Tuesday': 'Utorak',
  'Wednesday': 'Srijeda',
  'Thursday': 'Cetvrtak',
  'Friday': 'Petak',
  'Saturday': 'Subota',
  'Sunday': 'Nedjelja'
}

function formatDayName(name: string): string {
  return dayNames[name] || name
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('bs-BA', { day: 'numeric', month: 'long' })
}

function formatTime(isoString: string): string {
  const date = new Date(isoString)
  // Add 1 hour for Bosnia timezone
  date.setHours(date.getHours() + 1)
  return date.toLocaleTimeString('bs-BA', { hour: '2-digit', minute: '2-digit' })
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    'scheduled': 'Zakazano',
    'published': 'Objavljeno',
    'failed': 'Neuspjelo',
    'cancelled': 'Otkazano'
  }
  return labels[status] || status
}

async function loadPosts() {
  loading.value = true
  try {
    const response = await $api('/api/admin/social/posts?days=5')
    days.value = response.days || []
    stats.value = response.stats || { scheduled: 0, published: 0, failed: 0 }
  } catch (error) {
    console.error('Failed to load posts:', error)
  } finally {
    loading.value = false
  }
}

async function loadConfig() {
  try {
    const response = await $api('/api/admin/social/config')
    config.value = response
  } catch (error) {
    console.error('Failed to load config:', error)
  }
}

async function generatePosts() {
  generating.value = true
  try {
    const response = await $api('/api/admin/social/generate', {
      method: 'POST'
    })
    alert(`Kreirano ${response.created} postova`)
    await loadPosts()
  } catch (error) {
    console.error('Failed to generate posts:', error)
    alert('Greska pri generisanju postova')
  } finally {
    generating.value = false
  }
}

async function regeneratePost(postId: number) {
  try {
    await $api(`/api/admin/social/posts/${postId}/regenerate`, {
      method: 'POST'
    })
    await loadPosts()
  } catch (error) {
    console.error('Failed to regenerate post:', error)
    alert('Greska pri regenerisanju')
  }
}

async function publishPost(postId: number) {
  if (!confirm('Objavi ovaj post sada?')) return

  try {
    await $api(`/api/admin/social/posts/${postId}/publish`, {
      method: 'POST'
    })
    await loadPosts()
  } catch (error) {
    console.error('Failed to publish post:', error)
    alert('Greska pri objavljivanju')
  }
}

async function deletePost(postId: number) {
  if (!confirm('Obriši ovaj zakazani post?')) return

  try {
    await $api(`/api/admin/social/posts/${postId}`, {
      method: 'DELETE'
    })
    await loadPosts()
  } catch (error) {
    console.error('Failed to delete post:', error)
    alert('Greska pri brisanju')
  }
}

onMounted(() => {
  loadPosts()
  loadConfig()
})
</script>
