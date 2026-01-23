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
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Korisnici</h1>
        <p class="text-gray-600">Pregled svih registrovanih korisnika i njihovih OTP kodova</p>
      </div>

      <!-- Tabs -->
      <div class="mb-6 border-b border-gray-200">
        <nav class="-mb-px flex space-x-8">
          <button
            @click="activeTab = 'users'"
            :class="[
              'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === 'users'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            <Icon name="mdi:account-group" class="w-5 h-5 inline mr-2" />
            Korisnici
          </button>
          <button
            @click="activeTab = 'emails'; loadEmails()"
            :class="[
              'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === 'emails'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            <Icon name="mdi:email-newsletter" class="w-5 h-5 inline mr-2" />
            Email historija
          </button>
          <button
            @click="activeTab = 'jobs'; loadJobs()"
            :class="[
              'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === 'jobs'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            <Icon name="mdi:cog-sync" class="w-5 h-5 inline mr-2" />
            Job logovi
          </button>
          <button
            @click="activeTab = 'preferences'; loadPreferencesAnalytics()"
            :class="[
              'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === 'preferences'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            <Icon name="mdi:heart-outline" class="w-5 h-5 inline mr-2" />
            Preferencije
          </button>
          <button
            @click="activeTab = 'cities'; loadCities()"
            :class="[
              'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === 'cities'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            <Icon name="mdi:city" class="w-5 h-5 inline mr-2" />
            Gradovi
          </button>
        </nav>
      </div>

      <!-- Tab Content: Users -->
      <div v-show="activeTab === 'users'">

      <!-- Analytics Chart Section -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-gray-900">Aktivnost korisnika</h3>
          <!-- Interval Selector -->
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-500">Prikaz po:</span>
            <div class="inline-flex rounded-md shadow-sm">
              <button
                @click="changeInterval('hour')"
                :class="[
                  'px-3 py-1.5 text-sm font-medium rounded-l-md border',
                  selectedInterval === 'hour'
                    ? 'bg-purple-600 text-white border-purple-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                ]"
              >
                Sat
              </button>
              <button
                @click="changeInterval('day')"
                :class="[
                  'px-3 py-1.5 text-sm font-medium border-t border-b',
                  selectedInterval === 'day'
                    ? 'bg-purple-600 text-white border-purple-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                ]"
              >
                Dan
              </button>
              <button
                @click="changeInterval('month')"
                :class="[
                  'px-3 py-1.5 text-sm font-medium rounded-r-md border',
                  selectedInterval === 'month'
                    ? 'bg-purple-600 text-white border-purple-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                ]"
              >
                Mjesec
              </button>
            </div>
          </div>
        </div>

        <!-- Chart Loading State -->
        <div v-if="chartLoading" class="flex items-center justify-center h-64">
          <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
        </div>

        <!-- Chart -->
        <div v-else class="h-64">
          <ClientOnly>
            <Line v-if="chartData" :data="chartData" :options="chartOptions" />
          </ClientOnly>
        </div>

        <!-- Summary Stats -->
        <div v-if="analyticsData" class="mt-6 grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
          <div class="text-center">
            <p class="text-2xl font-semibold text-blue-600">{{ analyticsData.datasets.users.total }}</p>
            <p class="text-sm text-gray-500">{{ getIntervalLabel() }} - Novi korisnici</p>
          </div>
          <div class="text-center">
            <p class="text-2xl font-semibold text-green-600">{{ analyticsData.datasets.searches.total }}</p>
            <p class="text-sm text-gray-500">{{ getIntervalLabel() }} - Pretrage</p>
          </div>
        </div>
      </div>

      <!-- Search and Filters -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <div class="flex flex-wrap gap-4">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Pretraži po email, telefon, ime..."
            class="flex-1 min-w-[200px] px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 placeholder-gray-400"
            @input="debouncedSearch"
          />
          <!-- Deactivated Filter -->
          <select
            v-model="deactivatedFilter"
            @change="loadUsers(1)"
            class="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-700 bg-white"
          >
            <option value="">Svi korisnici</option>
            <option value="deactivated">Deaktivirani</option>
            <option value="active">Aktivni</option>
          </select>
          <!-- Notifications Filter -->
          <select
            v-model="notificationsFilter"
            @change="loadUsers(1)"
            class="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-700 bg-white"
          >
            <option value="">Sve notifikacije</option>
            <option value="disabled">Isključene notifikacije</option>
            <option value="enabled">Uključene notifikacije</option>
          </select>
          <button
            @click="loadUsers"
            class="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition"
          >
            <Icon name="mdi:magnify" class="w-5 h-5" />
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-5 gap-6 mb-4">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Ukupno korisnika</p>
              <p class="text-2xl font-bold text-gray-900">{{ totalUsers }}</p>
            </div>
            <Icon name="mdi:account-group" class="w-12 h-12 text-purple-600" />
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Email registracije</p>
              <p class="text-2xl font-bold text-gray-900">{{ emailUsers }}</p>
            </div>
            <Icon name="mdi:email" class="w-12 h-12 text-blue-600" />
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Google registracije</p>
              <p class="text-2xl font-bold text-gray-900">{{ googleUsers }}</p>
            </div>
            <Icon name="mdi:google" class="w-12 h-12 text-red-500" />
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Phone registracije</p>
              <p class="text-2xl font-bold text-gray-900">{{ phoneUsers }}</p>
            </div>
            <Icon name="mdi:cellphone" class="w-12 h-12 text-green-600" />
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Verifikovani</p>
              <p class="text-2xl font-bold text-gray-900">{{ verifiedUsers }}</p>
            </div>
            <Icon name="mdi:check-circle" class="w-12 h-12 text-teal-600" />
          </div>
        </div>
      </div>

      <!-- Deactivation Stats -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Deaktivirani računi</p>
              <p class="text-2xl font-bold text-red-600">{{ deactivationStats.deactivated_users || 0 }}</p>
              <p class="text-xs text-gray-400 mt-1">Korisnici koji su deaktivirali profil</p>
            </div>
            <Icon name="mdi:account-off" class="w-12 h-12 text-red-400" />
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-500">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Isključene notifikacije</p>
              <p class="text-2xl font-bold text-yellow-600">{{ deactivationStats.users_with_disabled_notifications || 0 }}</p>
              <p class="text-xs text-gray-400 mt-1">Korisnici sa bar jednim tipom isključene notifikacije</p>
            </div>
            <Icon name="mdi:bell-off" class="w-12 h-12 text-yellow-400" />
          </div>
        </div>
      </div>

      <!-- Users Table -->
      <div class="bg-white rounded-lg shadow-md overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Korisnik</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kontakt</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <div>Aktivnost (7 dana)</div>
                  <div class="flex gap-2 mt-1 font-normal normal-case">
                    <span class="flex items-center gap-1"><span class="w-2 h-2 bg-blue-400 rounded"></span>pretrage</span>
                    <span class="flex items-center gap-1"><span class="w-2 h-2 bg-yellow-400 rounded"></span>proizvodi</span>
                    <span class="flex items-center gap-1"><span class="w-2 h-2 bg-purple-400 rounded"></span>interakcije</span>
                  </div>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Poslednja prijava</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prodavnice</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Krediti</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">OTP Kod</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Registrovan</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Akcije</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="user in users" :key="user.id" :class="['hover:bg-gray-50 cursor-pointer', user.is_deactivated ? 'bg-red-50/50' : '']" @click="openUserProfile(user.id)">
                <!-- User -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div>
                      <div class="text-sm font-medium text-gray-900 hover:text-indigo-600 transition-colors" data-pii>
                        {{ user.first_name || 'N/A' }} {{ user.last_name || '' }}
                        <Icon name="mdi:open-in-new" class="w-3 h-3 inline ml-1 opacity-0 group-hover:opacity-100" />
                      </div>
                      <div class="text-sm text-gray-500">{{ user.city || 'N/A' }}</div>
                    </div>
                  </div>
                </td>

                <!-- Contact -->
                <td class="px-6 py-4">
                  <div class="text-sm text-gray-900">
                    <div v-if="user.email" class="flex items-center gap-2" data-pii>
                      <Icon name="mdi:email" class="w-4 h-4 text-gray-400" />
                      {{ user.email }}
                    </div>
                    <div v-if="user.phone" class="flex items-center gap-2" data-pii>
                      <Icon name="mdi:cellphone" class="w-4 h-4 text-gray-400" />
                      {{ user.phone }}
                    </div>
                  </div>
                  <span
                    :class="[
                      'mt-1 px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full',
                      user.registration_method === 'phone'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-blue-100 text-blue-800'
                    ]"
                  >
                    {{ user.registration_method === 'phone' ? 'Telefon' : 'Email' }}
                  </span>
                </td>

                <!-- Activity Chart -->
                <td class="px-6 py-4">
                  <div v-if="userActivity[user.id]" class="flex items-end gap-0.5 h-8">
                    <div
                      v-for="(day, index) in userActivity[user.id]"
                      :key="index"
                      class="flex flex-col items-center"
                    >
                      <div class="flex gap-px">
                        <!-- Search bar (blue) -->
                        <div
                          class="w-1.5 bg-blue-400 rounded-t transition-all"
                          :style="{ height: `${Math.min(day.searches * 4, 24)}px` }"
                          :title="`${day.day}: ${day.searches} pretraga`"
                        ></div>
                        <!-- Proizvodi visits bar (yellow) -->
                        <div
                          class="w-1.5 bg-yellow-400 rounded-t transition-all"
                          :style="{ height: `${Math.min((day.proizvodi || 0) * 4, 24)}px` }"
                          :title="`${day.day}: ${day.proizvodi || 0} posjeta Proizvodi`"
                        ></div>
                        <!-- Engagement bar (purple) -->
                        <div
                          class="w-1.5 bg-purple-400 rounded-t transition-all"
                          :style="{ height: `${Math.min(day.engagements * 4, 24)}px` }"
                          :title="`${day.day}: ${day.engagements} interakcija`"
                        ></div>
                      </div>
                      <span class="text-[8px] text-gray-400 mt-0.5">{{ day.day.substring(0, 2) }}</span>
                    </div>
                  </div>
                  <div v-else-if="loadingActivity[user.id]" class="text-xs text-gray-400">
                    <Icon name="mdi:loading" class="w-4 h-4 animate-spin" />
                  </div>
                  <button
                    v-else
                    @click="loadUserActivity(user.id)"
                    class="text-xs text-purple-600 hover:text-purple-800"
                  >
                    Učitaj
                  </button>
                </td>

                <!-- Status -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex flex-col gap-1">
                    <span
                      v-if="user.is_deactivated"
                      class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800"
                    >
                      Deaktiviran
                    </span>
                    <span
                      v-if="user.is_admin"
                      class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-purple-100 text-purple-800"
                    >
                      Admin
                    </span>
                    <span
                      :class="[
                        'px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full',
                        user.is_verified
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      ]"
                    >
                      {{ user.is_verified ? 'Verifikovan' : 'Nije verifikovan' }}
                    </span>
                  </div>
                </td>

                <!-- Last Login -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div v-if="user.last_login" class="text-sm">
                    <div class="flex items-center gap-1 mb-1">
                      <Icon
                        :name="getDeviceIcon(user.last_login.device_type)"
                        class="w-4 h-4 text-gray-500"
                      />
                      <span class="text-gray-900">{{ user.last_login.device_type || 'N/A' }}</span>
                    </div>
                    <div class="text-xs text-gray-500">
                      {{ user.last_login.os_name || '' }} {{ user.last_login.browser_name ? `/ ${user.last_login.browser_name}` : '' }}
                    </div>
                    <div class="text-xs text-gray-400 mt-1">
                      {{ formatDate(user.last_login.created_at) }}
                    </div>
                  </div>
                  <div v-else class="text-sm text-gray-400">
                    N/A
                  </div>
                </td>

                <!-- Preferred Stores -->
                <td class="px-6 py-4" @click.stop>
                  <div v-if="user.preferred_stores && user.preferred_stores.length > 0" class="flex flex-wrap gap-1 max-w-xs">
                    <span
                      v-for="store in user.preferred_stores.slice(0, 3)"
                      :key="store.id"
                      class="px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-700"
                      :title="store.name"
                    >
                      {{ truncateStoreName(store.name) }}
                    </span>
                    <button
                      v-if="user.preferred_stores.length > 3"
                      @click="showStoresModal(user)"
                      class="px-2 py-0.5 text-xs rounded bg-purple-100 text-purple-700 hover:bg-purple-200 cursor-pointer"
                    >
                      +{{ user.preferred_stores.length - 3 }}
                    </button>
                  </div>
                  <div v-else class="text-sm text-gray-400">
                    Sve
                  </div>
                </td>

                <!-- Credits -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <div>{{ user.weekly_credits_used || 0 }} / {{ user.weekly_credits || 10 }} <span class="text-gray-400 text-xs">tjedno</span></div>
                  <div v-if="user.extra_credits" class="text-purple-600 text-xs">+{{ user.extra_credits }} ekstra</div>
                </td>

                <!-- OTP Code -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div v-if="user.latest_otp" class="text-sm">
                    <div class="font-mono font-bold text-lg text-purple-600">
                      {{ user.latest_otp.code }}
                    </div>
                    <div class="text-xs text-gray-500 mt-1">
                      <div v-if="!user.latest_otp.expired && !user.latest_otp.is_used" class="text-green-600">
                        ✓ Aktivan
                      </div>
                      <div v-else-if="user.latest_otp.is_used" class="text-gray-400">
                        Iskorišten
                      </div>
                      <div v-else class="text-red-600">
                        Istekao
                      </div>
                      <div class="mt-1">
                        {{ formatDate(user.latest_otp.created_at) }}
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-sm text-gray-400">
                    N/A
                  </div>
                </td>

                <!-- Created At -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(user.created_at) }}
                </td>

                <!-- Actions -->
                <td class="px-6 py-4 whitespace-nowrap" @click.stop>
                  <div class="flex items-center gap-2">
                    <button
                      @click="openUserProfile(user.id)"
                      class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
                    >
                      <Icon name="mdi:account-details" class="w-4 h-4 mr-1" />
                      Profil
                    </button>
                    <button
                      @click="confirmDeleteUser(user)"
                      class="inline-flex items-center px-2 py-1.5 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                      title="Obriši korisnika"
                    >
                      <Icon name="mdi:delete" class="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="pagination.pages > 1" class="bg-gray-50 px-6 py-4 flex items-center justify-between">
          <div class="text-sm text-gray-700">
            Stranica {{ pagination.page }} od {{ pagination.pages }} ({{ pagination.total }} korisnika)
          </div>
          <div class="flex gap-2">
            <button
              @click="changePage(pagination.page - 1)"
              :disabled="pagination.page === 1"
              class="px-4 py-2 border border-gray-300 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              Prethodna
            </button>
            <button
              @click="changePage(pagination.page + 1)"
              :disabled="pagination.page === pagination.pages"
              class="px-4 py-2 border border-gray-300 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              Sledeća
            </button>
          </div>
        </div>
      </div>
      </div>
      <!-- End Tab Content: Users -->

      <!-- Tab Content: Emails -->
      <div v-show="activeTab === 'emails'">
        <!-- Email Stats Summary -->
        <div v-if="emailStats" class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-white rounded-lg shadow p-4 text-center">
            <div class="text-3xl font-bold text-purple-600">{{ emailStats.total_week }}</div>
            <div class="text-sm text-gray-500">Ova sedmica</div>
          </div>
          <div v-for="stat in emailStats.by_type?.slice(0, 3)" :key="stat.email_type" class="bg-white rounded-lg shadow p-4 text-center">
            <div class="text-2xl font-bold text-gray-900">{{ stat.sent }}</div>
            <div class="text-sm text-gray-500">{{ getEmailTypeLabel(stat.email_type) }}</div>
            <div v-if="stat.failed > 0" class="text-xs text-red-500">{{ stat.failed }} neuspjesno</div>
          </div>
        </div>

        <!-- Email Filters -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">Email historija</h3>
            <div class="flex items-center gap-3">
              <select v-model="emailTypeFilter" @change="loadEmails()" class="text-sm border border-gray-300 rounded-md px-3 py-2">
                <option value="">Svi tipovi</option>
                <option value="daily_scan">Dnevno skeniranje</option>
                <option value="weekly_summary">Sedmicni izvjestaj</option>
                <option value="verification">Verifikacija</option>
                <option value="welcome">Dobrodoslica</option>
                <option value="coupon_purchase">Kupovina kupona</option>
                <option value="coupon_reminder">Podsjetnik za kupon</option>
              </select>
              <button
                @click="loadEmails()"
                class="text-sm text-purple-600 hover:text-purple-800 flex items-center gap-1"
              >
                <Icon name="mdi:refresh" class="w-4 h-4" :class="{ 'animate-spin': emailsLoading }" />
                Osvježi
              </button>
            </div>
          </div>
        </div>

        <!-- Email Table -->
        <div class="bg-white rounded-lg shadow-md overflow-hidden">
          <div v-if="emailsLoading && emails.length === 0" class="flex items-center justify-center h-48">
            <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
          </div>

          <div v-else-if="emails.length === 0" class="text-center py-12 text-gray-500">
            <Icon name="mdi:email-off-outline" class="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p>Nema poslatih emailova</p>
          </div>

          <div v-else class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Korisnik</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tip</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Naslov</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Poslato</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200">
                <tr v-for="email in emails" :key="email.id" class="hover:bg-gray-50">
                  <td class="px-6 py-4">
                    <div class="text-sm font-medium text-gray-900" data-pii>{{ email.user_name || 'N/A' }}</div>
                    <div class="text-xs text-gray-500" data-pii>{{ email.email }}</div>
                  </td>
                  <td class="px-6 py-4">
                    <span class="px-2 py-1 text-xs rounded-full" :class="getEmailTypeBadgeClass(email.email_type)">
                      {{ getEmailTypeLabel(email.email_type) }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
                    {{ email.subject || '-' }}
                  </td>
                  <td class="px-6 py-4">
                    <span
                      class="px-2 py-1 text-xs rounded-full"
                      :class="email.status === 'sent' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                    >
                      {{ email.status === 'sent' ? 'Poslato' : 'Neuspjelo' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-500">
                    {{ formatEmailDate(email.sent_at) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Email Pagination -->
          <div v-if="emailPagination.pages > 1" class="bg-gray-50 px-6 py-4 flex items-center justify-between">
            <div class="text-sm text-gray-700">
              Stranica {{ emailPagination.page }} od {{ emailPagination.pages }}
            </div>
            <div class="flex gap-2">
              <button
                @click="loadEmails(emailPagination.page - 1)"
                :disabled="emailPagination.page === 1"
                class="px-4 py-2 border border-gray-300 rounded-lg text-sm disabled:opacity-50"
              >
                Prethodna
              </button>
              <button
                @click="loadEmails(emailPagination.page + 1)"
                :disabled="emailPagination.page === emailPagination.pages"
                class="px-4 py-2 border border-gray-300 rounded-lg text-sm disabled:opacity-50"
              >
                Sljedeca
              </button>
            </div>
          </div>
        </div>
      </div>
      <!-- End Tab Content: Emails -->

      <!-- Tab Content: Jobs -->
      <div v-show="activeTab === 'jobs'">
        <!-- Scheduled Jobs -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900">Zakazani poslovi</h3>
            <button
              @click="loadJobs"
              class="text-sm text-purple-600 hover:text-purple-800 flex items-center gap-1"
            >
              <Icon name="mdi:refresh" class="w-4 h-4" :class="{ 'animate-spin': jobsLoading }" />
              Osvježi
            </button>
          </div>

          <div v-if="jobsLoading && jobs.length === 0" class="flex items-center justify-center h-24">
            <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div
              v-for="job in jobs"
              :key="job.name"
              class="border rounded-lg p-4"
              :class="job.enabled ? 'border-gray-200' : 'border-gray-100 bg-gray-50'"
            >
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <Icon
                    :name="getJobIcon(job.name)"
                    class="w-5 h-5"
                    :class="job.enabled ? 'text-purple-600' : 'text-gray-400'"
                  />
                  <span class="font-medium text-gray-900">{{ getJobLabel(job.name) }}</span>
                </div>
                <span
                  :class="[
                    'px-2 py-0.5 text-xs rounded-full',
                    job.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'
                  ]"
                >
                  {{ job.enabled ? 'Aktivan' : 'Neaktivan' }}
                </span>
              </div>

              <div class="text-sm text-gray-500 mb-3">
                <div class="flex items-center gap-1">
                  <Icon name="mdi:clock-outline" class="w-4 h-4" />
                  Zakazano: {{ job.scheduled_time }}
                </div>
                <div v-if="job.last_run" class="mt-2 space-y-1">
                  <div class="flex items-center gap-1">
                    <Icon
                      :name="job.last_run.status === 'completed' ? 'mdi:check-circle' : job.last_run.status === 'failed' ? 'mdi:alert-circle' : 'mdi:loading'"
                      class="w-4 h-4"
                      :class="job.last_run.status === 'completed' ? 'text-green-600' : job.last_run.status === 'failed' ? 'text-red-600' : 'text-yellow-600 animate-spin'"
                    />
                    {{ formatEmailDate(job.last_run.started_at) }}
                  </div>
                  <div v-if="job.last_run.records_processed !== null" class="text-xs pl-5">
                    {{ job.last_run.records_success }}/{{ job.last_run.records_processed }} uspjesno
                    <span v-if="job.last_run.duration_seconds" class="text-gray-400">({{ job.last_run.duration_seconds.toFixed(1) }}s)</span>
                  </div>
                  <div v-if="job.last_run.error_message" class="text-xs text-red-500 pl-5">
                    {{ job.last_run.error_message.substring(0, 50) }}...
                  </div>
                </div>
                <div v-else class="flex items-center gap-1 mt-1 text-gray-400">
                  <Icon name="mdi:clock-alert-outline" class="w-4 h-4" />
                  Nikad nije pokrenuto
                </div>
              </div>

              <button
                @click="triggerJob(job.name)"
                :disabled="runningJob === job.name"
                class="w-full px-3 py-2 text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                :class="
                  runningJob === job.name
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-purple-600 text-white hover:bg-purple-700'
                "
              >
                <Icon
                  :name="runningJob === job.name ? 'mdi:loading' : 'mdi:play'"
                  class="w-4 h-4"
                  :class="{ 'animate-spin': runningJob === job.name }"
                />
                {{ runningJob === job.name ? 'Pokrece se...' : 'Pokreni sada' }}
              </button>
            </div>
          </div>

          <div v-if="jobMessage" class="mt-4 p-3 rounded-lg" :class="jobMessageType === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'">
            {{ jobMessage }}
          </div>
        </div>

        <!-- Job History -->
        <div class="bg-white rounded-lg shadow-md overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">Historija pokretanja</h3>
            <select v-model="jobHistoryFilter" @change="loadJobHistory()" class="text-sm border border-gray-300 rounded-md px-3 py-2">
              <option value="">Svi poslovi</option>
              <option value="product_scan">Skeniranje proizvoda</option>
              <option value="email_summary">Email izvjestaji</option>
              <option value="monthly_credits">Mjesecni krediti</option>
              <option value="coupon_reminders">Podsjetnici za kupone</option>
            </select>
          </div>

          <div v-if="jobHistoryLoading" class="flex items-center justify-center h-32">
            <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
          </div>

          <div v-else-if="jobHistory.length === 0" class="text-center py-12 text-gray-500">
            <Icon name="mdi:history" class="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p>Nema historije pokretanja</p>
          </div>

          <div v-else class="divide-y divide-gray-200">
            <!-- Grouped by day -->
            <div v-for="(dayRuns, dayKey) in jobHistoryByDay" :key="dayKey" class="border-b border-gray-100">
              <!-- Day Header -->
              <div class="bg-gray-50 px-6 py-3 flex items-center justify-between sticky top-0">
                <div class="flex items-center gap-2">
                  <Icon name="mdi:calendar" class="w-5 h-5 text-gray-500" />
                  <span class="font-semibold text-gray-900">{{ formatDayHeader(dayKey) }}</span>
                </div>
                <span class="text-sm text-gray-500">{{ dayRuns.length }} job{{ dayRuns.length !== 1 ? 'ova' : '' }}</span>
              </div>

              <!-- Jobs for this day -->
              <div class="divide-y divide-gray-100">
                <div v-for="run in dayRuns" :key="run.id" class="px-6 py-3 hover:bg-gray-50 flex items-center gap-4">
                  <!-- Time -->
                  <div class="w-16 text-sm text-gray-500">
                    {{ formatTimeOnly(run.started_at) }}
                  </div>

                  <!-- Job Name -->
                  <div class="flex items-center gap-2 w-48">
                    <Icon :name="getJobIcon(run.job_name)" class="w-5 h-5 text-purple-600" />
                    <span class="font-medium text-gray-900">{{ getJobLabel(run.job_name) }}</span>
                  </div>

                  <!-- Status -->
                  <div class="w-24">
                    <span
                      class="px-2 py-1 text-xs rounded-full"
                      :class="{
                        'bg-green-100 text-green-800': run.status === 'completed',
                        'bg-red-100 text-red-800': run.status === 'failed',
                        'bg-yellow-100 text-yellow-800': run.status === 'started'
                      }"
                    >
                      {{ run.status === 'completed' ? 'OK' : run.status === 'failed' ? 'Greska' : 'U toku' }}
                    </span>
                  </div>

                  <!-- Duration -->
                  <div class="w-16 text-sm text-gray-500">
                    {{ run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : '-' }}
                  </div>

                  <!-- Result -->
                  <div class="flex-1 text-sm">
                    <span v-if="run.records_processed !== null">
                      <span class="text-green-600 font-medium">{{ run.records_success }}</span>
                      <span class="text-gray-400">/</span>
                      <span class="text-gray-600">{{ run.records_processed }}</span>
                      <span v-if="run.records_failed > 0" class="text-red-600 ml-1">({{ run.records_failed }} failed)</span>
                    </span>
                    <span v-else-if="run.error_message" class="text-red-500 truncate" :title="run.error_message">
                      {{ run.error_message.substring(0, 50) }}...
                    </span>
                    <span v-else class="text-gray-400">-</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- End Tab Content: Jobs -->

      <!-- Tab Content: Preferences -->
      <div v-show="activeTab === 'preferences'">
        <!-- Loading State -->
        <div v-if="preferencesLoading" class="flex items-center justify-center h-64">
          <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
        </div>

        <div v-else-if="preferencesData">
          <!-- KPI Summary Cards -->
          <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-8">
            <div class="bg-white rounded-lg shadow p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-500 text-xs">Ukupno praćenih</p>
                  <p class="text-2xl font-bold text-purple-600">{{ preferencesData.summary.total_tracked }}</p>
                </div>
                <Icon name="mdi:heart" class="w-8 h-8 text-purple-200" />
              </div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-500 text-xs">Korisnika sa listom</p>
                  <p class="text-2xl font-bold text-blue-600">{{ preferencesData.summary.users_with_products }}</p>
                </div>
                <Icon name="mdi:account-heart" class="w-8 h-8 text-blue-200" />
              </div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-500 text-xs">Prosjek po korisniku</p>
                  <p class="text-2xl font-bold text-green-600">{{ preferencesData.summary.avg_per_user }}</p>
                </div>
                <Icon name="mdi:calculator" class="w-8 h-8 text-green-200" />
              </div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-500 text-xs">Stopa usvajanja</p>
                  <p class="text-2xl font-bold text-teal-600">{{ preferencesData.summary.adoption_rate }}%</p>
                </div>
                <Icon name="mdi:percent" class="w-8 h-8 text-teal-200" />
              </div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-500 text-xs">Novih danas</p>
                  <p class="text-2xl font-bold text-orange-600">{{ preferencesData.summary.new_today }}</p>
                </div>
                <Icon name="mdi:plus-circle" class="w-8 h-8 text-orange-200" />
              </div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-500 text-xs">Novih ove sedmice</p>
                  <p class="text-2xl font-bold text-pink-600">{{ preferencesData.summary.new_this_week }}</p>
                </div>
                <Icon name="mdi:calendar-week" class="w-8 h-8 text-pink-200" />
              </div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-500 text-xs">Verificiranih korisnika</p>
                  <p class="text-2xl font-bold text-gray-600">{{ preferencesData.summary.total_users }}</p>
                </div>
                <Icon name="mdi:account-group" class="w-8 h-8 text-gray-200" />
              </div>
            </div>
          </div>

          <!-- Chart Section -->
          <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <div class="flex items-center justify-between mb-6">
              <h3 class="text-lg font-semibold text-gray-900">Rast praćenih proizvoda (zadnjih 30 dana)</h3>
              <button
                @click="loadPreferencesAnalytics"
                class="text-sm text-purple-600 hover:text-purple-800 flex items-center gap-1"
              >
                <Icon name="mdi:refresh" class="w-4 h-4" :class="{ 'animate-spin': preferencesLoading }" />
                Osvježi
              </button>
            </div>
            <div class="h-64">
              <ClientOnly>
                <Line v-if="preferencesChartData" :data="preferencesChartData" :options="preferencesChartOptions" />
              </ClientOnly>
            </div>
          </div>

          <!-- Two Column Layout -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Top Tracked Terms -->
            <div class="bg-white rounded-lg shadow-md p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Top praćeni pojmovi</h3>
              <div class="space-y-3">
                <div
                  v-for="(term, index) in preferencesData.top_terms"
                  :key="term.term"
                  class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div class="flex items-center gap-3">
                    <span
                      class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
                      :class="index < 3 ? 'bg-purple-600 text-white' : 'bg-gray-300 text-gray-700'"
                    >
                      {{ index + 1 }}
                    </span>
                    <span class="font-medium text-gray-900">{{ term.term }}</span>
                  </div>
                  <span class="text-sm text-gray-500">{{ term.count }} korisnika</span>
                </div>
              </div>
            </div>

            <!-- Distribution -->
            <div class="bg-white rounded-lg shadow-md p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Distribucija po broju proizvoda</h3>
              <div class="space-y-4">
                <div v-for="(count, bucket) in preferencesData.distribution" :key="bucket" class="flex items-center gap-4">
                  <span class="w-16 text-sm font-medium text-gray-700">{{ bucket }}</span>
                  <div class="flex-1 bg-gray-200 rounded-full h-6 overflow-hidden">
                    <div
                      class="bg-gradient-to-r from-purple-500 to-purple-600 h-full rounded-full flex items-center justify-end pr-2"
                      :style="{ width: `${Math.max(count / maxDistribution * 100, 5)}%` }"
                    >
                      <span v-if="count > 0" class="text-xs text-white font-medium">{{ count }}</span>
                    </div>
                  </div>
                  <span class="w-12 text-sm text-gray-500 text-right">{{ count }}</span>
                </div>
              </div>
              <div class="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-500">
                <p>Koliko korisnika ima koliko praćenih proizvoda</p>
              </div>
            </div>
          </div>

          <!-- Info Box -->
          <div class="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div class="flex items-start gap-3">
              <Icon name="mdi:information" class="w-5 h-5 text-blue-600 mt-0.5" />
              <div class="text-sm text-blue-800">
                <p class="font-medium mb-1">KPI cilj: Povećati broj praćenih proizvoda po korisniku</p>
                <p class="text-blue-600">
                  Trenutno {{ preferencesData.summary.users_with_products }} od {{ preferencesData.summary.total_users }} korisnika ({{ preferencesData.summary.adoption_rate }}%)
                  prati proizvode. Prosjek je {{ preferencesData.summary.avg_per_user }} proizvoda po korisniku.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- End Tab Content: Preferences -->

      <!-- Tab Content: Cities -->
      <div v-show="activeTab === 'cities'">
        <!-- Loading State -->
        <div v-if="citiesLoading" class="flex items-center justify-center h-64">
          <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
        </div>

        <div v-else-if="citiesData">
          <!-- Summary Card -->
          <div class="bg-white rounded-lg shadow p-6 mb-6">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-gray-900">Korisnici po gradovima</h3>
                <p class="text-sm text-gray-500 mt-1">
                  Ukupno {{ citiesData.total }} korisnika u {{ citiesData.cities.length }} lokacija
                </p>
              </div>
              <button
                @click="loadCities"
                class="text-sm text-purple-600 hover:text-purple-800 flex items-center gap-1"
              >
                <Icon name="mdi:refresh" class="w-4 h-4" :class="{ 'animate-spin': citiesLoading }" />
                Osvježi
              </button>
            </div>
          </div>

          <!-- Cities Table -->
          <div class="bg-white rounded-lg shadow-md overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">#</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grad</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Broj korisnika</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Procenat</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vizualizacija</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr
                  v-for="(city, index) in citiesData.cities"
                  :key="city.city"
                  :class="[
                    'hover:bg-gray-50',
                    city.city === 'N/A' ? 'bg-yellow-50' : ''
                  ]"
                >
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ index + 1 }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center gap-2">
                      <Icon
                        :name="city.city === 'N/A' ? 'mdi:help-circle' : 'mdi:map-marker'"
                        :class="city.city === 'N/A' ? 'text-yellow-500' : 'text-purple-600'"
                        class="w-5 h-5"
                      />
                      <span
                        class="font-medium"
                        :class="city.city === 'N/A' ? 'text-yellow-700' : 'text-gray-900'"
                      >
                        {{ city.city }}
                      </span>
                      <span v-if="city.city === 'N/A'" class="text-xs text-yellow-600">(nije uneseno)</span>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="text-lg font-semibold text-gray-900">{{ city.count }}</span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="text-sm text-gray-600">
                      {{ ((city.count / citiesData.total) * 100).toFixed(1) }}%
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="w-48 bg-gray-200 rounded-full h-4 overflow-hidden">
                      <div
                        class="h-full rounded-full"
                        :class="city.city === 'N/A' ? 'bg-yellow-400' : 'bg-purple-500'"
                        :style="{ width: `${Math.max((city.count / maxCityCount) * 100, 2)}%` }"
                      ></div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Info Box -->
          <div class="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div class="flex items-start gap-3">
              <Icon name="mdi:information" class="w-5 h-5 text-blue-600 mt-0.5" />
              <div class="text-sm text-blue-800">
                <p class="font-medium mb-1">Kako korisnici biraju grad?</p>
                <p class="text-blue-600">
                  Korisnici mogu odabrati grad prilikom registracije ili u postavkama profila.
                  N/A znači da korisnik nije unio grad u svoj profil.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- End Tab Content: Cities -->
    </div>

    <!-- Stores Modal -->
    <div
      v-if="storesModalUser"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      @click.self="storesModalUser = null"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[80vh] overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-900">
            Prodavnice - <span data-pii>{{ storesModalUser.first_name || storesModalUser.email }}</span>
          </h3>
          <button
            @click="storesModalUser = null"
            class="text-gray-400 hover:text-gray-600"
          >
            <Icon name="mdi:close" class="w-6 h-6" />
          </button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[60vh]">
          <div class="space-y-2">
            <div
              v-for="store in storesModalUser.preferred_stores"
              :key="store.id"
              class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              <Icon name="mdi:store" class="w-5 h-5 text-purple-600" />
              <span class="text-gray-900">{{ store.name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete User Confirmation Modal -->
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      @click.self="showDeleteModal = false"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-red-50">
          <h3 class="text-lg font-semibold text-red-800 flex items-center gap-2">
            <Icon name="mdi:alert-circle" class="w-6 h-6" />
            Potvrda brisanja
          </h3>
          <button
            @click="showDeleteModal = false"
            class="text-gray-400 hover:text-gray-600"
          >
            <Icon name="mdi:close" class="w-6 h-6" />
          </button>
        </div>
        <div class="p-6">
          <p class="text-gray-700 mb-4">
            Jeste li sigurni da želite obrisati korisnika?
          </p>
          <div v-if="userToDelete" class="bg-gray-50 rounded-lg p-4 mb-4">
            <div class="font-medium text-gray-900" data-pii>
              {{ userToDelete.first_name || 'N/A' }} {{ userToDelete.last_name || '' }}
            </div>
            <div class="text-sm text-gray-600" data-pii>{{ userToDelete.email || userToDelete.phone }}</div>
          </div>
          <p class="text-sm text-red-600 mb-6">
            <Icon name="mdi:alert" class="w-4 h-4 inline mr-1" />
            Ova akcija je nepovratna. Svi podaci korisnika će biti trajno obrisani.
          </p>
          <div class="flex justify-end gap-3">
            <button
              @click="showDeleteModal = false"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Odustani
            </button>
            <button
              @click="deleteUser"
              :disabled="deleting"
              class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <Icon v-if="deleting" name="mdi:loading" class="w-4 h-4 animate-spin" />
              <Icon v-else name="mdi:delete" class="w-4 h-4" />
              {{ deleting ? 'Brisanje...' : 'Obriši korisnika' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

definePageMeta({
  middleware: 'auth',
  layout: 'default'
})

const { get, post, del } = useApi()
const { user } = useAuth()

// Redirect non-admins
if (!user.value?.is_admin) {
  navigateTo('/')
}

// Tab state
const activeTab = ref('users')

const users = ref<any[]>([])
const searchQuery = ref('')
const deactivatedFilter = ref('') // '', 'deactivated', 'active'
const notificationsFilter = ref('') // '', 'disabled', 'enabled'
const pagination = ref({
  page: 1,
  per_page: 50,
  total: 0,
  pages: 0
})
const userActivity = ref<Record<string, any[]>>({})
const loadingActivity = ref<Record<string, boolean>>({})
const storesModalUser = ref<any>(null)

// Delete user state
const showDeleteModal = ref(false)
const userToDelete = ref<any>(null)
const deleting = ref(false)

// Email history state
const emails = ref<any[]>([])
const emailsLoading = ref(false)
const emailTypeFilter = ref('')
const emailStats = ref<any>(null)
const emailPagination = ref({
  page: 1,
  per_page: 30,
  total: 0,
  pages: 0
})

// Job logs state
const jobs = ref<any[]>([])
const jobsLoading = ref(false)
const runningJob = ref<string | null>(null)
const jobMessage = ref('')
const jobMessageType = ref<'success' | 'error'>('success')

// Preferences analytics state
const preferencesData = ref<any>(null)
const preferencesLoading = ref(false)
const preferencesChartData = ref<any>(null)

// Cities state
const citiesData = ref<any>(null)
const citiesLoading = ref(false)

const maxCityCount = computed(() => {
  if (!citiesData.value?.cities?.length) return 1
  return citiesData.value.cities[0]?.count || 1
})

const preferencesChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        precision: 0
      }
    }
  },
  interaction: {
    intersect: false,
    mode: 'index' as const
  }
}

const maxDistribution = computed(() => {
  if (!preferencesData.value?.distribution) return 1
  return Math.max(...Object.values(preferencesData.value.distribution) as number[]) || 1
})
const jobHistory = ref<any[]>([])
const jobHistoryLoading = ref(false)
const jobHistoryFilter = ref('')

// Analytics chart state
const selectedInterval = ref('day')
const analyticsData = ref<any>(null)
const chartData = ref<any>(null)
const chartLoading = ref(true)

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        precision: 0
      }
    }
  },
  interaction: {
    intersect: false,
    mode: 'index' as const
  }
}

// Stats from server (not computed from current page)
const stats = ref({
  total: 0,
  email: 0,
  google: 0,
  phone: 0,
  verified: 0
})

// Deactivation stats
const deactivationStats = ref({
  deactivated_users: 0,
  users_with_disabled_notifications: 0,
  total_users: 0,
  active_users: 0
})

// Computed stats from server data
const totalUsers = computed(() => stats.value.total)
const emailUsers = computed(() => stats.value.email)
const googleUsers = computed(() => stats.value.google)
const phoneUsers = computed(() => stats.value.phone)
const verifiedUsers = computed(() => stats.value.verified)

onMounted(() => {
  loadUsers()
  loadAnalytics()
  loadDeactivationStats()
})

async function loadDeactivationStats() {
  try {
    const data = await get('/api/admin/users/deactivation-stats')
    deactivationStats.value = data
  } catch (error) {
    console.error('Error loading deactivation stats:', error)
  }
}

async function loadUsers(page = 1) {
  try {
    const params = new URLSearchParams()
    params.append('page', page.toString())
    params.append('per_page', pagination.value.per_page.toString())
    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }
    if (deactivatedFilter.value) {
      params.append('deactivated', deactivatedFilter.value)
    }
    if (notificationsFilter.value) {
      params.append('notifications', notificationsFilter.value)
    }

    const data = await get(`/api/admin/users?${params.toString()}`)
    users.value = data.users
    pagination.value = data.pagination

    // Update stats from server response
    if (data.stats) {
      stats.value = data.stats
    }

    // Load activity for all users after loading
    nextTick(() => {
      loadAllUserActivities()
    })
  } catch (error) {
    console.error('Error loading users:', error)
  }
}

function changePage(page: number) {
  if (page >= 1 && page <= pagination.value.pages) {
    pagination.value.page = page
    loadUsers(page)
  }
}

let searchTimeout: NodeJS.Timeout
function debouncedSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadUsers(1)
  }, 500)
}

function formatDate(dateString: string) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-Latn-BA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getDeviceIcon(deviceType: string | null): string {
  switch (deviceType) {
    case 'mobile':
      return 'mdi:cellphone'
    case 'tablet':
      return 'mdi:tablet'
    case 'desktop':
      return 'mdi:monitor'
    default:
      return 'mdi:help-circle-outline'
  }
}

function truncateStoreName(name: string): string {
  if (name.length > 12) {
    return name.substring(0, 10) + '...'
  }
  return name
}

function showStoresModal(user: any) {
  storesModalUser.value = user
}

async function loadUserActivity(userId: string) {
  loadingActivity.value[userId] = true
  try {
    const data = await get(`/api/admin/users/${userId}/activity`)
    userActivity.value[userId] = data.activity
  } catch (error) {
    console.error('Error loading user activity:', error)
  } finally {
    loadingActivity.value[userId] = false
  }
}

async function loadAllUserActivities() {
  // Load activity for all visible users in parallel
  const promises = users.value.map(u => loadUserActivity(u.id))
  await Promise.all(promises)
}

function openUserProfile(userId: string) {
  navigateTo(`/admin/users/${userId}`)
}

// Delete user functions
function confirmDeleteUser(user: any) {
  userToDelete.value = user
  showDeleteModal.value = true
}

async function deleteUser() {
  if (!userToDelete.value) return

  deleting.value = true
  try {
    await del(`/api/admin/users/${userToDelete.value.id}`)

    // Remove user from list
    users.value = users.value.filter(u => u.id !== userToDelete.value.id)

    // Update stats
    if (stats.value.total > 0) stats.value.total--

    // Close modal
    showDeleteModal.value = false
    userToDelete.value = null
  } catch (error: any) {
    console.error('Error deleting user:', error)
    alert(error.message || 'Greška pri brisanju korisnika')
  } finally {
    deleting.value = false
  }
}

// Analytics functions
function toCumulative(arr: number[]): number[] {
  let sum = 0
  return arr.map(val => {
    sum += val
    return sum
  })
}

async function loadAnalytics() {
  chartLoading.value = true

  try {
    const data = await get(`/api/admin/users/analytics?interval=${selectedInterval.value}`)
    analyticsData.value = data

    // Convert to cumulative values for slope chart
    const cumulativeUsers = toCumulative(data.datasets.users.data)
    const cumulativeSearches = toCumulative(data.datasets.searches.data)

    // Build chart data with cumulative values
    chartData.value = {
      labels: data.labels,
      datasets: [
        {
          label: data.datasets.users.label,
          data: cumulativeUsers,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.3,
          fill: true
        },
        {
          label: data.datasets.searches.label,
          data: cumulativeSearches,
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          tension: 0.3,
          fill: true
        }
      ]
    }
  } catch (error) {
    console.error('Error loading analytics:', error)
  } finally {
    chartLoading.value = false
  }
}

function changeInterval(interval: string) {
  selectedInterval.value = interval
  loadAnalytics()
}

function getIntervalLabel() {
  if (selectedInterval.value === 'hour') return 'Zadnja 24 sata'
  if (selectedInterval.value === 'day') return 'Zadnjih 30 dana'
  return 'Zadnjih 12 mjeseci'
}

// Email functions
async function loadEmails(page = 1) {
  emailsLoading.value = true
  try {
    let url = `/api/admin/retention/emails?page=${page}&per_page=${emailPagination.value.per_page}`
    if (emailTypeFilter.value) {
      url += `&type=${emailTypeFilter.value}`
    }
    const data = await get(url)
    emails.value = data.emails
    emailPagination.value = data.pagination

    // Load stats if not loaded
    if (!emailStats.value) {
      loadEmailStats()
    }
  } catch (error) {
    console.error('Error loading emails:', error)
  } finally {
    emailsLoading.value = false
  }
}

async function loadEmailStats() {
  try {
    const data = await get('/api/admin/retention/emails/stats')
    emailStats.value = data
  } catch (error) {
    console.error('Error loading email stats:', error)
  }
}

function getEmailTypeLabel(emailType: string): string {
  const labels: Record<string, string> = {
    'daily_scan': 'Dnevno sken.',
    'weekly_summary': 'Sedmicni',
    'verification': 'Verifikacija',
    'welcome': 'Dobrodoslica',
    'password_reset': 'Reset lozinke',
    'coupon_purchase': 'Kupon',
    'coupon_reminder': 'Podsjetnik',
    'coupon_expiry': 'Istek kupona',
    'bonus_credits': 'Bonus krediti'
  }
  return labels[emailType] || emailType
}

function getEmailTypeBadgeClass(emailType: string): string {
  const classes: Record<string, string> = {
    'daily_scan': 'bg-blue-100 text-blue-800',
    'weekly_summary': 'bg-purple-100 text-purple-800',
    'verification': 'bg-yellow-100 text-yellow-800',
    'welcome': 'bg-green-100 text-green-800',
    'coupon_purchase': 'bg-pink-100 text-pink-800',
    'coupon_reminder': 'bg-orange-100 text-orange-800'
  }
  return classes[emailType] || 'bg-gray-100 text-gray-800'
}

function formatEmailDate(dateString: string | null) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-Latn-BA', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Preferences analytics functions
async function loadPreferencesAnalytics() {
  preferencesLoading.value = true
  try {
    const data = await get('/api/admin/preferences/analytics')
    preferencesData.value = data

    // Build chart data
    preferencesChartData.value = {
      labels: data.chart.labels,
      datasets: [{
        label: 'Praćeni proizvodi',
        data: data.chart.data,
        borderColor: 'rgb(147, 51, 234)',
        backgroundColor: 'rgba(147, 51, 234, 0.1)',
        tension: 0.3,
        fill: true
      }]
    }
  } catch (error) {
    console.error('Error loading preferences analytics:', error)
  } finally {
    preferencesLoading.value = false
  }
}

// Cities functions
async function loadCities() {
  citiesLoading.value = true
  try {
    const data = await get('/api/admin/users/cities')
    citiesData.value = data
  } catch (error) {
    console.error('Error loading cities:', error)
  } finally {
    citiesLoading.value = false
  }
}

// Job functions
async function loadJobs() {
  jobsLoading.value = true
  try {
    const data = await get('/api/admin/retention/jobs')
    jobs.value = data.jobs

    // Also load job history
    if (jobHistory.value.length === 0) {
      loadJobHistory()
    }
  } catch (error) {
    console.error('Error loading jobs:', error)
  } finally {
    jobsLoading.value = false
  }
}

async function loadJobHistory() {
  jobHistoryLoading.value = true
  try {
    let url = '/api/admin/retention/jobs/history?limit=50'
    if (jobHistoryFilter.value) {
      url += `&job_name=${jobHistoryFilter.value}`
    }
    const data = await get(url)
    jobHistory.value = data.history || []
  } catch (error) {
    console.error('Error loading job history:', error)
  } finally {
    jobHistoryLoading.value = false
  }
}

async function triggerJob(jobName: string) {
  runningJob.value = jobName
  jobMessage.value = ''
  try {
    await post(`/api/admin/retention/jobs/${jobName}/run`, {})
    jobMessageType.value = 'success'
    jobMessage.value = `Posao "${getJobLabel(jobName)}" je uspjesno pokrenut!`
    // Refresh jobs status after a delay
    setTimeout(() => {
      loadJobs()
      loadJobHistory()
    }, 2000)
  } catch (error: any) {
    jobMessageType.value = 'error'
    jobMessage.value = `Greska pri pokretanju posla: ${error.message || 'Nepoznata greska'}`
  } finally {
    runningJob.value = null
    // Clear message after 5 seconds
    setTimeout(() => {
      jobMessage.value = ''
    }, 5000)
  }
}

function getJobIcon(jobName: string): string {
  const icons: Record<string, string> = {
    'product_scan': 'mdi:magnify-scan',
    'email_summary': 'mdi:email-newsletter',
    'monthly_credits': 'mdi:currency-usd',
    'coupon_reminders': 'mdi:bell-ring'
  }
  return icons[jobName] || 'mdi:clock-outline'
}

function getJobLabel(jobName: string): string {
  const labels: Record<string, string> = {
    'product_scan': 'Skeniranje proizvoda',
    'email_summary': 'Email izvjestaji',
    'monthly_credits': 'Mjesecni krediti',
    'coupon_reminders': 'Podsjetnici za kupone',
    'weekly_summary': 'Sedmicni izvjestaj',
    'biweekly_reengagement': 'Re-engagement',
    'social_media_publish': 'Social Media'
  }
  return labels[jobName] || jobName
}

// Group job history by day
const jobHistoryByDay = computed(() => {
  const grouped: Record<string, any[]> = {}

  for (const run of jobHistory.value) {
    if (!run.started_at) continue
    const dateKey = run.started_at.split('T')[0] // Get YYYY-MM-DD
    if (!grouped[dateKey]) {
      grouped[dateKey] = []
    }
    grouped[dateKey].push(run)
  }

  // Sort keys descending (newest first)
  const sortedKeys = Object.keys(grouped).sort().reverse()
  const result: Record<string, any[]> = {}
  for (const key of sortedKeys) {
    result[key] = grouped[key]
  }

  return result
})

function formatDayHeader(dateStr: string): string {
  const date = new Date(dateStr)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  if (dateStr === today.toISOString().split('T')[0]) {
    return 'Danas'
  }
  if (dateStr === yesterday.toISOString().split('T')[0]) {
    return 'Jucer'
  }

  return date.toLocaleDateString('sr-Latn-BA', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

function formatTimeOnly(dateString: string | null): string {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleTimeString('sr-Latn-BA', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

useSeoMeta({
  title: 'Korisnici - Admin - Popust.ba',
  description: 'Admin panel za upravljanje korisnicima'
})
</script>
