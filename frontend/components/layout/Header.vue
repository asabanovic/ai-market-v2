<template>
  <nav class="bg-white shadow-lg">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <div class="flex items-center">
          <NuxtLink to="/" class="flex items-center text-lg font-semibold text-gray-900">
            <span class="text-2xl font-bold text-purple-600">AI Pijaca</span>
          </NuxtLink>
        </div>

        <div class="hidden md:flex items-center space-x-6">
          <NuxtLink to="/" class="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors">
            Početna
          </NuxtLink>
          <NuxtLink to="/proizvodi" class="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors">
            Proizvodi
          </NuxtLink>
          <NuxtLink to="/kako-radimo" class="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors">
            Kako radimo
          </NuxtLink>
          <NuxtLink to="/kontakt" class="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors">
            Kontakt
          </NuxtLink>

          <!-- Search Counter -->
          <div
            v-if="searchCounts"
            :class="[
              'text-sm font-medium px-3 py-1 rounded-full border',
              searchCounts.remaining === 0
                ? 'border-red-200 bg-red-50 text-red-700'
                : searchCounts.remaining <= 2
                ? 'border-yellow-200 bg-yellow-50 text-yellow-700'
                : 'border-green-200 bg-green-50 text-green-700'
            ]"
          >
            <template v-if="searchCounts.is_unlimited">
              Krediti: {{ searchCounts.remaining }}
            </template>
            <template v-else>
              Krediti: {{ searchCounts.remaining }}/{{ searchCounts.daily_limit }}
            </template>
          </div>

          <!-- Header Icons (Favorites & Cart) -->
          <HeaderIcons v-if="isAuthenticated" @toggle-sidebar="showSidebar = true" />

          <template v-if="isAuthenticated">
            <div class="relative">
              <button
                @click.stop="toggleDropdown"
                class="flex items-center gap-2 text-gray-700 hover:text-purple-600 px-2 py-1.5 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
              >
                <!-- Circular Avatar -->
                <div class="w-9 h-9 rounded-full bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center text-white font-semibold text-sm shadow-sm">
                  {{ userInitials }}
                </div>
                <!-- Name in two rows -->
                <div class="flex flex-col items-start text-left">
                  <span class="text-xs font-medium leading-tight">{{ user?.first_name || 'Korisnik' }}</span>
                  <span class="text-xs text-gray-500 leading-tight">{{ user?.last_name || '' }}</span>
                </div>
                <Icon name="mdi:chevron-down" class="w-4 h-4 text-gray-400" />
              </button>
              <div
                v-if="showProfileDropdown"
                v-click-outside="closeDropdown"
                class="absolute right-0 z-50 mt-2 w-56 origin-top-right rounded-md bg-white shadow-xl ring-1 ring-black ring-opacity-5 divide-y divide-gray-100"
              >
                <!-- User Info -->
                <div class="px-4 py-3">
                  <p class="text-sm font-medium text-gray-900">{{ userName }}</p>
                  <p class="text-xs text-gray-500 truncate">{{ user?.email }}</p>
                </div>

                <!-- Menu Items -->
                <div class="py-1">
                  <NuxtLink
                    to="/profil"
                    class="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    @click="showProfileDropdown = false"
                  >
                    <Icon name="mdi:account" class="w-4 h-4 mr-2" />
                    Moj profil
                  </NuxtLink>
                  <NuxtLink
                    v-if="user?.is_admin"
                    to="/admin"
                    class="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    @click="showProfileDropdown = false"
                  >
                    <Icon name="mdi:shield-crown" class="w-4 h-4 mr-2" />
                    Admin Dashboard
                  </NuxtLink>
                </div>

                <!-- Logout -->
                <div class="py-1">
                  <button
                    @click="handleLogout"
                    class="flex items-center w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                  >
                    <Icon name="mdi:logout" class="w-4 h-4 mr-2" />
                    Odjava
                  </button>
                </div>
              </div>
            </div>
          </template>
          <template v-else>
            <NuxtLink to="/prijava" class="text-gray-700 hover:text-purple-600 px-3 py-2 rounded-md nav-text transition-colors">
              Prijava
            </NuxtLink>
            <NuxtLink to="/registracija" class="bg-purple-600 text-white px-4 py-2 rounded-md btn-text hover:bg-purple-700 transition-colors purple-pattern-overlay">
              Registracija
            </NuxtLink>
          </template>
        </div>

        <!-- Mobile menu button -->
        <div class="md:hidden flex items-center">
          <button
            @click="showMobileMenu = !showMobileMenu"
            class="text-gray-500 hover:text-gray-600 focus:outline-none focus:text-gray-600"
            aria-label="toggle menu"
          >
            <svg viewBox="0 0 24 24" class="h-6 w-6 fill-current">
              <path fill-rule="evenodd" d="M4 5h16a1 1 0 0 1 0 2H4a1 1 0 1 1 0-2zm0 6h16a1 1 0 0 1 0 2H4a1 1 0 0 1 0-2zm0 6h16a1 1 0 0 1 0 2H4a1 1 0 0 1 0-2z" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile menu -->
    <div v-if="showMobileMenu" class="md:hidden bg-white border-t">
      <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
        <NuxtLink to="/" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors">
          Početna
        </NuxtLink>
        <NuxtLink to="/proizvodi" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors">
          Proizvodi
        </NuxtLink>
        <NuxtLink to="/kako-radimo" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors">
          Kako radimo
        </NuxtLink>
        <NuxtLink to="/kontakt" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors">
          Kontakt
        </NuxtLink>

        <div
          v-if="searchCounts"
          :class="[
            'text-sm font-medium px-3 py-2 rounded-md mx-3 border',
            searchCounts.remaining === 0
              ? 'border-red-200 bg-red-50 text-red-700'
              : searchCounts.remaining <= 2
              ? 'border-yellow-200 bg-yellow-50 text-yellow-700'
              : 'border-green-200 bg-green-50 text-green-700'
          ]"
        >
          <template v-if="searchCounts.is_unlimited">
            Krediti: {{ searchCounts.remaining }}
          </template>
          <template v-else>
            Krediti: {{ searchCounts.remaining }}/{{ searchCounts.daily_limit }}
          </template>
        </div>

        <template v-if="isAuthenticated">
          <div class="border-t border-gray-200 pt-2 pb-2 px-3">
            <p class="text-sm font-medium text-gray-900">{{ userName }}</p>
            <p class="text-xs text-gray-500">{{ user?.email }}</p>
          </div>
          <NuxtLink to="/profil" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors">
            <Icon name="mdi:account" class="w-4 h-4 inline mr-2" />
            Moj profil
          </NuxtLink>
          <NuxtLink v-if="user?.is_admin" to="/admin" class="block px-3 py-2 text-purple-600 hover:text-purple-700 nav-text transition-colors">
            <Icon name="mdi:shield-crown" class="w-4 h-4 inline mr-2" />
            Admin Dashboard
          </NuxtLink>
          <button
            @click="handleLogout"
            class="block w-full text-left px-3 py-2 text-red-600 hover:text-red-700 btn-text transition-colors"
          >
            <Icon name="mdi:logout" class="w-4 h-4 inline mr-2" />
            Odjava
          </button>
        </template>
        <template v-else>
          <NuxtLink to="/prijava" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors">
            Prijava
          </NuxtLink>
          <NuxtLink to="/registracija" class="block px-3 py-2 text-purple-600 hover:text-purple-700 nav-text transition-colors">
            Registracija
          </NuxtLink>
        </template>
      </div>
    </div>

    <!-- Shopping Sidebar -->
    <ShoppingSidebar :is-open="showSidebar" @close="showSidebar = false" />

    <!-- Toast Container -->
    <ToastContainer />
  </nav>
</template>

<script setup lang="ts">
const { isAuthenticated, user, logout } = useAuth()
const { get } = useApi()

const showMobileMenu = ref(false)
const showProfileDropdown = ref(false)
const showSidebar = ref(false)
const searchCounts = ref<any>(null)
const logoError = ref(false)

// Computed property for user display name
const userName = computed(() => {
  if (!user.value) return 'Profil'

  const firstName = user.value.first_name?.trim()
  const lastName = user.value.last_name?.trim()

  if (firstName && lastName) {
    return `${firstName} ${lastName}`
  } else if (firstName) {
    return firstName
  } else if (user.value.email) {
    return user.value.email.split('@')[0]
  }

  return 'Profil'
})

// Computed property for user initials
const userInitials = computed(() => {
  if (!user.value) return 'U'

  const firstName = user.value.first_name?.trim()
  const lastName = user.value.last_name?.trim()

  if (firstName && lastName) {
    return `${firstName[0]}${lastName[0]}`.toUpperCase()
  } else if (firstName) {
    return firstName[0].toUpperCase()
  } else if (user.value.email) {
    return user.value.email[0].toUpperCase()
  }

  return 'U'
})

onMounted(async () => {
  if (isAuthenticated.value) {
    await loadSearchCounts()
  }
})

watch(isAuthenticated, async (newVal) => {
  if (newVal) {
    await loadSearchCounts()
  } else {
    searchCounts.value = null
  }
})

async function loadSearchCounts() {
  try {
    const data = await get('/auth/search-counts')
    searchCounts.value = data
    console.log('Search counts loaded:', data)
  } catch (error) {
    console.error('Error loading search counts:', error)
  }
}

function toggleDropdown() {
  console.log('Toggle dropdown clicked, current state:', showProfileDropdown.value)
  showProfileDropdown.value = !showProfileDropdown.value
}

function closeDropdown() {
  showProfileDropdown.value = false
}

async function handleLogout() {
  showProfileDropdown.value = false
  await logout()
  navigateTo('/')
}

const vClickOutside = {
  mounted(el: any, binding: any) {
    el.clickOutsideEvent = (event: Event) => {
      if (!(el === event.target || el.contains(event.target))) {
        binding.value()
      }
    }
    document.addEventListener('click', el.clickOutsideEvent)
  },
  unmounted(el: any) {
    document.removeEventListener('click', el.clickOutsideEvent)
  }
}
</script>
