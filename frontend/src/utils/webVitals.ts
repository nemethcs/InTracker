/**
 * Web Vitals performance monitoring
 * 
 * Tracks Core Web Vitals and other performance metrics:
 * - LCP (Largest Contentful Paint)
 * - INP (Interaction to Next Paint) - replaces FID in Web Vitals v5
 * - CLS (Cumulative Layout Shift)
 * - FCP (First Contentful Paint)
 * - TTFB (Time to First Byte)
 */

import { onCLS, onFCP, onINP, onLCP, onTTFB, type Metric } from 'web-vitals'

interface WebVitalsConfig {
  endpoint?: string
  debug?: boolean
  sampleRate?: number
}

class WebVitalsReporter {
  private config: Required<WebVitalsConfig>
  private metrics: Map<string, Metric> = new Map()

  constructor(config: WebVitalsConfig = {}) {
    this.config = {
      endpoint: config.endpoint || '/api/analytics/web-vitals',
      debug: config.debug || import.meta.env.DEV,
      sampleRate: config.sampleRate ?? 1.0,
    }
  }

  /**
   * Report metric to backend (if endpoint is configured)
   */
  private async reportMetric(metric: Metric): Promise<void> {
    // Only report if within sample rate
    if (Math.random() > this.config.sampleRate) {
      return
    }

    // Store metric locally
    this.metrics.set(metric.name, metric)

    // Log in development
    if (this.config.debug) {
      console.log(`[Web Vitals] ${metric.name}:`, {
        value: metric.value,
        rating: metric.rating,
        delta: metric.delta,
        id: metric.id,
      })
    }

    // Report to backend if endpoint is configured
    if (this.config.endpoint && this.config.endpoint.startsWith('http')) {
      try {
        await fetch(this.config.endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: metric.name,
            value: metric.value,
            rating: metric.rating,
            delta: metric.delta,
            id: metric.id,
            navigationType: metric.navigationType,
            url: window.location.href,
            timestamp: Date.now(),
          }),
          keepalive: true, // Send even if page is unloading
        })
      } catch (error) {
        if (this.config.debug) {
          console.warn('[Web Vitals] Failed to report metric:', error)
        }
      }
    }
  }

  /**
   * Initialize Web Vitals tracking
   */
  initialize(): void {
    // Core Web Vitals
    onCLS((metric) => {
      this.reportMetric(metric)
    })

    onFID((metric) => {
      this.reportMetric(metric)
    })

    onLCP((metric) => {
      this.reportMetric(metric)
    })

    // Additional metrics
    onFCP((metric) => {
      this.reportMetric(metric)
    })

    onTTFB((metric) => {
      this.reportMetric(metric)
    })

    if (this.config.debug) {
      console.log('[Web Vitals] Performance monitoring initialized')
    }
  }

  /**
   * Get all collected metrics
   */
  getMetrics(): Map<string, Metric> {
    return new Map(this.metrics)
  }

  /**
   * Get a specific metric
   */
  getMetric(name: string): Metric | undefined {
    return this.metrics.get(name)
  }

  /**
   * Clear all metrics
   */
  clearMetrics(): void {
    this.metrics.clear()
  }
}

// Create singleton instance
let webVitalsReporter: WebVitalsReporter | null = null

/**
 * Initialize Web Vitals monitoring
 */
export function initWebVitals(config?: WebVitalsConfig): void {
  if (webVitalsReporter) {
    console.warn('[Web Vitals] Already initialized')
    return
  }

  webVitalsReporter = new WebVitalsReporter(config)
  webVitalsReporter.initialize()
}

/**
 * Get Web Vitals reporter instance
 */
export function getWebVitalsReporter(): WebVitalsReporter | null {
  return webVitalsReporter
}

/**
 * Get all collected metrics
 */
export function getWebVitalsMetrics(): Map<string, Metric> {
  return webVitalsReporter?.getMetrics() || new Map()
}

/**
 * Get a specific metric
 */
export function getWebVitalsMetric(name: string): Metric | undefined {
  return webVitalsReporter?.getMetric(name)
}
