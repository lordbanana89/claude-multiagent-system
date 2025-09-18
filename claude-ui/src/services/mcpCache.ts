// MCP API Cache Service - Prevents duplicate requests

interface CacheEntry {
  data: any;
  timestamp: number;
  promise?: Promise<any>;
}

class MCPCacheService {
  private cache: Map<string, CacheEntry> = new Map();
  private readonly TTL = 5000; // 5 seconds cache
  private readonly MIN_INTERVAL = 1000; // Minimum 1 second between requests

  async fetch<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number = this.TTL
  ): Promise<T> {
    const now = Date.now();
    const entry = this.cache.get(key);

    // Return cached data if still valid
    if (entry && (now - entry.timestamp) < ttl) {
      // If there's an ongoing request, wait for it
      if (entry.promise) {
        return entry.promise;
      }
      return entry.data;
    }

    // If request was made recently, return old data
    if (entry && (now - entry.timestamp) < this.MIN_INTERVAL) {
      return entry.data;
    }

    // Create new request promise
    const promise = fetcher()
      .then(data => {
        // Update cache with result
        this.cache.set(key, {
          data,
          timestamp: now,
          promise: undefined
        });
        return data;
      })
      .catch(error => {
        // On error, keep old data if available
        if (entry) {
          this.cache.set(key, {
            ...entry,
            promise: undefined
          });
          return entry.data;
        }
        throw error;
      });

    // Store promise to prevent duplicate requests
    this.cache.set(key, {
      data: entry?.data,
      timestamp: entry?.timestamp || 0,
      promise
    });

    return promise;
  }

  clear(key?: string) {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }

  // Singleton instance
  private static instance: MCPCacheService;

  static getInstance(): MCPCacheService {
    if (!MCPCacheService.instance) {
      MCPCacheService.instance = new MCPCacheService();
    }
    return MCPCacheService.instance;
  }
}

export default MCPCacheService.getInstance();