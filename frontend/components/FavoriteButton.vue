<template>
  <button
    @click.stop="toggleFavorite"
    :disabled="loading"
    :class="[
      'transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed',
      showLabel
        ? 'inline-flex items-center gap-2 py-2.5 px-4 rounded-lg font-medium text-sm'
        : 'p-2 rounded-full bg-white/90 backdrop-blur-sm shadow-md hover:scale-110 hover:shadow-lg',
      isFavorited
        ? showLabel
          ? 'bg-red-500 hover:bg-red-600 text-white'
          : 'text-red-500 hover:text-red-600'
        : showLabel
          ? 'bg-white border border-gray-300 text-gray-700 hover:border-red-500 hover:text-red-500'
          : 'text-gray-600 hover:text-red-500'
    ]"
    :aria-label="isFavorited ? 'Ukloni iz omiljenih' : 'Sačuvaj u omiljene'"
    :title="isFavorited ? 'Ukloni iz omiljenih' : 'Sačuvaj u omiljene - obavijestićemo vas o novim popustima'"
  >
    <Icon
      :name="isFavorited ? 'mdi:heart' : 'mdi:heart-outline'"
      :style="{ width: iconSize + 'px', height: iconSize + 'px' }"
      class="transition-transform flex-shrink-0"
      :class="{ 'animate-bounce': loading }"
    />
    <span v-if="showLabel" class="whitespace-nowrap">{{ isFavorited ? 'U omiljenima' : 'Omiljeno' }}</span>
  </button>
</template>

<script setup lang="ts">
import { useFavoritesStore } from '~/stores/favorites'

const props = withDefaults(defineProps<{
  productId: number
  size?: number
  showLabel?: boolean
}>(), {
  size: 24,
  showLabel: false
})

const iconSize = computed(() => props.size || 24)

const emit = defineEmits<{
  'updated': []
}>()

const favoritesStore = useFavoritesStore()
const { handleApiError, showSuccess } = useCreditsToast()

const loading = ref(false)

const isFavorited = computed(() => favoritesStore.isFavorited(props.productId))

async function toggleFavorite() {
  loading.value = true

  try {
    if (isFavorited.value) {
      // Remove from favorites
      const favoriteId = favoritesStore.getFavoriteId(props.productId)
      if (favoriteId) {
        const result = await favoritesStore.removeFavorite(favoriteId)
        if (result.success) {
          showSuccess('Uklonjeno iz omiljenih')
          emit('updated')
        } else if (result.error) {
          handleApiError(result.error)
        }
      }
    } else {
      // Add to favorites
      const result = await favoritesStore.addFavorite(props.productId)
      if (result.success) {
        if (!result.already) {
          showSuccess('Dodato u omiljene!')
        }
        emit('updated')
      } else if (result.error) {
        handleApiError(result.error)
      }
    }
  } finally {
    loading.value = false
  }
}
</script>
