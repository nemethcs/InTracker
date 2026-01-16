/**
 * Optimized Image component with lazy loading and error handling
 */

import { useState, useRef, useEffect, ImgHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

interface OptimizedImageProps extends Omit<ImgHTMLAttributes<HTMLImageElement>, 'loading'> {
  src: string
  alt: string
  fallbackSrc?: string
  lazy?: boolean
  className?: string
  onError?: () => void
}

/**
 * Optimized Image component with:
 * - Native lazy loading support
 * - Error handling with fallback
 * - Loading state
 * - Intersection Observer for older browsers
 */
export function OptimizedImage({
  src,
  alt,
  fallbackSrc,
  lazy = true,
  className,
  onError,
  ...props
}: OptimizedImageProps) {
  const [imageSrc, setImageSrc] = useState<string>(src)
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)

  // Reset state when src changes
  useEffect(() => {
    setImageSrc(src)
    setIsLoading(true)
    setHasError(false)
  }, [src])

  // Intersection Observer for lazy loading (fallback for older browsers)
  useEffect(() => {
    if (!lazy || !imgRef.current) return

    // Check if native lazy loading is supported
    if ('loading' in HTMLImageElement.prototype) {
      // Native lazy loading is supported, no need for Intersection Observer
      return
    }

    // Fallback: Use Intersection Observer for older browsers
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && imgRef.current) {
            // Load the image when it enters the viewport
            if (imgRef.current.dataset.src) {
              imgRef.current.src = imgRef.current.dataset.src
              imgRef.current.removeAttribute('data-src')
            }
            observer.disconnect()
          }
        })
      },
      {
        rootMargin: '50px', // Start loading 50px before the image enters viewport
      }
    )

    if (imgRef.current) {
      observer.observe(imgRef.current)
    }

    return () => {
      observer.disconnect()
    }
  }, [lazy])

  const handleLoad = () => {
    setIsLoading(false)
  }

  const handleError = () => {
    setIsLoading(false)
    setHasError(true)
    
    // Try fallback image if available
    if (fallbackSrc && imageSrc !== fallbackSrc) {
      setImageSrc(fallbackSrc)
      setHasError(false)
      setIsLoading(true)
    } else {
      // Call custom error handler if provided
      onError?.()
    }
  }

  // Prepare src for lazy loading
  const finalSrc = lazy && !('loading' in HTMLImageElement.prototype) 
    ? undefined // Will be set via Intersection Observer
    : imageSrc

  return (
    <div className={cn('relative inline-block', className)}>
      <img
        ref={imgRef}
        src={finalSrc}
        data-src={lazy && !('loading' in HTMLImageElement.prototype) ? imageSrc : undefined}
        alt={alt}
        loading={lazy ? 'lazy' : 'eager'}
        onLoad={handleLoad}
        onError={handleError}
        className={cn(
          'transition-opacity duration-200',
          isLoading ? 'opacity-0' : 'opacity-100',
          hasError && !fallbackSrc ? 'opacity-50' : '',
          className
        )}
        {...props}
      />
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted animate-pulse">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
      {hasError && !fallbackSrc && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted">
          <span className="text-xs text-muted-foreground">Image not available</span>
        </div>
      )}
    </div>
  )
}
