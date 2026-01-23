<template>
  <div class="card group cursor-pointer" @click="viewProduct">
    <div class="relative">
      <img
        v-if="product.image_path"
        :src="product.image_path"
        :alt="product.title"
        class="w-full h-48 object-cover rounded-lg mb-4"
      />
      <div v-else class="w-full h-48 bg-gradient-to-br from-primary-100 to-accent-100 dark:from-primary-900 dark:to-accent-900 rounded-lg mb-4 flex items-center justify-center">
        <Icon name="mdi:image-off" class="w-12 h-12 text-gray-400" />
      </div>

      <!-- Discount badge -->
      <div
        v-if="product.has_discount"
        class="absolute top-2 right-2 bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold"
      >
        -{{ product.discount_percentage }}%
      </div>

      <!-- Contributor Badge Overlay (bottom of image) -->
      <div
        v-if="product.contributor_name"
        class="absolute bottom-4 left-0 right-0 z-10 bg-gradient-to-t from-purple-900/90 via-purple-800/70 to-transparent px-2 py-2.5 rounded-b-lg"
      >
        <div class="flex items-center gap-2 text-white text-xs">
          <div class="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center flex-shrink-0 ring-2 ring-white/50">
            <Icon name="mdi:account" class="w-4 h-4 text-white" />
          </div>
          <span class="line-clamp-2">
            Dodao/la <span class="font-semibold">{{ product.contributor_name }}</span>
          </span>
        </div>
      </div>
    </div>

    <div class="space-y-2">
      <h3 class="font-semibold text-lg line-clamp-2 group-hover:text-primary-500 transition-colors">
        {{ product.title }}
      </h3>

      <div class="flex items-baseline space-x-2">
        <span
          v-if="product.discount_price"
          class="text-2xl font-bold text-primary-500"
        >
          {{ formatPrice(product.discount_price) }} KM
        </span>
        <span
          :class="[
            'text-xl font-bold',
            product.discount_price ? 'line-through text-gray-400' : 'text-primary-500'
          ]"
        >
          {{ formatPrice(product.base_price) }} KM
        </span>
      </div>

      <div v-if="product.category" class="text-sm text-gray-600 dark:text-gray-400">
        <Icon name="mdi:tag" class="w-4 h-4 inline" />
        {{ product.category }}
      </div>

      <div v-if="product.business" class="text-sm text-gray-600 dark:text-gray-400">
        <Icon name="mdi:store" class="w-4 h-4 inline" />
        {{ product.business.name }}
      </div>

      <div v-if="product.expires" class="text-sm text-gray-600 dark:text-gray-400">
        <Icon name="mdi:calendar" class="w-4 h-4 inline" />
        Važi do: {{ formatDate(product.expires) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Product {
  id: number
  title: string
  base_price: number
  discount_price?: number
  has_discount?: boolean
  discount_percentage?: number
  image_path?: string
  category?: string
  expires?: string
  business?: {
    name: string
  }
  contributor_name?: string
  contributed_by?: string
}

interface Props {
  product: Product
}

const props = defineProps<Props>()

const formatPrice = (price: number) => {
  return price.toFixed(2)
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('bs-BA')
}

const viewProduct = () => {
  navigateTo(`/products/${props.product.id}`)
}
</script>
