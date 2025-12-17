<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
    <!-- Product Image -->
    <div class="relative h-32 bg-gray-100">
      <img
        v-if="product.image_path || product.image_url"
        :src="getImageUrl(product.image_path || product.image_url)"
        :alt="product.title"
        class="w-full h-full object-cover"
      />
      <div v-else class="flex items-center justify-center h-full text-gray-300">
        <Icon name="mdi:image-off" class="w-10 h-10" />
      </div>

      <!-- Price comparison badge -->
      <div
        v-if="matchType === 'clone' && product.is_cheaper"
        class="absolute top-2 left-2 bg-green-500 text-white px-2 py-0.5 rounded-full text-xs font-bold"
      >
        {{ Math.abs(product.price_diff_pct) }}% jeftinije
      </div>
      <div
        v-else-if="matchType === 'clone' && product.is_more_expensive"
        class="absolute top-2 left-2 bg-red-400 text-white px-2 py-0.5 rounded-full text-xs font-bold"
      >
        {{ product.price_diff_pct }}% skuplje
      </div>

      <!-- Size badge for siblings -->
      <div
        v-if="matchType === 'sibling' && product.size_value"
        class="absolute top-2 left-2 bg-blue-500 text-white px-2 py-0.5 rounded-full text-xs font-bold"
      >
        {{ product.size_value }}{{ product.size_unit || 'g' }}
      </div>

      <!-- Brand badge for brand variants -->
      <div
        v-if="matchType === 'brand_variant' && product.brand"
        class="absolute top-2 left-2 bg-orange-500 text-white px-2 py-0.5 rounded-full text-xs font-bold truncate max-w-[80%]"
      >
        {{ product.brand }}
      </div>

      <!-- Store name -->
      <div class="absolute bottom-2 right-2 bg-black/60 text-white px-2 py-0.5 rounded text-xs">
        {{ product.business_name }}
      </div>
    </div>

    <!-- Product Info -->
    <div class="p-3">
      <h4 class="text-sm font-medium text-gray-900 line-clamp-2 min-h-[2.5rem] mb-2">
        {{ product.title }}
      </h4>

      <!-- Price -->
      <div class="flex items-baseline gap-2 mb-3">
        <span class="text-lg font-bold" :class="priceColorClass">
          {{ formatPrice(product.effective_price) }} KM
        </span>
        <span
          v-if="product.discount_price && product.base_price > product.discount_price"
          class="text-xs text-gray-400 line-through"
        >
          {{ formatPrice(product.base_price) }} KM
        </span>
      </div>

      <!-- Action buttons - no click to open, only actions -->
      <div class="flex items-center justify-between">
        <div class="flex gap-1">
          <!-- Like button -->
          <button
            @click="emitAction('like')"
            class="p-1.5 rounded-lg hover:bg-green-50 transition-colors group"
            :class="{ 'bg-green-100': liked }"
            title="Svidja mi se"
          >
            <Icon
              name="mdi:thumb-up"
              class="w-4 h-4 transition-colors"
              :class="liked ? 'text-green-600' : 'text-gray-400 group-hover:text-green-600'"
            />
          </button>

          <!-- Dislike button -->
          <button
            @click="emitAction('dislike')"
            class="p-1.5 rounded-lg hover:bg-red-50 transition-colors group"
            :class="{ 'bg-red-100': disliked }"
            title="Ne svidja mi se"
          >
            <Icon
              name="mdi:thumb-down"
              class="w-4 h-4 transition-colors"
              :class="disliked ? 'text-red-600' : 'text-gray-400 group-hover:text-red-600'"
            />
          </button>
        </div>

        <div class="flex gap-1">
          <!-- Favorite button -->
          <button
            @click="emitAction('favorite')"
            class="p-1.5 rounded-lg hover:bg-pink-50 transition-colors group"
            :class="{ 'bg-pink-100': favorited }"
            title="Dodaj u favorite"
          >
            <Icon
              :name="favorited ? 'mdi:heart' : 'mdi:heart-outline'"
              class="w-4 h-4 transition-colors"
              :class="favorited ? 'text-pink-600' : 'text-gray-400 group-hover:text-pink-600'"
            />
          </button>

          <!-- Add to list button -->
          <button
            @click="emitAction('list')"
            class="p-1.5 rounded-lg hover:bg-purple-50 transition-colors group"
            :class="{ 'bg-purple-100': inList }"
            title="Dodaj na listu"
          >
            <Icon
              :name="inList ? 'mdi:playlist-check' : 'mdi:playlist-plus'"
              class="w-4 h-4 transition-colors"
              :class="inList ? 'text-purple-600' : 'text-gray-400 group-hover:text-purple-600'"
            />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  product: {
    id: number
    title: string
    brand?: string
    product_type?: string
    size_value?: number
    size_unit?: string
    variant?: string
    base_price?: number
    discount_price?: number
    effective_price: number
    image_path?: string
    image_url?: string
    business_id: number
    business_name: string
    city?: string
    price_diff: number
    price_diff_pct: number
    is_cheaper: boolean
    is_more_expensive: boolean
  }
  sourcePrice: number
  matchType: 'clone' | 'sibling' | 'brand_variant'
}>()

const emit = defineEmits<{
  action: [action: string, productId: number]
}>()

const config = useRuntimeConfig()

// Local state for action states
const liked = ref(false)
const disliked = ref(false)
const favorited = ref(false)
const inList = ref(false)

// Price color based on comparison
const priceColorClass = computed(() => {
  if (props.matchType === 'clone') {
    if (props.product.is_cheaper) return 'text-green-600'
    if (props.product.is_more_expensive) return 'text-red-500'
  }
  return 'text-gray-900'
})

const getImageUrl = (path: string) => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${config.public.apiBase}/static/${path}`
}

const formatPrice = (price: number) => {
  return price?.toFixed(2) || '0.00'
}

const emitAction = (action: string) => {
  // Toggle local state
  switch (action) {
    case 'like':
      liked.value = !liked.value
      if (liked.value) disliked.value = false
      break
    case 'dislike':
      disliked.value = !disliked.value
      if (disliked.value) liked.value = false
      break
    case 'favorite':
      favorited.value = !favorited.value
      break
    case 'list':
      inList.value = !inList.value
      break
  }

  emit('action', action, props.product.id)
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
