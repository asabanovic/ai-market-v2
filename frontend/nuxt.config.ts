export default defineNuxtConfig({
  devtools: { enabled: true },

  modules: [
    '@nuxt/image',
    '@nuxt/icon',
    '@vueuse/nuxt',
    '@pinia/nuxt',
  ],

  app: {
    head: {
      title: 'AI Pijaca - Inteligentna kupovina',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'AI-powered shopping assistant for Bosnia and Herzegovina' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        { href: 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap', rel: 'stylesheet' }
      ]
    },
    pageTransition: { name: 'page', mode: 'out-in' }
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:5001',
      googleOAuthEnabled: process.env.NUXT_PUBLIC_GOOGLE_OAUTH_ENABLED === 'true' || false
    }
  },

  // Performance optimizations
  nitro: {
    compressPublicAssets: true,
    minify: true,
  },

  experimental: {
    payloadExtraction: true,
    viewTransition: true,
  },

  // CSS
  css: ['~/assets/css/tailwind.css'],

  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  },

  // Build optimizations
  vite: {
    build: {
      cssCodeSplit: true,
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor': ['vue', 'vue-router'],
          }
        }
      }
    }
  },

  compatibilityDate: '2024-11-10'
})
