/**
 * First-Touch Attribution Tracking
 *
 * Captures attribution data on first landing and persists it until registration/login.
 * Priority: UTM params > fbclid > referrer analysis > direct
 *
 * Attribution is stored in localStorage and NEVER overwritten once set.
 */

interface AttributionData {
  source: string           // e.g., 'facebook', 'google', 'email', 'direct'
  medium: string | null    // e.g., 'cpc', 'social', 'email'
  campaign: string | null  // e.g., 'winter_sale_2025'
  fbclid: string | null    // Facebook click ID if present
  timestamp: string        // ISO timestamp of first touch
  landing_page: string     // URL where user first landed
  referrer: string | null  // Original referrer URL
}

const ATTRIBUTION_KEY = 'popust_first_touch'

export const useAttribution = () => {
  /**
   * Determine source from referrer URL
   */
  const getSourceFromReferrer = (referrer: string): string => {
    if (!referrer) return 'direct'

    const lowerRef = referrer.toLowerCase()

    // Facebook (including l.facebook.com redirect)
    if (lowerRef.includes('facebook.com') || lowerRef.includes('fb.com') || lowerRef.includes('l.facebook.com')) {
      return 'facebook'
    }

    // Instagram (owned by Facebook)
    if (lowerRef.includes('instagram.com') || lowerRef.includes('l.instagram.com')) {
      return 'instagram'
    }

    // Google (search, ads, etc.)
    if (lowerRef.includes('google.')) {
      return 'google'
    }

    // Bing
    if (lowerRef.includes('bing.com')) {
      return 'bing'
    }

    // Twitter/X
    if (lowerRef.includes('twitter.com') || lowerRef.includes('t.co') || lowerRef.includes('x.com')) {
      return 'twitter'
    }

    // LinkedIn
    if (lowerRef.includes('linkedin.com')) {
      return 'linkedin'
    }

    // TikTok
    if (lowerRef.includes('tiktok.com')) {
      return 'tiktok'
    }

    // YouTube
    if (lowerRef.includes('youtube.com') || lowerRef.includes('youtu.be')) {
      return 'youtube'
    }

    // If referrer exists but doesn't match known sources
    return 'referral'
  }

  /**
   * Capture attribution from current page context
   * Called on every page load, but only saves if no attribution exists
   */
  const captureAttribution = (): void => {
    if (!process.client) return

    // Check if attribution already exists - never overwrite!
    const existing = localStorage.getItem(ATTRIBUTION_KEY)
    if (existing) {
      return // First touch already captured
    }

    const url = new URL(window.location.href)
    const params = url.searchParams

    // Get referrer
    const referrer = document.referrer || null

    // Start with default attribution
    let attribution: AttributionData = {
      source: 'direct',
      medium: null,
      campaign: null,
      fbclid: null,
      timestamp: new Date().toISOString(),
      landing_page: window.location.pathname + window.location.search,
      referrer: referrer
    }

    // Priority 1: Check for UTM parameters (highest priority)
    const utmSource = params.get('utm_source')
    const utmMedium = params.get('utm_medium')
    const utmCampaign = params.get('utm_campaign')

    if (utmSource) {
      attribution.source = utmSource.toLowerCase()
      attribution.medium = utmMedium?.toLowerCase() || null
      attribution.campaign = utmCampaign || null
    }
    // Priority 2: Check for fbclid (Facebook click ID)
    else if (params.get('fbclid')) {
      attribution.source = 'facebook'
      attribution.medium = 'paid_social'
      attribution.fbclid = params.get('fbclid')
    }
    // Priority 3: Analyze referrer
    else if (referrer) {
      attribution.source = getSourceFromReferrer(referrer)

      // Set medium based on detected source
      if (['facebook', 'instagram', 'twitter', 'linkedin', 'tiktok'].includes(attribution.source)) {
        attribution.medium = 'social'
      } else if (attribution.source === 'google') {
        attribution.medium = 'organic'
      } else if (attribution.source === 'referral') {
        attribution.medium = 'referral'
      }
    }
    // Priority 4: Direct traffic (no referrer, no params)
    // attribution.source is already 'direct'

    // Store attribution in localStorage
    localStorage.setItem(ATTRIBUTION_KEY, JSON.stringify(attribution))

    console.log('[Attribution] First touch captured:', attribution)
  }

  /**
   * Get stored attribution data
   */
  const getAttribution = (): AttributionData | null => {
    if (!process.client) return null

    const stored = localStorage.getItem(ATTRIBUTION_KEY)
    if (!stored) return null

    try {
      return JSON.parse(stored) as AttributionData
    } catch {
      return null
    }
  }

  /**
   * Clear attribution after it's been persisted to the backend
   * Call this after successful registration that saved attribution
   */
  const clearAttribution = (): void => {
    if (!process.client) return
    localStorage.removeItem(ATTRIBUTION_KEY)
  }

  /**
   * Get attribution data formatted for backend API
   */
  const getAttributionForApi = (): Record<string, string | null> | null => {
    const attr = getAttribution()
    if (!attr) return null

    return {
      first_touch_source: attr.source,
      first_touch_medium: attr.medium,
      first_touch_campaign: attr.campaign,
      first_touch_fbclid: attr.fbclid,
      first_touch_timestamp: attr.timestamp,
      first_touch_landing_page: attr.landing_page,
      first_touch_referrer: attr.referrer
    }
  }

  return {
    captureAttribution,
    getAttribution,
    clearAttribution,
    getAttributionForApi
  }
}
