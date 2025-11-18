<template>
  <div>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </div>
</template>

<script setup lang="ts">
// Global app setup
const colorMode = useColorMode()

// Check auth on mount
onMounted(() => {
  const { checkAuth } = useAuth()
  checkAuth()
})
</script>
