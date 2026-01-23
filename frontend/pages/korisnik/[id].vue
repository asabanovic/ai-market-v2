<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white shadow-sm">
      <div class="max-w-4xl mx-auto px-4 py-6">
        <NuxtLink to="/" class="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4">
          <Icon name="mdi:arrow-left" class="w-5 h-5 mr-1" />
          Nazad
        </NuxtLink>

        <!-- Loading state -->
        <div v-if="loading" class="animate-pulse">
          <div class="flex items-center gap-4">
            <div class="w-20 h-20 bg-gray-200 rounded-full"></div>
            <div class="space-y-2">
              <div class="h-6 bg-gray-200 rounded w-32"></div>
              <div class="h-4 bg-gray-200 rounded w-48"></div>
            </div>
          </div>
        </div>

        <!-- Profile info -->
        <div v-else-if="profile" class="flex items-center gap-4">
          <div class="w-20 h-20 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center">
            <span class="text-3xl font-bold text-white">
              {{ profile.display_name?.[0]?.toUpperCase() || '?' }}
            </span>
          </div>
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ profile.display_name }}</h1>
            <p class="text-gray-500">Clan od {{ profile.member_since }}</p>
          </div>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="text-center py-8">
          <Icon name="mdi:account-off" class="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h2 class="text-xl font-semibold text-gray-900 mb-2">Korisnik nije pronaden</h2>
          <p class="text-gray-500">Ovaj profil ne postoji ili je uklonjen.</p>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div v-if="profile" class="max-w-4xl mx-auto px-4 py-6">
      <div class="grid grid-cols-2 gap-4 mb-8">
        <div class="bg-white rounded-xl shadow-sm p-4 text-center">
          <div class="text-3xl font-bold text-green-600">{{ profile.total_contributions }}</div>
          <div class="text-sm text-gray-500">Dodanih proizvoda</div>
        </div>
        <div class="bg-white rounded-xl shadow-sm p-4 text-center">
          <div class="text-3xl font-bold text-amber-500">{{ profile.credits_earned }}</div>
          <div class="text-sm text-gray-500">Zaradenih kredita</div>
        </div>
      </div>

      <!-- Contributed Products -->
      <div v-if="contributedProducts.length > 0">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Dodani proizvodi</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <div
            v-for="product in contributedProducts"
            :key="product.id"
            class="bg-white rounded-xl shadow-sm overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
            @click="navigateToProduct(product.id)"
          >
            <div class="aspect-square bg-gray-100 flex items-center justify-center p-2">
              <img
                v-if="product.image_path"
                :src="getImageUrl(product.image_path)"
                :alt="product.title"
                class="max-h-full max-w-full object-contain"
              />
              <Icon v-else name="mdi:image-off" class="w-12 h-12 text-gray-300" />
            </div>
            <div class="p-3">
              <h3 class="text-sm font-medium text-gray-900 line-clamp-2 mb-1">{{ product.title }}</h3>
              <div class="flex items-baseline gap-2">
                <span v-if="product.has_discount" class="text-lg font-bold text-green-600">
                  {{ formatPrice(product.discount_price) }} KM
                </span>
                <span
                  :class="product.has_discount ? 'text-sm text-gray-400 line-through' : 'text-lg font-bold text-gray-900'"
                >
                  {{ formatPrice(product.base_price) }} KM
                </span>
              </div>
              <div class="flex items-center gap-1 mt-1">
                <img
                  v-if="product.business?.logo_path"
                  :src="product.business.logo_path"
                  :alt="product.business.name"
                  class="w-4 h-4 object-contain"
                />
                <span class="text-xs text-gray-500">{{ product.business?.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- No contributions yet -->
      <div v-else class="text-center py-12 bg-white rounded-xl shadow-sm">
        <Icon name="mdi:package-variant" class="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 class="text-lg font-semibold text-gray-900 mb-2">Nema dodanih proizvoda</h3>
        <p class="text-gray-500">Ovaj korisnik jos nije dodao proizvode.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()

const loading = ref(true)
const error = ref(false)
const profile = ref<any>(null)
const contributedProducts = ref<any[]>([])

const userId = computed(() => route.params.id as string)

const fetchProfile = async () => {
  loading.value = true
  error.value = false

  try {
    const response = await fetch(`${config.public.apiBase}/api/korisnik/${userId.value}`)

    if (!response.ok) {
      throw new Error('User not found')
    }

    const data = await response.json()
    profile.value = data.profile
    contributedProducts.value = data.contributed_products || []
  } catch (err) {
    console.error('Error fetching profile:', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

const getImageUrl = (path: string) => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${config.public.apiBase}${path}`
}

const formatPrice = (price: number) => {
  if (!price) return '0.00'
  return price.toFixed(2)
}

const navigateToProduct = (productId: number) => {
  router.push(`/proizvodi/${productId}`)
}

onMounted(() => {
  fetchProfile()
})

// SEO
useHead({
  title: () => profile.value ? `${profile.value.display_name} - Popust.ba` : 'Profil korisnika - Popust.ba'
})
</script>
