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
            <h1 class="text-2xl font-semibold text-gray-900">Email Tracking</h1>
            <p class="mt-1 text-sm text-gray-600">Pratite ko se vratio iz email kampanja i kako</p>
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
          <span class="ml-3 text-lg">Ucitavanje...</span>
        </div>
      </div>

      <template v-else>
        <!-- Summary Stats Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-lg">📧</span>
              <span class="text-sm text-gray-500">Ukupno klikova</span>
            </div>
            <div class="text-2xl font-bold text-gray-900">{{ data?.summary?.total_clicks || 0 }}</div>
          </div>

          <div class="bg-white rounded-lg border border-green-200 bg-green-50 p-4">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-lg">📅</span>
              <span class="text-sm text-green-600">Danas</span>
            </div>
            <div class="text-2xl font-bold text-green-700">{{ data?.summary?.today_clicks || 0 }}</div>
          </div>

          <div class="bg-white rounded-lg border border-blue-200 bg-blue-50 p-4">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-lg">📆</span>
              <span class="text-sm text-blue-600">Ove sedmice</span>
            </div>
            <div class="text-2xl font-bold text-blue-700">{{ data?.summary?.week_clicks || 0 }}</div>
          </div>

          <div class="bg-white rounded-lg border border-purple-200 bg-purple-50 p-4">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-lg">👥</span>
              <span class="text-sm text-purple-600">Jedinstvenih korisnika (7d)</span>
            </div>
            <div class="text-2xl font-bold text-purple-700">{{ data?.summary?.unique_users_week || 0 }}</div>
          </div>
        </div>

        <!-- Two Column Layout -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <!-- Campaign Breakdown -->
          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Klikovi po kampanjama</h2>
            <div v-if="data?.campaigns?.length" class="space-y-3">
              <div v-for="campaign in data.campaigns" :key="campaign.campaign"
                   class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div class="font-medium text-gray-900">{{ formatCampaignName(campaign.campaign) }}</div>
                  <div class="text-sm text-gray-500">{{ campaign.unique_users }} korisnika</div>
                </div>
                <div class="text-right">
                  <div class="text-xl font-bold text-indigo-600">{{ campaign.clicks }}</div>
                  <div class="text-xs text-gray-500">klikova</div>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-gray-500">
              Nema podataka o kampanjama
            </div>
          </div>

          <!-- First Touch Sources (Registrations) -->
          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Izvor registracija (First Touch)</h2>
            <div v-if="data?.first_touch_sources?.length" class="space-y-3">
              <div v-for="source in data.first_touch_sources" :key="source.source"
                   class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div class="flex items-center gap-2">
                  <span class="text-lg">{{ getSourceIcon(source.source) }}</span>
                  <span class="font-medium text-gray-900">{{ source.source }}</span>
                </div>
                <div class="text-xl font-bold text-green-600">{{ source.registrations }}</div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-gray-500">
              Nema podataka o izvorima
            </div>
          </div>
        </div>

        <!-- Recent Clicks Table -->
        <div class="bg-white rounded-lg border border-gray-200 p-6 mb-8">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Zadnjih 50 klikova iz emaila</h2>
          <div v-if="data?.recent_clicks?.length" class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Korisnik</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kampanja</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stranica</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vrijeme</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="click in data.recent_clicks" :key="click.id" class="hover:bg-gray-50">
                  <td class="px-4 py-3 whitespace-nowrap">
                    <div class="text-sm font-medium text-gray-900">{{ click.name }}</div>
                    <div class="text-xs text-gray-500">{{ click.email }}</div>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                          :class="getCampaignBadgeClass(click.campaign)">
                      {{ formatCampaignName(click.campaign) }}
                    </span>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {{ click.landing_page }}
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {{ formatTime(click.timestamp) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="text-center py-8 text-gray-500">
            Nema podataka o klikovima. Klikovi ce se prikazati kada korisnici krenu klikati na linkove u emailovima.
          </div>
        </div>

        <!-- Registration Campaigns -->
        <div v-if="data?.registration_campaigns?.length" class="bg-white rounded-lg border border-gray-200 p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Registracije po kampanjama</h2>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div v-for="camp in data.registration_campaigns" :key="camp.campaign"
                 class="p-3 bg-gray-50 rounded-lg text-center">
              <div class="text-lg font-bold text-indigo-600">{{ camp.registrations }}</div>
              <div class="text-xs text-gray-600 truncate" :title="camp.campaign">{{ camp.campaign }}</div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

definePageMeta({
  middleware: 'auth'
})

const { $api } = useNuxtApp()
const isLoading = ref(true)
const data = ref(null)

const fetchData = async () => {
  isLoading.value = true
  try {
    const response = await $api.get('/api/admin/email-analytics')
    data.value = response
  } catch (error) {
    console.error('Error fetching email analytics:', error)
  } finally {
    isLoading.value = false
  }
}

const formatCampaignName = (campaign) => {
  if (!campaign) return 'Nepoznato'
  const names = {
    'daily_summary': 'Dnevni izvjestaj',
    'weekly_summary': 'Sedmicni izvjestaj',
    'verification': 'Verifikacija emaila',
    'welcome': 'Dobrodoslica',
    'password_reset': 'Reset lozinke',
    'business_invitation': 'Pozivnica biznisu',
    'bonus_credits': 'Bonus krediti',
    'coupon_purchase': 'Kupovina kupona',
    'coupon_sold': 'Kupon prodan',
    'coupon_reminder': 'Podsjetnik za kupon',
    'coupon_expired': 'Kupon istekao',
    'coupon_feedback': 'Povratna info kupona',
    'reengagement': 'Reaktivacija',
    'coupon_redeemed': 'Kupon iskoristen',
    'weekly_activation': 'Sedmicna aktivacija'
  }
  return names[campaign] || campaign
}

const getCampaignBadgeClass = (campaign) => {
  const classes = {
    'daily_summary': 'bg-blue-100 text-blue-800',
    'weekly_summary': 'bg-indigo-100 text-indigo-800',
    'verification': 'bg-green-100 text-green-800',
    'welcome': 'bg-purple-100 text-purple-800',
    'reengagement': 'bg-orange-100 text-orange-800',
    'coupon_reminder': 'bg-yellow-100 text-yellow-800',
    'coupon_expired': 'bg-red-100 text-red-800'
  }
  return classes[campaign] || 'bg-gray-100 text-gray-800'
}

const getSourceIcon = (source) => {
  const icons = {
    'facebook': '📘',
    'instagram': '📸',
    'google': '🔍',
    'email': '📧',
    'direct': '🔗',
    'referral': '🔀',
    'twitter': '🐦',
    'linkedin': '💼'
  }
  return icons[source?.toLowerCase()] || '🌐'
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Upravo sada'
  if (diffMins < 60) return `prije ${diffMins} min`
  if (diffHours < 24) return `prije ${diffHours}h`
  if (diffDays < 7) return `prije ${diffDays} dana`

  return date.toLocaleDateString('hr-HR', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchData()
})
</script>
