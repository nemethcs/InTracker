import { Link, useLocation } from 'react-router-dom'
import { FolderKanban, Settings, Sparkles, Shield, UsersRound } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useAuth } from '@/hooks/useAuth'

const navigation = [
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Ideas', href: '/ideas', icon: Sparkles },
  { name: 'Settings', href: '/settings', icon: Settings },
]

const teamNavigation = { name: 'Teams', href: '/teams', icon: UsersRound }
const adminNavigation = { name: 'Admin', href: '/admin', icon: Shield }

export function Sidebar() {
  const location = useLocation()
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const isTeamLeader = user?.role === 'team_leader'

  let allNavigation: typeof navigation = []
  
  // Admins only see Admin and Teams links
  if (isAdmin) {
    allNavigation = [adminNavigation, teamNavigation]
  } else {
    // Regular users and team leaders see normal navigation + Teams
    // All users (not just team leaders) can see Teams menu
    allNavigation = [...navigation, teamNavigation]
  }

  return (
    <aside className="w-64 border-r bg-background">
      <nav className="space-y-1 p-4">
        {allNavigation.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.href
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-smooth",
                "hover:bg-accent hover:text-accent-foreground",
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
