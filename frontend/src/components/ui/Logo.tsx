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

  const textSizeClasses = {
    sm: 'text-base',
    md: 'text-xl',
    lg: 'text-2xl',
  }

  return (
    <Link to="/" className={cn("flex items-center gap-2.5", className)}>
      <svg
        className={cn(sizeClasses[size], "flex-shrink-0")}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        {/* Background circle with gradient */}
        <defs>
          <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="hsl(var(--primary))" />
            <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0.8" />
          </linearGradient>
        </defs>
        
        {/* Outer ring */}
        <circle
          cx="16"
          cy="16"
          r="14"
          stroke="url(#logoGradient)"
          strokeWidth="2"
          fill="none"
          opacity="0.3"
        />
        
        {/* Inner tracking nodes */}
        <circle
          cx="16"
          cy="8"
          r="2.5"
          fill="url(#logoGradient)"
          opacity="0.9"
        />
        <circle
          cx="24"
          cy="16"
          r="2.5"
          fill="url(#logoGradient)"
          opacity="0.9"
        />
        <circle
          cx="16"
          cy="24"
          r="2.5"
          fill="url(#logoGradient)"
          opacity="0.9"
        />
        <circle
          cx="8"
          cy="16"
          r="2.5"
          fill="url(#logoGradient)"
          opacity="0.9"
        />
        
        {/* Connecting lines */}
        <line
          x1="16"
          y1="8"
          x2="24"
          y2="16"
          stroke="url(#logoGradient)"
          strokeWidth="1.5"
          strokeLinecap="round"
          opacity="0.4"
        />
        <line
          x1="24"
          y1="16"
          x2="16"
          y2="24"
          stroke="url(#logoGradient)"
          strokeWidth="1.5"
          strokeLinecap="round"
          opacity="0.4"
        />
        <line
          x1="16"
          y1="24"
          x2="8"
          y2="16"
          stroke="url(#logoGradient)"
          strokeWidth="1.5"
          strokeLinecap="round"
          opacity="0.4"
        />
        <line
          x1="8"
          y1="16"
          x2="16"
          y2="8"
          stroke="url(#logoGradient)"
          strokeWidth="1.5"
          strokeLinecap="round"
          opacity="0.4"
        />
        
        {/* Center dot */}
        <circle
          cx="16"
          cy="16"
          r="3"
          fill="url(#logoGradient)"
        />
      </svg>
      {showText && (
        <span className={cn(
          "font-bold tracking-tight text-foreground",
          textSizeClasses[size]
        )}>
          InTracker
        </span>
      )}
    </Link>
  )
}
