<template>
  <div class="container mx-auto px-4 py-12">
    <div v-if="product" class="max-w-4xl mx-auto">
      <div class="grid md:grid-cols-2 gap-8">
        <!-- Product image -->
        <div>
          <img
            v-if="product.image_path"
            :src="product.image_path"
            :alt="product.title"
            class="w-full rounded-2xl shadow-xl"
          />
          <div v-else class="w-full aspect-square bg-gradient-to-br from-primary-100 to-accent-100 dark:from-primary-900 dark:to-accent-900 rounded-2xl flex items-center justify-center">
            <Icon name="mdi:image-off" class="w-24 h-24 text-gray-400" />
          </div>
        </div>

        <!-- Product details -->
        <div class="space-y-6">
          <div>
            <h1 class="text-4xl font-bold mb-4">{{ product.title }}</h1>

            <div class="flex items-baseline space-x-4 mb-6">
              <span
                v-if="product.discount_price"
                class="text-5xl font-bold text-primary-500"
              >
                {{ formatPrice(product.discount_price) }} KM
              </span>
              <span
                :class="[
                  'text-3xl font-bold',
                  product.discount_price ? 'line-through text-gray-400' : 'text-primary-500'
                ]"
              >
                {{ formatPrice(product.base_price) }} KM
              </span>
            </div>

            <div v-if="product.has_discount" class="inline-block bg-red-500 text-white px-4 py-2 rounded-full font-bold mb-6">
              Ušteda: -{{ product.discount_percentage }}%
            </div>
          </div>

          <div class="space-y-4">
            <div v-if="product.category" class="flex items-center space-x-2">
              <Icon name="mdi:tag" class="w-5 h-5 text-gray-400" />
              <span>{{ product.category }}</span>
            </div>

            <div v-if="product.business" class="flex items-center space-x-2">
              <Icon name="mdi:store" class="w-5 h-5 text-gray-400" />
              <span>{{ product.business.name }}</span>
            </div>

            <div v-if="product.expires" class="flex items-center space-x-2">
              <Icon name="mdi:calendar" class="w-5 h-5 text-gray-400" />
              <span>Važi do: {{ formatDate(product.expires) }}</span>
            </div>
          </div>

          <div class="pt-6">
            <Button variant="primary" size="lg" block>
              <Icon name="mdi:cart" class="w-5 h-5" />
              <span>Pogledaj u prodavnici</span>
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading state -->
    <div v-else-if="isLoading" class="flex justify-center py-12">
      <LoadingSpinner />
    </div>

    <!-- Error state -->
    <div v-else class="text-center py-12">
      <Icon name="mdi:alert-circle" class="w-24 h-24 mx-auto mb-4 text-red-500" />
      <h2 class="text-2xl font-bold mb-2">Proizvod nije pronađen</h2>
      <NuxtLink to="/products" class="btn-primary inline-flex items-center space-x-2 mt-6">
        <Icon name="mdi:arrow-left" class="w-5 h-5" />
        <span>Nazad na proizvode</span>
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const api = useApi()

const product = ref<any>(null)
const isLoading = ref(false)

const formatPrice = (price: number) => {
  return price.toFixed(2)
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('bs-BA')
}

// Load product on mount
onMounted(async () => {
  isLoading.value = true
  try {
    const response = await api.get(`/api/products/${route.params.id}`)
    product.value = response.product
  } catch (error) {
    console.error('Failed to load product:', error)
  } finally {
    isLoading.value = false
  }
})

useSeoMeta({
  title: computed(() => product.value ? `${product.value.title} - AI Pijaca` : 'Proizvod - AI Pijaca'),
  description: computed(() => product.value?.title || 'Product details'),
})
</script>
