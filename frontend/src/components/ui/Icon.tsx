import React from 'react'
import { cn } from '@/lib/utils'

export type IconSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

const iconSizeClasses: Record<IconSize, string> = {
  xs: 'h-3 w-3',      // 12px - Very small icons (badges, inline text)
  sm: 'h-4 w-4',      // 16px - Default size (buttons, inline elements)
  md: 'h-5 w-5',      // 20px - Medium icons (cards, lists)
  lg: 'h-6 w-6',      // 24px - Large icons (headers, empty states)
  xl: 'h-8 w-8',      // 32px - Extra large icons (featured, hero sections)
}

interface IconProps {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>
  size?: IconSize
  className?: string
}

/**
 * Icon component with consistent sizing
 * 
 * Usage:
 * <Icon icon={CheckCircle} size="md" className="text-primary" />
 * 
 * Size guidelines:
 * - xs (12px): Badges, inline text, very small UI elements
 * - sm (16px): Default - buttons, inline elements, form fields
 * - md (20px): Cards, lists, medium UI elements
 * - lg (24px): Headers, empty states, prominent UI elements
 * - xl (32px): Featured icons, hero sections, large displays
 */
export function Icon({ icon: IconComponent, size = 'sm', className }: IconProps) {
  return (
    <IconComponent 
      className={cn(iconSizeClasses[size], className)} 
    />
  )
}

/**
 * Icon size utility for direct use with Lucide icons
 * 
 * Usage:
 * <CheckCircle className={iconSize('md')} />
 */
export function iconSize(size: IconSize = 'sm'): string {
  return iconSizeClasses[size]
}
