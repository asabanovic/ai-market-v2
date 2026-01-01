<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100] p-4 overflow-y-auto" @click.self="$emit('close')">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md md:max-w-xl lg:max-w-2xl p-6 md:p-8 relative animate-slide-up my-auto max-h-[90vh] overflow-y-auto">
          <!-- Close button -->
          <button
            @click="$emit('close')"
            class="absolute top-3 right-3 text-gray-400 hover:text-gray-600 transition-colors p-1"
          >
            <Icon name="mdi:close" class="w-5 h-5" />
          </button>

          <!-- Use unified PreferencesForm -->
          <PreferencesForm
            :show-skip-button="true"
            :show-back-button="false"
            source="profile"
            :initial-phone="user?.phone"
            :initial-interests="existingInterests"
            @complete="handleComplete"
            @skip="handleSkip"
          />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const props = defineProps<{
  show: boolean
  isNewUser?: boolean
}>()

const emit = defineEmits(['close', 'complete', 'skip'])

const { user } = useAuth()

// Get existing interests from user preferences
const existingInterests = computed(() => {
  const preferences = user.value?.preferences as Record<string, any> | null
  if (preferences?.grocery_interests && Array.isArray(preferences.grocery_interests)) {
    return preferences.grocery_interests
  }
  return []
})

function handleComplete() {
  emit('complete')
}

function handleSkip() {
  emit('skip')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.animate-slide-up {
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
