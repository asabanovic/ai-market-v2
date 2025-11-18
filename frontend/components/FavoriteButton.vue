<template>
  <button
    @click.stop="toggleFavorite"
    :disabled="loading"
    class="p-2 rounded-full bg-white/90 backdrop-blur-sm shadow-md transition-all duration-200 hover:scale-110 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
    :class="isFavorited ? 'text-red-500 hover:text-red-600' : 'text-gray-600 hover:text-red-500'"
    :aria-label="isFavorited ? 'Ukloni iz omiljenih' : 'Sačuvaj u omiljene'"
    :title="isFavorited ? 'Ukloni iz omiljenih' : 'Sačuvaj u omiljene - obavijestićemo vas o novim popustima'"
  >
    <Icon
      :name="isFavorited ? 'mdi:heart' : 'mdi:heart-outline'"
      class="w-6 h-6 transition-transform"
      :class="{ 'animate-bounce': loading }"
    />
  </button>
</template>

<script setup lang="ts">
import { useFavoritesStore } from '~/stores/favorites'

const props = defineProps<{
  productId: number
}>()

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
