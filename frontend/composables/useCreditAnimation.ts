// Composable for managing credit reward animations
import { ref } from 'vue'

interface CreditAnimation {
  id: string
  amount: number
  timestamp: number
}

const animations = ref<CreditAnimation[]>([])

export const useCreditAnimation = () => {
  const triggerCreditAnimation = (amount: number) => {
    const animation: CreditAnimation = {
      id: `credit-${Date.now()}-${Math.random()}`,
      amount,
      timestamp: Date.now()
    }

    animations.value.push(animation)

    // Remove animation after it completes (2 seconds)
    setTimeout(() => {
      animations.value = animations.value.filter(a => a.id !== animation.id)
    }, 2000)
  }

  return {
    animations,
    triggerCreditAnimation
  }
}
