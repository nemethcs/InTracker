import { ReactNode, useState } from 'react'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

interface MainLayoutProps {
  children: ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const toggleSidebar = () => {
    setSidebarOpen(prev => !prev)
  }

  const closeSidebar = () => {
    setSidebarOpen(false)
  }

  return (
    <div className="min-h-screen bg-background">
      <Header 
        sidebarOpen={sidebarOpen}
        onMenuClick={toggleSidebar}
      />
      <div className="flex relative">
        {/* Mobile overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden transition-opacity"
            onClick={closeSidebar}
            aria-hidden="true"
          />
        )}
        {/* Sidebar */}
        <Sidebar 
          isOpen={sidebarOpen}
          onClose={closeSidebar}
        />
        {/* Main content */}
        <main className="flex-1 min-w-0">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
