import { Link, useLocation } from 'react-router-dom'
import { FolderKanban, Settings, Sparkles, Shield, UsersRound, Users, X, BookOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useAuth } from '@/hooks/useAuth'

const navigation = [
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Ideas', href: '/ideas', icon: Sparkles },
  { name: 'Cursor Guide', href: '/guide', icon: BookOpen },
]

const teamNavigation = { name: 'Teams', href: '/teams', icon: UsersRound }
const usersNavigation = { name: 'Users', href: '/users', icon: Users }

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation()
  const { user } = useAuth()

  // All users (including admins) see the normal navigation + Teams
  // Admin functions are integrated into Teams and Settings pages
  // Admins also see Users menu item
  const isAdmin = user?.role === 'admin'
  const allNavigation = isAdmin 
    ? [...navigation, teamNavigation, usersNavigation]
    : [...navigation, teamNavigation]

  // Close sidebar when route changes (mobile)
  const handleLinkClick = () => {
    if (window.innerWidth < 1024) {
      onClose()
    }
  }

  return (
    <>
      {/* Mobile sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 border-r bg-background transform transition-transform duration-300 ease-in-out lg:hidden",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-14 items-center border-b px-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="ml-auto"
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
        <nav className="space-y-1 p-4">
          {allNavigation.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/')
            return (
              <Link
                key={item.name}
                to={item.href}
                onClick={handleLinkClick}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-smooth",
                  "hover:bg-accent hover:text-accent-foreground",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground"
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Desktop sidebar */}
      <aside className="hidden lg:block w-64 border-r bg-background shrink-0 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto">
        <nav className="space-y-1 p-4">
          {allNavigation.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/')
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-smooth",
                  "hover:bg-accent hover:text-accent-foreground",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground"
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </aside>
    </>
  )
}
