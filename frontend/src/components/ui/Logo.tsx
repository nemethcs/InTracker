import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'

interface LogoProps {
  className?: string
  showText?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function Logo({ className, showText = true, size = 'md' }: LogoProps) {
  const sizeClasses = {
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }

  return (
    <Link to="/" className={cn("flex items-center gap-2", className)}>
      <img
        src="/assets/logo.png"
        alt="InTracker"
        className={cn(sizeClasses[size], "object-contain")}
      />
      {showText && (
        <span className={cn(
          "font-bold tracking-tight",
          size === 'sm' && "text-base",
          size === 'md' && "text-xl",
          size === 'lg' && "text-2xl"
        )}>
          InTracker
        </span>
      )}
    </Link>
  )
}
