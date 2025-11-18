<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-500/10 via-transparent to-accent-500/10">
    <!-- Animated background elements -->
    <div class="absolute inset-0 overflow-hidden">
      <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl animate-pulse-slow"></div>
      <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-500/20 rounded-full blur-3xl animate-pulse-slow animate-delay-200"></div>
    </div>

    <div class="relative z-10 w-full">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
// Auth layout for login/register pages
</script>
