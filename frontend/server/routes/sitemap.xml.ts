// Dynamic sitemap.xml generation for SEO
// Fetches all products from the API and generates XML sitemap

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase || 'https://api.popust.ba'

  // Base URL for the site
  const baseUrl = 'https://popust.ba'

  // Static pages with their priorities and change frequencies
  const staticPages = [
    { url: '/', priority: '1.0', changefreq: 'daily' },
    { url: '/proizvodi', priority: '0.9', changefreq: 'daily' },
    { url: '/novosti', priority: '0.7', changefreq: 'weekly' },
    { url: '/prijava', priority: '0.5', changefreq: 'monthly' },
    { url: '/registracija', priority: '0.5', changefreq: 'monthly' },
    { url: '/podrska', priority: '0.4', changefreq: 'monthly' },
  ]

  // Fetch all product IDs from the API
  let productUrls: { url: string; priority: string; changefreq: string; lastmod?: string }[] = []

  try {
    // Fetch products for sitemap - this endpoint should return minimal data (id, updated_at)
    const response = await $fetch<{ products: { id: number; updated_at?: string }[] }>(
      `${apiBase}/api/sitemap/products`,
      { timeout: 30000 }
    )

    if (response?.products) {
      productUrls = response.products.map(product => ({
        url: `/proizvodi/${product.id}`,
        priority: '0.8',
        changefreq: 'daily',
        lastmod: product.updated_at ? new Date(product.updated_at).toISOString().split('T')[0] : undefined
      }))
    }
  } catch (error) {
    console.error('Failed to fetch products for sitemap:', error)
    // Continue with static pages only if API fails
  }

  // Combine all URLs
  const allUrls = [...staticPages, ...productUrls]

  // Generate XML
  const today = new Date().toISOString().split('T')[0]

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${allUrls.map(page => `  <url>
    <loc>${baseUrl}${page.url}</loc>
    <lastmod>${page.lastmod || today}</lastmod>
    <changefreq>${page.changefreq}</changefreq>
    <priority>${page.priority}</priority>
  </url>`).join('\n')}
</urlset>`

  // Set proper content type for XML
  setHeader(event, 'Content-Type', 'application/xml; charset=utf-8')
  // Cache for 1 hour (Google re-crawls sitemaps periodically)
  setHeader(event, 'Cache-Control', 'public, max-age=3600, s-maxage=3600')

  return xml
})
