import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'

interface NavigationItem {
  name: string
  href: string
  icon?: React.ComponentType<{ className?: string }>
}

interface NavigationProps {
  items: NavigationItem[]
  className?: string
}

export function Navigation({ items, className }: NavigationProps) {
  const location = useLocation()

  return (
    <nav className={cn("flex space-x-1", className)}>
      {items.map((item) => {
        const Icon = item.icon
        const isActive = location.pathname === item.href
        return (
          <Link
            key={item.name}
            to={item.href}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            )}
          >
            {Icon && <Icon className="h-4 w-4" />}
            {item.name}
          </Link>
        )
      })}
    </nav>
  )
}
