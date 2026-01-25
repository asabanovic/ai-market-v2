<template>
  <div>
    <nav class="bg-white shadow-lg">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <div class="flex items-center">
          <NuxtLink to="/" class="flex items-center" :active-class="''" :exact-active-class="''">
            <img
              src="/logo.png"
              alt="Popust Logo"
              class="h-12 md:h-16 w-auto md:px-4 py-2 transition-transform hover:scale-105"
              @error="logoError = true"
            />
            <span v-if="logoError" class="text-xl md:text-2xl font-bold text-purple-600 px-4 md:px-8">Popust</span>
          </NuxtLink>
          <span class="hidden lg:inline-block text-sm text-gray-500 ml-2 border-l border-gray-300 pl-3">Kupuj pametnije</span>
        </div>

        <div class="hidden md:flex items-center space-x-6">
          <NuxtLink to="/" class="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors" :active-class="''" :exact-active-class="''">
            Početna
          </NuxtLink>
          <NuxtLink to="/proizvodi" class="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors" :active-class="''" :exact-active-class="''">
            Proizvodi
          </NuxtLink>
          <ClientOnly>
            <template v-if="!isAuthenticated">
              <NuxtLink to="/novosti" class="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors" :active-class="''" :exact-active-class="''">
                Novosti
              </NuxtLink>
              <NuxtLink to="/kako-radimo" class="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors" :active-class="''" :exact-active-class="''">
                Kako radimo
              </NuxtLink>
              <NuxtLink to="/kontakt" class="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors" :active-class="''" :exact-active-class="''">
                Kontakt
              </NuxtLink>
            </template>
            <template #fallback>
              <NuxtLink to="/novosti" class="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors" :active-class="''" :exact-active-class="''">
                Novosti
              </NuxtLink>
              <NuxtLink to="/kako-radimo" class="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors" :active-class="''" :exact-active-class="''">
                Kako radimo
              </NuxtLink>
              <NuxtLink to="/kontakt" class="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors" :active-class="''" :exact-active-class="''">
                Kontakt
              </NuxtLink>
            </template>
          </ClientOnly>

          <ClientOnly>
            <!-- City Indicator -->
            <div v-if="isAuthenticated && user" class="relative">
              <button
                @click.stop="toggleCityDropdown"
                class="flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-full border border-purple-200 bg-purple-50 text-purple-700 hover:bg-purple-100 transition-colors"
                :title="user?.city ? `Vaš grad: ${user.city}` : 'Odaberite grad'"
              >
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                </svg>
                <span class="max-w-[100px] truncate">{{ user?.city || 'Grad' }}</span>
                <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M7 10l5 5 5-5z"/>
                </svg>
              </button>

              <!-- City Dropdown -->
              <div
                v-if="showCityDropdown"
                v-click-outside="closeCityDropdown"
                class="absolute right-0 z-50 mt-2 w-56 origin-top-right rounded-lg bg-white shadow-xl ring-1 ring-black ring-opacity-5 max-h-80 overflow-y-auto"
              >
                <div class="px-3 py-2 border-b border-gray-100">
                  <p class="text-xs text-gray-500 font-medium">Odaberite grad</p>
                </div>
                <div class="py-1">
                  <button
                    v-for="cityOption in cities"
                    :key="cityOption.id"
                    @click="changeCity(cityOption)"
                    :class="[
                      'flex items-center w-full px-3 py-2 text-sm text-left transition-colors',
                      cityOption.id === user?.city_id
                        ? 'bg-purple-50 text-purple-700 font-medium'
                        : 'text-gray-700 hover:bg-gray-50'
                    ]"
                    :disabled="isSavingCity"
                  >
                    <svg v-if="cityOption.id === user?.city_id" class="w-4 h-4 mr-2 text-purple-600" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                    </svg>
                    <span :class="{ 'ml-6': cityOption.id !== user?.city_id }">{{ cityOption.name }}</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Streak Badge -->
            <button
              v-if="isAuthenticated && user"
              @click="openStreakModal"
              class="text-sm font-medium px-3 py-1 rounded-full border border-purple-200 bg-purple-50 text-purple-700 hover:bg-purple-100 transition-colors flex items-center gap-1.5"
              title="Vaš streak - kliknite za detalje"
            >
              <span>{{ user?.current_streak >= 7 ? '🔥' : user?.current_streak >= 3 ? '🔥' : '✨' }}</span>
              <span class="font-bold">{{ user?.current_streak || 0 }}</span>
            </button>

            <!-- Search Counter -->
            <NuxtLink
              v-if="searchCounts"
              to="/krediti-uskoro"
              :class="[
                'text-sm font-medium px-3 py-1 rounded-full border cursor-pointer hover:opacity-80 transition-opacity',
                searchCounts.remaining === 0
                  ? 'border-red-200 bg-red-50 text-red-700'
                  : searchCounts.remaining <= 2
                  ? 'border-yellow-200 bg-yellow-50 text-yellow-700'
                  : 'border-green-200 bg-green-50 text-green-700'
              ]"
              :title="searchCounts.next_reset_date ? `Krediti se obnavljaju: ${formatResetDate(searchCounts.next_reset_date)}. Kliknite za više info.` : 'Kliknite za info o kreditima'"
            >
              <template v-if="searchCounts.is_unlimited">
                Krediti: {{ searchCounts.remaining }}
              </template>
              <template v-else>
                Krediti: {{ searchCounts.remaining }}/{{ searchCounts.weekly_limit || searchCounts.daily_limit || 40 }}
              </template>
            </NuxtLink>

            <!-- Header Icons (Favorites & Cart) -->
            <HeaderIcons v-if="isAuthenticated" @toggle-sidebar="showSidebar = true" />

            <!-- Privacy Mode Toggle (Admin only) -->
            <button
              v-if="isAuthenticated && user?.is_admin"
              @click="togglePrivacyMode"
              :class="[
                'p-2 rounded-full transition-all',
                privacyModeEnabled
                  ? 'bg-red-100 text-red-600 hover:bg-red-200'
                  : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
              ]"
              :title="privacyModeEnabled ? 'Privacy Mode ON - Klik za isključiti' : 'Privacy Mode OFF - Klik za uključiti'"
            >
              <svg v-if="privacyModeEnabled" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>

            <!-- Support Icon with Badge -->
            <NuxtLink
              v-if="isAuthenticated"
              to="/podrska"
              class="relative p-2 text-gray-700 hover:text-primary-600 transition-colors"
              title="Podrška"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <span
                v-if="supportUnreadCount > 0"
                class="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center"
              >
                {{ supportUnreadCount > 9 ? '9+' : supportUnreadCount }}
              </span>
            </NuxtLink>

            <template #fallback>
              <!-- Empty fallback to avoid server/client mismatch -->
            </template>
          </ClientOnly>

          <ClientOnly>
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
                    <p class="text-sm font-medium text-gray-900" data-pii>{{ userName }}</p>
                    <p class="text-xs text-gray-500 truncate" data-pii>{{ user?.email }}</p>
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
                      to="/liste"
                      class="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      @click="showProfileDropdown = false"
                    >
                      <Icon name="mdi:cart" class="w-4 h-4 mr-2" />
                      Moja korpa
                    </NuxtLink>
                    <NuxtLink
                      to="/podrska"
                      class="flex items-center justify-between px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      @click="showProfileDropdown = false"
                    >
                      <span class="flex items-center">
                        <Icon name="mdi:headset" class="w-4 h-4 mr-2" />
                        Podrška
                      </span>
                      <span
                        v-if="supportUnreadCount > 0"
                        class="bg-red-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center"
                      >
                        {{ supportUnreadCount }}
                      </span>
                    </NuxtLink>
                    <NuxtLink
                      to="/novosti"
                      class="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      @click="showProfileDropdown = false"
                    >
                      <Icon name="mdi:newspaper" class="w-4 h-4 mr-2" />
                      Novosti
                    </NuxtLink>
                    <NuxtLink
                      v-if="user?.has_business"
                      to="/moj-biznis"
                      class="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      @click="showProfileDropdown = false"
                    >
                      <Icon name="mdi:store" class="w-4 h-4 mr-2" />
                      Moj Biznis
                    </NuxtLink>
                    <button
                      @click="openFeedback"
                      class="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <Icon name="mdi:message-text-outline" class="w-4 h-4 mr-2" />
                      Povratna informacija
                    </button>
                    <NuxtLink
                      to="/racuni"
                      class="flex items-center justify-between px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      @click="showProfileDropdown = false"
                    >
                      <span class="flex items-center">
                        <Icon name="mdi:receipt-text-outline" class="w-4 h-4 mr-2" />
                        Moji računi
                      </span>
                      <span class="bg-amber-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">BETA</span>
                    </NuxtLink>
                    <NuxtLink
                      v-if="user?.is_admin"
                      to="/admin"
                      class="flex items-center px-4 py-2 text-sm text-purple-600 hover:bg-purple-50"
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
              <NuxtLink to="/prijava" class="px-4 py-2 text-sm font-medium border border-gray-200 rounded-lg text-gray-600 hover:border-gray-300 hover:text-gray-800 transition-colors">
                Prijava
              </NuxtLink>
              <NuxtLink to="/registracija" class="px-4 py-2 text-sm font-medium border border-gray-800 rounded-lg text-gray-800 bg-white hover:bg-gray-800 hover:text-white transition-colors">
                Registracija
              </NuxtLink>
            </template>
          </ClientOnly>
        </div>

        <!-- Mobile menu button -->
        <div class="md:hidden flex items-center">
          <button
            @click="showMobileMenu = !showMobileMenu"
            class="text-gray-500 hover:text-gray-600 focus:outline-none focus:text-gray-600 p-2"
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
        <NuxtLink to="/" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors" :active-class="''" :exact-active-class="''">
          Početna
        </NuxtLink>
        <NuxtLink to="/proizvodi" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors" :active-class="''" :exact-active-class="''">
          Proizvodi
        </NuxtLink>
        <ClientOnly>
          <template v-if="!isAuthenticated">
            <NuxtLink to="/novosti" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors" :active-class="''" :exact-active-class="''">
              Novosti
            </NuxtLink>
            <NuxtLink to="/kako-radimo" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors" :active-class="''" :exact-active-class="''">
              Kako radimo
            </NuxtLink>
            <NuxtLink to="/kontakt" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors" :active-class="''" :exact-active-class="''">
              Kontakt
            </NuxtLink>
          </template>
          <template #fallback>
            <NuxtLink to="/novosti" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors" :active-class="''" :exact-active-class="''">
              Novosti
            </NuxtLink>
            <NuxtLink to="/kako-radimo" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors" :active-class="''" :exact-active-class="''">
              Kako radimo
            </NuxtLink>
            <NuxtLink to="/kontakt" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors" :active-class="''" :exact-active-class="''">
              Kontakt
            </NuxtLink>
          </template>
        </ClientOnly>

        <ClientOnly>
          <!-- Mobile City Selector -->
          <div v-if="isAuthenticated && user" class="mx-3 mb-3">
            <label class="block text-xs text-gray-500 mb-1 px-1">Vaš grad</label>
            <select
              :value="user?.city_id || ''"
              @change="(e) => handleMobileCityChange((e.target as HTMLSelectElement).value)"
              class="w-full px-3 py-2 text-sm border border-purple-200 rounded-md bg-purple-50 text-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
              :disabled="isSavingCity"
            >
              <option value="">Odaberite grad</option>
              <option v-for="cityOption in cities" :key="cityOption.id" :value="cityOption.id">{{ cityOption.name }}</option>
            </select>
          </div>

          <!-- Mobile Streak Badge -->
          <button
            v-if="isAuthenticated && user"
            @click="openStreakModal"
            class="text-sm font-medium px-3 py-2 rounded-md mx-3 mb-2 border border-purple-200 bg-purple-50 text-purple-700 flex items-center gap-2 w-[calc(100%-1.5rem)]"
          >
            <span>{{ user?.current_streak >= 7 ? '🔥' : user?.current_streak >= 3 ? '🔥' : '✨' }}</span>
            <span class="font-bold">{{ user?.current_streak || 0 }}</span>
            <span class="text-purple-600">dana streak</span>
          </button>

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
              <div>Krediti: {{ searchCounts.remaining }}/{{ searchCounts.weekly_limit || searchCounts.daily_limit || 40 }}</div>
              <div v-if="searchCounts.next_reset_date" class="text-xs opacity-75 mt-1">
                Dopuna: {{ formatResetDate(searchCounts.next_reset_date) }}
              </div>
            </template>
          </div>

          <template #fallback>
            <!-- Empty fallback to avoid server/client mismatch -->
          </template>
        </ClientOnly>

        <ClientOnly>
          <template v-if="isAuthenticated">
            <div class="border-t border-gray-200 pt-2 pb-2 px-3">
              <p class="text-sm font-medium text-gray-900">{{ userName }}</p>
              <p class="text-xs text-gray-500">{{ user?.email }}</p>
            </div>
            <NuxtLink to="/profil" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors">
              <Icon name="mdi:account" class="w-4 h-4 inline mr-2" />
              Moj profil
            </NuxtLink>
            <NuxtLink to="/liste" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors">
              <Icon name="mdi:cart" class="w-4 h-4 inline mr-2" />
              Moja korpa
            </NuxtLink>
            <NuxtLink to="/podrska" class="flex items-center justify-between px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors">
              <span>
                <Icon name="mdi:headset" class="w-4 h-4 inline mr-2" />
                Podrška
              </span>
              <span
                v-if="supportUnreadCount > 0"
                class="bg-red-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center"
              >
                {{ supportUnreadCount }}
              </span>
            </NuxtLink>
            <NuxtLink v-if="user?.has_business" to="/moj-biznis" class="block px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors">
              <Icon name="mdi:store" class="w-4 h-4 inline mr-2" />
              Moj Biznis
            </NuxtLink>
            <button
              @click="openFeedback"
              class="block w-full text-left px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors"
            >
              <Icon name="mdi:message-text-outline" class="w-4 h-4 inline mr-2" />
              Povratna informacija
            </button>
            <NuxtLink to="/racuni" class="flex items-center justify-between px-3 py-2 text-gray-700 hover:text-purple-600 nav-text transition-colors">
              <span>
                <Icon name="mdi:receipt-text-outline" class="w-4 h-4 inline mr-2" />
                Moji računi
              </span>
              <span class="bg-amber-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">BETA</span>
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
            <NuxtLink to="/prijava" class="block mx-3 my-2 px-4 py-2 border border-gray-200 rounded-lg text-gray-600 hover:border-gray-300 hover:text-gray-800 nav-text transition-colors text-center">
              Prijava
            </NuxtLink>
            <NuxtLink to="/registracija" class="block mx-3 my-2 px-4 py-2 border border-gray-800 rounded-lg text-gray-800 bg-white hover:bg-gray-800 hover:text-white nav-text transition-colors text-center">
              Registracija
            </NuxtLink>
          </template>
        </ClientOnly>
      </div>
    </div>

    <!-- Shopping Sidebar -->
    <ShoppingSidebar :is-open="showSidebar" @close="showSidebar = false" />

    <!-- Toast Container -->
    <ToastContainer />

    <!-- Streak Timeline Modal -->
    <StreakTimeline ref="streakTimelineRef" />
  </nav>

    <!-- Mobile Bottom Navigation (outside nav to avoid hydration issues) -->
    <ClientOnly>
      <LayoutMobileBottomNav @toggle-sidebar="showSidebar = true" />
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
const { isAuthenticated, authReady, user, logout } = useAuth()
const { get, put } = useApi()
const { searchCounts, refreshCredits, clearCredits } = useSearchCredits()
const { privacyModeEnabled, togglePrivacyMode } = usePrivacyMode()

const showMobileMenu = ref(false)
const showProfileDropdown = ref(false)
const showSidebar = ref(false)
const logoError = ref(false)
const supportUnreadCount = ref(0)

// Streak timeline ref
const streakTimelineRef = ref<{ openModal: () => void } | null>(null)

function openStreakModal() {
  streakTimelineRef.value?.openModal()
}

// City selector state
const showCityDropdown = ref(false)
interface CityOption {
  id: number
  name: string
}
const cities = ref<CityOption[]>([])
const isSavingCity = ref(false)

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
    await refreshCredits()
    await loadCities()
    await loadSupportUnreadCount()
  }
})

async function loadCities() {
  try {
    const data = await get('/auth/cities')
    // Handle both old format (string[]) and new format ({id, name}[])
    if (data.cities && data.cities.length > 0) {
      if (typeof data.cities[0] === 'string') {
        // Old format - convert to objects (id will be null)
        cities.value = data.cities.map((name: string) => ({ id: 0, name }))
      } else {
        cities.value = data.cities
      }
    }
  } catch (error) {
    console.error('Error loading cities:', error)
  }
}

async function loadSupportUnreadCount() {
  try {
    const data = await get('/api/support/unread-count')
    supportUnreadCount.value = data.unread_count || 0
  } catch (error) {
    // Silently fail - user may not have access
    supportUnreadCount.value = 0
  }
}

watch(isAuthenticated, async (newVal) => {
  if (newVal) {
    await refreshCredits()
    await loadCities()
    await loadSupportUnreadCount()
  } else {
    clearCredits()
    supportUnreadCount.value = 0
  }
})

function formatResetDate(dateString: string): string {
  try {
    const date = new Date(dateString)
    const dayNames = ['Nedjelja', 'Ponedjeljak', 'Utorak', 'Srijeda', 'Četvrtak', 'Petak', 'Subota']
    const monthNames = ['januar', 'februar', 'mart', 'april', 'maj', 'juni', 'juli', 'avgust', 'septembar', 'oktobar', 'novembar', 'decembar']

    const dayName = dayNames[date.getDay()]
    const day = date.getDate()
    const month = monthNames[date.getMonth()]

    return `${dayName}, ${day}. ${month}`
  } catch (e) {
    return dateString
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

function openFeedback() {
  showProfileDropdown.value = false
  showMobileMenu.value = false
  // Dispatch custom event that app.vue listens for
  if (process.client) {
    window.dispatchEvent(new CustomEvent('open-feedback-popup'))
  }
}

function toggleCityDropdown() {
  showCityDropdown.value = !showCityDropdown.value
}

function closeCityDropdown() {
  showCityDropdown.value = false
}

async function changeCity(cityOption: CityOption) {
  if (!cityOption || cityOption.id === user.value?.city_id) {
    showCityDropdown.value = false
    return
  }

  isSavingCity.value = true
  try {
    const response = await put('/auth/user/profile', { city_id: cityOption.id })
    if (response.success && user.value) {
      user.value.city = cityOption.name
      user.value.city_id = cityOption.id
    }
  } catch (error) {
    console.error('Error updating city:', error)
  } finally {
    isSavingCity.value = false
    showCityDropdown.value = false
  }
}

// Handle mobile city dropdown change (receives string value from select)
function handleMobileCityChange(cityIdStr: string) {
  if (!cityIdStr) return
  const cityId = parseInt(cityIdStr, 10)
  const cityOption = cities.value.find(c => c.id === cityId)
  if (cityOption) {
    changeCity(cityOption)
  }
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
