# Image Optimization and Lazy Loading

## Overview

The frontend application includes optimized image loading with lazy loading support to improve performance and reduce initial page load time.

## OptimizedImage Component

The `OptimizedImage` component provides:

- **Native lazy loading**: Uses the browser's native `loading="lazy"` attribute
- **Intersection Observer fallback**: For older browsers that don't support native lazy loading
- **Error handling**: Automatic fallback to a default image if the primary image fails to load
- **Loading state**: Shows a loading spinner while the image is loading
- **Smooth transitions**: Opacity transitions for better UX

## Usage

### Basic Usage

```typescript
import { OptimizedImage } from '@/components/ui/OptimizedImage'

<OptimizedImage
  src="/path/to/image.jpg"
  alt="Description of image"
  lazy={true}
  className="rounded-lg"
/>
```

### With Fallback

```typescript
<OptimizedImage
  src="/path/to/image.jpg"
  alt="Description"
  fallbackSrc="/path/to/fallback.jpg"
  lazy={true}
/>
```

### Eager Loading (Above the Fold)

```typescript
<OptimizedImage
  src="/path/to/hero-image.jpg"
  alt="Hero image"
  lazy={false} // Load immediately
/>
```

## Implementation Details

### Native Lazy Loading

Modern browsers (Chrome 76+, Firefox 75+, Safari 15.4+) support native lazy loading via the `loading="lazy"` attribute. The component uses this when available.

### Intersection Observer Fallback

For older browsers, the component uses Intersection Observer to detect when the image enters the viewport and loads it then. The observer starts loading images 50px before they enter the viewport for smoother UX.

### Error Handling

1. If the primary image fails to load:
   - If a `fallbackSrc` is provided, it automatically tries to load the fallback
   - If no fallback is available, shows an "Image not available" message
   - Calls the optional `onError` callback

### Loading State

While the image is loading:
- Shows a loading spinner overlay
- Applies opacity transition when loaded
- Prevents layout shift

## Current Usage

The `OptimizedImage` component is currently used for:

1. **GitHub Avatars**: In `GitHubSetupStep` and `GitHubSettings` components
2. **User Avatars**: Via the `Avatar` component (uses native lazy loading)

## Avatar Component

The `Avatar` component from Radix UI has been updated to use native lazy loading:

```typescript
<Avatar>
  <AvatarImage src={user.avatar_url} alt={user.name} />
  <AvatarFallback>{user.name[0]}</AvatarFallback>
</Avatar>
```

The `AvatarImage` component now includes `loading="lazy"` by default.

## Best Practices

1. **Use lazy loading for below-the-fold images**: Images that aren't immediately visible should use `lazy={true}`

2. **Use eager loading for above-the-fold images**: Hero images, logos, and critical images should use `lazy={false}`

3. **Always provide alt text**: For accessibility and SEO

4. **Use appropriate image formats**:
   - WebP for modern browsers (with fallback)
   - JPEG for photos
   - PNG for images with transparency
   - SVG for icons and simple graphics

5. **Optimize image sizes**: Use appropriate dimensions and compression

6. **Provide fallback images**: For critical images, always provide a fallback

## Performance Benefits

- **Reduced initial load time**: Images are only loaded when needed
- **Lower bandwidth usage**: Only visible images are downloaded
- **Better Core Web Vitals**: Improves LCP (Largest Contentful Paint) and CLS (Cumulative Layout Shift)
- **Improved user experience**: Faster page loads, especially on mobile devices

## Future Enhancements

Potential improvements:

1. **Responsive images**: Add `srcset` and `sizes` attributes for different screen sizes
2. **Blur placeholder**: Show a blurred placeholder while loading
3. **Progressive loading**: Load low-quality placeholder first, then high-quality image
4. **Image CDN integration**: Use a CDN for optimized image delivery
5. **WebP with fallback**: Automatically serve WebP to supported browsers
