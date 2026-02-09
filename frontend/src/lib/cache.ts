/**
 * Client-side caching utilities for improved performance.
 * 
 * Provides localStorage-based caching with TTL (Time-To-Live) support.
 * Falls back gracefully when localStorage is unavailable (SSR, private browsing).
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

/**
 * Check if localStorage is available.
 */
function isLocalStorageAvailable(): boolean {
  try {
    const testKey = '__cache_test__';
    localStorage.setItem(testKey, 'test');
    localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
}

/**
 * Get a cached value from localStorage.
 * Returns null if not found or expired.
 */
export function getCached<T>(key: string): T | null {
  if (!isLocalStorageAvailable()) {
    return null;
  }

  try {
    const raw = localStorage.getItem(`cache:${key}`);
    if (!raw) {
      return null;
    }

    const entry: CacheEntry<T> = JSON.parse(raw);
    const age = Date.now() - entry.timestamp;

    if (age > entry.ttl) {
      // Expired - remove from cache
      localStorage.removeItem(`cache:${key}`);
      return null;
    }

    return entry.data;
  } catch {
    return null;
  }
}

/**
 * Store a value in the cache with a TTL.
 */
export function setCache<T>(key: string, data: T, ttlMs: number = 30000): void {
  if (!isLocalStorageAvailable()) {
    return;
  }

  try {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl: ttlMs,
    };
    localStorage.setItem(`cache:${key}`, JSON.stringify(entry));
  } catch {
    // Ignore errors (e.g., quota exceeded)
  }
}

/**
 * Remove a specific item from the cache.
 */
export function invalidateCache(key: string): void {
  if (!isLocalStorageAvailable()) {
    return;
  }

  try {
    localStorage.removeItem(`cache:${key}`);
  } catch {
    // Ignore errors
  }
}

/**
 * Clear all cached items (those with 'cache:' prefix).
 */
export function clearAllCache(): void {
  if (!isLocalStorageAvailable()) {
    return;
  }

  try {
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith('cache:')) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach((key) => localStorage.removeItem(key));
  } catch {
    // Ignore errors
  }
}

/**
 * Wrapper for async functions that caches results.
 * 
 * @param key - Cache key
 * @param fetcher - Async function that fetches the data
 * @param ttlMs - Time-to-live in milliseconds (default: 30 seconds)
 * @returns Cached data if available, otherwise fetches fresh data
 * 
 * @example
 * ```ts
 * const apps = await withCache(
 *   `applications:${persona}`,
 *   () => listApplications(persona),
 *   30000 // 30 seconds
 * );
 * ```
 */
export async function withCache<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlMs: number = 30000
): Promise<T> {
  // Check cache first
  const cached = getCached<T>(key);
  if (cached !== null) {
    return cached;
  }

  // Fetch fresh data
  const data = await fetcher();

  // Store in cache
  setCache(key, data, ttlMs);

  return data;
}

/**
 * Default cache TTLs for different data types.
 */
export const CACHE_TTL = {
  /** Application list - refresh frequently */
  APPLICATIONS: 30 * 1000, // 30 seconds
  /** Persona list - rarely changes */
  PERSONAS: 5 * 60 * 1000, // 5 minutes
  /** Policies - moderately stable */
  POLICIES: 2 * 60 * 1000, // 2 minutes
  /** Prompts - moderately stable */
  PROMPTS: 2 * 60 * 1000, // 2 minutes
} as const;
