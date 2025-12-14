<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center gap-4">
          <NuxtLink to="/admin" class="text-gray-500 hover:text-gray-700">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </NuxtLink>
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">Analitika angažmana</h1>
            <p class="mt-1 text-sm text-gray-600">Pregled korisničke aktivnosti: glasanje, komentari, favoriti, posjete</p>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-indigo-600">
          <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Učitavanje...</span>
        </div>
      </div>

      <template v-else>
        <!-- Summary Stats Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
          <!-- Total Votes -->
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-lg">👍</span>
              <span class="text-sm text-gray-500">Glasovi</span>
            </div>
            <div class="text-2xl font-bold text-gray-900">{{ stats.total_votes || 0 }}</div>
            <div class="text-xs text-gray-500 mt-1">
              <span class="text-green-600">↑{{ stats.total_upvotes || 0 }}</span>
              <span class="text-red-600 ml-1">↓{{ stats.total_downvotes || 0 }}</span>
            </div>
          </div>

          <!-- Total Comments -->
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-lg">💬</span>
              <span class="text-sm text-gray-500">Komentari</span>
            </div>
            <div class="text-2xl font-bold text-gray-900">{{ stats.total_comments || 0 }}</div>
            <div class="text-xs text-green-600 mt-1">+{{ stats.today_comments || 0 }} danas</div>
          </div>

          <!-- Total Favorites -->
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-lg">❤️</span>
              <span class="text-sm text-gray-500">Favoriti</span>
            </div>
            <div class="text-2xl font-bold text-gray-900">{{ stats.total_favorites || 0 }}</div>
            <div class="text-xs text-green-600 mt-1">+{{ stats.today_favorites || 0 }} danas</div>
          </div>

          <!-- Proizvodi Views -->
          <div class="bg-white rounded-lg border border-blue-200 p-4 bg-blue-50">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-lg">📦</span>
              <span class="text-sm text-blue-600">Proizvodi stranica</span>
            </div>
            <div class="text-2xl font-bold text-blue-700">{{ stats.proizvodi_views_total || 0 }}</div>
            <div class="text-xs text-blue-600 mt-1">{{ stats.unique_proizvodi_users || 0 }} korisnika</div>
          </div>

          <!-- Week Stats -->
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-lg">📅</span>
              <span class="text-sm text-gray-500">Ovaj tjedan</span>
            </div>
            <div class="text-lg font-bold text-gray-900">
              {{ stats.week_votes || 0 }} glasova
            </div>
            <div class="text-xs text-gray-500 mt-1">
              {{ stats.week_comments || 0 }} kom. / {{ stats.week_favorites || 0 }} fav.
            </div>
          </div>

          <!-- Engaged Users -->
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-lg">👥</span>
              <span class="text-sm text-gray-500">Aktivni korisnici</span>
            </div>
            <div class="text-lg font-bold text-gray-900">
              {{ stats.engaged_users_votes || 0 }} glas.
            </div>
            <div class="text-xs text-gray-500 mt-1">
              {{ stats.engaged_users_comments || 0 }} kom. / {{ stats.engaged_users_favorites || 0 }} fav.
            </div>
          </div>
        </div>

        <!-- Activity Tabs -->
        <div class="mb-6">
          <div class="border-b border-gray-200">
            <nav class="-mb-px flex space-x-8">
              <button
                @click="activeTab = 'proizvodi'"
                :class="[
                  activeTab === 'proizvodi'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
                ]"
              >
                📦 Proizvodi posjete ({{ recentProizvodiViews.length }})
              </button>
              <button
                @click="activeTab = 'votes'"
                :class="[
                  activeTab === 'votes'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
                ]"
              >
                👍 Glasovi ({{ recentVotes.length }})
              </button>
              <button
                @click="activeTab = 'comments'"
                :class="[
                  activeTab === 'comments'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
                ]"
              >
                💬 Komentari ({{ recentComments.length }})
              </button>
              <button
                @click="activeTab = 'favorites'"
                :class="[
                  activeTab === 'favorites'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
                ]"
              >
                ❤️ Favoriti ({{ recentFavorites.length }})
              </button>
              <button
                @click="activeTab = 'top'"
                :class="[
                  activeTab === 'top'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
                ]"
              >
                🏆 Top korisnici
              </button>
            </nav>
          </div>
        </div>

        <!-- Tab Content -->
        <div class="bg-white rounded-lg border border-gray-200">
          <!-- Proizvodi Views Tab -->
          <div v-if="activeTab === 'proizvodi'" class="divide-y divide-gray-200">
            <div v-if="recentProizvodiViews.length === 0" class="p-8 text-center text-gray-500">
              Nema podataka o posjetama stranice Proizvodi
            </div>
            <div v-for="view in recentProizvodiViews" :key="view.id" class="p-4 hover:bg-gray-50">
              <div class="flex items-center justify-between">
                <div>
                  <NuxtLink :to="`/admin/users/${view.user_id}`" class="font-medium text-indigo-600 hover:text-indigo-800 hover:underline">
                    {{ getUserDisplayName(view) }}
                  </NuxtLink>
                  <span class="text-gray-500 ml-2">posjetio/la Proizvodi</span>
                </div>
                <span class="text-sm text-gray-500">{{ formatDateTime(view.created_at) }}</span>
              </div>
              <div v-if="view.activity_data" class="mt-1 text-xs text-gray-500">
                <span v-if="view.activity_data.filters?.category">Kategorija: {{ view.activity_data.filters.category }}</span>
                <span v-if="view.activity_data.filters?.store" class="ml-2">Trgovina: {{ view.activity_data.filters.store }}</span>
                <span v-if="view.activity_data.page_number" class="ml-2">Stranica: {{ view.activity_data.page_number }}</span>
              </div>
            </div>
          </div>

          <!-- Votes Tab -->
          <div v-if="activeTab === 'votes'" class="divide-y divide-gray-200">
            <div v-if="recentVotes.length === 0" class="p-8 text-center text-gray-500">
              Nema glasova
            </div>
            <div v-for="vote in recentVotes" :key="vote.id" class="p-4 hover:bg-gray-50">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span :class="vote.vote_type === 'up' ? 'text-green-600' : 'text-red-600'" class="text-xl">
                    {{ vote.vote_type === 'up' ? '👍' : '👎' }}
                  </span>
                  <NuxtLink :to="`/admin/users/${vote.user_id}`" class="font-medium text-indigo-600 hover:text-indigo-800 hover:underline">
                    {{ getUserDisplayName(vote) }}
                  </NuxtLink>
                </div>
                <span class="text-sm text-gray-500">{{ formatDateTime(vote.created_at) }}</span>
              </div>
              <div class="mt-1 text-sm text-gray-600 ml-8">{{ vote.product_title }}</div>
            </div>
          </div>

          <!-- Comments Tab -->
          <div v-if="activeTab === 'comments'" class="divide-y divide-gray-200">
            <div v-if="recentComments.length === 0" class="p-8 text-center text-gray-500">
              Nema komentara
            </div>
            <div v-for="comment in recentComments" :key="comment.id" class="p-4 hover:bg-gray-50">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="text-xl">💬</span>
                  <NuxtLink :to="`/admin/users/${comment.user_id}`" class="font-medium text-indigo-600 hover:text-indigo-800 hover:underline">
                    {{ getUserDisplayName(comment) }}
                  </NuxtLink>
                </div>
                <span class="text-sm text-gray-500">{{ formatDateTime(comment.created_at) }}</span>
              </div>
              <div class="mt-1 text-sm text-gray-600 ml-8">
                <span class="text-gray-500">Na:</span> {{ comment.product_title }}
              </div>
              <div class="mt-1 text-sm text-gray-900 ml-8 bg-gray-50 rounded p-2">
                "{{ comment.comment_text }}"
              </div>
            </div>
          </div>

          <!-- Favorites Tab -->
          <div v-if="activeTab === 'favorites'" class="divide-y divide-gray-200">
            <div v-if="recentFavorites.length === 0" class="p-8 text-center text-gray-500">
              Nema favorita
            </div>
            <div v-for="fav in recentFavorites" :key="fav.id" class="p-4 hover:bg-gray-50">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="text-xl">❤️</span>
                  <NuxtLink :to="`/admin/users/${fav.user_id}`" class="font-medium text-indigo-600 hover:text-indigo-800 hover:underline">
                    {{ getUserDisplayName(fav) }}
                  </NuxtLink>
                  <span class="text-gray-500">sačuvao/la</span>
                </div>
                <span class="text-sm text-gray-500">{{ formatDateTime(fav.created_at) }}</span>
              </div>
              <div class="mt-1 text-sm text-gray-600 ml-8">{{ fav.product_title }}</div>
            </div>
          </div>

          <!-- Top Users Tab -->
          <div v-if="activeTab === 'top'" class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- Top Voters -->
              <div>
                <h3 class="font-medium text-gray-900 mb-4">🏆 Najaktivniji glasači</h3>
                <div v-if="topVoters.length === 0" class="text-gray-500 text-sm">Nema podataka</div>
                <div class="space-y-2">
                  <div v-for="(voter, i) in topVoters" :key="voter.user_id" class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <span class="text-sm font-medium text-gray-500 w-6">{{ i + 1 }}.</span>
                      <NuxtLink :to="`/admin/users/${voter.user_id}`" class="text-sm text-indigo-600 hover:text-indigo-800 hover:underline">
                        {{ getTopUserDisplayName(voter) }}
                      </NuxtLink>
                    </div>
                    <span class="text-sm font-medium text-indigo-600">{{ voter.count }} glasova</span>
                  </div>
                </div>
              </div>

              <!-- Top Commenters -->
              <div>
                <h3 class="font-medium text-gray-900 mb-4">🏆 Najaktivniji komentatori</h3>
                <div v-if="topCommenters.length === 0" class="text-gray-500 text-sm">Nema podataka</div>
                <div class="space-y-2">
                  <div v-for="(commenter, i) in topCommenters" :key="commenter.user_id" class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <span class="text-sm font-medium text-gray-500 w-6">{{ i + 1 }}.</span>
                      <NuxtLink :to="`/admin/users/${commenter.user_id}`" class="text-sm text-indigo-600 hover:text-indigo-800 hover:underline">
                        {{ getTopUserDisplayName(commenter) }}
                      </NuxtLink>
                    </div>
                    <span class="text-sm font-medium text-indigo-600">{{ commenter.count }} komentara</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth', 'admin']
})

const { get } = useApi()

const isLoading = ref(true)
const activeTab = ref('proizvodi')
const stats = ref<any>({})
const recentVotes = ref<any[]>([])
const recentComments = ref<any[]>([])
const recentFavorites = ref<any[]>([])
const recentProizvodiViews = ref<any[]>([])
const topVoters = ref<any[]>([])
const topCommenters = ref<any[]>([])

onMounted(async () => {
  await loadEngagementData()
})

async function loadEngagementData() {
  isLoading.value = true
  try {
    const data = await get('/api/admin/engagement')
    stats.value = data.stats || {}
    recentVotes.value = data.recent_votes || []
    recentComments.value = data.recent_comments || []
    recentFavorites.value = data.recent_favorites || []
    recentProizvodiViews.value = data.recent_proizvodi_views || []
    topVoters.value = data.top_voters || []
    topCommenters.value = data.top_commenters || []
  } catch (error) {
    console.error('Error loading engagement data:', error)
  } finally {
    isLoading.value = false
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

function getUserDisplayName(item: any) {
  if (item.user_first_name && item.user_last_name) {
    return `${item.user_first_name} ${item.user_last_name}`
  } else if (item.user_first_name) {
    return item.user_first_name
  }
  return item.user_email || 'Nepoznat korisnik'
}

function getTopUserDisplayName(item: any) {
  if (item.first_name && item.last_name) {
    return `${item.first_name} ${item.last_name}`
  } else if (item.first_name) {
    return item.first_name
  }
  return item.email || 'Nepoznat korisnik'
}

useSeoMeta({
  title: 'Analitika angažmana - Admin - Popust.ba',
  description: 'Pregled korisničke aktivnosti i metrika angažmana',
})
</script>
