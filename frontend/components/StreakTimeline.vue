<template>
  <div v-if="isAuthenticated && user">
    <!-- Modal overlay -->
    <Transition name="fade">
      <div
        v-if="showModal"
        class="fixed inset-0 bg-black/50 z-50 flex items-end sm:items-center justify-center"
        @click.self="showModal = false"
      >
        <!-- Modal content -->
        <Transition name="slide-up">
          <div
            v-if="showModal"
            class="bg-white w-full sm:w-[520px] sm:rounded-2xl rounded-t-3xl p-6 sm:p-8 shadow-2xl max-h-[85vh] overflow-y-auto"
          >
            <!-- Header -->
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center gap-4">
                <span class="text-5xl" :class="{ 'animate-pulse': currentStreak >= 3 }">
                  {{ currentStreak >= 7 ? '🔥' : currentStreak >= 3 ? '🔥' : '✨' }}
                </span>
                <div>
                  <h3 class="text-2xl font-bold text-gray-900">
                    {{ currentStreak }} {{ currentStreak === 1 ? 'dan' : 'dana' }}
                  </h3>
                  <p class="text-base text-purple-600 font-medium">{{ streakMessage }}</p>
                </div>
              </div>
              <button
                @click="showModal = false"
                class="text-gray-400 hover:text-gray-600 p-2"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Next milestone info -->
            <div v-if="nextMilestone" class="bg-purple-50 rounded-xl p-4 mb-6">
              <p class="text-base text-purple-700">
                Još <span class="font-bold">{{ daysToNextMilestone }}</span> dana do
                <span class="font-bold text-purple-900">+{{ nextMilestoneBonus }} kredita</span>
              </p>
            </div>

            <!-- Progress bar -->
            <div class="relative mb-8">
              <!-- Background track -->
              <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  class="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full transition-all duration-500"
                  :style="{ width: progressPercent + '%' }"
                />
              </div>

              <!-- Milestone markers -->
              <div class="absolute top-0 left-0 right-0 h-2 flex items-center">
                <div
                  v-for="(bonus, days) in sortedMilestones"
                  :key="days"
                  class="absolute transform -translate-x-1/2 flex flex-col items-center"
                  :style="{ left: getMilestonePosition(Number(days)) + '%' }"
                >
                  <!-- Circle with bonus -->
                  <div
                    :class="[
                      'w-8 h-8 rounded-full border-2 flex items-center justify-center transition-all -mt-3',
                      currentStreak >= Number(days)
                        ? 'bg-green-500 border-green-600 text-white'
                        : 'bg-white border-gray-300 text-gray-500'
                    ]"
                  >
                    <span class="text-[10px] font-bold">+{{ bonus }}</span>
                  </div>
                  <!-- Days label -->
                  <span
                    :class="[
                      'text-[10px] font-medium mt-1',
                      currentStreak >= Number(days) ? 'text-green-600' : 'text-gray-400'
                    ]"
                  >
                    {{ days }}d
                  </span>
                </div>
              </div>
            </div>

            <!-- Stats -->
            <div class="grid grid-cols-2 gap-4 text-center">
              <div class="bg-gray-50 rounded-xl p-4">
                <p class="text-3xl font-bold text-purple-600">{{ currentStreak }}</p>
                <p class="text-sm text-gray-500">Trenutni streak</p>
              </div>
              <div class="bg-gray-50 rounded-xl p-4">
                <p class="text-3xl font-bold text-green-600">{{ user?.longest_streak || 0 }}</p>
                <p class="text-sm text-gray-500">Najduži streak</p>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>

    <!-- Bonus notification toast -->
    <Transition name="slide-down">
      <div
        v-if="showBonusNotification"
        class="fixed top-20 left-1/2 transform -translate-x-1/2 z-50 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-3"
      >
        <span class="text-2xl">{{ bonusNotification.milestone ? '🎉' : '✨' }}</span>
        <div>
          <p class="font-semibold">
            {{ bonusNotification.milestone ? `${bonusNotification.milestone}-dnevni streak!` : 'Dnevni bonus!' }}
          </p>
          <p class="text-sm opacity-90">
            +{{ bonusNotification.total }} kredita dodano
          </p>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
const { isAuthenticated, user, lastBonusAwarded, clearBonusNotification } = useAuth()

const showModal = ref(false)
const showBonusNotification = ref(false)
const bonusNotification = ref({ daily: 0, streak: 0, milestone: null as number | null, total: 0 })

const currentStreak = computed(() => user.value?.current_streak || 0)
const nextMilestone = computed(() => user.value?.next_milestone || null)
const nextMilestoneBonus = computed(() => user.value?.next_milestone_bonus || null)
const milestones = computed(() => user.value?.milestones || { 3: 5, 7: 10, 14: 20, 30: 50, 60: 100 })

const sortedMilestones = computed(() => {
  const m = milestones.value
  const sorted: Record<number, number> = {}
  const keys = Object.keys(m).map(Number).sort((a, b) => a - b)
  keys.forEach(k => { sorted[k] = m[k] })
  return sorted
})

const daysToNextMilestone = computed(() => {
  if (!nextMilestone.value) return 0
  return nextMilestone.value - currentStreak.value
})

const streakMessage = computed(() => {
  const streak = currentStreak.value
  if (streak === 0) return 'Počnite svoj streak!'
  if (streak === 1) return 'Odlično! Prvi dan!'
  if (streak < 3) return 'Nastavite tako!'
  if (streak < 7) return 'Super! Samo naprijed!'
  if (streak < 14) return 'Fenomenalno!'
  if (streak < 30) return 'Nevjerojatno!'
  return 'Legenda!'
})

// Get sorted milestone days array
const milestoneDays = computed(() => {
  return Object.keys(milestones.value).map(Number).sort((a, b) => a - b)
})

// Calculate progress percentage (0-100) using milestone index-based scaling
const progressPercent = computed(() => {
  const streak = currentStreak.value
  const days = milestoneDays.value
  const numMilestones = days.length

  // Find where streak falls between milestones
  for (let i = 0; i < numMilestones; i++) {
    if (streak < days[i]) {
      // Between previous milestone and this one
      const prevDays = i === 0 ? 0 : days[i - 1]
      const prevPos = i === 0 ? 0 : ((i) / numMilestones) * 100
      const nextPos = ((i + 1) / numMilestones) * 100
      const progress = (streak - prevDays) / (days[i] - prevDays)
      return prevPos + progress * (nextPos - prevPos)
    }
  }
  // Past last milestone
  return 100
})

// Get position of milestone marker on the bar (0-100%) - evenly spaced
function getMilestonePosition(days: number): number {
  const allDays = milestoneDays.value
  const index = allDays.indexOf(days)
  if (index === -1) return 0
  // Position based on index (1-indexed for visual spacing)
  return ((index + 1) / allDays.length) * 100
}

// Expose openModal for parent to call
function openModal() {
  showModal.value = true
}

defineExpose({ openModal, currentStreak })

// Watch for bonus notifications
watch(lastBonusAwarded, (bonus) => {
  if (bonus && (bonus.daily_bonus > 0 || bonus.streak_bonus > 0)) {
    bonusNotification.value = {
      daily: bonus.daily_bonus,
      streak: bonus.streak_bonus,
      milestone: bonus.milestone_reached,
      total: bonus.daily_bonus + bonus.streak_bonus
    }
    showBonusNotification.value = true

    // Auto-hide after 4 seconds
    setTimeout(() => {
      showBonusNotification.value = false
      clearBonusNotification()
    }, 4000)
  }
}, { immediate: true })
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

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(100%);
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translate(-50%, -20px);
}
</style>
