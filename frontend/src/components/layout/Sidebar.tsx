import { Home, FolderKanban, CheckSquare, FileText, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Todos', href: '/todos', icon: CheckSquare },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  return (
    <aside className="w-64 border-r bg-background">
      <nav className="space-y-1 p-4">
        {navigation.map((item) => {
          const Icon = item.icon
          return (
            <a
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                "hover:bg-accent hover:text-accent-foreground",
                "text-muted-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.name}
            </a>
          )
        })}
      </nav>
    </aside>
  )
}
