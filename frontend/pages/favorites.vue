<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-start justify-between mb-4">
          <div class="flex-1">
            <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
              Omiljeni Proizvodi
            </h1>
            <p class="mt-2 text-gray-600 dark:text-gray-400">
              Vaša lista omiljenih proizvoda
            </p>
          </div>

          <!-- View Toggle -->
          <div v-if="favoritesStore.count > 0" class="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-lg p-1 shadow-sm">
            <button
              @click="viewMode = 'table'"
              :class="[
                'p-2 rounded transition-colors',
                viewMode === 'table'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              ]"
              title="Tabela prikaz"
            >
              <Icon name="mdi:table" class="w-5 h-5" />
            </button>
            <button
              @click="viewMode = 'tiles'"
              :class="[
                'p-2 rounded transition-colors',
                viewMode === 'tiles'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              ]"
              title="Pločice prikaz"
            >
              <Icon name="mdi:view-grid" class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="favoritesStore.loading" class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="favoritesStore.count === 0"
        class="text-center py-12"
      >
        <Icon name="mdi:heart-outline" class="w-24 h-24 text-gray-400 mx-auto mb-4" />
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          Nemate omiljenih proizvoda
        </h3>
        <p class="text-gray-600 dark:text-gray-400 mb-6">
          Počnite dodavati proizvode u omiljene kako biste ih brzo pronašli kasnije
        </p>
        <NuxtLink
          to="/proizvodi"
          class="inline-flex items-center px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors"
        >
          Pretraži proizvode
        </NuxtLink>
      </div>

      <!-- Table View -->
      <div v-else-if="viewMode === 'table'" class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Proizvod
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Prodavac
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Kategorija
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Cijena
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Popust
              </th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Akcije
              </th>
            </tr>
          </thead>
          <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            <tr
              v-for="favorite in favoritesStore.items"
              :key="favorite.favorite_id"
              class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <!-- Product with Image -->
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center gap-3">
                  <div class="flex-shrink-0 h-12 w-12">
                    <img
                      v-if="favorite.image_url"
                      :src="favorite.image_url"
                      :alt="favorite.name"
                      class="h-12 w-12 rounded object-cover"
                    />
                    <div v-else class="h-12 w-12 rounded bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                      <Icon name="mdi:image-off" class="w-6 h-6 text-gray-400" />
                    </div>
                  </div>
                  <div class="max-w-xs">
                    <div class="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {{ favorite.name }}
                    </div>
                  </div>
                </div>
              </td>

              <!-- Business -->
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center gap-2">
                  <img
                    v-if="favorite.business.logo"
                    :src="favorite.business.logo"
                    :alt="favorite.business.name"
                    class="w-6 h-6 object-contain"
                  />
                  <span class="text-sm text-gray-900 dark:text-white">
                    {{ favorite.business.name }}
                  </span>
                </div>
              </td>

              <!-- Category -->
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="text-sm text-gray-500 dark:text-gray-400">
                  {{ favorite.category || '-' }}
                </span>
              </td>

              <!-- Price -->
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex flex-col">
                  <span class="text-sm font-bold text-primary-600 dark:text-primary-400">
                    {{ favorite.price.toFixed(2) }} KM
                  </span>
                  <span
                    v-if="favorite.old_price"
                    class="text-xs text-gray-500 dark:text-gray-400 line-through"
                  >
                    {{ favorite.old_price.toFixed(2) }} KM
                  </span>
                </div>
              </td>

              <!-- Discount -->
              <td class="px-6 py-4 whitespace-nowrap">
                <span
                  v-if="favorite.discount_percent"
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                >
                  -{{ favorite.discount_percent }}%
                </span>
                <span v-else class="text-sm text-gray-400">-</span>
              </td>

              <!-- Actions -->
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="addToCart(favorite)"
                    class="inline-flex items-center px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white rounded-md transition-colors"
                    title="Dodaj u listu"
                  >
                    <Icon name="mdi:cart-plus" class="w-4 h-4 mr-1" />
                    Dodaj
                  </button>
                  <button
                    @click="removeFavorite(favorite.favorite_id)"
                    class="inline-flex items-center p-1.5 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors"
                    title="Ukloni iz omiljenih"
                  >
                    <Icon name="mdi:heart-off" class="w-5 h-5" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Tiles View -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div
          v-for="favorite in favoritesStore.items"
          :key="favorite.favorite_id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
        >
          <!-- Product Image -->
          <div class="relative h-48 bg-gray-200 dark:bg-gray-700">
            <img
              v-if="favorite.image_url"
              :src="favorite.image_url"
              :alt="favorite.name"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center">
              <Icon name="mdi:image-off" class="w-16 h-16 text-gray-400" />
            </div>

            <!-- Remove Favorite Button -->
            <button
              @click="removeFavorite(favorite.favorite_id)"
              class="absolute top-2 right-2 p-2 bg-white/90 dark:bg-gray-800/90 rounded-full hover:bg-red-500 hover:text-white transition-colors group"
            >
              <Icon name="mdi:heart" class="w-6 h-6 text-red-500 group-hover:text-white" />
            </button>

            <!-- Discount Badge -->
            <div
              v-if="favorite.discount_percent"
              class="absolute top-2 left-2 bg-red-500 text-white px-2 py-1 rounded-md text-sm font-bold"
            >
              -{{ favorite.discount_percent }}%
            </div>
          </div>

          <!-- Product Info -->
          <div class="p-4">
            <!-- Business -->
            <div class="flex items-center gap-2 mb-2">
              <img
                v-if="favorite.business.logo"
                :src="favorite.business.logo"
                :alt="favorite.business.name"
                class="w-6 h-6 object-contain"
              />
              <span class="text-sm text-gray-600 dark:text-gray-400">
                {{ favorite.business.name }}
              </span>
            </div>

            <!-- Product Name -->
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
              {{ favorite.name }}
            </h3>

            <!-- Category -->
            <p v-if="favorite.category" class="text-sm text-gray-500 dark:text-gray-400 mb-3">
              {{ favorite.category }}
            </p>

            <!-- Price -->
            <div class="flex items-center gap-2 mb-4">
              <span class="text-2xl font-bold text-primary-600 dark:text-primary-400">
                {{ favorite.price.toFixed(2) }} KM
              </span>
              <span
                v-if="favorite.old_price"
                class="text-sm text-gray-500 dark:text-gray-400 line-through"
              >
                {{ favorite.old_price.toFixed(2) }} KM
              </span>
            </div>

            <!-- Add to Cart Button -->
            <button
              @click="addToCart(favorite)"
              class="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <Icon name="mdi:cart-plus" class="w-5 h-5" />
              Dodaj u listu
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useFavoritesStore } from '~/stores/favorites'
import { useCartStore } from '~/stores/cart'

definePageMeta({
  middleware: 'auth'
})

const favoritesStore = useFavoritesStore()
const cartStore = useCartStore()
const { handleApiError, showSuccess } = useCreditsToast()

// View mode: 'table' or 'tiles' (default to table)
const viewMode = ref<'table' | 'tiles'>('table')

// Fetch favorites on mount
onMounted(async () => {
  await favoritesStore.fetchFavorites()
})

async function removeFavorite(favoriteId: number) {
  const result = await favoritesStore.removeFavorite(favoriteId)
  if (result.success) {
    showSuccess('Uklonjeno iz omiljenih')
  } else if (result.error) {
    handleApiError(result.error)
  }
}

async function addToCart(favorite: any) {
  const result = await cartStore.addItem(
    favorite.product_id,
    favorite.business.id,
    1
  )

  if (result.success) {
    showSuccess(`"${favorite.name}" dodano na listu!`)
  } else if (result.error) {
    handleApiError(result.error)
  }
}
</script>
