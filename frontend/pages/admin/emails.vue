<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-6">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">Email & Job Logs</h1>
            <p class="mt-1 text-sm text-gray-600">Pregled poslanih emailova i izvršenih scheduled job-ova</p>
          </div>
          <NuxtLink to="/admin" class="text-indigo-600 hover:text-indigo-800 text-sm">
            &larr; Nazad na Admin
          </NuxtLink>
        </div>
      </div>

      <!-- Tabs -->
      <div class="mb-6">
        <nav class="flex space-x-4">
          <button
            @click="activeTab = 'emails'"
            :class="[
              'px-4 py-2 rounded-lg font-medium text-sm transition-colors',
              activeTab === 'emails'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-100'
            ]"
          >
            Emailovi
          </button>
          <button
            @click="activeTab = 'jobs'"
            :class="[
              'px-4 py-2 rounded-lg font-medium text-sm transition-colors',
              activeTab === 'jobs'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-100'
            ]"
          >
            Job Runs
          </button>
        </nav>
      </div>

      <!-- Email Logs Tab -->
      <div v-if="activeTab === 'emails'" class="bg-white rounded-lg shadow">
        <!-- Filters -->
        <div class="p-4 border-b border-gray-200 flex flex-wrap gap-4">
          <select v-model="emailTypeFilter" class="rounded-md border-gray-300 text-sm text-gray-900">
            <option value="">Svi tipovi</option>
            <option value="daily_scan">Daily Scan</option>
            <option value="welcome">Welcome</option>
            <option value="verification">Verification</option>
          </select>
          <select v-model="emailStatusFilter" class="rounded-md border-gray-300 text-sm text-gray-900">
            <option value="">Svi statusi</option>
            <option value="sent">Sent</option>
            <option value="failed">Failed</option>
          </select>
          <button @click="loadEmails" class="px-3 py-1.5 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700">
            Filtriraj
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loadingEmails" class="p-8 text-center text-gray-500">
          Učitavanje...
        </div>

        <!-- Empty State -->
        <div v-else-if="emails.length === 0" class="p-8 text-center text-gray-500">
          Nema email logova za prikaz
        </div>

        <!-- Table -->
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vrijeme</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tip</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Detalji</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="email in emails" :key="email.id" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(email.sent_at) }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                  {{ email.email }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap">
                  <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                    {{ email.email_type }}
                  </span>
                </td>
                <td class="px-4 py-3 text-sm text-gray-500 max-w-xs truncate">
                  {{ email.subject || '-' }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap">
                  <span :class="[
                    'px-2 py-1 text-xs rounded-full',
                    email.status === 'sent' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  ]">
                    {{ email.status }}
                  </span>
                </td>
                <td class="px-4 py-3 text-sm text-gray-500">
                  <span v-if="email.error_message" class="text-red-600">{{ email.error_message }}</span>
                  <span v-else-if="email.extra_data">
                    {{ email.extra_data.total_products }} products
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="emailsPagination.pages > 1" class="p-4 border-t border-gray-200 flex items-center justify-between">
          <span class="text-sm text-gray-500">
            Prikazano {{ emails.length }} od {{ emailsPagination.total }} emailova
          </span>
          <div class="flex space-x-2">
            <button
              @click="emailsPage--; loadEmails()"
              :disabled="emailsPage <= 1"
              class="px-3 py-1 border rounded text-sm text-gray-900 disabled:opacity-50"
            >
              Prethodna
            </button>
            <span class="px-3 py-1 text-sm text-gray-900">{{ emailsPage }} / {{ emailsPagination.pages }}</span>
            <button
              @click="emailsPage++; loadEmails()"
              :disabled="emailsPage >= emailsPagination.pages"
              class="px-3 py-1 border rounded text-sm text-gray-900 disabled:opacity-50"
            >
              Sljedeća
            </button>
          </div>
        </div>
      </div>

      <!-- Job Runs Tab -->
      <div v-if="activeTab === 'jobs'" class="bg-white rounded-lg shadow">
        <!-- Filters -->
        <div class="p-4 border-b border-gray-200 flex flex-wrap gap-4">
          <select v-model="jobNameFilter" class="rounded-md border-gray-300 text-sm text-gray-900">
            <option value="">Svi jobovi</option>
            <option value="product_scan">Product Scan</option>
            <option value="email_summary">Email Summary</option>
            <option value="cleanup">Cleanup</option>
          </select>
          <button @click="loadJobs" class="px-3 py-1.5 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700">
            Filtriraj
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loadingJobs" class="p-8 text-center text-gray-500">
          Učitavanje...
        </div>

        <!-- Empty State -->
        <div v-else-if="jobs.length === 0" class="p-8 text-center text-gray-500">
          Nema job logova za prikaz
        </div>

        <!-- Table -->
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vrijeme</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Job</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trajanje</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Processed</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Success</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Failed</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Error</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="job in jobs" :key="job.id" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(job.started_at) }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap">
                  <span class="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800">
                    {{ job.job_name }}
                  </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap">
                  <span :class="[
                    'px-2 py-1 text-xs rounded-full',
                    job.status === 'completed' ? 'bg-green-100 text-green-800' :
                    job.status === 'running' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  ]">
                    {{ job.status }}
                  </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {{ job.duration_seconds ? Math.round(job.duration_seconds) + 's' : '-' }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 font-medium">
                  {{ job.records_processed || 0 }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-green-600 font-medium">
                  {{ job.records_success || 0 }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-red-600 font-medium">
                  {{ job.records_failed || 0 }}
                </td>
                <td class="px-4 py-3 text-sm text-red-600 max-w-xs truncate">
                  {{ job.error_message || '-' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="jobsPagination.pages > 1" class="p-4 border-t border-gray-200 flex items-center justify-between">
          <span class="text-sm text-gray-500">
            Prikazano {{ jobs.length }} od {{ jobsPagination.total }} jobova
          </span>
          <div class="flex space-x-2">
            <button
              @click="jobsPage--; loadJobs()"
              :disabled="jobsPage <= 1"
              class="px-3 py-1 border rounded text-sm text-gray-900 disabled:opacity-50"
            >
              Prethodna
            </button>
            <span class="px-3 py-1 text-sm text-gray-900">{{ jobsPage }} / {{ jobsPagination.pages }}</span>
            <button
              @click="jobsPage++; loadJobs()"
              :disabled="jobsPage >= jobsPagination.pages"
              class="px-3 py-1 border rounded text-sm text-gray-900 disabled:opacity-50"
            >
              Sljedeća
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

const { $api } = useNuxtApp()

const activeTab = ref('emails')

// Email state
const emails = ref<any[]>([])
const loadingEmails = ref(false)
const emailsPage = ref(1)
const emailsPagination = ref({ total: 0, pages: 1 })
const emailTypeFilter = ref('')
const emailStatusFilter = ref('')

// Jobs state
const jobs = ref<any[]>([])
const loadingJobs = ref(false)
const jobsPage = ref(1)
const jobsPagination = ref({ total: 0, pages: 1 })
const jobNameFilter = ref('')

async function loadEmails() {
  loadingEmails.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', emailsPage.value.toString())
    params.append('per_page', '50')
    if (emailTypeFilter.value) params.append('type', emailTypeFilter.value)
    if (emailStatusFilter.value) params.append('status', emailStatusFilter.value)

    const response = await $api(`/api/admin/email-logs?${params}`)
    emails.value = response.emails
    emailsPagination.value = { total: response.total, pages: response.pages }
  } catch (error) {
    console.error('Failed to load emails:', error)
  } finally {
    loadingEmails.value = false
  }
}

async function loadJobs() {
  loadingJobs.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', jobsPage.value.toString())
    params.append('per_page', '50')
    if (jobNameFilter.value) params.append('job_name', jobNameFilter.value)

    const response = await $api(`/api/admin/job-runs?${params}`)
    jobs.value = response.jobs
    jobsPagination.value = { total: response.total, pages: response.pages }
  } catch (error) {
    console.error('Failed to load jobs:', error)
  } finally {
    loadingJobs.value = false
  }
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('bs-BA', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Load initial data
onMounted(() => {
  loadEmails()
  loadJobs()
})

// Reload when tab changes
watch(activeTab, (newTab) => {
  if (newTab === 'emails') loadEmails()
  else loadJobs()
})
</script>
