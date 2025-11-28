export default defineNuxtConfig({
  devtools: { enabled: process.env.NODE_ENV !== 'production' },

  modules: [
    '@nuxt/image',
    '@nuxt/icon',
    '@vueuse/nuxt',
    '@pinia/nuxt',
  ],

  app: {
    head: {
      title: 'Popust.ba - Pronađite najbolje popuste i akcije u BiH',
      htmlAttrs: {
        lang: 'bs'
      },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        // Primary SEO
        { name: 'description', content: 'Pronađite najbolje popuste i akcije u Bosni i Hercegovini. Uporedite cijene u Bingu, Konzumu, Mercatoru i drugim trgovinama. Uštedite novac pri kupovini.' },
        { name: 'keywords', content: 'popusti, akcije, BiH, Bosna i Hercegovina, cijene, Bingo, Konzum, Mercator, kupovina, ušteda, supermarketi, trgovine' },
        { name: 'author', content: 'Popust.ba' },
        { name: 'robots', content: 'index, follow' },
        // Open Graph / Facebook
        { property: 'og:type', content: 'website' },
        { property: 'og:url', content: 'https://popust.ba/' },
        { property: 'og:title', content: 'Popust.ba - Pronađite najbolje popuste i akcije u BiH' },
        { property: 'og:description', content: 'Pronađite najbolje popuste i akcije u Bosni i Hercegovini. Uporedite cijene u Bingu, Konzumu, Mercatoru i drugim trgovinama.' },
        { property: 'og:image', content: 'https://popust.ba/logo.png' },
        { property: 'og:locale', content: 'bs_BA' },
        { property: 'og:site_name', content: 'Popust.ba' },
        // Twitter
        { name: 'twitter:card', content: 'summary_large_image' },
        { name: 'twitter:url', content: 'https://popust.ba/' },
        { name: 'twitter:title', content: 'Popust.ba - Pronađite najbolje popuste i akcije u BiH' },
        { name: 'twitter:description', content: 'Pronađite najbolje popuste i akcije u Bosni i Hercegovini. Uporedite cijene u Bingu, Konzumu, Mercatoru i drugim trgovinama.' },
        { name: 'twitter:image', content: 'https://popust.ba/logo.png' },
        // Theme color for mobile browsers
        { name: 'theme-color', content: '#7c3aed' },
        { name: 'msapplication-TileColor', content: '#7c3aed' },
        // Geo tags for local SEO
        { name: 'geo.region', content: 'BA' },
        { name: 'geo.placename', content: 'Bosnia and Herzegovina' }
      ],
      link: [
        // Favicons
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { rel: 'icon', type: 'image/png', sizes: '32x32', href: '/favicon-32x32.png' },
        { rel: 'icon', type: 'image/png', sizes: '16x16', href: '/favicon-16x16.png' },
        { rel: 'apple-touch-icon', sizes: '180x180', href: '/apple-touch-icon.png' },
        { rel: 'manifest', href: '/site.webmanifest' },
        // Canonical URL
        { rel: 'canonical', href: 'https://popust.ba/' },
        // Fonts
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

  // SSR configuration
  ssr: true,

  nitro: {
    preset: 'node-server',
    serveStatic: 'node',
    compressPublicAssets: true,
  },

  // CSS
  css: ['~/assets/css/tailwind.css'],

  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  },

  compatibilityDate: '2024-11-10'
})
