/**
 * Bosnian/Croatian/Serbian plural forms helper
 *
 * Rules:
 * - 1 (or ends in 1, except 11): singular form
 * - 2, 3, 4 (or ends in 2-4, except 12-14): paucal form
 * - 0, 5-9, 11-14 (or ends in 0, 5-9): plural form
 */
export function usePluralBs() {
  function pluralBs(n: number, singular: string, paucal: string, plural: string): string {
    n = Math.abs(n)
    const lastDigit = n % 10
    const lastTwoDigits = n % 100

    // Special case for teens (11-14) - always plural
    if (lastTwoDigits >= 11 && lastTwoDigits <= 14) {
      return plural
    }

    if (lastDigit === 1) {
      return singular
    } else if (lastDigit >= 2 && lastDigit <= 4) {
      return paucal
    } else {
      return plural
    }
  }

  return { pluralBs }
}
