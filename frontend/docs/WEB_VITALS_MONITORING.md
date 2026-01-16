# Web Vitals Performance Monitoring

## Overview

The frontend application includes Web Vitals performance monitoring to track Core Web Vitals and other important performance metrics. This helps identify performance issues and ensure a good user experience.

## Core Web Vitals

### LCP (Largest Contentful Paint)
- **Target**: < 2.5 seconds
- **Measures**: Loading performance - how long it takes for the largest content element to be visible
- **Impact**: User perception of page load speed

### INP (Interaction to Next Paint)
- **Target**: < 200 milliseconds
- **Measures**: Interactivity - time from user interaction to visual feedback (replaces FID in Web Vitals v5)
- **Impact**: User perception of page responsiveness
- **Note**: FID (First Input Delay) was deprecated in favor of INP, which provides a more comprehensive measure of interactivity

### CLS (Cumulative Layout Shift)
- **Target**: < 0.1
- **Measures**: Visual stability - unexpected layout shifts during page load
- **Impact**: User experience and content readability

## Additional Metrics

### FCP (First Contentful Paint)
- **Measures**: Time to first content (text, image, etc.) being rendered
- **Impact**: Perceived loading speed

### TTFB (Time to First Byte)
- **Measures**: Time from request to first byte received
- **Impact**: Server response time and network latency

## Implementation

### Initialization

Web Vitals monitoring is automatically initialized in `main.tsx`:

```typescript
import { initWebVitals } from './utils/webVitals'

initWebVitals({
  debug: import.meta.env.DEV,
  sampleRate: 1.0, // Report 100% of metrics
})
```

### Configuration Options

- `endpoint`: Backend endpoint for reporting metrics (optional)
- `debug`: Enable console logging (default: `import.meta.env.DEV`)
- `sampleRate`: Percentage of metrics to report (0.0 - 1.0, default: 1.0)

### Usage

```typescript
import { getWebVitalsMetrics, getWebVitalsMetric } from '@/utils/webVitals'

// Get all metrics
const metrics = getWebVitalsMetrics()

// Get specific metric
const lcp = getWebVitalsMetric('LCP')
if (lcp) {
  console.log('LCP:', lcp.value, lcp.rating)
}
```

## Metric Ratings

Each metric includes a `rating` field:
- `'good'`: Meets the target threshold
- `'needs-improvement'`: Close to threshold but could be better
- `'poor'`: Fails to meet the threshold

## Backend Integration

To report metrics to a backend endpoint, configure the `endpoint` option:

```typescript
initWebVitals({
  endpoint: 'https://api.example.com/analytics/web-vitals',
  sampleRate: 0.1, // Report 10% of metrics in production
})
```

The backend will receive POST requests with the following payload:

```json
{
  "name": "LCP",
  "value": 1234,
  "rating": "good",
  "delta": 1234,
  "id": "metric-id",
  "navigationType": "navigate",
  "url": "https://example.com/page",
  "timestamp": 1234567890
}
```

## Production Recommendations

1. **Sample Rate**: Use a lower sample rate (e.g., 0.1) in production to reduce backend load
2. **Endpoint**: Configure a backend endpoint to collect metrics for analysis
3. **Debug Mode**: Disable debug logging in production
4. **Error Handling**: Metrics are sent with `keepalive: true` to ensure delivery even if page is unloading

## Monitoring Dashboard

Consider creating a dashboard to visualize:
- Average metric values over time
- Distribution of metric ratings
- Performance trends
- Page-specific performance

## Best Practices

1. **Monitor Regularly**: Check metrics regularly to identify regressions
2. **Set Alerts**: Configure alerts for metrics that exceed thresholds
3. **Analyze Trends**: Look for patterns in performance data
4. **Optimize Based on Data**: Use metrics to prioritize optimization efforts

## Resources

- [Web Vitals Library](https://github.com/GoogleChrome/web-vitals)
- [Core Web Vitals](https://web.dev/vitals/)
- [Web Vitals Extension](https://chrome.google.com/webstore/detail/web-vitals/ahfhijdlegdabablpippeagghigmibma)
