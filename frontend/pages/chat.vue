<template>
  <div class="min-h-screen flex flex-col">
    <div class="flex-1 container mx-auto px-4 py-8">
      <div class="max-w-5xl mx-auto h-[calc(100vh-12rem)]">
        <div class="card h-full p-0 overflow-hidden">
          <ChatInterface />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth']
})

useSeoMeta({
  title: 'Chat - Popust.ba',
  description: 'Razgovarajte sa Popust asistentom',
})
</script>
